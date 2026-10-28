-- Project 18: view analisis catatan rework. Dibuat oleh 08_run_queries.py (DuckDB). Semua ORDER BY memakai tie-breaker.

-- Dasar: catatan valid dengan label hasil klasifikasi dan bulan
CREATE OR REPLACE VIEW v_note_llm AS
SELECT n.note_id, n.date, strftime(n.date, '%Y-%m') AS month, n.shift, n.station_code, n.model_code, n.note_text_clean,
       l.category_code AS llm_cat, l.confidence, l.sumber
FROM rework_note n JOIN llm_label l USING (note_id)
WHERE n.is_valid = 1;

-- Q1: Pareto kategori dengan kumulatif (window function)
CREATE OR REPLACE VIEW v_pareto AS
WITH c AS (SELECT llm_cat AS category_code, count(*) AS n FROM v_note_llm GROUP BY llm_cat),
     t AS (SELECT c.*, c.n * 1.0 / sum(c.n) OVER () AS share FROM c)
SELECT row_number() OVER (ORDER BY n DESC, category_code) AS rank, category_code, n, share,
       sum(share) OVER (ORDER BY n DESC, category_code ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_share
FROM t;

-- Q2: Pareto per stasiun (kerangka stasiun x kategori agar nol tetap muncul)
CREATE OR REPLACE VIEW v_pareto_station AS
WITH spine AS (SELECT s.station_code, d.category_code FROM (SELECT DISTINCT station_code FROM rework_note) s CROSS JOIN dim_category d),
     c AS (SELECT sp.station_code, sp.category_code, count(v.note_id) AS n
           FROM spine sp LEFT JOIN v_note_llm v ON v.station_code = sp.station_code AND v.llm_cat = sp.category_code GROUP BY 1, 2),
     t AS (SELECT *, n * 1.0 / sum(n) OVER (PARTITION BY station_code) AS share, sum(n) OVER (PARTITION BY station_code) AS station_total FROM c)
SELECT station_code, category_code, n, station_total, share,
       RANK() OVER (PARTITION BY station_code ORDER BY n DESC, category_code) AS rank_in_station
FROM t;

-- Q3: tren bulanan per kategori dengan LAG (kerangka bulan x kategori)
CREATE OR REPLACE VIEW v_trend_month AS
WITH spine AS (SELECT m.month, d.category_code FROM (SELECT DISTINCT month FROM v_note_llm) m CROSS JOIN dim_category d),
     c AS (SELECT sp.month, sp.category_code, count(v.note_id) AS n FROM spine sp
           LEFT JOIN v_note_llm v ON v.month = sp.month AND v.llm_cat = sp.category_code GROUP BY 1, 2),
     t AS (SELECT *, sum(n) OVER (PARTITION BY month) AS month_total FROM c)
SELECT month, category_code, n, month_total, n * 1.0 / month_total AS share,
       LAG(n * 1.0 / month_total) OVER (PARTITION BY category_code ORDER BY month) AS prev_share
FROM t;

-- Q4: tabel silang kategori x shift x model, dan kategori x stasiun
CREATE OR REPLACE VIEW v_cross_shift_model AS
SELECT llm_cat AS category_code, shift, model_code, count(*) AS n FROM v_note_llm GROUP BY 1, 2, 3;

CREATE OR REPLACE VIEW v_cross_station_cat AS
SELECT station_code, llm_cat AS category_code, count(*) AS n FROM v_note_llm GROUP BY 1, 2;

-- Q5, Q6, Q14: label klasifikasi vs label manual pada golden set
CREATE OR REPLACE VIEW v_compare_golden AS
SELECT m.note_id, m.category_code AS manual_cat, l.category_code AS llm_cat, l.confidence, b.category_code AS baseline_cat,
       CASE WHEN m.category_code = l.category_code THEN 1 ELSE 0 END AS match_llm,
       CASE WHEN m.category_code = b.category_code THEN 1 ELSE 0 END AS match_baseline
FROM manual_label m JOIN llm_label l USING (note_id) JOIN baseline_label b USING (note_id);

CREATE OR REPLACE VIEW v_confusion AS
SELECT manual_cat, llm_cat, count(*) AS n FROM v_compare_golden GROUP BY 1, 2;

CREATE OR REPLACE VIEW v_pareto_golden AS
WITH a AS (SELECT manual_cat AS category_code, count(*) AS n_manual FROM v_compare_golden GROUP BY 1),
     b AS (SELECT llm_cat AS category_code, count(*) AS n_llm FROM v_compare_golden GROUP BY 1)
SELECT d.category_code, coalesce(a.n_manual, 0) AS n_manual, coalesce(b.n_llm, 0) AS n_llm,
       RANK() OVER (ORDER BY coalesce(a.n_manual, 0) DESC, d.category_code) AS rank_manual,
       RANK() OVER (ORDER BY coalesce(b.n_llm, 0) DESC, d.category_code) AS rank_llm
FROM dim_category d LEFT JOIN a USING (category_code) LEFT JOIN b USING (category_code);

-- Q8: catatan di kategori Lainnya
CREATE OR REPLACE VIEW v_other AS
SELECT note_id, month, station_code, note_text_clean, confidence FROM v_note_llm WHERE llm_cat = 'C9';
