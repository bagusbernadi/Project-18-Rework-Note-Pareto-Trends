# Definisi dan asumsi (Project 18)

Ukuran dan batas yang tidak ditulis rancangan ditetapkan di sini dengan label **asumsi**, sebelum hasil uji dilihat. Nilainya ada di `code/common.py`. Uji sensitivitas ditulis di bagian akhir.

## Data valid dan golden set
| Istilah | Definisi | Status |
|---|---|---|
| Catatan ganda | Baris dengan tanggal, shift, stasiun, model, dan teks bersih yang sama; baris pertama dipertahankan | asumsi |
| Catatan terlalu singkat | Teks bersih kurang dari 3 kata (`MIN_WORDS`); dipertahankan tetapi `is_valid = 0` dan tidak diklasifikasi | asumsi |
| Catatan valid | Setelah catatan ganda dibuang, bukan kosong, dan tidak terlalu singkat | asumsi |
| Golden set | 300 catatan yang diberi label manual; yang ganda atau terlalu singkat tidak dipakai evaluasi | rancangan (±300) |
| Label manual | Pada simulasi memakai kebenaran generator tanpa noise (tidak ada pelabel manusia, tidak ada ketidaksepakatan antar pelabel) | asumsi |

## Klasifikasi
- Rancangan memakai Claude API. Project ini tidak punya API key, jadi diganti klasifikator lokal (TF-IDF + Logistic Regression) dengan nested cross-validation (5 fold luar, 3 fold dalam, 4 konfigurasi). Prediksi golden set adalah out-of-fold. Pengganti ini **bukan** LLM; semua hasil evaluasi menyebutnya "pengganti lokal".
- Pemanggil Claude API (`claude_client.py`) dan prompt (`prompts/classify_v1.md`) dibuat dan diuji dengan klien palsu (`07_test_claude_pipeline.py`), tetapi tidak pernah dijalankan terhadap API.
- Ambang keyakinan awal 0,70 (rancangan). Ambang alternatif dipilih dengan aturan tetap: ambang terendah yang membuat accuracy catatan otomatis >= 95% (asumsi). Konfigurasi tidak dipilih ulang dari data uji.

## Kriteria hipotesis (ditetapkan sebelum uji)
| Hipotesis | Kriteria Terbukti | Kriteria Belum bisa disimpulkan |
|---|---|---|
| H1: dua atau tiga kategori menyumbang sekitar 80% | Kumulatif 2 atau 3 kategori teratas berada di 75% sampai 85% (asumsi arti "sekitar 80%") | - |
| H2: LLM lebih tepat dari baseline, terutama pada catatan bersingkatan | Accuracy LLM lebih tinggi dari baseline dan selisih signifikan (McNemar) | LLM tidak diuji (tanpa API key) |
| H3: kategori mirip (goresan dan retak) paling sering tertukar | Pasangan C2 dan C3 adalah pasangan tertukar terbanyak | Total kesalahan di golden set kurang dari 10 (`MIN_ERRORS_H3`, asumsi) |
| H4: satu stasiun menjadi sumber utama satu kategori | Ada sel stasiun x kategori dengan porsi >= 1,5 kali porsi seharusnya dan Holm p < 0,05 (uji binomial satu sisi, 54 sel) | - |
| H5: sekitar 5 sampai 10% catatan terlalu singkat | Proporsi terlalu singkat terhadap catatan setelah ganda dibuang berada di 5% sampai 10% (rancangan) | - |

"Porsi seharusnya" untuk H4 = porsi catatan stasiun itu dari seluruh catatan valid.

## Pareto, tren, dan tabel silang
- Pareto dihitung dari catatan valid yang diklasifikasi (golden set memakai prediksi out-of-fold, sisanya model akhir).
- Lonjakan bulanan (Q3): p-chart per kategori, porsi bulan itu di atas 3 sigma dari porsi gabungan (asumsi).
- Q4 dan Q2: chi-square dan Cramér's V per faktor (stasiun, shift, model, bulan), koreksi Holm antar empat uji; sel diuji binomial dua sisi dengan Holm.

## Dampak (estimated, bukan hasil pengukuran)
| Asumsi | Nilai | Dipakai di |
|---|---|---|
| 1 catatan = 1 unit yang di-rework | - | Q11 |
| Menit rework per unit | 12 | Q11 |
| Penurunan kategori teratas | 20% | Q11 |
| Detik baca dan rekap manual per catatan | 20 | Q12 |
| Periode | 6 bulan (Maret sampai Agustus 2026) | Q11, Q12 |

Sensitivitas: penurunan 10, 20, 30, 50% dan menit rework 6, 12, 18; detik baca 10, 20, 30, 60 (`results/2-analysis/impact_sensitivity.csv`).

## Pertanyaan yang tidak bisa dijawab penuh
- Q9 (konsistensi dua kali jalan): pengganti lokal deterministik, jadi 100% identik dan tidak informatif untuk LLM.
- Q10 (biaya API dan waktu): tidak diukur, tanpa API key.
- Q7 dan H2: hanya membandingkan pengganti lokal dengan baseline; LLM tidak diuji.
