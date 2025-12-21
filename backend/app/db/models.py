from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
import enum
import uuid

from sqlalchemy import (
    String, Integer, Date, DateTime, Enum, ForeignKey, Text,
    UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import Base

# Enums
class GenderEnum(str, enum.Enum): male="male"; female="female"; unknown="unknown"
class SessionStatusEnum(str, enum.Enum): active="active"; archived="archived"; closed="closed"
class MessageRoleEnum(str, enum.Enum): user="user"; bot="bot"; system="system"
class DocTypeEnum(str, enum.Enum): statute="statute"; case_law="case_law"; regulation="regulation"; other="other"

class Person(Base):
    __tablename__ = "person"
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32))
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    address: Mapped["Address"] = relationship(back_populates="person", uselist=False, cascade="all, delete-orphan")
    chat_sessions: Mapped[List["ChatSession"]] = relationship(back_populates="person", cascade="all, delete-orphan")

class Address(Base):
    __tablename__ = "address"
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id", ondelete="CASCADE"), unique=True, nullable=False)
    line1: Mapped[Optional[str]] = mapped_column(String(200))
    city: Mapped[Optional[str]] = mapped_column(String(120))
    state: Mapped[Optional[str]] = mapped_column(String(120))
    postal_code: Mapped[Optional[str]] = mapped_column(String(24))
    country: Mapped[Optional[str]] = mapped_column(String(120))

    person: Mapped[Person] = relationship(back_populates="address")

class ChatSession(Base):
    __tablename__ = "chat_session"
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[SessionStatusEnum] = mapped_column(Enum(SessionStatusEnum), default=SessionStatusEnum.active, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    person: Mapped[Person] = relationship(back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_chat_session_person_status", "person_id", "status"),
    )

class ChatMessage(Base):
    __tablename__ = "chat_message"
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_session.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[MessageRoleEnum] = mapped_column(Enum(MessageRoleEnum), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    reasoning_context: Mapped[Optional[str]] = mapped_column(Text)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)

    session: Mapped[ChatSession] = relationship(back_populates="messages")
    attachments: Mapped[List["ChatAttachment"]] = relationship(back_populates="message", cascade="all, delete-orphan")

class DocumentStore(Base):
    __tablename__ = "document_store"
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    doc_type: Mapped[DocTypeEnum] = mapped_column(Enum(DocTypeEnum), default=DocTypeEnum.other, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    attachments: Mapped[List["ChatAttachment"]] = relationship(back_populates="document")

class ChatAttachment(Base):
    __tablename__ = "chat_attachment"
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_message.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_store.id", ondelete="CASCADE"), nullable=False, index=True)
    caption: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    message: Mapped[ChatMessage] = relationship(back_populates="attachments")
    document: Mapped[DocumentStore] = relationship(back_populates="attachments")

    __table_args__ = (
        UniqueConstraint("message_id", "document_id", name="uq_msg_doc_once"),
    )
