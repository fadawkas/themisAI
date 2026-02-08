# app/services/lawyer_rec.py

import os
import json
from math import radians, sin, cos, sqrt, atan2
from pathlib import Path
from typing import List, Dict, Any, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import requests


# ============================
# Nominatim Geocode (lokasi user)
# ============================

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
SESSION = requests.Session()
HEADERS = {
    "User-Agent": "ppkhi-lawyer-recommender/1.0 (oemarkid@gmail.com)",
}


def geocode_user_location(address: str) -> Optional[Dict[str, Any]]:
    """
    Geocode lokasi user menggunakan Nominatim (free-form address).
    Mengembalikan dict {lat, lon, display_name} atau None jika gagal.
    """
    if not address:
        return None

    params = {
        "q": address,
        "format": "jsonv2",
        "limit": 1,
        "countrycodes": "id",
    }

    try:
        resp = SESSION.get(
            f"{NOMINATIM_BASE}/search",
            params=params,
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None

        first = data[0]
        return {
            "lat": float(first["lat"]),
            "lon": float(first["lon"]),
            "display_name": first.get("display_name"),
        }
    except Exception as e:
        print("Geocode error:", e)
        return None


# ============================
# CONFIG – PENTING UNTUK DOCKER
# ============================

BASE_DIR = Path(__file__).resolve().parent

# Bisa di-override dari ENV, default ke /app/app/db/lawyers (mount di docker-compose)
LAWYER_INDEX_DIR = Path(
    os.getenv("LAWYER_INDEX_DIR", "/app/app/db/lawyers")
)

LAWYER_INDEX_PATH = LAWYER_INDEX_DIR / "index_lawyers.faiss"
LAWYER_META_PATH = LAWYER_INDEX_DIR / "lawyers_meta.jsonl"

EMBED_MODEL = os.getenv(
    "LAWYER_EMBED_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

# Bobot kombinasi semantik vs jarak (0.6 = 60% semantik, 40% jarak)
ALPHA_SEMANTIC = float(os.getenv("LAWYER_ALPHA_SEMANTIC", "0.6"))


# ============================
# LOAD INDEX & METADATA
# ============================

if not LAWYER_INDEX_PATH.exists():
    raise RuntimeError(f"Lawyer index not found: {LAWYER_INDEX_PATH}")

if not LAWYER_META_PATH.exists():
    raise RuntimeError(f"Lawyer metadata not found: {LAWYER_META_PATH}")

_index = faiss.read_index(str(LAWYER_INDEX_PATH))
_encoder = SentenceTransformer(EMBED_MODEL)

_lawyers: List[Dict[str, Any]] = []
with LAWYER_META_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        _lawyers.append(json.loads(line))

# Ambil lat/lon pengacara (dtype=object karena bisa None)
_lawyer_latlon = []
for rec in _lawyers:
    lat = rec.get("latitude")
    lon = rec.get("longitude")
    if lat is None or lon is None:
        _lawyer_latlon.append((None, None))
    else:
        _lawyer_latlon.append((float(lat), float(lon)))

_lawyer_latlon = np.array(_lawyer_latlon, dtype=object)


# ============================
# Helpers
# ============================

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Hitung jarak permukaan bumi (km) antara dua titik lat/lon.
    """
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def embed_case(text: str) -> np.ndarray:
    emb = _encoder.encode([text], convert_to_numpy=True)
    faiss.normalize_L2(emb)
    return emb.astype("float32")


def _semantic_search(query: str, top_k: int = 50):
    q = embed_case(query)
    D, I = _index.search(q, top_k)
    return I[0], D[0]


# ============================
# Core Rekomendasi (lokasi = string)
# ============================

def recommend_lawyers(
    user_location: str,
    case_description: str,
    top_k: int = 3,
    search_pool_k: int = 50,
) -> Any:
    """
    Rekomendasi pengacara (versi core):
    - geocode lokasi user (Nominatim)
    - semantic search kasus vs spesialisasi pengacara
    - gabungkan skor semantik + jarak (Haversine)
    """

    # 1) Geocode lokasi user
    geo = geocode_user_location(user_location)
    if not geo:
        return {"error": "Failed to geocode user location"}

    user_lat = geo["lat"]
    user_lon = geo["lon"]

    # 2) Semantic ranking
    idxs, sims = _semantic_search(case_description, top_k=search_pool_k)

    # 3) Combine semantic + distance
    results = []
    for idx, sim in zip(idxs, sims):
        if idx < 0:
            continue

        rec = _lawyers[idx]
        lawyer_lat, lawyer_lon = _lawyer_latlon[idx]

        # convert inner-product [-1,1] → [0,1]
        semantic_score = (float(sim) + 1) / 2

        if lawyer_lat is None or lawyer_lon is None:
            distance_km = None
            distance_score = 0.0
        else:
            distance_km = haversine_km(user_lat, user_lon, lawyer_lat, lawyer_lon)
            distance_score = 1 / (1 + distance_km)

        final_score = (
            ALPHA_SEMANTIC * semantic_score +
            (1 - ALPHA_SEMANTIC) * distance_score
        )

        results.append({
            "name": rec.get("name"),
            "alamat_kantor": rec.get("alamat_kantor") or rec.get("alamat"),
            "specialitas": rec.get("specialitas") or rec.get("spesialisasi"),
            "latitude": lawyer_lat,
            "longitude": lawyer_lon,
            "distance_km": distance_km,
            "semantic_score": semantic_score,
            "final_score": final_score,
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:top_k]


# ============================
# Versi untuk dipanggil dari Agent (pakai user DB)
# ============================


def build_user_address_from_db(user) -> Optional[str]:
    """
    Mengambil alamat user dengan hanya menggunakan line1 dan city.
    Lebih sederhana dan biasanya lebih stabil untuk geocode Nominatim.
    """
    addr = getattr(user, "address", None)
    if not addr:
        return None

    line1 = getattr(addr, "line1", None)
    city = getattr(addr, "city", None)

    if not city:
        return None  # minimal harus ada kota

    # Jika line1 kosong, pakai kota saja
    if not line1:
        return city.strip()

    # Jika dua-duanya ada
    return f"{line1.strip()}, {city.strip()}"



def recommend_lawyers_for_user(
    user,              # models.Person
    case_description: str,
    top_k: int = 3,
    search_pool_k: int = 50,
) -> Any:
    """
    Wrapper utama yang dipakai oleh agent / endpoint:
    - Ambil lokasi user dari DB (tabel Address)
    - Panggil core recommend_lawyers()
    """
    user_location = build_user_address_from_db(user)
    if not user_location:
        return {
            "error": "Alamat Anda belum lengkap. Mohon lengkapi alamat di profil."
        }

    return recommend_lawyers(
        user_location=user_location,
        case_description=case_description,
        top_k=top_k,
        search_pool_k=search_pool_k,
    )


# ============================
# Util: formatting untuk jawaban agent (opsional)
# ============================

def format_lawyer_recommendation_text(
    location_str: str,
    case_description: str,
    results: Any,
) -> str:
    """
    Format hasil rekomendasi pengacara dengan tampilan yang lebih rapi dan profesional.
    """
    if isinstance(results, dict) and results.get("error"):
        return f"Gagal mendapatkan rekomendasi pengacara: {results['error']}"

    if not results:
        return (
            "Maaf, belum ditemukan pengacara pidana yang relevan untuk lokasi dan kasus Anda "
            "berdasarkan data yang tersedia."
        )

    lines = []

    # HEADER
    lines.append(f"**Lokasi Anda terdeteksi:**\n{location_str}\n")
    lines.append(f"**Deskripsi Kasus:**\n{case_description}\n")
    lines.append("**Rekomendasi Pengacara Pidana**")
    lines.append("Berdasarkan lokasi & kecocokan spesialisasi, berikut pengacara yang paling relevan:\n")

    # LIST PENGACARA
    for i, r in enumerate(results, start=1):
        spes = r.get("specialitas") or []
        spes_str = "\n".join([f"- {s}" for s in spes])

        jarak = (
            f"{r['distance_km']:.2f} km"
            if r.get("distance_km") is not None
            else "Tidak diketahui"
        )

        lines.append(
            f"---\n"
            f"### **{i}. {r.get('name','(tanpa nama)')}**\n"
            f"*Jarak:* {jarak}\n\n"
            f"*Spesialisasi:*\n{spes_str}\n\n"
            f"*Alamat:* {r.get('alamat_kantor','-')}\n\n"
            f"*Skor Sistem:* {r.get('final_score', 0):.3f}\n"
        )

    lines.append("---\n")
    lines.append(
        "Skor dihitung menggunakan metode *weighted scoring* dengan menggabungkan "
        "jarak lokasi dan kecocokan spesialisasi. Semakin tinggi skor, semakin relevan "
        "pengacara untuk direkomendasikan.\n"
    )    

    return "\n".join(lines)
