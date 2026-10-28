# Kamus data (Project 18)

Data simulasi yang dianonimkan. Nama stasiun dan model diganti kode; nama orang, nomor lot, nomor serial, dan nama produk pada teks diganti penanda atau dihapus.

## rework_note (satu baris = satu catatan rework)
| Kolom | Isi |
|---|---|
| note_id | N00001 dan seterusnya, unik |
| date | tanggal catatan (2026-03 sampai 2026-08) |
| shift | Shift 1 atau Shift 2 |
| station_code | ST-A sampai ST-F |
| model_code | M-1 sampai M-3 |
| note_text_clean | teks anonim yang sudah dibersihkan |
| is_valid | 1 bila boleh diklasifikasi, 0 bila terlalu singkat |

## llm_label (hasil klasifikasi satu catatan valid)
| Kolom | Isi |
|---|---|
| note_id | kunci ke rework_note |
| category_code | C1 sampai C9 |
| confidence | 0 sampai 1 (probabilitas pengganti lokal, bukan keyakinan LLM) |
| model_name | nama klasifikator ("pengganti lokal TF-IDF + LogisticRegression") |
| prompt_version | versi prompt yang disiapkan (classify_v1) |
| sumber | out-of-fold (golden set) atau model akhir |

## manual_label (satu baris = satu catatan golden set valid)
| Kolom | Isi |
|---|---|
| note_id | kunci ke rework_note |
| category_code | label manual (pada simulasi: kebenaran generator) |
| labeled_by | "simulasi (kebenaran generator)" |
| labeled_at | kosong |

## dim_category (satu baris = satu kategori)
category_code, name, definition, example_note (lihat `taxonomy.md`).

## Aturan anonimisasi teks
Nama orang menjadi `[NAMA]`, nomor lot `[LOT]`, serial `[SN]`, nama produk `[PRODUK]`; nama stasiun dan model diganti kode. Jumlah penggantian per aturan ada di `data/anon/redaction_log.csv`. Pindai kebocoran: `results/3-presentation/leak_scan.csv`.
