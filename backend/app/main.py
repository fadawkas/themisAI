# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ThemisAI API")

ALLOWED = ["http://localhost:5173","http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}

from app.routers import auth, chat, documents
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(documents.router)
