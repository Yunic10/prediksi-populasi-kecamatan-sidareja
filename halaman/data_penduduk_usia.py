import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Constants
AGE_GROUPS = ['0-14', '15-60', '60+']
ITEMS_PER_PAGE = 10

# Fungsi untuk mendapatkan data dengan pagination
def get_age_population_data(page=1, items_per_page=ITEMS_PER_PAGE):
    offset = (page - 1) * items_per_page
    count_response = supabase.table("penduduk_usia").select("count", count="exact").execute()
    total_count = count_response.count
    
    response = supabase.table("penduduk_usia").select("*").order("id_tahun").range(offset, offset + items_per_page - 1).execute()
    df = pd.DataFrame(response.data)
    return df.replace([float("inf"), float("-inf")], 0).fillna(0), total_count

# Fungsi untuk mendapatkan semua data tanpa pagination
def get_all_age_population_data():
    response = supabase.table("penduduk_usia").select("*").order("id_tahun").execute()
    df = pd.DataFrame(response.data)
    return df.replace([float("inf"), float("-inf")], 0).fillna(0)

# CRUD Functions
def check_year_and_category_exists(id_tahun, kategori_usia):
    response = supabase.table("penduduk_usia").select("id_tahun, kategori_usia")\
                 .eq("id_tahun", id_tahun)\
                 .eq("kategori_usia", kategori_usia)\
                 .execute()
    return len(response.data) > 0

def check_year_exists(id_tahun):
    response = supabase.table("penduduk_usia").select("id_tahun")\
                 .eq("id_tahun", id_tahun)\
                 .execute()
    return len(response.data) > 0

def add_age_population_data(id_tahun, kategori_usia, laki_laki, perempuan):
    try:
        total = laki_laki + perempuan
        response = supabase.table("penduduk_usia").insert({
            "id_tahun": int(id_tahun),
            "kategori_usia": kategori_usia,
            "laki_laki": int(laki_laki),
            "perempuan": int(perempuan),
            "total": int(total)
        }).execute()
        return bool(response.data), "Data berhasil ditambahkan!" if response.data else "Gagal menambahkan data"
    except Exception as e:
        return False, f"Gagal menambahkan data: {str(e)}"

def add_all_age_population_data(id_tahun, data_0_14, data_15_60, data_60_plus):
    """
    Menambahkan data untuk semua kategori usia sekaligus
    data_0_14: dict dengan keys 'laki_laki', 'perempuan'
    data_15_60: dict dengan keys 'laki_laki', 'perempuan'  
    data_60_plus: dict dengan keys 'laki_laki', 'perempuan'
    """
    try:
        # Tambahkan data untuk kategori 0-14
        success1, msg1 = add_age_population_data(id_tahun, "0-14", data_0_14['laki_laki'], data_0_14['perempuan'])
        
        # Tambahkan data untuk kategori 15-60
        success2, msg2 = add_age_population_data(id_tahun, "15-60", data_15_60['laki_laki'], data_15_60['perempuan'])
        
        # Tambahkan data untuk kategori 60+
        success3, msg3 = add_age_population_data(id_tahun, "60+", data_60_plus['laki_laki'], data_60_plus['perempuan'])
        
        if success1 and success2 and success3:
            return True, "Data untuk semua kategori usia berhasil ditambahkan!"
        else:
            return False, f"Gagal menambahkan data: {msg1}, {msg2}, {msg3}"
    except Exception as e:
        return False, f"Gagal menambahkan data: {str(e)}"

def get_age_population_data(page=1):
    offset = (page - 1) * ITEMS_PER_PAGE
    count_response = supabase.table("penduduk_usia").select("count", count="exact").execute()
    total_count = count_response.count
    response = supabase.table("penduduk_usia").select("*").order("id_tahun").range(offset, offset + ITEMS_PER_PAGE - 1).execute()
    df = pd.DataFrame(response.data)
    return df.replace([float("inf"), float("-inf")], 0).fillna(0), total_count

def delete_age_population_data(id_tahun, kategori_usia):
    try:
        supabase.table("penduduk_usia").delete().eq("id_tahun", int(id_tahun)).eq("kategori_usia", kategori_usia).execute()
        return True, f"Data tahun {id_tahun} kelompok {kategori_usia} berhasil dihapus!"
    except Exception as e:
        return False, f"Gagal menghapus data: {str(e)}"

def update_age_population_data(id_tahun, kategori_usia, laki_laki, perempuan):
    try:
        total = laki_laki + perempuan
        supabase.table("penduduk_usia").update({
            "laki_laki": int(laki_laki),
            "perempuan": int(perempuan),
            "total": int(total)
        }).eq("id_tahun", int(id_tahun)).eq("kategori_usia", kategori_usia).execute()
        return True, f"Data tahun {id_tahun} kelompok {kategori_usia} berhasil diperbarui!"
    except Exception as e:
        return False, f"Gagal memperbarui data: {str(e)}"


# Confirmation Dialogs (menggunakan model modal dialog seperti contoh)
@st.dialog("Konfirmasi Perubahan")
def confirm_update(id_tahun, kategori_usia, laki_laki, perempuan):
    st.write(f"Apakah Anda yakin ingin memperbarui data untuk tahun {id_tahun} kelompok {kategori_usia}?")
    if st.button("Ya, Perbarui"):
        success, message = update_age_population_data(id_tahun, kategori_usia, laki_laki, perempuan)
        if success:
            st.success(message)
        else:
            st.error(message)
        st.rerun()

@st.dialog("Konfirmasi Penghapusan")
def confirm_delete(id_tahun, kategori_usia):
    st.write(f"Apakah Anda yakin ingin menghapus data untuk tahun {id_tahun} kelompok {kategori_usia}?")
    if st.button("Ya, Hapus"):
        success, message = delete_age_population_data(id_tahun, kategori_usia)
        if success:
            st.success(message)
            st.session_state.page = 1
        else:
            st.error(message)
        st.rerun()

@st.dialog("Konfirmasi Penambahan")
def confirm_tambah(new_year, age_group, males, females):
    st.write(f"Apakah Anda yakin ingin menambahkan data untuk tahun {new_year} kelompok {age_group}?")
    if st.button("Ya, Tambah"):
        success, message = add_age_population_data(new_year, age_group, males, females)
        if success:
            st.success(message)
            st.session_state.page = 1
        else:
            st.error(message)
        st.rerun()

@st.dialog("Konfirmasi Penambahan Semua Kategori")
def confirm_tambah_semua(new_year, data_0_14, data_15_60, data_60_plus):
    st.write(f"Apakah Anda yakin ingin menambahkan data untuk tahun {new_year} untuk semua kategori usia?")
    st.write("**Data yang akan ditambahkan:**")
    st.write(f"- 0-14: Laki-laki {data_0_14['laki_laki']}, Perempuan {data_0_14['perempuan']}")
    st.write(f"- 15-60: Laki-laki {data_15_60['laki_laki']}, Perempuan {data_15_60['perempuan']}")
    st.write(f"- 60+: Laki-laki {data_60_plus['laki_laki']}, Perempuan {data_60_plus['perempuan']}")
    
    if st.button("Ya, Tambah Semua"):
        success, message = add_all_age_population_data(new_year, data_0_14, data_15_60, data_60_plus)
        if success:
            st.success(message)
            st.session_state.page = 1
            # Reset form setelah berhasil menambah data
            st.session_state.form_key += 1
        else:
            st.error(message)
        st.rerun()

# Main App
def app():
    st.header("Data Penduduk Berdasarkan Kelompok Umur")
    
    # Inisialisasi session state untuk form reset
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0
    
    # Tambahkan checkbox untuk tampilkan semua data
    show_all = st.checkbox("Tampilkan Semua Data", value=False)
    
    if show_all:
        # Mode tampilkan semua data
        df = get_all_age_population_data()
        st.info(f"Menampilkan semua {len(df)} data")
    else:
        # Mode pagination
        if 'page' not in st.session_state:
            st.session_state.page = 1
        
        df, total_count = get_age_population_data(st.session_state.page)
        total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("Sebelumnya") and st.session_state.page > 1:
                st.session_state.page -= 1
                st.rerun()
        with col2:
            st.write(f"Halaman {st.session_state.page} dari {total_pages} | Total Data: {total_count}")
        with col3:
            if st.button("Berikutnya") and st.session_state.page < total_pages:
                st.session_state.page += 1
                st.rerun()

    # Tampilkan tabel dengan tombol hapus per baris
    col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 2, 2, 2, 2])
    with col1:
        st.write("Tahun")
    with col2:
        st.write("Kategori Usia")
    with col3:
        st.write("Laki-laki")
    with col4:
        st.write("Perempuan")
    with col5:
        st.write("Total")
    with col6:
        st.write("Hapus")

    # Tampilkan data dalam tabel
    for index, row in df.iterrows():
        with col1:
            tahun = st.number_input("", value=int(row["id_tahun"]), key=f"tahun{index}", label_visibility='collapsed', step=1, format="%d")
        with col2:
            kategori_usia = st.text_input("", value=row["kategori_usia"], key=f"kategori_{index}", label_visibility='collapsed', disabled=True)
        with col3:
            laki_laki = st.number_input("", value=int(row["laki_laki"]), key=f"laki_{index}", label_visibility='collapsed', step=1, format="%d")
        with col4:
            perempuan = st.number_input("", value=int(row["perempuan"]), key=f"perempuan_{index}", label_visibility='collapsed', step=1, format="%d")
        with col5:
            total = st.number_input("", value=int(row["total"]), key=f"total_{index}", label_visibility='collapsed', step=1, format="%d", disabled=True)
        with col6:
            if st.button("Hapus", key=f"hapus_{index}"):
                confirm_delete(int(row["id_tahun"]), row["kategori_usia"])

        # Jika ada perubahan data (hanya laki-laki dan perempuan, bukan kategori usia)
        if (laki_laki != row["laki_laki"] or perempuan != row["perempuan"]):
            confirm_update(row["id_tahun"], row["kategori_usia"], laki_laki, perempuan)
    
    # Add new data form - Form untuk mengisi 3 kategori usia sekaligus
    st.subheader("Tambah Data Baru (Semua Kategori Usia)")
    with st.form(f"add_form_{st.session_state.form_key}"):
        # Input tahun
        new_year = st.number_input("Tahun", min_value=2000, max_value=2100, step=1, key=f"year_input_{st.session_state.form_key}")
        
        # Kategori 0-14
        st.write("**Kategori Usia 0-14**")
        col1, col2 = st.columns(2)
        with col1:
            males_0_14 = st.number_input("Laki-laki (0-14)", min_value=0, step=1, key=f"males_0_14_{st.session_state.form_key}")
        with col2:
            females_0_14 = st.number_input("Perempuan (0-14)", min_value=0, step=1, key=f"females_0_14_{st.session_state.form_key}")
        
        total_0_14 = males_0_14 + females_0_14
        st.write(f"Total 0-14: {total_0_14}")
        
        # Kategori 15-60
        st.write("**Kategori Usia 15-60**")
        col3, col4 = st.columns(2)
        with col3:
            males_15_60 = st.number_input("Laki-laki (15-60)", min_value=0, step=1, key=f"males_15_60_{st.session_state.form_key}")
        with col4:
            females_15_60 = st.number_input("Perempuan (15-60)", min_value=0, step=1, key=f"females_15_60_{st.session_state.form_key}")
        
        total_15_60 = males_15_60 + females_15_60
        st.write(f"Total 15-60: {total_15_60}")
        
        # Kategori 60+
        st.write("**Kategori Usia 60+**")
        col5, col6 = st.columns(2)
        with col5:
            males_60_plus = st.number_input("Laki-laki (60+)", min_value=0, step=1, key=f"males_60_plus_{st.session_state.form_key}")
        with col6:
            females_60_plus = st.number_input("Perempuan (60+)", min_value=0, step=1, key=f"females_60_plus_{st.session_state.form_key}")
        
        total_60_plus = males_60_plus + females_60_plus
        st.write(f"Total 60+: {total_60_plus}")
        
        # Total keseluruhan
        total_all = total_0_14 + total_15_60 + total_60_plus
        st.write(f"**Total Keseluruhan: {total_all}**")
        
        if st.form_submit_button("Tambah Data Semua Kategori"):
            # Validasi: semua input laki-laki dan perempuan tidak boleh nol
            if males_0_14 == 0:
                st.error("Jumlah laki-laki kategori 0-14 tidak boleh nol!")
            elif females_0_14 == 0:
                st.error("Jumlah perempuan kategori 0-14 tidak boleh nol!")
            elif males_15_60 == 0:
                st.error("Jumlah laki-laki kategori 15-60 tidak boleh nol!")
            elif females_15_60 == 0:
                st.error("Jumlah perempuan kategori 15-60 tidak boleh nol!")
            elif males_60_plus == 0:
                st.error("Jumlah laki-laki kategori 60+ tidak boleh nol!")
            elif females_60_plus == 0:
                st.error("Jumlah perempuan kategori 60+ tidak boleh nol!")
            elif total_all == 0:
                st.error("Total penduduk tidak boleh nol!")
            elif check_year_exists(new_year):
                st.error(f"Data untuk tahun {new_year} sudah ada!")
            else:
                # Siapkan data untuk setiap kategori
                data_0_14 = {'laki_laki': males_0_14, 'perempuan': females_0_14}
                data_15_60 = {'laki_laki': males_15_60, 'perempuan': females_15_60}
                data_60_plus = {'laki_laki': males_60_plus, 'perempuan': females_60_plus}
                
                confirm_tambah_semua(new_year, data_0_14, data_15_60, data_60_plus)

# if __name__ == "__main__":
#     app()