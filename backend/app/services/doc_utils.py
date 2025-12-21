import os
from pathlib import Path
from typing import List

from docx import Document as DocxDocument
import PyPDF2


def extract_text_from_docx(path: str) -> str:
    doc = DocxDocument(path)
    parts = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def extract_text_from_pdf(path: str) -> str:
    text_parts = []
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            t = page.extract_text() or ""
            t = t.strip()
            if t:
                text_parts.append(t)
    return "\n\n".join(text_parts)


def extract_text_from_document(path: str, max_chars: int = 8000) -> str:
    """
    Wrapper: deteksi ekstensi dan ekstrak teks, batasi panjang (biar nggak jebol token).
    """
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix in [".docx"]:
        txt = extract_text_from_docx(str(p))
    elif suffix in [".pdf"]:
        txt = extract_text_from_pdf(str(p))
    else:
        # fallback: treat as plain text
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            txt = ""

    txt = txt.strip()
    if len(txt) > max_chars:
        txt = txt[:max_chars] + "\n\n...[dipotong, dokumen terlalu panjang]"

    return txt
