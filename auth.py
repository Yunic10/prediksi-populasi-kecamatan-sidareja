import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Inisialisasi Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Inisialisasi cookie manager
cookies = EncryptedCookieManager(password="my_very_strong_key_123!")  # Ganti dengan kunci yang kuat

if not cookies.ready():
    st.stop()  # Tunggu hingga cookies siap

def get_user_credentials(username):
    """Mengambil data user dari tabel 'users' di Supabase"""
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def login(username, password):
    """Fungsi login dengan verifikasi ke database"""
    user = get_user_credentials(username)
    
    if user and user["password"] == password:  # Perbandingan password langsung (tidak aman untuk production)
        cookies["authenticated"] = "true"
        cookies["username"] = username
        cookies.save()
        st.rerun()
        return True
    return False

def logout():
    """Fungsi logout untuk menghapus session"""
    cookies["authenticated"] = "false"
    cookies["username"] = ""
    cookies.save()
    st.rerun()

def is_authenticated():
    """Cek apakah user sudah login"""
    return cookies.get("authenticated") == "true"

# Tampilan Streamlit
def auth_page():
    st.title("Login System")
    
    if is_authenticated():
        st.success(f"Selamat datang, {cookies.get('username')}!")
        if st.button("Logout"):
            logout()
        
        # Konten setelah login berhasil
        st.write("## Konten Terproteksi")
        st.write("Anda sekarang dapat mengakses konten ini karena sudah login.")
        
    else:
        with st.form("login_form"):
            st.write("## Silakan Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login"):
                if login(username, password):
                    st.success("Login berhasil!")
                else:
                    st.error("Username atau password salah")

# Contoh data dummy (untuk development saja)
def create_dummy_user():
    try:
        # Cek apakah user test sudah ada
        existing = supabase.table("users").select("*").eq("username", "admin").execute()
        if not existing.data:
            supabase.table("users").insert({
                "username": "admin",
                "password": "admin123"  # ganti di production!
            }).execute()
    except Exception as e:
        st.warning(f"Gagal membuat dummy user: {str(e)}")
