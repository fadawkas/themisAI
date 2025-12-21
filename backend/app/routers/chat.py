from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.services.pidana_graph_agent import run_pidana_graph
from app.services.doc_utils import extract_text_from_document

from app.db.database import get_db
from app.db import models
from app.routers.auth import get_current_user
from app.db.models import MessageRoleEnum, SessionStatusEnum, DocTypeEnum, DocumentStore

# ---- Pydantic v1/v2 compatibility layer ----
from pydantic import BaseModel, Field
try:
    # Pydantic v2
    from pydantic import ConfigDict  # type: ignore
    _PYDANTIC_V2 = True
except Exception:
    _PYDANTIC_V2 = False

class _BaseModel(BaseModel):
    if _PYDANTIC_V2:
        # v2
        model_config = ConfigDict(from_attributes=True)
    else:
        # v1
        class Config:
            orm_mode = True
# --------------------------------------------

router = APIRouter(prefix="/chat", tags=["chat"])

# =========================
# Schemas (Outputs)
# =========================

class DocumentOut(_BaseModel):
    id: UUID
    path: str
    doc_type: DocTypeEnum
    title: Optional[str]
    uploaded_at: datetime

class ChatAttachmentOut(_BaseModel):
    id: UUID
    message_id: UUID
    document_id: UUID
    caption: Optional[str]
    created_at: datetime
    document: Optional[DocumentOut] = None

class ChatMessageOut(_BaseModel):
    id: UUID
    session_id: UUID
    role: MessageRoleEnum
    content: str
    sent_at: datetime
    reasoning_context: Optional[str] = None
    latency_ms: Optional[int] = None
    attachments: List[ChatAttachmentOut] = Field(default_factory=list)

class ChatSessionOut(_BaseModel):
    id: UUID
    person_id: UUID
    title: Optional[str] = None
    status: SessionStatusEnum
    created_at: datetime
    updated_at: datetime

# =========================
# Schemas (Inputs)
# =========================

class CreateSessionIn(_BaseModel):
    title: Optional[str] = None

class CreateMessageIn(_BaseModel):
    session_id: UUID
    content: str
    role: MessageRoleEnum = MessageRoleEnum.user
    document_ids: Optional[List[UUID]] = None
    captions: Optional[List[Optional[str]]] = None
    latency_ms: Optional[int] = None
    reasoning_context: Optional[str] = None

class UpdateSessionIn(_BaseModel):
    title: Optional[str] = None


# =========================
# Sessions
# =========================

@router.post("/sessions", status_code=status.HTTP_201_CREATED, response_model=ChatSessionOut)
def create_session(
    payload: CreateSessionIn,
    db: Session = Depends(get_db),
    current: models.Person = Depends(get_current_user),
):
    sess = models.ChatSession(person_id=current.id, title=payload.title, status=SessionStatusEnum.active)
    db.add(sess); db.commit(); db.refresh(sess)
    return sess

@router.get("/sessions", response_model=List[ChatSessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    current: models.Person = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status_filter: Optional[SessionStatusEnum] = Query(None, alias="status"),
):
    q = db.query(models.ChatSession).filter(models.ChatSession.person_id == current.id)
    if status_filter:
        q = q.filter(models.ChatSession.status == status_filter)
    return q.order_by(models.ChatSession.created_at.desc()).offset(offset).limit(limit).all()

@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current: models.Person = Depends(get_current_user),
):
    sess = db.get(models.ChatSession, session_id)
    if not sess or sess.person_id != current.id:
        raise HTTPException(404, "session not found")
    return sess

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current: models.Person = Depends(get_current_user),
):
    sess = db.get(models.ChatSession, session_id)
    if not sess or sess.person_id != current.id:
        raise HTTPException(404, "session not found")
    db.delete(sess); db.commit()
    return

# =========================
# Messages
# =========================

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageOut])
def list_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current: models.Person = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    sess = db.get(models.ChatSession, session_id)
    if not sess or sess.person_id != current.id:
        raise HTTPException(404, "session not found")

    msgs = (db.query(models.ChatMessage)
              .filter(models.ChatMessage.session_id == session_id)
              .order_by(models.ChatMessage.sent_at.asc())
              .offset(offset).limit(limit).all())
    # Ensure nested relations are loaded while the DB session is open
    for m in msgs:
        _ = [att.document for att in m.attachments]
    return msgs

@router.post("/messages", status_code=status.HTTP_201_CREATED, response_model=ChatMessageOut)
def create_message(
    payload: CreateMessageIn,
    db: Session = Depends(get_db),
    current: models.Person = Depends(get_current_user),
):
    sess = db.get(models.ChatSession, payload.session_id)
    if not sess or sess.person_id != current.id:
        raise HTTPException(404, "session not found")

    # 1) Simpan pesan user dulu
    user_msg = models.ChatMessage(
        session_id=payload.session_id,
        role=MessageRoleEnum.user,
        content=payload.content,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 2) Ambil teks dari dokumen terlampir (kalau ada)
    extra_context_parts: List[str] = []

    if payload.document_ids:
        docs = (
            db.query(models.DocumentStore)
              .filter(models.DocumentStore.id.in_(payload.document_ids))
              .all()
        )

        # Simpan relasi ke ChatAttachment
        for doc in docs:
            att = models.ChatAttachment(
                message_id=user_msg.id,
                document_id=doc.id,
                caption=None,
            )
            db.add(att)

        db.commit()

        # Ekstrak teksnya
        for doc in docs:
            try:
                txt = extract_text_from_document(doc.path, max_chars=4000)
                if txt:
                    extra_context_parts.append(
                        f"[DOKUMEN: {doc.title or doc.path}]\n{txt}"
                    )
            except Exception as e:
                print("Error extract doc:", doc.path, e)

    extra_context = "\n\n".join(extra_context_parts) if extra_context_parts else None

    # 3) Panggil PIDANA GRAPH AGENT (intent routing + RAG + lawyer rec + dokumen user)
    try:
        answer = run_pidana_graph(payload.content, current, extra_context=extra_context)
        sources = None  # optional, karena pidana_graph_agent tidak mengembalikan sources
    except Exception as e:
        raise HTTPException(500, f"Pidana agent failed: {e}")

    # 4) Simpan jawaban bot
    bot_msg = models.ChatMessage(
        session_id=payload.session_id,
        role=MessageRoleEnum.bot,
        content=answer,
        reasoning_context=sources,
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    return bot_msg



@router.put("/sessions/{session_id}", response_model=ChatSessionOut)
def update_session(
    session_id: UUID,
    payload: UpdateSessionIn,
    db: Session = Depends(get_db),
    current: models.Person = Depends(get_current_user),
):
    sess = db.get(models.ChatSession, session_id)
    if not sess or sess.person_id != current.id:
        raise HTTPException(404, "session not found")

    # apply updates
    if payload.title is not None:
        new_title = payload.title.strip()
        sess.title = new_title or "Untitled"

    # if you allow status updates
    # if payload.status is not None:
    #     sess.status = payload.status

    # ensure updated_at changes if your model doesn't auto-update
    if hasattr(sess, "updated_at"):
        try:
            sess.updated_at = datetime.utcnow()
        except Exception:
            pass

    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess