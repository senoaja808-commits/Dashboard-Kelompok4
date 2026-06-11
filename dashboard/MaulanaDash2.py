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
    page_title="Recovery Boiler",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme DCS dengan aksen warna Hijau Mint & Oranye Smelt
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    div[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; }
    .stTabs [aria-selected="true"] { color: #00f5d4 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SIDEBAR CONTROL PANEL (RECOVERY BOILER SPECIFIC)
# ==============================================================================
st.sidebar.title("DCS Recovery Boiler")
st.sidebar.markdown("**PIC:** Maulana")
st.sidebar.markdown("---")

st.sidebar.subheader("💧 Karakteristik Black Liquor")
bl_solids = st.sidebar.slider("Black Liquor Dry Solids (%)", 65.0, 85.0, 78.0, step=0.5)
bl_flow = st.sidebar.slider("Black Liquor Flow Rate (Ton/Jam)", 40.0, 120.0, 85.0, step=2.0)

st.sidebar.subheader("💨 Strategi Udara Bertingkat")
primary_air = st.sidebar.slider("Primary Air Flow (Kilosm³/h)", 50.0, 100.0, 75.0, step=1.0)
sootblower_freq = st.sidebar.slider("Sootblower Cycle Frequency (Jam)", 1, 6, 2)

# ==============================================================================
# 3. RECOVERY BOILER CHEMICAL ENGINE (LINKED TO SLIDERS)
# ==============================================================================
def generate_recovery_boiler_data(solids, flow, air, sootfreq):
    base_end = datetime.now()
    base_start = base_end - timedelta(days=7)
    timestamps = pd.date_range(start=base_start, end=base_end, freq='15min')
    n_rows = len(timestamps)
    
    np.random.seed(999) # Mengunci baseline data reaktif
    
    # 1. Efisiensi Termal (Makin tinggi DS/Dry Solids, makin sedikit air yang diuapkan, efisiensi naik)
    base_efficiency = 65.0 + ((solids - 65) * 0.8) - (6 - sootfreq) * 0.5
    efficiency = np.clip(base_efficiency + np.random.normal(0, 0.2, n_rows), 60.0, 85.0)
    
    # 2. Laju Pengosongan Kimia / Smelt Flow Rate (Ton/Jam)
    # Kandungan anorganik dari cairan hitam yang berhasil dicairkan kembali
    base_smelt = flow * (solids / 100.0) * 0.45
    smelt_flow = base_smelt + np.random.normal(0, 0.5, n_rows)
    
    # 3. High Pressure Steam Generation (Ton/Jam)
    base_steam = flow * (solids / 100.0) * 3.1 + (air * 0.1)
    steam_flow = np.clip(base_steam + np.random.normal(0, 1.5, n_rows), 100.0, 450.0)
    
    # 4. Total Tekanan Steam (Bar)
    steam_press = 80 + (solids * 0.1) + np.random.normal(0, 0.3, n_rows)
    
    # 5. Reduksi Efisiensi Kimia / Reduction Efficiency (%)
    # Mengukur seberapa sukses mengubah Na2SO4 menjadi Na2S (Kunci sukses Kraft Process)
    # Udara primer (Primary Air) yang pas menjaga zona reduksi di bawah tungku tetap optimal
    base_reduction = 94.0 + (air * 0.02) if air <= 80 else 96.0 - ((air - 80) * 0.1)
    reduction_efficiency = np.clip(base_reduction + np.random.normal(0, 0.1, n_rows), 88.0, 97.5)

    return pd.DataFrame({
        'Timestamp': timestamps,
        'Dry_Solids': solids + np.random.normal(0, 0.1, n_rows),
        'Steam_Flow': steam_flow,
        'Steam_Pressure': steam_press,
        'Smelt_Flow': smelt_flow,
        'Reduction_Efficiency': reduction_efficiency,
        'Thermal_Efficiency': efficiency
    })

# Jalankan kalkulasi data fiktif reaktif
df_rec = generate_recovery_boiler_data(bl_solids, bl_flow, primary_air, sootblower_freq)
latest = df_rec.iloc[-1]

# ==============================================================================
# 4. MAIN HEADERS & METRICS (CONTROL COCKPIT)
# ==============================================================================
st.title("Recovery Boiler")
st.markdown("Sistem Pemulihan Kimia *Kraft* dan Pembangkitan Uap Tekanan Tinggi dari Pembakaran *Black Liquor*.")
st.markdown("---")

kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.metric(
        label="Chemical Reduction Efficiency", 
        value=f"{latest['Reduction_Efficiency']:.2f} %",
        delta="+0.15% vs Standar" if latest['Reduction_Efficiency'] > 93 else "-0.5% Kritis"
    )
    if latest['Reduction_Efficiency'] >= 92:
        st.success("CHEMICAL LOOP: EXCELLENT")
    else:
        st.error("CHEMICAL LOOP: LOW REDUCTION")

with kpi_cols[1]:
    st.metric(
        label="Smelt Flow Output Rate", 
        value=f"{latest['Smelt_Flow']:.1f} Ton/Jam",
        delta="Menuju Green Liquor Tank",
        delta_color="off"
    )
    st.info("SPOUT SYSTEM: CLEAR")

with kpi_cols[2]:
    st.metric(
        label="High Pressure Steam Flow", 
        value=f"{latest['Steam_Flow']:.1f} Ton/Jam",
        delta=f"Tekanan: {latest['Steam_Pressure']:.1f} Bar"
    )
    st.success("STEAM STATE: STABLE")

with kpi_cols[3]:
    st.metric(
        label="Thermal Efficiency Index", 
        value=f"{latest['Thermal_Efficiency']:.2f} %",
        delta="Dipengaruhi Kandungan Air BL"
    )
    st.info("BOILER RUN: OPTIMAL")

# ==============================================================================
# 5. PROCESS TABS & INTERACTIVE PLOTS
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab_chem, tab_steam_rec, tab_fouling = st.tabs([
    "Siklus Pemulihan Kimia (Smelt)", 
    "Keseimbangan Uap & Energi", 
    "Pengawasan Fouling & Sootblowing"
])

with tab_chem:
    st.subheader("Efisiensi Reduksi & Output Zat Kimia")
    col1, col2 = st.columns(2)
    with col1:
        fig_red = px.line(df_rec, x='Timestamp', y='Reduction_Efficiency', title="Tren Efisiensi Reduksi Na2SO4 -> Na2S (%)", color_discrete_sequence=['#00f5d4'])
        fig_red.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_red, use_container_width=True)
    with col2:
        fig_smelt = px.area(df_rec, x='Timestamp', y='Smelt_Flow', title="Laju Alir Smelt Cair Cairan Masak (Ton/Jam)", color_discrete_sequence=['#ff9f1c'])
        fig_smelt.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_smelt, use_container_width=True)

with tab_steam_rec:
    st.subheader("Produksi Steam Terhadap Pengaruh Dry Solids")
    fig_st_rec = go.Figure()
    fig_st_rec.add_trace(go.Scatter(x=df_rec['Timestamp'], y=df_rec['Steam_Flow'], name='Steam Flow (Ton/Jam)', line=dict(color='#0ea5e9', width=2.5)))
    fig_st_rec.add_trace(go.Scatter(x=df_rec['Timestamp'], y=df_rec['Dry_Solids'], name='Black Liquor Dry Solids (%)', yaxis='y2', line=dict(color='#e11d48', width=1.5, dash='dash')))
    
    fig_st_rec.update_layout(
        title="Dampak Konsentrasi Padatan Kering Terhadap Generasi Energi Uap",
        yaxis=dict(title=dict(text="Laju Alir Steam (Ton/Jam)", font=dict(color="#0ea5e9")), tickfont=dict(color="#0ea5e9")),
        yaxis2=dict(title=dict(text="Dry Solids BL (%)", font=dict(color="#e11d48")), tickfont=dict(color="#e11d48"), overlaying='y', side='right'),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_st_rec, use_container_width=True)

with tab_fouling:
    st.subheader("Efisiensi Termal Akibat Abu Pembakaran (*Ash Carryover*)")
    fig_foul = px.line(df_rec, x='Timestamp', y='Thermal_Efficiency', title="Profil Efisiensi Termal Penukar Panas (%)", color_discrete_sequence=['#a855f7'])
    fig_foul.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_foul, use_container_width=True)

# ==============================================================================
# 6. DATAFRAME LOGS
# ==============================================================================
st.markdown("---")
st.subheader("Recovery Boiler Operational Data Logs")
st.dataframe(df_rec.sort_values(by='Timestamp', ascending=False), use_container_width=True, height=200)

st.markdown("---")
st.caption("Recovery Boiler Industrial Automation Module v1.0 • Maulana • Universitas Riau")