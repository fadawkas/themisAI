# app/routers/documents.py
from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db import models
from app.routers.auth import get_current_user
from app.services.doc_utils import extract_text_from_document  # <- yang benar

UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/documents", tags=["documents"])


def _safe_filename(name: str) -> str:
    name = (name or "document").replace("\\", "/").split("/")[-1]
    name = name.strip() or "document"
    return name


@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current: models.Person = Depends(get_current_user),
):
    saved = []

    for f in files:
        filename = _safe_filename(f.filename)
        dest = os.path.join(UPLOAD_DIR, filename)

        content = await f.read()
        if not content:
            continue

        with open(dest, "wb") as out:
            out.write(content)

        extracted_text: Optional[str] = None
        try:
            extracted_text = extract_text_from_document(dest, max_chars=8000)
        except Exception as e:
            # log aja, jangan fail upload
            print("extract failed:", filename, e)
            extracted_text = None

        doc = models.DocumentStore(
            path=dest,
            doc_type=models.DocTypeEnum.other,
            title=filename,
            extracted_text=extracted_text,
        )

        db.add(doc)
        db.flush()  # supaya doc.id terisi

        saved.append({
            "id": str(doc.id),
            "title": doc.title,
            "doc_type": doc.doc_type,
            "path": doc.path,
            "extracted_text_len": len(extracted_text or ""),
        })

    if not saved:
        raise HTTPException(400, "no files uploaded")

    db.commit()
    return {"saved": saved}
