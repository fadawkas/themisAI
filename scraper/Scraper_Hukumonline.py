import requests
from bs4 import BeautifulSoup
import json
import os
import time
from tqdm import tqdm
import re

# === CLEANER FUNCTION ===
def aggressive_clean_response_text(text):
    # Remove promo-related parts
    promo_keywords = [
        "Pernyataan Penyangkalan",
        "Konsultan Mitra Justika",
        "Belajar Hukum",
        "Hukumonline Pro",
        "Lihat Semua Kelas",
        "Perkaya riset hukum Anda",
        "Baca juga:",
        "selengkapnya",
        "pelajari lebih lanjut",
        "di sini",
        "konsultasikan langsung dengan",
        "Justika"
    ]

    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if not any(keyword.lower() in line.lower() for keyword in promo_keywords):
            cleaned_lines.append(line.strip())

    cleaned_text = "\n".join(cleaned_lines)

    # Remove footnotes like [1], [2], [3], etc.
    cleaned_text = re.sub(r'\[\d+', '', cleaned_text)
    cleaned_text = re.sub(r'\d+\]', '', cleaned_text)

    # Clean up excessive spaces and enters
    cleaned_text = re.sub(r'\n{2,}', '\n\n', cleaned_text)
    cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)

    cleaned_text = cleaned_text.replace('‐', '-')  # fix weird dash

    return cleaned_text.strip()

# === SCRAPING CONFIGURATION ===
INPUT_URL_FILE = 'URLs_QA.txt'
OUTPUT_FOLDER = 'datasets'
OUTPUT_FILE = 'QAs_Hukumonline_Clean.json'
DELAY_SECONDS = 1
MAX_URLS = 500  # Only scrape 5 URLs for test

# === PREPARATION ===
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

with open(INPUT_URL_FILE, 'r', encoding='utf-8') as f:
    urls = [line.strip() for line in f.readlines() if line.strip()]

urls = urls[:MAX_URLS]

dataset = []

# === SCRAPING PROCESS ===
for url in tqdm(urls, desc=f"Scraping and Cleaning QA Hukumonline"):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to access {url} (status {response.status_code})")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')

        divs = soup.find_all('div', class_='css-c816ma e1vjmfpm0')
        if not divs or len(divs) < 1:
            print(f"Content not found at {url}")
            continue

        # Extract question
        question_ps = divs[0].find_all('p')
        question_text = "\n".join(p.get_text(strip=True) for p in question_ps)

        # Extract response
        ulasan_parts = []
        for div in divs[1:]:
            p_tags = div.find_all('p')
            ulasan_parts.extend(p.get_text(strip=True) for p in p_tags)

        article = soup.find('article')
        if article:
            article_ps = article.find_all('p')
            ulasan_parts.extend(p.get_text(strip=True) for p in article_ps)

        ulasan_text = "\n\n".join(ulasan_parts).strip()

        # === APPLY CLEANER ===
        question_text = aggressive_clean_response_text(question_text)
        ulasan_text = aggressive_clean_response_text(ulasan_text)

        if question_text and ulasan_text:
            dataset.append({
                "instruction": question_text,
                "response": ulasan_text
            })
        else:
            print(f"Question or Response is empty at {url}")

        time.sleep(DELAY_SECONDS)

    except Exception as e:
        print(f"Error scraping {url}: {e}")

# === SAVE TO FILE ===
output_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print(f"\nScraping & cleaning completed! {len(dataset)} records saved to {output_path}")
