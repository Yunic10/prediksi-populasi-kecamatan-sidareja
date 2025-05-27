import streamlit as st
from auth import login, is_authenticated

def app():
    st.header("Login Admin")

    if is_authenticated():
        st.success("Anda sudah login sebagai admin.")
        return  # Menghentikan eksekusi jika sudah login

    username = st.text_input("Username", key="username")
    password = st.text_input("Password", type="password", key="password")

    if st.button("Submit"):
        if login(username, password):  # Menggunakan fungsi login dari auth.py
            st.success("Login berhasil! Silakan navigasi ke halaman admin.")
            st.rerun()  # Refresh halaman agar menu admin muncul
        else:
            st.error("Username atau password salah.")
