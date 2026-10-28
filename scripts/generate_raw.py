"""Project 18 (langkah 1 dari 2): catatan rework SIMULASI berisi identitas (nama, produk, lot, serial, stasiun). Seed tetap.

Seluruh catatan karangan, tetapi ditulis seperti catatan operator (singkatan, salah ketik, nama orang). Kategori sebenarnya
disimpan sebagai kebenaran (truth) untuk menilai klasifikasi. Hasil (data/private/raw/, tidak di-commit):
notes_raw.csv, truth.csv. Jalankan: python scripts/generate_raw.py && python scripts/anonymize.py   (versi data: v1)
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "private" / "raw"
SEED = 18260302
DATA_VERSION = "v1"
N_NOTES = 3000
STATIONS = ["Dispensing", "Placement", "Reflow", "AOI", "Assembly", "Final Test"]
MODELS = ["Modul KR-45", "Modul KR-60", "Modul KR-90"]
NAMES = ["Budi", "Sari", "Andi", "Rina", "Joko", "Wati", "Dewi", "Eko", "Fitri", "Hendra"]
PARTS = ["sisi kiri", "sisi kanan", "area tengah", "pojok atas", "lensa", "konektor", "bracket", "pcb"]
CATS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"]
CAT_NAME = {"C1": "Kontaminasi / debu", "C2": "Goresan", "C3": "Retak / patah", "C4": "Perekat kurang / berlebih",
            "C5": "Posisi tidak sejajar", "C6": "Dimensi di luar toleransi", "C7": "Gagal uji fungsi",
            "C8": "Label / pengemasan", "C9": "Lainnya / tidak jelas"}
BASE_W = dict(C1=.15, C2=.09, C3=.05, C4=.23, C5=.18, C6=.07, C7=.08, C8=.03, C9=.12)
STATION_BOOST = {"Dispensing": {"C4": 3.0}, "Placement": {"C5": 3.0}, "Final Test": {"C7": 4.0}, "AOI": {"C2": 2.0}}
T = {
    "C1": ["ada debu di {p}, bersihkan ulang", "kotoran menempel di {p}", "partikel asing di {p}, dilap lalu cek lagi",
           "kontaminasi minyak di {p}", "tdk bersih {p}, ada serat"],
    "C2": ["goresan di {p}", "baret halus di {p} sdh dicek", "ada scratch di {p}, panjang kira2 3mm", "lecet {p} saat handling"],
    "C3": ["retak di {p}", "patah di {p}, tdk bisa dipakai", "crack kecil {p} setelah press", "bagian {p} pecah"],
    "C4": ["lem kurang, {p} tdk nempel", "perekat berlebih meluber di {p}", "glue tipis di {p}, lepas saat ditarik",
           "dispense kurang {p}", "lem luber ke {p}"],
    "C5": ["posisi miring {p}", "tdk sejajar di {p}, geser sekitar 0.3mm", "komponen bergeser {p}", "alignment meleset {p}"],
    "C6": ["dimensi {p} di luar toleransi", "ukuran {p} kebesaran, out of spec", "tebal {p} kurang dari spec", "gap {p} terlalu lebar"],
    "C7": ["gagal uji fungsi, tdk ada output", "functional test NG, sensor tdk respon", "tes fungsi gagal berulang",
           "output tegangan rendah saat tes", "no signal saat final test"],
    "C8": ["label salah tempel", "label terbalik di kemasan", "barcode tdk terbaca", "kemasan sobek, label kabur"],
    "C9": ["ng lagi", "cek ulang", "rework", "tdk ok", "lihat lot sebelumnya", "ada masalah, belum tau penyebabnya"],
}
SUFFIX = ["", "", "", " - {lot}", " ({name})", " produk {model}", " SN{sn}", " dikerjakan {name}", " lot {lot}"]

rng = np.random.default_rng(SEED)
days = pd.bdate_range("2026-03-02", periods=130)
rows, truth = [], []
for i in range(N_NOTES):
    st = STATIONS[int(rng.integers(0, len(STATIONS)))]
    w = np.array([BASE_W[c] * STATION_BOOST.get(st, {}).get(c, 1.0) for c in CATS])
    cat = CATS[int(rng.choice(len(CATS), p=w / w.sum()))]
    short = cat == "C9" and rng.random() < 0.75          # catatan sangat singkat tanpa konteks (tidak valid untuk klasifikasi)
    text = T[cat][int(rng.integers(0, 4 if short else len(T[cat])))].format(p=PARTS[int(rng.integers(0, len(PARTS)))])
    suf = ("" if short else SUFFIX[int(rng.integers(0, len(SUFFIX)))]).format(
        lot=f"LOT-{int(rng.integers(0, 65536)):04X}", name=NAMES[int(rng.integers(0, len(NAMES)))],
        model=MODELS[int(rng.integers(0, len(MODELS)))], sn=int(rng.integers(10_000_000, 99_999_999)))
    text += suf
    if rng.random() < 0.15:
        text = text.replace("tidak", "tdk").replace("sudah", "sdh").replace("di ", "d ", 1)
    if rng.random() < 0.04:
        text = text.upper()
    d = days[int(rng.integers(0, len(days)))]
    rows.append([f"N{i + 1:05d}", d.date(), "Shift 1" if rng.random() < 0.5 else "Shift 2", st,
                 MODELS[int(rng.integers(0, len(MODELS)))], text])
    truth.append([f"N{i + 1:05d}", cat])
# duplikat (+-2%): catatan yang sama tersalin ulang
for k in rng.choice(N_NOTES, int(N_NOTES * 0.02), replace=False):
    rows.append([f"N{len(rows) + 1:05d}"] + rows[int(k)][1:])
    truth.append([f"N{len(rows):05d}", truth[int(k)][1]])

RAW.mkdir(parents=True, exist_ok=True)
pd.DataFrame(rows, columns=["note_id", "date", "shift", "station_name", "model_name", "note_text"]).to_csv(RAW / "notes_raw.csv", index=False)
pd.DataFrame(truth, columns=["note_id", "category_code"]).to_csv(RAW / "truth.csv", index=False)
print(f"{len(rows)} catatan -> {RAW}")
