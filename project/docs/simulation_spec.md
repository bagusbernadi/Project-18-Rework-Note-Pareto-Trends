# Spesifikasi simulasi (Project 18)

Data adalah simulasi. Parameter ada di `code/1-data-preparation/python/00_generate_raw.py` (seed 18260302, versi v1) dan identik dengan generator di repo DataCenter (sidik jari SHA-256 dicek oleh `02_verify_fingerprint.py`).

| Parameter | Nilai |
|---|---|
| Catatan | 3.000 catatan asli ditambah 60 baris ganda di akhir (total 3.060) |
| Periode | 2026-03 sampai 2026-08 |
| Stasiun | enam; nama asli diganti ST-A sampai ST-F oleh anonimisasi |
| Model | tiga; diganti M-1 sampai M-3 |
| Bobot dasar kategori C1 sampai C9 | 0,15 / 0,09 / 0,05 / 0,23 / 0,18 / 0,07 / 0,08 / 0,03 / 0,12 |
| Pengganda stasiun | empat stasiun; tiga kali untuk dua pasangan, empat kali dan dua kali untuk dua lainnya (kategori dan stasiun asli hanya ada di generator) |
| Catatan sangat singkat | 75% dari catatan C9 |
| Golden set | 300 catatan acak |

Fakta yang ditanam (8): C4 penyebab terbesar; urutan lima kategori teratas; empat sel stasiun x kategori menonjol; tidak ada efek shift dan model; tidak ada lonjakan bulanan; sekitar 9% catatan terlalu singkat; teks templat dapat dikenali. Hasil uji pemulihan: `results/2-analysis/ground_truth_check.csv` (hanya `14_ground_truth_check.py` yang membaca `truth.csv` dan `mapping.json`).

**Sifat simulasi yang dicatat jujur.** Teks dibuat dari templat sederhana (3 sampai 6 kalimat per kategori), jadi baseline kata kunci dan klasifikator lokal hampir sempurna. Ini tidak mewakili catatan operator nyata yang lebih beragam. Tidak ada noise pada label manual.
