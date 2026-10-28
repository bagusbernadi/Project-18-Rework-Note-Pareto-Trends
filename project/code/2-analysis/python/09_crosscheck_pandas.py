"""09: Cek silang SQL vs pandas. Hitung ulang Pareto, Pareto per stasiun, tren bulanan, dan perbandingan golden set dengan pandas
dari data bersih dan label, lalu bandingkan dengan hasil view SQL (08). Harus identik."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
import common as CM

note = pd.read_csv(CM.CLEAN / "rework_note_clean.csv")
lab = pd.read_csv(CM.RES2 / "llm_label.csv")
man = pd.read_csv(CM.CLEAN / "manual_label_clean.csv")
base = pd.read_csv(CM.RES2 / "baseline_label.csv")
v = note[note.is_valid == 1].merge(lab[["note_id", "category_code"]], on="note_id")
v["month"] = v.date.str[:7]
rows = []


def cmp(name, a, b, keys):
    m = a.merge(b, on=keys, suffixes=("_sql", "_py"), how="outer")
    cols = [c for c in m.columns if c.endswith("_sql")]
    diff = max(float((m[c] - m[c.replace("_sql", "_py")]).abs().max()) for c in cols)
    rows.append(dict(pemeriksaan=name, dibandingkan=len(m), cocok=int((m[cols].values == m[[c.replace('_sql', '_py') for c in cols]].values).all(1).sum()
                                                                  if diff == 0 else (np.isclose(m[cols].values.astype(float), m[[c.replace('_sql', '_py') for c in cols]].values.astype(float), atol=1e-9)).all(1).sum()),
                     selisih_maks=diff, hasil="cocok" if diff < 1e-9 and not m.isna().any().any() else "beda"))


sq = pd.read_csv(CM.RES2 / "pareto.csv")
py = v.groupby("category_code").size().rename("n").reset_index().sort_values(["n", "category_code"], ascending=[False, True])
py["share"] = py.n / py.n.sum(); py["cum_share"] = py.share.cumsum(); py["rank"] = range(1, len(py) + 1)
cmp("Pareto kategori (Q1)", sq[["category_code", "n", "share", "cum_share", "rank"]], py[["category_code", "n", "share", "cum_share", "rank"]], ["category_code"])
sq = pd.read_csv(CM.RES2 / "pareto_station.csv")
idx = pd.MultiIndex.from_product([sorted(v.station_code.unique()), CM.CATS], names=["station_code", "category_code"])
py = v.groupby(["station_code", "category_code"]).size().reindex(idx, fill_value=0).rename("n").reset_index()
py["station_total"] = py.groupby("station_code").n.transform("sum")
py = py.sort_values(["station_code", "n", "category_code"], ascending=[True, False, True])
py["rank_in_station"] = py.groupby("station_code").cumcount() + 1
py["share"] = py.n / py.station_total
cmp("Pareto per stasiun (Q2)", sq[["station_code", "category_code", "n", "station_total", "share", "rank_in_station"]], py[["station_code", "category_code", "n", "station_total", "share", "rank_in_station"]], ["station_code", "category_code"])
sq = pd.read_csv(CM.RES2 / "trend_month.csv")
idx = pd.MultiIndex.from_product([sorted(v.month.unique()), CM.CATS], names=["month", "category_code"])
py = v.groupby(["month", "category_code"]).size().reindex(idx, fill_value=0).rename("n").reset_index()
py["month_total"] = py.groupby("month").n.transform("sum"); py["share"] = py.n / py.month_total
cmp("Tren bulanan (Q3)", sq[["month", "category_code", "n", "month_total", "share"]], py, ["month", "category_code"])
sq = pd.read_csv(CM.RES2 / "compare_golden.csv")
py = man.rename(columns={"category_code": "manual_cat"}).merge(lab[["note_id", "category_code"]].rename(columns={"category_code": "llm_cat"}), on="note_id") \
        .merge(base.rename(columns={"category_code": "baseline_cat"}), on="note_id")
py["match_llm"] = (py.manual_cat == py.llm_cat).astype(int); py["match_baseline"] = (py.manual_cat == py.baseline_cat).astype(int)
cmp("Golden set: kecocokan label (Q5, Q7)", sq[["note_id", "match_llm", "match_baseline"]], py[["note_id", "match_llm", "match_baseline"]], ["note_id"])
sq = pd.read_csv(CM.RES2 / "confusion.csv")
py = py.groupby(["manual_cat", "llm_cat"]).size().rename("n").reset_index()
cmp("Confusion matrix (Q6)", sq, py, ["manual_cat", "llm_cat"])
out = pd.DataFrame(rows)
out.to_csv(CM.RES2 / "crosscheck_sql_pandas.csv", index=False)
print(out.to_string(index=False))
assert (out.hasil == "cocok").all(), "SQL dan pandas tidak cocok"
