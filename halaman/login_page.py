import streamlit as st
from auth import login, is_authenticated, get_current_user

def app():
    st.header("🔐 Login Admin")
    
    # Cek status login dari session state
    if is_authenticated():
        name, username = get_current_user()
        st.success(f"Selamat datang, {name}!")
        st.info(f"Username: {username}")
        
        if st.button("Logout"):
            from auth import logout
            logout()
    else:
        # Tampilkan form login
        success, name, username = login()
        if success:
            st.rerun()
    
    # Informasi login
    st.markdown("---")
    st.markdown("### Informasi Login")
    st.markdown("""
    **User Default:**
    - Username: `admin`, Password: `admin123`
    - Username: `user1`, Password: `admin123`
    - Username: `user2`, Password: `admin123`
    """)
