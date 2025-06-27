import streamlit as st
import pandas as pd
import os

@st.cache_data
def load_csv_data(filename):
    """Load data CSV dengan caching"""
    file_path = os.path.join('data', filename)
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        st.error(f"File {filename} tidak ditemukan")
        return pd.DataFrame()

@st.cache_data
def load_excel_data(filename):
    """Load data Excel dengan caching"""
    file_path = os.path.join('data', filename)
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    else:
        st.error(f"File {filename} tidak ditemukan")
        return pd.DataFrame()

@st.cache_data
def get_data_files():
    """Dapatkan daftar file data yang tersedia"""
    data_dir = 'data'
    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        return [f for f in files if f.endswith(('.csv', '.xlsx'))]
    return []

@st.cache_data
def load_penduduk_usia_data():
    """Load data penduduk berdasarkan usia"""
    return load_csv_data('Jumlah Penduduk Menurut Kelompok Umur.csv')

@st.cache_data
def load_kepala_keluarga_data():
    """Load data kepala keluarga"""
    return load_csv_data('kepala_keluarga.csv')

@st.cache_data
def load_migrasi_data():
    """Load data migrasi"""
    return load_csv_data('migrasi.csv')

@st.cache_data
def load_status_perkawinan_data():
    """Load data status perkawinan"""
    return load_csv_data('status_kawin.csv')

@st.cache_data
def load_putus_sekolah_data():
    """Load data putus sekolah"""
    return load_csv_data('tidak_bersekolah.csv')

@st.cache_data
def load_penduduk_desa_data():
    """Load data penduduk per desa"""
    return load_csv_data('penduduk_perdesa.csv')

@st.cache_data
def load_fasilitas_data():
    """Load data fasilitas"""
    return load_csv_data('fasilitas.csv')

@st.cache_data
def load_geografi_data():
    """Load data geografi"""
    return load_csv_data('geografi.csv')

@st.cache_data
def load_main_data():
    """Load data utama"""
    return load_csv_data('Data.csv')

@st.cache_data
def load_excel_main_data():
    """Load data utama dari Excel"""
    return load_excel_data('Data.xlsx') 