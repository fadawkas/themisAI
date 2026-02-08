import os
import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ========= CONFIG =========

BASE_DIR = Path(__file__).resolve().parent

# input: lawyers_with_geo.jsonl (punya field: name, alamat, specialitas, text, lat, lon, dst.)
LAWYER_JSONL = Path(os.getenv("LAWYER_JSONL", BASE_DIR / "lawyers_with_geo.jsonl"))

# output: folder lawyers/ (index + meta)
LAWYER_INDEX_PATH = Path(
    os.getenv("LAWYER_INDEX_PATH", BASE_DIR / "lawyers/index_lawyers.faiss")
)
LAWYER_META_PATH = Path(
    os.getenv("LAWYER_META_PATH", BASE_DIR / "lawyers/lawyers_meta.jsonl")
)

EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)


def build_lawyer_text(rec: dict) -> str:
    """
    Teks yang dipakai untuk embedding.
    Fokus ke specialitas + ringkasan teks.
    """

    # specialitas: list of string
    spec = rec.get("specialitas") or []
    if isinstance(spec, list):
        spec_text = ", ".join(spec)
    else:
        spec_text = str(spec)

    # kalau di JSONL sudah ada field "text" yang lengkap, kita pakai juga
    base_text = rec.get("text") or ""

    name = rec.get("name") or rec.get("nama") or ""
    alamat = rec.get("alamat") or rec.get("alamat_kantor") or ""
    status = rec.get("status") or ""

    parts = [
        name,
        f"Status: {status}" if status else "",
        f"Alamat: {alamat}" if alamat else "",
        f"Spesialisasi: {spec_text}" if spec_text else "",
        base_text,
    ]
    return " | ".join(p for p in parts if p)


def main():
    if not LAWYER_JSONL.exists():
        raise FileNotFoundError(f"{LAWYER_JSONL} not found")

    LAWYER_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAWYER_META_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("[*] Loading lawyers JSONL...")
    lawyers = []
    with LAWYER_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            lawyers.append(obj)

    print(f"[*] Loaded {len(lawyers)} lawyers")

    # siapkan teks untuk embedding
    texts = [build_lawyer_text(rec) for rec in lawyers]

    # simpan metadata apa adanya (supaya lawyer_rec.py bisa pakai field-field tersebut)
    with LAWYER_META_PATH.open("w", encoding="utf-8") as f:
        for rec, text in zip(lawyers, texts):
            # pastikan field "text" ada dan konsisten
            rec_out = dict(rec)
            rec_out["text"] = text
            f.write(json.dumps(rec_out, ensure_ascii=False) + "\n")

    print("[*] Saved metadata to", LAWYER_META_PATH)

    # build embeddings
    print("[*] Encoding lawyers...")
    model = SentenceTransformer(EMBED_MODEL)
    emb = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    faiss.normalize_L2(emb)

    # build faiss index
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)

    print("[*] Saving FAISS index...")
    faiss.write_index(index, str(LAWYER_INDEX_PATH))

    print("Done.")
    print("Index:", LAWYER_INDEX_PATH)
    print("Meta :", LAWYER_META_PATH)


if __name__ == "__main__":
    main()
