import streamlit as st
import requests
import os
import math
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD, ACCESO QUANT Y ENLACE MÁGICO
# ==========================================
st.set_page_config(page_title="Quant Elite V26", layout="wide", initial_sidebar_state="expanded")

def check_password():
    token = ""
    try:
        if "token" in st.query_params: token = st.query_params["token"]
    except:
        params = st.experimental_get_query_params()
        if "token" in params: token = params["token"][0]
        
    if token == "capo": st.session_state["password_correct"] = True
    if st.session_state.get("password_correct", False): return True

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
        st.markdown("<div class='login-title'>⚡ QUANT TERMINAL V26</div>", unsafe_allow_html=True)
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
# 3. MOTOR CUANTITATIVO Y SIMULADOR DE ORO
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

    if "Ganador" in mercado or "Kills por Equipo" in mercado and "Carrera" not in mercado:
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

    # NUEVO: LÓGICA DE CARRERAS DE KILLS (RACE TO X)
    elif "Carrera" in mercado:
        prob_win = wr1 / total_wr if es_equipo_1 else wr2 / total_wr
        # Mientras más corta la carrera, más aleatoria es (varianza baja). 
        if "5" in mercado: varianza = 0.60
        elif "10" in mercado: varianza = 0.75
        else: varianza = 0.85 # Carrera a 15 premia más al equipo favorito
        prob_base = 0.50 + ((prob_win - 0.50) * varianza)

    return max(0.05, min(0.95, prob_base))

# ==========================================
# 4. TEMAS Y CSS
# ==========================================
st.sidebar.markdown("### 🎨 Apariencia")
tema = st.sidebar.selectbox("", ["Azul Oscuro (Defecto)", "Verde Hacker", "Blanco Elegante", "Rojo Táctico"])

if tema == "Blanco Elegante": c_bg = "#F8FAFC"; c_card = "#FFFFFF"; c_text = "#0F172A"; c_sub = "#475569"; c_border = "#CBD5E1"; c_acc = "#0284C7"; c_btn = "#E2E8F0"