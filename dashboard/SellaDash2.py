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
    page_title="DCS Paper Finishing & Slitting Management",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme DCS Finishing Master (Aksen Amber Gold & Cyber Punk Orange)
st.markdown("""
    <style>
    .main { background-color: #0a0d14; color: #c9d1d9; }
    div[data-testid="stSidebar"] { background-color: #111420; border-right: 1px solid #262c40; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; font-family: 'Consolas', monospace; }
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; font-size: 14px; }
    .stTabs [aria-selected="true"] { color: #f59e0b !important; font-weight: bold; border-bottom-color: #f59e0b !important; }
    .status-box { padding: 12px; border-radius: 6px; text-align: center; font-weight: bold; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SIDEBAR CONTROL PANEL (ADVANCED FINISHING & PACKAGING LOGISTICS)
# ==============================================================================
st.sidebar.title("🛠️ DCS FINISHING CORE CONSOLE")
st.sidebar.markdown("**PIC:** Sella")
st.sidebar.markdown("---")

st.sidebar.subheader("✂️ Slitter-Winder Mechanics")
winder_speed = st.sidebar.slider("Winder Drive Speed (m/min)", 1200, 2800, 2100, step=50)
web_tension = st.sidebar.slider("Web Tension Setpoint (N/m)", 150, 600, 380, step=10)
slitter_knives_status = st.sidebar.selectbox("Slitter Blade Sharpness Condition", ["Excellent", "Normal Wear", "Dull - Require Change"])

st.sidebar.subheader("📐 Slitting Profile & Dimensions")
customer_roll_width = st.sidebar.slider("Ordered Roll Width (mm)", 500, 2500, 1050, step=50)
paper_caliper_in = st.sidebar.slider("Input Sheet Caliper (µm)", 60, 250, 95, step=5)
paper_gsm_in = st.sidebar.slider("Input Paper Grammage (GSM)", 40, 200, 75, step=5)

st.sidebar.subheader("📦 Automated Wrapping Line")
wrapping_speed_cap = st.sidebar.slider("Conveyor Wrapping Rate (Reels/Shift)", 50, 250, 160, step=10)
strap_tightness = st.sidebar.slider("Strapping Head Pressure (Bar)", 4.0, 7.0, 5.5, step=0.1)

# ==============================================================================
# 3. ADVANCED FINISHING GEOMETRY & QUALITY MATHEMATICAL MODEL
# ==============================================================================
@st.cache_data(ttl=60)
def generate_complex_finishing_data(speed, tension, blade_cond, r_width, caliper, gsm, wrap_cap, strap_press):
    base_end = datetime.now()
    base_start = base_end - timedelta(days=6)
    timestamps = pd.date_range(start=base_start, end=base_end, freq='15min')
    n_rows = len(timestamps)
    
    np.random.seed(88) # Seed dikunci agar visualisasi tren stabil
    
    # --- 1. Perhitungan Geometri Gulungan Kertas (Jumbo Reel to Customer Roll) ---
    # Total panjang kertas tergulung dalam 1 set (asumsi running time per set 45 menit)
    linear_length = speed * 45.0
    # Rumus Diameter Luar Gulungan (Outer Diameter - mm)
    # $D = \sqrt{D_{core}^2 + \frac{4 \cdot \text{panjang} \cdot \text{caliper}}{\pi \cdot 1000}}$
    core_diameter = 150.0 # Standard 6 inch core
    outer_diameter = np.sqrt(core_diameter**2 + (4 * linear_length * (caliper / 1000.0)) / np.pi)
    
    # Berat per Gulungan Customer (Customer Reel Weight - Kg)
    # Volume Silinder Hollow * Density Kertas (asumsi density ~0.8 g/cm³)
    roll_weight = (np.pi * ((outer_diameter/2000)**2 - (core_diameter/2000)**2) * (r_width/1000) * 800)
    
    # --- 2. Perhitungan Optimasi Trim & Reject Rate ---
    # Total lebar mesin konstan 6500mm. Dihitung sisa tepi jika dipotong sesuai pesanan width.
    total_machine_width = 6500
    max_multiples = total_machine_width // r_width
    trim_waste_mm = total_machine_width - (max_multiples * r_width)
    trim_pct = (trim_waste_mm / total_machine_width) * 100
    
    # Penalti Kerusakan Akibat Kondisi Pisau Potong & Tension
    blade_penalty = 0.2 if blade_cond == "Excellent" else (1.2 if blade_cond == "Normal Wear" else 4.5)
    tension_deviation = abs(tension - 380) / 100
    winder_reject_pct = trim_pct + (speed * 0.0008) + (tension_deviation * 3.5) + blade_penalty
    
    # --- 3. Deteksi Cacat Lembaran Otomatis via WIS (Web Inspection System) ---
    # Jumlah cacat per 10,000 meter kertas
    base_holes = int(2 + (speed / 800) + blade_penalty)
    base_wrinkles = int(1 + (tension_deviation * 4))
    
    # --- 4. Parameter Mekanikal Drive & Hidrolik ---
    motor_torque = 45.0 + (speed * 0.015) + (tension * 0.05) + np.random.normal(0, 0.8, n_rows)
    hydraulic_temp = 38.0 + (speed * 0.008) + (strap_press * 1.5) + np.random.normal(0, 0.4, n_rows)
    
    # --- 5. Status Keandalan Operasi Seksi Winder ---
    winder_status = []
    actual_reels_packed = []
    for j in range(n_rows):
        if winder_reject_pct > 18.0 or motor_torque[j] > 95.0:
            winder_status.append("CRITICAL SLIP")
            actual_reels_packed.append(0)
        elif blade_cond == "Dull - Require Change" and j % 12 == 0:
            winder_status.append("BLADE INTERLOCK")
            actual_reels_packed.append(0)
        else:
            winder_status.append("OPERATIONAL")
            actual_reels_packed.append(int((wrap_cap / 32) + np.random.randint(-1, 2)))

    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Winder_Speed': speed + np.random.normal(0, 8, n_rows),
        'Outer_Diameter': outer_diameter + np.random.normal(0, 0.5, n_rows),
        'Roll_Weight': roll_weight + np.random.normal(0, 1, n_rows),
        'Reject_Percentage': np.clip(winder_reject_pct + np.random.normal(0, 0.15, n_rows), 1.5, 45.0),
        'Motor_Torque': np.clip(motor_torque, 20.0, 100.0),
        'Hydraulic_Temp': hydraulic_temp,
        'Packed_Count': actual_reels_packed,
        'Status': winder_status,
        'Holes_Detected': [base_holes + np.random.randint(0, 3) for _ in range(n_rows)],
        'Wrinkles_Detected': [base_wrinkles + np.random.randint(0, 2) for _ in range(n_rows)]
    })
    
    return df, trim_waste_mm, max_multiples

# Jalankan kalkulasi model mesin matematika
df_fin, trim_mm, roll_multiples = generate_complex_finishing_data(
    winder_speed, web_tension, slitter_knives_status, customer_roll_width,
    paper_caliper_in, paper_gsm_in, wrapping_speed_cap, strap_tightness
)

latest = df_fin.iloc[-1]

# ==============================================================================
# 4. MASTER SCADA COCKPIT HEADERS & REACTIVE KPIs
# ==============================================================================
st.title("🏗️ ADVANCED DCS PAPER FINISHING & REWINDER")
st.markdown("Sistem Pemotongan Otomatis (*Slitter Slitting Optimization*), Kalkulasi Dimensi, dan Logistik Pengemasan.")
st.markdown("---")

# Row 1: Status Sistem & Parameter Geometri Gulungan Akhir
top_cols = st.columns(5)
with top_cols[0]:
    if latest['Status'] == "OPERATIONAL":
        st.markdown("<div class='status-box' style='background-color:#047857; border:1px solid #10b981; color:#ffffff;'>WINDER: OPERATIONAL</div>", unsafe_allow_html=True)
    elif latest['Status'] == "BLADE INTERLOCK":
        st.markdown("<div class='status-box' style='background-color:#b45309; border:1px solid #f59e0b; color:#ffffff;'>BLADE INTERLOCK DETECTED</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-box' style='background-color:#b91c1c; border:1px solid #ef4444; color:#ffffff;'>SYSTEM TRIP: EMERGENCY</div>", unsafe_allow_html=True)

with top_cols[1]:
    st.metric("Customer Reel Diameter", f"{latest['Outer_Diameter']:.1f} mm", delta=f"Caliper: {paper_caliper_in} µm")
with top_cols[2]:
    st.metric("Calculated Reel Weight", f"{latest['Roll_Weight']:.1f} Kg", delta=f"Width: {customer_roll_width} mm")
with top_cols[3]:
    st.metric("Slitter Set Combination", f"{roll_multiples:.0f} Cuts / Jumbo", delta=f"Sisa Lebar Potongan: {trim_mm} mm")
with top_cols[4]:
    st.metric("Total Reject & Trim Loss", f"{latest['Reject_Percentage']:.2f} %", delta="Target: < 5.0 %", delta_color="inverse" if latest['Reject_Percentage'] > 6.0 else "normal")

# ==============================================================================
# 5. MULTI-LEVEL INDUSTRIAL PROCESS TABS
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
tab_slitter, tab_wis, tab_mechanical, tab_wrapping_logistics = st.tabs([
    "✂️ Slitter-Winder Cutting Dynamics", 
    "👁️ WIS Surface Quality Map", 
    "🎚️ Drive Motors & Hydraulic Health",
    "📦 Wrapping Line & Dispatch Logistics"
])

# ---- TAB 1: OPERASI PISAU SLITTER ----
with tab_slitter:
    st.subheader("Dinamika Kecepatan Potong Terhadap Kehilangan Bahan (Losses)")
    col1, col2 = st.columns(2)
    with col1:
        fig_w_speed = px.line(df_fin, x='Timestamp', y='Winder_Speed', title="Laju Kecepatan Putar Drive Drum Winder (m/min)", color_discrete_sequence=['#f59e0b'])
        fig_w_speed.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_w_speed, use_container_width=True)
    with col2:
        fig_loss = px.area(df_fin, x='Timestamp', y='Reject_Percentage', title="Profil Akumulasi Persentase Trim & Reject (%)", color_discrete_sequence=['#ef4444'])
        fig_loss.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_loss, use_container_width=True)

# ---- TAB 2: METODE INSPEKSI KAMERA OTOMATIS (WIS) ----
with tab_wis:
    st.subheader("Peta Distribusi Defect Permukaan Kertas Berdasarkan Pemindaian Real-time")
    w_col1, w_col2 = st.columns([1, 2])
    with w_col1:
        st.markdown("<div style='background-color:#1e293b; padding:15px; border-radius:8px;'><b>Kondisi Cacat Per Gulungan Kertas:</b><br><br>"
                    f"• Lubang Lembaran (Holes): <span style='color:#f43f5e; font-weight:bold;'>{latest['Holes_Detected']} Titik / Set</span><br>"
                    f"• Kerutan Kertas (Wrinkles): <span style='color:#eab308; font-weight:bold;'>{latest['Wrinkles_Detected']} Kasus / Set</span><br><br>"
                    "<i>Sistem interlock otomatis akan menandai wilayah defect untuk dipotong pada mesin rewinder berikutnya.</i></div>", unsafe_allow_html=True)
    with w_col2:
        # Scatter plot simulasi visual koordinat defect pada lembaran
        np.random.seed(12)
        defect_types = ['Hole'] * latest['Holes_Detected'] + ['Wrinkle'] * latest['Wrinkles_Detected']
        x_coords = np.random.randint(10, customer_roll_width-10, size=len(defect_types)) if len(defect_types) > 0 else []
        y_coords = np.random.randint(100, 5000, size=len(defect_types)) if len(defect_types) > 0 else []
        
        if len(defect_types) > 0:
            df_defect_map = pd.DataFrame({'Slit_Position_X (mm)': x_coords, 'Linear_Length_Y (m)': y_coords, 'Defect_Type': defect_types})
            fig_wis_map = px.scatter(df_defect_map, x='Slit_Position_X (mm)', y='Linear_Length_Y (m)', color='Defect_Type', 
                                     title="Peta Koordinat Cacat Gulungan Komersial (WIS Live Scanner View)",
                                     color_discrete_map={'Hole': '#f43f5e', 'Wrinkle': '#eab308'}, symbol='Defect_Type')
            fig_wis_map.update_traces(marker=dict(size=12))
            fig_wis_map.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_range=[0, 6500])
            st.plotly_chart(fig_wis_map, use_container_width=True)
        else:
            st.success("100% PERFECT SHEET: Tidak ada cacat yang terdeteksi.")

# ---- TAB 3: HEALTH MONITORING (DIAGNOSTIK MESIN) ----
with tab_mechanical:
    st.subheader("Pemantauan Komponen Mekanikal Penggerak & Tekanan Cairan")
    col3, col4 = st.columns(2)
    with col3:
        fig_torque = go.Figure()
        fig_torque.add_trace(go.Scatter(x=df_fin['Timestamp'], y=df_fin['Motor_Torque'], name='Motor Drive Torque (%)', line=dict(color='#0ea5e9', width=2)))
        fig_torque.add_hline(y=90.0, line=dict(color='red', dash='dash'), annotation_text="Overload Limit")
        fig_torque.update_layout(title="Persentase Beban Torsi Motor Penarik Lembaran", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_torque, use_container_width=True)
    with col4:
        fig_hyd = px.line(df_fin, x='Timestamp', y='Hydraulic_Temp', title="Suhu Sistem Hidrolik Pengunci Reel Mandrel (°C)", color_discrete_sequence=['#a855f7'])
        fig_hyd.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_hyd, use_container_width=True)

# ---- TAB 4: LINI PACKAGING & LOGISTIK KELUAR ----
with tab_wrapping_logistics:
    st.subheader("Pemantauan Output Pengemasan Final Finishing")
    col5, col6 = st.columns([2, 1])
    with col5:
        fig_wrap = px.bar(df_fin[-32:], x='Timestamp', y='Packed_Count', title="Jumlah Gulungan Selesai Dikemas per Blok Waktu (Reels Count)", color_discrete_sequence=['#10b981'])
        fig_wrap.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_wrap, use_container_width=True)
    with w_col1:
        total_shift_pack = df_fin['Packed_Count'].sum()
        st.markdown("<div style='background-color:#111827; padding:20px; border-radius:8px; border:1px solid #374151; text-align:center; margin-top:40px;'>"
                    "<h3>TOTAL OUTPUT PACKING</h3>"
                    f"<h1 style='color:#10b981;'>{total_shift_pack}</h1>"
                    "<b>GULUNGAN SIAP KIRIM (READY TO DISPATCH)</b></div>", unsafe_allow_html=True)

# ==============================================================================
# 6. HISTORICAL MASTER AUTOMATION LOGS & CSV DISPATCH
# ==============================================================================
st.markdown("---")
st.subheader("📋 Historical Database SCADA & Finishing Logs")
st.dataframe(df_fin.sort_values(by='Timestamp', ascending=False), use_container_width=True, height=220)

csv_dispatch = df_fin.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download SCADA Finishing Production Log Report",
    data=csv_dispatch,
    file_name="FINISHING_PRODUCTION_SCADA_REPORT.csv",
    mime="text/csv"
)

st.markdown("---")
st.caption("Industrial Finishing Execution System Platform Engine v4.2 • Sella • Universitas Riau")