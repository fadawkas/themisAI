# app/services/password_reset.py
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

def make_reset_token() -> str:
    return secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def expires_at(minutes: int = 15) -> datetime:
    return datetime.utcnow() + timedelta(minutes=minutes)
