import streamlit as st
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Konfigurasi Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def confirm_user(user_id):
    """Update status user menjadi confirmed."""
    try:
        supabase.table("users").update({"is_confirmed": True}).eq("id_admin", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Gagal mengkonfirmasi user: {e}")
        return False

def get_unconfirmed_users():
    """Mengambil daftar user yang belum dikonfirmasi."""
    try:
        response = supabase.table("users").select("id_admin, nama, username, role, is_confirmed").eq("is_confirmed", False).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Gagal mengambil data user: {e}")
        return []

def app():
    st.header("Konfirmasi Akun User Baru")
    st.info("Halaman ini hanya dapat diakses oleh Superadmin.")

    unconfirmed_users = get_unconfirmed_users()

    if not unconfirmed_users:
        st.success("Tidak ada akun baru yang perlu dikonfirmasi saat ini.")
    else:
        st.write("Berikut adalah daftar akun yang menunggu konfirmasi:")
        
        for user in unconfirmed_users:
            col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
            with col1:
                st.write(user['id_admin'])
            with col2:
                st.write(user['nama'])
            with col3:
                st.write(user['username'])
            with col4:
                if st.button(f"Konfirmasi {user['username']}", key=f"confirm_{user['id_admin']}"):
                    if confirm_user(user['id_admin']):
                        st.success(f"Akun {user['username']} berhasil dikonfirmasi!")
                        st.rerun()

    st.markdown("---")
    st.write("Setelah dikonfirmasi, user dapat login ke sistem.") 