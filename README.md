# Prediksi Populasi Kecamatan Sidareja

Aplikasi Streamlit untuk prediksi populasi Kecamatan Sidareja menggunakan machine learning dengan model SVM (Support Vector Machine).

## Fitur

- **Dashboard Prediksi**: Visualisasi prediksi populasi 3 tahun ke depan
- **Manajemen Data**: CRUD untuk berbagai jenis data penduduk
- **Prediksi Berdasarkan Kategori**:
  - Jumlah Penduduk (Laki-laki & Perempuan)
  - Kepala Keluarga
  - Migrasi (Masuk & Keluar)
  - Status Perkawinan
  - Penduduk Berdasarkan Usia
  - Anak Putus Sekolah
- **Sistem Autentikasi**: Login/logout untuk admin
- **Visualisasi Interaktif**: Grafik dan tabel dengan Plotly

## Instalasi

1. Clone repository ini
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Buat file `.env` dengan konfigurasi Supabase:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

4. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```

## Struktur Database

Aplikasi menggunakan Supabase dengan tabel-tabel berikut:

- `penduduk_tahunan`: Data jumlah penduduk tahunan
- `keluarga`: Data kepala keluarga
- `migrasi`: Data migrasi masuk dan keluar
- `status_perkawinan`: Data status perkawinan
- `penduduk_usia`: Data penduduk berdasarkan usia
- `putus_sekolah`: Data anak putus sekolah
- `tahun`: Referensi tahun
- `users`: Data pengguna untuk autentikasi

## Model Machine Learning

- **Algoritma**: Support Vector Machine (SVM) dengan kernel RBF
- **Preprocessing**: StandardScaler untuk normalisasi data
- **Metrik Evaluasi**: MAPE (Mean Absolute Percentage Error) dan R²
- **Prediksi**: 3 tahun ke depan berdasarkan data historis

## Penggunaan

1. **Dashboard**: Lihat prediksi populasi secara keseluruhan
2. **Menu Unauthenticated**: Akses visualisasi tanpa login
3. **Menu Authenticated**: Akses manajemen data (CRUD) setelah login
4. **Login**: Username: `admin`, Password: `admin123`

## Bug Fixes yang Telah Diperbaiki

1. **Invalid @st.dialog decorators**: Diganti dengan sistem konfirmasi yang proper
2. **Hardcoded credentials**: Dipindahkan ke environment variables
3. **Missing error handling**: Ditambahkan try-catch untuk handling error
4. **Data structure inconsistencies**: Diperbaiki struktur data di beberapa file
5. **Authentication system**: Diganti dari cookies ke session state

## Kontributor

- Yudith Nico Priambodo

## Lisensi

© 2025 - Yudith Nico Priambodo 