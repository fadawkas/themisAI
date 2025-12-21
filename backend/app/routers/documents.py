import os
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.routers.auth import get_current_user
from app.core.config import settings


UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("")
def create_document(path: str, doc_type: models.DocTypeEnum = models.DocTypeEnum.other, title: Optional[str] = None, db: Session = Depends(get_db), current=Depends(get_current_user)):
    doc = models.DocumentStore(path=path, doc_type=doc_type, title=title)
    db.add(doc); db.commit(); db.refresh(doc)
    return doc

@router.post("/upload")
async def upload(files: List[UploadFile] = File(...), db: Session = Depends(get_db), current=Depends(get_current_user)):
    saved = []
    for f in files:
        dest = os.path.join(UPLOAD_DIR, f.filename)
        content = await f.read()
        with open(dest, "wb") as out: out.write(content)
        doc = models.DocumentStore(path=dest, doc_type=models.DocTypeEnum.other, title=f.filename)
        db.add(doc); db.flush()
        saved.append(doc)
    db.commit()
    return saved
