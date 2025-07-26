import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Konfigurasi Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_data(name, age):
    data = {"name": name, "age": age}
    supabase.table("users").insert(data).execute()

def read_data():
    users = supabase.table("users").select("id, name, age").execute()
    penduduk_tahunan =  supabase.table("penduduk_tahunan").select("id_tahun,jumlah_penduduk,laki_laki,perempuan").execute()
    return {
        "users": users.data,
        "penduduk_tahunan":penduduk_tahunan.data
    }

def update_data(user_id, name, age):
    supabase.table("users").update({"name": name, "age": age}).eq("id", user_id).execute()

def delete_data(user_id):
    supabase.table("users").delete().eq("id", user_id).execute()

def confirm_user(user_id):
    supabase.table("users").update({"is_confirmed": True}).eq("id_admin", user_id).execute()

def get_unconfirmed_users():
    response = supabase.table("users").select("id_admin, nama, username, role, is_confirmed").eq("is_confirmed", False).execute()
    return response.data if response.data else []

st.title("CRUD Streamlit dengan Supabase")

# Form untuk menambah data
with st.form("create_form"):
    name = st.text_input("Nama")
    age = st.number_input("Usia", min_value=0, step=1)
    submit = st.form_submit_button("Tambah")
    if submit:
        create_data(name, age)
        st.success("Data berhasil ditambahkan!")

# Menampilkan data
data = read_data()
if data["users"]:
    df_users = pd.DataFrame(data["users"])  # Konversi list of dict ke DataFrame
    df_users.set_index('id', inplace=True)  # Gunakan 'id' sebagai indeks
    st.dataframe(df_users, use_container_width=True)
if data["penduduk_tahunan"]:
    df_penduduk_tahunan = pd.DataFrame(data["penduduk_tahunan"])
    df_penduduk_tahunan = df_penduduk_tahunan.astype({"id_tahun":"string"})
    df_penduduk_tahunan.set_index('id_tahun', inplace=True)
    st.dataframe(df_penduduk_tahunan, use_container_width=True)
else:
    st.write("Belum ada data.")

# Tambahkan tampilan untuk superadmin
if "superadmin" in [u.get("role", "") for u in data["users"]]:
    st.subheader("Konfirmasi Akun User Baru (Hanya Superadmin)")
    unconfirmed = get_unconfirmed_users()
    if unconfirmed:
        for user in unconfirmed:
            st.write(f"ID: {user['id_admin']}, Nama: {user['nama']}, Username: {user['username']}, Role: {user['role']}")
            if st.button(f"Konfirmasi {user['username']}", key=f"confirm_{user['id_admin']}"):
                confirm_user(user['id_admin'])
                st.success(f"Akun {user['username']} berhasil dikonfirmasi!")
                st.rerun()
    else:
        st.info("Tidak ada akun yang perlu dikonfirmasi.")

# Form untuk update
user_id = st.number_input("Masukkan ID untuk update:", min_value=1, step=1)
new_name = st.text_input("Nama Baru")
new_age = st.number_input("Usia Baru", min_value=0, step=1)
if st.button("Update Data"):
    update_data(user_id, new_name, new_age)
    st.success("Data berhasil diperbarui!")

# Hapus data
user_id_delete = st.number_input("Masukkan ID untuk hapus:", min_value=1, step=1)
if st.button("Hapus Data"):
    delete_data(user_id_delete)
    st.success("Data berhasil dihapus!")
