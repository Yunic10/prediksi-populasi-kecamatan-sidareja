import streamlit as st
import yaml
import bcrypt
import json
import os
import time
from yaml.loader import SafeLoader
from dotenv import load_dotenv
from supabase import create_client, Client
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_session_duration():
    """Durasi session login dalam jam (default: 24 jam)"""
    return 24

@st.cache_data
def load_config():
    """Load konfigurasi dari file YAML dengan caching"""
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config

def verify_password(plain_password, hashed_password):
    """Fungsi untuk memverifikasi password"""
    if hashed_password is None:
        return False
    # check_password_hash dari werkzeug otomatis mendeteksi metode (scrypt, pbkdf2, dll)
    return check_password_hash(hashed_password, plain_password)

@st.cache_data
def get_session_file():
    """Dapatkan path file session"""
    return "session_data.json"

def save_session_data(username, name, expiry_hours=24):
    """Simpan data session ke file"""
    session_file = get_session_file()
    session_data = {
        "username": username,
        "name": name,
        "login_time": time.time(),
        "expiry_time": time.time() + (expiry_hours * 3600)
    }
    try:
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan session: {e}")
        return False

def load_session_data():
    """Load data session dari file"""
    session_file = get_session_file()
    try:
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Cek apakah session masih valid
            if time.time() < session_data.get("expiry_time", 0):
                return session_data
            else:
                # Session expired, hapus file
                os.remove(session_file)
        return None
    except Exception as e:
        st.error(f"Gagal load session: {e}")
        return None

def clear_session_data():
    """Hapus data session"""
    session_file = get_session_file()
    try:
        if os.path.exists(session_file):
            os.remove(session_file)
        return True
    except Exception as e:
        st.error(f"Gagal hapus session: {e}")
        return False

def init_session_state():
    """Inisialisasi session state untuk autentikasi"""
    if "authentication_status" not in st.session_state:
        # Cek apakah ada session yang tersimpan
        session_data = load_session_data()
        if session_data:
            st.session_state["authentication_status"] = True
            st.session_state["username"] = session_data.get("username")
            st.session_state["name"] = session_data.get("name")
        else:
            st.session_state["authentication_status"] = False
            st.session_state["username"] = None
            st.session_state["name"] = None

def save_login_state(username, name, role):
    """Menyimpan status login ke session state"""
    session_file = get_session_file()
    login_time = time.time()
    expiry_time = login_time + (get_session_duration() * 3600)  # Durasi dalam detik
    
    session_data = {
        "username": username,
        "name": name,
        "role": role,
        "login_time": login_time,
        "expiry_time": expiry_time
    }
    
    with open(session_file, 'w') as f:
        json.dump(session_data, f)
        
    # Set session state Streamlit
    st.session_state['authentication_status'] = True # Pastikan ini di-set
    st.session_state['logged_in'] = True
    st.session_state['username'] = username
    st.session_state['name'] = name
    st.session_state['role'] = role

def clear_login_state():
    """Hapus status login dari session state dan file"""
    st.session_state["authentication_status"] = False
    st.session_state["username"] = None
    st.session_state["name"] = None
    # Hapus file session
    clear_session_data()

def login():
    """Fungsi login manual"""
    # Inisialisasi session state
    init_session_state()
    
    config = load_config()
    
    with st.form("login_form"):
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            # Cek ke database Supabase
            try:
                response = supabase.table("users").select("id_admin, nama, username, password, role, is_confirmed").eq("username", username).execute()
                if response.data and len(response.data) > 0:
                    user_data = response.data[0]
                    role = user_data.get("role", "admin")
                    is_confirmed = user_data.get("is_confirmed", None)
                    # Superadmin boleh login meskipun is_confirmed False/null
                    if role != "superadmin" and not is_confirmed:
                        st.error("Akun Anda belum dikonfirmasi oleh superadmin.")
                        return False, None, None
                    if verify_password(password, user_data['password']):
                        # Pastikan 'nama' dan 'role' ada sebelum disimpan
                        nama = user_data.get('nama', 'User Tanpa Nama')
                        role = user_data.get('role', 'admin')
                        save_login_state(username, nama, role)
                        now = datetime.utcnow().isoformat()
                        supabase.table("users").update({"last_login": now}).eq("id_admin", user_data["id_admin"]).execute()
                        st.success(f'Selamat datang *{nama}*')
                        return True, nama, username
                    else:
                        st.error('Password salah')
                        return False, None, None
                else:
                    st.error('Username tidak ditemukan')
                    return False, None, None
            except Exception as e:
                st.error(f"Gagal login: {str(e)}")
                return False, None, None
    return False, None, None

def logout():
    """Fungsi logout"""
    clear_login_state()
    st.rerun()

def is_authenticated():
    """Cek apakah user sudah login"""
    init_session_state()
    return st.session_state.get("authentication_status", False)

def get_current_user():
    """Mendapatkan informasi user yang sedang login"""
    init_session_state()
    return st.session_state.get("name", None), st.session_state.get("username", None)

def register_user():
    """Widget untuk registrasi user baru"""
    st.warning("Fitur registrasi tidak tersedia dalam mode sederhana")

def forgot_password():
    """Widget untuk lupa password"""
    st.warning("Fitur lupa password tidak tersedia dalam mode sederhana")

def forgot_username():
    """Widget untuk lupa username"""
    st.warning("Fitur lupa username tidak tersedia dalam mode sederhana")

def update_user_details():
    """Widget untuk update detail user"""
    st.warning("Fitur update profile tidak tersedia dalam mode sederhana")

# Tampilan Streamlit
def auth_page():
    st.title("Login System")
    
    if is_authenticated():
        st.success(f"Selamat datang, {st.session_state.get('username', '')}!")
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
