"""16: One-sheet infografik (PNG dan PDF). Semua angka dibaca dari results/2-analysis."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import common as CM

R = CM.RES2
par = pd.read_csv(R / "pareto.csv")
em = pd.read_csv(R / "eval_metrics.csv")
hy = pd.read_csv(R / "hypotheses.csv").set_index("kode")
q11 = pd.read_csv(R / "impact_q11.csv").iloc[0]
q12 = pd.read_csv(R / "impact_q12.csv").iloc[0]
cell = pd.read_csv(R / "stats_station_cell.csv")
sig = cell[cell.memenuhi_h4 == 1].sort_values(["station_code", "category_code"])
k80 = int((par.cum_share >= CM.TOP_SHARE_TARGET).idxmax() + 1)

fig = plt.figure(figsize=(8.27, 11.69))
fig.text(0.5, 0.95, "Penyebab rework apa yang paling sering?", ha="center", fontsize=20, weight="bold", color="#174EA6")
fig.text(0.5, 0.92, "Project 18: Rework Note Analysis (data simulasi, anonim; klasifikasi pengganti lokal, bukan Claude API)", ha="center", fontsize=10, color="#5F6368")
ax = fig.add_axes([0.1, 0.55, 0.82, 0.31])
lab = [f"{c}\n{CM.CAT_NAME[c].split(' /')[0]}" for c in par.category_code]
ax.bar(lab, par.n, color=["#1A73E8" if i < k80 else "#9AA0A6" for i in range(len(par))])
ax.set_ylabel("Jumlah catatan")
ax2 = ax.twinx()
ax2.plot(lab, par.cum_share * 100, color="#D93025", marker="o")
ax2.axhline(80, color="#D93025", ls="--", lw=0.8)
ax2.set_ylim(0, 100); ax2.set_ylabel("Kumulatif (%)")
ax.set_title(f"Pareto: {k80} kategori diperlukan untuk mencapai 80%", loc="left", fontsize=12, color="#174EA6")
ax.tick_params(axis="x", labelsize=7)
for s in ("top",):
    ax.spines[s].set_visible(False); ax2.spines[s].set_visible(False)
top = par.iloc[0]
bullets = [
    f"Penyebab terbesar: {top.category_code} {CM.CAT_NAME[top.category_code]} ({top.share * 100:.1f}% catatan).",
    f"Tiga kategori teratas hanya {par.cum_share.iloc[2] * 100:.1f}% (H1: {hy.loc['H1', 'hasil']}).",
    "Stasiun menonjol: " + ", ".join(f"{r.station_code} untuk {r.category_code}" for r in sig.itertuples()) + ".",
    f"Pengganti lokal: accuracy {em.accuracy.iloc[0] * 100:.1f}%, baseline kata kunci {em.accuracy.iloc[1] * 100:.1f}% pada golden set.",
    f"Estimasi (estimated): {q11.jam_dihemat_per_bulan:.1f} jam rework dan {q12.jam_dihemat_per_bulan:.1f} jam baca per bulan.",
    "Batasan: data simulasi, teks templat sederhana, Claude API tidak diuji.",
]
fig.text(0.10, 0.47, "Temuan utama", fontsize=13, weight="bold", color="#174EA6")
for i, b in enumerate(bullets):
    fig.text(0.10, 0.435 - i * 0.04, f"• {b}", fontsize=10, color="#202124")
fig.text(0.5, 0.03, "Angka: results/2-analysis. Estimasi berlabel estimated.", ha="center", fontsize=8, color="#5F6368")
fig.savefig(CM.OUTPUTS / "infographic.png", dpi=150)
fig.savefig(CM.OUTPUTS / "infographic.pdf", metadata={"CreationDate": None, "ModDate": None})
print("infografik ditulis")
