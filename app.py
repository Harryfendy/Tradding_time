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
    teks_pip = st.text_input("Target Pip", value="5,10,15,20,25")
    daftar_pip = [int(x.strip()) for x in teks_pip.split(",")]
    menit_maju = st.number_input("Lihat Ke Depan (Menit)", min_value=5, value=60)

# ============== MUAT DATA ==============
@st.cache_data(ttl=3600)
def muat_data():
    try:
        df = pd.read_csv("data/hasil_akhir.csv")
        
        if 'time' not in df.columns:
            st.error(f"❌ Kolom tersedia: {', '.join(df.columns)}")
            return None
        
        df['time'] = pd.to_datetime(df['time'])
        df['menit_buka'] = df['time'].dt.strftime('%H:%M')
        df['hari_nama'] = df['time'].dt.day_name()
        df = df.sort_values('time').reset_index(drop=True)
        return df
    except FileNotFoundError:
        st.error("❌ File data/hasil_akhir.csv TIDAK DITEMUKAN!")
        return None

df = muat_data()
if df is None:
    st.stop()

# Saring sesuai hari
df_saring = df.copy()
if hari_pilih:
    if isinstance(hari_pilih, list):
        df_saring = df_saring[df_saring['hari_nama'].isin(hari_pilih)]
    else:
        df_saring = df_saring[df_saring['hari_nama'] == hari_pilih]

# ============== HITUNG PERSENTASE PER MENIT ==============
st.subheader("📋 Ringkasan")
st.info(f"""
✅ Total Data: {len(df_saring):,} baris
✅ Aturan: 1 Pip = 0.1 harga
✅ Target Pip: {', '.join(map(str, daftar_pip))}
✅ Lihat ke depan: {menit_maju} menit
""")

daftar_menit = sorted(df_saring['menit_buka'].unique())
hasil_peta = []

for waktu_buka in daftar_menit:
    data_waktu = df_saring[df_saring['menit_buka'] == waktu_buka]
    baris = {"Waktu Buka": waktu_buka}
    
    for pip in daftar_pip:
        rentang = pip / 10  # ✅ 1 pip = 0.1 → 5 pip = 0.5, 10 pip = 1.0 dst
        total = 0
        naik = 0
        turun = 0
        
        for idx, row in data_waktu.iterrows():
            buka = row['open']
            akhir = min(idx + 1 + menit_maju, len(df_saring))
            ke_depan = df_saring.iloc[idx+1 : akhir]
            
            if len(ke_depan) < 2:
                continue
            
            tertinggi = ke_depan['high'].max()
            terendah = ke_depan['low'].min()
            
            naik_cukup = (tertinggi - buka) >= rentang
            turun_cukup = (buka - terendah) >= rentang
            
            if naik_cukup and not turun_cukup:
                naik += 1
                total += 1
            elif turun_cukup and not naik_cukup:
                turun += 1
                total += 1
            elif naik_cukup and turun_cukup:
                idx_naik = ke_depan[ke_depan['high'] >= buka + rentang].index.min()
                idx_turun = ke_depan[ke_depan['low'] <= buka - rentang].index.min()
                if idx_naik < idx_turun:
                    naik += 1
                else:
                    turun += 1
                total += 1
        
        if total > 0:
            pct_naik = (naik / total) * 100
            pct_turun = (turun / total) * 100
            if pct_naik >= 55:
                baris[f"{pip} Pip"] = f"UP {pct_naik:.1f}%"
            elif pct_turun >= 55:
                baris[f"{pip} Pip"] = f"DOWN {pct_turun:.1f}%"
            else:
                baris[f"{pip} Pip"] = f"— {pct_naik:.0f}% —"
        else:
            baris[f"{pip} Pip"] = "—"
    
    hasil_peta.append(baris)

df_peta = pd.DataFrame(hasil_peta)

# ============== TAMPILAN ==============
st.subheader("🗺️ Peta Waktu XAUUSD")

def warna_sel(val):
    s = str(val).upper()
    if "UP" in s:
        return "background-color:#b7f0c8; color:#0b6623; font-weight:bold; text-align:center"
    elif "DOWN" in s:
        return "background-color:#f8c8cb; color:#8b0000; font-weight:bold; text-align:center"
    return "background-color:#f0f0f0; color:#666; text-align:center"

st.dataframe(
    df_peta.style.map(warna_sel),
    use_container_width=True,
    hide_index=True,
    height=750
)