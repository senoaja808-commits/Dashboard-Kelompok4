import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==============================================================================
# 1. INITIAL SYSTEM CONFIGURATION & DCS THEME
# ==============================================================================
st.set_page_config(
    page_title="Board Finishing",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme DCS Multi-Ply Industrial (Aksen Amber & Deep Navy)
st.markdown("""
    <style>
    .main { background-color: #05070a; color: #e2e8f0; font-family: 'Consolas', monospace; }
    div[data-testid="stSidebar"] { background-color: #0a0e17; border-right: 2px solid #f59e0b; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8 !important; font-size: 15px; }
    .stTabs [aria-selected="true"] { color: #f59e0b !important; font-weight: bold; border-bottom-color: #f59e0b !important; }
    .metric-container { background-color: #0f172a; padding: 15px; border-radius: 6px; border: 1px solid #1e293b; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SIDEBAR CONTROL PANEL (DCS FINISHING INTERFACE)
# ==============================================================================
st.sidebar.title("🎛️ DCS BOARD FINISHING")
st.sidebar.markdown("**PIC:** Seno Aji Nugroho")
st.sidebar.markdown("---")

st.sidebar.subheader("🌀 Slitter Winder Section")
winder_speed = st.sidebar.slider("Winder Drive Speed (m/min)", 500, 2500, 1600, step=50)
web_tension = st.sidebar.slider("Web Tension Control (N/m)", 100, 600, 350, step=10)
rider_roll_nip = st.sidebar.slider("Rider Roll Nip Load (kN/m)", 1.0, 6.0, 2.8, step=0.1)
edge_trim_setpoint = st.sidebar.slider("Edge Trim Allowance (mm)", 20, 100, 50, step=5)

st.sidebar.subheader("📐 Sheet Cutter Station")
cutter_freq = st.sidebar.slider("Rotary Knife Knife Freq (cuts/min)", 50, 450, 220, step=10)
sheet_length = st.sidebar.slider("Sheet Cut Length (mm)", 600, 2400, 1200, step=50)
scanner_sensitivity = st.sidebar.slider("Optical Defect Scanner (%)", 80, 100, 97, step=1)

st.sidebar.subheader("📦 Packaging & Strapping")
strapping_force = st.sidebar.slider("Strapping Tension Force (N)", 500, 2000, 1200, step=100)
wrap_count = st.sidebar.slider("Stretch Wrapping Layers", 2, 10, 5, step=1)

# Input data dari seksi Board Machine (Baseline Material)
base_gsm = st.sidebar.number_input("Input Material GSM (from Machine)", value=320)
machine_width = 5.6 # Meter (Fixed Industrial Width)

# ==============================================================================
# 3. MATHEMATICAL PROCESS ENGINE (STABLE & REACTIVE)
# ==============================================================================
# 1. Kalkulasi Live Gross TPH (Input Masuk Winder)
live_gross_tph = (winder_speed * machine_width * base_gsm * 60) / 1000000.0

# 2. Kalkulasi Trim Loss (Material yang dibuang di Slitter)
trim_ratio = ((edge_trim_setpoint * 2) / (machine_width * 1000)) * 100
trim_loss_tph = live_gross_tph * (trim_ratio / 100)

# 3. Kalkulasi Reject Rate (Sortir Lembaran Cacat)
reject_pct = (100 - scanner_sensitivity) * 0.15
live_net_tph = (live_gross_tph - trim_loss_tph) * (1.0 - (reject_pct / 100))

# 4. Kalkulasi Profil Kekerasan Gulungan (Hardness Index)
live_hardness = 55.0 + (web_tension * 0.04) + (rider_roll_nip * 4.5)
live_hardness = np.clip(live_hardness, 60.0, 95.0)

# 5. Status Interlock Keamanan
if web_tension > 570 or winder_speed > 2450:
    op_status = "CRITICAL: WEB SNAP DETECTED"
    live_net_tph = 0.0
else:
    op_status = "SYSTEM NORMAL"

# ==============================================================================
# 4. DATA LOGS & TREND GENERATOR (48H HISTORICAL)
# ==============================================================================
@st.cache_data(ttl=5)
def get_historical_logs(speed, net_val, hardness_val):
    base_end = datetime.now()
    base_start = base_end - timedelta(days=2)
    time_index = pd.date_range(start=base_start, end=base_end, freq='30min')
    n = len(time_index)
    np.random.seed(101)
    
    h_net = [net_val + np.random.normal(0, 0.3) if net_val > 0 else 0.0 for _ in range(n)]
    h_hard = [hardness_val + np.random.normal(0, 0.8) for _ in range(n)]
    h_reject = [((100-scanner_sensitivity)*0.15) + np.random.normal(0, 0.02) for _ in range(n)]
    
    return pd.DataFrame({
        'Timestamp': time_index,
        'Gross_In_TPH': [v * 1.02 for v in h_net],
        'Net_Out_TPH': h_net,
        'Hardness_H': h_hard,
        'Reject_Rate_Pct': h_reject,
        'Pallet_Count': [int(speed * 0.012 + np.random.randint(-2, 3)) if net_val > 0 else 0 for _ in range(n)],
        'Knife_Efficiency': [97.5 + np.random.normal(0, 0.2) for _ in range(n)]
    })

df_log = get_historical_logs(winder_speed, live_net_tph, live_hardness)

# ==============================================================================
# 5. BOARD FINISHING - MAIN COCKPIT
# ==============================================================================
st.title("BOARD FINISHING")
st.markdown("Sistem Pengendalian Slitter-Winder, Presisi Sheet-Cutter, dan Otomasi Pengemasan Palet Akhir.")
st.markdown("---")

# Row 1: Live Status & Key Performance Indicators
kpi_cols = st.columns(5)

with kpi_cols[0]:
    if op_status == "SYSTEM NORMAL":
        st.markdown("<div style='background-color:#022c22; color:#10b981; padding:12px; border-radius:6px; text-align:center; font-weight:bold; border:1px solid #10b981;'>STATUS: SYSTEM NORMAL</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background-color:#450a0a; color:#f87171; padding:12px; border-radius:6px; text-align:center; font-weight:bold; border:1px solid #dc2626;'>STATUS: INTERLOCK TRIP</div>", unsafe_allow_html=True)

with kpi_cols[1]:
    st.metric("Net Output Capacity", f"{live_net_tph:.1f} Ton/Jam", delta=f"In: {live_gross_tph:.1f} TPH")

with kpi_cols[2]:
    st.metric("Avg Reel Hardness", f"{live_hardness:.1f} H", delta="Target: 75-85 H")

with kpi_cols[3]:
    st.metric("Total Trim Loss", f"{trim_ratio:.2f} %", delta=f"{trim_loss_tph:.2f} TPH", delta_color="inverse")

with kpi_cols[4]:
    st.metric("Sorting Reject Rate", f"{reject_pct:.2f} %", delta=f"{cutter_freq} CPM")

# ==============================================================================
# 6. SUBSYSTEM ANALYTICS TABS
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs([
    "🌀 Slitter-Winder Analysis", 
    "📐 Sheeter Efficiency Profile", 
    "📦 Packaging & Inventory State"
])

# ---- TAB 1: SLITTER WINDER ----
with tab1:
    st.subheader("Profil Mekanika Slitter Winder")
    ca, cb = st.columns([2, 1])
    with ca:
        fig_prod = go.Figure()
        fig_prod.add_trace(go.Scatter(x=df_log['Timestamp'], y=df_log['Gross_In_TPH'], name='Gross Input TPH', line=dict(color='#334155', width=1)))
        fig_prod.add_trace(go.Scatter(x=df_log['Timestamp'], y=df_log['Net_Out_TPH'], name='Net Output TPH', fill='tozeroy', line=dict(color='#f59e0b', width=2.5)))
        fig_prod.update_layout(title="Keseimbangan Aliran Massa Finishing (Mass Balance)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_prod, use_container_width=True)
    with cb:
        # Cross-Direction Hardness Simulation
        pos = ["Tend", "Center-L", "Center", "Center-R", "Drive"]
        h_points = [live_hardness + x for x in [np.random.normal(-0.5,0.2), np.random.normal(0.5,0.1), np.random.normal(0.2,0.1), np.random.normal(-0.3,0.1), np.random.normal(-0.6,0.2)]]
        fig_h = go.Figure(data=[go.Bar(x=pos, y=h_points, marker_color='#f59e0b', text=[f"{p:.1f}H" for p in h_points], textposition='auto')])
        fig_h.update_layout(title="CD Hardness Profile (Schmidt Index)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_range=[0, 110])
        st.plotly_chart(fig_h, use_container_width=True)

# ---- TAB 2: SHEET CUTTER ----
with tab2:
    st.subheader("Efisiensi Seksi Pemotongan Lembaran Plano")
    cc, cd = st.columns(2)
    with cc:
        fig_eff = px.line(df_log, x='Timestamp', y='Knife_Efficiency', title="Efisiensi Sinkronisasi Rotary Knife (%)", color_discrete_sequence=['#10b981'])
        fig_eff.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_eff, use_container_width=True)
    with cd:
        fig_rej = px.area(df_log, x='Timestamp', y='Reject_Rate_Pct', title="Laju Penolakan Scanner Optik (%)", color_discrete_sequence=['#ef4444'])
        fig_rej.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_rej, use_container_width=True)

# ---- TAB 3: PACKAGING & LOGISTICS ----
with tab3:
    st.subheader("Status Otomasi Robotik Packaging & Konveyor Warehouse")
    ce, cf = st.columns(2)
    with ce:
        fig_p = px.bar(df_log, x='Timestamp', y='Pallet_Count', title="Output Kemasan Palet Selesai (Units/Hr)", color_discrete_sequence=['#3b82f6'])
        fig_p.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_p, use_container_width=True)
    with cf:
        st.markdown("<div style='background-color:#0f172a; padding:20px; border-radius:8px; border:1px solid #1e293b;'>", unsafe_allow_html=True)
        st.markdown("<h4>⚙️ SCADA Digital Output Status:</h4>", unsafe_allow_html=True)
        st.markdown(f"• Strapping Machine Force: <b style='color:#10b981;'>{strapping_force} N (STABLE)</b>", unsafe_allow_html=True)
        st.markdown(f"• Stretch Wrap Rotation: <b style='color:#10b981;'>{wrap_count} Layers (ACTIVE)</b>", unsafe_allow_html=True)
        st.markdown(f"• Conveyor Drive Status: <b style='color:#10b981;'>READY / AUTO</b>", unsafe_allow_html=True)
        st.markdown(f"• Label Printing System: <b style='color:#10b981;'>ONLINE</b>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# 7. HISTORICAL DATABASE REGISTRY
# ==============================================================================
st.markdown("---")
st.subheader("📋 Historical Sensor Registry Log")
st.dataframe(df_log.sort_values(by='Timestamp', ascending=False), use_container_width=True, height=220)

st.markdown("---")
st.caption("Board Finishing Automation SCADA Engine v4.0 • Seno • Universitas Riau")