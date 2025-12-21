import requests
from bs4 import BeautifulSoup
import os
import time
from tqdm import tqdm

# === CONFIGURATION ===
BASE_URL = "https://www.hukumonline.com/klinik/pidana/"
OUTPUT_FILE = "URLs_QA.txt"
NUM_PAGES = 50         # Mau ambil berapa halaman (misal 20 halaman)
DELAY_SECONDS = 1      # Delay antar page untuk sopan scraping

urls = []

print(f"Crawling konsultasi kategori PIDANA dari {NUM_PAGES} halaman...")

for page in tqdm(range(1, NUM_PAGES + 1), desc="Crawling Halaman PIDANA"):
    try:
        page_url = f"{BASE_URL}page/{page}/"
        response = requests.get(page_url, timeout=10)
        if response.status_code != 200:
            print(f"Gagal akses {page_url} (status {response.status_code})")
            break

        soup = BeautifulSoup(response.content, 'html.parser')

        # Cari semua div yang berisi artikel konsultasi
        divs = soup.find_all('div', class_='css-1povsli')
        found_this_page = 0

        for div in divs:
            a_tag = div.find('a')
            if a_tag:
                href = a_tag.get('href')
                if href and href.startswith('/klinik/a/'):
                    full_url = f"https://www.hukumonline.com{href}"
                    urls.append(full_url)
                    found_this_page += 1

        print(f"Halaman {page} ➔ Ditemukan {found_this_page} link konsultasi pidana")

        time.sleep(DELAY_SECONDS)

    except Exception as e:
        print(f"Error saat akses halaman {page_url}: {e}")
        break

# === SIMPAN LINK ===
urls = sorted(list(set(urls)))  # Hilangkan duplikat

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for url in urls:
        f.write(url + '\n')

print(f"\nCrawling selesai! Total {len(urls)} link konsultasi PIDANA disimpan ke {OUTPUT_FILE}")
