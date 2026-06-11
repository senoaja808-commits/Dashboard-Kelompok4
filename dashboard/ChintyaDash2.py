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
    page_title="Pulp Dryer Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme DCS Operator Room Premium
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    div[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; }
    .stTabs [aria-selected="true"] { color: #58a6ff !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. ADVANCED INTERACTIVE SIDEBAR CONTROL PANEL
# ==============================================================================
st.sidebar.title("DCS Pulp Dryer Control")
st.sidebar.markdown("**PIC:** Chintya Isya Ababil")
st.sidebar.markdown("---")

st.sidebar.subheader("🎯 Parameter Operasi Wet End")
wire_speed_setpoint = st.sidebar.slider("Machine Wire Speed (m/min)", 140.0, 220.0, 180.0, step=5.0)
headbox_consistency_setpoint = st.sidebar.slider("Headbox Consistency (%)", 0.8, 1.6, 1.2, step=0.05)

st.sidebar.subheader("♨️ Parameter Operasi Airborne Dryer")
steam_pressure_setpoint = st.sidebar.slider("Steam Pressure Inlet (Bar)", 3.0, 6.0, 4.5, step=0.1)
target_moisture = st.sidebar.slider("Target Moisture Lembaran (%)", 7.0, 13.0, 10.0, step=0.2)

st.sidebar.subheader("📅 Filter Periode")
base_end = datetime.now()
base_start = base_end - timedelta(days=7)
date_selection = st.sidebar.date_input(
    "Rentang Waktu Sensor", 
    value=[base_start.date(), base_end.date()], 
    min_value=base_start.date(), 
    max_value=base_end.date()
)

# ==============================================================================
# 3. HIGHLY COUPLED INTERACTIVE DATA MATHEMATICAL ENGINE
# ==============================================================================
def generate_highly_interactive_dryer_data(w_speed, h_consistency, s_pressure, t_moisture):
    timestamps = pd.date_range(start=base_start, end=base_end, freq='15min')
    n_rows = len(timestamps)
    
    np.random.seed(42) # Seed dikunci agar baseline kokoh
    
    # [MATHEMATICAL COUPLING RELATIONSHIPS]
    # 1. Produksi berbanding lurus dengan Kecepatan Wire & Konsistensi Headbox
    base_prod = (w_speed * 5.5) * (h_consistency / 1.2)
    production_rate = base_prod + np.random.normal(0, 12, n_rows)
    
    # 2. Kebutuhan Steam (Steam Flow) melonjak jika mesin makin cepat (banyak air dibawa)
    # atau jika user memaksa mengeringkan pulp sampai moisture sangat rendah (low target moisture)
    moisture_drying_effort = max(0.5, 15.0 - t_moisture)
    base_steam = (w_speed * 0.18) + (moisture_drying_effort * 2.5) + (s_pressure * 1.2)
    steam_flow = base_steam + np.random.normal(0, 1.5, n_rows)
    
    # 3. Kelembaban Akhir Lembaran (Moisture) ditentukan oleh tekanan uap vs kecepatan tarikan mesin
    # Semakin tinggi pressure = makin kering (moisture drop). Semakin cepat wire = waktu tinggal sedikit, moisture naik.
    drying_efficiency_factor = (s_pressure / 4.5) * 12.0
    calculated_moisture = (w_speed / 15) - drying_efficiency_factor + np.random.normal(0, 0.25, n_rows)
    # Dekatkan tren ke arah target_moisture pilihan user di sidebar untuk kebutuhan simulasi interaktif
    final_sheet_moisture = np.clip(0.7 * calculated_moisture + 0.3 * t_moisture, 4.0, 16.0)
    
    # 4. Berat per Bale Finishing Line
    bale_weight = np.random.normal(250.1, 0.3, n_rows) + (final_sheet_moisture - t_moisture) * 0.1
    
    # 5. Konsumsi Energi Spesifik (GJ / Ton Pulp)
    specific_energy = (steam_flow * 2.2) / (production_rate / 24)

    return pd.DataFrame({
        'Timestamp': timestamps,
        'Wire_Speed': w_speed + np.random.normal(0, 1.5, n_rows),
        'Headbox_Consistency': h_consistency + np.random.normal(0, 0.02, n_rows),
        'Steam_Flow_Rate': steam_flow,
        'Steam_Pressure': s_pressure + np.random.normal(0, 0.05, n_rows),
        'Final_Sheet_Moisture': final_sheet_moisture,
        'Production_Rate': production_rate,
        'Bale_Weight': bale_weight,
        'Specific_Energy_Consumption': specific_energy
    })

# Panggil fungsi data secara reaktif
df_master = generate_highly_interactive_dryer_data(
    wire_speed_setpoint, 
    headbox_consistency_setpoint, 
    steam_pressure_setpoint, 
    target_moisture
)

# Filter Berdasarkan Tanggal
if isinstance(date_selection, (list, tuple)) and len(date_selection) == 2:
    df_filtered = df_master[(df_master['Timestamp'].dt.date >= date_selection[0]) & (df_master['Timestamp'].dt.date <= date_selection[1])]
else:
    df_filtered = df_master

# ==============================================================================
# 4. MAIN HEADERS & REACTIVE CONTROL ROOM KPIs
# ==============================================================================
st.title("Pulp Dryer")
st.markdown("Sistem Pemantauan Multivariabel Reaktif: Wet End Drainage, Airborne Thermal Insulation, dan Finishing Line Area.")
st.markdown("---")

latest = df_filtered.iloc[-1]
kpi_cols = st.columns(4)

with kpi_cols[0]:
    m_val = latest['Final_Sheet_Moisture']
    delta_m = m_val - target_moisture
    st.metric(
        label="Final Sheet Moisture", 
        value=f"{m_val:.2f} %", 
        delta=f"{delta_m:+.2f} % vs Target",
        delta_color="inverse" if abs(delta_m) > 0.6 else "normal"
    )
    if abs(delta_m) <= 0.6:
        st.success("MOISTURE QUALITY: PASSED")
    else:
        st.error("MOISTURE QUALITY: REJECT")

with kpi_cols[1]:
    s_val = latest['Steam_Flow_Rate']
    st.metric(
        label="Steam Demand Laju Alir", 
        value=f"{s_val:.1f} Ton/H", 
        delta=f"Press: {latest['Steam_Pressure']:.1f} Bar"
    )
    if s_val < 58.0:
        st.success("ENERGY EFFICIENCY: GREEN")
    else:
        st.warning("ENERGY EFFICIENCY: HIGH LOAD")

with kpi_cols[2]:
    p_val = latest['Production_Rate']
    st.metric(
        label="Total Production Capacity", 
        value=f"{p_val:.0f} ADt/Day", 
        delta=f"Speed: {latest['Wire_Speed']:.0f} m/min"
    )
    st.success("RUNNABILITY: OPTIMAL")

with kpi_cols[3]:
    st.metric(
        label="Specific Energy Index", 
        value=f"{latest['Specific_Energy_Consumption']:.2f} GJ/t", 
        delta="Target < 2.50"
    )
    st.info("OPERATIONAL STATE: LIVE")

# ==============================================================================
# 5. INTEGRATED COMPONENT BREAKDOWN & INTERACTIVE GRAPHICS
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab_wet, tab_dryer, tab_finishing = st.tabs([
    "Wet End Drainage & Former", 
    "Airborne Dryer Box Thermal", 
    "Cutter, Baling & Logistik"
])

# TAB 1: WET END
with tab_wet:
    st.subheader("Dewatering Mekanis & Laju Alir Formers")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        fig_speed = px.line(df_filtered, x='Timestamp', y='Wire_Speed', title="Machine Speed Tracking (m/min) - Mengikuti Slider", color_discrete_sequence=['#10b981'])
        fig_speed.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_speed, use_container_width=True)
    with col_w2:
        fig_const = px.line(df_filtered, x='Timestamp', y='Headbox_Consistency', title="Forming Box Consistency Concentration (%)", color_discrete_sequence=['#3b82f6'])
        fig_const.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_const, use_container_width=True)

# TAB 2: AIRBORNE DRYER (Paling Terlihat Impak Mutlak Kontrol Kustomisasi)
with tab_dryer:
    st.subheader("Simulasi Termodinamika Pengeringan Lembaran")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        fig_moist_chart = go.Figure()
        fig_moist_chart.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Final_Sheet_Moisture'], name='Aktual Moisture Sensor', line=dict(color='#f59e0b', width=2.5)))
        fig_moist_chart.add_hline(y=target_moisture, line=dict(dash="dash", color="#38bdf8", width=2), annotation_text=f"Target Setpoint: {target_moisture}%")
        fig_moist_chart.update_layout(title="Respon Tren Moisture Serat (Bergeser Mengikuti Tekanan Steam & Target Moisture)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_moist_chart, use_container_width=True)
    with col_d2:
        fig_steam_chart = go.Figure()
        fig_steam_chart.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Steam_Flow_Rate'], name='Konsumsi Steam (Ton/Jam)', line=dict(color='#ef4444', width=2)))
        fig_steam_chart.update_layout(title="Dampak Kecepatan Mesin & Target Mutu Terhadap Laju Konsumsi Steam", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_steam_chart, use_container_width=True)

# TAB 3: FINISHING & TONNAGE OUTFLOW
with tab_finishing:
    st.subheader("Kuantitas & Berat Hasil Akhir Pengemasan (Baling Line)")
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        fig_prod = px.area(df_filtered, x='Timestamp', y='Production_Rate', title="Kapasitas Tonase Harian Aktual (Air-Dried Ton / Day)", color_discrete_sequence=['#a855f7'])
        fig_prod.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_prod, use_container_width=True)
    with col_f2:
        fig_energy = px.histogram(df_filtered, x='Specific_Energy_Consumption', title="Distribusi Efisiensi Energi Spesifik (GJ/Ton)", color_discrete_sequence=['#ec4899'])
        fig_energy.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_energy, use_container_width=True)

# ==============================================================================
# 6. MASTER RECTIFIED DATA LOGS & EXPORT
# ==============================================================================
st.markdown("---")
st.subheader("DCS Telemetry Master Data Logs")

st.dataframe(
    df_filtered.sort_values(by='Timestamp', ascending=False),
    use_container_width=True,
    height=250
)

csv_data = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download Master Data Sheet (.csv)",
    data=csv_data,
    file_name=f"PULP_DRYER_OPERATIONAL_LOG.csv",
    mime="text/csv"
)

st.markdown("---")
st.caption("Pulp Drying Advanced Predictive Engineering Matrix v2.5 • Chintya Isya Ababil • Universitas Riau")