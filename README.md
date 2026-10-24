[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 18: Rework Note Analysis with LLM: Defect Pareto & Trends

**Status: Design (rancangan).** Halaman rancangan ada di [`index.html`](index.html). Analisis, dashboard, dan angka hasil belum dikerjakan, sehingga bagian Analysis, Recommendation, dan Impact di bawah masih kosong.

**Tujuan:** membangun pipeline yang mengelompokkan catatan rework dan defect tulisan bebas operator ke kategori penyebab dengan Claude API, mengukur ketepatannya terhadap label manual, lalu menampilkan Pareto dan tren per stasiun dan bulan.

| | |
|---|---|
| Kategori | Manufaktur (data anonim) |
| Tingkat | Sedang sampai sulit |
| Data | Catatan kerja yang dianonimkan (nama orang, produk, stasiun, lot, dan serial dihapus atau diganti kode) |
| Tools | Claude API, Python (pandas, scikit-learn), DuckDB + SQL, Excel, Streamlit + Plotly |

## 1. Problem

**Pertanyaan utama:** Penyebab defect dan rework apa yang paling sering muncul di catatan operator, bagaimana trennya per stasiun dan per bulan, dan seberapa bisa dipercaya klasifikasi otomatisnya?

Rancangan memecahnya menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan) dalam tema kategori, tren, ketepatan, biaya dan dampak, serta validitas. Daftar lengkap ada di bagian 2 halaman rancangan.

## 2. Data

- Catatan rework dan defect dari pekerjaan nyata yang dianonimkan. Hanya teks yang sudah dianonimkan yang dikirim ke API. Data asli tidak masuk repositori.
- Ukuran (perkiraan): ±3.000 catatan, 6 stasiun (ST-A sampai ST-F), ±6 bulan; golden set ±300 catatan berlabel manual.
- Rencana tabel: `rework_note`, `llm_label`, `manual_label`, `dim_category`.

## 3. Analysis

Belum dikerjakan. Rencana langkah (12 langkah, tahap A sampai D) ada di bagian 6 halaman rancangan: taksonomi 9 kategori, klasifikasi Claude API dengan output JSON, baseline kata kunci, evaluasi (accuracy, macro F1, confusion matrix), lalu Pareto dan tren.

Hipotesis yang akan diuji (belum terbukti):
1. Dua atau tiga kategori menyumbang ±80% catatan.
2. LLM lebih tepat dibanding baseline kata kunci.
3. Kategori yang mirip paling sering tertukar.
4. Satu stasiun dominan untuk kategori tertentu.
5. ±5–10% catatan terlalu singkat untuk diklasifikasi.

## 4. Recommendation

Belum dikerjakan. Output yang direncanakan: kategori penyebab prioritas per stasiun dan aturan kapan hasil LLM perlu dicek manual.

## 5. Impact

Belum dikerjakan. Rumus yang akan dipakai (semua hasil diberi label `estimated`):

```
Jam rework dihemat = (rate lama − rate baru) × volume × menit per unit ÷ 60
```

## Batasan yang sudah diketahui

- Angka confidence dari LLM tidak selalu sesuai ketepatan sebenarnya.
- Golden set dibuat satu orang.
- Catatan hanya mencerminkan apa yang ditulis operator.
- API key disimpan di secrets, tidak di repositori.

## Struktur repository

```
index.html   Halaman rancangan project (bisa dibuka di browser atau lewat GitHub Pages)
README.md    Dokumen ini
```

Folder `docs/`, `data/`, `prompts/`, `scripts/`, `sql/`, `notebooks/`, `dashboard/`, dan `outputs/` ditambahkan saat pengerjaan dimulai. Folder `data/private/` tidak pernah di-commit.
