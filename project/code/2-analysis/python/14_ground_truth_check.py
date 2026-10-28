"""14: Cek kebenaran simulasi (ground truth). Satu-satunya skrip analisis yang membaca data/raw/truth.csv dan data/mapping.json.

Parameter yang ditanam generator (00_generate_raw.py): bobot dasar kategori, pengganda untuk empat stasiun (tiga kali untuk dua pasangan,
empat kali dan dua kali untuk dua lainnya; nama asli hanya ada di generator dan kunci pemetaan), 75% catatan C9 dibuat sangat singkat, 60 catatan ganda di akhir. Tidak ada efek shift, model, atau bulan yang ditanam.
Hasil: ground_truth_check.csv, truth_accuracy.csv
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

R = CM.RES2
tr = pd.read_csv(CM.RAW / "truth.csv").set_index("note_id").category_code
mp = dict(json.load(open(CM.MAPPING))["station"])
nl = pd.read_csv(R / "note_llm.csv")
bl = pd.read_csv(R / "baseline_label.csv")
nl["truth"] = nl.note_id.map(tr)
acc_llm = float((nl.truth == nl.llm_cat).mean())
bl["truth"] = bl.note_id.map(tr)
bcol = "category_code"
acc_bl = float((bl.truth == bl[bcol]).mean())
bl_valid = bl[bl.note_id.isin(nl.note_id)]
acc_bl_valid = float((bl_valid.truth == bl_valid[bcol]).mean())
pd.DataFrame([dict(klasifikator="pengganti lokal", n=len(nl), accuracy_terhadap_kebenaran=acc_llm),
              dict(klasifikator="baseline kata kunci", n=len(bl_valid), accuracy_terhadap_kebenaran=acc_bl_valid)]).to_csv(R / "truth_accuracy.csv", index=False, float_format="%.10g")

par = pd.read_csv(R / "pareto.csv")
cell = pd.read_csv(R / "stats_station_cell.csv")
ch = pd.read_csv(R / "stats_chi.csv").set_index("faktor")
fl = pd.read_csv(R / "stats_trend_flags.csv")
sh = pd.read_csv(R / "stats_short.csv").iloc[0]
tc = nl.truth.value_counts().sort_index()
true_rank = tc.sort_values(ascending=False, kind="stable").index.tolist()
rows = []
planted = {"Dispensing": "C4", "Placement": "C5", "Final Test": "C7", "AOI": "C2"}
for nm, c in planted.items():
    code = mp[nm]
    r = cell[(cell.station_code == code) & (cell.category_code == c)].iloc[0]
    rows.append(dict(fakta=f"{code} menyumbang lebih banyak {c}", ditanam="pengganda 2 sampai 4 kali",
                     terdeteksi=f"rasio {r.rasio:.2f}; Holm p {r.p_holm:.3g}", hasil="Sesuai" if r.memenuhi_h4 == 1 else "Sebagian"))
rows.append(dict(fakta="Kategori teratas pada Pareto adalah C4", ditanam="bobot dasar C4 0,23 tertinggi",
                 terdeteksi=f"teratas {par.category_code.iloc[0]}; kebenaran {true_rank[0]}", hasil="Sesuai" if par.category_code.iloc[0] == true_rank[0] == "C4" else "Sebagian"))
rows.append(dict(fakta="Urutan 5 kategori teratas sama dengan kebenaran", ditanam="bobot dasar dan pengganda stasiun",
                 terdeteksi=f"hasil {' '.join(par.category_code.head(5))}; kebenaran {' '.join(true_rank[:5])}", hasil="Sesuai" if par.category_code.head(5).tolist() == true_rank[:5] else "Sebagian"))
rows.append(dict(fakta="Tidak ada efek shift dan model", ditanam="tidak ada",
                 terdeteksi=f"p Holm shift {ch.loc['shift', 'p_holm']:.3f}; model {ch.loc['model', 'p_holm']:.3f}", hasil="Sesuai" if (ch.loc["shift", "signifikan"] == 0 and ch.loc["model", "signifikan"] == 0) else "Sebagian"))
rows.append(dict(fakta="Tidak ada lonjakan bulanan yang ditanam", ditanam="tidak ada",
                 terdeteksi=f"{int(fl.lonjakan.sum())} lonjakan dan {int(fl.penurunan.sum())} penurunan melewati 3 sigma", hasil="Sesuai" if fl.lonjakan.sum() == 0 and fl.penurunan.sum() == 0 else "Sebagian"))
rows.append(dict(fakta="Sekitar 9% catatan terlalu singkat", ditanam="75% dari C9 (bobot 0,12) dibuat sangat singkat",
                 terdeteksi=f"{sh.proporsi:.4f} dari catatan setelah dibersihkan", hasil="Sesuai" if 0.05 <= sh.proporsi <= 0.10 else "Sebagian"))
rows.append(dict(fakta="Ketepatan klasifikasi terhadap kebenaran generator", ditanam="teks dari templat sederhana",
                 terdeteksi=f"pengganti lokal {acc_llm:.4f}; baseline {acc_bl_valid:.4f}", hasil="Sesuai" if acc_llm >= 0.95 else "Sebagian"))
out = pd.DataFrame(rows)
out.to_csv(R / "ground_truth_check.csv", index=False)
print(out.to_string(index=False)); print(pd.read_csv(R / "truth_accuracy.csv"))
