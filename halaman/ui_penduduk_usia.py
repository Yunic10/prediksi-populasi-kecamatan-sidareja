import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from model import train_svm_model, predict_population
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def fetch_population_data():
    try:
        response = supabase.table('penduduk_usia').select('*').execute()
        df = pd.DataFrame(response.data)
        df['id_tahun'] = df['id_tahun'].astype(int)
        return df.sort_values('id_tahun')
    except Exception as e:
        st.error(f"Gagal mengambil data: {str(e)}")
        return pd.DataFrame()

def app():
    st.title("Prediksi Jumlah Penduduk per Kelompok Umur")
    st.markdown("---")
    
    # Load data
    df = fetch_population_data()
    if df.empty:
        st.warning("Tidak ada data yang ditemukan!")
        st.stop()
    
    # Get unique age groups
    age_groups = df['kategori_usia'].unique()
    
    # Calculate percentage changes
    df_grouped = df.groupby('kategori_usia')
    for col in ['laki_laki', 'perempuan', 'total']:
        df[f'% Perubahan {col}'] = df_grouped[col].pct_change() * 100
    
    # Train models for each age group
    models = {}
    metrics = {}
    
    for group in age_groups:
        # Filter data for the current age group
        group_data = df[df['kategori_usia'] == group]
        
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
            'MAPE Laki': mape_laki,
            'R² Laki': r2_laki,
            'MAPE Perempuan': mape_perempuan,
            'R² Perempuan': r2_perempuan
        }
    
    # Make predictions for 2024-2026
    last_year = df['id_tahun'].max()
    next_years = np.array([last_year + 1, last_year + 2, last_year + 3]).reshape(-1, 1)
    
    pred_data = []
    for group in age_groups:
        # Get predictions
        pred_total = models[group]['total'].predict(next_years)
        pred_laki = models[group]['laki_laki'].predict(next_years)
        pred_perempuan = models[group]['perempuan'].predict(next_years)
        
        # Get last historical values
        filtered_df = df[(df['id_tahun'] == last_year) & (df['kategori_usia'] == group)]
        if not filtered_df.empty:
            last_values = filtered_df.iloc[0]
        else:
            # Handle the case where no matching data was found
            last_values = None  # or some default value
            st.warning(f"No data found for year {last_year} and age group {group}")
        
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

    # Historical data
    for age in age_categories:
        age_data = combined_df[(combined_df['Type'] == 'Historical') & 
                            (combined_df['kategori_usia'] == age)]
        
        fig.add_trace(go.Bar(
            x=age_data['id_tahun'],
            y=age_data['total'],
            name=f'{age} (Historical)',
            marker_color=age_colors[age],
            text=age_data['total'].apply(lambda x: f"{x:,.0f}"),
            textposition='auto',
            opacity=0.7
        ))

    # Predicted data
    for age in age_categories:
        age_data = combined_df[(combined_df['Type'] == 'Predicted') & 
                            (combined_df['kategori_usia'] == age)]
        
        fig.add_trace(go.Bar(
            x=age_data['id_tahun'],
            y=age_data['total'],
            name=f'{age} (Predicted)',
            marker_color=age_colors[age],
            text=age_data['total'].apply(lambda x: f"{x:,.0f}"),
            textposition='auto',
            marker_line_color='rgb(0,0,0)',
            marker_line_width=1.5,
            opacity=0.9
        ))

    fig.update_layout(
        barmode='group',
        title='Perkembangan Penduduk per Kelompok Umur',
        xaxis_title='Tahun',
        yaxis_title='Jumlah Penduduk',
        legend_title="Kelompok Umur",
        hovermode='x unified',
        bargap=0.15,
        bargroupgap=0.1
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Display historical data
    st.subheader("Data Historis")

    # Daftar kolom yang ingin ditampilkan
    columns_to_show = [
        'id_tahun',
        'kategori_usia',
        'laki_laki',
        'perempuan',
        'total',
        '% Perubahan laki_laki',
        '% Perubahan perempuan',
        '% Perubahan total'
    ]

    # Filter kolom yang akan ditampilkan (exclude id_penduduk_usia)
    formatted_df = (
        df[columns_to_show]  # Hanya ambil kolom yang ingin ditampilkan
        .rename(columns={
            'id_tahun': 'Tahun',
            'kategori_usia': 'Kelompok Umur',
            'laki_laki': 'Laki-laki',
            'perempuan': 'Perempuan',
            'total': 'Total'
        })
        .reset_index(drop=True)  # Reset index
    )

    # Format nilai numerik
    def format_value(x, is_pct=False):
        if pd.isna(x):
            return ""
        if is_pct:
            return f"{float(x):+.1f}%"
        return f"{float(x):,.0f}"

    # Terapkan formatting
    formatted_df['Tahun'] = formatted_df['Tahun'].astype(str)  
    formatted_df['Laki-laki'] = formatted_df['Laki-laki'].apply(lambda x: format_value(x))
    formatted_df['Perempuan'] = formatted_df['Perempuan'].apply(lambda x: format_value(x))
    formatted_df['Total'] = formatted_df['Total'].apply(lambda x: format_value(x))

    # Format kolom persentase jika ada
    pct_cols = ['% Δ Laki_laki', '% Δ Perempuan', '% Δ Total']
    for col in pct_cols:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(lambda x: format_value(x, is_pct=True))

    # Fungsi styling
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

    # Terapkan styling
    styled_df = (
        formatted_df
        .style
        .applymap(style_negative_positive)
        .format(None, na_rep="")
    )

    # Tampilkan tabel
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=600,
        hide_index=True
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