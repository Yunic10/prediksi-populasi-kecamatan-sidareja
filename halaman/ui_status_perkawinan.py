import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from model import fetch_data, train_svm_model, predict_population

def app():
    st.title("Prediksi Status Perkawinan")
    st.markdown("---")
    
    # ======= DATA PREPARATION ======= 
    df = fetch_data(
        table_name="status_perkawinan",
        feature_columns=["id_tahun"],
        target_columns=["status_kawin", "cerai_hidup"]
    ).sort_values("id_tahun")
    
    # Hitung perubahan
    df["% Perubahan Kawin"] = df["status_kawin"].pct_change() * 100
    df["% Perubahan Cerai"] = df["cerai_hidup"].pct_change() * 100
    
    # Train model untuk kedua kategori
    models = {}
    metrics = {}
    for target in ['status_kawin', 'cerai_hidup']:
        model, mae, mape, r2 = train_svm_model(
            table_name="status_perkawinan",
            feature_columns=["id_tahun"],
            target_column=target
        )
        models[target] = model
        metrics[target] = {'MAPE': mape, 'R²': r2}
    
    # ======= PREDICTION LOGIC =======
    last_year = df['id_tahun'].max()
    next_years = np.array([last_year + 1, last_year + 2, last_year + 3]).reshape(-1, 1)  # 3 tahun prediksi

    # Mendapatkan prediksi untuk 3 tahun
    predictions = {
        'status_kawin': models['status_kawin'].predict(next_years),
        'cerai_hidup': models['cerai_hidup'].predict(next_years)
    }

    # Menghitung perubahan persentase
    last_values = df[df['id_tahun'] == last_year].iloc[0]
    changes = {
        'status_kawin': (predictions['status_kawin'] - last_values['status_kawin']) / last_values['status_kawin'] * 100,
        'cerai_hidup': (predictions['cerai_hidup'] - last_values['cerai_hidup']) / last_values['cerai_hidup'] * 100
    }

    # ======= PREDICTION DISPLAY =======
    cols = st.columns(2)
    with cols[0]:
        st.metric(
            f"Prediksi Kawin {last_year+1}", 
            f"{predictions['status_kawin'][0]:,.0f}",
            delta=f"{changes['status_kawin'][0]:+.1f}%"
        )
        st.metric(
            f"Prediksi Kawin {last_year+2}", 
            f"{predictions['status_kawin'][1]:,.0f}",
            delta=f"{changes['status_kawin'][1]:+.1f}%"
        )
        st.metric(
            f"Prediksi Kawin {last_year+3}", 
            f"{predictions['status_kawin'][2]:,.0f}",
            delta=f"{changes['status_kawin'][2]:+.1f}%"
        )

    with cols[1]:
        st.metric(
            "Prediksi Cerai Hidup (2024)",
            f"{predictions['cerai_hidup'][0]:,.0f}",
            delta=f"{changes['cerai_hidup'][0]:+.1f}%"
        )
        st.metric(
            "Prediksi Cerai Hidup (2025)",
            f"{predictions['cerai_hidup'][1]:,.0f}",
            delta=f"{changes['cerai_hidup'][1]:+.1f}%"
        )
        st.metric(
            "Prediksi Cerai Hidup (2026)",
            f"{predictions['cerai_hidup'][2]:,.0f}",
            delta=f"{changes['cerai_hidup'][2]:+.1f}%"
        )
    
    # ======= VISUALIZATION =======
    st.header("Trend Historis & Prediksi")
    
    # Siapkan data untuk visualisasi
    viz_df = df.tail(5).copy()
    viz_df['Type'] = 'Historical'
    
    # Tambahkan data prediksi
    pred_df = pd.DataFrame({
        'id_tahun': next_years.flatten(),
        'status_kawin': predictions['status_kawin'],
        'cerai_hidup': predictions['cerai_hidup'],
        'Type': ['Predicted'] * 3
    })
    viz_df = pd.concat([viz_df, pred_df])
    
    # Buat visualisasi bar chart
    fig_bar = go.Figure()

    # Data historis
    fig_bar.add_trace(go.Bar(
        x=viz_df[viz_df['Type']=='Historical']['id_tahun'],
        y=viz_df[viz_df['Type']=='Historical']['status_kawin'],
        name='Status Kawin (Historical)',
        marker_color='#2ecc71'
    ))

    fig_bar.add_trace(go.Bar(
        x=viz_df[viz_df['Type']=='Historical']['id_tahun'],
        y=viz_df[viz_df['Type']=='Historical']['cerai_hidup'],
        name='Cerai Hidup (Historical)',
        marker_color='#e74c3c'
    ))

    # Data prediksi
    fig_bar.add_trace(go.Bar(
        x=pred_df['id_tahun'],
        y=pred_df['status_kawin'],
        name='Status Kawin (Predicted)',
        marker_color='#27ae60'
    ))

    fig_bar.add_trace(go.Bar(
        x=pred_df['id_tahun'],
        y=pred_df['cerai_hidup'],
        name='Cerai Hidup (Predicted)',
        marker_color='#c0392b'
    ))

    fig_bar.update_layout(
        barmode='group',
        title='Perbandingan Status Perkawinan',
        xaxis_title='Tahun',
        yaxis_title='Jumlah Penduduk',
        legend_title="Kategori"
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # ======= TABEL DETAIL =======
    st.header("Detail Data Historis")
    
    # Format tabel
    display_df = df.rename(columns={
        "id_tahun": "Tahun",
        "status_kawin": "Kawin (Jiwa)",
        "% Perubahan Kawin": "% Δ Kawin",
        "cerai_hidup": "Cerai Hidup (Jiwa)", 
        "% Perubahan Cerai": "% Δ Cerai"
    })
    
    # Konversi ke string dengan format yang tepat
    display_df['Tahun'] = display_df['Tahun'].astype(str)  # Pastikan tahun sebagai string
    display_df['Kawin (Jiwa)'] = display_df['Kawin (Jiwa)'].apply(lambda x: f"{int(x):,}")
    display_df['Cerai Hidup (Jiwa)'] = display_df['Cerai Hidup (Jiwa)'].apply(lambda x: f"{int(x):,}")
    display_df['% Δ Kawin'] = display_df['% Δ Kawin'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "")
    display_df['% Δ Cerai'] = display_df['% Δ Cerai'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "")
    
    # Fungsi styling khusus
    def style_negative_positive(val):
        if not isinstance(val, str) or len(val) == 0:
            return ''
        if (val.startswith('+') or val[0].isdigit()) and '%' in val:
            color = '#2ecc71'  # Hijau untuk positif
        elif val.startswith('-') and '%' in val:
            color = '#e74c3c'  # Merah untuk negatif
        else:
            return ''
        return f'color: {color}'
    
    # Terapkan styling
    styled_df = (
        display_df.style
        .map(style_negative_positive, subset=["% Δ Kawin", "% Δ Cerai"])
        .format(None, na_rep="")  # Handle nilai kosong
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

    st.write("*% Δ Kawin : presentase perubahan jumlah status kawin dari data sebelumnya")
    st.write("*% Δ Cerai : presentase perubahan jumlah status cerai dari data sebelumnya")
    
    # ======= MODEL PERFORMANCE =======
    st.header("Model Prediksi Berdasarkan MAPE dan R²")
    
    perf_df = pd.DataFrame(metrics).T.reset_index()
    perf_df.columns = ['Kategori', 'MAPE (%)', 'R²']
    
    # Format sebagai string
    perf_df['MAPE (%)'] = perf_df['MAPE (%)'].apply(lambda x: f"{x:.1f}%")
    perf_df['R²'] = perf_df['R²'].apply(lambda x: f"{x:.3f}")
    
    st.dataframe(
        perf_df,
        use_container_width=True,
        hide_index=True
    )

    st.write("*MAPE (Mean Absolute Precentage Error) : Rata - rata presentase dibandingkan dengan nilai aslinya. " \
    "Semakin kecil MAPE semakin akurat model")
    st.write("*R-squared : Mengukur seberapa baik model menjelaskan variasi data. " \
    "Semakin mendekati angka 1 semakin baik model menjelaskan variasi data")

    st.markdown("---")
    st.caption("© 2025 - Yudith Nico Priambodo")