import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from model import fetch_data, train_svm_model, predict_population

def style_negative_positive(val):
    if not isinstance(val, str) or len(val) == 0:
        return ''
    if (val.startswith('+') or val[0].isdigit()) and '%' in val:
        color = '#2ecc71'
    elif val.startswith('-') and '%' in val:
        color = '#e74c3c'
    else:
        return ''
    return f'color: {color}'

def app():
    st.title("Prediksi Jumlah Kepala Keluarga")
    st.markdown("---")
    
    # ======= DATA PREPARATION ======= 
    df = fetch_data(
        table_name="keluarga",
        feature_columns=["id_tahun"],
        target_columns=["pria", "wanita", "jumlah_kepala_keluarga"]
    ).sort_values("id_tahun")
    
    # Calculate jumlah_kepala_keluargas and changes
    df['jumlah_kepala_keluarga'] = df['pria'] + df['wanita']
    df["% Perubahan Pria"] = df["pria"].pct_change() * 100
    df["% Perubahan Wanita"] = df["wanita"].pct_change() * 100
    df["% Perubahan jumlah_kepala_keluarga"] = df["jumlah_kepala_keluarga"].pct_change() * 100
    
    # Train model for each category
    models = {}
    metrics = {}
    for target in ['pria', 'wanita', 'jumlah_kepala_keluarga']:
        model, mae, mape, r2 = train_svm_model(
            table_name="keluarga",
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
        'pria': models['pria'].predict(next_years),
        'wanita': models['wanita'].predict(next_years)
    }

    # Menghitung perubahan persentase
    last_values = df[df['id_tahun'] == last_year].iloc[0]
    changes = {
        'pria': (predictions['pria'] - last_values['pria']) / last_values['pria'] * 100,
        'wanita': (predictions['wanita'] - last_values['wanita']) / last_values['wanita'] * 100,
        'jumlah_kepala_keluarga': ((predictions['pria'] + predictions['wanita']) - last_values['jumlah_kepala_keluarga']) / last_values['jumlah_kepala_keluarga'] * 100
    }

    # ======= PREDICTION DISPLAY =======
    st.header("Prediksi 3 Tahun ke Depan")
    cols = st.columns(3)
    with cols[0]:
        st.metric(
            f"Prediksi Kepala Keluarga Pria {last_year+1}", 
            f"{predictions['pria'][0]:,.0f}",
            delta=f"{changes['pria'][0]:+.1f}%"
        )
        st.metric(
            f"Prediksi Kepala Keluarga Pria {last_year+2}", 
            f"{predictions['pria'][1]:,.0f}",
            delta=f"{changes['pria'][1]:+.1f}%"
        )
        st.metric(
            f"Prediksi Kepala Keluarga Pria {last_year+3}", 
            f"{predictions['pria'][2]:,.0f}",
            delta=f"{changes['pria'][2]:+.1f}%"
        )

    with cols[1]:
        st.metric(
            f"Prediksi Kepala Keluarga Wanita {last_year+1}",
            f"{predictions['wanita'][0]:,.0f}",
            delta=f"{changes['wanita'][0]:+.1f}%"
        )
        st.metric(
            f"Prediksi Kepala Keluarga Wanita {last_year+2}",
            f"{predictions['wanita'][1]:,.0f}",
            delta=f"{changes['wanita'][1]:+.1f}%"
        )
        st.metric(
            f"Prediksi Kepala Keluarga Wanita {last_year+3}",
            f"{predictions['wanita'][2]:,.0f}",
            delta=f"{changes['wanita'][2]:+.1f}%"
        )

    with cols[2]:
        st.metric(
            "Total Kepala Keluarga (2024)",
            f"{predictions['pria'][0] + predictions['wanita'][0]:,.0f}",
            delta=f"{changes['jumlah_kepala_keluarga'][0]:+.1f}%"
        )
        st.metric(
            "Total Kepala Keluarga (2025)",
            f"{predictions['pria'][1] + predictions['wanita'][1]:,.0f}",
            delta=f"{changes['jumlah_kepala_keluarga'][1]:+.1f}%"
        )
        st.metric(
            "Total Kepala Keluarga (2026)",
            f"{predictions['pria'][2] + predictions['wanita'][2]:,.0f}",
            delta=f"{changes['jumlah_kepala_keluarga'][2]:+.1f}%"
        )

    # ======= VISUALIZATION =======
    viz_df = df.tail(8).copy()
    viz_df['Type'] = 'Historical'

    # Membuat pred_df dengan panjang yang konsisten (3 tahun)
    pred_df = pd.DataFrame({
        'id_tahun': next_years.flatten(),
        'pria': predictions['pria'],
        'wanita': predictions['wanita'],
        'jumlah_kepala_keluarga': predictions['pria'] + predictions['wanita'],
        'Type': ['Predicted'] * 3
    })

    viz_df = pd.concat([viz_df, pred_df])

    # Visualisasi dengan Plotly
    fig_bar = go.Figure()

    # Data historis
    fig_bar.add_trace(go.Bar(
        x=viz_df[viz_df['Type']=='Historical']['id_tahun'],
        y=viz_df[viz_df['Type']=='Historical']['pria'],
        name='Kepala Keluarga Pria (Historical)',
        marker_color='#3498db'
    ))

    fig_bar.add_trace(go.Bar(
        x=viz_df[viz_df['Type']=='Historical']['id_tahun'],
        y=viz_df[viz_df['Type']=='Historical']['wanita'],
        name='wanita (Historical)',
        marker_color='#f39c12',
        base=viz_df[viz_df['Type']=='Historical']['pria']
    ))

    # Data prediksi
    fig_bar.add_trace(go.Bar(
        x=pred_df['id_tahun'],
        y=pred_df['pria'],
        name='Kepala Keluarga Pria (Predicted)',
        marker_color='#2980b9'
    ))

    fig_bar.add_trace(go.Bar(
        x=pred_df['id_tahun'],
        y=pred_df['wanita'],
        name='wanita (Predicted)',
        marker_color='#d35400',
        base=pred_df['pria']
    ))

    fig_bar.update_layout(
        barmode='stack',
        title='Komposisi Kepala Keluarga Berdasarkan Jenis Kelamin',
        xaxis_title='Tahun',
        yaxis_title='Jumlah Kepala Keluarga'
    )

    st.plotly_chart(fig_bar, use_container_width=True)
    
    # ======= HISTORICAL DATA TABLE =======
    st.header("Data Historis")
    
    # Format the historical data
    hist_df = df.copy()
    hist_df = hist_df.rename(columns={
        'id_tahun': 'Tahun',
        'pria': 'Pria',
        'wanita': 'Wanita',
        'jumlah_kepala_keluarga': 'Total Kepala Keluarga',
        '% Perubahan Pria': '% Δ Pria',
        '% Perubahan Wanita': '% Δ Wanita',
        '% Perubahan jumlah_kepala_keluarga': '% Δ Total'
    })
    
    # Convert to formatted strings
    hist_df['Tahun'] = hist_df['Tahun'].astype(str)  
    hist_df['Pria'] = hist_df['Pria'].apply(lambda x: f"{x:,.0f}")
    hist_df['Wanita'] = hist_df['Wanita'].apply(lambda x: f"{x:,.0f}")
    hist_df['Total Kepala Keluarga'] = hist_df['Total Kepala Keluarga'].apply(lambda x: f"{x:,.0f}")
    
    # Apply percentage formatting
    pct_cols = ['% Δ Pria', '% Δ Wanita', '% Δ Total']
    for col in pct_cols:
        if col in hist_df.columns:
            hist_df[col] = hist_df[col].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "")
    
    # Display the table with styling
    st.dataframe(
        hist_df.style.map(style_negative_positive, subset=pct_cols),
        use_container_width=True,
        hide_index=True
    )

    st.write("*% Δ Pria : presentase perubahan jumlah pria dari data sebelumnya")
    st.write("*% Δ Wanita : presentase perubahan jumlah wanita dari data sebelumnya")
    st.write("*% Δ Total : presentase perubahan jumlah kepala keluarga (pria dan wanita) dari data sebelumnya")
    
    # ======= MODEL PERFORMANCE =======
    st.header("Model Prediksi Berdasarkan MAPE dan R²")
    
    perf_df = pd.DataFrame(metrics).T.reset_index()
    perf_df.columns = ['Kategori', 'MAPE (%)', 'R²']
    
    st.dataframe(
        perf_df.style.format({
            'MAPE (%)': '{:,.1f}%',
            'R²': '{:.3f}'
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