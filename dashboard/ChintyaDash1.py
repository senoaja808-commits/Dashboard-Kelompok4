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
    page_title="Fiberline System Console",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme DCS Fiberline Control Interface Professional
st.markdown("""
    <style>
    .main { background-color: #060913; color: #cbd5e1; font-family: 'Consolas', monospace; }
    div[data-testid="stSidebar"] { background-color: #0c111d; border-right: 2px solid #58a6ff; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; font-size: 15px; }
    .stTabs [aria-selected="true"] { color: #58a6ff !important; font-weight: bold; border-bottom-color: #58a6ff !important; }
    .status-card { padding: 12px; border-radius: 6px; text-align: center; font-weight: bold; font-family: monospace; }
    .data-card { background-color: #0f172a; border: 1px solid #1e293b; padding: 15px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DYNAMIC OPERATIONAL CONTROL ROOM (SIDEBAR CONSOLE)
# ==============================================================================
st.sidebar.title("🎛️ DCS FIBERLINE CONTROL")
st.sidebar.markdown("**PIC:** Chintya Isya Ababil")
st.sidebar.markdown("---")

st.sidebar.subheader("🎯 Quality Specification Targets")
target_brightness = st.sidebar.slider("Target Brightness (% ISO)", 80.0, 95.0, 89.5, step=0.5)
alert_kappa_limit = st.sidebar.slider("Post-O2 Kappa Upper Limit", 10.0, 20.0, 14.5, step=0.1)

st.sidebar.subheader("🧪 Chemical Charge Setpoints")
ea_charge = st.sidebar.slider("Effective Alkali (EA) Charge (%)", 15.0, 22.0, 18.5, step=0.5)
liquor_wood_ratio = st.sidebar.slider("Liquor-to-Wood Ratio", 2.5, 5.0, 3.6, step=0.1)
o2_pressure = st.sidebar.slider("O2 Reactor Pressure (bar)", 3.0, 8.0, 5.5, step=0.1)

st.sidebar.subheader("⚙️ Process Optimization")
anthraquinone_dosage = st.sidebar.slider("Anthraquinone (AQ) Catalyst (kg/t)", 0.0, 2.0, 0.5, step=0.1)
wash_loss_target = st.sidebar.slider("Target Washing Loss (kg COD/t)", 5.0, 15.0, 8.0, step=0.5)

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
# 3. INTERACTIVE SIMULATION ENGINE (FIXED TECHNICAL MATHEMATICS)
# ==============================================================================
def generate_advanced_fiberline_data(t_brightness, a_kappa, ea, lw_ratio, o2_p, aq, w_loss):
    timestamps = pd.date_range(start=base_start, end=base_end, freq='15min')
    n_rows = len(timestamps)
    
    np.random.seed(42) 
    
    # Area 1: Feeding System
    woodchip_feed = np.random.normal(165, 3.5, n_rows)
    chip_moisture = np.random.normal(47.8, 0.8, n_rows)
    dry_wood_feed = woodchip_feed * (1 - (chip_moisture / 100))
    
    # Area 2: Continuous Digester Model (Kinetika Delignifikasi)
    white_liquor_flow = dry_wood_feed * (lw_ratio * 0.55) + np.random.normal(0, 1.0, n_rows)
    cooking_temp = 158.0 + (ea * 0.45) + np.random.normal(0, 0.8, n_rows)
    h_factor = 1120 + (cooking_temp - 164) * 38 + np.random.normal(0, 5, n_rows)
    
    # Efek katalis AQ menaikkan yield serat selulosa
    pulp_yield = np.clip(48.2 - (h_factor - 1120) * 0.005 - (ea - 18.5) * 0.18 + (aq * 0.4), 41.0, 53.0)
    pulp_production = dry_wood_feed * (pulp_yield / 100)
    
    # Area 3: Washing & O2 Delignification Model
    # Kappa brown line murni berkorelasi dengan pembebanan alkali (EA)
    kappa_brown = np.random.normal(30.0, 0.5, n_rows) - (ea - 18.5) * 0.4
    
    # PERBAIKAN UTAMA: Kappa post-O2 murni didorong turun oleh O2 Pressure dan EA. 
    # Nilai ini tidak dikunci ke slider 'a_kappa' agar pengujian limit fungsional bisa dicapai.
    kappa_post_o2 = np.clip(12.2 + np.random.normal(0, 0.15, n_rows) - (o2_p - 5.5) * 0.5 + (w_loss * 0.04), 8.5, 24.0)
    
    o2_flow_rate = pulp_production * 22.5 + (o2_p * 3.1) + np.random.normal(0, 0.4, n_rows)
    washing_eff = np.clip(99.0 - (w_loss * 0.08) + np.random.normal(0, 0.05, n_rows), 95.0, 99.8)
    
    # Area 4: Bleaching Plant (D0 - EOP - D1 Stage)
    kappa_factor = 0.21 + np.random.normal(0, 0.005, n_rows)
    clo2_d0 = (kappa_post_o2 * kappa_factor * 10) 
    h2o2_eop = np.random.normal(11.8, 0.2, n_rows) + (w_loss * 0.15)
    clo2_d1 = np.random.normal(14.5, 0.3, n_rows) + (t_brightness - 89.5) * 1.4
    
    # Profil kecemerlangan akhir stabil merefleksikan target pengendalian kontroler DCS pabrik
    final_brightness = np.clip(t_brightness + np.random.normal(0.1, 0.1, n_rows) - (kappa_post_o2 * 0.01), 70.0, 98.5)

    # Menghitung total konsumsi harian (ton/hari) gas ClO2
    tot_clo2_day = (pulp_production * (clo2_d0 + clo2_d1) * 24) / 1000.0

    return pd.DataFrame({
        'Timestamp': timestamps,
        'Woodchip_Feed_Rate': woodchip_feed,
        'Woodchip_Moisture': chip_moisture,
        'Dry_Wood_Feed': dry_wood_feed,
        'White_Liquor_Flow': white_liquor_flow,
        'Digester_Cooking_Temp': cooking_temp,
        'Calculated_H_Factor': h_factor,
        'Pulp_Yield_Percent': pulp_yield,
        'Pulp_Production_Rate': pulp_production,
        'Blow_Line_Kappa': kappa_brown,
        'BSW_Washing_Efficiency': washing_eff,
        'Post_O2_Kappa': kappa_post_o2,
        'O2_Gas_Flow': o2_flow_rate,
        'Bleaching_D0_ClO2': clo2_d0,
        'Bleaching_EOP_H2O2': h2o2_eop,
        'Bleaching_D1_ClO2': clo2_d1,
        'Final_Pulp_Brightness_ISO': final_brightness,
        'Daily_ClO2_Consumption': tot_clo2_day
    })

# Sinkronisasi Engine Data dengan Nilai Input Slider
df_master = generate_advanced_fiberline_data(
    target_brightness, alert_kappa_limit, ea_charge, liquor_wood_ratio, o2_pressure, anthraquinone_dosage, wash_loss_target
)

# Pengecekan Keamanan Rentang Kalender
if isinstance(date_selection, (list, tuple)) and len(date_selection) == 2:
    df_filtered = df_master[(df_master['Timestamp'].dt.date >= date_selection[0]) & (df_master['Timestamp'].dt.date <= date_selection[1])]
else:
    df_filtered = df_master

latest = df_filtered.iloc[-1]

# ==============================================================================
# 4. MAIN HEADERS & REAL-TIME DCS MONITORING SYSTEM
# ==============================================================================
st.title("FIBERLINE")
st.markdown("Sistem Pengawasan Terintegrasi: Woodchip Feeding, Continuous Digester, Washing, dan Bleaching Plant.")
st.markdown("---")

# Penyusunan Lini Metrik Utama (DCS Panel Style)
kpi_cols = st.columns(5)

with kpi_cols[0]:
    b_val = latest['Final_Pulp_Brightness_ISO']
    k_val = latest['Post_O2_Kappa']
    
    # PERBAIKAN LOGIKA STATUS EVALUASI KUALITAS MUTU:
    # Mengakomodasi toleransi industri industri (+/- 0.3 untuk brightness)
    is_brightness_ok = b_val >= (target_brightness - 0.3)
    is_kappa_ok = k_val <= alert_kappa_limit
    
    if is_brightness_ok and is_kappa_ok:
        st.markdown("<div class='status-card' style='background-color:#064e3b; color:#10b981; border:1px solid #10b981;'>QUALITY: OPTIMAL</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-card' style='background-color:#450a0a; color:#f87171; border:1px solid #dc2626;'>QUALITY: OFF-SPEC</div>", unsafe_allow_html=True)

with kpi_cols[1]:
    st.metric(
        label="Final Pulp Brightness", 
        value=f"{b_val:.1f} % ISO", 
        delta=f"{(b_val - target_brightness):+.1f} vs Target",
        delta_color="normal" if b_val >= target_brightness else "inverse"
    )

with kpi_cols[2]:
    st.metric(
        label="Post-O2 Kappa Number", 
        value=f"{k_val:.2f}", 
        delta=f"{(k_val - alert_kappa_limit):+.2f} vs Limit",
        delta_color="inverse" if k_val > alert_kappa_limit else "normal"
    )

with kpi_cols[3]:
    st.metric(label="Calculated H-Factor", value=f"{latest['Calculated_H_Factor']:.0f}", delta=f"Yield: {latest['Pulp_Yield_Percent']:.1f}%")

with kpi_cols[4]:
    st.metric(label="Pulp Production Rate", value=f"{latest['Pulp_Production_Rate']:.1f} ADt/H", delta=f"Feed: {latest['Woodchip_Feed_Rate']:.0f} t/h")

# ==============================================================================
# 5. DIAGRAM DAN HISTOGRAM ANALISIS SUBSISTEM
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab_feed, tab_digester, tab_washing, tab_bleaching, tab_balance = st.tabs([
    "🌀 Woodchip Feeding System", 
    "🔥 Continuous Digester Tower", 
    "🧪 Washing & O2 Delignification", 
    "⚡ Bleaching Plant Automation",
    "📊 Mass & Chemical Balance"
])

# ---- TAB 1: WOODCHIP FEEDING SYSTEM ----
with tab_feed:
    st.subheader("Manajemen Aliran Masuk Bahan Baku")
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        fig_feed = px.line(df_filtered, x='Timestamp', y='Woodchip_Feed_Rate', title="Laju Aliran Pengumpanan Serpihan Kayu (Wet Woodchip t/h)", color_discrete_sequence=['#3b82f6'])
        fig_feed.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_feed, use_container_width=True)
    with col_f2:
        fig_moist = px.histogram(df_filtered, x='Woodchip_Moisture', title="Distribusi Kadar Air Serpihan Kayu (Moisture %)", color_discrete_sequence=['#60a5fa'])
        fig_moist.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_moist, use_container_width=True)

# ---- TAB 2: CONTINUOUS DIGESTER TOWER ----
with tab_digester:
    st.subheader("Keseimbangan Termal & Kimia di Menara Digester Pemasak")
    fig_dig = go.Figure()
    fig_dig.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Digester_Cooking_Temp'], name='Cooking Temperature (°C)', line=dict(color='#ef4444', width=2.5)))
    fig_dig.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Pulp_Yield_Percent'], name='Pulp Yield (%)', yaxis='y2', line=dict(color='#10b981', width=1.5, dash='dash')))
    
    fig_dig.update_layout(
        title="Dinamika Korelasi Temperatur Memasak Terhadap Efisiensi Yield Serat Selulosa",
        yaxis=dict(title=dict(text="Cooking Temperature (°C)", font=dict(color="#ef4444")), tickfont=dict(color="#ef4444")),
        yaxis2=dict(title=dict(text="Pulp Yield (%)", font=dict(color="#10b981")), tickfont=dict(color="#10b981"), overlaying='y', side='right'),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_dig, use_container_width=True)

# ---- TAB 3: WASHING & O2 DELIGNIFICATION ----
with tab_washing:
    st.subheader("Pengurangan Kandungan Lignin Terlarut & Efisiensi Pencuci")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        fig_kappa = go.Figure()
        fig_kappa.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Blow_Line_Kappa'], name='Pre-O2 Kappa (Blow Line)', line=dict(color='#f59e0b', width=1.5)))
        fig_kappa.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Post_O2_Kappa'], name='Post-O2 Delignification Kappa', line=dict(color='#10b981', width=2.5)))
        fig_kappa.add_hline(y=alert_kappa_limit, line=dict(dash="dot", color="#ef4444"), annotation_text=f"Alarm Limit: {alert_kappa_limit}")
        fig_kappa.update_layout(title="Profil Penurunan Bilangan Kappa Pasca O2 Delignifikasi", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_kappa, use_container_width=True)
    with col_w2:
        fig_wash = px.line(df_filtered, x='Timestamp', y='BSW_Washing_Efficiency', title="Efisiensi Pembersihan Organik Brown Stock Washer (%)", color_discrete_sequence=['#a855f7'])
        fig_wash.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_wash, use_container_width=True)

# ---- TAB 4: BLEACHING PLANT AUTOMATION ----
with tab_bleaching:
    st.subheader("Otomasi Dosis Pemutihan Kimia (D0 - EOP - D1 Stage)")
    col_b1, col_b2 = st.columns([1, 2])
    with col_b1:
        fig_chem = go.Figure()
        fig_chem.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Bleaching_D0_ClO2'], fill='tozeroy', name='D0 Stage ClO2 (kg/t)', line=dict(color='#ec4899')))
        fig_chem.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Bleaching_EOP_H2O2'], fill='tonexty', name='EOP Stage H2O2 (kg/t)', line=dict(color='#eab308')))
        fig_chem.add_trace(go.Scatter(x=df_filtered['Timestamp'], y=df_filtered['Bleaching_D1_ClO2'], fill='tonexty', name='D1 Stage ClO2 (kg/t)', line=dict(color='#3b82f6')))
        fig_chem.update_layout(title="Grafik Konsumsi Bahan Kimia Pemutih per Ton Pulp", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_chem, use_container_width=True)
    with col_b2:
        fig_bright = px.line(df_filtered, x='Timestamp', y='Final_Pulp_Brightness_ISO', title="Pencapaian Akhir Derajat Keputihan Serat (% ISO)", color_discrete_sequence=['#ffffff'])
        fig_bright.add_hline(y=target_brightness, line=dict(dash="dash", color="#38bdf8"), annotation_text=f"Target: {target_brightness}")
        fig_bright.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bright, use_container_width=True)

# ---- TAB 5: MASS & CHEMICAL BALANCE ----
with tab_balance:
    st.subheader("Neraca Massa dan Audit Penggunaan Bahan Kimia Harian")
    col_bal1, col_bal2 = st.columns(2)
    
    with col_bal1:
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.markdown("<h4>📋 Neraca Massa Bahan Baku Kayu</h4>", unsafe_allow_html=True)
        st.write(f"• Total Umpan Serpihan Kayu (Basah): **{latest['Woodchip_Feed_Rate']:.2f} t/h**")
        st.write(f"• Kadar Air Kandungan Kayu: **{latest['Woodchip_Moisture']:.2f} %**")
        st.write(f"• Laju Pengeringan Kayu Neto: **{latest['Dry_Wood_Feed']:.2f} Bone-Dry t/h**")
        st.write(f"• Laju Efisiensi Yield Memasak: **{latest['Pulp_Yield_Percent']:.2f} %**")
        st.write(f"• Estimasi Serat Selulosa Terlarut (Reject Lignin): **{(latest['Dry_Wood_Feed'] - latest['Pulp_Production_Rate']):.2f} t/h**")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_bal2:
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.markdown("<h4>📈 Konsumsi Finansial Reagen Pemutih (Bleach Chemical Audit)</h4>", unsafe_allow_html=True)
        st.write(f"• Laju Dosis D0 Stage ClO2: **{latest['Bleaching_D0_ClO2']:.2f} kg/ADt**")
        st.write(f"• Laju Dosis EOP Stage H2O2: **{latest['Bleaching_EOP_H2O2']:.2f} kg/ADt**")
        st.write(f"• Laju Dosis D1 Stage ClO2: **{latest['Bleaching_D1_ClO2']:.2f} kg/ADt**")
        st.write(f"• Estimasi Kebutuhan Total ClO2 Pabrik: **{latest['Daily_ClO2_Consumption']:.2f} Metric Ton / Hari**")
        st.write(f"• Target Kehilangan Organik di Pencuci (Washing Loss): **{wash_loss_target} kg COD/t**")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    fig_balance_line = px.area(df_filtered, x='Timestamp', y='Daily_ClO2_Consumption', title="Tren Proyeksi Konsumsi Gas ClO2 Harian Pabrik (Tons/Day)", color_discrete_sequence=['#14b8a6'])
    fig_balance_line.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_balance_line, use_container_width=True)

# ==============================================================================
# 6. SERVER DATAFRAME STORAGE LOGS
# ==============================================================================
st.markdown("---")
st.subheader("📋 Core Data Historian Sensor Database Registry Log")
st.dataframe(df_filtered.sort_values(by='Timestamp', ascending=False), use_container_width=True, height=220)

st.markdown("---")
st.caption("Advanced Industrial Fiberline SCADA Core Engine v6.0 • Chintya Isya Ababil • Universitas Riau")