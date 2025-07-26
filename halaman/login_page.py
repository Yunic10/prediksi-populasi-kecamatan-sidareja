import streamlit as st
from auth import login, is_authenticated, get_current_user
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def register():
    st.header("Register Akun Baru")
    with st.form("register_form"):
        nama = st.text_input("Nama Lengkap")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        password2 = st.text_input("Konfirmasi Password", type="password")
        submit = st.form_submit_button("Daftar")
        if submit:
            if not nama or not username or not password or not password2:
                st.error("Semua field wajib diisi!")
            elif password != password2:
                st.error("Password dan konfirmasi password tidak sama!")
            else:
                # Cek username sudah ada
                response = supabase.table("users").select("id_admin").eq("username", username).execute()
                if response.data and len(response.data) > 0:
                    st.error("Username sudah terdaftar!")
                else:
                    hashed = generate_password_hash(password)
                    supabase.table("users").insert({
                        "nama": nama,
                        "username": username,
                        "password": hashed,
                        "role": "admin",
                        "is_confirmed": False
                    }).execute()
                    st.success("Registrasi berhasil! Silakan tunggu konfirmasi dari superadmin sebelum bisa login.")
                    st.info("Kembali ke halaman login untuk masuk setelah akun dikonfirmasi.")

def app():
    st.header("Login Admin")

    if is_authenticated():
        name, username = get_current_user()
        st.success(f"Selamat datang, {name}!")
        st.info(f"Username: {username}")
        if st.button("Logout"):
            from auth import logout
            logout()
            st.rerun() # Tambahkan rerun setelah logout
    else:
        # Gunakan st.tabs untuk tampilan yang lebih modern
        login_tab, register_tab = st.tabs(["Login", "Register"])

        with login_tab:
            st.subheader("Login ke Akun Anda")
            success, name, username = login()
            if success:
                st.rerun()

        with register_tab:
            register()
