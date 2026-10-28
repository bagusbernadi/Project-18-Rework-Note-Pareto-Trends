"""Project 18 (langkah 2 dari 2): anonymization catatan simulasi -> data/anon/. Seed tetap.

Menghapus/mengganti nama orang, produk, lot, nomor seri, dan nama stasiun. Hasil (data/anon/): rework_note.csv,
manual_label.csv (golden set 300 catatan), dim_category.csv, redaction_log.csv. Pemetaan stasiun/model ada di project/data/mapping.json (tidak di-commit).
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import ANON, MAPPING, RAW
SEED = 18260999
GOLDEN_N = 300
NAMES = ["Budi", "Sari", "Andi", "Rina", "Joko", "Wati", "Dewi", "Eko", "Fitri", "Hendra"]
CAT_NAME = {"C1": "Kontaminasi / debu", "C2": "Goresan", "C3": "Retak / patah", "C4": "Perekat kurang / berlebih",
            "C5": "Posisi tidak sejajar", "C6": "Dimensi di luar toleransi", "C7": "Gagal uji fungsi",
            "C8": "Label / pengemasan", "C9": "Lainnya / tidak jelas"}
RULES = [("nama", re.compile(r"\b(?:" + "|".join(NAMES) + r")\b", re.I), "[NAMA]"),
         ("lot", re.compile(r"\bLOT-[0-9A-F]{4}\b", re.I), "[LOT]"),
         ("serial", re.compile(r"\bSN\d{8}\b", re.I), "[SN]"),
         ("produk", re.compile(r"\bModul KR-\d{2}\b", re.I), "[PRODUK]")]

rng = np.random.default_rng(SEED)
raw = pd.read_csv(RAW / "notes_raw.csv", parse_dates=["date"])
truth = pd.read_csv(RAW / "truth.csv")

st_map = {s: f"ST-{chr(65 + i)}" for i, s in enumerate(sorted(raw["station_name"].unique()))}
md_map = {m: f"M-{i + 1}" for i, m in enumerate(sorted(raw["model_name"].unique()))}
for s, c in st_map.items():                                     # nama stasiun di teks -> kode stasiun
    RULES.append(("stasiun", re.compile(rf"\b{re.escape(s)}\b", re.I), c))
log = {}


def clean(text):
    for name, rx, rep in RULES:
        text, n = rx.subn(rep, text)
        log[name] = log.get(name, 0) + n
    return re.sub(r"\s+", " ", text).strip()


note = pd.DataFrame({"note_id": raw["note_id"], "date": raw["date"].dt.date, "shift": raw["shift"],
                     "station_code": raw["station_name"].map(st_map), "model_code": raw["model_name"].map(md_map),
                     "note_text_clean": raw["note_text"].map(clean)})
note["is_valid"] = note["note_text_clean"].str.split().str.len() >= 3      # terlalu singkat -> tidak valid
leak = [s for s in list(st_map) + list(md_map) + NAMES if note["note_text_clean"].str.contains(rf"\b{re.escape(s)}\b", case=False).any()]
assert not leak, f"identitas tersisa: {leak}"

gold_ids = sorted(rng.choice(note["note_id"], GOLDEN_N, replace=False))
manual = truth[truth["note_id"].isin(gold_ids)].copy()

ANON.mkdir(parents=True, exist_ok=True)
note.to_csv(ANON / "rework_note.csv", index=False)
manual.to_csv(ANON / "manual_label.csv", index=False)
pd.DataFrame([(k, v) for k, v in CAT_NAME.items()], columns=["category_code", "name"]).to_csv(ANON / "dim_category.csv", index=False)
pd.DataFrame(list(log.items()), columns=["rule", "n_replaced"]).to_csv(ANON / "redaction_log.csv", index=False)
MAPPING.write_text(json.dumps({"station": st_map, "model": md_map}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"anon: {len(note)} catatan ({int((~note['is_valid']).sum())} terlalu singkat), golden set {len(manual)}; "
      f"penggantian {log}; cek kebocoran: lolos")
