# Sistem Autentikasi Sidareja

## Overview
Aplikasi ini menggunakan sistem autentikasi manual yang aman dengan session persistence untuk menjaga user tetap login saat refresh.

## Fitur Autentikasi

### ✅ Fitur yang Tersedia
- **Login/Logout**: Autentikasi dengan username dan password
- **Session Persistence**: Status login tetap tersimpan saat refresh browser
- **Session Expiry**: Session otomatis expired setelah 24 jam
- **Password Hashing**: Bcrypt encryption untuk keamanan
- **Caching**: Data konfigurasi di-cache untuk performa optimal

### 🔐 User Default
```
Username: admin
Password: admin123
Email: admin@sidareja.com

Username: user1  
Password: admin123
Email: user1@sidareja.com

Username: user2
Password: admin123  
Email: user2@sidareja.com
```

## Struktur File

### File Konfigurasi
- `config.yaml` - Konfigurasi user dan pengaturan autentikasi
- `auth.py` - Fungsi-fungsi autentikasi utama dengan session persistence
- `halaman/login_page.py` - Halaman login dengan UI sederhana
- `session_data.json` - File temporary untuk menyimpan session (auto-generated)

### File Utilitas
- `generate_password.py` - Script untuk generate password hash
- `data_utils.py` - Utility untuk caching data CSV/Excel

## Cara Penggunaan

### 1. Login
1. Buka aplikasi
2. Klik menu "Login"
3. Masukkan username dan password
4. Setelah berhasil, menu admin akan muncul
5. **Status login akan tetap tersimpan saat refresh browser**

### 2. Session Management
- **Session Duration**: 24 jam (dapat diubah di `auth.py`)
- **Auto Logout**: Session otomatis expired setelah 24 jam
- **Manual Logout**: Klik tombol logout untuk keluar segera

### 3. Keamanan
- Password di-hash menggunakan bcrypt
- Session data disimpan di file temporary
- File session otomatis dihapus saat logout atau expired

## Menambah User Baru

### Cara Manual Edit config.yaml
1. Generate password hash:
```bash
python generate_password.py
```

2. Edit `config.yaml`:
```yaml
credentials:
  usernames:
    newuser:
      email: newuser@example.com
      name: New User Name
      password: $2b$12$... # hash dari generate_password.py
```

## Caching System

### Data Caching
- **Konfigurasi**: `@st.cache_data` untuk `load_config()`
- **Data CSV/Excel**: `@st.cache_data` untuk semua fungsi load data
- **Session File**: `@st.cache_data` untuk path file session

### Manfaat Caching
- **Performa**: Data tidak perlu di-load ulang setiap kali
- **Efisiensi**: Mengurangi I/O operations
- **User Experience**: Loading lebih cepat

## Troubleshooting

### Error: "Session tidak tersimpan"
- Pastikan folder aplikasi memiliki permission write
- Cek apakah file `session_data.json` dapat dibuat

### Error: "Login otomatis logout"
- Cek apakah file `session_data.json` ada dan valid
- Pastikan waktu sistem tidak berubah drastis

### Error: "Password tidak dikenali"
- Pastikan password hash di `config.yaml` benar
- Gunakan `generate_password.py` untuk generate hash baru

## Dependencies

```txt
streamlit>=1.28.0
PyYAML>=5.3.1
bcrypt>=3.1.7
pandas>=2.0.0
```

## File Session

### session_data.json
File temporary yang berisi:
```json
{
  "username": "admin",
  "name": "Administrator", 
  "login_time": 1640995200.0,
  "expiry_time": 1641081600.0
}
```

### Keamanan
- File ini **TIDAK** masuk ke repository (ada di .gitignore)
- Otomatis dihapus saat logout atau expired
- Berisi data sensitif, jangan share

## Referensi
- [Streamlit Session State](https://docs.streamlit.io/library/api-reference/session-state)
- [Bcrypt Documentation](https://pypi.org/project/bcrypt/)
- [PyYAML Documentation](https://pyyaml.org/) 