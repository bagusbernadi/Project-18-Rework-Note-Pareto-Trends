[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 18: Rework Note Analysis with LLM: Defect Pareto & Trends

**Status: Selesai di branch `project-18-build` (belum di-merge ke `main`).** Halaman rancangan dan laporan: [`design-and-report/index.html`](design-and-report/index.html) (tab Design Project dan Report Project).

**Tujuan:** mengelompokkan catatan rework operator ke kategori penyebab, membuat Pareto dan tren per stasiun dan bulan, serta menilai seberapa bisa dipercaya klasifikasi otomatisnya.

| | |
|---|---|
| Kategori | Manufaktur, teks tidak terstruktur (data anonim) |
| Tingkat | Sedang sampai sulit |
| Data | **Simulasi** yang dianonimkan (catatan karangan; stasiun dan model diganti kode; nama orang, lot, serial dihapus) |
| Tools | DuckDB + SQL, Python (pandas, scikit-learn, SciPy, statsmodels), Excel (dihitung ulang LibreOffice), Streamlit + Plotly |

> **Penting:** rancangan memakai Claude API. Project ini **tidak memanggil Claude API** (tidak ada API key). Klasifikasi dijalankan oleh pengganti lokal (TF-IDF + Logistic Regression). Hasil evaluasi di bawah adalah hasil pengganti lokal, bukan hasil LLM.

## 1. Problem

**Pertanyaan utama:** penyebab defect dan rework apa yang paling sering muncul di catatan operator, bagaimana trennya per stasiun dan per bulan, dan seberapa bisa dipercaya klasifikasi otomatisnya?

Rancangan memecahnya menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan). Daftar lengkap ada di halaman rancangan.

## 2. Data

- Data simulasi catatan rework (100% karangan), dibuat `00_generate_raw.py` lalu dianonimkan `01_anonymize.py`. Data tidak di-commit; dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256 di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) (`02_verify_fingerprint.py`).
- Versi data v1, seed 18260302 (generator) dan 18260999 (pemetaan). Hasil: 3.060 catatan mentah, 2.724 valid untuk klasifikasi, Maret sampai Agustus 2026, golden set 300 catatan (269 valid).
- Tabel: `dim_category`, `rework_note`, `manual_label`, `llm_label`. Kamus data: `project/docs/data_dictionary.md`.

## 3. Analysis

Pareto dan tren dengan view SQL, uji chi-square dan binomial dengan koreksi Holm, p-chart bulanan, evaluasi klasifikasi (accuracy, macro F1, confusion matrix, precision, recall, kalibrasi keyakinan) pada golden set, dan pembanding baseline kata kunci. Definisi dan asumsi: `project/docs/definitions.md`.

- Penyebab terbesar: **C4 Perekat kurang / berlebih** (27,3% catatan). Tiga kategori teratas 64,0%; butuh 5 kategori untuk mencapai 80%.
- Stasiun yang menonjol: ST-A untuk C2, ST-C untuk C4, ST-D untuk C7, ST-E untuk C5.
- Pengganti lokal: accuracy 99,3%, macro F1 0,988 pada golden set; baseline kata kunci accuracy 100,0%.

Hipotesis rancangan:
1. Dua atau tiga kategori menyumbang sekitar 80% catatan rework. **Tidak terbukti.**
2. LLM lebih tepat dibanding baseline kata kunci, terutama pada catatan yang memakai singkatan. **Belum bisa disimpulkan.**
3. Kategori yang mirip, misalnya goresan dan retak, paling sering tertukar. **Belum bisa disimpulkan.**
4. Satu stasiun menjadi sumber utama untuk satu kategori tertentu. **Terbukti.**
5. Sekitar 5 sampai 10% catatan terlalu singkat atau tidak jelas untuk diklasifikasi. **Terbukti.**

Uji pemulihan fakta yang ditanam: 10 dari 10 pulih penuh (`project/results/2-analysis/ground_truth_check.csv`).

## 4. Recommendation

Mulai perbaikan dari C4 dan stasiun yang menonjol; jangan memfokuskan pada satu atau dua penyebab saja. Jalankan pipeline dengan Claude API pada golden set yang sama sebelum mempercayai klasifikasi LLM.

## 5. Impact

Estimasi (`estimated`): menurunkan C4 20% menghemat sekitar 5,0 jam rework per bulan, dan klasifikasi otomatis menghemat sekitar 2,8 jam baca per bulan. Asumsi: satu catatan = satu unit, 12 menit rework per unit, 20 detik baca per catatan.

## Batasan

- **Data adalah simulasi** dan teks dibuat dari templat sederhana; angka terlalu optimistis dibanding catatan nyata.
- **Claude API tidak diuji**: H2, perbandingan LLM dengan baseline, konsistensi dua kali jalan (Q9), dan biaya (Q10) tidak terjawab untuk LLM. Label manual adalah kebenaran generator tanpa noise.
- Hanya sedikit kesalahan di golden set, jadi H3 (kategori mirip tertukar) tidak bisa disimpulkan.
- Batas yang ditetapkan sendiri (asumsi): arti "sekitar 80%", rasio 1,5 untuk H4, batas 3 sigma, batas 3 kata (9,0% catatan terlalu singkat), ambang keyakinan, menit rework, dan detik baca.
- Dashboard belum di-deploy (diuji dengan Streamlit AppTest: 16 dari 16 lulus). Success criteria "orang awam menyebut penyebab terbesar dalam 1 menit" belum diuji. Slide presentasi tidak dibuat.
- Cek silang: SQL vs pandas 397 dari 5, SQL vs Excel 9 dari 9 kategori (Excel dihitung ulang LibreOffice). Pemanggil API diuji dengan klien palsu (8 dari 8 lulus). Pindai kebocoran identitas: 108 file, 0 gagal.

## Menjalankan

Dari folder `project/`:

```
pip install -r requirements.txt
for f in code/1-data-preparation/python/*.py code/2-analysis/python/[0-9]*.py code/3-presentation/python/*.py; do python3 "$f"; done
python3 ../design-and-report/src/build_report.py
streamlit run code/3-presentation/streamlit/app.py
```

Claude API (opsional, tidak dijalankan di project ini): salin `.env.example` menjadi `.env`, isi `ANTHROPIC_API_KEY`, lalu gunakan `code/2-analysis/python/claude_client.py` dengan `prompts/classify_v1.md`.

## Struktur repository

```
README.md
index.html                     pengalihan ke design-and-report/
design-and-report/             index.html (tab Design + Report), src/ (page_v1.html, report.css, report_lib.py, build_report.py)
project/
  code/                        common.py; 1-data-preparation/python (00 sampai 04); 2-analysis/{python,sql} (05 sampai 14); 3-presentation/{python,streamlit} (15 sampai 20)
  results/                     1-data-preparation/ 2-analysis/ 3-presentation/ (CSV hasil, analysis.ipynb)
  prompts/                     classify_v1.md
  outputs/                     crosscheck.xlsx, infographic.pdf dan .png
  data/                        README.md (data tidak di-commit)
  docs/                        definitions.md, taxonomy.md, data_dictionary.md, cleaning_decisions.md, simulation_spec.md, datacenter_fingerprint.csv
  requirements.txt, .env.example
```
