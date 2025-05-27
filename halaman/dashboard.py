import streamlit as st
import pandas as pd
import plotly.express as px
from model import train_and_predict

def app():
    st.header("Prediksi Populasi Kecamatan Sidareja")
    # Panggil fungsi model
    results = train_and_predict()
    df = results["df"]
    # Grafik menggunakan Plotly
    fig = px.line(
        df,
        x="Tahun",
        y="Jumlah Penduduk",
        markers=True,
        title="Grafik Pertumbuhan Populasi",
        labels={"Tahun": "Tahun", "Jumlah Penduduk": "Populasi"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Prediksi untuk tahun depan
    st.markdown("### Prediksi Populasi Masa Depan")
    st.write(f"**2024:** {int(results['predictions']['2024'])} jiwa")
    st.write(f"**2025:** {int(results['predictions']['2025'])} jiwa")

    # Metrics tambahan
    st.markdown("### Evaluasi Model")
    st.write(f"**MAE:** {results['mae']:.2f}")
    st.write(f"**MAPE:** {results['mape']:.2f}%")
    st.write(f"**R-Squared:** {results['r_squared']:.2f}")