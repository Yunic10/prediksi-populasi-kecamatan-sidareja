import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from model import fetch_data, train_svm_model, predict_population

@st.cache_data
def fetch_population_data():
    """Fetch population data dari Supabase dengan caching"""
    try:
        df = fetch_data(
            table_name="penduduk_usia",
            feature_columns=["id_tahun"],
            target_columns=["kategori_usia", "laki_laki", "perempuan", "total"]
        )
        if not df.empty:
            # Pastikan kolom id_tahun ada dan bertipe int
            if 'id_tahun' in df.columns:
                df['id_tahun'] = df['id_tahun'].astype(int)
            else:
                # Jika tidak ada kolom id_tahun, buat dari index atau kolom tahun
                if 'tahun' in df.columns:
                    df['id_tahun'] = df['tahun'].astype(int)
                else:
                    # Buat tahun dummy berdasarkan index
                    df['id_tahun'] = range(2020, 2020 + len(df))
            
            return df.sort_values('id_tahun')
        else:
            st.warning("Data kosong atau tidak ditemukan!")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal mengambil data: {str(e)}")
        return pd.DataFrame()

def app():
    st.title("Prediksi Jumlah Penduduk per Kelompok Umur")
    st.markdown("---")
    
    # Load data dengan caching
    df = fetch_population_data()
    if df.empty:
        st.warning("Tidak ada data yang ditemukan!")
        st.stop()
    
    # Get unique age groups
    age_groups = df['kategori_usia'].unique() if 'kategori_usia' in df.columns else []
    
    if len(age_groups) == 0:
        st.error("Kolom 'kategori_usia' tidak ditemukan dalam data!")
        st.write("Kolom yang tersedia:", df.columns.tolist())
        st.stop()
    
    # Calculate percentage changes
    df_grouped = df.groupby('kategori_usia')
    for col in ['laki_laki', 'perempuan', 'total']:
        if col in df.columns:
            df[f'% Perubahan {col}'] = df_grouped[col].pct_change() * 100
    
    # Train models for each age group
    models = {}
    metrics = {}
    
    for group in age_groups:
        # Filter data for the current age group
        group_data = df[df['kategori_usia'] == group]
        
        if len(group_data) < 2:
            st.warning(f"Data tidak cukup untuk kelompok {group}")
            continue
        
        # Train models
        model_total, mae_total, mape_total, r2_total = train_svm_model(
            feature_columns=['id_tahun'],
            target_column='total',
            data=group_data
        )
        
        model_laki, mae_laki, mape_laki, r2_laki = train_svm_model(
            feature_columns=['id_tahun'],
            target_column='laki_laki',
            data=group_data
        )
        
        model_perempuan, mae_perempuan, mape_perempuan, r2_perempuan = train_svm_model(
            feature_columns=['id_tahun'],
            target_column='perempuan',
            data=group_data
        )
        
        models[group] = {
            'total': model_total,
            'laki_laki': model_laki,
            'perempuan': model_perempuan
        }
        
        metrics[group] = {
            'MAPE Total': mape_total,
            'R² Total': r2_total,
            'MAPE Laki': mae_laki,
            'R² Laki': r2_laki,
            'MAPE Perempuan': mae_perempuan,
            'R² Perempuan': r2_perempuan
        }
    
    # Make predictions for 2024-2026
    last_year = df['id_tahun'].max()
    next_years = np.array([last_year + 1, last_year + 2, last_year + 3]).reshape(-1, 1)
    
    pred_data = []
    for group in age_groups:
        if group not in models:
            continue
            
        # Get predictions
        pred_total = models[group]['total'].predict(next_years)
        pred_laki = models[group]['laki_laki'].predict(next_years)
        pred_perempuan = models[group]['perempuan'].predict(next_years)
        
        # Get last historical values
        filtered_df = df[(df['id_tahun'] == last_year) & (df['kategori_usia'] == group)]
        if not filtered_df.empty:
            last_values = filtered_df.iloc[0]
            
            # Calculate percentage changes
            changes_total = (pred_total - last_values['total']) / last_values['total'] * 100
            changes_laki = (pred_laki - last_values['laki_laki']) / last_values['laki_laki'] * 100
            changes_perempuan = (pred_perempuan - last_values['perempuan']) / last_values['perempuan'] * 100
            
            for i, year in enumerate(next_years.flatten()):
                pred_data.append({
                    'Tahun': year,
                    'Kelompok Umur': group,
                    'Total': pred_total[i],
                    'Laki-laki': pred_laki[i],
                    'Perempuan': pred_perempuan[i],
                    '% Δ Total': changes_total[i],
                    '% Δ Laki': changes_laki[i],
                    '% Δ Perempuan': changes_perempuan[i]
                })
        else:
            st.warning(f"No data found for year {last_year} and age group {group}")
    
    if not pred_data:
        st.error("Tidak dapat membuat prediksi karena data tidak cukup")
        st.stop()
        
    pred_df = pd.DataFrame(pred_data)
    
    # Display predictions
    st.header("Hasil Prediksi 2024-2026")
    
    # Age group selector
    selected_group = st.selectbox(
        "Pilih Kelompok Umur untuk Detail:",
        age_groups
    )
    
    # Show metrics for selected group
    group_pred = pred_df[pred_df['Kelompok Umur'] == selected_group]
    last_values = df[(df['id_tahun'] == last_year) & (df['kategori_usia'] == selected_group)].iloc[0]
    
    cols = st.columns(3)
    with cols[0]:
        for i, year in enumerate([2024, 2025, 2026]):
            st.metric(
                f"Prediksi {selected_group} {year}", 
                f"{group_pred[group_pred['Tahun'] == year]['Total'].values[0]:,.0f}",
                delta=f"{group_pred[group_pred['Tahun'] == year]['% Δ Total'].values[0]:+.1f}%"
            )
    
    with cols[1]:
        for i, year in enumerate([2024, 2025, 2026]):
            st.metric(
                f"Prediksi {selected_group} {year}", 
                f"{group_pred[group_pred['Tahun'] == year]['Laki-laki'].values[0]:,.0f}",
                delta=f"{group_pred[group_pred['Tahun'] == year]['% Δ Laki'].values[0]:+.1f}%"
            )
    
    with cols[2]:
        for i, year in enumerate([2024, 2025, 2026]):
            st.metric(
                f"Prediksi {selected_group} {year}", 
                f"{group_pred[group_pred['Tahun'] == year]['Perempuan'].values[0]:,.0f}",
                delta=f"{group_pred[group_pred['Tahun'] == year]['% Δ Perempuan'].values[0]:+.1f}%"
            )
    
    # Combined visualization for all age groups
    st.header("Trend Historis & Prediksi per Kelompok Umur")

    # Prepare data for visualization - group by age categories
    age_categories = ['0-14', '15-60', '60+']

    # Historical data grouped by age category
    hist_df = df.groupby(['id_tahun', 'kategori_usia']).sum().reset_index()
    hist_df = hist_df[hist_df['kategori_usia'].isin(age_categories)].tail(15)  # Last 5 years (3 categories)
    hist_df['Type'] = 'Historical'

    # Predicted data grouped by age category
    pred_viz_df = pred_df.copy()
    pred_viz_df = pred_viz_df[pred_viz_df['Kelompok Umur'].isin(age_categories)]
    pred_viz_df = pred_viz_df.rename(columns={
        'Total': 'total',
        'Laki-laki': 'laki_laki',
        'Perempuan': 'perempuan',
        'Kelompok Umur': 'kategori_usia'
    })
    pred_viz_df['Type'] = 'Predicted'
    pred_viz_df['id_tahun'] = pred_viz_df['Tahun']

    combined_df = pd.concat([hist_df, pred_viz_df])

    # Create figure
    fig = go.Figure()

    # Colors for each age category
    age_colors = {
        '0-14': '#3498db',
        '15-60': '#2ecc71',
        '60+': '#e74c3c'
    }

    # Add traces for each age category
    for age_cat in age_categories:
        # Historical data
        hist_data = combined_df[(combined_df['kategori_usia'] == age_cat) & (combined_df['Type'] == 'Historical')]
        if not hist_data.empty:
            fig.add_trace(go.Scatter(
                x=hist_data['id_tahun'],
                y=hist_data['total'],
                mode='lines+markers',
                name=f'{age_cat} (Historical)',
                line=dict(color=age_colors[age_cat], width=3),
                marker=dict(size=8)
            ))
        
        # Predicted data
        pred_data = combined_df[(combined_df['kategori_usia'] == age_cat) & (combined_df['Type'] == 'Predicted')]
        if not pred_data.empty:
            fig.add_trace(go.Scatter(
                x=pred_data['id_tahun'],
                y=pred_data['total'],
                mode='lines+markers',
                name=f'{age_cat} (Predicted)',
                line=dict(color=age_colors[age_cat], width=3, dash='dash'),
                marker=dict(size=8, symbol='diamond')
            ))

    fig.update_layout(
        title='Trend Jumlah Penduduk per Kelompok Umur (Historikal & Prediksi)',
        xaxis_title='Tahun',
        yaxis_title='Jumlah Penduduk',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display prediction table
    st.header("Tabel Prediksi Detail")
    
    def format_value(x, is_pct=False):
        if pd.isna(x):
            return "-"
        if is_pct:
            return f"{x:.1f}%"
        return f"{x:,.0f}"
    
    def style_negative_positive(val):
        if pd.isna(val):
            return ''
        if isinstance(val, str) and '%' in val:
            val = float(val.replace('%', ''))
        if val < 0:
            return 'color: #e74c3c'
        elif val > 0:
            return 'color: #2ecc71'
        return ''

    # Style the prediction table
    styled_pred_df = pred_df.copy()
    for col in ['Total', 'Laki-laki', 'Perempuan']:
        styled_pred_df[col] = styled_pred_df[col].apply(lambda x: format_value(x))
    for col in ['% Δ Total', '% Δ Laki', '% Δ Perempuan']:
        styled_pred_df[col] = styled_pred_df[col].apply(lambda x: format_value(x, is_pct=True))

    st.dataframe(
        styled_pred_df.style.applymap(style_negative_positive, subset=['% Δ Total', '% Δ Laki', '% Δ Perempuan']),
        use_container_width=True
    )

    st.write("*% Δ Laki-laki : presentase perubahan jumlah laki-laki dari data sebelumnya")
    st.write("*% Δ Perempuan : presentase perubahan jumlah perempuan dari data sebelumnya")
    st.write("*% Δ Total : presentase perubahan jumlah penduduk (laki-laki dan perempuan) dari data sebelumnya")

    # Model performance table
    st.header("Model Prediksi Berdasarkan MAPE dan R²")

    perf_df = pd.DataFrame([
        {
            'Kelompok Umur': group,
            'MAPE Total': f"{metrics[group]['MAPE Total']:,.1f}%",
            'R² Total': f"{metrics[group]['R² Total']:.3f}",
            'MAPE Laki': f"{metrics[group]['MAPE Laki']:,.1f}%",
            'R² Laki': f"{metrics[group]['R² Laki']:.3f}",
            'MAPE Perempuan': f"{metrics[group]['MAPE Perempuan']:,.1f}%",
            'R² Perempuan': f"{metrics[group]['R² Perempuan']:.3f}"
        }
        for group in age_groups
    ]).reset_index(drop=True)  # Reset index

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