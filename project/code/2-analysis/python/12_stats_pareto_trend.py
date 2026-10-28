"""12: Uji statistik Pareto dan tren (Q1 sampai Q4) dan kesimpulan hipotesis H1 sampai H5.

Kriteria keputusan ditetapkan di docs/definitions.md sebelum hasil dilihat (konstanta di common.py).
Hasil: stats_pareto.csv, stats_station_cell.csv, stats_chi.csv, stats_trend_flags.csv, stats_cross_cells.csv, hypotheses.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint
import common as CM

R = CM.RES2
cats = CM.CATS
nl = pd.read_csv(R / "note_llm.csv")
N = len(nl)
par = pd.read_csv(R / "pareto.csv")
st = pd.read_csv(R / "cross_station_cat.csv")


def wil(k, n):
    lo, hi = proportion_confint(k, n, alpha=CM.ALPHA, method="wilson")
    return float(lo), float(hi)


# Q1 / H1: kumulatif pada 2 dan 3 kategori teratas, dan jumlah kategori untuk mencapai band
rows = []
for k in (2, 3, 4, 5):
    cum = int(par.n.head(k).sum())
    lo, hi = wil(cum, N)
    rows.append(dict(k_kategori=k, kategori=" ".join(par.category_code.head(k)), n=cum, cum_share=cum / N, ci_low=lo, ci_high=hi,
                     dalam_band=int(CM.H1_BAND[0] <= cum / N <= CM.H1_BAND[1])))
sp = pd.DataFrame(rows)
sp["k_untuk_80"] = int((par.cum_share >= CM.TOP_SHARE_TARGET).idxmax() + 1)
sp.to_csv(R / "stats_pareto.csv", index=False, float_format="%.10g")
h1 = bool(sp[sp.k_kategori.isin([2, 3])].dalam_band.any())

# Q2 / H4: sel stasiun x kategori. porsi seharusnya = porsi stasiun dari seluruh catatan; uji binomial satu sisi, Holm atas semua sel
tot_st = st.groupby("station_code").n.sum()
tot_cat = st.groupby("category_code").n.sum()
cells = []
for _, r in st.sort_values(["station_code", "category_code"]).iterrows():
    exp_p = tot_st[r.station_code] / N
    obs = r.n / tot_cat[r.category_code]
    p = float(stats.binomtest(int(r.n), int(tot_cat[r.category_code]), exp_p, alternative="greater").pvalue)
    cells.append(dict(station_code=r.station_code, category_code=r.category_code, n=int(r.n), n_kategori=int(tot_cat[r.category_code]),
                      porsi_stasiun=float(obs), porsi_seharusnya=float(exp_p), rasio=float(obs / exp_p), p_mentah=p))
cd = pd.DataFrame(cells)
cd["p_holm"] = multipletests(cd.p_mentah, method="holm")[1]
cd["memenuhi_h4"] = ((cd.rasio >= CM.H4_MIN_SHARE_RATIO) & (cd.p_holm < CM.ALPHA)).astype(int)
cd = cd.sort_values(["rasio", "station_code", "category_code"], ascending=[False, True, True]).reset_index(drop=True)
cd.to_csv(R / "stats_station_cell.csv", index=False, float_format="%.10g")
h4 = int(cd.memenuhi_h4.sum())

# chi-square + Cramér's V untuk stasiun, shift, model, bulan terhadap kategori
chi = []


def chi_v(name, col):
    t = pd.crosstab(nl[col], nl.llm_cat).reindex(columns=cats, fill_value=0)
    t = t.loc[:, t.sum() > 0]
    c2, p, dof, exp = stats.chi2_contingency(t)
    v = float(np.sqrt(c2 / (t.values.sum() * (min(t.shape) - 1))))
    chi.append(dict(faktor=name, chi2=float(c2), dof=int(dof), p=float(p), cramers_v=v, n=int(t.values.sum()), sel_harapan_min=float(exp.min())))
    return t, exp


tabs = {}
for name, col in (("stasiun", "station_code"), ("shift", "shift"), ("model", "model_code"), ("bulan", "month")):
    tabs[name] = chi_v(name, col)
ch = pd.DataFrame(chi)
ch["p_holm"] = multipletests(ch.p, method="holm")[1]
ch["signifikan"] = (ch.p_holm < CM.ALPHA).astype(int)
ch.to_csv(R / "stats_chi.csv", index=False, float_format="%.10g")

# Q4: sel shift/model x kategori dengan residual terstandar; uji binomial dua sisi, Holm
cc = []
for name in ("shift", "model"):
    t, exp = tabs[name]
    for lv in t.index:
        for c in t.columns:
            n_lv, n_c = int(t.loc[lv].sum()), int(t[c].sum())
            p = float(stats.binomtest(int(t.loc[lv, c]), n_c, n_lv / N).pvalue)
            cc.append(dict(faktor=name, level=lv, category_code=c, n=int(t.loc[lv, c]), porsi_dalam_kategori=t.loc[lv, c] / n_c, porsi_seharusnya=n_lv / N, p_mentah=p))
cc = pd.DataFrame(cc)
cc["p_holm"] = multipletests(cc.p_mentah, method="holm")[1]
cc["rasio"] = cc.porsi_dalam_kategori / cc.porsi_seharusnya
cc["signifikan"] = (cc.p_holm < CM.ALPHA).astype(int)
cc.to_csv(R / "stats_cross_cells.csv", index=False, float_format="%.10g")

# Q3: lonjakan bulanan per kategori: p-chart, batas 3 sigma dari porsi gabungan (asumsi), Holm bukan dipakai (aturan kendali)
tm = pd.read_csv(R / "trend_month.csv")
mt = tm.groupby("month").n.sum()
flag = []
for c in cats:
    p0 = tm[tm.category_code == c].n.sum() / N
    for m, tot in mt.items():
        k = int(tm[(tm.month == m) & (tm.category_code == c)].n.sum())
        sig = np.sqrt(p0 * (1 - p0) / tot)
        z = (k / tot - p0) / sig
        flag.append(dict(month=m, category_code=c, n=k, share=k / tot, share_rata=p0, z=float(z), lonjakan=int(z > 3), penurunan=int(z < -3)))
fl = pd.DataFrame(flag)
fl.to_csv(R / "stats_trend_flags.csv", index=False, float_format="%.10g")

# H5: catatan terlalu singkat, dasar catatan setelah ganda dibuang
dq = pd.read_csv(CM.RES1 / "data_quality.csv").set_index("kategori")
short = int(dq.loc["terlalu singkat (< 3 kata)", "jumlah"])
base = int(dq.loc["catatan setelah dibersihkan", "jumlah"])
raw_n = int(dq.loc["catatan (mentah)", "jumlah"])
sh_lo, sh_hi = wil(short, base)
h5 = CM.H5_BAND[0] <= short / base <= CM.H5_BAND[1]

# H3 dan H2 dari evaluasi
pairs = pd.read_csv(R / "eval_confusion_pairs.csv")
errs = int(pairs.jumlah.sum()) if len(pairs) else 0
pairs["pasang"] = pairs.apply(lambda r: " ".join(sorted([r.manual, r.klasifikasi])), axis=1)
pu = pairs.groupby("pasang").jumlah.sum().sort_values(ascending=False)
c23 = int(pu.get("C2 C3", 0))
em = pd.read_csv(R / "eval_metrics.csv")
cmp_ = pd.read_csv(R / "eval_compare.csv").iloc[0]

top3 = " ".join(par.category_code.head(3))
s3 = sp[sp.k_kategori == 3].iloc[0]
s2 = sp[sp.k_kategori == 2].iloc[0]
best = cd.iloc[0]
hy = []
hy.append(dict(kode="H1", hipotesis="Dua atau tiga kategori menyumbang sekitar 80% catatan rework.",
               hasil="Tidak terbukti" if not h1 else "Terbukti",
               bukti=f"2 kategori {s2.cum_share:.4f}; 3 kategori ({top3}) {s3.cum_share:.4f}; band {CM.H1_BAND[0]} sampai {CM.H1_BAND[1]}; kategori untuk mencapai 80%: {int(sp.k_untuk_80.iloc[0])}"))
hy.append(dict(kode="H2", hipotesis="LLM lebih tepat dibanding baseline kata kunci, terutama pada catatan yang memakai singkatan.",
               hasil="Belum bisa disimpulkan",
               bukti=f"LLM tidak diuji (tanpa API key); pengganti lokal accuracy {em.accuracy.iloc[0]:.4f} vs baseline {em.accuracy.iloc[1]:.4f}, selisih {cmp_.selisih_accuracy:.4f}, McNemar p {cmp_.p_mcnemar_eksak:.4f}"))
hy.append(dict(kode="H3", hipotesis="Kategori yang mirip, misalnya goresan dan retak, paling sering tertukar.",
               hasil="Belum bisa disimpulkan" if errs < CM.MIN_ERRORS_H3 else ("Terbukti" if (len(pu) and pu.index[0] == "C2 C3") else "Tidak terbukti"),
               bukti=f"total salah {errs} pada golden set (minimum {CM.MIN_ERRORS_H3}); tertukar C2 dan C3: {c23}"))
hy.append(dict(kode="H4", hipotesis="Satu stasiun menjadi sumber utama untuk satu kategori tertentu.",
               hasil="Terbukti" if h4 else "Tidak terbukti",
               bukti=f"{h4} dari {len(cd)} sel memenuhi rasio >= {CM.H4_MIN_SHARE_RATIO} dan Holm p < {CM.ALPHA}; tertinggi {best.station_code} {best.category_code} rasio {best.rasio:.4f}"))
hy.append(dict(kode="H5", hipotesis="Sekitar 5 sampai 10% catatan terlalu singkat atau tidak jelas untuk diklasifikasi.",
               hasil="Terbukti" if h5 else "Tidak terbukti",
               bukti=f"{short} dari {base} catatan ({short / base:.4f}; CI Wilson {sh_lo:.4f} sampai {sh_hi:.4f}); terhadap catatan mentah {short / raw_n:.4f}"))
pd.DataFrame(hy).to_csv(R / "hypotheses.csv", index=False)
pd.DataFrame([dict(terlalu_singkat=short, dasar=base, proporsi=short / base, ci_low=sh_lo, ci_high=sh_hi, proporsi_mentah=short / raw_n)]).to_csv(R / "stats_short.csv", index=False, float_format="%.10g")
print(sp.round(4).to_string(index=False)); print(ch.round(4).to_string(index=False)); print(cd.head(8).round(4).to_string(index=False))
print(cc[cc.signifikan == 1].round(4).to_string(index=False)); print(fl[(fl.lonjakan == 1) | (fl.penurunan == 1)].round(3).to_string(index=False))
print(pd.DataFrame(hy)[["kode", "hasil", "bukti"]].to_string(index=False))
