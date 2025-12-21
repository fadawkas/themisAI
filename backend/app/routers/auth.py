from datetime import date  # <- add this import

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.db.database import get_db
from app.db import models
from app.core.security import hash_password, verify_password, create_access_token
from app.core.security import maybe_upgrade_hash

from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")


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
