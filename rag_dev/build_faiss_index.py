import os, re, json, argparse, hashlib, sys
from tqdm import tqdm

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    print("Install sentence-transformers: pip install sentence-transformers", file=sys.stderr); raise

try:
    import faiss, numpy as np
except Exception:
    print("Install faiss-cpu: pip install faiss-cpu", file=sys.stderr); raise

def normalize_ws(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s

def clean_text(s: str) -> str:
    s = s.replace("\x00", " ")
    return normalize_ws(s)

def chunk_text(text: str, max_tokens=450, overlap=80):
    """Whitespace 'token' chunking with overlap. Disable by --no-chunk."""
    words = text.split()
    if not words: return []
    step = max_tokens - overlap
    chunks = []
    for i in range(0, len(words), step):
        chunk = words[i:i+max_tokens]
        if len(chunk) < 50: break
        chunks.append(" ".join(chunk))
    return chunks

def split_legal_blocks(text: str):
    # Prefer split by "Pasal" for UU/PP/Perma etc.
    parts = re.split(r"(?=Pasal\s+\d+[A-Za-z]?)", text, flags=re.I)
    return parts if len(parts) > 1 else [text]

def to_records(obj, do_chunk=True, max_tokens=450, overlap=80):
    """
    Accepts flexible schema. Expects at least:
      - text   (string)  OR  content (string)
    Optional metadata:
      - title, url, doc_type, number, year, level, case_number, decision_date, court, subject, source
    """
    text = obj.get("text") or obj.get("content") or ""
    if not isinstance(text, str): text = str(text)
    text = clean_text(text)
    if not text: return []

    base_meta = {
        "title": obj.get("title",""),
        "url": obj.get("url",""),
        "doc_type": obj.get("doc_type",""),
        "number": obj.get("number",""),
        "year": obj.get("year",""),
        "level": obj.get("level",""),
        "case_number": obj.get("case_number",""),
        "decision_date": obj.get("decision_date",""),
        "court": obj.get("court",""),
        "subject": obj.get("subject",""),
        "source": obj.get("source",""),
    }

    base_id = obj.get("id") or hashlib.sha1((base_meta["title"] + base_meta["url"] + text[:200]).encode()).hexdigest()

    if not do_chunk:
        return [{
            "id": base_id, "chunk_id": "0001", "text": text, **base_meta
        }]

    # legal-aware split
    blocks = split_legal_blocks(text)
    chunks=[]
    for b in blocks:
        chunks.extend(chunk_text(b, max_tokens=max_tokens, overlap=overlap))

    recs=[]
    for i, ch in enumerate(chunks, 1):
        recs.append({"id": base_id, "chunk_id": f"{i:04d}", "text": ch, **base_meta})
    return recs

def read_jsonl(jsonl_path, max_docs=0):
    with open(jsonl_path, "r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f, 1):
            if max_docs and i > max_docs: break
            try:
                yield json.loads(line)
            except:
                yield {"text": line.strip()}

def dedup(records):
    seen=set(); out=[]
    for r in records:
        key = hashlib.sha1(r["text"].lower().encode()).hexdigest()
        if key in seen: continue
        seen.add(key); out.append(r)
    return out

def build_embeddings(records, model_name):
    model = SentenceTransformer(model_name)
    texts = [r["text"] for r in records]
    embs = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    return np.asarray(embs, dtype="float32")

def build_faiss(embs, out_path):
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine if embeddings normalized
    index.add(embs)
    faiss.write_index(index, out_path)
    return index

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True, help="Path to UU_docs.jsonl")
    ap.add_argument("--out-dir", required=True, help="Where to save index & metadata")
    ap.add_argument("--embed-model", default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    ap.add_argument("--max-docs", type=int, default=0, help="limit for quick test")
    ap.add_argument("--no-chunk", action="store_true", help="store whole doc as one chunk")
    ap.add_argument("--max-tokens", type=int, default=450)
    ap.add_argument("--overlap", type=int, default=80)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # 1) load + convert to per-chunk records
    all_chunks=[]
    for obj in tqdm(read_jsonl(args.jsonl, max_docs=args.max_docs), desc="Loading"):
        all_chunks.extend(to_records(
            obj,
            do_chunk=not args.no_chunk,
            max_tokens=args.max_tokens,
            overlap=args.overlap
        ))

    # 2) dedup
    all_chunks = dedup(all_chunks)

    # 3) save metadata
    meta_path = os.path.join(args.out_dir, "metadata.jsonl")
    with open(meta_path, "w", encoding="utf-8") as f:
        for r in all_chunks:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"chunks: {len(all_chunks)} → {meta_path}")

    # 4) embeddings
    embs = build_embeddings(all_chunks, args.embed_model)

    # 5) faiss
    index_path = os.path.join(args.out_dir, "index.faiss")
    build_faiss(embs, index_path)

    print(f"index: {index_path}")
    print(f"done.")

if __name__ == "__main__":
    main()
