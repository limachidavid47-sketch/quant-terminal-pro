import streamlit as st
import requests
import os
import math
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y ACCESO QUANT MLBB
# ==========================================
st.set_page_config(page_title="Quant Elite V20 - MLBB", layout="wide", initial_sidebar_state="expanded")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("""
        <style>
        .stApp { background-color: #05080F; color: #F8FAFC; }
        .login-box { background: #0F172A; border: 2px solid #F59E0B; border-radius: 20px; padding: 40px; text-align: center; margin-top: 10vh; }
        .login-title { color: #F59E0B; font-size: 30px; font-weight: 900; letter-spacing: 3px; }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.markdown("<div class='login-title'>⚡ MLBB QUANT V20</div>", unsafe_allow_html=True)
            st.markdown("<p style='color:#64748B; margin-bottom:25px;'>OPERACIONES EXCLUSIVAS MOBILE LEGENDS</p>", unsafe_allow_html=True)
            u = st.text_input("Operador", key="login_u")
            p = st.text_input("Clave", type="password", key="login_p")
            if st.button("CONECTAR"):
                if u == st.secrets["usuario"] and p == st.secrets["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else: st.error("ERROR DE ACCESO")
            st.markdown("</div>", unsafe_allow_html=True)
        return False
    return True

if not check_password(): st.stop()

# ==========================================
# 2. MOTOR DE DATOS (HISTORIAL 10 PARTIDAS MLBB)
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

@st.cache_data(ttl=60)
def call_api_live(endpoint, params_str=""):
    url = f"https://api.pandascore.co/mobile-legends/{endpoint}?{params_str}"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

@st.cache_data(ttl=21600, show_spinner=False)
def fetch_mlbb_history(team_id):
    url = "https://api.pandascore.co/mobile-legends/matches"
    params = f"filter[opponent_id]={team_id}&filter[status]=finished&sort=-end_at&per_page=10"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(f"{url}?{params}", headers=headers)
        if res.status_code == 200:
            hist = res.json()
            if not hist: return 0.50, ['unknown']*5
            wins = sum(1 for m in hist if str(m.get('winner_id')) == str(team_id))
            form = ['win' if str(m.get('winner_id')) == str(team_id) else 'loss' for m in hist]
            return (wins/len(hist)), form[:5]
    except: pass
    return 0.50, ['unknown']*5

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(round(monto, 2)))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

# ==========================================
# 3. ALGORITMO DE MOMENTUM Y ORO (ESPECIAL MLBB)
# ==========================================
def motor_quant_mlbb(wr1, wr2, mercado, opcion, linea, gold_diff=0, minute=0):
    # Probabilidad Base H2H
    total = wr1 + wr2
    prob = (wr1 / total) if (total > 0 and ("A" in opcion or "Más" in opcion)) else (wr2 / total if total > 0 else 0.5)
    
    # Ajuste por Mercado
    if "Handicap" in mercado:
        prob -= (abs(linea) * 0.05) # Mayor impacto en handicap por velocidad de MLBB
    
    # Simulación Económica (Calibración MLBB: Pivote min 12, Divisor 5000)
    if minute > 0:
        impacto_oro = (gold_diff / 5000) * (1 / (1 + (minute / 12)**2))
        prob += impacto_oro

    return max(0.05, min(0.95, prob))

# ==========================================
# 4. INTERFAZ TÁCTICA
# ==========================================
st.sidebar.markdown(f"### 🏦 Bankroll: {bank_actual:.2f} U")
if st.sidebar.button("🗑️ RECARGAR DATOS"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
tema = st.sidebar.selectbox("🎨 Tema", ["Azul Oscuro", "Verde Hacker", "Rojo Táctico"])
colors = {
    "Azul Oscuro": ("#0B1120", "#1E293B", "#F1F5F9", "#38BDF8"),
    "Verde Hacker": ("#000000", "#051A05", "#4ADE80", "#10B981"),
    "Rojo Táctico": ("#0A0000", "#1A0505", "#FECACA", "#EF4444")
}
bg, card, text, acc = colors[tema]

st.markdown(f"""<style>
    .stApp {{ background-color: {bg}; color: {text}; }}
    [data-testid="stSidebar"] {{ background-color: {card} !important; border-right: 1px solid {acc}; }}
    .glass-card {{ background: {card}; border: 1px solid {acc}44; border-radius: 15px; padding: 15px; margin-bottom: 15px; }}
    .wr-badge {{ font-size: 14px; color: #10B981; font-weight: 900; background: rgba(16, 185, 129, 0.1); padding: 2px 10px; border-radius: 20px; }}
    .tower-plate {{ width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin: 0 2px; }}
    .win {{ background: #10B981; }} .loss {{ background: #EF4444; }} .unknown {{ background: #475569; }}
    .sniper-alert {{ background: rgba(16, 185, 129, 0.15); border: 2px dashed #10B981; padding: 15px; border-radius: 10px; color: #10B981; font-weight: 900; text-align: center; animation: pulse 1.5s infinite; }}
    @keyframes pulse {{ 0% {{opacity: 1;}} 50% {{opacity: 0.6;}} 100% {{opacity: 1;}} }}
</style>""", unsafe_allow_html=True)

# ==========================================
# 5. RADAR EXCLUSIVO MLBB
# ==========================================
st.title("📡 Radar Quant: Mobile Legends")
matches = call_api_live("matches/running") + call_api_live("matches/upcoming", "per_page=30")

if not matches:
    st.info("Buscando ligas activas (MPL Indonesia, Filipinas, etc.)...")
else:
    c1, c2 = st.columns(2)
    for i, m in enumerate(matches[:16]):
        opp = m.get('opponents', [])
        if len(opp) < 2: continue
        t1, t2 = opp[0]['opponent'], opp[1]['opponent']
        
        wr1, form1 = fetch_mlbb_history(t1['id'])
        wr2, form2 = fetch_mlbb_history(t2['id'])
        
        with (c1 if i % 2 == 0 else c2):
            st.markdown(f"""<div class="glass-card">
                <div style="display:flex; justify-content:space-between; font-size:11px;"><span>🏆 {m['league']['name']}</span><span style="color:{acc}">{'🔴 EN VIVO' if m['status']=='running' else '🕒 PRÓXIMO'}</span></div>
                <div style="display:flex; justify-content:space-around; align-items:center; text-align:center; margin:15px 0;">
                    <div><div style="font-size:12px; font-weight:bold;">{t1['name']}</div><img src="{t1['image_url']}" style="width:50px;"><br><span class="wr-badge">{wr1*100:.0f}%</span><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form1])}</div></div>
                    <div style="font-size:20px; font-weight:900; color:{acc}">VS</div>
                    <div><div style="font-size:12px; font-weight:bold;">{t2['name']}</div><img src="{t2['image_url']}" style="width:50px;"><br><span class="wr-badge">{wr2*100:.0f}%</span><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form2])}</div></div>
                </div>
            </div>""", unsafe_allow_html=True)
            
            with st.expander("⚙️ OPERACIÓN MLBB"):
                mer = st.selectbox("Mercado", ["Ganador", "Handicap", "Total Kills"], key=f"m_{i}")
                opc = st.selectbox("A favor de", ["Equipo A", "Equipo B", "Más (+)", "Menos (-)"], key=f"o_{i}")
                lin = st.number_input("Línea", value=0.0, step=0.5, key=f"l_{i}")
                
                rem = st.checkbox("💸 Modelo Económico (Oro)", key=f"r_{i}")
                g_diff, m_act = 0, 0
                if rem:
                    m_act = st.number_input("Minuto", value=10, key=f"min_{i}")
                    g_diff = st.number_input("Dif. Oro", value=0, step=500, key=f"oro_{i}")
                
                prob = motor_quant_mlbb(wr1, wr2, mer, opc, lin, g_diff, m_act)
                
                st.markdown(f"""<div style="text-align:center; border:1px solid {acc}; border-radius:10px; padding:10px;">
                    <div style="font-size:10px; text-transform:uppercase;">Probabilidad del Algoritmo</div>
                    <div style="font-size:24px; font-weight:900; color:{acc}">{prob*100:.1f}%</div>
                </div>""", unsafe_allow_html=True)
                
                if prob >= 0.75:
                    st.markdown("<div class='sniper-alert'>🎯 SNIPER ALERT: VENTAJA CRÍTICA</div>", unsafe_allow_html=True)
                
                cuota = st.number_input("Cuota Casino", value=1.0, key=f"c_{i}")
                if cuota > (1/prob):
                    k = (((cuota-1)*prob)-(1-prob))/(cuota-1)
                    stake = k * 0.25 * bank_actual
                    if stake > 0:
                        st.success(f"🔥 VALOR: Sugerido {stake:.2f} U")
                        if st.button("REGISTRAR", key=f"b_{i}"):
                            gestionar_bank(bank_actual - stake)
                            st.rerun()
                else: st.warning(f"❌ Sin valor matemático.")