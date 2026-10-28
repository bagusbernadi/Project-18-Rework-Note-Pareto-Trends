# Keputusan pembersihan teks (Project 18)

| Masalah | Aturan | Keputusan | Jumlah |
|---|---|---|---|
| Teks kosong | panjang 0 setelah trim | dibuang | dari `results/1-data-preparation/data_quality.csv` |
| Catatan ganda | tanggal, shift, stasiun, model, dan teks bersih sama | baris pertama dipertahankan, sisanya dibuang | idem |
| Terlalu singkat | kurang dari 3 kata (asumsi) | dipertahankan, `is_valid = 0`, tidak diklasifikasi | idem |
| Huruf besar-kecil | semua huruf kecil | diseragamkan | - |
| Singkatan umum | tdk, sdh, yg, kira2, d, dgn | dikembangkan | - |
| Penanda anonim | `[NAMA]`, `[LOT]`, `[SN]`, `[PRODUK]` beserta kata "lot", "produk", "dikerjakan" di depannya | dihapus | - |
| Kode stasiun di teks | ST-x | dihapus | - |

Log per catatan: `results/1-data-preparation/cleaning_log.csv`. Aturan diuji pada data simulasi; data kerja nyata bisa memuat pola kotor lain yang belum teruji.
