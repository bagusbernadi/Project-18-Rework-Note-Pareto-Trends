"""06: Klasifikasi catatan valid ke 9 kategori (langkah 6 rancangan: Claude API).

PENYIMPANGAN DARI RANCANGAN: tidak ada Claude API key, sehingga klasifikasi dikerjakan oleh PENGGANTI LOKAL (TF-IDF + regresi logistik)
yang dilatih pada golden set. Ini bukan LLM. Modul claude_client.py (prompt, pemeriksa JSON, ulang satu kali, pemanggil API) sudah ditulis,
tetapi pemanggilan API sebenarnya tidak dijalankan dan belum diuji (hanya logikanya, di 07_test_claude_pipeline.py).

Evaluasi jujur tanpa kebocoran:
- Catatan golden set: label = prediksi out-of-fold (5-fold stratified) dari nested CV; konfigurasi dipilih HANYA dari CV dalam (3-fold) pada data latih tiap fold.
- Catatan lain: model dilatih pada seluruh golden set (konfigurasi dipilih dengan CV 5-fold pada golden set).
Hasil: results/2-analysis/llm_label.csv, classifier_config.csv; tabel llm_label di notes.duckdb; prompts/classify_v1.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import duckdb
import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
import common as CM
import claude_client as CC

MODEL_NAME = "pengganti-lokal tfidf+logreg (bukan LLM)"
note = pd.read_csv(CM.CLEAN / "rework_note_clean.csv")
gold = pd.read_csv(CM.CLEAN / "manual_label_clean.csv")
v = note[note.is_valid == 1].reset_index(drop=True)
g = v.merge(gold, on="note_id", how="inner").reset_index(drop=True)
rest = v[~v.note_id.isin(g.note_id)].reset_index(drop=True)
CONFIGS = {"kata C=1": ("word", 1.0), "kata C=10": ("word", 10.0), "karakter C=10": ("char", 10.0), "kata+karakter C=10": ("both", 10.0)}


def feats(kind):
    w = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True)
    c = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True)
    return {"word": [w], "char": [c], "both": [w, c]}[kind]


def fit_predict(cfg, tr_text, tr_y, te_text):
    kind, C = CONFIGS[cfg]
    vs = feats(kind)
    Xtr = hstack([x.fit_transform(tr_text) for x in vs]).tocsr()
    Xte = hstack([x.transform(te_text) for x in vs]).tocsr()
    lr = LogisticRegression(C=C, max_iter=2000, random_state=CM.SEED).fit(Xtr, tr_y)
    return lr.predict(Xte), lr.predict_proba(Xte).max(1), lr


def pick_config(text, y, seed):
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed)
    best, best_s, scores = None, -1, {}
    for cfg in CONFIGS:
        s = []
        for a, b in skf.split(text, y):
            p, _, _ = fit_predict(cfg, text[a], y[a], text[b])
            s.append(f1_score(y[b], p, average="macro", zero_division=0))
        scores[cfg] = float(np.mean(s))
        if scores[cfg] > best_s + 1e-12:
            best, best_s = cfg, scores[cfg]
    return best, scores


text, y = g.note_text_clean.to_numpy(), g.category_code.to_numpy()
oof_cat, oof_conf, cfg_rows = np.empty(len(g), dtype=object), np.zeros(len(g)), []
outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=CM.SEED)
for k, (a, b) in enumerate(outer.split(text, y)):
    cfg, sc = pick_config(text[a], y[a], CM.SEED + k)
    p, conf, _ = fit_predict(cfg, text[a], y[a], text[b])
    oof_cat[b], oof_conf[b] = p, conf
    cfg_rows.append(dict(tahap=f"fold {k + 1}", konfigurasi_terpilih=cfg, **{f"cv_dalam {c}": round(s, 4) for c, s in sc.items()}))
final_cfg, final_sc = pick_config(text, y, CM.SEED + 99)
cfg_rows.append(dict(tahap="model akhir (seluruh golden set)", konfigurasi_terpilih=final_cfg, **{f"cv_dalam {c}": round(s, 4) for c, s in final_sc.items()}))
pd.DataFrame(cfg_rows).to_csv(CM.RES2 / "classifier_config.csv", index=False)
p_rest, conf_rest, _ = fit_predict(final_cfg, text, y, rest.note_text_clean.to_numpy())

out = pd.concat([
    pd.DataFrame(dict(note_id=g.note_id, category_code=oof_cat, confidence=np.round(oof_conf, 6), sumber="out-of-fold (golden set)")),
    pd.DataFrame(dict(note_id=rest.note_id, category_code=p_rest, confidence=np.round(conf_rest, 6), sumber="model akhir")),
]).sort_values("note_id").reset_index(drop=True)
out["model_name"] = MODEL_NAME
out["prompt_version"] = "tidak berlaku"
out["tokens"] = pd.NA
out.to_csv(CM.RES2 / "llm_label.csv", index=False)
CM.PROMPTS.mkdir(exist_ok=True)
(CM.PROMPTS / "classify_v1.md").write_text(
    "# Prompt klasifikasi (versi classify_v1)\n\nPrompt untuk Claude API. Belum dijalankan terhadap API pada project ini (lihat README).\n\n```\n" + CC.render_prompt() + "\n```\n", encoding="utf-8")

con = duckdb.connect(str(CM.DB_PATH))
con.execute("DROP TABLE IF EXISTS llm_label")
con.register("lab", out)
con.execute("CREATE TABLE llm_label AS SELECT note_id, category_code, CAST(confidence AS DOUBLE) AS confidence, model_name, prompt_version, "
            "CAST(NULL AS INTEGER) AS tokens, CAST(NULL AS TIMESTAMP) AS created_at, sumber FROM lab")
assert con.execute("SELECT count(*) FROM llm_label l LEFT JOIN rework_note n USING (note_id) WHERE n.note_id IS NULL OR n.is_valid = 0").fetchone()[0] == 0
con.close()
print(f"golden valid {len(g)}, lain {len(rest)}; model akhir {final_cfg}; macro F1 OOF {f1_score(y, oof_cat.astype(str), average='macro'):.4f}")
