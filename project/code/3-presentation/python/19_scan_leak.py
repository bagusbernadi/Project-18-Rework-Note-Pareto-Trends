"""19: Pindai kebocoran identitas. Mencari nama asli (dari mapping key) di semua file yang akan di-commit.
Kode generator (00), anonimisasi (01), dan cek kebenaran (14) memuat nama asli karangan karena mendefinisikan atau memakai pemetaan: dicatat, tidak dihitung kebocoran.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

REPO = CM.ROOT.parent
key = json.loads(CM.MAPPING.read_text(encoding="utf-8"))
TERMS = {"nama stasiun": list(dict(key["station"])), "nama model": list(dict(key["model"]))}
_gen = (CM.ROOT / "code" / "1-data-preparation" / "python" / "00_generate_raw.py").read_text(encoding="utf-8")
TERMS["nama orang"] = re.findall(r'"([A-Z][a-z]+)"', re.search(r"NAMES = \[(.*?)\]", _gen, re.S).group(1))
PATTERNS = {"nomor lot": r"\bLOT-[0-9A-F]{4}\b", "nomor serial": r"\bSN\d{8}\b"}
ALLOW = {"project/code/1-data-preparation/python/00_generate_raw.py", "project/code/1-data-preparation/python/01_anonymize.py",
         "project/code/2-analysis/python/14_ground_truth_check.py", "project/code/3-presentation/python/19_scan_leak.py"}
SKIP_DIRS = {"__pycache__", ".git"}
SKIP_FILES = {"leak_scan.csv", "mapping.json", "notes.duckdb", "notes.duckdb.wal"}
TEXT = {".csv", ".md", ".py", ".html", ".sql", ".txt", ".css", ".js", ".json", ".ipynb", ".yaml", ".yml", ".toml"}
roots = [REPO / "README.md", REPO / "index.html", REPO / "design-and-report", REPO / "project", REPO / ".gitignore"]
files = []
for r in roots:
    if r.is_file():
        files.append(r)
    elif r.exists():
        for p in r.rglob("*"):
            if p.is_file() and not (set(p.parts) & SKIP_DIRS) and p.name not in SKIP_FILES and (p.suffix in TEXT or p.name == ".gitignore") \
                    and "data/raw" not in p.as_posix():
                files.append(p)
rows = []
for p in sorted(set(files)):
    rel = p.relative_to(REPO).as_posix()
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    hits = {k: sum(1 for t in v if re.search(rf"\b{re.escape(t)}\b", text)) for k, v in TERMS.items()}
    hits.update({k: len(re.findall(v, text, re.I)) for k, v in PATTERNS.items()})
    n = sum(hits.values())
    label = "kode pemetaan (diizinkan)" if rel in ALLOW else "data/hasil/dokumen"
    rows.append(dict(file=rel, jenis=label, kecocokan=n, kategori=";".join(f"{k}={v}" for k, v in hits.items() if v)))
scan = pd.DataFrame(rows)
scan["hasil"] = scan.apply(lambda r: "lulus" if r.kecocokan == 0 else ("diizinkan (kode pemetaan)" if r.jenis.startswith("kode") else "gagal"), axis=1)
scan.to_csv(CM.RES3 / "leak_scan.csv", index=False)
print(f"file dipindai: {len(scan)}; file gagal: {int((scan.hasil == 'gagal').sum())}")
print(scan[scan.kecocokan > 0][["file", "jenis", "kecocokan", "hasil"]].to_string(index=False))
assert int((scan.hasil == "gagal").sum()) == 0, "ada kebocoran identitas"
