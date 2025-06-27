import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from model import fetch_data, train_svm_model, predict_population

def app():
    st.title("Analisis & Prediksi Anak Putus Sekolah")
    st.markdown("---")
    
    # ======= DATA PREPARATION ======= 
    df = fetch_data(
        table_name="putus_sekolah",
        feature_columns=["id_tahun"],
        target_columns=["jumlah_putus_sekolah"]
    ).sort_values("id_tahun")
    
    # Hitung perubahan
    df["% Perubahan"] = df["jumlah_putus_sekolah"].pct_change() * 100
    
    # ======= MODEL TRAINING =======
    st.header("Prediksi 3 Tahun ke Depan")
    
    # Train model
    model, mae, mape, r2 = train_svm_model(
        table_name="putus_sekolah",
        feature_columns=["id_tahun"],
        target_column="jumlah_putus_sekolah"
    )
    
    # ======= PREDICTION LOGIC =======
    last_year = df['id_tahun'].max()
    next_years = np.array([last_year + 1, last_year + 2, last_year + 3]).reshape(-1, 1)  # 3 tahun prediksi

    # Mendapatkan prediksi untuk 3 tahun
    predictions = model.predict(next_years)

    # Menghitung perubahan persentase
    last_value = df[df['id_tahun'] == last_year].iloc[0]['jumlah_putus_sekolah']
    changes = (predictions - last_value) / last_value * 100

    # ======= PREDICTION DISPLAY =======
    cols = st.columns(3)
    with cols[0]:
        st.metric(
            f"Prediksi {last_year+1}", 
            f"{predictions[0]:,.0f}",
            delta=f"{changes[0]:+.1f}%"
        )
    
    with cols[1]:
        st.metric(
            f"Prediksi {last_year+2}", 
            f"{predictions[1]:,.0f}",
            delta=f"{changes[1]:+.1f}%"
        )
    
    with cols[2]:
        st.metric(
            f"Prediksi {last_year+3}", 
            f"{predictions[2]:,.0f}",
            delta=f"{changes[2]:+.1f}%"
        )
    
    # ======= VISUALIZATION =======
    st.header("Trend Historis & Prediksi")
    
    # Siapkan data untuk visualisasi
    viz_df = df.tail(5).copy()
    viz_df['Type'] = 'Historical'
    
    # Tambahkan data prediksi
    pred_df = pd.DataFrame({
        'id_tahun': next_years.flatten(),
        'jumlah_putus_sekolah': predictions,
        'Type': ['Predicted'] * 3
    })
    viz_df = pd.concat([viz_df, pred_df])
    
    # Buat visualisasi line chart
    fig = px.line(
        viz_df,
        x="id_tahun",
        y="jumlah_putus_sekolah",
        color="Type",
        markers=True,
        title=f"Trend Anak Putus Sekolah ({last_year-4}-{next_years[-1][0]})",
        labels={"id_tahun": "Tahun", "jumlah_putus_sekolah": "Jumlah"},
        color_discrete_map={
            "Historical": "#3498db",  # Biru untuk data historis
            "Predicted": "#e74c3c"    # Merah untuk prediksi
        }
    )
    
    # Tambahkan anotasi untuk prediksi
    for i, year in enumerate(next_years.flatten()):
        fig.add_annotation(
            x=year,
            y=predictions[i],
            text=f"{predictions[i]:,.0f}",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40
        )
    
    fig.update_layout(
        legend_title="Kategori",
        xaxis_title="Tahun",
        yaxis_title="Jumlah Anak Putus Sekolah",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
        # ======= TABEL DETAIL =======
    st.header("Detail Data Historis")

    # Format tabel
    display_df = df.rename(columns={
        "id_tahun": "Tahun",
        "jumlah_putus_sekolah": "Jumlah Anak Putus Sekolah",
        "% Perubahan": "Perubahan (%)"
    })

    # Konversi ke string dengan format yang tepat
    display_df['Tahun'] = display_df['Tahun'].astype(str)  # Pastikan tahun sebagai string
    display_df['Jumlah Anak Putus Sekolah'] = display_df['Jumlah Anak Putus Sekolah'].apply(lambda x: f"{int(x):,}")
    display_df['Perubahan (%)'] = display_df['Perubahan (%)'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "")
    
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
        .map(style_negative_positive, subset=["Perubahan (%)"])
        .format(None, na_rep="")  # Handle nilai kosong
        .set_properties(**{
            'text-align': 'center',
            'padding': '8px 12px',
            'font-family': 'Arial, sans-serif'
        })
        .set_table_styles([{
            'selector': 'thead th',
            'props': [
                ('background-color', '#2c3e50'),
                ('color', 'white'),
                ('font-weight', 'bold'),
                ('text-align', 'center')
            ]
        }])
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

    st.write("*% perubahan : presentase perubahan jumlah anak putus sekolah dari data sebelumnya")
    
    # ======= MODEL PERFORMANCE =======
    st.header("Model Prediksi Berdasarkan MAPE dan R²")
    
    perf_df = pd.DataFrame({
        'Metrik': ['Mean Absolute Percentage Error', 'R-squared'],
        'Value': [f"{mape:.1f}%", f"{r2:.3f}"]
    })
    
    st.dataframe(
        perf_df.style.format({
            'Value': '{}'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    st.write("*MAPE (Mean Absolute Precentage Error) : Rata - rata presentase dibandingkan dengan nilai aslinya. " \
    "Semakin kecil MAPE semakin akurat model")
    st.write("*R-squared : Mengukur seberapa baik model menjelaskan variasi data. " \
    "Semakin mendekati angka 1 semakin baik model menjelaskan variasi data")

    st.markdown("---")
    st.caption("© 2025 - Yudith Nico Priambodo")