# app/services/rag_engine.py
import os, json, faiss, requests
from sentence_transformers import SentenceTransformer

# Load FAISS index + metadata once at startup
VLLM_BASE = os.getenv("VLLM_BASE")
INDEX_DIR = os.getenv("INDEX_DIR", "/app/app/db/index_uu")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
TOP_K = int(os.getenv("TOP_K", "2"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))


SYSTEM_PROMPT = """
Anda adalah asisten hukum profesional bergaya penulisan seperti artikel di Hukumonline.
Tulislah jawaban dengan struktur analitis, lengkap, dan informatif, mencakup:
1. Pendahuluan singkat konteks hukum.
2. Penjelasan isi pasal/ayat yang relevan (kutip langsung jika ada).
3. Penjabaran logika hukum dan interpretasinya.
4. Poin-poin penting atau langkah hukum jika diperlukan.
5. Bagian 'Dasar Hukum' di akhir, mencantumkan peraturan yang dikutip.
6. Akhiri dengan kalimat sopan seperti 'Demikian penjelasan kami, semoga bermanfaat.'

Gaya bahasa:
- Gunakan bahasa hukum formal, sistematis, dan mudah dipahami masyarakat umum.
- Hindari opini pribadi atau spekulasi.
- Jika konteks tidak ditemukan, jawab: "Berdasarkan konteks yang tersedia, informasi terkait belum ditemukan."
"""

USER_TEMPLATE = """PERTANYAAN:
{question}

KONTEKS TERKAIT:
{context}

Sumber:
{sources}

Instruksi:
- Susun jawaban menyerupai artikel hukum online yang lengkap dan berurutan.
- Gunakan format berikut (bisa disesuaikan):

PENJELASAN:
(berikan uraian dan analisis hukum berdasarkan konteks)

DASAR HUKUM:
- Sebutkan UU, Pasal, dan peraturan yang relevan secara bernomor.

CATATAN:
Seluruh informasi hukum ini bersifat edukatif dan umum, bukan nasihat hukum spesifik.
Untuk kasus konkret, konsultasikan kepada advokat atau konsultan hukum berizin.
"""


index = faiss.read_index(os.path.join(INDEX_DIR, "index.faiss"))
meta = [json.loads(l) for l in open(os.path.join(INDEX_DIR, "metadata.jsonl"), "r")]
encoder = SentenceTransformer(EMBED_MODEL)

def search(query, k=TOP_K):
    qv = encoder.encode([query], normalize_embeddings=True).astype("float32")
    D, I = index.search(qv, k)
    hits = [meta[i] for i in I[0] if i < len(meta)]
    if not hits:
        return [{"text": "Tidak ditemukan konteks hukum yang relevan.", "title": "—", "doc_type": "—", "url": ""}]
    return hits


def build_context(hits):
    blocks, sources = [], []
    for rank, h in enumerate(hits, 1):
        blocks.append(f"[{rank}] ({h.get('doc_type','')}) {h['text']}")
        sources.append(f"[S{rank}] {h.get('title','')} — {h.get('url','')}")
    return "\n\n".join(blocks), "\n".join(sources)

def ask_vllm(question: str, extra_context: str | None = None):
    hits = search(question)
    base_context, sources = build_context(hits)

    if extra_context:
        extra_context = extra_context[:8000]
        full_context = (
            base_context
            + "\n\n[DOKUMEN PENGGUNA]\n"
            + extra_context
        )
        max_tokens = 1200
    else:
        full_context = base_context
        max_tokens = MAX_TOKENS

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(
                question=question, context=full_context, sources=sources)}
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    r = requests.post(f"{VLLM_BASE}/v1/chat/completions", json=payload, timeout=300)
    r.raise_for_status()
    reply = r.json()["choices"][0]["message"]["content"]
    return reply, sources
