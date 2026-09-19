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

st.title("📊 TRADING HISTORY BY TIME")
st.success(f"✅ Selamat datang, {st.session_state.nama}!")
if st.button("🚪 Keluar"):
    st.session_state.sudah_masuk = False
    st.rerun()

# ============== PENGATURAN ==============
with st.sidebar:
    st.header("⚙️ Pengaturan")
    tgl_mulai = st.date_input("Dari Tanggal", value=datetime(2025,9,1))
    tgl_akhir = st.date_input("Sampai Tanggal", value=datetime(2026,9,19))
    
    batas_2thn = tgl_mulai + timedelta(days=730)
    if tgl_akhir > batas_2thn:
        st.error("⚠️ Maksimal 2 Tahun!")
        tgl_akhir = batas_2thn

    st.subheader("📆 Kelompokkan Hari")
    mode = st.radio("Pilih Cara:", [
        "✅ Semua Hari",
        "📅 Hari yang Sama Saja",
        "🔍 Pilih Hari Tertentu"
    ])
    hari_pilih = None
    peta_hari = {
        "Senin": "Monday", "Selasa": "Tuesday", "Rabu": "Wednesday",
        "Kamis": "Thursday", "Jumat": "Friday"
    }
    if mode == "📅 Hari yang Sama Saja":
        hari_nama = st.selectbox("Pilih Hari:", list(peta_hari.keys()))
        hari_pilih = peta_hari[hari_nama]
    elif mode == "🔍 Pilih Hari Tertentu":
        hari_pilih = []
        for n, e in peta_hari.items():
            if st.checkbox(n, True):
                hari_pilih.append(e)

    st.divider()
    teks_pip = st.text_input("Rentang Pip", value="50,100,150,200,250")
    daftar_pip = [int(x.strip()) for x in teks_pip.split(",")]

# ============== MUAT DATA ==============
@st.cache_data(ttl=3600)
def muat_data():
    try:
        df = pd.read_csv("data/hasil_akhir.csv")
        df['time'] = pd.to_datetime(df['time'])
        df['hari'] = df['time'].dt.day_name()
        df['jam'] = df['time'].dt.hour
        return df
    except FileNotFoundError:
        return None

df = muat_data()

if df is None:
    st.warning("⚠️ Data belum tersedia. Jalankan proses_data.py dulu!")
    st.stop()

# Saring data sesuai hari
df_saring = df.copy()
if hari_pilih:
    if isinstance(hari_pilih, list):
        df_saring = df_saring[df_saring['hari'].isin(hari_pilih)]
    else:
        df_saring = df_saring[df_saring['hari'] == hari_pilih]

# ============== HITUNG PERSENTASE NAIK/TURUN ==============
hasil_peta = []
for jam in sorted(df_saring['jam'].unique()):
    per_jam = df_saring[df_saring['jam'] == jam]
    baris = {"Jam": f"{jam:02d}:00"}
    
    for pip in daftar_pip:
        # Hitung apakah harga naik/turun mencapai target pip
        hitung_naik = 0
        hitung_total = 0
        for _, row in per_jam.iterrows():
            rentang = pip / 100  # 50 pip = 0.50
            naik = (row['high'] - row['open']) >= rentang
            turun = (row['open'] - row['low']) >= rentang
            if naik or turun:
                hitung_total += 1
                if naik:
                    hitung_naik += 1
        
        if hitung_total > 0:
            persen = (hitung_naik / hitung_total) * 100
            if persen >= 50:
                baris[f"{pip} Pip"] = f"UP {persen:.1f}%"
            else:
                baris[f"{pip} Pip"] = f"DOWN {100-persen:.1f}%"
        else:
            baris[f"{pip} Pip"] = "—"
    
    hasil_peta.append(baris)

df_peta = pd.DataFrame(hasil_peta)

# ============== TAMPILAN ==============
st.subheader("📋 Ringkasan")
st.info(f"""
✅ Rentang: {tgl_mulai.strftime('%d %b %Y')} — {tgl_akhir.strftime('%d %b %Y')}
✅ Cara Hitung: {mode}
✅ Total baris data: {len(df_saring):,}
""")

st.subheader("🗺️ Peta Waktu XAUUSD")

def warna_sel(val):
    s = str(val).upper()
    if "UP" in s:
        return "background-color:#b7f0c8; color:#0b6623; font-weight:bold; text-align:center"
    elif "DOWN" in s:
        return "background-color:#f8c8cb; color:#8b0000; font-weight:bold; text-align:center"
    return "text-align:center"

st.dataframe(
    df_peta.style.map(warna_sel),
    use_container_width=True,
    hide_index=True,
    height=700
)