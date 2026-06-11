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
    page_title="Power Boiler",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme DCS Khas Operator Boiler (Aksen Oranye/Api)
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    div[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; }
    .stTabs [aria-selected="true"] { color: #ff914d !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SIDEBAR CONTROL PANEL (POWER BOILER SPECIFIC)
# ==============================================================================
st.sidebar.title("DCS Power Boiler Control")
st.sidebar.markdown("**PIC:** Maulana")
st.sidebar.markdown("---")

st.sidebar.subheader("🔥 Kontrol Pembakaran & Bahan Bakar")
biomass_feed = st.sidebar.slider("Biomass (Bark/Wood) Feed Rate (Ton/Jam)", 30.0, 80.0, 55.0, step=2.0)
coal_infusion = st.sidebar.slider("Coal (Batu Bara) Support Rate (Ton/Jam)", 5.0, 30.0, 12.0, step=1.0)

st.sidebar.subheader("💨 Parameter Udara & Air Umpan")
air_fuel_ratio = st.sidebar.slider("Air-to-Fuel Ratio (O2 Trim)", 1.5, 4.0, 2.5, step=0.1)
feedwater_temp = st.sidebar.slider("Feedwater Inlet Temp (°C)", 110.0, 150.0, 130.0, step=2.0)

# ==============================================================================
# 3. INTERACTIVE BOILER THERMODYNAMICS ENGINE (LINKED TO SLIDERS)
# ==============================================================================
def generate_power_boiler_data(biomass, coal, afr, fw_temp):
    base_end = datetime.now()
    base_start = base_end - timedelta(days=7)
    timestamps = pd.date_range(start=base_start, end=base_end, freq='15min')
    n_rows = len(timestamps)
    
    np.random.seed(888) # Dikunci agar baseline stabil, pergeseran murni dari slider
    
    # Total Panas Masuk (Coal punya nilai kalor lebih tinggi dari Biomass)
    heat_input = (biomass * 3.5) + (coal * 6.0) 
    
    # Temperatur Ruang Bakar (Furnace Temperature)
    base_furnace_temp = 850 + (heat_input * 1.5) - (afr * 25)
    furnace_temp = base_furnace_temp + np.random.normal(0, 8, n_rows)
    
    # Laju Produksi Steam (Ton/Jam)
    base_steam_flow = (heat_input * 0.85) + (fw_temp - 130) * 0.3
    steam_flow = np.clip(base_steam_flow + np.random.normal(0, 2, n_rows), 50.0, 250.0)
    
    # Tekanan Steam Utama (Main Steam Pressure - Bar)
    steam_pressure = np.clip(90 + (steam_flow * 0.1) + np.random.normal(0, 0.5, n_rows), 60.0, 130.0)
    
    # Efisiensi Boiler (%) 
    afr_loss = abs(afr - 2.6) * 3.0
    boiler_efficiency = np.clip(88.0 - afr_loss - (biomass*0.05) + np.random.normal(0, 0.2, n_rows), 70.0, 92.0)
    
    # Emisi Gas Buang (SOx)
    sox_emission = (coal * 4.5) - (afr * 2) + np.random.normal(0, 1, n_rows)

    return pd.DataFrame({
        'Timestamp': timestamps,
        'Biomass_Feed': biomass + np.random.normal(0, 0.5, n_rows),
        'Coal_Feed': coal + np.random.normal(0, 0.2, n_rows),
        'Furnace_Temperature': furnace_temp,
        'Main_Steam_Flow': steam_flow,
        'Main_Steam_Pressure': steam_pressure,
        'Boiler_Efficiency': boiler_efficiency,
        'SOx_Emission': sox_emission
    })

# Panggil mesin data reaktif
df_boiler = generate_power_boiler_data(biomass_feed, coal_infusion, air_fuel_ratio, feedwater_temp)
latest = df_boiler.iloc[-1]

# ==============================================================================
# 4. MAIN HEADERS & METRICS (CONTROL COCKPIT)
# ==============================================================================
st.title("Power Boiler")
st.markdown("Sistem Pengawasan Pembakaran Biomass & Batu Bara untuk Suplai Energi Turbin Uap Utama.")
st.markdown("---")

kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.metric(
        label="Main Steam Flow Rate", 
        value=f"{latest['Main_Steam_Flow']:.1f} Ton/Jam",
        delta=f"Press: {latest['Main_Steam_Pressure']:.1f} Bar"
    )
    st.success("STEAM SUPPLY: STABLE")

with kpi_cols[1]:
    st.metric(
        label="Furnace Bed Temperature", 
        value=f"{latest['Furnace_Temperature']:.1f} °C",
        delta="Target: 900 - 1050 °C",
        delta_color="off"
    )
    if 900 <= latest['Furnace_Temperature'] <= 1050:
        st.success("THERMAL STATE: OPTIMAL")
    else:
        st.warning("THERMAL STATE: ATTENTION")

with kpi_cols[2]:
    eff_val = latest['Boiler_Efficiency']
    st.metric(
        label="Thermal Efficiency Index", 
        value=f"{eff_val:.2f} %",
        delta="-0.4% vs Shift Lalu" if eff_val < 85 else "+0.8% Optimal"
    )
    st.info("COMBUSTION: EVALUATED")

with kpi_cols[3]:
    st.metric(
        label="SOx Environmental Flue Gas", 
        value=f"{latest['SOx_Emission']:.1f} mg/Nm³",
        delta="Ambang Batas: 200",
        delta_color="inverse" if latest['SOx_Emission'] > 150 else "normal"
    )
    st.success("EMISSION: COMPLIANT")

# ==============================================================================
# 5. PROCESS TABS & INTERACTIVE PLOTS
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab_combustion, tab_steam, tab_emission = st.tabs([
    "Sistem Pembakaran Tungku", 
    "Sirkulasi Steam & Air Umpan", 
    "Analisis Emisi Gas Buang"
])

with tab_combustion:
    st.subheader("Kondisi Termal Ruang Bakar (Furnace)")
    col1, col2 = st.columns(2)
    with col1:
        fig_temp = px.line(df_boiler, x='Timestamp', y='Furnace_Temperature', title="Tren Temperatur Bed Tungku Utama (°C)", color_discrete_sequence=['#ff6b35'])
        fig_temp.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_temp, use_container_width=True)
    with col2:
        fig_eff = px.line(df_boiler, x='Timestamp', y='Boiler_Efficiency', title="Efisiensi Pembakaran Real-time (%)", color_discrete_sequence=['#10b981'])
        fig_eff.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_eff, use_container_width=True)

with tab_steam:
    st.subheader("Produksi Energi Uap Bertekanan Tinggi")
    fig_steam = go.Figure()
    fig_steam.add_trace(go.Scatter(x=df_boiler['Timestamp'], y=df_boiler['Main_Steam_Flow'], name='Steam Flow (Ton/H)', line=dict(color='#0ea5e9', width=2.5)))
    fig_steam.add_trace(go.Scatter(x=df_boiler['Timestamp'], y=df_boiler['Main_Steam_Pressure'], name='Main Steam Pressure (Bar)', yaxis='y2', line=dict(color='#a855f7', width=1.5, dash='dot')))
    
    # Pembaruan struktur penulisan properti sumbu sesuai rekomendasi error Plotly
    fig_steam.update_layout(
        title="Korelasi Laju Alir Uap Terhadap Tekanan Kerja Header",
        yaxis=dict(
            title=dict(text="Laju Alir Steam (Ton/Jam)", font=dict(color="#0ea5e9")), 
            tickfont=dict(color="#0ea5e9")
        ),
        yaxis2=dict(
            title=dict(text="Tekanan Uap (Bar)", font=dict(color="#a855f7")), 
            tickfont=dict(color="#a855f7"), 
            overlaying='y', 
            side='right'
        ),
        template="plotly_dark", 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_steam, use_container_width=True)

with tab_emission:
    st.subheader("Kepatuhan Lingkungan (Flue Gas Analyzer)")
    fig_em = px.area(df_boiler, x='Timestamp', y='SOx_Emission', title="Kadar Emisi SOx di Cerobong (mg/Nm³)", color_discrete_sequence=['#ef4444'])
    fig_em.add_hline(y=150, line=dict(dash="dash", color="yellow"), annotation_text="Batas Aman Internal")
    fig_em.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_em, use_container_width=True)

# ==============================================================================
# 6. RECTIFIED DATAFRAME LOGS
# ==============================================================================
st.markdown("---")
st.subheader("Power Boiler Sensor Data Logs")
st.dataframe(df_boiler.sort_values(by='Timestamp', ascending=False), use_container_width=True, height=200)

st.markdown("---")
st.caption("Power Boiler Utility Automation Module v1.0 • Maulana • Universitas Riau")