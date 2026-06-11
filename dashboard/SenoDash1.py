import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==============================================================================
# 1. KONFIGURASI UTAMA & TEMA SISTEM DCS
# ==============================================================================
st.set_page_config(
    page_title="Board Machine Optimization",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema Industri Gelap (DCS High-Contrast Black & Cyan Neon)
st.markdown("""
    <style>
    .main { background-color: #060913; color: #d1d5db; }
    div[data-testid="stSidebar"] { background-color: #0b0f19; border-right: 1px solid #1e293b; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; font-family: 'Consolas', monospace; }
    .stTabs [data-baseweb="tab"] { color: #9ca3af !important; font-size: 14px; }
    .stTabs [aria-selected="true"] { color: #00f0ff !important; font-weight: bold; border-bottom-color: #00f0ff !important; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. PANEL KONTROL SIDEBAR (DCS CONSOLE - OPERASI SENO)
# ==============================================================================
st.sidebar.title("🎛️ DCS BOARD MACHINE")
st.sidebar.markdown("**PIC:** Seno Aji Nugroho")
st.sidebar.markdown("---")

st.sidebar.subheader("🥞 Wet-End Multi-Ply Layer Setup")
board_speed = st.sidebar.slider("Wire Machine Speed (m/min)", 300, 1100, 650, step=50)

# Input Lapisan Luar (Top & Bottom)
top_ply_ratio = st.sidebar.slider("Top Ply Layer (Bleached Kraft) (%)", 10, 30, 20, step=1)
bottom_ply_ratio = st.sidebar.slider("Bottom Ply Layer (Testliner) (%)", 20, 50, 40, step=1)

# FIX VARIABEL BARU: Pastikan dideklarasikan di sini agar tidak NameError di bawah!
headbox_slice_opening = st.sidebar.slider("Headbox Slice Lip Opening (mm)", 12.0, 30.0, 18.5, step=0.5)

# Perhitungan otomatis lapisan tengah (Core/Center) agar total selalu 100%
center_ply_ratio = 100 - top_ply_ratio - bottom_ply_ratio

st.sidebar.markdown(f"""
    <div style='background-color:#111827; padding:10px; border-radius:5px; border:1px solid #374151;'>
        <small style='color:#9ca3af;'>Live Computed Layer Balance:</small><br>
        • Top Ply: <b>{top_ply_ratio}%</b><br>
        • Center Core Ply: <b style='color:#00f0ff;'>{center_ply_ratio}%</b><br>
        • Bottom Ply: <b>{bottom_ply_ratio}%</b>
    </div>
""", unsafe_allow_html=True)

st.sidebar.subheader("🗜️ Seksi Press & De-watering")
shoe_press_load = st.sidebar.slider("Shoe Press Load (kN/m)", 500, 1400, 900, step=50)
vacuum_pressure = st.sidebar.slider("Uhle Box Vacuum (kPa)", -60, -20, -40, step=5)

st.sidebar.subheader("🔥 Seksi Thermal & Dryer Cylinder")
yankee_pressure = st.sidebar.slider("Yankee Cylinder Steam (Bar)", 4.0, 9.0, 6.0, step=0.5)
dryer_temp = st.sidebar.slider("Dryer Hood Temp (°C)", 110, 180, 140, step=5)

st.sidebar.subheader("📋 Target Spesifikasi Produk")
target_gsm = st.sidebar.slider("Target Grammage (GSM)", 200, 500, 300, step=20)

# ==============================================================================
# 3. LIVE MATHEMATICAL ENGINE (100% AMAN, RESPONSIVE & ANTI-0.0)
# ==============================================================================
# 1. Perhitungan Live Kapasitas Produksi Massal (Ton/Jam)
trim_width = 5.6
live_gross_tph = (board_speed * trim_width * target_gsm * 60) / 1000000.0

# 2. Karakteristik Geometri Lembaran Karton (Caliper & Bulk)
live_bulk = 1.20 + (center_ply_ratio * 0.003) - (shoe_press_load * 0.0001)
live_caliper = target_gsm * live_bulk

# 3. Model Live Kadar Air (Moisture)
moisture_base = 35.0
press_efficiency = (shoe_press_load * 0.006) + (abs(vacuum_pressure) * 0.06)
thermal_efficiency = (yankee_pressure * 0.7) + (dryer_temp * 0.04)
speed_load_effect = board_speed * 0.008

live_moisture = moisture_base + speed_load_effect - press_efficiency - thermal_efficiency
live_moisture = np.clip(live_moisture, 5.8, 8.5)

# 4. Logic Interlock Safety DCS
if live_moisture > 9.5 or center_ply_ratio < 10 or center_ply_ratio > 70:
    live_status = "INTERLOCK TRIP"
    live_net_tph = 0.0
else:
    live_status = "SYSTEM NORMAL"
    live_net_tph = live_gross_tph

# ==============================================================================
# 4. DATA GENERATOR (UNTUK VISUALISASI GRAFIK TREN HISTORIS)
# ==============================================================================
@st.cache_data(ttl=10)
def generate_scada_history(speed, gsm, c_ratio):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=2)
    time_index = pd.date_range(start=start_time, end=end_time, freq='30min')
    rows = len(time_index)
    np.random.seed(24)
    
    h_gross = (speed * 5.6 * gsm * 60) / 1000000.0 + np.random.normal(0, 0.3, rows)
    h_moisture = 6.7 + np.sin(np.linspace(0, 15, rows)) * 0.4 + np.random.normal(0, 0.1, rows)
    h_caliper = (gsm * 1.32) + np.random.normal(0, 2, rows)
    
    return pd.DataFrame({
        'Timestamp': time_index,
        'Gross_TPH': h_gross,
        'Net_TPH': h_gross,
        'Caliper': h_caliper,
        'Moisture_Final': h_moisture,
        'Fresh_Water': 115 + (speed * 0.03) + np.random.normal(0, 2, rows),
        'White_Water': (h_gross * 14.8) + np.random.normal(0, 3, rows),
        'Center_Ratio': c_ratio + np.random.normal(0, 0.1, rows),
        'Stiffness_MD': (gsm * 0.1 + c_ratio * 0.2) + np.random.normal(0, 0.4, rows),
        'Stiffness_CD': ((gsm * 0.1 + c_ratio * 0.2) * 0.45) + np.random.normal(0, 0.2, rows),
        'Status': ["SYSTEM NORMAL" for _ in range(rows)]
    })

df_bm = generate_scada_history(board_speed, target_gsm, center_ply_ratio)

# ==============================================================================
# 5. COCKPIT UTAMA & LIVE KPI METRICS DI LAYAR UTAMA
# ==============================================================================
st.title("🏭 BOARD MACHINE CONTROL COCKPIT")
st.markdown("Sistem Pengendalian Distribusi Serat Multi-Lapisan Komprehensif, Pemerasan Hidrolik Beban Tinggi, dan Keseimbangan Thermal.")
st.markdown("---")

kpi_cols = st.columns(5)
with kpi_cols[0]:
    if live_status == "SYSTEM NORMAL":
        st.markdown("<div style='background-color:#022c22; color:#00ffb7; padding:12px; border-radius:6px; text-align:center; font-weight:bold; border:1px solid #059669;'>STATUS: SYSTEM NORMAL</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background-color:#450a0a; color:#f87171; padding:12px; border-radius:6px; text-align:center; font-weight:bold; border:1px solid #dc2626;'>STATUS: INTERLOCK TRIP</div>", unsafe_allow_html=True)

with kpi_cols[1]:
    st.metric(
        label="Net Output Capacity", 
        value=f"{live_net_tph:.1f} Ton/Jam", 
        delta=f"Gross: {live_gross_tph:.1f} TPH"
    )
with kpi_cols[2]:
    st.metric("Calculated Board Caliper", f"{live_caliper:.1f} µm", delta=f"Bulk: {live_bulk:.2f} cm³/g")
with kpi_cols[3]:
    st.metric("Bending Stiffness (MD)", f"{(target_gsm * 0.1 + center_ply_ratio * 0.2):.1f} mNm", delta=f"Core Ply: {center_ply_ratio}%", delta_color="off")
with kpi_cols[4]:
    st.metric("Live Moisture Content", f"{live_moisture:.2f} %", delta="Target: 6.0 - 8.0%")

# ==============================================================================
# 6. TAB DETAIL SUBSISTEM INDUSTRI
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab_wetbox, tab_dewatering, tab_thermal, tab_water = st.tabs([
    "🥞 Multi-Forming Headbox & Layers", 
    "🗜️ Press & Vacuum Extraction", 
    "🔥 Yankee Cylinder & Thermal Profiling",
    "💧 White Water Closed-Loop Recirculation"
])

# ---- TAB 1: FORMING SECTION ----
with tab_wetbox:
    st.subheader("Manajemen Distribusi Tiga Aliran Komponen Bubur Serat (*Ply Stratification*)")
    col1, col2 = st.columns([2, 1])
    with col1:
        fig_strat = go.Figure()
        fig_strat.add_trace(go.Scatter(x=df_bm['Timestamp'], y=[top_ply_ratio]*len(df_bm), name='Top Ply (Serat Kraft Halus)', stackgroup='one', line=dict(color='#00e1ff', width=1)))
        fig_strat.add_trace(go.Scatter(x=df_bm['Timestamp'], y=df_bm['Center_Ratio'], name='Center Core Ply (Serat Bulky/Mechanical)', stackgroup='one', line=dict(color='#374151', width=1)))
        fig_strat.add_trace(go.Scatter(x=df_bm['Timestamp'], y=[bottom_ply_ratio]*len(df_bm), name='Bottom Ply (Serat Testliner Daur Ulang)', stackgroup='one', line=dict(color='#9a3412', width=1)))
        fig_strat.update_layout(title="Visualisasi Distribusi Profil Lapisan Karton (%)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_range=[0, 100])
        st.plotly_chart(fig_strat, use_container_width=True)
    with col2:
        # DI SINI SUDAH FIXED: Memanggil variabel headbox_slice_opening dengan aman!
        st.markdown(f"""
        <div style='background-color:#0f172a; padding:20px; border-radius:8px; border:1px solid #1e293b;'>
            <h4 style='color:#00e1ff; margin-top:0;'>📐 Analisis Formasi Struktur Karton:</h4><br>
            • Rasio Top Ply (Luar Atas): <b>{top_ply_ratio} %</b><br>
            • Rasio Center Core (Tengah): <b style='color:#00f0ff;'>{center_ply_ratio} %</b><br>
            • Rasio Bottom Ply (Luar Bawah): <b>{bottom_ply_ratio} %</b><br>
            • Pembukaan Lip Headbox: <b>{headbox_slice_opening} mm</b><br><br>
            <span style='color:#f59e0b;'><i>*Prinsip I-Beam: Lapisan luar atas dan bawah menahan gaya tarik (tensile), sementara lapisan tengah memaksimalkan ketebalan (bulk) untuk meningkatkan kekakuan tekuk (bending stiffness).*</i></span>
        </div>
        """, unsafe_allow_html=True)

# ---- TAB 2: SEKSI DE-WATERING ----
with tab_dewatering:
    st.subheader("Efisiensi Penarikan Air Mekanis via Shoe Press & Vakum Uhle Box")
    col3, col4 = st.columns(2)
    with col3:
        fig_moist_trend = go.Figure()
        fig_moist_trend.add_trace(go.Scatter(x=df_bm['Timestamp'], y=df_bm['Moisture_Final'], name='Moisture Historical', line=dict(color='#10b981', width=2.5)))
        fig_moist_trend.update_layout(title="Tren Kadar Air Akhir Produk Lembaran (Historical)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_moist_trend, use_container_width=True)
    with col4:
        fig_cal_trend = px.line(df_bm, x='Timestamp', y='Caliper', title="Profil Ketebalan Karton Historis (µm)", color_discrete_sequence=['#f59e0b'])
        fig_cal_trend.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_cal_trend, use_container_width=True)

# ---- TAB 3: SEKSI THERMAL CONTROL ----
with tab_thermal:
    st.subheader("Profil Energi Temperatur Tudung Pengering Utama & Silinder Yankee")
    col5, col6 = st.columns(2)
    with col5:
        fig_stiff = go.Figure()
        fig_stiff.add_trace(go.Scatter(x=df_bm['Timestamp'], y=df_bm['Stiffness_MD'], name='Kekakuan MD (Machine Direction)', line=dict(color='#3b82f6', width=2)))
        fig_stiff.add_trace(go.Scatter(x=df_bm['Timestamp'], y=df_bm['Stiffness_CD'], name='Kekakuan CD (Cross Direction)', line=dict(color='#f43f5e', width=1.5, dash='dot')))
        fig_stiff.update_layout(title="Kekakuan Tekuk Lembaran (*Bending Stiffness Analysis*)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_stiff, use_container_width=True)
    with col6:
        fig_bar_thermal = go.Figure(data=[
            go.Bar(name='Tekanan Yankee (Bar)', x=['Setpoint', 'Live'], y=[yankee_pressure, yankee_pressure], marker_color='#ef4444'),
            go.Bar(name='Suhu Dryer Hood (°C/10)', x=['Setpoint', 'Live'], y=[dryer_temp/10.0, dryer_temp/10.0], marker_color='#f97316')
        ])
        fig_bar_thermal.update_layout(title="Verifikasi Validasi Live Sistem Pemanas Termal", barmode='group', template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar_thermal, use_container_width=True)

# ---- TAB 4: SIKLO AIR PROSES ----
with tab_water:
    st.subheader("Neraca Kesetimbangan Air Bersih & Sirkulasi Air Putih (*White Water Recycle*)")
    col7, col8 = st.columns(2)
    with col7:
        fig_fresh = px.area(df_bm, x='Timestamp', y='Fresh_Water', title="Laju Konsumsi Fresh Water Lini Produksi (m³/Jam)", color_discrete_sequence=['#8b5cf6'])
        fig_fresh.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_fresh, use_container_width=True)
    with col8:
        fig_white = px.line(df_bm, x='Timestamp', y='White_Water', title="Sirkulasi Loop White Water Wet-End (m³/Jam)", color_discrete_sequence=['#10b981'])
        fig_white.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_white, use_container_width=True)

# ==============================================================================
# 7. LOG RIWAYAT DATABASE MONITORING SENSOR
# ==============================================================================
st.markdown("---")
st.subheader("📋 Master Sensor Database History Log")
st.dataframe(df_bm.sort_values(by='Timestamp', ascending=False), use_container_width=True, height=180)

st.markdown("---")
st.caption("Advanced Industrial Multi-Ply Board Structural SCADA Core Module v4.6 • Seno • Universitas Riau")