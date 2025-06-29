import streamlit as st
import pandas as pd
from supabase import create_client, Client
from model import fetch_data
import os
from dotenv import load_dotenv

load_dotenv()

# Koneksi ke Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv('SUPABASE_KEY')  # Menggunakan environment variable untuk keamanan
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fungsi untuk mengecek apakah tahun sudah ada di tabel keluarga
def check_year_exists(id_tahun):
    response = supabase.table("keluarga").select("id_tahun").eq("id_tahun", id_tahun).execute()
    return len(response.data) > 0

# Fungsi untuk menambahkan tahun jika belum ada di tabel tahun
def add_year_if_not_exists(id_tahun):
    response = supabase.table("tahun").select("id_tahun").eq("id_tahun", id_tahun).execute()
    if len(response.data) == 0:  # Jika tahun belum ada, tambahkan
        supabase.table("tahun").insert({"id_tahun": id_tahun, "tahun": id_tahun}).execute()

# Fungsi untuk menambahkan data kepala keluarga
def add_population_data(id_tahun, jumlah_kepala_keluarga, pria, wanita):
    try:
        response = supabase.table("keluarga").insert({
            "id_tahun": int(id_tahun),  # Konversi ke integer
            "jumlah_kepala_keluarga": int(jumlah_kepala_keluarga),  # Konversi ke integer
            "pria": int(pria),  # Konversi ke integer
            "wanita": int(wanita)  # Konversi ke integer
        }).execute()
        
        # Cek apakah data berhasil ditambahkan
        if response.data:  # Jika ada data yang dikembalikan, berarti sukses
            return True, "Data berhasil ditambahkan!"
        else:
            return False, "Gagal menambahkan data: Tidak ada data yang dikembalikan."
    except Exception as e:
        return False, f"Gagal menambahkan data: {str(e)}"

# Fungsi untuk mengambil data kepala keluarga
def get_population_data():
    keluarga = fetch_data(
        table_name="keluarga",
        feature_columns=["id_tahun"],
        target_columns=["jumlah_kepala_keluarga", "pria", "wanita"]
    )
    df = pd.DataFrame(keluarga)
    df = df.reset_index(drop=True)
    # Mengganti NaN dan inf dengan nilai default
    df = df.replace([float("inf"), float("-inf")], 0).fillna(0)
    return df

# Fungsi untuk menghapus data
def delete_population_data(id_tahun):
    try:
        # Konversi id_tahun ke integer
        id_tahun = int(id_tahun)
        supabase.table("keluarga").delete().eq("id_tahun", id_tahun).execute()
        st.success(f"Data untuk tahun {id_tahun} berhasil dihapus!")
    except Exception as e:
        st.error(f"Gagal menghapus data: {str(e)}")

# Fungsi untuk memperbarui data
def update_population_data(id_tahun, jumlah_kepala_keluarga, pria, wanita):
    try:
        supabase.table("keluarga").update({
            "jumlah_kepala_keluarga": int(jumlah_kepala_keluarga),  # Konversi ke integer
            "pria": int(pria),  # Konversi ke integer
            "wanita": int(wanita)  # Konversi ke integer
        }).eq("id_tahun", int(id_tahun)).execute()  # Konversi ke integer
        st.success(f"Data untuk tahun {id_tahun} berhasil diperbarui!")
    except Exception as e:
        st.error(f"Gagal memperbarui data: {str(e)}")

# Fungsi utama aplikasi
def app():
    st.header("Data Jumlah Kepala Keluarga")
    st.title("Manajemen Data Kepala Keluarga")

    # Inisialisasi session state untuk form reset
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0

    # Ambil data kepala keluarga
    df = get_population_data()

    # Tampilkan tabel dengan tombol hapus per baris
    col1, col2, col3, col4, col5 = st.columns([2, 3, 3, 3, 2])
    with col1:
        st.write("Tahun")
    with col2:
        st.write("Pria")
    with col3:
        st.write("Wanita")
    with col4:
        st.write("Total")
    with col5:
        st.write("Hapus")

    # Dialog untuk konfirmasi update
    @st.dialog("Konfirmasi Perubahan")
    def confirm_update(id_tahun, pria, wanita):
        total = pria + wanita
        st.write(f"Apakah Anda yakin ingin memperbarui data untuk tahun {id_tahun}?")
        if st.button("Ya, Perbarui"):
            update_population_data(id_tahun, total, pria, wanita)
            st.rerun()

    # Dialog untuk konfirmasi hapus
    @st.dialog("Konfirmasi Penghapusan")
    def confirm_delete(id_tahun):
        st.write(f"Apakah Anda yakin ingin menghapus data untuk tahun {id_tahun}?")
        if st.button("Ya, Hapus"):
            delete_population_data(id_tahun)
            st.rerun()

    # Dialog untuk konfirmasi tambah
    @st.dialog("Konfirmasi Penambahan")
    def confirm_tambah(tahun_baru, pria, wanita):
        total = pria + wanita
        st.write(f"Apakah Anda yakin ingin menambahkan data untuk tahun {tahun_baru}?")
        if st.button("Ya, Tambah"):
            success, message = add_population_data(tahun_baru, total, pria, wanita)
            if success:
                st.success(message)
                # Reset form setelah berhasil menambah data
                st.session_state.form_key += 1
            else:
                st.error(message)
            st.rerun()

    # Tampilkan data dalam tabel
    for index, row in df.iterrows():
        with col1:
            tahun = st.number_input("", value=int(row["id_tahun"]), key=f"tahun{index}", label_visibility='collapsed', step=1, format="%d")
        with col2:
            pria = st.number_input("", value=int(row["pria"]), key=f"Pria_{index}", label_visibility='collapsed', step=1, format="%d")
        with col3:
            wanita = st.number_input("", value=int(row["wanita"]), key=f"Wanita_{index}", label_visibility='collapsed', step=1, format="%d")
        with col4:
            # Hitung total otomatis dan tampilkan
            total_otomatis = pria + wanita
            total_display = st.number_input("", value=total_otomatis, key=f"total_{index}", label_visibility='collapsed', step=1, format="%d", disabled=True)
        with col5:
            if st.button("Hapus", key=f"hapus_{index}"):
                confirm_delete(int(row["id_tahun"]))  # Konversi ke integer

        # Jika ada perubahan data, tampilkan dialog konfirmasi update
        if (pria != row["pria"] or wanita != row["wanita"]):
            confirm_update(row["id_tahun"], pria, wanita)

    # Form untuk menambahkan data baru
    st.subheader("Tambah Data Baru")
    with st.form(f"add_form_{st.session_state.form_key}"):
        col1, col2 = st.columns(2)
        with col1:
            tahun_baru = st.number_input("Masukkan tahun", min_value=2024, max_value=3000, step=1, format="%d", key=f"tahun_input_{st.session_state.form_key}")
        with col2:
            st.write("")  # Spacer
        
        col3, col4 = st.columns(2)
        with col3:
            pria = st.number_input("Jumlah Kepala Keluarga Pria", min_value=0, step=1, key=f"pria_input_{st.session_state.form_key}")
        with col4:
            wanita = st.number_input("Jumlah Kepala Keluarga Wanita", min_value=0, step=1, key=f"wanita_input_{st.session_state.form_key}")
        
        # Hitung total otomatis
        jumlah_kepala_keluarga = pria + wanita
        st.write(f"**Total Jumlah Kepala Keluarga:** {jumlah_kepala_keluarga}")
        
        if st.form_submit_button("Tambah Data"):
            if jumlah_kepala_keluarga == 0:
                st.error("Jumlah kepala keluarga tidak boleh nol!")
            elif check_year_exists(tahun_baru):
                st.error(f"Data kepala keluarga untuk tahun {tahun_baru} sudah ada!")
            else:
                add_year_if_not_exists(tahun_baru)
                confirm_tambah(tahun_baru, pria, wanita)