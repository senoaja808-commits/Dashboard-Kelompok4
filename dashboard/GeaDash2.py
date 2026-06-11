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
    page_title="Viscose Machine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme DCS Viscose Machine Control Interface Professional
st.markdown("""
    <style>
    .main { background-color: #060913; color: #cbd5e1; font-family: 'Consolas', monospace; }
    div[data-testid="stSidebar"] { background-color: #0c111d; border-right: 2px solid #06b6d4; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; font-size: 15px; }
    .stTabs [aria-selected="true"] { color: #06b6d4 !important; font-weight: bold; border-bottom-color: #06b6d4 !important; }
    .status-card { padding: 12px; border-radius: 6px; text-align: center; font-weight: bold; font-family: monospace; }
    .data-card { background-color: #0f172a; border: 1px solid #1e293b; padding: 15px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DYNAMIC OPERATIONAL CONTROL ROOM (SIDEBAR CONSOLE)
# ==============================================================================
st.sidebar.title("🎛️ DCS CONTROL PANEL")
st.sidebar.markdown("**PIC:** Sri Wahyuni Gea")
st.sidebar.markdown("**Operational Department:** Viscose Preparation Division")
st.sidebar.markdown("---")

st.sidebar.subheader("🎯 Viscose Dope Quality Targets")
target_viscosity = st.sidebar.slider("Target Viscosity (Poise)", 30.0, 70.0, 48.0, step=0.5)
target_ripening = st.sidebar.slider("Target Ripening Index (Hottenroth)", 9.0, 15.0, 11.5, step=0.1)

st.sidebar.subheader("🧪 Xanthation & Alkallization Reactor")
cs2_dosing = st.sidebar.slider("CS2 Charge Ratio (% on Cellulose)", 28.0, 38.0, 32.5, step=0.5)
steeping_naoh = st.sidebar.slider("Steeping Lye NaOH Conc (%)", 16.0, 22.0, 18.5, step=0.1)
ripening_temp = st.sidebar.slider("Ripening Room Temp (°C)", 15.0, 30.0, 19.5, step=0.5)

st.sidebar.subheader("⚙️ Blending & Filtration Mechanics")
blender_rpm = st.sidebar.slider("Homogenizer Blender Speed (RPM)", 200, 600, 450, step=10)
filter_press_limit = st.sidebar.slider("Max Filter Differential Pressure (Bar)", 1.0, 5.0, 3.2, step=0.1)

st.sidebar.subheader("📅 SCADA Data Range Filter")
base_end = datetime.now()
base_start = base_end - timedelta(days=7)
date_selection = st.sidebar.date_input(
    "Sensor Timestamp Filter", 
    value=[base_start.date(), base_end.date()], 
    min_value=base_start.date(), 
    max_value=base_end.date()
)

# ==============================================================================
# 3. INTERACTIVE SIMULATION ENGINE (VISCOSE DOPE BIO-CHEMICAL KINETICS)
# ==============================================================================
def generate_viscose_machine_data(t_visc, t_ripe, cs2, naoh, temp, rpm, p_filter):
    timestamps = pd.date_range(start=base_start, end=base_end, freq='15min')
    n_rows = len(timestamps)
    
    np.random.seed(202) 
    
    # Area 1: Steeping & Dissolving Feedrate
    pulp_feed = np.random.normal(12.5, 0.3, n_rows)
    dissolving_water = pulp_feed * np.random.normal(7.8, 0.1, n_rows)
    
    # Area 2: Xanthation & Ripening Kinetics
    # Indeks kematangan dipengaruhi oleh suhu ruangan ripening dan konsentrasi NaOH alkali
    actual_ripening = np.clip(
        t_ripe + np.random.normal(0, 0.1, n_rows) - (temp - 19.5) * 0.15 + (naoh - 18.5) * 0.2,
        6.0, 18.0
    )
    
    # Viskositas fluida dibentuk oleh rasio blending CS2 dan putaran pengaduk homogenizer
    actual_viscosity = np.clip(
        t_visc + np.random.normal(0, 0.4, n_rows) + (cs2 - 32.5) * 0.8 - (rpm - 450) * 0.03,
        20.0, 90.0
    )
    
    # Area 3: Filtration Pressure Drop
    # Jika viskositas terlalu kental, tekanan pada filter press naik mendekati limit breakout
    viscosity_deviation = max(0, actual_viscosity.mean() - 50)
    actual_dp = np.clip(
        1.8 + np.random.normal(0, 0.08, n_rows) + (viscosity_deviation * 0.05),
        0.2, 6.0
    )
    
    # Total Dope Yield Output Volume (m3/h)
    dope_production = (pulp_feed * (naoh/100) * 3.5) + (dissolving_water * 0.9)

    return pd.DataFrame({
        'Timestamp': timestamps,
        'Pulp_Feed_Rate': pulp_feed,
        'Dissolving_Water_Flow': dissolving_water,
        'NaOH_Concentration': np.full(n_rows, naoh) + np.random.normal(0, 0.05, n_rows),
        'CS2_Dosing_Rate': np.full(n_rows, cs2) + np.random.normal(0, 0.1, n_rows),
        'Ripening_Temperature': np.full(n_rows, temp) + np.random.normal(0, 0.15, n_rows),
        'Blender_Speed_RPM': np.full(n_rows, rpm) + np.random.normal(0, 2, n_rows),
        'Actual_Ripening_Index': actual_ripening,
        'Actual_Viscosity': actual_viscosity,
        'Filter_Differential_Pressure': actual_dp,
        'Viscose_Dope_Production': dope_production
    })

# Sinkronisasi Engine Data dengan Nilai Input Slider
df_master = generate_viscose_machine_data(
    target_viscosity, target_ripening, cs2_dosing, steeping_naoh, ripening_temp, blender_rpm, filter_press_limit
)

# Filter Kalender
if isinstance(date_selection, (list, tuple)) and len(date_selection) == 2:
    df_filtered = df_master[(df_master['Timestamp'].dt.date >= date_selection[0]) & (df_master['Timestamp'].dt.date <= date_selection[1])]
else:
    df_filtered = df_master

latest = df_filtered.iloc[-1]

# ==============================================================================
# 4. MAIN HEADERS & REAL-TIME DCS MONITORING SYSTEM
# ==============================================================================
st.title("VISCOSE MACHINE")
st.markdown("Sistem Pengawasan Terintegrasi: Wood Pulp Steeping, Xanthation Reactor, Vacuum Ripening, dan Stage Filtration System.")
st.markdown("---")

# Lini Metrik Utama (DCS Panel Style - Unsur Warna Cyan Khas Pabrik Kimia Hulu)
kpi_cols = st.columns(5)

with kpi_cols[0]:
    v_visc = latest['Actual_Viscosity']
    v_ripe = latest['Actual_Ripening_Index']
    v_dp = latest['Filter_Differential_Pressure']
    
    # Logika Interlock Keselamatan Proses Viscose:
    # Aman jika viskositas normal dan tekanan filter press tidak melebihi limit mekanis
    is_viscosity_ok = abs(v_visc - target_viscosity) <= 3.0
    is_pressure_ok = v_dp <= filter_press_limit
    
    if is_viscosity_ok and is_pressure_ok:
        st.markdown("<div class='status-card' style='background-color:#083344; color:#22d3ee; border:1px solid #06b6d4;'>PROCESS: OPTIMAL</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-card' style='background-color:#450a0a; color:#f87171; border:1px solid #dc2626;'>PROCESS: WARNING</div>", unsafe_allow_html=True)

with kpi_cols[1]:
    st.metric(
        label="Dope Viscosity", 
        value=f"{v_visc:.2f} Poise", 
        delta=f"{(v_visc - target_viscosity):+.2f} vs Target",
        delta_color="normal" if abs(v_visc - target_viscosity) <= 3.0 else "inverse"
    )

with kpi_cols[2]:
    st.metric(
        label="Ripening Index", 
        value=f"{v_ripe:.1f} °H", 
        delta=f"{(v_ripe - target_ripening):+.1f} vs Target"
    )

with kpi_cols[3]:
    st.metric(
        label="Filter Press DP", 
        value=f"{v_dp:.2f} Bar", 
        delta=f"{(v_dp - filter_press_limit):+.2f} vs Limit",
        delta_color="inverse" if v_dp > filter_press_limit else "normal"
    )

with kpi_cols[4]:
    st.metric(label="Viscose Dope Outflow", value=f"{latest['Viscose_Dope_Production']:.2f} m³/h", delta=f"Pulp: {latest['Pulp_Feed_Rate']:.1f} t/h")

# ==============================================================================
# 5. DIAGRAM DAN HISTOGRAM ANALISIS SUBSISTEM
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab_alkali, tab_xanthation, tab_filtration, tab_mass_balance = st.tabs([
    "🧪 Alkallization Room", 
    "⚗️ Xanthation & Ripening", 
    "🌀 Fine Filtration Press", 
    "📊 Dope Mass Balance Audit"
])

# ---- TAB 1: ALKALLIZATION ROOM ----
with tab_alkali:
    st.subheader("Pengendalian Mutu Penghancuran Selulosa Mentah & Konsentrasi Lye")
    col_a1, col_a2 = st.columns([2, 1])
    with col_a1:
        fig_pulp = px.line(df_filtered, x='Timestamp', y='Pulp_Feed_Rate', title="Laju Aliran Pengumpanan Wood Pulp Mentah (Tons/Hour)", color_discrete_sequence=['#06b6d4'])
        fig_pulp.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pulp, use_container_width=True)
    with col_a2:
        fig_naoh = px.histogram(df_filtered, x='NaOH_Concentration', title="Variasi Densitas Larutan Akali NaOH (%)", color_discrete_sequence=['#22d3ee'])
        fig_naoh.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_naoh, use_container_width=True)

# ---- TAB 2: XANTHATION & RIPENING ----
with tab_xanthation:
    st.subheader("Tren Termal Reaktor Xanthation & Indeks Kematangan Selulosa")
    fig_xanth = go.Figure()
    fig_xanth.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Actual_Ripening_Index'], name='Ripening Index (°H)', line=dict(color='#22c55e', width=2.5)))
    fig_xanth.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Ripening_Temperature'], name='Ripening Room Temp (°C)', yaxis='y2', line=dict(color='#eab308', width=1.5, dash='dash')))
    
    fig_xanth.update_layout(
        title="Korelasi Pengaruh Suhu Ruangan Terhadap Kecepatan Pematangan Cairan Dope",
        yaxis=dict(title=dict(text="Ripening Index (Hottenroth Degrees)", font=dict(color="#22c55e")), tickfont=dict(color="#22c55e")),
        yaxis2=dict(title=dict(text="Reactor Temperature (°C)", font=dict(color="#eab308")), tickfont=dict(color="#eab308"), overlaying='y', side='right'),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_xanth, use_container_width=True)

# ---- TAB 3: FINE FILTRATION PRESS ----
with tab_filtration:
    st.subheader("Analisis Delta Tekanan Penyaringan & Indeks Viskositas")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        fig_visc = go.Figure()
        fig_visc.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Actual_Viscosity'], name='Actual Viscosity', line=dict(color='#a855f7', width=2.5)))
        fig_visc.add_hline(y=target_viscosity, line=dict(dash="dot", color="#06b6d4"), annotation_text=f"Target: {target_viscosity} Poise")
        fig_visc.update_layout(title="Kekentalan Cairan Viscose Dope Sebelum Spinning", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_visc, use_container_width=True)
    with col_f2:
        fig_dp = go.Figure()
        fig_dp.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Filter_Differential_Pressure'], name='Filter DP', line=dict(color='#f43f5e', width=2)))
        fig_dp.add_hline(y=filter_press_limit, line=dict(dash="dot", color="#f43f5e"), annotation_text=f"Max Limit: {filter_press_limit} Bar")
        fig_dp.update_layout(title="Differential Pressure Drop Filter Press (Indikator Sumbatan Blockage)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_dp, use_container_width=True)

# ---- TAB 4: DOPE MASS BALANCE AUDIT ----
with tab_mass_balance:
    st.subheader("Neraca Massa Pembentukan Larutan Viskos Cair Tekstil")
    col_bal1, col_bal2 = st.columns(2)
    
    with col_bal1:
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.markdown("<h4>📋 Chemical Feed Inputs</h4>", unsafe_allow_html=True)
        st.write(f"• Konsentrasi Umpan Wood Pulp Padat: **{latest['Pulp_Feed_Rate']:.2f} Ton/Jam**")
        st.write(f"• Air Pelarut (*Dissolving Soft Water*): **{latest['Dissolving_Water_Flow']:.2f} m³/Jam**")
        st.write(f"• Rasio Penambahan Gas Karbon Disulfida ($CS_2$): **{latest['CS2_Dosing_Rate']:.2f} %**")
        st.write(f"• Putaran Motor Mixer Homogenizer: **{latest['Blender_Speed_RPM']:.0f} RPM**")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_bal2:
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.markdown("<h4>📊 Viscose Dope Output Quality Evaluation</h4>", unsafe_allow_html=True)
        st.write(f"• Kandungan Lye Sellulose Alkali: **{latest['NaOH_Concentration']:.2f} %**")
        st.write(f"• Viskositas Akhir Cairan Dope: **{latest['Actual_Viscosity']:.2f} Poise**")
        st.write(f"• Indeks Pematangan Termal Tangki Vacuum: **{latest['Actual_Ripening_Index']:.2f} Hottenroth (°H)**")
        st.write(f"• Output Aliran Bersih Cairan Viscose Siap Kirim: **{latest['Viscose_Dope_Production']:.2f} m³/Jam**")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    fig_prod_area = px.area(df_filtered, x='Timestamp', y='Viscose_Dope_Production', title="Tren Akumulasi Laju Aliran Akumulatif Hasil Viscose Dope (m³/h)", color_discrete_sequence=['#06b6d4'])
    fig_prod_area.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_prod_area, use_container_width=True)

# ==============================================================================
# 6. SERVER DATAFRAME STORAGE LOGS
# ==============================================================================
st.markdown("---")
st.subheader("📋 Core Data Historian Sensor Database Registry Log")
st.dataframe(df_filtered.sort_values(by='Timestamp', ascending=False), use_container_width=True, height=220)

st.markdown("---")
st.caption("Advanced Industrial Viscose Machine SCADA Engine v2.0 • Sri Wahyuni Gea • Universitas Riau")