import streamlit as st
st.set_page_config(page_title="Sidareja Predict")

from streamlit_option_menu import option_menu
from halaman import data_jumlah_penduduk, data_kepala_keluarga, data_putus_sekolah, data_migrasi, data_status_perkawinan, data_penduduk_usia, login_page, ui_dashboard, ui_kepala_keluarga, ui_migrasi, ui_penduduk_usia, ui_status_perkawinan, ui_putus_sekolah, konfirmasi_akun
from auth import is_authenticated, get_current_user, logout

def show_unauthenticated_menu():
    with st.sidebar:
        app = option_menu(
            menu_title='',
            options=['Dashboard', 'Penduduk Berdasarkan Usia', 'Keluarga', 'Migrasi', 'Status Perkawinan', 'Putus Sekolah', 'Login'],
            icons=['speedometer2', 'diagram-3', 'people-fill', 'arrow-left-right', 'heart-fill', 'book', 'box-arrow-in-right'],
            menu_icon='chat-text-fill',
            default_index=0,
            styles={
                "container": {"padding": "5!important"},
                "icon": {"color": "white", "font-size": "14px"},
                "nav-link": {"color": "white", "font-size": "14px", "text-align": "left", "margin": "5px 0px", "--hover-color": "blue"},
                "nav-link-selected": {"background-color": "grey", "font-weight": "normal"},
            }
        )
    if app == "Dashboard":
        ui_dashboard.app()
    elif app == "Penduduk Berdasarkan Usia":
        ui_penduduk_usia.app()
    elif app == "Keluarga":
        ui_kepala_keluarga.app()
    elif app == "Migrasi":
        ui_migrasi.app()
    elif app == "Status Perkawinan":
        ui_status_perkawinan.app()
    elif app == "Putus Sekolah":
        ui_putus_sekolah.app()
    elif app == "Login":
        login_page.app()

def show_authenticated_menu():
    # Tampilkan informasi user yang sedang login
    name, username = get_current_user()
    role = st.session_state.get('role', 'admin') # Ambil role dari session
    st.sidebar.title("👤 User Info")
    st.sidebar.success(f"Selamat datang, {name}!")
    st.sidebar.warning(f"Role: {role.capitalize()}")

    with st.sidebar:
        options = [
            'Data Jumlah Penduduk', 
            'Data Jumlah Kepala Keluarga', 
            'Data Jumlah Migrasi', 
            'Data Status Perkawinan', 
            'Data Putus Sekolah',
            'Data Penduduk Berdasarkan Usia'
        ]
        icons = [
            'people-fill',
            'person-vcard-fill',
            'arrow-left-right',
            'heart-fill',
            'book',
            'graph-up'
        ]
        
        # Tambahkan menu konfirmasi jika user adalah superadmin
        if role == "superadmin":
            options.append('Konfirmasi Akun')
            icons.append('person-check-fill')

        options.append('Logout')
        icons.append('box-arrow-right')

        app = option_menu(
            menu_title='',
            options=options,
            icons=icons,
            menu_icon='chat-text-fill',
            default_index=0,
            styles={
                "container": {"padding": "5!important"},
                "icon": {"color": "white", "font-size": "14px"},
                "nav-link": {"color": "white", "font-size": "14px", "text-align": "left", "margin": "5px 0px", "--hover-color": "blue"},
                "nav-link-selected": {"background-color": "grey", "font-weight": "normal"},
            }
        )

    # Navigasi menu
    if app == 'Konfirmasi Akun' and role == "superadmin":
        konfirmasi_akun.app()
    elif app == 'Logout':
        logout()
        st.rerun()
    if app == 'Data Jumlah Penduduk':
        data_jumlah_penduduk.app()
    elif app == 'Data Jumlah Kepala Keluarga':
        data_kepala_keluarga.app()
    elif app == 'Data Jumlah Migrasi':
        data_migrasi.app()
    elif app == 'Data Status Perkawinan':
        data_status_perkawinan.app()
    elif app == 'Data Putus Sekolah':
        data_putus_sekolah.app()
    elif app == 'Data Penduduk Berdasarkan Usia':
        data_penduduk_usia.app()


def main():
    if is_authenticated():
        show_authenticated_menu()
    else:
        show_unauthenticated_menu()

if __name__ == "__main__":
    main() 