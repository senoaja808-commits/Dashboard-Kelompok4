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
    page_title="Water Treatment Plant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme DCS Khas Operator WTP (Aksen Biru Air Bersih / Teal)
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    div[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; }
    .stTabs [aria-selected="true"] { color: #06b6d4 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SIDEBAR CONTROL PANEL (WTP SPECIFIC)
# ==============================================================================
st.sidebar.title("DCS WTP Control Panel")
st.sidebar.markdown("**PIC:** Harits")
st.sidebar.markdown("---")

st.sidebar.subheader("🌊 Intake & Laju Alir Air")
raw_water_inflow = st.sidebar.slider("Raw Water Inflow (m³/Jam)", 500, 2000, 1200, step=50)
raw_turbidity = st.sidebar.slider("Raw Water Turbidity (NTU)", 50, 500, 150, step=10)

st.sidebar.subheader("🧪 Injeksi Bahan Kimia (Chemical Dosing)")
alum_dosage = st.sidebar.slider("Alum Coagulant Dosing (ppm)", 10.0, 50.0, 25.0, step=1.0)
polymer_dosage = st.sidebar.slider("Polymer Flocculant Dosing (ppm)", 0.5, 5.0, 1.8, step=0.1)

# ==============================================================================
# 3. INTERACTIVE WATER PURIFICATION ENGINE (LINKED TO SLIDERS)
# ==============================================================================
def generate_wtp_data(inflow, turbidity, alum, polymer):
    base_end = datetime.now()
    base_start = base_end - timedelta(days=7)
    timestamps = pd.date_range(start=base_start, end=base_end, freq='15min')
    n_rows = len(timestamps)
    
    np.random.seed(111) # Baseline dikunci agar stabil
    
    # 1. Perhitungan Kekeruhan Akhir (Clarified Water Turbidity)
    # Dosing kimia yang pas (Alum & Polymer) akan menurunkan kekeruhan secara eksponensial
    optimum_alum = 15.0 + (turbidity * 0.08)
    alum_error = abs(alum - optimum_alum)
    
    base_clear_turbidity = 2.0 + (turbidity * 0.02) + (alum_error * 0.4) - (polymer * 0.3)
    clarified_turbidity = np.clip(base_clear_turbidity + np.random.normal(0, 0.2, n_rows), 0.5, 15.0)
    
    # 2. Produksi Air Bersih Akhir / Process Water Output (m³/Jam)
    # Ada pengurangan volume akibat pembuangan lumpur pengendapan (sludge blowdown ~3%)
    water_output = inflow * 0.97
    
    # 3. Konsumsi Air Backwash Filter (m³/Jam)
    backwash_flow = 30 + (turbidity * 0.05) + np.random.normal(0, 1, n_rows)
    
    # 4. Nilai pH Air Hasil Olahan
    # Alum bersifat asam, makin tinggi alum dosing tanpa netralisasi, pH akan turun
    calculated_ph = 7.2 - (alum * 0.02) + np.random.normal(0, 0.05, n_rows)
    final_ph = np.clip(calculated_ph, 5.5, 7.8)

    return pd.DataFrame({
        'Timestamp': timestamps,
        'Clarified_Turbidity': clarified_turbidity,
        'Process_Water_Output': water_output + np.random.normal(0, 5, n_rows),
        'Backwash_Flow': backwash_flow,
        'Final_pH': final_ph
    })

# Panggil fungsi kalkulasi data
df_wtp = generate_wtp_data(raw_water_inflow, raw_turbidity, alum_dosage, polymer_dosage)
latest = df_wtp.iloc[-1]

# ==============================================================================
# 4. MAIN HEADERS & METRICS (CONTROL COCKPIT)
# ==============================================================================
st.title("Water Treatment Plant")
st.markdown("Sistem Pemurnian Air Sungai Menjadi Air Proses Berkualitas Tinggi untuk Kebutuhan Operasional Pabrik.")
st.markdown("---")

kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.metric(
        label="Clarified Water Turbidity", 
        value=f"{latest['Clarified_Turbidity']:.2f} NTU",
        delta="Standar Mutu: < 5.0 NTU",
        delta_color="off"
    )
    if latest['Clarified_Turbidity'] <= 5.0:
        st.success("WATER QUALITY: PASS")
    else:
        st.error("WATER QUALITY: HIGH TURBIDITY")

with kpi_cols[1]:
    st.metric(
        label="Total Process Water Supply", 
        value=f"{latest['Process_Water_Output']:.1f} m³/Jam",
        delta="Distribusi Jalur Utama"
    )
    st.success("DISTRIBUTION: STABLE")

with kpi_cols[2]:
    st.metric(
        label="Output Water pH Level", 
        value=f"{latest['Final_pH']:.2f}",
        delta="Ambang Aman: 6.5 - 7.5",
        delta_color="off"
    )
    if 6.5 <= latest['Final_pH'] <= 7.5:
        st.success("CHEMISTRY: NEUTRAL")
    else:
        st.warning("CHEMISTRY: ADJUST pH DOSING")

with kpi_cols[3]:
    st.metric(
        label="Filter Backwash Flow Rate", 
        value=f"{latest['Backwash_Flow']:.1f} m³/Jam",
        delta="Siklus Pembersihan Pasir"
    )
    st.info("FILTRATION: ACTIVE")

# ==============================================================================
# 5. PROCESS TABS & INTERACTIVE PLOTS
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab_clarifier, tab_supply, tab_chemical = st.tabs([
    "Kinerja Penurunan Kekeruhan", 
    "Keseimbangan Suplai Air Proses", 
    "Analisis Tren pH & Kimia"
])

with tab_clarifier:
    st.subheader("Efisiensi Pengendapan Unit Clarifier")
    fig_turb = px.line(df_wtp, x='Timestamp', y='Clarified_Turbidity', title="Kekeruhan Akhir Air Olahan (NTU)", color_discrete_sequence=['#06b6d4'])
    fig_turb.add_hline(y=5.0, line=dict(dash="dash", color="red"), annotation_text="Batas Maksimum Standar")
    fig_turb.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_turb, use_container_width=True)

with tab_supply:
    st.subheader("Kapasitas Suplai Air Bersih Pabrik")
    fig_sup = px.area(df_wtp, x='Timestamp', y='Process_Water_Output', title="Laju Alir Pasokan Air ke Lini Produksi (m³/Jam)", color_discrete_sequence=['#3b82f6'])
    fig_sup.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_sup, use_container_width=True)

with tab_chemical:
    st.subheader("Korelasi Kualitas Kimia Air Olahan")
    fig_ph = go.Figure()
    fig_ph.add_trace(go.Scatter(x=df_wtp['Timestamp'], y=df_wtp['Final_pH'], name='pH Air Akhir', line=dict(color='#10b981', width=2.5)))
    fig_ph.add_trace(go.Scatter(x=df_wtp['Timestamp'], y=df_wtp['Backwash_Flow'], name='Laju Backwash (m³/h)', yaxis='y2', line=dict(color='#f59e0b', width=1.5, dash='dot')))
    
    fig_ph.update_layout(
        title="Dinamika Nilai pH Terhadap Siklus Operasional Filter",
        yaxis=dict(title=dict(text="Skala pH", font=dict(color="#10b981")), tickfont=dict(color="#10b981")),
        yaxis2=dict(title=dict(text="Laju Alir Backwash (m³/Jam)", font=dict(color="#f59e0b")), tickfont=dict(color="#f59e0b"), overlaying='y', side='right'),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_ph, use_container_width=True)

# ==============================================================================
# 6. DATAFRAME LOGS
# ==============================================================================
st.markdown("---")
st.subheader("Water Treatment Sensor Data Logs")
st.dataframe(df_wtp.sort_values(by='Timestamp', ascending=False), use_container_width=True, height=200)

st.markdown("---")
st.caption("WTP Automation & Clarification Module v1.0 • Harits • Universitas Riau")