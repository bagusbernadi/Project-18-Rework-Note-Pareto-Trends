"""15: Data untuk dashboard Streamlit (results/3-presentation). Semua angka berasal dari results/2-analysis dan 1-data-preparation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

R2, R3 = CM.RES2, CM.RES3
par = pd.read_csv(R2 / "pareto.csv")
par["nama"] = par.category_code.map(CM.CAT_NAME)
par.to_csv(R3 / "dashboard_pareto.csv", index=False, float_format="%.10g")
ps = pd.read_csv(R2 / "pareto_station.csv")
ps["nama"] = ps.category_code.map(CM.CAT_NAME)
ps.to_csv(R3 / "dashboard_pareto_station.csv", index=False, float_format="%.10g")
tm = pd.read_csv(R2 / "trend_month.csv")
tm["nama"] = tm.category_code.map(CM.CAT_NAME)
tm.to_csv(R3 / "dashboard_trend.csv", index=False, float_format="%.10g")
pd.read_csv(R2 / "stats_station_cell.csv").to_csv(R3 / "dashboard_station_cell.csv", index=False, float_format="%.10g")
pd.read_csv(R2 / "eval_metrics.csv").to_csv(R3 / "dashboard_eval_metrics.csv", index=False, float_format="%.10g")
pd.read_csv(R2 / "eval_per_class.csv").assign(nama=lambda d: d.category_code.map(CM.CAT_NAME)).to_csv(R3 / "dashboard_per_class.csv", index=False, float_format="%.10g")
pd.read_csv(R2 / "eval_confusion_matrix.csv").to_csv(R3 / "dashboard_confusion.csv", index=False)
pd.read_csv(R2 / "eval_threshold.csv").to_csv(R3 / "dashboard_threshold.csv", index=False, float_format="%.10g")
pd.read_csv(R2 / "hypotheses.csv").to_csv(R3 / "dashboard_hipotesis.csv", index=False)
nl = pd.read_csv(R2 / "note_llm.csv")
nl["nama"] = nl.llm_cat.map(CM.CAT_NAME)
q = nl[nl.confidence < CM.CONF_THRESHOLD].sort_values(["confidence", "note_id"])
q[["note_id", "date", "shift", "station_code", "model_code", "note_text_clean", "llm_cat", "nama", "confidence"]].to_csv(R3 / "dashboard_antrean.csv", index=False, float_format="%.6g")
pd.read_csv(R2 / "impact_q11.csv").to_csv(R3 / "dashboard_dampak_q11.csv", index=False, float_format="%.10g")
pd.read_csv(R2 / "impact_q12.csv").to_csv(R3 / "dashboard_dampak_q12.csv", index=False, float_format="%.10g")
print("dashboard data ditulis:", len(list(R3.glob("dashboard_*.csv"))), "file; antrean", len(q))
