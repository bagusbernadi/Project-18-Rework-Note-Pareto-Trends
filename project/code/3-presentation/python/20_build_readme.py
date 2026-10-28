"""20: README.md dari CSV hasil (angka tidak diketik). Dijalankan paling akhir sebelum build_report.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

R2, R1, R3 = CM.RES2, CM.RES1, CM.RES3
par = pd.read_csv(R2 / "pareto.csv")
hy = pd.read_csv(R2 / "hypotheses.csv")
em = pd.read_csv(R2 / "eval_metrics.csv")
q11 = pd.read_csv(R2 / "impact_q11.csv").iloc[0]
q12 = pd.read_csv(R2 / "impact_q12.csv").iloc[0]
gt = pd.read_csv(R2 / "ground_truth_check.csv")
dq = pd.read_csv(R1 / "data_quality.csv").set_index("kategori")
cx = pd.read_csv(R2 / "crosscheck_excel.csv")
py = pd.read_csv(R2 / "crosscheck_sql_pandas.csv")
dt = pd.read_csv(R3 / "dashboard_test.csv")
lk = pd.read_csv(R3 / "leak_scan.csv")
sc = pd.read_csv(R2 / "stats_station_cell.csv")
sp = pd.read_csv(R2 / "stats_pareto.csv")
sh = pd.read_csv(R2 / "stats_short.csv").iloc[0]
cpt = pd.read_csv(R2 / "claude_pipeline_test.csv")


def I(n): return f"{int(round(float(n))):,}".replace(",", ".")
def D(x, d=1): return f"{float(x):.{d}f}".replace(".", ",")
def P(x, d=1): return D(float(x) * 100, d) + "%"


top = par.iloc[0]
sig = sc[sc.memenuhi_h4 == 1].sort_values(["station_code", "category_code"])
s3 = sp[sp.k_kategori == 3].iloc[0]
k80 = int(sp.k_untuk_80.iloc[0])
mraw = int(dq.loc["catatan (mentah)", "jumlah"]); mval = int(dq.loc["catatan valid untuk klasifikasi", "jumlah"])
hyp = "\n".join(f"{r.kode[1:]}. {r.hipotesis} **{r.hasil}.**" for r in hy.itertuples())
txt = f"""[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 18: Rework Note Analysis with LLM: Defect Pareto & Trends

**Status: Selesai di branch `project-18-build` (belum di-merge ke `main`).** Halaman rancangan dan laporan: [`design-and-report/index.html`](design-and-report/index.html) (tab Design Project dan Report Project).

**Tujuan:** mengelompokkan catatan rework operator ke kategori penyebab, membuat Pareto dan tren per stasiun dan bulan, serta menilai seberapa bisa dipercaya klasifikasi otomatisnya.

| | |
|---|---|
| Kategori | Manufaktur, teks tidak terstruktur (data anonim) |
| Tingkat | Sedang sampai sulit |
| Data | **Simulasi** yang dianonimkan (catatan karangan; stasiun dan model diganti kode; nama orang, lot, serial dihapus) |
| Tools | DuckDB + SQL, Python (pandas, scikit-learn, SciPy, statsmodels), Excel (dihitung ulang LibreOffice), Streamlit + Plotly |

> **Penting:** rancangan memakai Claude API. Project ini **tidak memanggil Claude API** (tidak ada API key). Klasifikasi dijalankan oleh pengganti lokal (TF-IDF + Logistic Regression). Hasil evaluasi di bawah adalah hasil pengganti lokal, bukan hasil LLM.

## 1. Problem

**Pertanyaan utama:** penyebab defect dan rework apa yang paling sering muncul di catatan operator, bagaimana trennya per stasiun dan per bulan, dan seberapa bisa dipercaya klasifikasi otomatisnya?

Rancangan memecahnya menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan). Daftar lengkap ada di halaman rancangan.

## 2. Data

- Data simulasi catatan rework (100% karangan), dibuat `00_generate_raw.py` lalu dianonimkan `01_anonymize.py`. Data tidak di-commit; dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256 di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) (`02_verify_fingerprint.py`).
- Versi data v1, seed 18260302 (generator) dan 18260999 (pemetaan). Hasil: {I(mraw)} catatan mentah, {I(mval)} valid untuk klasifikasi, Maret sampai Agustus 2026, golden set {I(dq.loc['golden set (mentah)', 'jumlah'])} catatan ({I(dq.loc['golden set valid (dipakai evaluasi)', 'jumlah'])} valid).
- Tabel: `dim_category`, `rework_note`, `manual_label`, `llm_label`. Kamus data: `project/docs/data_dictionary.md`.

## 3. Analysis

Pareto dan tren dengan view SQL, uji chi-square dan binomial dengan koreksi Holm, p-chart bulanan, evaluasi klasifikasi (accuracy, macro F1, confusion matrix, precision, recall, kalibrasi keyakinan) pada golden set, dan pembanding baseline kata kunci. Definisi dan asumsi: `project/docs/definitions.md`.

- Penyebab terbesar: **{top.category_code} {CM.CAT_NAME[top.category_code]}** ({P(top.share)} catatan). Tiga kategori teratas {P(s3.cum_share)}; butuh {I(k80)} kategori untuk mencapai 80%.
- Stasiun yang menonjol: {", ".join(f"{r.station_code} untuk {r.category_code}" for r in sig.itertuples())}.
- Pengganti lokal: accuracy {P(em.accuracy.iloc[0])}, macro F1 {D(em.macro_f1.iloc[0], 3)} pada golden set; baseline kata kunci accuracy {P(em.accuracy.iloc[1])}.

Hipotesis rancangan:
{hyp}

Uji pemulihan fakta yang ditanam: {int((gt.hasil == 'Sesuai').sum())} dari {len(gt)} pulih penuh (`project/results/2-analysis/ground_truth_check.csv`).

## 4. Recommendation

Mulai perbaikan dari {top.category_code} dan stasiun yang menonjol; jangan memfokuskan pada satu atau dua penyebab saja. Jalankan pipeline dengan Claude API pada golden set yang sama sebelum mempercayai klasifikasi LLM.

## 5. Impact

Estimasi (`estimated`): menurunkan {top.category_code} {P(q11.penurunan, 0)} menghemat sekitar {D(q11.jam_dihemat_per_bulan)} jam rework per bulan, dan klasifikasi otomatis menghemat sekitar {D(q12.jam_dihemat_per_bulan)} jam baca per bulan. Asumsi: satu catatan = satu unit, {I(q11.menit_per_unit)} menit rework per unit, {I(q12.detik_per_catatan)} detik baca per catatan.

## Batasan

- **Data adalah simulasi** dan teks dibuat dari templat sederhana; angka terlalu optimistis dibanding catatan nyata.
- **Claude API tidak diuji**: H2, perbandingan LLM dengan baseline, konsistensi dua kali jalan (Q9), dan biaya (Q10) tidak terjawab untuk LLM. Label manual adalah kebenaran generator tanpa noise.
- Hanya sedikit kesalahan di golden set, jadi H3 (kategori mirip tertukar) tidak bisa disimpulkan.
- Batas yang ditetapkan sendiri (asumsi): arti "sekitar 80%", rasio 1,5 untuk H4, batas 3 sigma, batas 3 kata ({P(sh.proporsi)} catatan terlalu singkat), ambang keyakinan, menit rework, dan detik baca.
- Dashboard belum di-deploy (diuji dengan Streamlit AppTest: {int((dt.hasil == 'lulus').sum())} dari {len(dt)} lulus). Success criteria "orang awam menyebut penyebab terbesar dalam 1 menit" belum diuji. Slide presentasi tidak dibuat.
- Cek silang: SQL vs pandas {int(py.cocok.sum())} dari {len(py)}, SQL vs Excel {int(cx.cocok.sum())} dari {len(cx)} kategori (Excel dihitung ulang LibreOffice). Pemanggil API diuji dengan klien palsu ({int((cpt.hasil == 'lulus').sum())} dari {len(cpt)} lulus). Pindai kebocoran identitas: {len(lk)} file, {int((lk.hasil == 'gagal').sum())} gagal.

## Menjalankan

Dari folder `project/`:

```
pip install -r requirements.txt
for f in code/1-data-preparation/python/*.py code/2-analysis/python/[0-9]*.py code/3-presentation/python/*.py; do python3 "$f"; done
python3 ../design-and-report/src/build_report.py
streamlit run code/3-presentation/streamlit/app.py
```

Claude API (opsional, tidak dijalankan di project ini): salin `.env.example` menjadi `.env`, isi `ANTHROPIC_API_KEY`, lalu gunakan `code/2-analysis/python/claude_client.py` dengan `prompts/classify_v1.md`.

## Struktur repository

```
README.md
index.html                     pengalihan ke design-and-report/
design-and-report/             index.html (tab Design + Report), src/ (page_v1.html, report.css, report_lib.py, build_report.py)
project/
  code/                        common.py; 1-data-preparation/python (00 sampai 04); 2-analysis/{{python,sql}} (05 sampai 14); 3-presentation/{{python,streamlit}} (15 sampai 20)
  results/                     1-data-preparation/ 2-analysis/ 3-presentation/ (CSV hasil, analysis.ipynb)
  prompts/                     classify_v1.md
  outputs/                     crosscheck.xlsx, infographic.pdf dan .png
  data/                        README.md (data tidak di-commit)
  docs/                        definitions.md, taxonomy.md, data_dictionary.md, cleaning_decisions.md, simulation_spec.md, datacenter_fingerprint.csv
  requirements.txt, .env.example
```
"""
txt = txt.replace("{CM.CAT_NAME[top.category_code]}", CM.CAT_NAME[top.category_code])
(CM.ROOT.parent / "README.md").write_text(txt, encoding="utf-8")
print("README ditulis")
