import streamlit as st
import requests
import os
import math
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD, ACCESO QUANT Y ENLACE MÁGICO
# ==========================================
st.set_page_config(page_title="Quant Elite V25", layout="wide", initial_sidebar_state="expanded")

def check_password():
    # BLINDAJE MULTI-VERSIÓN PARA EL ENLACE MÁGICO
    token = ""
    try:
        if "token" in st.query_params: token = st.query_params["token"]
    except:
        params = st.experimental_get_query_params()
        if "token" in params: token = params["token"][0]
        
    if token == "capo":
        st.session_state["password_correct"] = True

    if st.session_state.get("password_correct", False):
        return True

    # PANTALLA DE LOGIN
    st.markdown("""
    <style>
    .stApp { background-color: #05080F; color: #F8FAFC; }
    .login-box { background: #0F172A; border: 2px solid #10B981; border-radius: 20px; padding: 40px; text-align: center; margin-top: 10vh; box-shadow: 0 0 20px rgba(16, 185, 129, 0.2); }
    .login-title { color: #10B981; font-size: 30px; font-weight: 900; letter-spacing: 3px; }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>⚡ QUANT TERMINAL V25</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748B; margin-bottom:25px;'>SISTEMA MULTI-DISCIPLINA HFT</p>", unsafe_allow_html=True)
        u = st.text_input("Usuario", key="login_u")
        p = st.text_input("Contraseña", type="password", key="login_p")
        if st.button("AUTENTICAR", use_container_width=True):
            if u == st.secrets["usuario"] and p == st.secrets["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("ACCESO DENEGADO")
        st.markdown("</div>", unsafe_allow_html=True)
    return False

if not check_password(): st.stop()

# ==========================================
# 2. MOTOR DE DATOS HFT (6 HORAS CACHÉ)
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

@st.cache_data(ttl=60)
def call_api_live(game_slug, endpoint, params_str=""):
    url = f"https://api.pandascore.co/{game_slug}/{endpoint}?{params_str}"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

@st.cache_data(ttl=21600, show_spinner=False)
def fetch_historical_data(game_slug, team_id):
    url = f"https://api.pandascore.co/{game_slug}/matches"
    params = f"filter[opponent_id]={team_id}&filter[status]=finished&sort=-end_at&per_page=10"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(f"{url}?{params}", headers=headers)
        if res.status_code == 200:
            hist = res.json()
            if not hist: return [], 0.50, ['unknown']*5
            wins = sum(1 for m in hist if str(m.get('winner_id')) == str(team_id))
            form = ['win' if str(m.get('winner_id')) == str(team_id) else 'loss' for m in hist]
            return hist, (wins/len(hist)), (form[:5])
    except: pass
    return [], 0.50, ['unknown']*5

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(round(monto, 2)))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

# ==========================================
# 3. MOTOR CUANTITATIVO
# ==========================================
def calculate_gold_impact(gold_diff, minute, game_slug):
    if minute <= 0: return 0
    if game_slug == "dota2": divisor_oro, min_pivote = 10000, 30
    elif game_slug == "mobile-legends": divisor_oro, min_pivote = 5000, 12
    else: divisor_oro, min_pivote = 8000, 25

    impacto_bruto = gold_diff / divisor_oro
    time_decay = 1 / (1 + (minute / min_pivote)**2)
    return max(-0.40, min(0.40, impacto_bruto * time_decay))

def motor_cuantitativo_avanzado(wr_t1, wr_t2, mercado, opcion, linea_casino, t1_name):
    wr1, wr2 = (wr_t1 or 0.50), (wr_t2 or 0.50)
    prob_base = 0.50
    total_wr = wr1 + wr2
    if total_wr == 0: total_wr = 1 

    es_equipo_1 = (opcion == t1_name)

    if "Ganador" in mercado or "Kills por Equipo" in mercado:
        prob_base = wr1 / total_wr if es_equipo_1 else wr2 / total_wr

    elif "Handicap" in mercado:
        prob_win = wr1 / total_wr if es_equipo_1 else wr2 / total_wr
        dificultad = (abs(linea_casino) * 0.025)
        prob_base = prob_win - dificultad if linea_casino < 0 else prob_win + dificultad

    elif "Total" in mercado or "Duración" in mercado:
        momentum_combinado = (wr1 + wr2) / 2
        if opcion == "Más (+)":
            prob_base = 0.50 + (momentum_combinado - 0.50) * 0.3
            if linea_casino > 0 and linea_casino < 25: prob_base += 0.10 
        else: 
            prob_base = 0.50 - (momentum_combinado - 0.50) * 0.3
            if linea_casino > 35: prob_base += 0.10 

    elif "Primer" in mercado or "Primera" in mercado:
        prob_win = wr1 / total_wr if es_equipo_1 else wr2 / total_wr
        prob_base = 0.50 + ((prob_win - 0.50) * 0.7) 

    return max(0.05, min(0.95, prob_base))

# ==========================================
# 4. TEMAS Y CSS
# ==========================================
st.sidebar.markdown("### 🎨 Apariencia")
tema = st.sidebar.selectbox("", ["Azul Oscuro (Defecto)", "Verde Hacker", "Blanco Elegante", "Rojo Táctico"])

if tema == "Blanco Elegante": c_bg = "#F8FAFC"; c_card = "#FFFFFF"; c_text = "#0F172A"; c_sub = "#475569"; c_border = "#CBD5E1"; c_acc = "#0284C7"; c_btn = "#E2E8F0"
elif tema == "Rojo Táctico": c_bg = "#0A0000"; c_card = "#1A0505"; c_text = "#FECACA"; c_sub = "#FCA5A5"; c_border = "#7F1D1D"; c_acc = "#EF4444"; c_btn = "#450A0A"
elif tema == "Verde Hacker": c_bg = "#000000"; c_card = "#051A05"; c_text = "#4ADE80"; c_sub = "#22C55E"; c_border = "#14532D"; c_acc = "#10B981"; c_btn = "#064E3B"
else: c_bg = "#0B1120"; c_card = "#1E293B"; c_text = "#F1F5F9"; c_sub = "#94A3B8"; c_border = "#334155"; c_acc = "#38BDF8"; c_btn = "#0F172A"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {c_bg}; color: {c_text}; font-family: 'Inter', sans-serif; }}
    [data-testid="stSidebar"] {{ background-color: {c_card} !important; border-right: 1px solid {c_border}; }}
    .glass-card {{ background: {c_card}; border: 1px solid {c_border}; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .team-logo {{ width: 60px; height: 60px; object-fit: contain; margin-bottom: 5px; }}
    .team-name {{ font-size: 14px; font-weight: bold; color: {c_text}; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}}
    .winrate-text {{ font-size: 13px; color: {c_acc}; font-weight: 900; margin-bottom: 5px; background: {c_btn}; padding: 2px 8px; border-radius: 10px; display: inline-block; }}
    .form-container {{ display: flex; gap: 4px; justify-content: center; margin-top: 5px; }}
    .tower-plate {{ width: 14px; height: 8px; border-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }}
    .win {{ background-color: #10B981; }}
    .loss {{ background-color: #EF4444; }}
    .unknown {{ background-color: #475569; opacity: 0.5; }}
    .vs-text {{ font-size: 20px; font-weight: bold; color: {c_acc}; margin: 0 10px; }}
    .badge-live {{ background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite;}}
    .badge-time {{ background: {c_acc}; color: {c_bg}; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }}
    .prob-box {{ background: {c_btn}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; margin-bottom: 15px; transition: all 0.3s ease; }}
    .prob-number {{ font-size: 32px; font-weight: 900; color: {c_acc}; }}
    .stream-btn {{ background-color: #9146FF; color: white !important; padding: 8px 12px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: bold; display: block; margin-top: 15px; text-align: center; transition: 0.2s; }}
    .stream-btn:hover {{ background-color: #772CE8; transform: scale(1.02); }}
    .sniper-alert {{ background: rgba(16, 185, 129, 0.15); border: 2px dashed #10B981; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center; color: #10B981; font-weight: bold; font-size: 16px; animation: pulse 1.5s infinite; text-transform: uppercase; letter-spacing: 1px; }}
    div.stButton > button {{ background-color: {c_btn}; color: {c_acc}; border: 1px solid {c_border}; font-weight: bold; border-radius: 8px;