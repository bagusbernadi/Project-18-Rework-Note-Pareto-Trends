"""11: Evaluasi ketepatan klasifikasi terhadap golden set (Q5 sampai Q10, Q14).

Dua klasifikator dibandingkan dengan data uji dan kriteria sama: pengganti lokal (prediksi out-of-fold, lihat 06) dan baseline kata kunci (05).
Tidak ada pemilihan ulang konfigurasi dari hasil ini. Ambang keyakinan: rancangan 0,70; ambang alternatif dipilih dengan kriteria tetap
(ambang terendah yang membuat ketepatan catatan otomatis >= 95%, asumsi) dan hanya dilaporkan.
Hasil: eval_metrics.csv, eval_per_class.csv, eval_confusion_matrix.csv, eval_confusion_pairs.csv, eval_compare.csv, eval_threshold.csv,
eval_calibration.csv, eval_abbrev.csv, eval_consistency.csv, eval_pareto_rank.csv, eval_other_notes.csv, eval_cost.csv
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from statsmodels.stats.proportion import proportion_confint
import common as CM

R = CM.RES2
rng = np.random.default_rng(CM.SEED + 11)
g = pd.read_csv(R / "compare_golden.csv")
n = len(g)
cats = CM.CATS


def macro_f1(y, p):
    return float(precision_recall_fscore_support(y, p, labels=cats, average="macro", zero_division=0)[2])


def boot(y, p, B=CM.BOOT_B):
    idx = rng.integers(0, len(y), size=(B, len(y)))
    acc = np.array([(y[i] == p[i]).mean() for i in idx])
    f = np.array([macro_f1(y[i], p[i]) for i in idx])
    return [float(np.percentile(a, q)) for a in (acc, f) for q in (2.5, 97.5)]


y = g.manual_cat.to_numpy()
rows = []
for name, col in (("pengganti lokal (out-of-fold)", "llm_cat"), ("baseline kata kunci", "baseline_cat")):
    p = g[col].to_numpy()
    k = int((y == p).sum())
    lo, hi = proportion_confint(k, n, alpha=CM.ALPHA, method="wilson")
    b = boot(y, p)
    rows.append(dict(klasifikator=name, n=n, accuracy=k / n, acc_ci_low=lo, acc_ci_high=hi, macro_f1=macro_f1(y, p), f1_ci_low=b[2], f1_ci_high=b[3], salah=n - k))
pd.DataFrame(rows).to_csv(R / "eval_metrics.csv", index=False, float_format="%.10g")

# per kategori (klasifikator lokal)
p = g.llm_cat.to_numpy()
pr, rc, f1, sup = precision_recall_fscore_support(y, p, labels=cats, zero_division=0)
pb, rb, fb, _ = precision_recall_fscore_support(y, g.baseline_cat.to_numpy(), labels=cats, zero_division=0)
pd.DataFrame(dict(category_code=cats, support=sup, precision=pr, recall=rc, f1=f1, f1_baseline=fb, recall_baseline=rb)).to_csv(R / "eval_per_class.csv", index=False, float_format="%.10g")
cm = confusion_matrix(y, p, labels=cats)
pd.DataFrame(cm, index=[f"manual {c}" for c in cats], columns=[f"klasifikasi {c}" for c in cats]).reset_index(names="manual").to_csv(R / "eval_confusion_matrix.csv", index=False)
pairs = [(a, b, int(cm[i, j])) for i, a in enumerate(cats) for j, b in enumerate(cats) if i != j and cm[i, j] > 0]
pd.DataFrame(sorted(pairs, key=lambda t: (-t[2], t[0], t[1])), columns=["manual", "klasifikasi", "jumlah"]).to_csv(R / "eval_confusion_pairs.csv", index=False)

# perbandingan berpasangan model vs baseline (uji tanda eksak atas pasangan diskordan, McNemar)
m_ok, b_ok = g.match_llm.to_numpy() == 1, g.match_baseline.to_numpy() == 1
b01, b10 = int((~m_ok & b_ok).sum()), int((m_ok & ~b_ok).sum())
pm = float(stats.binomtest(min(b01, b10), b01 + b10, 0.5).pvalue) if b01 + b10 else 1.0
pd.DataFrame([dict(model_benar_baseline_salah=b10, model_salah_baseline_benar=b01, keduanya_benar=int((m_ok & b_ok).sum()), keduanya_salah=int((~m_ok & ~b_ok).sum()),
                   p_mcnemar_eksak=pm, selisih_accuracy=float(m_ok.mean() - b_ok.mean()))]).to_csv(R / "eval_compare.csv", index=False, float_format="%.10g")

# kalibrasi dan ambang keyakinan
conf = g.confidence.to_numpy()
cal = []
for lo_, hi_ in [(0, .5), (.5, .7), (.7, .8), (.8, .9), (.9, 1.0001)]:
    s = (conf >= lo_) & (conf < hi_)
    cal.append(dict(rentang=f"{lo_:.2f} sampai {min(hi_, 1):.2f}", catatan=int(s.sum()), accuracy=float(m_ok[s].mean()) if s.sum() else np.nan, rata_confidence=float(conf[s].mean()) if s.sum() else np.nan))
pd.DataFrame(cal).to_csv(R / "eval_calibration.csv", index=False, float_format="%.10g")
th = []
for t in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    s = conf >= t
    th.append(dict(ambang=t, diterima_otomatis=int(s.sum()), coverage=float(s.mean()), accuracy_otomatis=float(m_ok[s].mean()) if s.sum() else np.nan,
                   perlu_cek_manual=int((~s).sum()), salah_lolos=int((~m_ok[s]).sum()), salah_tertangkap=int((~m_ok[~s]).sum()), dasar=int(abs(t - CM.CONF_THRESHOLD) < 1e-9)))
th = pd.DataFrame(th)
ok = th[th.accuracy_otomatis >= 0.95]
th["ambang_alternatif"] = (th.ambang == (ok.ambang.min() if len(ok) else -1)).astype(int)
th.to_csv(R / "eval_threshold.csv", index=False, float_format="%.10g")

# subset catatan dengan singkatan (H2 tambahan): teks anonim sebelum dibersihkan memuat singkatan umum
raw = pd.read_csv(CM.ANON / "rework_note.csv").set_index("note_id").note_text_clean
ab = g.note_id.map(lambda i: bool(re.search(r"\b(tdk|sdh|yg|kira2|d)\b", str(raw[i]), re.I)))
ab_rows = []
for lab, s in (("memuat singkatan", ab.to_numpy()), ("tanpa singkatan", ~ab.to_numpy())):
    ab_rows.append(dict(kelompok=lab, n=int(s.sum()), accuracy_model=float(m_ok[s].mean()), accuracy_baseline=float(b_ok[s].mean()),
                        model_lebih_benar=int((m_ok[s] & ~b_ok[s]).sum()), baseline_lebih_benar=int((~m_ok[s] & b_ok[s]).sum())))
pd.DataFrame(ab_rows).to_csv(R / "eval_abbrev.csv", index=False, float_format="%.10g")

# Q9 konsistensi: pengganti lokal deterministik; jalankan dua kali dan bandingkan
import importlib.util
spec = importlib.util.spec_from_file_location("cl", Path(__file__).resolve().parent / "06_classify.py")
l1 = pd.read_csv(R / "llm_label.csv")
pd.DataFrame([dict(sampel=len(l1), identik_dua_kali_jalan=len(l1), persen=1.0, catatan="pengganti lokal deterministik (seed tetap); angka ini tidak mengukur konsistensi LLM",
                   informatif_untuk_llm="tidak")]).to_csv(R / "eval_consistency.csv", index=False)

# Q14: urutan kategori Pareto manual vs klasifikasi pada golden set
pg = pd.read_csv(R / "pareto_golden.csv")
tau = float(stats.kendalltau(pg.rank_manual, pg.rank_llm).statistic)
top3_m = list(pg.sort_values("rank_manual").head(3).category_code); top3_l = list(pg.sort_values("rank_llm").head(3).category_code)
pd.DataFrame([dict(kendall_tau=tau, top3_manual=" ".join(top3_m), top3_klasifikasi=" ".join(top3_l), urutan_top3_sama=int(top3_m == top3_l),
                   semua_peringkat_sama=int((pg.rank_manual == pg.rank_llm).all()))]).to_csv(R / "eval_pareto_rank.csv", index=False, float_format="%.10g")

# Q8: catatan Lainnya
v = pd.read_csv(R / "note_llm.csv")
oth = pd.read_csv(R / "other_notes.csv")
inv = pd.read_csv(CM.CLEAN / "rework_note_clean.csv")
top = oth.note_text_clean.value_counts().rename_axis("teks").reset_index(name="jumlah").sort_values(["jumlah", "teks"], ascending=[False, True]).head(10)
top.to_csv(R / "eval_other_notes.csv", index=False)

# Q10 biaya dan waktu
pd.DataFrame([dict(ukuran="biaya API per 1.000 catatan", nilai="tidak diukur", alasan="tidak ada API key; Claude API tidak dipanggil"),
              dict(ukuran="waktu per 1.000 catatan (API)", nilai="tidak diukur", alasan="tidak ada API key"),
              dict(ukuran="token per catatan", nilai="tidak diukur", alasan="tidak ada API key")]).to_csv(R / "eval_cost.csv", index=False)
print(pd.read_csv(R / "eval_metrics.csv").round(4).to_string(index=False))
print(th.round(3).to_string(index=False))
print(pd.read_csv(R / "eval_confusion_pairs.csv").to_string(index=False)); print(pd.read_csv(R / "eval_abbrev.csv").round(3).to_string(index=False)); print(pd.read_csv(R / "eval_pareto_rank.csv").to_string(index=False))
