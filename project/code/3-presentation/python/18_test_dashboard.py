"""18: Uji dashboard dengan Streamlit AppTest: tiap halaman berjalan tanpa exception, angka tampil sama dengan CSV."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from streamlit.testing.v1 import AppTest
import common as CM

APP = CM.ROOT / "code" / "3-presentation" / "streamlit" / "app.py"
par = pd.read_csv(CM.RES2 / "pareto.csv")
que = pd.read_csv(CM.RES3 / "dashboard_antrean.csv")
th = pd.read_csv(CM.RES2 / "eval_threshold.csv")
res = {}
at = AppTest.from_file(str(APP), default_timeout=90).run()
res["halaman Ringkasan tanpa error"] = not at.exception
shown = {m.label: m.value for m in at.metric}
res["jumlah catatan sama dengan CSV"] = shown["Catatan diklasifikasi"] == f"{int(par.n.sum()):,}".replace(",", ".")
res["porsi penyebab terbesar sama dengan CSV"] = shown["Porsi penyebab terbesar"] == f"{par.share.iloc[0] * 100:.1f}%"
res["kategori untuk 80% sama dengan CSV"] = shown["Kategori untuk mencapai 80%"] == str(int((par.cum_share >= 0.8).idxmax() + 1))
at.selectbox[0].set_value("C2").run()
res["ganti kategori tren tanpa error"] = not at.exception
for page in ("Per Stasiun", "Evaluasi Model", "Antrean Cek Manual"):
    at.sidebar.radio[0].set_value(page).run()
    res[f"halaman {page} tanpa error"] = not at.exception
    res[f"halaman {page} punya tabel atau grafik"] = len(at.dataframe) + len(at.get("plotly_chart")) >= 1
at.sidebar.radio[0].set_value("Per Stasiun").run()
at.selectbox[0].set_value("ST-C").run()
res["filter stasiun tanpa error"] = not at.exception
at.sidebar.radio[0].set_value("Evaluasi Model").run()
at.slider[0].set_value(0.8).run()
r = th[(th.ambang - 0.8).abs() < 1e-9].iloc[0]
res["slider ambang tanpa error"] = not at.exception
res["slider ambang: perlu cek manual sama dengan CSV"] = {m.label: m.value for m in at.metric}["Perlu cek manual"] == str(int(r.perlu_cek_manual))
at.sidebar.radio[0].set_value("Antrean Cek Manual").run()
res["antrean sama dengan CSV"] = f"{len(que)} catatan" in at.markdown[0].value or any(f"{len(que)} catatan" in m.value for m in at.markdown)
at.selectbox[0].set_value(que.station_code.iloc[0]).run()
res["filter antrean tanpa error"] = not at.exception
out = pd.DataFrame(list(res.items()), columns=["pemeriksaan", "hasil"])
out["hasil"] = out.hasil.map({True: "lulus", False: "gagal"})
out.to_csv(CM.RES3 / "dashboard_test.csv", index=False)
print(out.to_string(index=False))
assert (out.hasil == "lulus").all(), "uji dashboard gagal"
