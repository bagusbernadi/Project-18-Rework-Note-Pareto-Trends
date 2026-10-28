"""13: Estimasi dampak (Q11 dan Q12). Semua angka berlabel estimated: memakai asumsi di docs/definitions.md, bukan hasil pengukuran.

Q11: jam rework dihemat per bulan = catatan kategori teratas per bulan x penurunan x menit rework per unit / 60 (1 catatan = 1 unit, asumsi).
Q12: jam baca dan rekap manual dihemat per bulan = catatan per bulan x detik per catatan / 3600 (semua catatan setelah dibersihkan).
Hasil: impact_q11.csv, impact_q12.csv, impact_sensitivity.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

R = CM.RES2
par = pd.read_csv(R / "pareto.csv")
nl = pd.read_csv(R / "note_llm.csv")
dq = pd.read_csv(CM.RES1 / "data_quality.csv").set_index("kategori")
months = nl.month.nunique()
top = par.iloc[0]
per_month_top = top.n / months
clean_n = int(dq.loc["catatan setelah dibersihkan", "jumlah"])
per_month_all = clean_n / months
q11 = per_month_top * CM.TOP_REDUCTION * CM.REWORK_MIN_PER_UNIT / 60
q12 = per_month_all * CM.READ_SEC_PER_NOTE / 3600
pd.DataFrame([dict(kategori_teratas=top.category_code, nama=CM.CAT_NAME[top.category_code], catatan_per_bulan=per_month_top, penurunan=CM.TOP_REDUCTION,
                   menit_per_unit=CM.REWORK_MIN_PER_UNIT, jam_dihemat_per_bulan=q11, label="estimated")]).to_csv(R / "impact_q11.csv", index=False, float_format="%.10g")
pd.DataFrame([dict(catatan_per_bulan=per_month_all, detik_per_catatan=CM.READ_SEC_PER_NOTE, jam_dihemat_per_bulan=q12, label="estimated")]).to_csv(R / "impact_q12.csv", index=False, float_format="%.10g")
rows = []
for red in (0.10, 0.20, 0.30, 0.50):
    for mnt in (6, 12, 18):
        rows.append(dict(analisis="Q11", penurunan=red, parameter=mnt, satuan="menit per unit", jam_per_bulan=per_month_top * red * mnt / 60))
for sec in (10, 20, 30, 60):
    rows.append(dict(analisis="Q12", penurunan=float("nan"), parameter=sec, satuan="detik per catatan", jam_per_bulan=per_month_all * sec / 3600))
pd.DataFrame(rows).to_csv(R / "impact_sensitivity.csv", index=False, float_format="%.10g")
print(q11, q12)
