"""Generator Report v2 (Project 18). Dijalankan paling akhir, setelah seluruh pipeline dijalankan ulang dari nol.

Input : design-and-report/src/page_v1.html (rancangan, pane Design TIDAK diubah), project/results/*.
Output: design-and-report/index.html
Setiap angka di teks Report berasal dari CSV lewat helper report_lib (I, D, P, cs). audit() memeriksa token angka
yang tidak berasal dari data dan tidak ada di STATIC. truth.csv tidak dibaca di sini (hanya hasil cek 14).
"""
import re
import sys
from html import escape as esc
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO / "project"
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(HERE))
import pandas as pd
import common as C
import report_lib as R
from report_lib import I, D, P, cs, pill, BLUE, GREY, table, qa, legend, bars, lines, pareto_svg, audit

SRC = (HERE / "page_v1.html").read_text(encoding="utf-8")
CSS_EXTRA = (HERE / "report.css").read_text(encoding="utf-8")
r1, r2, r3 = C.RES1, C.RES2, C.RES3


def rd(d, n):
    return pd.read_csv(d / n)


par = rd(r2, "pareto.csv"); ps = rd(r2, "pareto_station.csv"); tm = rd(r2, "trend_month.csv"); pg = rd(r2, "pareto_golden.csv")
em = rd(r2, "eval_metrics.csv"); epc = rd(r2, "eval_per_class.csv"); ecp = rd(r2, "eval_confusion_pairs.csv"); ecmp = rd(r2, "eval_compare.csv").iloc[0]
ecal = rd(r2, "eval_calibration.csv"); eth = rd(r2, "eval_threshold.csv"); eab = rd(r2, "eval_abbrev.csv"); eoth = rd(r2, "eval_other_notes.csv")
epr = rd(r2, "eval_pareto_rank.csv").iloc[0]; econ = rd(r2, "eval_consistency.csv").iloc[0]; ecost = rd(r2, "eval_cost.csv")
spar = rd(r2, "stats_pareto.csv"); scell = rd(r2, "stats_station_cell.csv"); schi = rd(r2, "stats_chi.csv").set_index("faktor")
sflag = rd(r2, "stats_trend_flags.csv"); scross = rd(r2, "stats_cross_cells.csv"); sshort = rd(r2, "stats_short.csv").iloc[0]
hyp = rd(r2, "hypotheses.csv"); q11 = rd(r2, "impact_q11.csv").iloc[0]; q12 = rd(r2, "impact_q12.csv").iloc[0]; isens = rd(r2, "impact_sensitivity.csv")
gtc = rd(r2, "ground_truth_check.csv"); tacc = rd(r2, "truth_accuracy.csv")
cfg = rd(r2, "classifier_config.csv"); cpt = rd(r2, "claude_pipeline_test.csv"); oth = rd(r2, "other_notes.csv")
cx_py = rd(r2, "crosscheck_sql_pandas.csv"); cx_ex = rd(r2, "crosscheck_excel.csv"); ll = rd(r2, "llm_label.csv"); nl = rd(r2, "note_llm.csv")
dq = rd(r1, "data_quality.csv").set_index("kategori"); dbc = rd(r1, "db_checks.csv"); dbt = rd(r1, "db_tables.csv")
fp = rd(r1, "fingerprint_check.csv"); dtest = rd(r3, "dashboard_test.csv"); leak = rd(r3, "leak_scan.csv")
anon = pd.read_csv(C.ANON / "rework_note.csv"); redl = pd.read_csv(C.ANON / "redaction_log.csv")

CN = C.CAT_NAME
H = {r.kode: r for r in hyp.itertuples()}
N = len(nl)
top = par.iloc[0]
n_db_ok = int((dbc.hasil == "lulus").sum()); n_fp_ok = int((fp.hasil == "cocok").sum())
n_py, n_py_ok = len(cx_py), int(cx_py.cocok.sum())
n_ex, n_ex_ok = len(cx_ex), int(cx_ex.cocok.sum())
n_dash, n_dash_ok = len(dtest), int((dtest.hasil == "lulus").sum())
n_leak, n_leak_fail = len(leak), int((leak.hasil == "gagal").sum())
n_cpt, n_cpt_ok = len(cpt), int((cpt.hasil == "lulus").sum())
n_gt, n_gt_ok = len(gtc), int((gtc.hasil == "Sesuai").sum())
dqv = {k: int(dq.loc[k, "jumlah"]) for k in dq.index}
k80 = int(spar.k_untuk_80.iloc[0])
s3 = spar[spar.k_kategori == 3].iloc[0]; s5 = spar[spar.k_kategori == 5].iloc[0]
eml, ebl = em.iloc[0], em.iloc[1]
n_gold = int(eml.n)
n_err = int(eml.salah)
sig = scell[scell.memenuhi_h4 == 1].sort_values(["station_code", "category_code"])
n_other = int((nl.llm_cat == "C9").sum())
mon = sorted(tm.month.unique())
n_mon = len(mon)
nrows_cell = len(scell)
n_queue = int((nl.confidence < C.CONF_THRESHOLD).sum())
th07 = eth[eth.dasar == 1].iloc[0]


def pv(p):
    return "< 0,001" if float(p) < 0.001 else D(float(p), 3)


def ci(lo, hi, d=1):
    return f"CI 95% {D(lo * 100, d)}% sampai {D(hi * 100, d)}%"


def verdict_pill(v):
    return pill(v, {"Terbukti": "", "Belum bisa disimpulkan": "p", "Tidak terbukti": "d"}.get(v, "d"))


def kpi(v, l, d, color):
    return f'<div class="card kpi" style="--h:var(--{color})"><span class="v">{v}</span><span class="l">{l}</span><span class="d">{d}</span></div>'


def nm(c):
    return f"{c} ({CN[c]})"


# ---------- grafik ----------
chart_par = pareto_svg(list(par.category_code), list(par.share), list(par.cum_share), [i < k80 for i in range(len(par))],
                       [f"{nm(r.category_code)}: {D(r.share * 100, 1)}% ({I(r.n)} catatan), kumulatif {D(r.cum_share * 100, 1)}%" for r in par.itertuples()],
                       "Grafik Pareto kategori (garis putus-putus 80%)")
top5 = list(par.category_code.head(5))
COLS = {"C4": "#1A73E8", "C5": "#E8710A", "C1": "#188038", "C7": "#9334E6", "C2": "#D93025"}
chart_tr = lines([m[5:] for m in mon], [(c, COLS[c], 2, [float(tm[(tm.category_code == c) & (tm.month == m)].share.iloc[0]) for m in mon]) for c in top5],
                 lambda v: D(v * 100, 0) + "%", "Grafik porsi bulanan lima kategori teratas", h=250, zero=True)

# ---------- pertanyaan ----------
QS = [
    (1, "Kategori penyebab apa saja yang menyumbang sekitar 80% dari semua catatan rework?", "Utama"),
    (2, "Kategori apa yang dominan di tiap stasiun?", "Utama"),
    (3, "Bagaimana tren bulanan setiap kategori, dan adakah bulan dengan lonjakan?", "Utama"),
    (4, "Apakah kategori tertentu lebih sering di shift atau model tertentu?", "Pendukung"),
    (5, "Seberapa tepat klasifikasi LLM dibanding label manual?", "Utama"),
    (6, "Kategori mana yang paling sering salah, dan dengan kategori apa tertukar?", "Utama"),
    (7, "Apakah LLM lebih tepat dibanding cara sederhana berbasis kata kunci?", "Utama"),
    (8, 'Berapa persen catatan masuk "Lainnya / tidak jelas", dan seperti apa isinya?', "Pendukung"),
    (9, "Apakah hasil tetap sama jika catatan yang sama diklasifikasi ulang?", "Pendukung"),
    (10, "Berapa biaya API dan waktu proses per 1.000 catatan?", "Pendukung"),
    (11, "Berapa jam rework yang bisa dihemat jika kategori teratas turun sekian persen?", "Utama"),
    (12, "Berapa jam baca dan rekap manual yang dihemat per bulan?", "Tambahan"),
    (13, "Berapa persen catatan tidak valid (kosong, ganda, terlalu singkat), dan bagaimana ditangani?", "Utama"),
    (14, "Apakah Pareto dari label LLM sama dengan Pareto dari label manual pada sampel yang sama?", "Utama"),
]
WARN = {3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14}
NOANS = {9, 10}
top_st = ps[ps.rank_in_station == 1].sort_values("station_code")
fl_up, fl_dn = int(sflag.lonjakan.sum()), int(sflag.penurunan.sum())
cmax = sflag.z.abs().max()
pairs_txt = "; ".join(f"{r.manual} dinilai {r.klasifikasi} ({I(r.jumlah)})" for r in ecp.itertuples()) or "tidak ada"
c23 = int(ecp[ecp.apply(lambda r: sorted([r.manual, r.klasifikasi]) == ['C2', 'C3'], axis=1)].jumlah.sum()) if len(ecp) else 0
weak = epc.sort_values(["recall", "category_code"]).iloc[0]
ab_y, ab_n = eab.iloc[0], eab.iloc[1]
c1 = pg.set_index("category_code")
ANS = {
    1: (f"Penyebab terbesar {nm(top.category_code)} ({D(top.share * 100, 1)}%, {I(top.n)} dari {I(N)} catatan valid). Dua kategori teratas {P(spar.iloc[0].cum_share, 1)} dan tiga kategori teratas ({' '.join(par.category_code.head(3))}) "
        f"{P(s3.cum_share, 1)} ({ci(s3.ci_low, s3.ci_high)}). Diperlukan {I(k80)} kategori untuk mencapai 80% (kumulatif {P(s5.cum_share, 1)}). Hipotesis H1 (dua atau tiga kategori) tidak didukung data."),
    2: ("Kategori dominan per stasiun: " + ", ".join(f"{r.station_code} {r.category_code} ({D(r.share * 100, 0)}%)" for r in top_st.itertuples())
        + f". Stasiun dan kategori saling terkait: chi-square {D(schi.loc['stasiun', 'chi2'], 0)}, p {pv(schi.loc['stasiun', 'p'])}, Cramér's V {D(schi.loc['stasiun', 'cramers_v'], 3)} (efek kecil sampai sedang). "
        f"{I(len(sig))} sel menonjol (rasio >= {D(C.H4_MIN_SHARE_RATIO, 1)}, Holm p < 0,05): " + ", ".join(f"{r.station_code} untuk {r.category_code} (rasio {D(r.rasio, 2)})" for r in sig.itertuples()) + "."),
    3: (f"Tidak ada bulan yang melewati batas 3 sigma pada {I(len(sflag))} sel kategori-bulan ({I(fl_up)} lonjakan, {I(fl_dn)} penurunan; |z| terbesar {D(cmax, 2)}). "
        f"Komposisi kategori antar bulan berbeda tipis: chi-square p {pv(schi.loc['bulan', 'p'])} sebelum koreksi, p Holm {pv(schi.loc['bulan', 'p_holm'])}, Cramér's V {D(schi.loc['bulan', 'cramers_v'], 3)}. "
        f"Batas 3 sigma adalah asumsi project; sel kecil (harapan minimum {D(schi.loc['bulan', 'sel_harapan_min'], 1)}) membuat uji kurang andal."),
    4: (f"Tidak. Kategori tidak berbeda menurut shift (p Holm {pv(schi.loc['shift', 'p_holm'])}, V {D(schi.loc['shift', 'cramers_v'], 3)}) maupun model (p Holm {pv(schi.loc['model', 'p_holm'])}, V {D(schi.loc['model', 'cramers_v'], 3)}). "
        f"Tidak ada sel shift atau model yang signifikan setelah Holm ({I(int(scross.signifikan.sum()))} dari {I(len(scross))})."),
    5: (f"Pada golden set ({I(n_gold)} catatan valid), pengganti lokal mencapai accuracy {P(eml.accuracy, 1)} ({ci(eml.acc_ci_low, eml.acc_ci_high)}) dan macro F1 {D(eml.macro_f1, 3)} ({D(eml.f1_ci_low, 3)} sampai {D(eml.f1_ci_high, 3)}, bootstrap). "
        f"Ini <b>bukan hasil Claude API</b>: LLM tidak diuji karena tidak ada API key. Prediksi adalah out-of-fold; label manual adalah kebenaran generator tanpa noise, dan teks dibuat dari templat sederhana, jadi angka terlalu optimistis dibanding catatan nyata."),
    6: (f"Hanya {I(n_err)} kesalahan dari {I(n_gold)} catatan: {pairs_txt}. Recall terendah {weak.category_code} ({D(weak.recall * 100, 1)}%, dukungan {I(weak.support)} catatan). "
        f"Dengan dua kesalahan, pola pasangan yang tertukar tidak bisa disimpulkan (H3: {H['H3'].hasil.lower()}); pasangan goresan dan retak (C2 dan C3) tertukar {I(c23)} kali."),
    7: (f"Baseline kata kunci mencapai accuracy {P(ebl.accuracy, 1)} dibanding {P(eml.accuracy, 1)} pengganti lokal; selisih {D(ecmp.selisih_accuracy * 100, 2)} poin tidak signifikan (McNemar eksak p {D(ecmp.p_mcnemar_eksak, 2)}). "
        f"Pada catatan bersingkatan ({I(ab_y.n)} catatan) accuracy pengganti lokal {P(ab_y.accuracy_model, 1)} dan baseline {P(ab_y.accuracy_baseline, 1)}. <b>LLM tidak diuji</b>, jadi H2 tidak bisa disimpulkan; templat teks sederhana membuat aturan kata kunci sama baiknya."),
    8: (f"{I(n_other)} dari {I(N)} catatan valid ({P(n_other / N, 1)}) masuk Lainnya. Isinya berulang: " + "; ".join(f"\"{esc(r.teks)}\" ({I(r.jumlah)})" for r in eoth.head(2).itertuples())
        + f". Catatan yang terlalu singkat ({I(dqv['terlalu singkat (< 3 kata)'])}) tidak diklasifikasi dan dilaporkan terpisah (Q13). Isinya hanya berasal dari beberapa kalimat templat generator, bukan catatan nyata."),
    9: (f"Pengganti lokal deterministik: {I(econ.identik_dua_kali_jalan)} dari {I(econ.sampel)} catatan identik pada dua kali jalan ({P(econ.persen, 0)}). Angka ini <b>tidak informatif</b> untuk LLM, yang bisa berbeda antar panggilan; Q9 belum terjawab untuk Claude API."),
    10: ("Tidak diukur. Claude API tidak dipanggil (tidak ada API key), sehingga biaya, waktu, dan token per 1.000 catatan tidak ada. Pemanggil API dan prompt sudah dibuat dan diuji dengan klien palsu "
         f"({I(n_cpt_ok)} dari {I(n_cpt)} pemeriksaan lulus), siap dijalankan bila key tersedia."),
    11: (f"Estimasi (estimated): menurunkan {nm(q11.kategori_teratas)} sebesar {P(q11.penurunan, 0)} menghemat sekitar {D(q11.jam_dihemat_per_bulan, 1)} jam rework per bulan "
         f"({D(q11.catatan_per_bulan, 0)} catatan per bulan x {I(q11.menit_per_unit)} menit per unit). Asumsi: satu catatan sama dengan satu unit yang di-rework dan 12 menit per unit (bukan dari data); sensitivitas {D(isens[isens.analisis == 'Q11'].jam_per_bulan.min(), 1)} sampai {D(isens[isens.analisis == 'Q11'].jam_per_bulan.max(), 1)} jam per bulan."),
    12: (f"Estimasi (estimated): sekitar {D(q12.jam_dihemat_per_bulan, 1)} jam baca dan rekap per bulan ({D(q12.catatan_per_bulan, 0)} catatan per bulan x {I(q12.detik_per_catatan)} detik). "
         f"Detik per catatan adalah asumsi; sensitivitas {D(isens[isens.analisis == 'Q12'].jam_per_bulan.min(), 1)} sampai {D(isens[isens.analisis == 'Q12'].jam_per_bulan.max(), 1)} jam per bulan."),
    13: (f"Dari {I(dqv['catatan (mentah)'])} catatan mentah: {I(dqv['teks kosong'])} kosong, {I(dqv['catatan ganda'])} ganda (dibuang, baris pertama dipertahankan), {I(dqv['terlalu singkat (< 3 kata)'])} terlalu singkat "
         f"({P(sshort.proporsi_mentah, 1)} dari mentah; dipertahankan tetapi tidak diklasifikasi). {I(dqv['catatan valid untuk klasifikasi'])} catatan valid. Batas 3 kata adalah asumsi; aturan diuji pada data simulasi, belum pada data kotor nyata."),
    14: (f"Ya. Pada golden set, urutan tiga kategori teratas dari label pengganti lokal sama dengan label manual ({' '.join(epr.top3_manual.split())}), seluruh peringkat sama, Kendall tau {D(epr.kendall_tau, 2)}. "
         f"Sampel hanya {I(n_gold)} catatan dan C9 hanya {I(c1.loc['C9', 'n_manual'])}; hasil memakai pengganti lokal, bukan LLM. Cek silang Excel untuk Pareto: {I(n_ex_ok)} dari {I(n_ex)} kategori cocok dengan SQL."),
}


def qchip(n, t):
    return f'<a class="qc{" w" if n in WARN else ""}" href="#sec2{n}" title="{esc(t)}">Q{n}</a>'


def qcard(n, t, p):
    st = "Tidak terjawab penuh" if n in NOANS else ("Dengan catatan" if n in WARN else "Terjawab")
    return f'<span id="sec2{n}"></span>' + qa(f"Q{n}", t, p, ANS[n], status=st, warn=n in WARN)


def block(qs):
    return "".join(qcard(n, t, p) for n, t, p in QS if n in qs)


hyp_table = table(["ID", "Hipotesis (sesuai rancangan)", "Bukti", "Verdict"], [[f"<b>{r.kode}</b>", esc(r.hipotesis), esc(cs(r.bukti)), verdict_pill(r.hasil)] for r in hyp.itertuples()])
n_ans = 14 - len(NOANS)

sec2 = []
sec2.append(f'<div class="card"><h3>Jawaban singkat</h3><p>{I(n_ans)} dari {I(14)} pertanyaan terjawab dengan angka dari data ({I(9)} Utama, {I(4)} Pendukung, {I(1)} Tambahan); '
            f'Q9 dan Q10 tidak bisa dijawab penuh karena Claude API tidak dipanggil. {I(len(WARN))} pertanyaan diberi catatan kuning (asumsi, sampel kecil, hasil memakai pengganti lokal, atau estimasi). '
            f'Pertanyaan utama project dijawab di bagian 7.</p><p class="how">Klik nomor pertanyaan untuk melompat. Q hijau = terjawab. Q kuning = terjawab dengan catatan atau tidak terjawab penuh.</p>'
            f'<div class="qchips">' + "".join(qchip(n, t) for n, t, _ in QS) + '</div></div>')
sec2.append('<h3>2.1 Pareto dan hipotesis 80%</h3><div class="card"><p>Grafik 2.1a: Pareto kategori dari catatan valid (batang biru = kategori yang dibutuhkan untuk mencapai 80%).</p>' + chart_par
            + '<p>Tabel 2.1b: jumlah, porsi, dan kumulatif per kategori.</p>'
            + table(["Peringkat", "Kategori", "Catatan", "Porsi", "Kumulatif"], [[I(r.rank), esc(nm(r.category_code)), I(r.n), P(r.share, 1), P(r.cum_share, 1)] for r in par.itertuples()])
            + '<p>Tabel 2.1c: kumulatif k kategori teratas dengan CI Wilson (band H1 75% sampai 85%).</p>'
            + table(["Jumlah kategori", "Kategori", "Catatan", "Kumulatif", "CI 95%", "Dalam band"], [[I(r.k_kategori), r.kategori, I(r.n), P(r.cum_share, 1), f"{D(r.ci_low * 100, 1)}% sampai {D(r.ci_high * 100, 1)}%", "ya" if r.dalam_band else "tidak"] for r in spar.itertuples()])
            + '</div>')
sec2.append(block([1]))
sec2.append('<h3>2.2 Stasiun, shift, dan model</h3><div class="card"><p>Tabel 2.2a: dua kategori teratas per stasiun (porsi dari catatan stasiun itu).</p>'
            + table(["Stasiun", "Catatan", "Teratas", "Porsi", "Kedua", "Porsi"], [[s, I(ps[ps.station_code == s].station_total.iloc[0]),
                    nm(ps[(ps.station_code == s) & (ps.rank_in_station == 1)].category_code.iloc[0]), P(ps[(ps.station_code == s) & (ps.rank_in_station == 1)].share.iloc[0], 1),
                    nm(ps[(ps.station_code == s) & (ps.rank_in_station == 2)].category_code.iloc[0]), P(ps[(ps.station_code == s) & (ps.rank_in_station == 2)].share.iloc[0], 1)] for s in sorted(ps.station_code.unique())])
            + f'<p>Tabel 2.2b: sel stasiun dan kategori dengan rasio tertinggi (porsi stasiun dibanding porsi seharusnya; uji binomial satu sisi, Holm atas {I(nrows_cell)} sel).</p>'
            + table(["Stasiun", "Kategori", "Catatan", "Porsi dalam kategori", "Porsi seharusnya", "Rasio", "p Holm", "Memenuhi"], [[r.station_code, r.category_code, I(r.n), P(r.porsi_stasiun, 1), P(r.porsi_seharusnya, 1), D(r.rasio, 2), pv(r.p_holm), "ya" if r.memenuhi_h4 else "tidak"] for r in scell.head(8).itertuples()])
            + '<p>Tabel 2.2c: uji hubungan kategori dengan faktor (chi-square, koreksi Holm antar empat uji).</p>'
            + table(["Faktor", "Chi-square", "Derajat bebas", "p", "p Holm", "Cramér's V", "Signifikan"], [[f, D(r.chi2, 1), I(r.dof), pv(r.p), pv(r.p_holm), D(r.cramers_v, 3), "ya" if r.signifikan else "tidak"] for f, r in schi.iterrows()])
            + '</div>')
sec2.append(block([2, 4]))
sec2.append('<h3>2.3 Tren bulanan</h3><div class="card"><p>Grafik 2.3a: porsi bulanan lima kategori teratas.</p>' + chart_tr + legend([(COLS[c], c) for c in top5])
            + '<p>Tabel 2.3b: jumlah catatan per kategori dan bulan.</p>'
            + table(["Bulan"] + list(C.CATS) + ["Total"], [[m] + [I(tm[(tm.month == m) & (tm.category_code == c)].n.sum()) for c in C.CATS] + [I(tm[tm.month == m].n.sum())] for m in mon])
            + '</div>')
sec2.append(block([3]))
sec2.append(f'<h3>2.4 Ketepatan klasifikasi (golden set)</h3><div class="card"><p>Tabel 2.4a: accuracy dan macro F1 pada {I(n_gold)} catatan golden set valid (hasil <b>pengganti lokal</b>, bukan Claude API).</p>'
            + table(["Klasifikator", "Catatan", "Accuracy", "CI 95% (Wilson)", "Macro F1", "CI 95% (bootstrap)", "Salah"], [[esc(r.klasifikator), I(r.n), P(r.accuracy, 1), f"{D(r.acc_ci_low * 100, 1)}% sampai {D(r.acc_ci_high * 100, 1)}%", D(r.macro_f1, 3), f"{D(r.f1_ci_low, 3)} sampai {D(r.f1_ci_high, 3)}", I(r.salah)] for r in em.itertuples()])
            + '<p>Tabel 2.4b: precision, recall, dan F1 per kategori.</p>'
            + table(["Kategori", "Dukungan", "Precision", "Recall", "F1", "F1 baseline"], [[esc(nm(r.category_code)), I(r.support), D(r.precision, 3), D(r.recall, 3), D(r.f1, 3), D(r.f1_baseline, 3)] for r in epc.itertuples()])
            + f'<p>Tabel 2.4c: perbandingan berpasangan pengganti lokal dan baseline (McNemar eksak) serta subset catatan bersingkatan.</p>'
            + table(["Kelompok", "Catatan", "Accuracy pengganti lokal", "Accuracy baseline", "Pengganti lebih benar", "Baseline lebih benar"],
                    [[esc(r.kelompok), I(r.n), P(r.accuracy_model, 1), P(r.accuracy_baseline, 1), I(r.model_lebih_benar), I(r.baseline_lebih_benar)] for r in eab.itertuples()])
            + '</div>')
sec2.append(block([5, 6, 7]))
sec2.append('<h3>2.5 Catatan Lainnya, konsistensi, dan biaya</h3><div class="card"><p>Tabel 2.5a: isi catatan yang masuk Lainnya (C9).</p>'
            + table(["Teks catatan", "Jumlah"], [[esc(r.teks), I(r.jumlah)] for r in eoth.itertuples()])
            + '<p>Tabel 2.5b: kalibrasi keyakinan pengganti lokal pada golden set.</p>'
            + table(["Rentang keyakinan", "Catatan", "Accuracy", "Rata-rata keyakinan"], [[cs(r.rentang), I(r.catatan), P(r.accuracy, 1), D(r.rata_confidence, 2)] for r in ecal.itertuples()])
            + '<p>Tabel 2.5c: ambang keyakinan dan beban cek manual pada golden set (dasar 0,70).</p>'
            + table(["Ambang", "Diterima otomatis", "Accuracy otomatis", "Perlu cek manual", "Salah lolos", "Salah tertangkap"], [[D(r.ambang, 1) + (" (dasar)" if r.dasar else ""), P(r.coverage, 1), P(r.accuracy_otomatis, 1), I(r.perlu_cek_manual), I(r.salah_lolos), I(r.salah_tertangkap)] for r in eth.itertuples()])
            + '<p>Tabel 2.5d: biaya, waktu, dan token Claude API.</p>'
            + table(["Ukuran", "Nilai", "Alasan"], [[esc(r.ukuran), esc(r.nilai), esc(r.alasan)] for r in ecost.itertuples()])
            + '</div>')
sec2.append(block([8, 9, 10]))
sec2.append('<h3>2.6 Dampak (estimated)</h3><div class="card"><p>Tabel 2.6a: sensitivitas jam hemat per bulan terhadap asumsi (semua estimated).</p>'
            + table(["Analisis", "Penurunan", "Parameter", "Jam per bulan"], [[r.analisis, ("-" if pd.isna(r.penurunan) else P(r.penurunan, 0)), f"{I(r.parameter)} {r.satuan}", D(r.jam_per_bulan, 1)] for r in isens.itertuples()])
            + '</div>')
sec2.append(block([11, 12]))
sec2.append('<h3>2.7 Kualitas data, Pareto golden, dan cek silang</h3><div class="card"><p>Tabel 2.7a: kualitas data (Q13). Log per catatan di results/1-data-preparation/cleaning_log.csv.</p>'
            + table(["Kategori", "Jumlah", "Dasar", "Keputusan"], [[k, I(dq.loc[k, "jumlah"]), I(dq.loc[k, "dasar"]), esc(dq.loc[k, "keputusan"])] for k in dq.index])
            + '<p>Tabel 2.7b: Pareto golden set, label manual dibanding label klasifikasi (Q14).</p>'
            + table(["Kategori", "Catatan manual", "Catatan klasifikasi", "Peringkat manual", "Peringkat klasifikasi"], [[esc(nm(r.category_code)), I(r.n_manual), I(r.n_llm), I(r.rank_manual), I(r.rank_llm)] for r in pg.sort_values("rank_manual").itertuples()])
            + '<p>Tabel 2.7c: cek silang Excel (dihitung ulang LibreOffice) untuk jumlah dan peringkat per kategori.</p>'
            + table(["Kategori", "Manual Excel", "Manual SQL", "Klasifikasi Excel", "Klasifikasi SQL", "Peringkat manual (Excel/SQL)", "Peringkat klasifikasi (Excel/SQL)", "Cocok"],
                    [[r.category_code, I(r.n_manual_excel), I(r.n_manual_sql), I(r.n_klasifikasi_excel), I(r.n_klasifikasi_sql), f"{I(r.rank_manual_excel)} / {I(r.rank_manual_sql)}", f"{I(r.rank_klasifikasi_excel)} / {I(r.rank_klasifikasi_sql)}", "ya" if r.cocok else "tidak"] for r in cx_ex.itertuples()])
            + '<p>Tabel 2.7d: SQL vs pandas.</p>'
            + table(["Pemeriksaan", "Dibandingkan", "Cocok", "Hasil"], [[esc(r.pemeriksaan), I(r.dibandingkan), I(r.cocok), r.hasil] for r in cx_py.itertuples()])
            + '</div>')
sec2.append(block([13, 14]))
sec2.append('<h3>Hipotesis pada Design Project</h3><div class="card"><p class="how">Bunyi hipotesis mengikuti rancangan. Kriteria keputusan ditetapkan sebelum hasil dilihat (docs/definitions.md).</p>' + hyp_table + '</div>')

REP = []
REP.append('<div class="callout a"><h4>Data project ini adalah simulasi, klasifikasi bukan LLM</h4>Data adalah simulasi yang dianonimkan (lihat docs/simulation_spec.md). Claude API tidak dipanggil karena tidak ada API key; klasifikasi memakai pengganti lokal (TF-IDF + Logistic Regression). '
           'Angka menggambarkan simulasi dan pengganti lokal, bukan catatan pabrik dan bukan LLM.</div>')
REP.append('<h2 id="rp1">1. Data yang berhasil didapatkan<small>Isi data mentah, tabel di database, dan data hasil analisis</small></h2>')
REP.append('<div class="kpis">'
           + kpi(I(dqv["catatan (mentah)"]), "catatan mentah", f"{I(dqv['catatan valid untuk klasifikasi'])} valid untuk klasifikasi.", "navyH")
           + kpi(I(len(C.CATS)), "kategori", "8 penyebab dan 1 Lainnya.", "tealH")
           + kpi(I(n_mon), "bulan", "Maret sampai Agustus 2026.", "amberH")
           + kpi(I(len(dbt) + 1), "tabel di database", "3 tabel data plus llm_label.", "plumH")
           + kpi(I(n_gold), "golden set valid", f"Dari {I(dqv['golden set (mentah)'])} catatan golden mentah.", "roseH")
           + kpi(I(n_fp_ok), "sidik jari cocok", f"Dari {I(len(fp))} berkas, dicocokkan dengan repo DataCenter.", "skyH")
           + '</div>')
sample = anon.head(6)
REP.append('<h3>1.1 Data mentah dan anonim</h3><div class="card"><p>Tabel 1.1a: contoh enam baris pertama rework_note yang sudah dianonimkan (data simulasi).</p>'
           + table(["note_id", "date", "shift", "station_code", "model_code", "note_text_clean", "is_valid"], [[esc(cs(v)) for v in r] for r in sample.itertuples(index=False)])
           + '<p>Tabel 1.1b: penggantian aturan anonimisasi.</p>' + table(["Aturan", "Jumlah penggantian"], [[r.rule, I(r.n_replaced)] for r in redl.itertuples()])
           + '<p>Tabel 1.1c: kualitas data (Q13).</p>'
           + table(["Kategori", "Jumlah", "Dasar", "Keputusan"], [[k, I(dq.loc[k, "jumlah"]), I(dq.loc[k, "dasar"]), esc(dq.loc[k, "keputusan"])] for k in dq.index]) + '</div>')
FILES = {
    "baseline_label.csv": "label baseline kata kunci", "classifier_config.csv": "konfigurasi pengganti lokal per fold (nested CV)", "claude_pipeline_test.csv": "pemeriksaan pemanggil API dengan klien palsu",
    "compare_golden.csv": "label manual, klasifikasi, dan baseline pada golden set", "confusion.csv": "confusion matrix (SQL)", "cross_shift_model.csv": "kategori per shift dan model",
    "cross_station_cat.csv": "kategori per stasiun", "crosscheck_excel.csv": "cek silang Excel", "crosscheck_sql_pandas.csv": "cek silang SQL vs pandas",
    "eval_abbrev.csv": "ketepatan pada catatan bersingkatan", "eval_calibration.csv": "kalibrasi keyakinan", "eval_compare.csv": "perbandingan berpasangan model dan baseline",
    "eval_confusion_matrix.csv": "confusion matrix golden set", "eval_confusion_pairs.csv": "pasangan kategori yang tertukar", "eval_consistency.csv": "konsistensi dua kali jalan",
    "eval_cost.csv": "biaya dan waktu API", "eval_metrics.csv": "accuracy dan macro F1 dengan CI", "eval_other_notes.csv": "isi catatan Lainnya", "eval_pareto_rank.csv": "perbandingan peringkat Pareto manual dan klasifikasi",
    "eval_per_class.csv": "precision, recall, F1 per kategori", "eval_threshold.csv": "ambang keyakinan dan beban cek manual", "ground_truth_check.csv": "uji pemulihan fakta yang ditanam",
    "hypotheses.csv": "verdict H1 sampai H5", "impact_q11.csv": "estimasi jam rework (estimated)", "impact_q12.csv": "estimasi jam baca (estimated)", "impact_sensitivity.csv": "sensitivitas dampak",
    "llm_label.csv": "label klasifikasi tiap catatan valid", "note_llm.csv": "catatan valid dengan label dan keyakinan", "other_notes.csv": "catatan yang masuk Lainnya", "pareto.csv": "Pareto kategori",
    "pareto_golden.csv": "Pareto golden set", "pareto_station.csv": "Pareto per stasiun", "stats_chi.csv": "chi-square faktor terhadap kategori", "stats_cross_cells.csv": "uji sel shift dan model",
    "stats_pareto.csv": "kumulatif k kategori teratas", "stats_short.csv": "proporsi catatan terlalu singkat", "stats_station_cell.csv": "uji sel stasiun dan kategori", "stats_trend_flags.csv": "uji lonjakan bulanan (p-chart)",
    "trend_month.csv": "tren bulanan per kategori", "truth_accuracy.csv": "ketepatan terhadap kebenaran generator"}
real = sorted(p.name for p in r2.glob("*.csv"))
assert set(real) == set(FILES), ("CSV belum terdokumentasi / tidak ada:", set(real) ^ set(FILES))
REP.append('<h3>1.2 Tabel di database dan hasil</h3><div class="card"><p>Tabel 1.2a: tabel di notes.duckdb (tidak di-commit, dibuat ulang dari skrip).</p>'
           + table(["Tabel", "Baris"], [[r.tabel, I(r.baris)] for r in dbt.itertuples()] + [["llm_label", I(len(ll))]])
           + f'<p>Tabel 1.2b: pengecekan aturan database. {I(n_db_ok)} dari {I(len(dbc))} lulus.</p>'
           + table(["Pengecekan", "Pelanggaran", "Hasil"], [[r.pengecekan, I(r.pelanggaran), pill(r.hasil, "" if r.hasil == "lulus" else "d")] for r in dbc.itertuples()])
           + f'<p>Tabel 1.2c: {I(len(FILES))} file hasil analisis di results/2-analysis.</p>'
           + table(["File", "Isi"], [[f, FILES[f]] for f in sorted(FILES)]) + '</div>')
REP.append('<h3>1.3 Angka kunci (KPI)</h3><div class="card"><p>Tabel 1.3: ukuran kinerja utama.</p>'
           + table(["KPI", "Rumus ringkas", "Hasil", "Jumlah data"], [
               ["Kategori teratas", "catatan kategori / catatan valid", f"{nm(top.category_code)} {P(top.share, 1)}", I(N) + " catatan"],
               ["Kategori untuk mencapai 80%", "jumlah kategori pada Pareto kumulatif", f"{I(k80)} kategori ({P(s5.cum_share, 1)})", I(N) + " catatan"],
               ["Accuracy pengganti lokal", "benar / golden set valid", f"{P(eml.accuracy, 1)} ({ci(eml.acc_ci_low, eml.acc_ci_high)})", I(n_gold) + " catatan"],
               ["Macro F1 pengganti lokal", "rata-rata F1 per kategori", f"{D(eml.macro_f1, 3)}", I(n_gold) + " catatan"],
               ["Catatan terlalu singkat", "terlalu singkat / catatan setelah ganda dibuang", f"{P(sshort.proporsi, 1)} ({ci(sshort.ci_low, sshort.ci_high)})", I(sshort.dasar) + " catatan"],
               ["Jam hemat (estimated)", "lihat Q11 dan Q12", f"{D(q11.jam_dihemat_per_bulan, 1)} jam rework dan {D(q12.jam_dihemat_per_bulan, 1)} jam baca per bulan", I(n_mon) + " bulan"]]) + '</div>')

REP.append('<h2 id="rp2">2. Apakah business question terjawab?<small>' + f'{I(14)} pertanyaan pada Design Project, dijawab dengan data' + '</small></h2>')
REP.extend(sec2)

gt_rows = [[esc(cs(r.fakta)), esc(cs(r.ditanam)), esc(cs(r.terdeteksi)), pill(r.hasil, "" if r.hasil == "Sesuai" else "p")] for r in gtc.itertuples()]
REP.append('<h2 id="rp3">3. Apakah dataset sesuai dengan Design Project?<small>Perbandingan rancangan dengan realisasi</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 3a. Rancangan dan realisasi dataset.</p>'
           + table(["Hal", "Rancangan", "Realisasi", "Verdict"], [
               ["Sumber data", "catatan rework nyata yang dianonimkan", "data simulasi dari generator, lalu dianonimkan", pill("Berubah", "p")],
               ["Izin penggunaan data", "izin pemakaian dan izin mengirim teks ke API perlu dipastikan", "tidak berlaku (data simulasi); teks tidak dikirim ke API", pill("Tidak berlaku", "d")],
               ["Ukuran", f"±{I(3000)} catatan, golden set ±{I(300)}", f"{I(dqv['catatan (mentah)'])} catatan mentah, {I(dqv['catatan valid untuk klasifikasi'])} valid; golden set {I(dqv['golden set (mentah)'])} mentah, {I(n_gold)} valid", pill("Sesuai", "")],
               ["Tabel", "rework_note, llm_label, manual_label, dim_category", "sama; llm_label berisi hasil pengganti lokal dengan kolom sumber, tanpa kolom tokens dan created_at", pill("Sesuai + penyesuaian", "p")],
               ["Kategori", "9 kategori (8 penyebab dan Lainnya)", f"{I(len(C.CATS))} kategori, definisi di docs/taxonomy.md", pill("Sesuai", "")],
               ["Aturan anonimisasi", "hapus nama orang, produk, lot, serial; ganti stasiun dengan kode", f"sama; pindai kebocoran {I(n_leak)} file, {I(n_leak_fail)} gagal", pill("Sesuai", "")],
               ["Data tidak lengkap", "catatan kosong, ganda, terlalu singkat", f"{I(dqv['teks kosong'])} kosong, {I(dqv['catatan ganda'])} ganda, {I(dqv['terlalu singkat (< 3 kata)'])} terlalu singkat", pill("Sesuai", "")],
               ["Format jawaban LLM", "JSON dengan kategori, keyakinan, alasan; di luar daftar diulang satu kali", f"diuji dengan klien palsu ({I(n_cpt_ok)} dari {I(n_cpt)} lulus); tidak dijalankan terhadap API", pill("Sebagian", "p")],
               ["Hipotesis H1", "dua atau tiga kategori menyumbang sekitar 80%", f"tiga kategori {P(s3.cum_share, 1)}; butuh {I(k80)} kategori", verdict_pill(H["H1"].hasil)],
               ["Hipotesis H2", "LLM lebih tepat dari baseline, terutama pada singkatan", "LLM tidak diuji; pengganti lokal tidak lebih tepat dari baseline", verdict_pill(H["H2"].hasil)],
               ["Hipotesis H3", "kategori mirip paling sering tertukar", f"hanya {I(n_err)} kesalahan; belum cukup", verdict_pill(H["H3"].hasil)],
               ["Hipotesis H4", "satu stasiun menjadi sumber utama satu kategori", f"{I(len(sig))} dari {I(nrows_cell)} sel memenuhi kriteria", verdict_pill(H["H4"].hasil)],
               ["Hipotesis H5", "sekitar 5 sampai 10% catatan terlalu singkat", f"{P(sshort.proporsi, 1)} ({ci(sshort.ci_low, sshort.ci_high)})", verdict_pill(H["H5"].hasil)],
               ["Angka asumsi", "ambang 0,70, golden set ±300", "batas 3 kata, arti sekitar 80%, ambang rasio 1,5, batas 3 sigma, menit rework, detik baca adalah asumsi (docs/definitions.md)", pill("Sesuai + tambahan", "")],
               ["Sidik jari data", "tidak ada di rancangan", f"{I(n_fp_ok)} dari {I(len(fp))} berkas cocok dengan repo DataCenter", pill("Tambahan", "")],
           ]) + '</div>')
REP.append('<div class="card"><p class="how">Tabel 3b. Uji pemulihan fakta yang ditanam (validasi metode, bukan hasil analisis).</p>'
           + table(["Fakta", "Ditanam", "Terdeteksi", "Hasil"], gt_rows)
           + f'<p>{I(n_gt_ok)} dari {I(n_gt)} fakta pulih penuh. Ketepatan terhadap kebenaran generator pada semua {I(tacc.iloc[0].n)} catatan valid: pengganti lokal {P(tacc.iloc[0].accuracy_terhadap_kebenaran, 1)}, baseline {P(tacc.iloc[1].accuracy_terhadap_kebenaran, 1)}.</p></div>')

REP.append('<h2 id="rp4">4. Apakah tools yang digunakan sesuai?<small>Perbandingan rancangan dengan eksekusi</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 4a. Tools rancangan dan realisasi.</p>'
           + table(["Tool", "Rancangan", "Realisasi", "Verdict"], [
               ["Claude API", "klasifikasi dengan output JSON, token dan waktu dicatat", "tidak dipanggil (tidak ada API key); diganti klasifikator lokal TF-IDF + Logistic Regression; pemanggil API dibuat dan diuji dengan klien palsu", pill("Diganti pengganti lokal", "d")],
               ["Python (pandas, scikit-learn)", "pembersihan, baseline, accuracy, macro F1, confusion matrix", "sama; ditambah SciPy, statsmodels untuk uji, nested cross-validation", pill("Sesuai + tambahan", "")],
               ["DuckDB + SQL", "Pareto, tren, perbandingan label sebagai view", f"views.sql; {I(n_py_ok)} dari {I(n_py)} cocok dengan pandas", pill("Sesuai", "")],
               ["Excel", "label manual golden set dan cek silang Pareto (Q14)", f"cek silang Pareto dengan formula, dihitung ulang LibreOffice; {I(n_ex_ok)} dari {I(n_ex)} kategori cocok; label manual bukan dari Excel (kebenaran generator)", pill("Sesuai + penyesuaian", "p")],
               ["Streamlit + Plotly", "dashboard 4 halaman, link publik", f"4 halaman diuji dengan AppTest ({I(n_dash_ok)} dari {I(n_dash)} lulus); belum di-deploy", pill("Sebagian", "p")],
               ["GitHub + Markdown", "kode, prompt, contoh data anonim, README", "repo dan README; data tidak di-commit; branch belum di-merge", pill("Sesuai", "")]]) + '</div>')

STEPS = [
    ("1", "Menyusun taksonomi kategori", "docs/taxonomy.md dari templat generator, tidak membaca catatan nyata", "Sesuai + penyesuaian", "p"),
    ("2", "Merancang tabel dan aturan anonimisasi", "docs/data_dictionary.md", "Sesuai", ""),
    ("3", "Menganonimkan catatan", "generator (00), anonimisasi (01), sidik jari (02)", "Berubah", "p"),
    ("4", "Membersihkan teks", "03_clean.py, log cleaning", "Sesuai", ""),
    ("5", "Membuat label manual (golden set)", "kebenaran generator, bukan dilabeli manusia", "Berubah", "p"),
    ("6", "Klasifikasi dengan Claude API", "pengganti lokal (06); API tidak dijalankan", "Diganti pengganti lokal", "d"),
    ("7", "Membuat baseline kata kunci", "05_baseline_keyword.py", "Sesuai", ""),
    ("8", "Mengevaluasi ketepatan", "11_evaluate.py; Q9 dan Q10 tidak informatif atau tidak diukur", "Sebagian", "p"),
    ("9", "Menganalisis Pareto dan tren", "08, 12 (stats), 09 dan 10 (cek silang)", "Sesuai", ""),
    ("10", "Menghitung dampak", "13_impact.py (estimated), 14_ground_truth_check.py", "Sesuai + tambahan", ""),
    ("11", "Membuat dashboard", "15 sampai 19: data dashboard, infografik, notebook, uji AppTest, pindai kebocoran", "Sebagian", "p"),
    ("12", "README dan finalisasi", "README dan Report (build_report.py)", "Sebagian", "p")]
RENAMES = [
    ("docs/taxonomy.md", ["project/docs/taxonomy.md"], True),
    ("docs/data_dictionary.md", ["project/docs/data_dictionary.md"], True),
    ("scripts/anonymize_text.py", ["project/code/1-data-preparation/python/01_anonymize.py"], True),
    ("data/private/", ["project/data/raw/", "project/data/mapping.json"], False),
    ("scripts/clean_text.py", ["project/code/1-data-preparation/python/03_clean.py"], True),
    ("docs/cleaning_log.md", ["project/docs/cleaning_decisions.md", "project/results/1-data-preparation/cleaning_log.csv"], True),
    ("data/golden_set.csv", ["project/data/anon/manual_label.csv"], False),
    ("prompts/classify_v1.md", ["project/prompts/classify_v1.md"], True),
    ("scripts/classify.py", ["project/code/2-analysis/python/06_classify.py", "project/code/2-analysis/python/claude_client.py"], True),
    ("scripts/baseline_keyword.py", ["project/code/2-analysis/python/05_baseline_keyword.py"], True),
    ("notes.duckdb", ["project/notes.duckdb"], False),
    ("sql/", ["project/code/2-analysis/sql/views.sql"], True),
    ("notebooks/evaluation.ipynb", ["project/results/3-presentation/analysis.ipynb"], True),
    ("outputs/*.csv", ["project/results/2-analysis/"], True),
    ("dashboard/app.py", ["project/code/3-presentation/streamlit/app.py"], True),
    ("requirements.txt", ["project/requirements.txt"], True),
    (".env.example", ["project/.env.example"], True),
    ("outputs/infographic.pdf / .png", ["project/outputs/infographic.pdf", "project/outputs/infographic.png"], True),
    ("README.md", ["README.md"], True),
    ("index.html", ["design-and-report/index.html"], True),
    ("slides/presentation.pdf", [], True)]
for _, dest, committed in RENAMES:
    for d in dest:
        assert (REPO / d).exists() or d.endswith("index.html") or not committed, d
rn_rows = []
for a, dest, committed in RENAMES:
    rn_rows.append([a, "(tidak dibuat)" if not dest else ", ".join(dest) + ("" if committed else " (tidak di-commit)")])
REP.append('<h2 id="rp5">5. Apakah alur pengerjaan sesuai dengan Design Project?<small>' + f'{I(12)} langkah rancangan vs yang dijalankan' + '</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 5a. Dua belas langkah rancangan dan yang dijalankan.</p>'
           + table(["No", "Langkah rancangan", "Realisasi", "Verdict"], [[n, t, r, pill(v, k)] for n, t, r, v, k in STEPS])
           + '<p>Tabel 5b: penyesuaian dan improvisasi yang tidak ada di rancangan.</p>'
           + table(["Penyesuaian", "Alasan"], [
               ["Data simulasi dari repo DataCenter", "data kerja tidak tersedia; user memilih data simulasi; data dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256"],
               ["Pengganti lokal untuk Claude API", "tidak ada API key; TF-IDF + Logistic Regression dengan nested cross-validation; hasilnya tidak boleh dibaca sebagai hasil LLM"],
               ["Pemanggil API dan prompt diuji dengan klien palsu", "agar pipeline siap dijalankan bila API key tersedia; tidak pernah menghubungi API"],
               ["Label manual dari kebenaran generator", "tidak ada pelabel manusia; tidak ada noise atau ketidaksepakatan antar pelabel"],
               ["Catatan terlalu singkat tidak diklasifikasi", "batas 3 kata adalah asumsi; dilaporkan terpisah (Q13, H5)"],
               ["Definisi sekitar 80%, rasio 1,5 untuk H4, batas 3 sigma, menit rework, detik baca", "rancangan tidak menentukan; label asumsi di docs/definitions.md, kriteria ditetapkan sebelum uji"],
               ["Uji pemulihan fakta (14) dan pindai kebocoran (19)", "validasi yang tidak ada di rancangan"]])
           + '<p>Tabel 5c: perubahan nama dan lokasi file terhadap rancangan.</p>'
           + table(["Rancangan", "Realisasi"], rn_rows) + '</div>')

docs_list = [(a, d[0] if d else "", c) for a, d, c in RENAMES if a not in ("index.html",)]


def doc_status(a, committed, path):
    if not path:
        return pill("Tidak dibuat", "d")
    if not committed:
        return pill("Tidak di-commit", "d")
    return pill("Ada", "") if (REPO / path).exists() else pill("Belum ada", "d")


REP.append('<h2 id="rp6">6. Apakah project output tercapai?<small>Output pada Design Project, bagian 7</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 6a. Status output rancangan.</p>'
           + table(["Output", "Label", "Status", "Bukti"], [
               ["Dashboard tren defect", "Utama", pill("Sebagian", "p"), f"4 halaman diuji dengan AppTest ({I(n_dash_ok)} dari {I(n_dash)}); belum di-deploy"],
               ["Pipeline klasifikasi", "Utama", pill("Sebagian", "p"), f"pemanggil API dan prompt diuji dengan klien palsu ({I(n_cpt_ok)} dari {I(n_cpt)}); yang dijalankan adalah pengganti lokal"],
               ["Laporan evaluasi model", "Utama", pill("Sebagian", "p"), "notebook dan Report; hasil pengganti lokal, bukan LLM"],
               ["Golden set dan taksonomi", "Utama", pill("Sebagian", "p"), "taksonomi di docs/taxonomy.md; golden set (kebenaran generator) tidak di-commit, dibuat ulang"],
               ["Database dan query SQL", "Utama", pill("Tercapai", ""), f"notes.duckdb (tidak di-commit); views.sql; {I(n_db_ok)} pengecekan lulus"],
               ["One-sheet infografik", "Utama", pill("Tercapai", ""), "outputs/infographic.pdf dan .png"],
               ["README dan repositori", "Utama", pill("Sebagian", "p"), "README dan Report; branch belum di-merge ke main"],
               ["Slide presentasi", "Opsional", pill("Tidak dibuat", "d"), "-"]])
           + '<p>Tabel 6b: daftar dokumen rancangan dan status pada repositori.</p>'
           + table(["Dokumen", "Status"], [[a, doc_status(a, c, p)] for a, p, c in docs_list]) + '</div>')

criteria = [
    ("Kesembilan pertanyaan Utama terjawab dengan angka dari data", "Sebagian", "delapan terjawab; Q7 hanya untuk pengganti lokal karena LLM tidak diuji"),
    ("Ketepatan dilaporkan jujur dan lebih baik dari baseline (macro F1 >= 0,80)", "Tidak terpenuhi", f"macro F1 pengganti lokal {D(eml.macro_f1, 3)} memenuhi batas, tetapi tidak lebih baik dari baseline ({P(eml.accuracy, 1)} vs {P(ebl.accuracy, 1)}); LLM tidak diuji"),
    ("Tiga kategori teratas label LLM sama dengan label manual", "Terpenuhi", f"sama ({epr.top3_manual}); hasil pengganti lokal, bukan LLM"),
    ("Pemeriksaan anonimisasi tidak menemukan nama asli", "Terpenuhi", f"pindai {I(n_leak)} file, {I(n_leak_fail)} gagal"),
    ("Orang awam menyebut penyebab terbesar dari dashboard dalam 1 menit", "Belum diuji", "belum ada uji dengan pembaca awam; dashboard belum di-deploy"),
    ("Checklist standar terpenuhi (dashboard ter-deploy)", "Sebagian", "dashboard belum di-deploy; branch belum di-merge")]
n_ok_crit = sum(1 for c in criteria if c[1] == "Terpenuhi")
REP.append('<h2 id="rp7">7. Kesimpulan<small>Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan</small></h2>')
REP.append('<h4>7.1 Hasil analisis</h4><div class="card">'
           '<p><b>Pertanyaan utama:</b> penyebab defect dan rework apa yang paling sering muncul di catatan operator, bagaimana trennya per stasiun dan per bulan, dan seberapa bisa dipercaya klasifikasi otomatisnya?</p>'
           f'<p>Penyebab paling sering adalah {nm(top.category_code)} ({P(top.share, 1)}), disusul {nm(par.category_code.iloc[1])} ({P(par.share.iloc[1], 1)}) dan {nm(par.category_code.iloc[2])} ({P(par.share.iloc[2], 1)}). '
           f'Penyebabnya tersebar: tiga kategori hanya {P(s3.cum_share, 1)} dan diperlukan {I(k80)} kategori untuk 80% (Q1). '
           f'Empat stasiun punya satu kategori yang menonjol: ' + ", ".join(f"{r.station_code} untuk {r.category_code}" for r in sig.itertuples()) + f' (Q2). Tidak ada lonjakan bulanan dan tidak ada pengaruh shift atau model (Q3, Q4). '
           f'Klasifikasi pengganti lokal tepat {P(eml.accuracy, 1)} pada golden set, tetapi baseline kata kunci sama baiknya dan hasilnya tidak boleh dibaca sebagai hasil LLM: Claude API tidak diuji, sehingga kepercayaan terhadap LLM, biaya, dan konsistensinya belum terjawab (Q7, Q9, Q10). '
           f'Urutan tiga kategori teratas pada golden set sama dengan label manual (Q14).</p>'
           f'<p>Hipotesis: H1 {H["H1"].hasil.lower()}, H2 {H["H2"].hasil.lower()}, H3 {H["H3"].hasil.lower()}, H4 {H["H4"].hasil.lower()}, H5 {H["H5"].hasil.lower()}.</p></div>')
REP.append('<h4>7.2 Impact</h4><div class="card">'
           f'<p>Estimasi (estimated): menurunkan {nm(q11.kategori_teratas)} sebesar {P(q11.penurunan, 0)} menghemat sekitar {D(q11.jam_dihemat_per_bulan, 1)} jam rework per bulan, dan klasifikasi otomatis menghemat sekitar {D(q12.jam_dihemat_per_bulan, 1)} jam baca dan rekap per bulan. '
           'Angka memakai asumsi (satu catatan sama dengan satu unit yang di-rework, 12 menit per unit, 20 detik baca per catatan) yang bukan hasil pengukuran, dan bergantung pada akurasi pengganti lokal yang terlalu optimistis.</p>'
           '<p>Nilai praktis: daftar penyebab dan stasiun untuk memulai perbaikan, serta antrean cek manual untuk catatan yang ragu-ragu. Nilai analitis: evaluasi klasifikasi teks yang jujur dengan golden set, interval kepercayaan, dan pembanding sederhana. '
           'Nilai portofolio: pipeline dari anonimisasi sampai dashboard. Belum terukur: biaya dan konsistensi LLM, dampak nyata di lini.</p></div>')
REP.append('<h4>7.3 Success criteria</h4><div class="card">'
           + table(["Kriteria", "Status", "Bukti"], [[k, pill(s, "" if s == "Terpenuhi" else ("p" if s == "Sebagian" else "d")), cs(b)] for k, s, b in criteria])
           + f'<p>Hasil: {I(n_ok_crit)} dari {I(len(criteria))} kriteria tercapai.</p></div>')
REP.append('<h4>7.4 Rekomendasi</h4><div class="card"><ul class="tight">'
           f'<li>Mulai perbaikan dari {nm(top.category_code)}, dan periksa stasiun yang menonjol: ' + ", ".join(f"{r.station_code} untuk {r.category_code}" for r in sig.itertuples()) + '.</li>'
           f'<li>Jangan memfokuskan perbaikan pada satu atau dua penyebab saja: butuh {I(k80)} kategori untuk mencapai 80% catatan.</li>'
           '<li>Jalankan pipeline dengan Claude API pada golden set yang sama sebelum mempercayai klasifikasi LLM, lalu bandingkan dengan baseline kata kunci.</li>'
           f'<li>Kirim catatan dengan keyakinan di bawah {D(C.CONF_THRESHOLD, 2)} ke cek manual ({I(n_queue)} catatan pada data ini).</li></ul></div>')
REP.append('<h4>7.5 Saran perbaikan</h4><div class="card"><ul class="tight">'
           '<li>Jalankan Claude API dengan API key, catat token, waktu, dan konsistensi dua kali jalan (Q9 dan Q10).</li>'
           '<li>Ganti data simulasi dengan catatan operator nyata yang dianonimkan setelah izin perusahaan jelas; teks nyata jauh lebih beragam daripada templat.</li>'
           '<li>Minta dua orang melabeli golden set dan hitung kesepakatan antar pelabel.</li>'
           '<li>Uji aturan cleaning dengan catatan kotor nyata dan deploy dashboard, lalu uji dengan pembaca awam.</li></ul></div>')
REP.append('<h4>7.6 Batasan</h4><div class="card"><ul class="tight">'
           f'<li><b>Data adalah simulasi.</b> Angka menggambarkan simulasi, bukan catatan pabrik. {I(n_gt_ok)} dari {I(n_gt)} fakta yang ditanam pulih penuh. Teks dibuat dari templat sederhana sehingga klasifikasi terlalu mudah.</li>'
           '<li><b>Klasifikasi bukan LLM.</b> Claude API tidak dipanggil; H2, Q7, Q9, dan Q10 tidak bisa dijawab untuk LLM. Label manual adalah kebenaran generator tanpa noise.</li>'
           f'<li>Hanya {I(n_err)} kesalahan di golden set ({I(n_gold)} catatan), jadi H3 tidak bisa disimpulkan dan kategori kecil seperti C9 ({I(c1.loc["C9", "n_manual"])} catatan) tidak teruji.</li>'
           f'<li>Ukuran dan batas yang ditetapkan sendiri (asumsi): arti sekitar 80% (75% sampai 85%), rasio {D(C.H4_MIN_SHARE_RATIO, 1)} untuk H4, batas 3 sigma, batas 3 kata, ambang keyakinan {D(C.CONF_THRESHOLD, 2)}, menit rework, dan detik baca.</li>'
           f'<li>Pada H5, batas atas CI ({P(sshort.ci_high, 1)}) sedikit melewati 10%, sedangkan estimasi titik ({P(sshort.proporsi, 1)}) di dalam band.</li>'
           '<li>Aturan cleaning belum teruji pada data kotor nyata. Dashboard belum di-deploy; success criteria "orang awam menyebut penyebab terbesar dalam 1 menit" belum diuji; branch belum di-merge ke main; slide presentasi tidak dibuat.</li>'
           '<li>Pola per stasiun belum tentu penyebab: stasiun bisa lebih sering menemukan defect, bukan menciptakannya. Dampak dalam jam dan berlabel estimated, belum dalam rupiah.</li></ul></div>')

REPORT_PANE = ('<div class="pane" id="report" data-tab="report" hidden>\n'
               '<div class="callout g"><h4>Report Project versi 2: evaluasi hasil terhadap Design Project</h4>'
               f'Cek silang: {I(n_py_ok)} dari {I(n_py)} SQL vs pandas, {I(n_ex_ok)} dari {I(n_ex)} SQL vs Excel. Angka diaudit dari CSV hasil. '
               '<b>Data pada project ini adalah simulasi dan klasifikasi memakai pengganti lokal, bukan Claude API.</b></div>\n'
               + '<div class="card"><p class="how">Ringkasan tujuh pertanyaan evaluasi. Klik untuk melompat ke bagian.</p>'
               + table(["No", "Pertanyaan evaluasi", "Verdict", "Ringkasan"], [
                   [f'<span class="en">{i}</span>', f'<a href="#rp{i}">{t}</a>', pill(v[0], v[1]), v[2]] for i, (t, v) in enumerate([
                       ("Data yang berhasil didapatkan", ("Berhasil", "", f"{I(dqv['catatan (mentah)'])} catatan, {I(dqv['catatan valid untuk klasifikasi'])} valid")),
                       ("Apakah business question terjawab?", ("Sebagian", "p", f"{I(n_ans)} dari {I(14)} terjawab; Q9 dan Q10 tidak penuh")),
                       ("Apakah dataset sesuai dengan Design Project?", ("Berubah", "p", "data simulasi, bukan catatan nyata")),
                       ("Apakah tools yang digunakan sesuai?", ("Diganti pengganti lokal", "d", "Claude API tidak dipanggil")),
                       ("Apakah alur pengerjaan sesuai dengan Design Project?", ("Sebagian", "p", "klasifikasi lokal; dashboard belum di-deploy")),
                       ("Apakah project output tercapai?", ("Sebagian", "p", "dashboard belum di-deploy, slide tidak dibuat")),
                       ("Kesimpulan", ("Simulasi", "", f"{nm(top.category_code)} terbesar; butuh {I(k80)} kategori untuk 80%")),
                   ], 1)]) + '</div>\n' + "\n".join(REP) + '\n</div>\n')

nav_src = SRC[SRC.index('<nav aria-label="Project navigation">'):SRC.index('</nav>') + 6]
btn_design = re.search(r'<button[^>]*data-t="design"[^>]*>.*?</button>', nav_src, re.S).group(0)
btn_report = re.search(r'<button[^>]*data-t="report"[^>]*>.*?</button>', nav_src, re.S).group(0)
links_design = re.search(r'<div class="links" data-tab="design">.*?</div>', nav_src, re.S).group(0)
new_report_links = ('<div class="links" data-tab="report" hidden>' + "".join(f'<a href="#rp{i}">{t}</a>' for i, t in enumerate(
    ["Data", "Business Questions", "Dataset", "Tools", "Alur Kerja", "Project Output", "Kesimpulan"], 1)) + '</div>')
nav_new = '<nav aria-label="Project navigation">' + btn_design + btn_report + links_design + new_report_links + '</nav>'
design_start = SRC.index('<header class="banner">')
design_end = SRC.index('<div class="pane" id="report"')
design_pane = SRC[design_start:design_end]
head_end = SRC.index('</style>')
body_start = SRC.index('<body>')
hub_link = SRC[body_start:SRC.index('<main>')]
html = SRC[:head_end] + CSS_EXTRA + "\n" + SRC[head_end:body_start] + hub_link + '<main>\n' + nav_new + '\n' + design_pane + REPORT_PANE + SRC[SRC.index('</main>'):]
assert design_pane in html, "pane Design berubah"

STATIC = {str(i) for i in range(0, 41)} | {"2026", "50", "60", "80", "100", "200", "300", "3000", "0,05", "0,95", "0,5", "1,5", "3,0", "0,25", "0,1", "1,0", "4", "0,70", "0,80", "0,7",
                                           "2,5", "1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "7.1", "7.2", "7.3", "7.4", "7.5", "7.6", "01", "03", "04", "05", "06", "07", "08", "09", "00", "02",
                                           "25", "75", "85", "95", "1.000", "3a", "3b", "18", "65", "12", "16", "13", "14", "15", "17", "19"}
n_tok, bad = audit(REPORT_PANE, STATIC)
print(f"token angka diperiksa: {n_tok}; tidak terdaftar: {len(bad)}")
if bad:
    vt = R.visible_text(REPORT_PANE)
    print("TIDAK TERDAFTAR:", bad[:80])
    for t in bad[:40]:
        m = re.search(r"(?<![\d.,])" + re.escape(t) + r"(?![\d,])", vt)
        if m:
            print("  ", t, "|", vt[max(0, m.start() - 60):m.end() + 30].replace("\n", " "))
    raise SystemExit("audit gagal: ada angka yang tidak berasal dari data")
out = HERE.parent / "index.html"
out.write_text(html, encoding="utf-8")
print("written", out, len(html))
