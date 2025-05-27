import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def app():
    st.header("Piramida Penduduk")
    # Judul aplikasi
    st.title("Piramida Penduduk Berdasarkan Jenis Kelamin")

    # Upload file Excel
    uploaded_file = st.file_uploader("Unggah file Excel", type="xlsx")

    if uploaded_file:
        # Membaca data dari sheet "piramida"
        data = pd.read_excel(uploaded_file, sheet_name="Piramida")
        
        # Pastikan kolom sesuai format
        if {'Usia', 'Laki-laki', 'Perempuan'}.issubset(data.columns):
            # Membuat piramida
            fig = go.Figure()
            data = data.sort_values(by="Usia", ascending=False)
             # Filter baris Total
            non_total_data = data[data["Usia"] != "Total"].copy()  # Baris selain "Total"
            total_data = data[data["Usia"] == "Total"].copy()  # Baris "Total"
        
            # Perbesar data untuk baris selain "Total"
            non_total_data["Laki-laki"] *= 10
            non_total_data["Perempuan"] *= 10

            # Menggabungkan kembali data
            processed_data = pd.concat([non_total_data, total_data])
    
            # Bar untuk laki-laki (negatif agar arah ke kiri)
            fig.add_trace(go.Bar(
                y=processed_data["Usia"], 
                x=-processed_data["Laki-laki"], 
                name="Laki-laki", 
                orientation='h',
                marker_color='blue'
            ))

            # Bar untuk perempuan
            fig.add_trace(go.Bar(
                y=processed_data["Usia"], 
                x=processed_data["Perempuan"], 
                name="Perempuan", 
                orientation='h',
                marker_color='pink'
            ))

            # Layout piramida
            fig.update_layout(
                title="Piramida Penduduk Berdasarkan Jenis Kelamin",
                barmode='overlay',
                xaxis=dict(title="Jumlah Penduduk", tickvals=[-500, -250, 0, 250, 500],
                        ticktext=["500", "250", "0", "250", "500"]),
                yaxis=dict(title="Kelompok Usia"),
                legend=dict(title="Jenis Kelamin"),
                template="plotly_white",
            )

            # Tampilkan grafik di Streamlit
            st.plotly_chart(fig)

        else:
            st.error("Sheet 'piramida' harus memiliki kolom 'Usia', 'Laki-laki', dan 'Perempuan'.")
