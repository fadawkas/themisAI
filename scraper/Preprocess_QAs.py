import json
import google.generativeai as genai
import time

# === KONFIGURASI ===
INPUT_FILE = 'datasets/QAs_Hukumonline_Clean.json'   # File JSON input 
OUTPUT_FILE = 'datasets/QAs_Hukumonline_Clean_GEN.json'  # Output file
MAX_ITEMS = 250

# === SETUP GEMINI ===
genai.configure(api_key="")

model = genai.GenerativeModel('gemini-1.5-pro')

# === CLEANING FUNCTION ===
def clean_text_with_gemini(text):
    prompt = f"""Tolong bersihkan dan rapihkan teks berikut ini:
- Gabungkan kata yang patah
- Hapus karakter aneh seperti [ ] dan footnotes
- Hilangkan tanggal-tanggal tanpa konteks
- Berikan kesimpulan jawaban di bagian bawah sebelum "Dasar Hukum"
- Pastikan penulisan sama detailnya dengan jawaban asli
- Pertahankan bagian "Dasar Hukum" dan "Referensi"
- Jadikan jawaban lebih natural dan profesional, seolah-olah ditulis ulang oleh ahli hukum.

Teks:
{text}
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error from Gemini API: {e}")
        return text  # fallback: return original

# === BACA DATASET ===
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# === PROSES DAN CLEANING ===
cleaned_dataset = []
total = MAX_ITEMS if MAX_ITEMS else len(dataset)

for i, item in enumerate(dataset[:total], 1):
    print(f"🔄 Memproses data #{i}...")
    cleaned_response = clean_text_with_gemini(item['response'])

    cleaned_dataset.append({
        "instruction": item['instruction'],
        "response": cleaned_response
    })

    time.sleep(2) 

# === SIMPAN HASIL ===
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(cleaned_dataset, f, ensure_ascii=False, indent=2)

print(f"\nCleaning selesai! Total {len(cleaned_dataset)} records disimpan ke {OUTPUT_FILE}")

