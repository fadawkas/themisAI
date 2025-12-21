# app/services/pidana_graph_agent.py

from __future__ import annotations
from typing import TypedDict, Literal, Optional, Any

import os
import requests

from langgraph.graph import StateGraph, END

from app.services.rag_engine import ask_vllm
from app.services.lawyer_rec import recommend_lawyers_for_user, format_lawyer_recommendation_text, build_user_address_from_db


# ============================
# 1. STATE UNTUK LANGGRAPH
# ============================

class AgentState(TypedDict):
    question: str
    intent: Optional[str]
    answer: Optional[str]
    user: Any
    extra_context: Optional[str]  


# ============================
# 2. INTENT CLASSIFIER (ROUTER)
# ============================

VLLM_BASE = os.getenv("VLLM_BASE")
INTENT_MODEL = os.getenv("INTENT_MODEL", os.getenv("MODEL_NAME", "google/gemma-3-4b-it"))

INTENT_SYSTEM_PROMPT = """
Kamu adalah classifier untuk pesan pengguna.

Klasifikasikan pesan ke dalam SATU dari label berikut:
- PIDANA_QA         : jika isi pesan bertanya tentang hukum pidana Indonesia
                      (KUHP, KUHAP, laporan pidana, delik, ancaman pidana, penahanan, dsb.)
- LAWYER_REC        : Gunakan label ini jika pesan pengguna:
                        - meminta rekomendasi pengacara
                        - menyebut kata "pengacara", "advokat", "kuasa hukum", "lawyer"
                        - bertanya bagaimana mendapatkan bantuan pengacara
                        - meminta pendampingan hukum
                        - menulis "rekomendasi pengacara", "butuh advokat", "cari lawyer", dll.

                        PERATURAN KERAS:
                        Jika pesan MENGANDUNG salah satu kata:
                        ["pengacara", "advokat", "lawyer", "kuasa hukum"]
                        → SELALU pilih LAWYER_REC.
- SAPA              : jika pesan hanya berupa sapaan atau pertanyaan ringan seperti
                      "halo", "apa fungsi kamu", "kamu siapa", tanpa isi hukum yang spesifik.
- NON_PIDANA        : jika isi pesan di luar hukum pidana, misalnya:
                      hukum perdata, waris, pajak, bisnis, pernikahan,
                      atau topik non-hukum (curhat, coding, matematika, dll).

Batasan:
- Jawab HANYA dengan salah satu label: PIDANA_QA, LAWYER_REC, SAPA, NON_PIDANA
- Jangan menambahkan penjelasan lain.
"""

def classify_intent(state: AgentState) -> AgentState:
    question = state["question"]
    q_lower = question.lower()

    # 1) RULE-BASED: hard keyword untuk LAWYER_REC
    lawyer_keywords = ["pengacara", "advokat", "lawyer", "kuasa hukum"]
    if any(kw in q_lower for kw in lawyer_keywords):
        return {**state, "intent": "LAWYER_REC"}

    # 2) Kalau tidak kena rule, baru pakai LLM
    payload = {
        "model": INTENT_MODEL,
        "messages": [
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "temperature": 0.0,
        "max_tokens": 4,
    }

    resp = requests.post(f"{VLLM_BASE}/v1/chat/completions", json=payload, timeout=60)
    resp.raise_for_status()
    label = resp.json()["choices"][0]["message"]["content"].strip().upper()

    # Safety net: kalau LLM ngaco, paksa NON_PIDANA
    if label not in {"PIDANA_QA", "LAWYER_REC", "SAPA", "NON_PIDANA"}:
        label = "NON_PIDANA"

    return {**state, "intent": label}


# ============================
# 3. HANDLER NODE
# ============================

def handle_sapa(state: AgentState) -> AgentState:
    ans = (
        "Halo, saya ThemisAI, asisten hukum pidana Indonesia.\n\n"
        "Saya dirancang untuk menjawab pertanyaan seputar hukum pidana "
        "(KUHP, KUHAP, proses penyidikan, penuntutan, jenis delik, ancaman pidana, dsb.) "
        "dan dapat membantu memberikan rekomendasi pengacara pidana.\n\n"
        "Silakan ajukan pertanyaan terkait hukum pidana yang ingin Anda ketahui."
    )
    return {**state, "answer": ans}


def handle_non_pidana(state: AgentState) -> AgentState:
    ans = (
        "Maaf, saya hanya dapat membantu menjawab pertanyaan terkait hukum pidana di Indonesia.\n\n"
        "Topik seperti hukum perdata, pajak, bisnis, waris, pernikahan, maupun "
        "pertanyaan non-hukum tidak termasuk dalam cakupan saya.\n\n"
        "Silakan ajukan pertanyaan lain yang secara jelas berkaitan dengan hukum pidana "
    )
    return {**state, "answer": ans}


def handle_pidana_qa(state: AgentState) -> AgentState:
    question = state["question"]
    extra_context = state.get("extra_context")

    
    answer, sources = ask_vllm(question, extra_context=extra_context)
    return {**state, "answer": answer}


def handle_lawyer_rec(state: AgentState) -> AgentState:
    """
    Handler rekomendasi pengacara PIDANA berbasis:
    - deskripsi kasus = pertanyaan user (state["question"])
    - lokasi = alamat user di DB (tabel Address via models.Person.address)
    """
    q = state["question"]
    user = state.get("user")

    # Kalau belum ada user di state (fallback safety)
    if not user:
        ans = (
            "Untuk memberikan rekomendasi pengacara pidana, saya perlu mengetahui profil "
            "dan alamat Anda dari sistem.\n\n"
            "Saat ini data profil belum terdeteksi. Silakan pastikan Anda sudah login dan "
            "mengisi alamat lengkap di menu profil."
        )
        return {**state, "answer": ans}
    
    addr_str = build_user_address_from_db(user)
    print("DEBUG user address for geocode:", addr_str)

    # 1) panggil core rekomendasi berbasis alamat user di DB
    results = recommend_lawyers_for_user(
        user=user,
        case_description=q,
        top_k=3,
        search_pool_k=50,
    )

    # 2) format alamat user sebagai teks lokasi (untuk ditampilkan)
    location_str = build_user_address_from_db(user) or "(alamat tidak lengkap)"

    # 3) format hasil ke teks yang rapi
    formatted = format_lawyer_recommendation_text(
        location_str=location_str,
        case_description=q,
        results=results,
    )

    return {**state, "answer": formatted}


# ============================
# 4. ROUTER UNTUK GRAPH
# ============================

def route_from_intent(state: AgentState) -> str:
    intent = state.get("intent", "NON_PIDANA")
    if intent == "PIDANA_QA":
        return "handle_pidana_qa"
    if intent == "LAWYER_REC":
        return "handle_lawyer_rec"
    if intent == "SAPA":
        return "handle_sapa"
    return "handle_non_pidana"


# ============================
# 5. BANGUN GRAPH
# ============================

builder = StateGraph(AgentState)

builder.add_node("classify_intent", classify_intent)
builder.add_node("handle_sapa", handle_sapa)
builder.add_node("handle_non_pidana", handle_non_pidana)
builder.add_node("handle_pidana_qa", handle_pidana_qa)
builder.add_node("handle_lawyer_rec", handle_lawyer_rec)

builder.set_entry_point("classify_intent")

builder.add_conditional_edges(
    "classify_intent",
    route_from_intent,
    {
        "handle_sapa": "handle_sapa",
        "handle_non_pidana": "handle_non_pidana",
        "handle_pidana_qa": "handle_pidana_qa",
        "handle_lawyer_rec": "handle_lawyer_rec",
    },
)

# Semua handler → END
builder.add_edge("handle_sapa", END)
builder.add_edge("handle_non_pidana", END)
builder.add_edge("handle_pidana_qa", END)
builder.add_edge("handle_lawyer_rec", END)

pidana_graph_app = builder.compile()


# ============================
# 6. FUNGSI ENTRYPOINT UNTUK FASTAPI
# ============================

def run_pidana_graph(question: str, user, extra_context: Optional[str] = None) -> str:
    """
    Fungsi pembungkus yang dipanggil dari router /chat.
    `user` = instance models.Person (current user dari FastAPI)
    """
    result = pidana_graph_app.invoke({
        "question": question,
        "intent": None,
        "answer": None,
        "user": user,
        "extra_context": extra_context,
    })
    return result["answer"] or ""

