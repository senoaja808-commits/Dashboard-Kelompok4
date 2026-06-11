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
    page_title="Yarn Machine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme DCS Yarn Machine Control Interface Professional
st.markdown("""
    <style>
    .main { background-color: #060913; color: #cbd5e1; font-family: 'Consolas', monospace; }
    div[data-testid="stSidebar"] { background-color: #0c111d; border-right: 2px solid #a855f7; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; font-size: 15px; }
    .stTabs [aria-selected="true"] { color: #a855f7 !important; font-weight: bold; border-bottom-color: #a855f7 !important; }
    .status-card { padding: 12px; border-radius: 6px; text-align: center; font-weight: bold; font-family: monospace; }
    .data-card { background-color: #0f172a; border: 1px solid #1e293b; padding: 15px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DYNAMIC OPERATIONAL CONTROL ROOM (SIDEBAR CONSOLE)
# ==============================================================================
st.sidebar.title("🎛️ DCS CONTROL PANEL")
st.sidebar.markdown("**PIC:** Sri Wahyuni Gea")
st.sidebar.markdown("**Operational Department:** Spinning Division")
st.sidebar.markdown("---")

st.sidebar.subheader("🎯 Yarn Quality Specification Targets")
target_tenacity = st.sidebar.slider("Target Tenacity (cN/tex)", 15.0, 35.0, 24.5, step=0.5)
max_broken_filaments = st.sidebar.slider("Max Broken Filaments Allowance", 1.0, 10.0, 3.5, step=0.1)

st.sidebar.subheader("🧪 Spinning Bath Formulation")
h2so4_conc = st.sidebar.slider("H2SO4 Acid Concentration (g/L)", 110.0, 150.0, 130.0, step=1.0)
znso4_conc = st.sidebar.slider("ZnSO4 Salt Concentration (g/L)", 10.0, 20.0, 15.0, step=0.5)
bath_temperature = st.sidebar.slider("Spinning Bath Temp (°C)", 40.0, 60.0, 48.0, step=0.5)

st.sidebar.subheader("⚙️ Kinematic Controls")
takeup_speed = st.sidebar.slider("Take-up Godet Speed (m/min)", 50.0, 120.0, 85.0, step=1.0)
stretch_ratio = st.sidebar.slider("Filament Stretch Ratio (%)", 40.0, 90.0, 65.0, step=1.0)

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
# 3. INTERACTIVE SIMULATION ENGINE (FIXED YARN SPINNING KINETICS)
# ==============================================================================
def generate_yarn_machine_data(t_tenacity, m_broken, h2so4, znso4, temp, speed, stretch):
    timestamps = pd.date_range(start=base_start, end=base_end, freq='15min')
    n_rows = len(timestamps)
    
    np.random.seed(101) 
    
    # Area 1: Viscose Dope Supply
    viscose_flow = np.random.normal(42.5, 0.8, n_rows) + (speed * 0.1)
    viscose_cellulose_content = np.random.normal(9.2, 0.1, n_rows)
    dry_cellulose_feed = viscose_flow * (viscose_cellulose_content / 100) * 60 # kg/h
    
    # Area 2: Spinning Bath Coagulation Kinetics
    na2so4_generated = np.random.normal(280.0, 2.0, n_rows) + (h2so4 * 0.2)
    decomposition_index = (h2so4 / 130.0) * (temp / 48.0) + np.random.normal(0, 0.02, n_rows)
    
    # Area 3: Filament Stretching & Mechanics
    actual_tenacity = np.clip(
        t_tenacity + np.random.normal(0.1, 0.12, n_rows) + (stretch - 65) * 0.08 + (znso4 - 15.0) * 0.15, 
        12.0, 40.0
    )
    
    acid_deviation = abs(h2so4 - 130.0)
    actual_broken = np.clip(
        2.1 + np.random.normal(0, 0.15, n_rows) + (speed - 85) * 0.05 + (acid_deviation * 0.08) - (znso4 - 15) * 0.05, 
        0.2, 15.0
    )
    
    # Produksi Benang Neto (Yarn Production Output)
    yarn_output_tpd = (dry_cellulose_feed * 24) / 1000.0 # Metric Tons/Day

    return pd.DataFrame({
        'Timestamp': timestamps,
        'Viscose_Dope_Flow': viscose_flow,
        'Cellulose_Content': viscose_cellulose_content,
        'Dry_Cellulose_Feed': dry_cellulose_feed,
        'H2SO4_Concentration': np.full(n_rows, h2so4) + np.random.normal(0, 0.4, n_rows),
        'ZnSO4_Concentration': np.full(n_rows, znso4) + np.random.normal(0, 0.1, n_rows),
        'Na2SO4_Concentration': na2so4_generated,
        'Bath_Temperature': np.full(n_rows, temp) + np.random.normal(0, 0.2, n_rows),
        'Decomposition_Index': decomposition_index,
        'Takeup_Speed': np.full(n_rows, speed) + np.random.normal(0, 0.3, n_rows),
        'Stretch_Ratio': np.full(n_rows, stretch),
        'Actual_Tenacity': actual_tenacity,
        'Broken_Filaments': actual_broken,
        'Yarn_Production_TPD': yarn_output_tpd
    })

# Sinkronisasi Engine Data dengan Nilai Input Slider
df_master = generate_yarn_machine_data(
    target_tenacity, max_broken_filaments, h2so4_conc, znso4_conc, bath_temperature, takeup_speed, stretch_ratio
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
st.title("YARN MACHINE")
st.markdown("Sistem Pengawasan Terintegrasi: Viscose Dope Extrusion, Acid Regeneration Spinning Bath, dan Filament Take-up Stretching.")
st.markdown("---")

# Lini Metrik Utama
kpi_cols = st.columns(5)

with kpi_cols[0]:
    y_ten = latest['Actual_Tenacity']
    y_brok = latest['Broken_Filaments']
    
    is_tenacity_ok = y_ten >= (target_tenacity - 0.2)
    is_broken_ok = y_brok <= max_broken_filaments
    
    if is_tenacity_ok and is_broken_ok:
        st.markdown("<div class='status-card' style='background-color:#1e1b4b; color:#c084fc; border:1px solid #a855f7;'>QUALITY: OPTIMAL</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-card' style='background-color:#450a0a; color:#f87171; border:1px solid #dc2626;'>QUALITY: OFF-SPEC</div>", unsafe_allow_html=True)

with kpi_cols[1]:
    st.metric(
        label="Yarn Tenacity Strength", 
        value=f"{y_ten:.2f} cN/tex", 
        delta=f"{(y_ten - target_tenacity):+.2f} vs Target",
        delta_color="normal" if y_ten >= target_tenacity else "inverse"
    )

with kpi_cols[2]:
    st.metric(
        label="Broken Filaments Counter", 
        value=f"{y_brok:.2f} pcs", 
        delta=f"{(y_brok - max_broken_filaments):+.2f} vs Limit",
        delta_color="inverse" if y_brok > max_broken_filaments else "normal"
    )

with kpi_cols[3]:
    st.metric(label="Spinning Take-up Speed", value=f"{latest['Takeup_Speed']:.1f} m/min", delta=f"Stretch: {latest['Stretch_Ratio']:.0f}%")

with kpi_cols[4]:
    st.metric(label="Total Yarn Production", value=f"{latest['Yarn_Production_TPD']:.2f} t/d", delta=f"Dope: {latest['Viscose_Dope_Flow']:.1f} m³/h")

# ==============================================================================
# 5. DIAGRAM DAN HISTOGRAM ANALISIS SUBSISTEM
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab_dope, tab_bath, tab_kinematics, tab_balance = st.tabs([
    "🌀 Viscose Feeding Control", 
    "🧪 Acid Coagulation Bath", 
    "⚡ Godet Take-up Mechanicals", 
    "📊 Yarn Mass Balance Audit"
])

# ---- TAB 1: VISCOSE FEEDING CONTROL ----
with tab_dope:
    st.subheader("Manajemen Aliran Masuk Bahan Baku Cairan Viscose (Dope)")
    col_d1, col_d2 = st.columns([2, 1])
    with col_d1:
        fig_dope = px.line(df_filtered, x='Timestamp', y='Viscose_Dope_Flow', title="Laju Aliran Injeksi Viscose ke Spinneret (m³/h)", color_discrete_sequence=['#c084fc'])
        fig_dope.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_dope, use_container_width=True)
    with col_d2:
        fig_content = px.histogram(df_filtered, x='Cellulose_Content', title="Variasi Kandungan Selulosa dalam Dope (%)", color_discrete_sequence=['#e879f9'])
        fig_content.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_content, use_container_width=True)

# ---- TAB 2: ACID COAGULATION BATH ----
with tab_bath:
    st.subheader("Konsentrasi Kimia & Regenerasi Larutan Asam Bak Putar")
    fig_bath = go.Figure()
    fig_bath.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['H2SO4_Concentration'], name='H2SO4 Acid (g/L)', line=dict(color='#ef4444', width=2.5)))
    fig_bath.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Na2SO4_Concentration'], name='Na2SO4 Salt (g/L)', yaxis='y2', line=dict(color='#3b82f6', width=1.5, dash='dash')))
    fig_bath.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['ZnSO4_Concentration'], name='ZnSO4 Salt (g/L)', line=dict(color='#eab308', width=2)))
    
    fig_bath.update_layout(
        title="Profil Komposisi Kimia Cairan Spinning Bath untuk Desantofikasi Selulosa",
        yaxis=dict(title=dict(text="H2SO4 & ZnSO4 Concentration (g/L)", font=dict(color="#ffffff")), tickfont=dict(color="#ffffff")),
        yaxis2=dict(title=dict(text="Na2SO4 Salt Buffer (g/L)", font=dict(color="#3b82f6")), tickfont=dict(color="#3b82f6"), overlaying='y', side='right'),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_bath, use_container_width=True)

# ---- TAB 3: GODET TAKE-UP MECHANICALS ----
with tab_kinematics:
    st.subheader("Analisis Mekanik Regangan Serat & Defect Filamen")
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        fig_tenacity = go.Figure()
        fig_tenacity.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Actual_Tenacity'], name='Actual Yarn Tenacity', line=dict(color='#22c55e', width=2.5)))
        fig_tenacity.add_hline(y=target_tenacity, line=dict(dash="dot", color="#c084fc"), annotation_text=f"Target: {target_tenacity} cN/tex")
        fig_tenacity.update_layout(title="Kekuatan Mekanis Serat Benang Rayon Aktual", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_tenacity, use_container_width=True)
    with col_k2:
        fig_broken = go.Figure()
        fig_broken.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Broken_Filaments'], name='Broken Filaments Rate', line=dict(color='#f43f5e', width=2)))
        fig_broken.add_hline(y=max_broken_filaments, line=dict(dash="dot", color="#f43f5e"), annotation_text=f"Max Limit: {max_broken_filaments}")
        fig_broken.update_layout(title="Laju Deteksi Cacat Benang (Broken Filaments)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_broken, use_container_width=True)

# ---- TAB 4: YARN MASS BALANCE AUDIT ----
with tab_balance:
    st.subheader("Neraca Massa Transformasi Cairan Viscose Menjadi Benang Padat")
    col_bal1, col_bal2 = st.columns(2)
    
    with col_bal1:
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.markdown("<h4>📋 Fluid Mechanical Feed Balance</h4>", unsafe_allow_html=True)
        st.write(f"• Total Umpan Cairan Viscose Dope: **{latest['Viscose_Dope_Flow']:.2f} m³/h**")
        st.write(f"• Konsentrasi Selulosa Murni dalam Dope: **{latest['Cellulose_Content']:.2f} %**")
        st.write(f"• Laju Aliran Selulosa Kering Neto: **{latest['Dry_Cellulose_Feed']:.2f} kg/hour**")
        st.write(f"• Suhu Operasional Bak Reaktor Asam: **{latest['Bath_Temperature']:.2f} °C**")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_bal2:
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.markdown("<h4>📊 Production Output Audit</h4>", unsafe_allow_html=True)
        st.write(f"• Setpoint Rasio Regangan Mekanis (Stretch): **{stretch_ratio} %**")
        st.write(f"• Indeks Efisiensi Desantofikasi Reaktor: **{latest['Decomposition_Index']:.3f} (Normal: 0.95 - 1.15)**")
        st.write(f"• Proyeksi Output Produksi Benang Utama: **{latest['Yarn_Production_TPD']:.2f} Metric Ton / Hari**")
        st.write(f"• Formula Garam Pengendali Penggembungan Filamen (ZnSO4): **{latest['ZnSO4_Concentration']:.2f} g/L**")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    fig_production_area = px.area(df_filtered, x='Timestamp', y='Yarn_Production_TPD', title="Tren Akumulasi Output Pabrik Pemasakan (Tons/Day)", color_discrete_sequence=['#a855f7'])
    fig_production_area.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_production_area, use_container_width=True)

# ==============================================================================
# 6. SERVER DATAFRAME STORAGE LOGS
# ==============================================================================
st.markdown("---")
st.subheader("📋 Core Data Historian Sensor Database Registry Log")
st.dataframe(df_filtered.sort_values(by='Timestamp', ascending=False), use_container_width=True, height=220)

st.markdown("---")
st.caption("Advanced Industrial Yarn Machine SCADA Engine v2.0 • Sri Wahyuni Gea • Universitas Riau")