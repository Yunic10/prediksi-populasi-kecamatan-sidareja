import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
from model import fetch_data, train_svm_model, predict_population
import os

# Koneksi ke Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv('SUPABASE_KEY')  # Menggunakan environment variable untuk keamanan
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
def app():
    st.header("Prediksi Populasi Kecamatan Sidareja")

    # Ambil data tahunan untuk grafik
    df= fetch_data(
        table_name="penduduk_tahunan", 
        feature_columns= ["id_tahun"], 
        target_columns= ["jumlah_penduduk", "laki_laki", "perempuan"]
        ).sort_values("id_tahun")
    
    # Calculate jumlah_penduduks and changes
    df['Jumlah Penduduk'] = df['laki_laki'] + df['perempuan']
    df["% Perubahan Laki_laki"] = df["laki_laki"].pct_change() * 100
    df["% Perubahan Perempuan"] = df["perempuan"].pct_change() * 100
    df["% Perubahan Jumlah Penduduk"] = df["jumlah_penduduk"].pct_change() * 100
    
    # Train model for each category
    models = {}
    metrics = {}
    for target in ['laki_laki', 'perempuan', 'jumlah_penduduk']:
        model, mae, mape, r2 = train_svm_model(
            table_name="penduduk_tahunan",
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
        'laki_laki': models['laki_laki'].predict(next_years),
        'perempuan': models['perempuan'].predict(next_years)
    }

    # Menghitung perubahan persentase
    last_values = df[df['id_tahun'] == last_year].iloc[0]
    changes = {
        'laki_laki': (predictions['laki_laki'] - last_values['laki_laki']) / last_values['laki_laki'] * 100,
        'perempuan': (predictions['perempuan'] - last_values['perempuan']) / last_values['perempuan'] * 100,
        'jumlah_penduduk': ((predictions['laki_laki'] + predictions['perempuan']) - last_values['jumlah_penduduk']) / last_values['jumlah_penduduk'] * 100
    }

    # ======= PREDICTION DISPLAY =======
    st.header("Prediksi 3 Tahun ke Depan")
    cols = st.columns(3)
    with cols[0]:
        st.metric(
            f"Prediksi Laki-laki {last_year+1}", 
            f"{predictions['laki_laki'][0]:,.0f}",
            delta=f"{changes['laki_laki'][0]:+.1f}%"
        )
        st.metric(
            f"Prediksi Laki-laki {last_year+2}", 
            f"{predictions['laki_laki'][1]:,.0f}",
            delta=f"{changes['laki_laki'][1]:+.1f}%"
        )
        st.metric(
            f"Prediksi Laki-laki {last_year+3}", 
            f"{predictions['laki_laki'][2]:,.0f}",
            delta=f"{changes['laki_laki'][2]:+.1f}%"
        )

    with cols[1]:
        st.metric(
            f"Prediksi Perempuan {last_year+1}",
            f"{predictions['perempuan'][0]:,.0f}",
            delta=f"{changes['perempuan'][0]:+.1f}%"
        )
        st.metric(
            f"Prediksi Perempuan {last_year+2}",
            f"{predictions['perempuan'][1]:,.0f}",
            delta=f"{changes['perempuan'][1]:+.1f}%"
        )
        st.metric(
            f"Prediksi Perempuan {last_year+3}",
            f"{predictions['perempuan'][2]:,.0f}",
            delta=f"{changes['perempuan'][2]:+.1f}%"
        )

    with cols[2]:
        st.metric(
            f"Total Penduduk {last_year+1}",
            f"{predictions['laki_laki'][0] + predictions['perempuan'][0]:,.0f}",
            delta=f"{changes['jumlah_penduduk'][0]:+.1f}%"
        )
        st.metric(
            f"Total Penduduk {last_year+2}",
            f"{predictions['laki_laki'][1] + predictions['perempuan'][1]:,.0f}",
            delta=f"{changes['jumlah_penduduk'][1]:+.1f}%"
        )
        st.metric(
            f"Total Penduduk {last_year+3}",
            f"{predictions['laki_laki'][2] + predictions['perempuan'][2]:,.0f}",
            delta=f"{changes['jumlah_penduduk'][2]:+.1f}%"
        )

    # ======= VISUALIZATION =======
    viz_df = df.tail(8).copy()
    viz_df['Type'] = 'Historical'

    # Membuat pred_df dengan panjang yang konsisten (3 tahun)
    pred_df = pd.DataFrame({
        'id_tahun': next_years.flatten(),
        'laki_laki': predictions['laki_laki'],
        'perempuan': predictions['perempuan'],
        'jumlah_penduduk': predictions['laki_laki'] + predictions['perempuan'],
        'Type': ['Predicted'] * 3
    })

    viz_df = pd.concat([viz_df, pred_df])

    # Visualisasi dengan Plotly
    fig_bar = go.Figure()

    # Data historis
    fig_bar.add_trace(go.Bar(
        x=viz_df[viz_df['Type']=='Historical']['id_tahun'],
        y=viz_df[viz_df['Type']=='Historical']['laki_laki'],
        name='Laki-laki (Historical)',
        marker_color='#3498db'
    ))

    fig_bar.add_trace(go.Bar(
        x=viz_df[viz_df['Type']=='Historical']['id_tahun'],
        y=viz_df[viz_df['Type']=='Historical']['perempuan'],
        name='Perempuan (Historical)',
        marker_color='#f39c12',
        base=viz_df[viz_df['Type']=='Historical']['laki_laki']
    ))

    # Data prediksi
    fig_bar.add_trace(go.Bar(
        x=pred_df['id_tahun'],
        y=pred_df['laki_laki'],
        name='Laki-laki (Predicted)',
        marker_color='#2980b9'
    ))

    fig_bar.add_trace(go.Bar(
        x=pred_df['id_tahun'],
        y=pred_df['perempuan'],
        name='Perempuan (Predicted)',
        marker_color='#d35400',
        base=pred_df['laki_laki']
    ))

    fig_bar.update_layout(
        barmode='stack',
        title='Komposisi Penduduk Berdasarkan Jenis Kelamin',
        xaxis_title='Tahun',
        yaxis_title='Jumlah Penduduk'
    )

    # Create line chart for trends
    fig_line = px.line(
        viz_df,
        x="id_tahun",
        y="jumlah_penduduk",
        color="Type",
        markers=True,
        title=f"Trend Line Jumlah Penduduk",
        labels={"id_tahun": "Tahun", "jumlah_penduduk": "Jumlah Penduduk"},
        color_discrete_map={"Historical": "#2ecc71", "Predicted": "#e74c3c"}
    )
    fig_line.update_layout(
        showlegend=True,
        xaxis_title="Tahun",
        yaxis_title="Jumlah Penduduk"
    )

    # Display charts
    st.plotly_chart(fig_bar, use_container_width=True)
    st.plotly_chart(fig_line, use_container_width=True)
    
    # ======= DETAIL TABLE =======
    st.header("Data Historis")

    # Define all possible columns we might want to display
    possible_columns = {
        "id_tahun": "Tahun",
        "laki_laki": "Laki-laki",
        "perempuan": "Perempuan",
        "jumlah_penduduk": "Total Penduduk"
    }

    # Check which columns actually exist in our DataFrame
    available_cols = {col: name for col, name in possible_columns.items() if col in df.columns}

    if not available_cols:
        st.error("No valid population data columns found in the DataFrame!")
        return

    # Calculate percentage changes only for columns that exist
    if "laki_laki" in df.columns:
        df["% Perubahan Laki_laki"] = df["laki_laki"].pct_change() * 100
        available_cols["% Perubahan Laki_laki"] = "% Δ Laki"

    if "perempuan" in df.columns:
        df["% Perubahan Perempuan"] = df["perempuan"].pct_change() * 100
        available_cols["% Perubahan Perempuan"] = "% Δ Perempuan"

    if "jumlah_penduduk" in df.columns:
        df["% Perubahan Jumlah Penduduk"] = df["jumlah_penduduk"].pct_change() * 100
        available_cols["% Perubahan Jumlah Penduduk"] = "% Δ Total"

    # Create the display DataFrame with only available columns
    final_df = df[list(available_cols.keys())].rename(columns=available_cols)

    # Convert all values to strings
    final_df_str = final_df.astype(str)

    # Apply formatting to string values
    for col in final_df_str.columns:
        if col in ["Laki-laki", "Perempuan", "Total Penduduk"]:
            final_df_str[col] = final_df_str[col].apply(lambda x: f"{float(x):,.0f}" if x.replace('.','',1).isdigit() else x)
        elif col in ["% Δ Laki-laki", "% Δ Perempuan", "% Δ Total"]:
            final_df_str[col] = final_df_str[col].apply(lambda x: f"{float(x):+.1f}%" if x.replace('.','',1).replace('-','',1).isdigit() else x)

    # Apply styling
    def color_negative_red(val):
        if isinstance(val, str) and val.startswith('-'):
            return 'color: #e74c3c'
        elif isinstance(val, str) and val[0].isdigit():
            return 'color: #ffffff'
        if isinstance(val, str) and val.startswith('+'):
            return 'color: #2ecc71'
        return ''

    styled_df = final_df_str.style.applymap(color_negative_red)

    # Display the table
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

    st.write("*% Δ Laki-laki : presentase perubahan jumlah laki-laki dari data sebelumnya")
    st.write("*% Δ Perempuan : presentase perubahan jumlah perempuan dari data sebelumnya")
    st.write("*% Δ Total : presentase perubahan jumlah penduduk (laki-laki dan perempuan) dari data sebelumnya")

    # ======= MODEL PERFORMANCE =======
    st.header("Model Prediksi Berdasarkan MAPE dan R²")

    perf_df = pd.DataFrame(metrics).T.reset_index()
    perf_df.columns = ['Kategori', 'MAPE (%)', 'R²']

    # Convert performance metrics to strings with formatting
    perf_df_str = perf_df.copy()
    perf_df_str['MAPE (%)'] = perf_df_str['MAPE (%)'].apply(lambda x: f"{x:,.1f}%")
    perf_df_str['R²'] = perf_df_str['R²'].apply(lambda x: f"{x:.3f}")

    st.dataframe(
        perf_df_str,
        use_container_width=True,
        hide_index=True
    )
    
    st.write("*MAPE (Mean Absolute Precentage Error) : Rata - rata presentase dibandingkan dengan nilai aslinya. " \
    "Semakin kecil MAPE semakin akurat model")
    st.write("*R-squared : Mengukur seberapa baik model menjelaskan variasi data. " \
    "Semakin mendekati angka 1 semakin baik model menjelaskan variasi data")

    st.markdown("---")
    st.caption("© 2025 - Yudith Nico Priambodo")


#     # # Grafik menggunakan Plotly
#     # fig = px.line(
#     #     df,
#     #     x="id_tahun",
#     #     y="jumlah_penduduk",
#     #     markers=True,
#     #     title="Grafik Pertumbuhan Populasi",
#     #     labels={"id_tahun": "Tahun", "jumlah_penduduk": "Populasi"}
#     # )
#     # st.plotly_chart(fig, use_container_width=True)

#     # # Prediksi untuk tahun depan
#     # st.markdown("### Prediksi Populasi Masa Depan")
#     # st.write(f"**2024:** {predict_population(2024, model)} jiwa")
#     # st.write(f"**2025:** {predict_population(2025, model)} jiwa")

#     # # Metrics tambahan
#     # st.markdown("### Evaluasi Model")
#     # st.write(f"**MAE:** {mae:.2f}")
#     # st.write(f"**MAPE:** {mape:.2f}%")
#     # st.write(f"**R-Squared:** {r_squared:.2f}")

#     # # Input tahun untuk prediksi manual
#     # year_input = st.number_input("Masukkan tahun untuk prediksi:", min_value=2024, max_value=2050, value=2024)
#     # st.write(f"**Prediksi Populasi {year_input}:** {predict_population(year_input, model)} jiwa")


# # import streamlit as st
# # import plotly.express as px
# # from model import fetch_data, train_svm_model, predict_population

# # def app():
# #     st.header("Dashboard Prediksi Populasi Kecamatan Sidareja")

# #     # Ambil data
# #     table_name = "penduduk_tahunan"
# #     feature_columns = ["id_tahun"]
# #     target_column = "jumlah_penduduk"
    
# #     # Train model
# #     model, mae, mape, r_squared = train_svm_model(table_name, feature_columns, target_column)
    
# #     # Ambil data tahunan
# #     data_tahunan = fetch_data(table_name=table_name, feature_columns=feature_columns, target_column=target_column)
    
# #     if data_tahunan.empty:
# #         st.error("Data tidak ditemukan. Pastikan database memiliki data yang sesuai.")
# #         return
    
# #     st.dataframe(data_tahunan)
# #     df = data_tahunan
    
# #     # Grafik pertumbuhan populasi
# #     st.subheader("📈 Grafik Pertumbuhan Populasi")
# #     fig = px.line(
# #         df,
# #         x="id_tahun",
# #         y="jumlah_penduduk",
# #         markers=True,
# #         title="Grafik Pertumbuhan Populasi",
# #         labels={"id_tahun": "Tahun", "jumlah_penduduk": "Populasi"}
# #     )
# #     st.plotly_chart(fig, use_container_width=True)
    
# #     # Prediksi populasi untuk beberapa tahun ke depan
# #     st.subheader("🔮 Prediksi Populasi Masa Depan")
# #     tahun_prediksi = [2024, 2025, 2030]
# #     hasil_prediksi = {tahun: predict_population(tahun, model) for tahun in tahun_prediksi}
    
# #     for tahun, prediksi in hasil_prediksi.items():
# #         st.write(f"**{tahun}:** {prediksi:,.0f} jiwa")
    
#     # # Evaluasi model
#     # st.subheader("📊 Evaluasi Model")
#     # col1, col2, col3 = st.columns(3)
#     # col1.metric("MAE", f"{mae:.2f}")
#     # col2.metric("MAPE", f"{mape:.2f}%")
#     # col3.metric("R-Squared", f"{r_squared:.2f}")
    
#     # # Input prediksi manual
#     # st.subheader("🔢 Prediksi Populasi Berdasarkan Input Tahun")
#     # tahun_input = st.number_input("Masukkan tahun untuk prediksi:", min_value=2024, max_value=2050, value=2024)
#     # hasil_manual = predict_population(tahun_input, model)
#     # st.success(f"Prediksi Populasi {tahun_input}: {hasil_manual:,.0f} jiwa")
    
# # if __name__ == "__main__":
# #     app()
