from datetime import date  # <- add this import

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.db.database import get_db
from app.db import models
from app.core.security import hash_password, verify_password, create_access_token
from app.core.security import maybe_upgrade_hash
from app.services.password_reset import make_reset_token, hash_token, expires_at
from app.services.mailer import send_reset_email

from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")

class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=128)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.Person:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = db.query(models.Person).filter(models.Person.email == email).first()
    if not user or not user.is_active:
        raise cred_exc
    return user


@router.post("/signup")
def signup(
    full_name: str,
    email: str,
    password: str,
    gender: models.GenderEnum = models.GenderEnum.unknown,
    date_of_birth: date | None = None,  # <- NEW
    line1: str = None,
    city: str = None,
    state: str = None,
    postal_code: str = None,
    country: str = None,
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    if db.query(models.Person).filter(models.Person.email == email).first():
        raise HTTPException(400, "Email already registered")

    # create user
    user = models.Person(
        full_name=full_name.strip(),
        email=email,
        password_hash=hash_password(password),
        gender=gender,
        date_of_birth=date_of_birth,  # <- NEW
    )
    db.add(user)
    db.flush()  # assign user.id (UUID)

    # create address if provided
    if any([line1, city, state, postal_code, country]):
        addr = models.Address(
            person_id=user.id,
            line1=line1,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
        )
        db.add(addr)

    db.commit()
    db.refresh(user)

    token = create_access_token(subject=email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,  # UUID
            "full_name": user.full_name,
            "email": user.email,
            "gender": user.gender,
            "date_of_birth": user.date_of_birth,  # <- NEW (FastAPI will serialize)
        },
    }


@router.post("/signin")
def signin(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    email = form_data.username.strip().lower()
    user = db.query(models.Person).filter(models.Person.email == email).first()
    if not user or not user.password_hash or not verify_password(
        form_data.password, user.password_hash
    ):
        raise HTTPException(401, "Invalid email or password")
    
    if new_hash := maybe_upgrade_hash(user.password_hash, form_data.password):
        user.password_hash = new_hash
        db.commit()

    token = create_access_token(subject=user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(current: models.Person = Depends(get_current_user)):
    return {
        "id": current.id,  # UUID
        "full_name": current.full_name,
        "email": current.email,
        "is_active": current.is_active,
        "gender": current.gender,
        "date_of_birth": current.date_of_birth,  # <- NEW
        "address": {
            "line1": current.address.line1 if current.address else None,
            "city": current.address.city if current.address else None,
            "state": current.address.state if current.address else None,
            "postal_code": current.address.postal_code if current.address else None,
            "country": current.address.country if current.address else None,
        },
    }

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(models.Person).filter(models.Person.email == email).first()

    # anti email-enumeration: always return ok
    if not user or not user.is_active:
        return {"ok": True}

    raw = make_reset_token()

    rec = models.PasswordResetToken(
        person_id=user.id,
        token_hash=hash_token(raw),
        expires_at=expires_at(15),
        used=False,
    )
    db.add(rec)
    db.commit()

    try:
        send_reset_email(user.email, raw)
    except Exception:
        # keep response generic
        return {"ok": True}

    return {"ok": True}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)):
    token_h = hash_token(payload.token.strip())

    rec = (
        db.query(models.PasswordResetToken)
        .filter(models.PasswordResetToken.token_hash == token_h)
        .first()
    )
    if not rec:
        raise HTTPException(400, "Token tidak valid")
    if rec.used:
        raise HTTPException(400, "Token sudah digunakan")
    if rec.expires_at < datetime.utcnow():
        raise HTTPException(400, "Token sudah kedaluwarsa")

    user = db.get(models.Person, rec.person_id)
    if not user or not user.is_active:
        raise HTTPException(400, "User tidak ditemukan/aktif")

    user.password_hash = hash_password(payload.new_password)
    rec.used = True

    db.add(user)
    db.add(rec)
    db.commit()

    return {"ok": True}