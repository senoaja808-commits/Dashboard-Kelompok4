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
    page_title="Waste Water Treatment Plant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme DCS Khas Operator WWTP (Aksen Hijau Bio-Eco / Emerald)
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    div[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; }
    .stTabs [aria-selected="true"] { color: #10b981 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SIDEBAR CONTROL PANEL (WWTP SPECIFIC)
# ==============================================================================
st.sidebar.title("DCS WWTP Control Panel")
st.sidebar.markdown("**PIC:** Harits")
st.sidebar.markdown("---")

st.sidebar.subheader("☣️ Beban Air Limbah (Inlet Effluent)")
effluent_inflow = st.sidebar.slider("Wastewater Inflow (m³/Jam)", 800, 2500, 1500, step=50)
inlet_cod = st.sidebar.slider("Inlet COD Concentration (mg/L)", 500, 2000, 1100, step=50)

st.sidebar.subheader("🦠 Parameter Bakteri Aerasi (Activated Sludge)")
aeration_dissolved_o2 = st.sidebar.slider("Aeration DO Level (mg/L)", 0.5, 4.0, 2.0, step=0.1)
nutrient_urea_dosing = st.sidebar.slider("Urea/Nutrient Feed (kg/Jam)", 10.0, 60.0, 35.0, step=1.0)

# ==============================================================================
# 3. INTERACTIVE EFFLUENT BIO-DIGESTION ENGINE (LINKED TO SLIDERS)
# ==============================================================================
def generate_wwtp_data(inflow, cod_in, do, nutrient):
    base_end = datetime.now()
    base_start = base_end - timedelta(days=7)
    timestamps = pd.date_range(start=base_start, end=base_end, freq='15min')
    n_rows = len(timestamps)
    
    np.random.seed(222) # Baseline dikunci stabil
    
    # 1. Perhitungan Efisiensi Degradasi Biologi oleh Bakteri (%). 
    # Bakteri butuh DO ideal (~2.0 mg/L) dan nutrisi seimbang untuk mendegradasi COD.
    do_penalty = abs(do - 2.2) * 15.0
    nutrient_ratio = nutrient / (inflow * (cod_in/1000000.0) + 1)
    nutrient_penalty = abs(nutrient_ratio - 5.0) * 0.2
    
    base_efficiency = 95.0 - do_penalty - nutrient_penalty
    removal_efficiency = np.clip(base_efficiency + np.random.normal(0, 0.5, n_rows), 50.0, 98.5)
    
    # 2. Konsentrasi COD Keluar (Outlet COD) -> Target Lingkungan Pemerintah
    cod_out = cod_in * (1 - (removal_efficiency / 100.0))
    
    # 3. Laju Alir Total Discharge Akhir ke Sungai (m³/Jam)
    discharge_flow = inflow * 0.99 
    
    # 4. Total Suspended Solids Akhir / Final TSS (mg/L)
    # Jika DO terlalu rendah, lumpur aktif lambat mengendap, TSS outlet naik
    base_tss = 15.0 + (3.0 - do) * 8.0 if do < 2.0 else 15.0 + (do - 2.0) * 2.0
    final_tss = np.clip(base_tss + np.random.normal(0, 1, n_rows), 5.0, 80.0)

    return pd.DataFrame({
        'Timestamp': timestamps,
        'Removal_Efficiency': removal_efficiency,
        'Outlet_COD': cod_out,
        'Final_TSS': final_tss,
        'Discharge_Flow': discharge_flow + np.random.normal(0, 3, n_rows)
    })

# Panggil fungsi mesin kalkulasi reaktif
df_wwtp = generate_wwtp_data(effluent_inflow, inlet_cod, aeration_dissolved_o2, nutrient_urea_dosing)
latest = df_wwtp.iloc[-1]

# ==============================================================================
# 4. MAIN HEADERS & METRICS (CONTROL COCKPIT)
# ==============================================================================
st.title("Waste Water Treatment Plant")
st.markdown("Sistem Pemantauan Dekontaminasi Biologi dan Pengolahan Limbah Cair Cairan Sisa Pabrik (*Effluent*).")
st.markdown("---")

kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.metric(
        label="Outlet COD Concentration", 
        value=f"{latest['Outlet_COD']:.1f} mg/L",
        delta="Batas Regulasi: < 100 mg/L",
        delta_color="off"
    )
    if latest['Outlet_COD'] <= 100.0:
        st.success("ENVIRONMENT: SAFE DISCHARGE")
    else:
        st.error("ENVIRONMENT: ILLEGAL OVERFLOW ALERT")

with kpi_cols[1]:
    st.metric(
        label="COD Destruction Efficiency", 
        value=f"{latest['Removal_Efficiency']:.2f} %",
        delta="Kinerja Bakteri Aerob"
    )
    if latest['Removal_Efficiency'] >= 90.0:
        st.success("BIOMASS HEALTH: ACTIVE")
    else:
        st.warning("BIOMASS HEALTH: SLUDGE BULKING")

with kpi_cols[2]:
    st.metric(
        label="Final Total Suspended Solids (TSS)", 
        value=f"{latest['Final_TSS']:.1f} mg/L",
        delta="Batas Regulasi: < 50 mg/L",
        delta_color="off"
    )
    if latest['Final_TSS'] <= 50.0:
        st.success("CLARIFIER: CLEAR WATER")
    else:
        st.warning("CLARIFIER: SOLID CARRYOVER")

with kpi_cols[3]:
    st.metric(
        label="Total Final Discharge Flow", 
        value=f"{latest['Discharge_Flow']:.1f} m³/Jam",
        delta="Menuju Badan Sungai Utama"
    )
    st.info("OUTFALL PUMP: RUNNING")

# ==============================================================================
# 5. PROCESS TABS & INTERACTIVE PLOTS
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab_biology, tab_compliance, tab_solids_f = st.tabs([
    "Kinerja Bio-Degradasi (COD Removal)", 
    "Grafik Kepatuhan Baku Mutu", 
    "Analisis Padatan TSS Terlarut"
])

with tab_biology:
    st.subheader("Efektivitas Dekomposisi Zat Organik")
    fig_bio = px.line(df_wwtp, x='Timestamp', y='Removal_Efficiency', title="Persentase Pemisahan Kandungan Kimia Organik (%)", color_discrete_sequence=['#10b981'])
    fig_bio.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_bio, use_container_width=True)

with tab_compliance:
    st.subheader("Grafik Parameter COD Akhir vs Standar Pemerintah")
    fig_cod = px.area(df_wwtp, x='Timestamp', y='Outlet_COD', title="Kadar COD Air Akhir Olahan (mg/L)", color_discrete_sequence=['#3b82f6'])
    fig_cod.add_hline(y=100, line=dict(dash="dash", color="#ef4444"), annotation_text="Ambang Batas Hukum Lingkungan")
    fig_cod.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_cod, use_container_width=True)

with tab_solids_f:
    st.subheader("Korelasi Padatan Tersuspensi Terhadap Volume Buangan")
    fig_tss = go.Figure()
    fig_tss.add_trace(go.Scatter(x=df_wwtp['Timestamp'], y=df_wwtp['Final_TSS'], name='Kadar TSS (mg/L)', line=dict(color='#f59e0b', width=2.5)))
    fig_tss.add_trace(go.Scatter(x=df_wwtp['Timestamp'], y=df_wwtp['Discharge_Flow'], name='Laju Discharge (m³/h)', yaxis='y2', line=dict(color='#a855f7', width=1.5, dash='dash')))
    
    fig_tss.update_layout(
        title="Dinamika Distribusi TSS Terhadap Laju Alir Outfall",
        yaxis=dict(title=dict(text="TSS (mg/L)", font=dict(color="#f59e0b")), tickfont=dict(color="#f59e0b")),
        yaxis2=dict(title=dict(text="Laju Alir Buangan (m³/Jam)", font=dict(color="#a855f7")), tickfont=dict(color="#a855f7"), overlaying='y', side='right'),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_tss, use_container_width=True)

# ==============================================================================
# 6. DATAFRAME LOGS
# ==============================================================================
st.markdown("---")
st.subheader("WWTP Environmental Compliance Log Records")
st.dataframe(df_wwtp.sort_values(by='Timestamp', ascending=False), use_container_width=True, height=200)

st.markdown("---")
st.caption("Activated Sludge & Effluent Treatment Control Module v1.0 • Harits • Universitas Riau")