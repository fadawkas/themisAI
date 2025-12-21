import json
import time
import requests
from pathlib import Path
from tqdm import tqdm

INPUT_FILE = Path("lawyers_ppkhi_jakarta_detailed_addr.jsonl")
OUTPUT_FILE = Path("lawyers_with_geo.jsonl")

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"

SESSION = requests.Session()
HEADERS = {
    "User-Agent": "ppkhi-lawyer-finder/1.0 (oemarkid@gmail.com)",
}

def nominatim_search_freeform(query: str):
    """
    Call Nominatim /search API (free-form query)
    Docs: https://nominatim.org/release-docs/develop/api/Search/#search-queries :contentReference[oaicite:2]{index=2}
    """
    if not query:
        return None, None

    params = {
        "q": query,
        "format": "jsonv2",  
        "limit": 1,
        "addressdetails": 0,
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
            return None, None

        first = data[0]
        return float(first["lat"]), float(first["lon"])
    except Exception as e:
        print(f"[WARN] Nominatim error for '{query}': {e}")
        return None, None


def choose_address(record: dict) -> str | None:
    """
    Pick the most useful address field for a lawyer.
    Adjust this list to match your JSONL schema.
    """
    candidates = [
        "alamat_kantor",
        "alamat",
        "lokasi",
        "domisili",
        "full_address",
    ]
    for key in candidates:
        val = record.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} not found")

    records = []
    with INPUT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    print(f"Loaded {len(records)} lawyers")

    enriched = []
    for rec in tqdm(records, desc="Geocoding lawyers with Nominatim"):
        addr = choose_address(rec)

        query = addr

        lat, lon = nominatim_search_freeform(query)
        time.sleep(1.0)

        rec["latitude"] = lat
        rec["longitude"] = lon
        rec["geocode_query"] = query
        enriched.append(rec)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for rec in enriched:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Saved lawyers with lat/lon → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
