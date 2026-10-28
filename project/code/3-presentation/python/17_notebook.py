"""17: Notebook analisis Q1 sampai Q14 (nbformat, dieksekusi nbclient). Hanya membaca CSV hasil. Id sel deterministik.
Hasil: results/3-presentation/analysis.ipynb"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import nbformat as nbf
from nbclient import NotebookClient
import common as CM

cells = []
def md(t): cells.append(nbf.v4.new_markdown_cell(t))
def code(t): cells.append(nbf.v4.new_code_cell(t))

md("# Project 18: Rework Note Analysis, analisis Q1 sampai Q14\nNotebook ini membaca CSV di `results/2-analysis` dan `results/1-data-preparation`. Data adalah simulasi yang dianonimkan. Klasifikasi memakai pengganti lokal (TF-IDF + Logistic Regression), bukan Claude API.")
code("from pathlib import Path\nimport pandas as pd\nimport matplotlib\nmatplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
     "R2 = Path('../2-analysis'); R1 = Path('../1-data-preparation')\npd.set_option('display.width', 160)")
md("## Q1 dan H1: Pareto kategori")
code("p = pd.read_csv(R2/'pareto.csv'); display(p); display(pd.read_csv(R2/'stats_pareto.csv'))\nfig, ax = plt.subplots(figsize=(8,3)); ax.bar(p.category_code, p.n); ax.set_ylabel('catatan'); plt.show()")
md("## Q2 dan H4: kategori per stasiun")
code("display(pd.read_csv(R2/'pareto_station.csv').query('rank_in_station<=2')); display(pd.read_csv(R2/'stats_station_cell.csv').query('memenuhi_h4==1'))")
md("## Q3 dan Q4: tren bulanan, shift, dan model")
code("t = pd.read_csv(R2/'trend_month.csv'); display(t.pivot(index='month', columns='category_code', values='n')); display(pd.read_csv(R2/'stats_chi.csv')); display(pd.read_csv(R2/'stats_trend_flags.csv').query('lonjakan==1 or penurunan==1'))")
md("## Q5 sampai Q7 dan H2, H3: ketepatan klasifikasi")
code("display(pd.read_csv(R2/'eval_metrics.csv')); display(pd.read_csv(R2/'eval_per_class.csv')); display(pd.read_csv(R2/'eval_confusion_pairs.csv')); display(pd.read_csv(R2/'eval_compare.csv')); display(pd.read_csv(R2/'eval_abbrev.csv'))")
md("## Q8 sampai Q10: catatan Lainnya, konsistensi, biaya, kalibrasi")
code("display(pd.read_csv(R2/'eval_other_notes.csv')); display(pd.read_csv(R2/'eval_consistency.csv')); display(pd.read_csv(R2/'eval_cost.csv')); display(pd.read_csv(R2/'eval_calibration.csv')); display(pd.read_csv(R2/'eval_threshold.csv'))")
md("## Q11 dan Q12: dampak (estimated)")
code("display(pd.read_csv(R2/'impact_q11.csv')); display(pd.read_csv(R2/'impact_q12.csv')); display(pd.read_csv(R2/'impact_sensitivity.csv'))")
md("## Q13 dan Q14: kualitas data, Pareto golden, dan cek silang")
code("display(pd.read_csv(R1/'data_quality.csv')); display(pd.read_csv(R2/'eval_pareto_rank.csv')); display(pd.read_csv(R2/'crosscheck_sql_pandas.csv')); display(pd.read_csv(R2/'crosscheck_excel.csv'))")
md("## Hipotesis dan cek kebenaran simulasi")
code("display(pd.read_csv(R2/'hypotheses.csv')); display(pd.read_csv(R2/'ground_truth_check.csv'))")
nb = nbf.v4.new_notebook()
nb.cells = cells
for i, c in enumerate(nb.cells):
    c["id"] = f"c{i:03d}"
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
out = CM.RES3
NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(out)}}).execute()
for c in nb.cells:
    c.get("metadata", {}).pop("execution", None)
nbf.write(nb, out / "analysis.ipynb")
print("notebook ditulis")
