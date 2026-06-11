import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==============================================================================
# 1. INITIAL SYSTEM CONFIGURATION & THEME
# ==============================================================================
st.set_page_config(
    page_title="DCS Paper Machine Advanced Cockpit",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling DCS Industri Tingkat Lanjut (Aksen Neon Indigo & Amber Alert)
st.markdown("""
    <style>
    .main { background-color: #0b0f17; color: #c9d1d9; }
    div[data-testid="stSidebar"] { background-color: #121620; border-right: 1px solid #21262d; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; font-family: 'Courier New', monospace; }
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; font-size: 14px; }
    .stTabs [aria-selected="true"] { color: #818cf8 !important; font-weight: bold; border-bottom-color: #818cf8 !important; }
    .metric-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SIDEBAR CONTROL PANEL (ADVANCED INDUSTRIAL PARAMETERS)
# ==============================================================================
st.sidebar.title("🎛️ DCS PM#1 MAIN CONSOLE")
st.sidebar.markdown("**Senior Automation Engineer:** Sella")
st.sidebar.markdown("---")

st.sidebar.subheader("🚀 Wet-End (Forming & Press)")
machine_speed = st.sidebar.slider("Wire Machine Speed (m/min)", 600, 2000, 1350, step=25)
headbox_pressure = st.sidebar.slider("Headbox Jet-to-Wire Ratio", 0.95, 1.05, 1.01, step=0.01)
consistency_inlet = st.sidebar.slider("Stock Consistency to Headbox (%)", 0.3, 1.2, 0.6, step=0.05)

st.sidebar.subheader("♨️ Dry-End (Steam & Calender)")
steam_pressure_group1 = st.sidebar.slider("Pre-Dryer Steam Pressure (Bar)", 2.0, 5.0, 3.8, step=0.1)
steam_pressure_group2 = st.sidebar.slider("Main-Dryer Steam Pressure (Bar)", 4.0, 8.0, 5.5, step=0.1)
calender_nip_load = st.sidebar.slider("Calender Linear Nip Load (kN/m)", 40, 150, 85, step=5)

st.sidebar.subheader("📋 Product Specification Target")
target_gsm = st.sidebar.slider("Target Basis Weight (GSM)", 40, 200, 80, step=5)
target_moisture = st.sidebar.slider("Target Moisture Content (%)", 5.0, 8.5, 6.5, step=0.1)

# ==============================================================================
# 3. HIGH-FIDELITY PAPER PHYSICS SIMULATION ENGINE
# ==============================================================================
@st.cache_data(ttl=60)
def generate_advanced_pm_data(speed, jet_wire, consistency, steam1, steam2, nip_load, gsm, t_moist):
    base_end = datetime.now()
    base_start = base_end - timedelta(days=5)
    timestamps = pd.date_range(start=base_start, end=base_end, freq='15min')
    n_rows = len(timestamps)
    
    np.random.seed(42) # Konsistensi stok data tak acak acakan
    
    # --- 1. Perhitungan Mekanika Laju Produksi Bruto ---
    # Produksi (Ton/Jam) = Speed (m/min) * Lebar Mesin (asumsi 6.5m) * GSM * 60 / 1,000,000 * Efisiensi
    width = 6.5
    gross_production = (speed * width * gsm * 60) / 1000000.0
    
    # --- 2. Perhitungan Profil Kelembaban (Moisture) ---
    # Kecepatan tinggi memperpendek waktu retensi pengeringan (Moisture naik)
    # Konsistensi rendah memasukkan lebih banyak air ke mesin (Moisture naik)
    # Tekanan steam tinggi menurunkan kadar air (Moisture turun)
    moisture_effect = 12.5 + (speed * 0.004) + ((1.2 - consistency) * 2.0) - (steam1 * 0.7) - (steam2 * 0.9)
    moisture_array = np.clip(moisture_effect + np.random.normal(0, 0.12, n_rows), 3.5, 11.0)
    
    # --- 3. Perhitungan Ketebalan Kertas (Caliper - µm) ---
    # Dipengaruhi oleh gramatur dasar (GSM) dan tekanan penjepitan calender roll (nip_load)
    base_caliper = (gsm * 1.3) - (nip_load * 0.15) + ((1.01 - jet_wire) * 10)
    caliper_array = np.clip(base_caliper + np.random.normal(0, 0.8, n_rows), 50.0, 300.0)
    
    # --- 4. Indeks Formasi Serat & Kekuatan Tarik (Tensile Index) ---
    # Formasi terbaik terjadi ketika Jet-to-Wire Ratio mendekati ideal (1.00 - 1.02)
    formation_loss = abs(jet_wire - 1.01) * 150
    formation_array = np.clip(92 - formation_loss - (speed * 0.005) + np.random.normal(0, 0.7, n_rows), 55.0, 96.0)
    
    tensile_array = (formation_array * 0.6) + (consistency * 12) + np.random.normal(0, 0.5, n_rows)
    
    # --- 5. Keandalan Mekanis & Risiko Kertas Putus (Sheet Breaks) ---
    # Kecepatan melebihi 1600 m/min meningkatkan getaran mekanis dan risiko lembaran putus
    vibration_base = 1.2 + (speed / 700)**2.5
    vibration_array = vibration_base + np.random.normal(0, 0.15, n_rows)
    
    bearing_temp = 45 + (speed * 0.02) + (nip_load * 0.05) + np.random.normal(0, 0.3, n_rows)
    
    # Penentuan status runnability
    status_array = []
    net_production = []
    for i in range(n_rows):
        # Jika vibrasi terlalu ekstrem atau moisture terlalu basah (>9.5%), kertas putus (Break)
        if vibration_array[i] > 6.2 or moisture_array[i] > 9.5:
            status_array.append("SHEET BREAK")
            net_production.append(0.0)
        else:
            status_array.append("RUNNING")
            net_production.append(gross_production)
            
    # --- 6. Matriks OEE Efisiensi Total ---
    availability = (status_array.count("RUNNING") / n_rows) * 100
    performance = (speed / 2000) * 100 # Rasio kecepatan terhadap desain maksimum
    quality_rate = np.mean([100 if (t_moist-1 <= m <= t_moist+1) else 90 for m in moisture_array])
    oee_score = (availability / 100) * (performance / 100) * (quality_rate / 100) * 100

    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Machine_Speed': speed + np.random.normal(0, 2, n_rows),
        'Gross_Prod': gross_production,
        'Net_Production': net_production,
        'Moisture': moisture_array,
        'Caliper': caliper_array,
        'Formation': formation_array,
        'Tensile': tensile_array,
        'Vibration': vibration_array,
        'Bearing_Temp': bearing_temp,
        'Status': status_array
    })
    
    return df, oee_score, availability, performance, quality_rate

# Eksekusi simulasi
df_pm, oee, avail, perf, qual = generate_advanced_pm_data(
    machine_speed, headbox_pressure, consistency_inlet,
    steam_pressure_group1, steam_pressure_group2, calender_nip_load,
    target_gsm, target_moisture
)

latest = df_pm.iloc[-1]

# ==============================================================================
# 4. COCKPIT DASHBOARD HEADERS & CRITICAL METRICS
# ==============================================================================
st.title("🏭 ADVANCED DCS PAPER MACHINE (PM#1)")
st.markdown("Sistem Integrasi Lini Produksi Otomatisasi Terpusat QCS & DCS — Pengawasan Real-time.")
st.markdown("---")

# Row 1: Status Utama & Matriks Kinerja OEE
oee_cols = st.columns(5)
with oee_cols[0]:
    if latest['Status'] == "RUNNING":
        st.markdown("<div style='background-color:#064e3b; padding:10px; border-radius:5px; text-align:center; border:1px solid #059669;'><b>SYSTEM STATUS: RUNNING</b></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background-color:#7f1d1d; padding:10px; border-radius:5px; text-align:center; border:1px solid #dc2626;'><b>SYSTEM STATUS: BREAK DETECTED</b></div>", unsafe_allow_html=True)

with oee_cols[1]:
    st.metric("OEE Overall Score", f"{oee:.1f} %", delta="Target KPI: >85%")
with oee_cols[2]:
    st.metric("Machine Availability", f"{avail:.1f} %", delta="Waktu Operasi")
with oee_cols[3]:
    st.metric("Performance Rate", f"{perf:.1f} %", delta="Rasio Kecepatan")
with oee_cols[4]:
    st.metric("Quality Yield Rate", f"{qual:.1f} %", delta="Akurasi Spesifikasi")

st.markdown("<br>", unsafe_allow_html=True)

# Row 2: Sensor QCS Utama (Kualitas Lembaran)
qcs_cols = st.columns(4)
with qcs_cols[0]:
    st.metric(
        label="Scanner Basis Weight", 
        value=f"{target_gsm} GSM", 
        delta=f"Output Net: {latest['Net_Production']:.1f} Ton/Jam"
    )
with qcs_cols[1]:
    m_now = latest['Moisture']
    st.metric(
        label="Scanner Moisture Content", 
        value=f"{m_now:.2f} %", 
        delta=f"Target Dev: {(m_now - target_moisture):.2f} %",
        delta_color="inverse" if abs(m_now - target_moisture) > 0.5 else "normal"
    )
with qcs_cols[2]:
    st.metric(
        label="Caliper (Thickness)", 
        value=f"{latest['Caliper']:.1f} µm", 
        delta=f"Nip Press Load: {calender_nip_load} kN/m",
        delta_color="off"
    )
with qcs_cols[3]:
    st.metric(
        label="Fiber Tensile Strength", 
        value=f"{latest['Tensile']:.2f} Nm/g", 
        delta=f"Formation: {latest['Formation']:.1f} Pts"
    )

# ==============================================================================
# 5. MULTI-LINE PROCESS TABS & GRAPHICAL ANALYSIS
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab_qcs, tab_steam_balance, tab_mechanical, tab_event_log = st.tabs([
    "📊 QCS Quality Scanner Profile", 
    "💨 Dryer Steam & Thermal Balance", 
    "🩺 Mechanical Health & Predictive Maintenance",
    "🚨 Automation Alarm & Event Logs"
])

# ---- TAB 1: PROFILE SCANNER UTAMA ----
with tab_qcs:
    st.subheader("Profil Pengendalian Mutu Lembaran Kertas Komprehensif")
    col1, col2 = st.columns(2)
    with col1:
        fig_moist_trend = go.Figure()
        fig_moist_trend.add_trace(go.Scatter(x=df_pm['Timestamp'], y=df_pm['Moisture'], name='Moisture Aktual (%)', line=dict(color='#818cf8', width=2)))
        fig_moist_trend.add_hline(y=target_moisture, line=dict(color='#10b981', dash='dash'), annotation_text="Setpoint Target")
        fig_moist_trend.add_hline(y=target_moisture+1, line=dict(color='#ef4444', dash='dot'), annotation_text="UCL (Batas Atas)")
        fig_moist_trend.add_hline(y=target_moisture-1, line=dict(color='#ef4444', dash='dot'), annotation_text="LCL (Batas Bawah)")
        fig_moist_trend.update_layout(title="Tren Kontrol Kadar Air (Moisture Control Loop)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_moist_trend, use_container_width=True)
    with col2:
        fig_caliper = px.line(df_pm, x='Timestamp', y='Caliper', title="Keseragaman Ketebalan Lembaran Kertas (Caliper Profiles - µm)", color_discrete_sequence=['#fbbf24'])
        fig_caliper.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_caliper, use_container_width=True)

# ---- TAB 2: SISTEM THERMAL & STEAM BALANCE ----
with tab_steam_balance:
    st.subheader("Distribusi Tekanan Uap Panas di Silinder Dryer")
    col3, col4 = st.columns(2)
    with col3:
        # Korelasi Laju Produksi vs Kecepatan Mesin
        fig_steam_ratio = go.Figure()
        fig_steam_ratio.add_trace(go.Scatter(x=df_pm['Timestamp'], y=df_pm['Net_Production'], name='Net Production Rate (TPH)', fill='tozeroy', line=dict(color='#059669')))
        fig_steam_ratio.update_layout(title="Kapasitas Output Tonase Bersih yang Dihasilkan", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_steam_ratio, use_container_width=True)
    with col4:
        # Tampilan komparasi grup pengeringan
        fig_bar_steam = go.Figure(data=[
            go.Bar(name='Pre-Dryer Section', x=['Target Setpoint', 'Aktual Operasi'], y=[steam_pressure_group1, steam_pressure_group1 * 0.98], marker_color='#a855f7'),
            go.Bar(name='Main-Dryer Section', x=['Target Setpoint', 'Aktual Operasi'], y=[steam_pressure_group2, steam_pressure_group2 * 0.99], marker_color='#ec4899')
        ])
        fig_bar_steam.update_layout(title="Perbandingan Tekanan Uap Antar Seksi Silinder Pengering (Bar)", barmode='group', template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar_steam, use_container_width=True)

# ---- TAB 3: HEALTH MONITORING (PREDICTIVE MAINTENANCE) ----
with tab_mechanical:
    st.subheader("Sistem Deteksi Dini Kerusakan Komponen Mekanikal")
    col5, col6 = st.columns(2)
    with col5:
        fig_vib = px.line(df_pm, x='Timestamp', y='Vibration', title="Tingkat Vibrasi Rumah Bantalan Roll (Vibration Level - mm/s)", color_discrete_sequence=['#f43f5e'])
        fig_vib.add_hline(y=5.0, line=dict(color='yellow', dash='dash'), annotation_text="Batas Peringatan Kebisingan")
        fig_vib.add_hline(y=6.2, line=dict(color='red', dash='dot'), annotation_text="Batas Kritis Trip Otomatis")
        fig_vib.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_vib, use_container_width=True)
    with col6:
        fig_temp = px.area(df_pm, x='Timestamp', y='Bearing_Temp', title="Suhu Operasional Bantalan Poros Utama (°C)", color_discrete_sequence=['#d97706'])
        fig_temp.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_temp, use_container_width=True)

# ---- TAB 4: ALARM & HISTORICAL SYSTEM LOG ----
with tab_event_log:
    st.subheader("Daftar Urutan Kejadian Sistem Otomatisasi (Sequence of Events)")
    
    # Memfilter data kejadian kritis (saat ada break atau anomali)
    breaks_df = df_pm[df_pm['Status'] == "SHEET BREAK"][['Timestamp', 'Machine_Speed', 'Moisture', 'Vibration', 'Status']]
    breaks_df['Message'] = "❌ CRITICAL ALARM: Paper sheet severed due to excessive speed/moisture stress. Production halted."
    
    warning_df = df_pm[(df_pm['Vibration'] > 4.8) & (df_pm['Status'] == "RUNNING")][['Timestamp', 'Machine_Speed', 'Moisture', 'Vibration', 'Status']]
    warning_df['Message'] = "⚠️ WARNING LOG: High mechanical vibration detected on Press Section #2."
    
    # Gabung log kejadian
    log_total = pd.concat([breaks_df, warning_df]).sort_values(by='Timestamp', ascending=False)
    
    if not log_total.empty:
        st.dataframe(log_total[['Timestamp', 'Status', 'Message', 'Machine_Speed', 'Vibration']], use_container_width=True)
    else:
        st.success("✅ Seluruh parameter operasi normal. Tidak ada rekaman alarm kritis dalam 5 hari terakhir.")

# ==============================================================================
# 6. HISTORICAL MASTER SENSOR DATA LOGS
# ==============================================================================
st.markdown("---")
st.subheader("📋 Master Sensor SCADA History Database")
st.dataframe(df_pm.sort_values(by='Timestamp', ascending=False), use_container_width=True, height=220)

st.markdown("---")
st.caption("Advanced QCS-DCS Core Platform Engine v3.4 • Sella • Universitas Riau")