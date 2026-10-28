"""05: Baseline kata kunci dan regex (pembanding Q7). Aturan ditulis dari definisi taksonomi dan pembacaan sampel catatan,
sebelum evaluasi, dan tidak diubah sesudah melihat hasil. Catatan tanpa kata kunci masuk C9. Bila beberapa kategori cocok,
dipilih yang kata kuncinya paling banyak cocok; seri dipecah menurut urutan kode kategori.
Hasil: results/2-analysis/baseline_label.csv (semua catatan valid).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

RULES = {
    "C1": [r"debu", r"kotor", r"partikel", r"kontaminasi", r"tidak bersih", r"serat", r"minyak"],
    "C2": [r"goresan", r"baret", r"lecet", r"scratch"],
    "C3": [r"retak", r"patah", r"crack", r"pecah"],
    "C4": [r"\blem\b", r"perekat", r"glue", r"dispense", r"luber", r"nempel"],
    "C5": [r"miring", r"sejajar", r"geser", r"bergeser", r"alignment", r"meleset"],
    "C6": [r"dimensi", r"ukuran", r"tebal", r"\bgap\b", r"toleransi", r"out of spec", r"\bspec\b"],
    "C7": [r"uji fungsi", r"tes fungsi", r"functional", r"\boutput\b", r"sinyal", r"signal", r"sensor", r"tegangan"],
    "C8": [r"label", r"barcode", r"kemasan"],
}
note = pd.read_csv(CM.CLEAN / "rework_note_clean.csv")
v = note[note.is_valid == 1].copy()


def predict(t):
    best, score = "C9", 0
    for cat, pats in RULES.items():
        n = sum(1 for p in pats if re.search(p, t))
        if n > score:
            best, score = cat, n
    return best


v["category_code"] = v.note_text_clean.map(predict)
v[["note_id", "category_code"]].to_csv(CM.RES2 / "baseline_label.csv", index=False)
print(v.category_code.value_counts().sort_index().to_dict())
