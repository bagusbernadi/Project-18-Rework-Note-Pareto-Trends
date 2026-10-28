"""03: Audit kualitas dan pembersihan teks (Q13).

Aturan (rancangan: kosong, ganda, terlalu singkat; urutan dan batas = asumsi, lihat docs/definitions.md):
  1. teks kosong (setelah dibersihkan)     2. catatan ganda: tanggal, shift, stasiun, model, dan teks sama (baris pertama dipertahankan)
  3. terlalu singkat: kurang dari 3 kata (tidak dikirim ke classifier, dihitung terpisah)
Pembersihan teks (note_text_clean): huruf kecil, singkatan umum diperluas, penanda anonim ([NAMA], [LOT], [SN], [PRODUK]) dan kode stasiun
dihapus, tanda baca berlebih dirapikan. Hasil: data/clean/*.csv, results/1-data-preparation/data_quality.csv dan cleaning_log.csv.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

note = pd.read_csv(CM.ANON / "rework_note.csv", keep_default_na=False)
gold = pd.read_csv(CM.ANON / "manual_label.csv")
n_raw = len(note)
ABBR = {"tdk": "tidak", "sdh": "sudah", "yg": "yang", "kira2": "kira-kira", "d": "di", "dgn": "dengan"}
PLACEHOLDER = re.compile(r"\b(?:lot|produk|dikerjakan)\s+\[(?:NAMA|LOT|SN|PRODUK)\]|\[(?:NAMA|LOT|SN|PRODUK)\]|\bST-[A-F]\b", re.I)


def clean(t):
    t = PLACEHOLDER.sub(" ", str(t)).lower()
    t = re.sub(r"[()]", " ", t)
    t = re.sub(r"\s+-\s+|\s+-$|^-\s+", " ", t)
    toks = [ABBR.get(w, w) for w in re.split(r"\s+", t.strip()) if w]
    out = " ".join(toks).strip(" ,.-")
    return re.sub(r"\s+", " ", out)


note["note_text_clean"] = note["note_text_clean"].map(clean)
empty = note["note_text_clean"].str.len() == 0
dup = note.duplicated(["date", "shift", "station_code", "model_code", "note_text_clean"], keep="first") & ~empty
short = (note["note_text_clean"].str.split().str.len() < CM.MIN_WORDS) & ~empty & ~dup
log = []
for i in note.index[empty]:
    log.append((note.at[i, "note_id"], "teks kosong", "dibuang"))
for i in note.index[dup]:
    log.append((note.at[i, "note_id"], "catatan ganda", "dibuang"))
for i in note.index[short]:
    log.append((note.at[i, "note_id"], "terlalu singkat", "dipertahankan, tidak diklasifikasi (is_valid = 0)"))
keep = note[~empty & ~dup].copy()
keep["is_valid"] = (~short[keep.index]).astype(int)
keep[["note_id", "date", "shift", "station_code", "model_code", "note_text_clean", "is_valid"]].to_csv(CM.CLEAN / "rework_note_clean.csv", index=False)
gold_ok = gold[gold.note_id.isin(keep[keep.is_valid == 1].note_id)]
gold_ok.to_csv(CM.CLEAN / "manual_label_clean.csv", index=False)
pd.read_csv(CM.ANON / "dim_category.csv").to_csv(CM.CLEAN / "dim_category_clean.csv", index=False)
pd.DataFrame(log, columns=["note_id", "masalah", "keputusan"]).to_csv(CM.RES1 / "cleaning_log.csv", index=False)
n_valid = int(keep.is_valid.sum())
dq = [("catatan (mentah)", n_raw, n_raw, "dasar"), ("teks kosong", int(empty.sum()), n_raw, "dibuang"),
      ("catatan ganda", int(dup.sum()), n_raw, "dibuang (baris pertama dipertahankan)"),
      ("terlalu singkat (< 3 kata)", int(short.sum()), n_raw, "dipertahankan, tidak diklasifikasi"),
      ("catatan setelah dibersihkan", len(keep), n_raw, "dipakai"), ("catatan valid untuk klasifikasi", n_valid, len(keep), "dipakai"),
      ("golden set (mentah)", len(gold), len(gold), "dasar"), ("golden set valid (dipakai evaluasi)", len(gold_ok), len(gold), "dipakai"),
      ("golden set dibuang (ganda atau terlalu singkat)", len(gold) - len(gold_ok), len(gold), "tidak dipakai evaluasi")]
pd.DataFrame([(a, b, c, round(b / c, 6), d) for a, b, c, d in dq], columns=["kategori", "jumlah", "dasar", "proporsi", "keputusan"]).to_csv(CM.RES1 / "data_quality.csv", index=False)
print(f"mentah {n_raw}; kosong {int(empty.sum())}; ganda {int(dup.sum())}; singkat {int(short.sum())}; valid {n_valid}; golden valid {len(gold_ok)} dari {len(gold)}")
print(keep.note_text_clean.sample(8, random_state=3).tolist())
