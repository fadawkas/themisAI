#!/usr/bin/env python3
import os, re, json, argparse, hashlib, tempfile
from pathlib import Path
from tqdm import tqdm

# extractors
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_text
from pypdf import PdfReader

# ocr
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

HDR_FTR_MAX_LINES = 3  # strip up to top/bottom N lines if repeated

LEGAL_LEVEL_RE = re.compile(
    r'\b(undang-?undang|uu|peraturan pemerintah|pp|peraturan presiden|perpres|perma|sema|peraturan mahkamah agung)\b',
    re.I
)
PASAL_SPLIT = re.compile(r'(?=Pasal\s+\d+[A-Za-z]?)', re.I)
BAB_SPLIT = re.compile(r'(?=BAB\s+[IVXLCDM]+)', re.I)
AMAR_MARK = re.compile(r'\b(AMAR PUTUSAN|MENGADILI)\b', re.I)
PERTIMBANGAN_MARK = re.compile(r'\b(PERTIMBANGAN HUKUM)\b', re.I)

def norm_ws(s: str) -> str:
    s = re.sub(r'-\s*\n\s*', '', s)           # join hyphenated line breaks
    s = re.sub(r'\n{2,}', '\n', s)            # shrink blank lines
    s = re.sub(r'[ \t]+', ' ', s)             # collapse spaces
    return s.strip()

def strip_headers_footers(page_texts):
    """Remove constant header/footer lines across pages."""
    if not page_texts: return ""
    pages = [t.splitlines() for t in page_texts]
    # candidate header/footer by intersection of first/last few lines
    headers = set(pages[0][:HDR_FTR_MAX_LINES]) if pages[0] else set()
    footers = set(pages[0][-HDR_FTR_MAX_LINES:]) if pages[0] else set()
    for lines in pages[1:]:
        headers &= set(lines[:HDR_FTR_MAX_LINES])
        footers &= set(lines[-HDR_FTR_MAX_LINES:])
    cleaned=[]
    for lines in pages:
        # drop matched header/footer
        start = 0
        end = len(lines)
        while start < len(lines) and lines[start] in headers:
            start += 1
        while end > 0 and lines[end-1] in footers:
            end -= 1
        cleaned.append("\n".join(lines[start:end]))
    return "\n".join(cleaned)

def extract_pymupdf(pdf_path):
    doc = fitz.open(pdf_path)
    page_texts=[]
    is_scanned_flags=[]
    for p in doc:
        t = p.get_text("text")
        t = t if t else ""
        page_texts.append(t)
        # if page has very few characters and has images => likely scanned
        is_scanned_flags.append( (len(t.strip()) < 30) and (len(p.get_images())>0) )
    text = strip_headers_footers(page_texts)
    return text, any(is_scanned_flags)

def extract_pdfminer(pdf_path):
    try:
        return pdfminer_text(pdf_path), False
    except Exception:
        return "", False

def extract_pypdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        texts=[]
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return "\n".join(texts), False
    except Exception:
        return "", False

def ocr_pdf(pdf_path, dpi=300, lang="ind"):
    pages = convert_from_path(pdf_path, dpi=dpi)
    texts=[]
    for img in pages:
        if not isinstance(img, Image.Image):
            img = img.convert("RGB")
        txt = pytesseract.image_to_string(img, lang=lang)
        texts.append(txt)
    return "\n".join(texts)

def detect_metadata(title_guess, fulltext):
    title = title_guess or ""
    # doc number/year/level
    level = None
    number = None
    year = None

    mlevel = LEGAL_LEVEL_RE.search(fulltext[:2000])
    if mlevel: level = mlevel.group(1).upper().replace("UNDANG-UNDANG","UU")\
        .replace("PERATURAN PRESIDEN","PERPRES").replace("PERATURAN PEMERINTAH","PP")\
        .replace("PERATURAN MAHKAMAH AGUNG","PERMA")

    mnum = re.search(r'(UU|PP|PERPRES|PERMA|SEMA)\s*(No\.?|Nomor)?\s*([0-9A-Za-z./-]+)', fulltext[:4000], re.I)
    if mnum: number = mnum.group(3)

    myear = re.search(r'Tahun\s*(\d{4})', fulltext[:4000], re.I)
    if myear: year = int(myear.group(1))

    # case metadata
    case_number = None
    court = None
    decision_date = None
    subject = None

    mcase = re.search(r'(Nomor|No\.)\s*[:.]?\s*([0-9A-Za-z/.\-]+)', fulltext, re.I)
    if mcase: case_number = mcase.group(2)

    for k in ["Mahkamah Agung","Pengadilan Tinggi","Pengadilan Negeri","Pengadilan Agama","PTUN","Pengadilan Tata Usaha Negara"]:
        if re.search(rf'\b{k}\b', fulltext, re.I):
            court = k; break

    mdate = re.search(r'(Tanggal\s*Putusan|Diputus\s*pada|Ditetapkan\s*pada)\s*[:.]?\s*([0-9]{1,2}\s+\w+\s+\d{4})', fulltext, re.I)
    if mdate: decision_date = mdate.group(2)

    # classify doc_type by signals
    doc_type = "peraturan" if (level or "undang-undang" in (fulltext.lower())) else "putusan"

    return {
        "title": title,
        "doc_type": doc_type,
        "level": level,
        "number": number,
        "year": year,
        "case_number": case_number,
        "court": court,
        "decision_date": decision_date,
        "subject": subject
    }

def split_legal_blocks(text):
    # prefer legal structure; else fall back to fixed chunks
    blocks = []
    # Priority: Pertimbangan / Amar
    if PERTIMBANGAN_MARK.search(text) or AMAR_MARK.search(text):
        # crude split around these headings
        parts = re.split(r'(PERTIMBANGAN HUKUM|AMAR PUTUSAN|MENGADILI)', text, flags=re.I)
        # re-join pairs [heading, body]
        tmp=[]
        for i in range(0, len(parts), 2):
            seg = " ".join(parts[i:i+2])
            if seg.strip(): tmp.append(seg)
        blocks = tmp
    else:
        # Pasal/BAB based
        parts = PASAL_SPLIT.split(text) if PASAL_SPLIT.search(text) else BAB_SPLIT.split(text)
        blocks = parts if parts else [text]
    return blocks

def window_words(s, max_tokens=450, overlap=80):
    ws = s.split()
    out=[]
    step = max_tokens - overlap
    for i in range(0, len(ws), step):
        chunk = ws[i:i+max_tokens]
        if len(chunk) < 60: break
        out.append(" ".join(chunk))
    return out

def to_chunks(text):
    text = norm_ws(text)
    blocks = split_legal_blocks(text)
    chunks=[]
    for b in blocks:
        chunks += window_words(b, 450, 80)
    return chunks

def process_pdf(pdf_path: str, source_url: str = ""):
    # 1) text extraction fast path
    text, scanned = extract_pymupdf(pdf_path)
    if len(text.strip()) < 100:
        # try alternatives
        txt2, _ = extract_pypdf(pdf_path)
        if len(txt2.strip()) > len(text.strip()):
            text = txt2
        else:
            txt3, _ = extract_pdfminer(pdf_path)
            if len(txt3.strip()) > len(text.strip()):
                text = txt3
    # 2) OCR if needed (or if still too short)
    if scanned or len(text.strip()) < 1000:
        try:
            text_ocr = ocr_pdf(pdf_path, dpi=300, lang="ind")
            if len(text_ocr.strip()) > len(text.strip()):
                text = text_ocr
        except Exception:
            pass

    text = norm_ws(text)
    # 3) metadata
    title_guess = Path(pdf_path).stem.replace("_", " ").replace("-", " ")
    meta = detect_metadata(title_guess, text)

    # 4) chunking
    chunks = to_chunks(text)
    base_id = hashlib.sha1((source_url or pdf_path).encode()).hexdigest()
    output=[]
    for i, ch in enumerate(chunks, 1):
        output.append({
            "id": base_id,
            "chunk_id": f"{i:04d}",
            "text": ch,
            "title": meta["title"],
            "url": source_url,
            "doc_type": meta["doc_type"],
            "number": meta["number"],
            "year": meta["year"],
            "level": meta["level"],
            "case_number": meta["case_number"],
            "decision_date": meta["decision_date"],
            "court": meta["court"],
            "subject": meta["subject"],
            "source": "local-pdf"
        })
    return output

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", required=True, help="Folder berisi PDF")
    ap.add_argument("--out-jsonl", required=True, help="Output JSONL (clean chunks)")
    args = ap.parse_args()

    pdfs = []
    for ext in ("*.pdf",):
        pdfs += list(Path(args.pdf_dir).rglob(ext))

    total=0
    with open(args.out_jsonl, "w", encoding="utf-8") as out:
        for fp in tqdm(pdfs, desc="Processing PDFs"):
            recs = process_pdf(str(fp), source_url=str(fp))
            for r in recs:
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
                total += 1
    print(f"[OK] Wrote {total} chunks -> {args.out_jsonl}")

if __name__ == "__main__":
    main()
