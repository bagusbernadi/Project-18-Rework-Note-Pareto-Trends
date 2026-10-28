"""Dashboard Rework Note Analysis (Streamlit + Plotly). 4 halaman: Ringkasan, Per Stasiun, Evaluasi Model, Antrean Cek Manual.
Data dibaca dari results/3-presentation (dibuat oleh 15_dashboard_data.py). Data simulasi yang dianonimkan.
Klasifikasi pada project ini memakai pengganti lokal (TF-IDF + Logistic Regression), bukan Claude API.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

RES = Path(__file__).resolve().parents[3] / "results" / "3-presentation"


@st.cache_data
def load(name):
    return pd.read_csv(RES / name)


par, ps, tm = load("dashboard_pareto.csv"), load("dashboard_pareto_station.csv"), load("dashboard_trend.csv")
cell, em, pc = load("dashboard_station_cell.csv"), load("dashboard_eval_metrics.csv"), load("dashboard_per_class.csv")
conf, th, hyp, que = load("dashboard_confusion.csv"), load("dashboard_threshold.csv"), load("dashboard_hipotesis.csv"), load("dashboard_antrean.csv")
q11, q12 = load("dashboard_dampak_q11.csv").iloc[0], load("dashboard_dampak_q12.csv").iloc[0]

st.set_page_config(page_title="Rework Note Analysis", layout="wide")
st.title("Rework Note Analysis: Defect Pareto & Trends")
st.caption("Data simulasi yang dianonimkan. Klasifikasi memakai pengganti lokal, bukan Claude API. Angka menggambarkan simulasi, bukan kondisi pabrik.")
page = st.sidebar.radio("Halaman", ["Ringkasan", "Per Stasiun", "Evaluasi Model", "Antrean Cek Manual"])

if page == "Ringkasan":
    top = par.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Catatan diklasifikasi", f"{int(par.n.sum()):,}".replace(",", "."))
    c2.metric("Penyebab terbesar", f"{top.category_code} {top.nama}")
    c3.metric("Porsi penyebab terbesar", f"{top.share * 100:.1f}%")
    k80 = int((par.cum_share >= 0.8).idxmax() + 1)
    c4.metric("Kategori untuk mencapai 80%", str(k80))
    fig = go.Figure()
    fig.add_bar(x=par.category_code + " " + par.nama, y=par.n, name="Jumlah catatan", marker_color="#1A73E8")
    fig.add_scatter(x=par.category_code + " " + par.nama, y=par.cum_share * 100, name="Kumulatif (%)", yaxis="y2", mode="lines+markers", line=dict(color="#D93025"))
    fig.update_layout(yaxis=dict(title="Jumlah catatan"), yaxis2=dict(title="Kumulatif (%)", overlaying="y", side="right", range=[0, 100]), height=420, xaxis_tickangle=-30)
    st.plotly_chart(fig, width="stretch")
    st.caption("Pareto seluruh catatan valid. Perkiraan dampak (estimated): menurunkan kategori teratas 20% menghemat sekitar "
               f"{q11.jam_dihemat_per_bulan:.1f} jam rework per bulan; rekap otomatis menghemat sekitar {q12.jam_dihemat_per_bulan:.1f} jam baca per bulan (asumsi di docs/definitions.md).")
    month = st.selectbox("Tren bulanan: kategori", sorted(tm.category_code.unique()))
    t = tm[tm.category_code == month]
    f2 = px.line(t, x="month", y="share", markers=True)
    f2.update_layout(yaxis_title="Porsi catatan bulan itu", height=300)
    st.plotly_chart(f2, width="stretch")

elif page == "Per Stasiun":
    stn = sorted(ps.station_code.unique())
    sel = st.selectbox("Stasiun", ["semua"] + stn)
    pv = ps.pivot(index="station_code", columns="category_code", values="share")
    f = px.imshow(pv * 100, text_auto=".1f", aspect="auto", color_continuous_scale="Blues", labels=dict(color="% catatan stasiun"))
    f.update_layout(height=380)
    st.plotly_chart(f, width="stretch")
    d = ps if sel == "semua" else ps[ps.station_code == sel]
    st.dataframe(d.sort_values(["station_code", "rank_in_station"])[["station_code", "category_code", "nama", "n", "share", "rank_in_station"]], hide_index=True, width="stretch")
    st.subheader("Sel stasiun dan kategori yang menonjol (rasio >= 1,5 dan Holm p < 0,05)")
    st.dataframe(cell[cell.memenuhi_h4 == 1][["station_code", "category_code", "n", "porsi_stasiun", "porsi_seharusnya", "rasio", "p_holm"]], hide_index=True, width="stretch")

elif page == "Evaluasi Model":
    st.dataframe(em, hide_index=True, width="stretch")
    st.caption("Golden set valid; prediksi pengganti lokal adalah out-of-fold. Interval kepercayaan: Wilson (accuracy), bootstrap (macro F1).")
    st.dataframe(pc[["category_code", "nama", "support", "precision", "recall", "f1", "f1_baseline"]], hide_index=True, width="stretch")
    m = conf.set_index("manual")
    f = px.imshow(m, text_auto=True, aspect="auto", color_continuous_scale="Blues")
    f.update_layout(height=420)
    st.plotly_chart(f, width="stretch")
    t = st.slider("Ambang keyakinan", 0.3, 0.9, 0.7, step=0.1)
    r = th[(th.ambang - t).abs() < 1e-9].iloc[0]
    a, b, c = st.columns(3)
    a.metric("Diterima otomatis", f"{r.coverage * 100:.1f}%")
    b.metric("Accuracy otomatis", f"{r.accuracy_otomatis * 100:.1f}%")
    c.metric("Perlu cek manual", f"{int(r.perlu_cek_manual)}")
    st.subheader("Hipotesis")
    st.dataframe(hyp[["kode", "hasil", "bukti"]], hide_index=True, width="stretch")

else:
    st.write(f"Antrean catatan dengan keyakinan di bawah 0,70: {len(que)} catatan.")
    stn = st.selectbox("Stasiun", ["semua"] + sorted(que.station_code.unique()))
    cat = st.selectbox("Kategori hasil klasifikasi", ["semua"] + sorted(que.llm_cat.unique()))
    d = que
    if stn != "semua":
        d = d[d.station_code == stn]
    if cat != "semua":
        d = d[d.llm_cat == cat]
    st.dataframe(d, hide_index=True, width="stretch")
