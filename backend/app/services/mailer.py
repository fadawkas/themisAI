# app/services/mailer.py
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

def send_reset_email(to_email: str, token: str) -> None:
    # DEV fallback
    if not SMTP_HOST:
        print(f"[DEV] reset token for {to_email}: {token}")
        return

    link = f"{FRONTEND_URL}/reset-password?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "Reset Password - ThemisAI"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.set_content(
        "Anda meminta reset password.\n\n"
        f"Token: {token}\n"
        f"Link: {link}\n\n"
        "Token berlaku 15 menit. Jika Anda tidak meminta ini, abaikan email ini."
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        if SMTP_USER:
            s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
