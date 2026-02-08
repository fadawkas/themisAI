import json

# Path ke file dataset
FILE_PATH = "QAs_Hukumonline_Clean.json"

# Membaca isi file JSON
with open(FILE_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Menghitung jumlah entri
jumlah_baris = len(data)
print(f"Jumlah baris (row) dalam {FILE_PATH}: {jumlah_baris}")

# (Opsional) Menampilkan beberapa contoh
print("\nContoh 3 entri pertama:")
for i, item in enumerate(data[:3], start=1):
    print(f"{i}. Instruction: {item['instruction'][:80]}...")
    print(f"   Response: {item['response'][:80]}...\n")
