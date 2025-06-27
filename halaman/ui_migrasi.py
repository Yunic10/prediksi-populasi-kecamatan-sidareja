import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from model import fetch_data, train_svm_model, predict_population

def app():
    st.title("Prediksi Migrasi Penduduk")
    st.markdown("---")
    
    # ======= DATA PREPARATION ======= 
    df = fetch_data(
        table_name="migrasi",
        feature_columns=["id_tahun"],
        target_columns=["migrasi_masuk", "migrasi_keluar"]
    ).sort_values("id_tahun")
    
    # Hitung perubahan
    df["% Perubahan Masuk"] = df["migrasi_masuk"].pct_change() * 100
    df["% Perubahan Keluar"] = df["migrasi_keluar"].pct_change() * 100
    
    # Train model untuk kedua kategori
    models = {}
    metrics = {}
    for target in ['migrasi_masuk', 'migrasi_keluar']:
        model, mae, mape, r2 = train_svm_model(
            table_name="migrasi",
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
        'migrasi_masuk': models['migrasi_masuk'].predict(next_years),
        'migrasi_keluar': models['migrasi_keluar'].predict(next_years)
    }

    # Menghitung perubahan persentase
    last_values = df[df['id_tahun'] == last_year].iloc[0]
    changes = {
        'migrasi_masuk': (predictions['migrasi_masuk'] - last_values['migrasi_masuk']) / last_values['migrasi_masuk'] * 100,
        'migrasi_keluar': (predictions['migrasi_keluar'] - last_values['migrasi_keluar']) / last_values['migrasi_keluar'] * 100
    }

    # ======= PREDICTION DISPLAY =======
    cols = st.columns(2)
    with cols[0]:
        st.metric(
            f"Prediksi Masuk {last_year+1}", 
            f"{predictions['migrasi_masuk'][0]:,.0f}",
            delta=f"{changes['migrasi_masuk'][0]:+.1f}%"
        )
        st.metric(
            f"Prediksi Masuk {last_year+2}", 
            f"{predictions['migrasi_masuk'][1]:,.0f}",
            delta=f"{changes['migrasi_masuk'][1]:+.1f}%"
        )
        st.metric(
            f"Prediksi Masuk {last_year+3}", 
            f"{predictions['migrasi_masuk'][2]:,.0f}",
            delta=f"{changes['migrasi_masuk'][2]:+.1f}%"
        )

    with cols[1]:
        st.metric(
            f"Prediksi Keluar {last_year+1}",
            f"{predictions['migrasi_keluar'][0]:,.0f}",
            delta=f"{changes['migrasi_keluar'][0]:+.1f}%"
        )
        st.metric(
            f"Prediksi Keluar {last_year+2}",
            f"{predictions['migrasi_keluar'][1]:,.0f}",
            delta=f"{changes['migrasi_keluar'][1]:+.1f}%"
        )
        st.metric(
            f"Prediksi Keluar {last_year+3}",
            f"{predictions['migrasi_keluar'][2]:,.0f}",
            delta=f"{changes['migrasi_keluar'][2]:+.1f}%"
        )
    
    # ======= VISUALIZATION =======
    st.header("Trend Historis & Prediksi")
    
    # Siapkan data untuk visualisasi
    viz_df = df.tail(5).copy()
    viz_df['Type'] = 'Historical'
    
    # Tambahkan data prediksi
    pred_df = pd.DataFrame({
        'id_tahun': np.tile(next_years.flatten(), 2),
        'Kategori': np.repeat(['migrasi_masuk', 'migrasi_keluar'], 3),
        'Jumlah': np.concatenate([predictions['migrasi_masuk'], predictions['migrasi_keluar']]),
        'Type': ['Predicted'] * 6
    })
    
    # Konversi data historis ke format long
    historical_long = viz_df.melt(
        id_vars=['id_tahun', 'Type'],
        value_vars=['migrasi_masuk', 'migrasi_keluar'],
        var_name='Kategori',
        value_name='Jumlah'
    )
    
    # Gabungkan data
    combined_df = pd.concat([historical_long, pred_df])
    
    # Buat visualisasi line chart
    fig = px.line(
        combined_df,
        x="id_tahun",
        y="Jumlah",
        color="Kategori",
        line_dash="Type",
        markers=True,
        title=f"Trend Migrasi Penduduk ({last_year-4}-{next_years[-1][0]})",
        labels={"id_tahun": "Tahun", "Jumlah": "Jumlah Migrasi"},
        color_discrete_map={
            'migrasi_masuk': '#2ecc71',  # Hijau untuk migrasi masuk
            'migrasi_keluar': '#e74c3c'   # Merah untuk migrasi keluar
        },
        line_dash_map={
            'Historical': 'solid',
            'Predicted': 'dot'
        }
    )
    
    # Tambahkan anotasi untuk prediksi
    for year_idx, year in enumerate(next_years.flatten()):
        for kat in ['migrasi_masuk', 'migrasi_keluar']:
            val = predictions[kat][year_idx]
            fig.add_annotation(
                x=year,
                y=val,
                text=f"{val:,.0f}",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-40 if kat == 'migrasi_masuk' else 40,
                font=dict(
                    color='#2ecc71' if kat == 'migrasi_masuk' else '#e74c3c'
                )
            )
    
    fig.update_layout(
        legend_title="Kategori Migrasi",
        xaxis_title="Tahun",
        yaxis_title="Jumlah Migrasi",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ======= TABEL DETAIL =======
    st.header("Detail Data Historis")
    
    # Format tabel
    display_df = df.rename(columns={
        "id_tahun": "Tahun",
        "migrasi_masuk": "Migrasi Masuk",
        "% Perubahan Masuk": "% Δ Masuk",
        "migrasi_keluar": "Migrasi Keluar", 
        "% Perubahan Keluar": "% Δ Keluar"
    })
    
    # Konversi ke string dengan format yang tepat
    display_df['Tahun'] = display_df['Tahun'].astype(str)  # Pastikan tahun sebagai string
    display_df['Migrasi Masuk'] = display_df['Migrasi Masuk'].apply(lambda x: f"{int(x):,}")
    display_df['Migrasi Keluar'] = display_df['Migrasi Keluar'].apply(lambda x: f"{int(x):,}")
    display_df['% Δ Masuk'] = display_df['% Δ Masuk'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "")
    display_df['% Δ Keluar'] = display_df['% Δ Keluar'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "")
    
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
        .map(style_negative_positive, subset=["% Δ Masuk", "% Δ Keluar"])
        .format(None, na_rep="")  # Handle nilai kosong
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

    st.write("*% Δ Masuk : presentase perubahan jumlah penduduk masuk dari data sebelumnya")
    st.write("*% Δ Keluar : presentase perubahan jumlah penduduk keluar dari data sebelumnya")
    
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