import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="TRADING HISTORY BY TIME", layout="wide")

# ============== HALAMAN LOGIN ==============
@st.cache_data(ttl=60)
def muat_daftar_pengguna():
    try:
        with open("data/daftar_pengguna.json") as f:
            return json.load(f)
    except:
        return {"admin": "123456"}

DAFTAR_PENGGUNA = muat_daftar_pengguna()

if "sudah_masuk" not in st.session_state:
    st.session_state.sudah_masuk = False

if not st.session_state.sudah_masuk:
    st.title("🔐 MASUK — TRADING HISTORY BY TIME")
    with st.form("form_login"):
        nama = st.text_input("👤 Nama Pengguna")
        sandi = st.text_input("🔑 Kata Sandi", type="password")
        masuk = st.form_submit_button("✅ Masuk")
    
    if masuk:
        nama = nama.strip()
        if nama in DAFTAR_PENGGUNA and sandi == DAFTAR_PENGGUNA[nama]:
            st.session_state.sudah_masuk = True
            st.session_state.nama = nama
            st.rerun()
        else:
            st.error("❌ Nama pengguna atau kata sandi salah!")
    st.stop()

# --- BERHASIL MASUK ---
st.title("📊 TRADING HISTORY BY TIME")
st.success(f"✅ Selamat datang, {st.session_state.nama}!")
if st.button("🚪 Keluar"):
    st.session_state.sudah_masuk = False
    st.rerun()

# ============== PENGATURAN ==============
with st.sidebar:
    st.header("⚙️ Pengaturan")
    st.subheader("📅 Rentang Riwayat Data")
    tgl_mulai = st.date_input("Dari Tanggal", value=datetime(2024,9,1))
    tgl_akhir = st.date_input("Sampai Tanggal", value=datetime(2026,8,30))
    
    batas_2thn = tgl_mulai + timedelta(days=730)
    if tgl_akhir > batas_2thn:
        st.error("⚠️ Maksimal 2 Tahun! Dipersingkat otomatis.")
        tgl_akhir = batas_2thn

    st.subheader("📆 Kelompokkan Hari")
    mode = st.radio("Pilih Cara:", [
        "✅ Semua Hari",
        "📅 Hari yang Sama Saja",
        "🔍 Pilih Hari Tertentu"
    ])
    hari_pilih = None
    if mode == "📅 Hari yang Sama Saja":
        hari_pilih = st.selectbox("Pilih Hari:", ["Senin","Selasa","Rabu","Kamis","Jumat"])
    elif mode == "🔍 Pilih Hari Tertentu":
        hari_pilih = []
        if st.checkbox("Senin",True): hari_pilih.append("Senin")
        if st.checkbox("Selasa",True): hari_pilih.append("Selasa")
        if st.checkbox("Rabu",True): hari_pilih.append("Rabu")
        if st.checkbox("Kamis",True): hari_pilih.append("Kamis")
        if st.checkbox("Jumat",True): hari_pilih.append("Jumat")

    st.divider()
    waktu_mulai = st.time_input("Waktu Mulai", value=datetime(2026,1,1,2,0))
    waktu_akhir = st.time_input("Waktu Berakhir", value=datetime(2026,1,1,6,0))
    langkah_menit = st.number_input("Langkah Menit", min_value=1, value=1)
    teks_pip = st.text_input("Rentang Pip", value="50,100,150,200,250")
    daftar_pip = [int(x.strip()) for x in teks_pip.split(",")]

# ============== MUAT & TAMPILKAN DATA ==============
@st.cache_data(ttl=3600)
def muat_data():
    try:
        return pd.read_csv("data/hasil_akhir.csv")
    except FileNotFoundError:
        return None

df = muat_data()
durasi = (tgl_akhir - tgl_mulai).days

st.subheader("📋 Ringkasan Pengaturan")
st.info(f"""
✅ Rentang: {tgl_mulai.strftime('%d %b %Y')} — {tgl_akhir.strftime('%d %b %Y')}  ({durasi} hari)
✅ Cara Hitung: {mode}
✅ Rentang Pip: {', '.join(map(str,daftar_pip))} pip
""")

if df is None:
    st.warning("⚠️ Data belum tersedia. Jalankan /update dari Telegram di Server Master untuk membuat data!")
    st.stop()

# Pewarnaan tabel
def warna_sel(val):
    s = str(val).upper()
    if "UP" in s:
        return "background-color:#b7f0c8; color:#0b6623; font-weight:bold; text-align:center"
    elif "DOWN" in s:
        return "background-color:#f8c8cb; color:#8b0000; font-weight:bold; text-align:center"
    else:
        return "background-color:#e9e9e9; color:#444444; font-weight:bold; text-align:center"

st.subheader("📊 Peta Hasil")
st.dataframe(
    df.style.applymap(warna_sel),
    use_container_width=True,
    hide_index=True,
    height=600
)
