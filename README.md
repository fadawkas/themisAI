# ThemisAI  
Sistem Konsultasi dan Rekomendasi Tindak Lanjut Hukum Pidana Berbasis Large Language Model dan Retrieval Augmented Generation

---

## Deskripsi
ThemisAI merupakan sistem konsultasi hukum pidana berbasis website yang dikembangkan dengan memanfaatkan teknologi Large Language Model (LLM) dan pendekatan Retrieval Augmented Generation (RAG). Sistem ini dirancang untuk membantu masyarakat umum dalam memperoleh informasi hukum pidana yang relevan, kontekstual, dan berbasis sumber hukum resmi Indonesia. Dengan mengombinasikan kemampuan pemahaman bahasa alami dari LLM dan mekanisme pencarian semantik pada basis data vektor, sistem mampu menghasilkan jawaban yang lebih faktual dan dapat ditelusuri ke dokumen hukum yang digunakan sebagai konteks.

---

## Latar Belakang Penelitian
Pemanfaatan kecerdasan buatan dalam bidang hukum memiliki potensi besar untuk meningkatkan akses masyarakat terhadap informasi hukum. Namun, penggunaan model bahasa tanpa dukungan konteks dokumen yang valid berisiko menghasilkan informasi yang tidak akurat. Oleh karena itu, penelitian ini mengimplementasikan pendekatan Retrieval Augmented Generation untuk memastikan bahwa setiap jawaban yang dihasilkan LLM didukung oleh dokumen hukum pidana yang relevan, seperti KUHP, KUHAP, dan peraturan perundang-undangan terkait.

---

## Konteks Akademik
Repository ini dikembangkan sebagai bagian dari tugas akhir (skripsi) pada Program Studi Informatika, Fakultas Ilmu Komputer, Universitas Pembangunan Nasional “Veteran” Jakarta. Fokus utama penelitian meliputi perancangan arsitektur sistem konsultasi hukum berbasis LLM, implementasi pipeline RAG, serta evaluasi kualitas jawaban sistem melalui pendekatan kuantitatif dan kualitatif.

---

## Tujuan Penelitian
Tujuan dari pengembangan sistem ThemisAI adalah sebagai berikut:
1. Mengimplementasikan sistem konsultasi hukum pidana berbasis website dengan pendekatan Retrieval Augmented Generation.
2. Mengintegrasikan Large Language Model dengan basis data vektor untuk meningkatkan relevansi dan ketepatan jawaban.
3. Mengevaluasi kualitas jawaban sistem menggunakan metrik evaluasi RAGAS.
4. Melakukan pengujian fungsional dan penerimaan pengguna untuk menilai kelayakan sistem.

---

## Arsitektur Sistem
Sistem ThemisAI terdiri dari beberapa komponen utama, yaitu:
- Frontend berbasis web sebagai antarmuka interaksi pengguna.
- Backend API yang mengelola logika aplikasi dan orkestrasi pipeline RAG.
- Modul embedding untuk mengubah dokumen hukum menjadi representasi vektor.
- Basis data vektor FAISS untuk pencarian semantik dokumen hukum.
- Large Language Model yang menghasilkan jawaban berdasarkan konteks hasil retrieval.
- Basis data relasional untuk menyimpan data pengguna dan riwayat konsultasi.

---

## Struktur Direktori
themisAI/
├── backend/ # Backend API dan pipeline RAG
├── frontend/ # Antarmuka web pengguna
├── rag_dev/ # Pengembangan dan eksperimen RAG
├── finetune_dev/ # Eksperimen fine-tuning model
├── scraper/ # Pengumpulan dan pemrosesan data hukum
├── benchmark/ # Evaluasi model dan metrik RAGAS
├── docker-compose.dev.yml
├── .gitignore
└── README.md

---

## Teknologi yang Digunakan
- Python
- FastAPI
- Large Language Model (LLM)
- FAISS (Vector Database)
- PostgreSQL
- Docker dan Docker Compose
- React
- RAGAS

---

## Metode Evaluasi
Evaluasi sistem dilakukan melalui beberapa pendekatan, antara lain:
- Evaluasi kualitas jawaban menggunakan metrik RAGAS yang meliputi faithfulness, answer relevancy, context precision, dan context recall.
- Pengujian fungsional menggunakan metode black-box testing.
- User Acceptance Testing (UAT) untuk menilai tingkat penerimaan dan kepuasan pengguna terhadap sistem.

---

## Cara Menjalankan Sistem
Untuk menjalankan sistem pada lingkungan pengembangan, pastikan Docker dan Docker Compose telah terpasang. Sistem dapat dijalankan menggunakan perintah berikut:

Setelah proses build selesai, frontend dan backend akan berjalan sesuai dengan konfigurasi yang telah ditentukan.

---

## Catatan Keamanan
Repository ini tidak menyertakan file konfigurasi sensitif seperti file environment, API key, model hasil pelatihan, embedding, maupun database dump. Seluruh data sensitif dikelola secara terpisah dan tidak dipublikasikan dalam repository ini.

---

## Disclaimer
Sistem ThemisAI dikembangkan untuk tujuan akademik dan penelitian. Informasi yang dihasilkan oleh sistem bersifat informatif dan tidak dapat dijadikan sebagai nasihat hukum resmi maupun pengganti konsultasi dengan praktisi hukum yang berwenang.

---

## Penulis
Muhammad Fadawkas Oemarki  
Program Studi Informatika  
Fakultas Ilmu Komputer  
Universitas Pembangunan Nasional “Veteran” Jakarta  

---

## Lisensi
Repository ini digunakan untuk kepentingan akademik dan penelitian. Hak cipta sepenuhnya berada pada penulis.

