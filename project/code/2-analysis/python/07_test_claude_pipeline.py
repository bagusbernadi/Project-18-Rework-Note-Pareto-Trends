"""07: Uji logika pipeline Claude API dengan klien palsu (TANPA memanggil API): prompt, pemeriksa JSON, ulang satu kali, nilai cadangan.
Hasil: results/2-analysis/claude_pipeline_test.csv. Pemanggilan API sebenarnya tidak diuji."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import common as CM
import claude_client as CC


class Fake:
    def __init__(self, answers):
        self.answers, self.calls = list(answers), 0

    def complete(self, prompt, note):
        self.calls += 1
        return self.answers.pop(0), 100, 20


res = {}
res["prompt memuat 9 kode kategori"] = all(c in CC.render_prompt() for c in CM.TAXONOMY)
res["JSON valid diterima"] = CC.parse_answer('{"category_code": "C4", "confidence": 0.9, "reason": "x"}') == ("C4", 0.9)
res["kategori di luar daftar ditolak"] = CC.parse_answer('{"category_code": "C12", "confidence": 0.9}') is None
res["confidence di luar 0..1 ditolak"] = CC.parse_answer('{"category_code": "C1", "confidence": 1.4}') is None
res["teks bukan JSON ditolak"] = CC.parse_answer("kategori C1") is None
f = Fake(['bukan json', '{"category_code": "C2", "confidence": 0.8, "reason": "baret"}'])
r = CC.classify_note(f, "baret di pcb")
res["jawaban tidak valid diulang satu kali lalu diterima"] = r["category_code"] == "C2" and f.calls == 2 and r["attempts"] == 2 and r["valid"] == 1
f = Fake(["x", "y"])
r = CC.classify_note(f, "catatan")
res["dua kali tidak valid menjadi C9 dengan confidence 0"] = r["category_code"] == "C9" and r["confidence"] == 0.0 and f.calls == 2 and r["valid"] == 0
res["token dijumlahkan"] = r["tokens"] == 240
out = pd.DataFrame(list(res.items()), columns=["pemeriksaan", "hasil"])
out["hasil"] = out.hasil.map({True: "lulus", False: "gagal"})
out.to_csv(CM.RES2 / "claude_pipeline_test.csv", index=False)
print(out.to_string(index=False))
assert (out.hasil == "lulus").all()
