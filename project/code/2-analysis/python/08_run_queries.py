"""08: Buat view SQL (DuckDB) dan ekspor hasilnya ke CSV (Q1 sampai Q6, Q8, Q14). Dibulatkan 10 desimal agar jalan ulang identik."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import duckdb
import pandas as pd
import common as CM

con = duckdb.connect(str(CM.DB_PATH))
con.execute("DROP TABLE IF EXISTS baseline_label")
con.execute(f"CREATE TABLE baseline_label AS SELECT note_id, category_code FROM read_csv('{CM.RES2 / 'baseline_label.csv'}', header=true)")
sql = (CM.SQL_DIR / "views.sql").read_text(encoding="utf-8")
for stmt in [s.strip() for s in sql.split(";") if s.strip() and not all(l.startswith("--") for l in s.strip().splitlines())]:
    con.execute(stmt)
EXPORT = {
    "pareto.csv": "SELECT * FROM v_pareto ORDER BY rank",
    "pareto_station.csv": "SELECT * FROM v_pareto_station ORDER BY station_code, rank_in_station, category_code",
    "trend_month.csv": "SELECT * FROM v_trend_month ORDER BY month, category_code",
    "cross_shift_model.csv": "SELECT * FROM v_cross_shift_model ORDER BY category_code, shift, model_code",
    "cross_station_cat.csv": "SELECT * FROM v_cross_station_cat ORDER BY station_code, category_code",
    "compare_golden.csv": "SELECT * FROM v_compare_golden ORDER BY note_id",
    "confusion.csv": "SELECT * FROM v_confusion ORDER BY manual_cat, llm_cat",
    "pareto_golden.csv": "SELECT * FROM v_pareto_golden ORDER BY category_code",
    "other_notes.csv": "SELECT * FROM v_other ORDER BY note_id",
    "note_llm.csv": "SELECT note_id, date, month, shift, station_code, model_code, note_text_clean, llm_cat, confidence, sumber FROM v_note_llm ORDER BY note_id",
}
for name, q in EXPORT.items():
    df = con.execute(q).df()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].round(10)
    df.to_csv(CM.RES2 / name, index=False)
    print(f"{name}: {len(df)} baris")
con.close()
