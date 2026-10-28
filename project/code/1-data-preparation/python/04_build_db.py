"""04: Muat data bersih ke DuckDB (notes.duckdb) dan jalankan aturan pengecekan.

Tabel: dim_category, rework_note, manual_label. llm_label ditambahkan oleh 06_classify.py.
Hasil: notes.duckdb (tidak di-commit), results/1-data-preparation/db_checks.csv dan db_tables.csv.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import duckdb
import pandas as pd
import common as CM

if CM.DB_PATH.exists():
    CM.DB_PATH.unlink()
con = duckdb.connect(str(CM.DB_PATH))
dim = pd.DataFrame([(k, v[0], v[1], v[2]) for k, v in CM.TAXONOMY.items()], columns=["category_code", "name", "definition", "example_note"])
con.register("dim_df", dim)
con.execute(f"""
CREATE TABLE dim_category AS SELECT * FROM dim_df;
CREATE TABLE rework_note AS SELECT note_id, CAST(date AS DATE) AS date, shift, station_code, model_code, note_text_clean,
  CAST(is_valid AS INTEGER) AS is_valid FROM read_csv('{CM.CLEAN / "rework_note_clean.csv"}', header=true);
CREATE TABLE manual_label AS SELECT note_id, category_code, 'simulasi (kebenaran generator)' AS labeled_by, CAST(NULL AS DATE) AS labeled_at
  FROM read_csv('{CM.CLEAN / "manual_label_clean.csv"}', header=true);
""")
checks = [
    ("note_id unik", "SELECT count(*) - count(DISTINCT note_id) FROM rework_note"),
    ("teks tidak kosong", "SELECT count(*) FROM rework_note WHERE note_text_clean IS NULL OR length(trim(note_text_clean)) = 0"),
    ("kategori manual ada di dim_category", "SELECT count(*) FROM manual_label m LEFT JOIN dim_category d USING (category_code) WHERE d.category_code IS NULL"),
    ("label manual punya catatan", "SELECT count(*) FROM manual_label m LEFT JOIN rework_note n USING (note_id) WHERE n.note_id IS NULL"),
    ("label manual hanya pada catatan valid", "SELECT count(*) FROM manual_label m JOIN rework_note n USING (note_id) WHERE n.is_valid = 0"),
    ("satu label manual per catatan", "SELECT count(*) - count(DISTINCT note_id) FROM manual_label"),
    ("tanggal dalam periode 2026-03 sampai 2026-08", "SELECT count(*) FROM rework_note WHERE date < DATE '2026-03-01' OR date > DATE '2026-08-31'"),
]
rows = []
for name, q in checks:
    n = int(con.execute(q).fetchone()[0])
    rows.append(dict(pengecekan=name, pelanggaran=n, hasil="lulus" if n == 0 else "gagal"))
pd.DataFrame(rows).to_csv(CM.RES1 / "db_checks.csv", index=False)
tabs = [dict(tabel=t, baris=int(con.execute(f"SELECT count(*) FROM {t}").fetchone()[0])) for t in ("dim_category", "rework_note", "manual_label")]
pd.DataFrame(tabs).to_csv(CM.RES1 / "db_tables.csv", index=False)
con.close()
bad = [r for r in rows if r["hasil"] != "lulus"]
print(tabs, f"pengecekan lulus {len(rows) - len(bad)} dari {len(rows)}")
assert not bad, bad
