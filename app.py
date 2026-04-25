import streamlit as st
import requests
import os
import math
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD, ACCESO QUANT Y ENLACE MÁGICO
# ==========================================
st.set_page_config(page_title="Quant Elite V27", layout="wide", initial_sidebar_state="expanded")

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
        st.markdown("<div class='login-title'>⚡ QUANT TERMINAL V27</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748B; margin-bottom:25px;'>OMNI-SISTEMA HFT (MOBAs + FPS)</p>", unsafe_allow_html=True)
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
# 2. MOTOR DE DATOS HFT (6 HORAS CACHÉ - 10 PARTIDOS)
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
# 3. MOTORES CUANTITATIVOS (MOBA & FPS)
# ==========================================
# MOTOR 1: ECONOMÍA MOBA
def calculate_gold_impact(gold_diff, minute, game_slug):
    if minute <= 0: return 0
    if game_slug == "dota2": divisor, pivote = 10000, 30
    elif game_slug == "mobile-legends": divisor, pivote = 5000, 12
    else: divisor, pivote = 8000, 25
    impacto_bruto = gold_diff / divisor
    return max(-0.40, min(0.40, impacto_bruto * (1 / (1 + (minute / pivote)**2))))

def motor_moba(wr1, wr2, mercado, opcion, linea_casino, t1_name):
    prob_base = 0.50
    total_wr = wr1 + wr2 if (wr1 + wr2) > 0 else 1
    es_eq1 = (opcion == t1_name)

    if "Ganador" in mercado or "Kills por" in mercado and "Carrera" not in mercado:
        prob_base = wr1 / total_wr if es_eq1 else wr2 / total_wr
    elif "Handicap" in mercado:
        prob_win = wr1 / total_wr if es_eq1 else wr2 / total_wr
        dificultad = (abs(linea_casino) * 0.025)
        prob_base = prob_win - dificultad if linea_casino < 0 else prob_win + dificultad
    elif "Total" in mercado or "Duración" in mercado:
        mom = (wr1 + wr2) / 2
        prob_base = 0.50 + (mom - 0.50) * 0.3 if "Más" in opcion else 0.50 - (mom - 0.50) * 0.3
        if linea_casino > 35: prob_base += 0.10 if "Más" not in opcion else 0
    elif "Primer" in mercado or "Primera" in mercado:
        prob_base = 0.50 + (((wr1 / total_wr if es_eq1 else wr2 / total_wr) - 0.50) * 0.7)
    elif "Carrera" in mercado:
        var = 0.60 if "5" in mercado else 0.75 if "10" in mercado else 0.85
        prob_base = 0.50 + (((wr1 / total_wr if es_eq1 else wr2 / total_wr) - 0.50) * var)
    return max(0.05, min(0.95, prob_base))

# MOTOR 2: TÁCTICA FPS (INFERENCIA BAYESIANA SIMPLIFICADA)
def motor_fps(wr1, wr2, mercado, opcion, linea, t1_name, f_blood, eco_adv):
    total_wr = wr1 + wr2 if (wr1 + wr2) > 0 else 1
    es_eq1 = (opcion == t1_name)
    prob_base = wr1 / total_wr if es_eq1 else wr2 / total_wr

    if "Handicap" in mercado:
        dificultad = (abs(linea) * 0.04) # En FPS, cada ronda vale más estadísticamente
        prob_base = prob_base - dificultad if linea < 0 else prob_base + dificultad
    elif "Total" in mercado:
        prob_base = 0.5 + ((wr1 + wr2) / 2 - 0.5) * 0.4 if "Más" in opcion else 0.5 - ((wr1 + wr2) / 2 - 0.5) * 0.4

    # Simulación Bayesiana In-Play
    if f_blood == "A favor": prob_base += 0.18
    elif f_blood == "En contra": prob_base -= 0.18

    if eco_adv == "Full Buy vs Eco": prob_base += 0.25
    elif eco_adv == "Eco vs Full Buy": prob_base -= 0.25

    return max(0.05, min(0.95, prob_base))

# ==========================================
# 4. TEMAS Y CSS
# ==========================================
st.sidebar.markdown("### 🎨 Apariencia")
tema = st.sidebar.selectbox("", ["Azul Oscuro (Defecto)", "Verde Hacker", "Rojo Táctico"])
colors = {"Azul Oscuro": ("#0B1120", "#1E293B", "#F1F5F9", "#38BDF8"), "Verde Hacker": ("#000000", "#051A05", "#4ADE80", "#10B981"), "Rojo Táctico": ("#0A0000", "#1A0505", "#FECACA", "#EF4444")}
c_bg, c_card, c_text, c_acc = colors[tema]
c_sub, c_border, c_btn = "#94A3B8", "#334155", "#0F172A"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {c_bg}; color: {c_text}; font-family: 'Inter', sans-serif; }}
    [data-testid="stSidebar"] {{ background-color: {c_card} !important; border-right: 1px solid {c_border}; }}
    .glass-card {{ background: {c_card}; border: 1px solid {c_border}; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .team-logo {{ width: 60px; height: 60px; object-fit: contain; margin-bottom: 5px; }}
    .winrate-text {{ font-size: 13px; color: {c_acc}; font-weight: 900; margin-bottom: 5px; background: {c_btn}; padding: 2px 8px; border-radius: 10px; display: inline-block; }}
    .tower-plate {{ width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin:0 2px; }}
    .win {{ background-color: #10B981; }} .loss {{ background-color: #EF4444; }} .unknown {{ background-color: #475569; }}
    .prob-box {{ background: {c_btn}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; margin-bottom: 15px; }}
    .prob-number {{ font-size: 32px; font-weight: 900; color: {c_acc}; }}
    .sniper-alert {{ background: rgba(16, 185, 129, 0.15); border: 2px dashed #10B981; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center; color: #10B981; font-weight: bold; animation: pulse 1.5s infinite; }}
    div.stButton > button {{ background-color: {c_btn}; color: {c_acc}; border: 1px solid {c_border}; font-weight: bold; border-radius: 8px; padding: 10px; }}
    [data-testid="stExpanderDetails"] {{ padding-bottom: 180px !important; }}
    @keyframes pulse {{ 0% {{opacity: 1;}} 50% {{opacity: 0.6;}} 100% {{opacity: 1;}} }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. SIDEBAR: EL INTERRUPTOR MAESTRO
# ==========================================
st.sidebar.markdown("---")
token_activo = False
try:
    if "token" in st.query_params and st.query_params["token"] == "capo": token_activo = True
except: pass
if token_activo: st.sidebar.markdown("<div style='background-color:#10B981; color:white; padding:5px; border-radius:5px; text-align:center; font-weight:bold; font-size:12px; margin-bottom:10px;'>🔓 MODO CAPO ACTIVO</div>", unsafe_allow_html=True)

st.sidebar.markdown(f"<h2 style='color:{c_acc}; text-align:center;'>🏦 Mi Bankroll</h2>", unsafe_allow_html=True)
nuevo_bank = st.sidebar.number_input("Ajustar Saldo (U):", value=float(bank_actual), step=10.0)
if st.sidebar.button("💾 Guardar Saldo", use_container_width=True): gestionar_bank(nuevo_bank); st.rerun()
st.sidebar.markdown(f"<h1 style='text-align:center; color:{c_text};'>{bank_actual:.2f} U</h1>", unsafe_allow_html=True)

st.sidebar.markdown("---")

# EL SWITCH PRINCIPAL
categoria = st.sidebar.radio("🌐 TIPO DE OPERACIÓN", ["⚔️ MOBAs (Estrategia)", "🔫 Shooters (Tácticos)"])
st.sidebar.markdown("---")

if categoria == "⚔️ MOBAs (Estrategia)":
    juegos_config = {
        "League of Legends": {"slug": "lol", "mercados": ["-- Seleccione un Mercado --", "Ganador del Partido", "Handicap", "Primera Sangre", "Primer Dragón", "Carrera a 5 Kills", "Total Dragones", "Total Barones", "Total Torres", "Total Kills", "Duración de Partida"]},
        "Dota 2": {"slug": "dota2", "mercados": ["-- Seleccione un Mercado --", "Ganador del Partido", "Handicap", "Primer Roshan", "Carrera a 10 Kills", "Total Torres", "Total Kills", "Duración de Partida"]},
        "Mobile Legends": {"slug": "mobile-legends", "mercados": ["-- Seleccione un Mercado --", "Ganador del Partido", "Handicap", "Primer Lord", "Carrera a 5 Kills", "Total Kills", "Duración de Partida"]}
    }
else:
    juegos_config = {
        "CS:GO 2": {"slug": "csgo", "mercados": ["-- Seleccione un Mercado --", "Ganador del Partido", "Handicap de Rondas", "Total de Rondas (O/U)", "Ganador Ronda de Pistolas"]},
        "Valorant": {"slug": "valorant", "mercados": ["-- Seleccione un Mercado --", "Ganador del Partido", "Handicap de Rondas", "Total de Rondas (O/U)", "Ganador Ronda de Pistolas"]}
    }

st.sidebar.markdown(f"<h3 style='color:{c_text};'>🎮 Disciplina</h3>", unsafe_allow_html=True)
juego_sel = st.sidebar.radio("", list(juegos_config.keys()))
slug = juegos_config[juego_sel]["slug"]
mercados_list = juegos_config[juego_sel]["mercados"]

if st.sidebar.button("🗑️ Limpiar Caché", use_container_width=True): st.cache_data.clear(); st.rerun()

# ==========================================
# 6. RADAR QUANT CORE
# ==========================================
st.markdown(f"<h2 style='color:{c_text};'>📡 Radar Quant: {juego_sel}</h2>", unsafe_allow_html=True)
    
running = call_api_live(slug, "matches/running", "per_page=10")
upcoming = call_api_live(slug, "matches/upcoming", "per_page=30&sort=begin_at")
partidos_totales = running + upcoming

hoy = datetime.now()
str_hoy = hoy.strftime("%Y-%m-%d")
str_mañana = (hoy + timedelta(days=1)).strftime("%Y-%m-%d")

partidos_filtrados = [p for p in partidos_totales if p['status'] == 'running' or p['begin_at'].startswith(str_hoy) or p['begin_at'].startswith(str_mañana)]

if not partidos_filtrados: st.info("Escaneando servidores. No hay actividad oficial inmediata.")
else:
    c1, c2 = st.columns(2)
    for i, m in enumerate(partidos_filtrados[:16]):
        opp = m.get('opponents', [])
        if len(opp) < 2: continue
        t1, t2 = opp[0]['opponent'], opp[1]['opponent']
        
        _, wr1, form1 = fetch_historical_data(slug, t1['id'])
        _, wr2, form2 = fetch_historical_data(slug, t2['id'])

        badge = "<span class='badge-live'>🔴 EN VIVO</span>" if m['status'] == 'running' else "<span class='badge-time'>🕒 PRÓXIMO</span>"

        with (c1 if i % 2 == 0 else c2):
            st.markdown(f"""
            <div class="glass-card">
                <div style="margin-bottom: 10px; font-size: 11px; display: flex; justify-content: space-between;"><span>🏆 {m['league']['name']}</span>{badge}</div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 40%;"><div style="font-size:12px; font-weight:bold;">{t1['name']}</div><img src="{t1.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr1*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form1])}</div></div>
                    <div style="font-size: 20px; font-weight: bold; color: {c_acc};">VS</div>
                    <div style="width: 40%;"><div style="font-size:12px; font-weight:bold;">{t2['name']}</div><img src="{t2.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr2*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form2])}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"⚙️ Analítica y Operación"):
                sel_mer = st.selectbox("Mercado:", mercados_list, key=f"mer_{i}")
                
                if sel_mer != "-- Seleccione un Mercado --":
                    c_izq, c_der = st.columns(2)
                    with c_izq:
                        if "Total" in sel_mer or "Duración" in sel_mer: sel_opcion = st.radio("Opción:", ["Más (+)", "Menos (-)"], horizontal=True, key=f"op_{i}")
                        else: sel_opcion = st.radio("A favor de:", [t1['name'], t2['name']], horizontal=True, key=f"op_{i}")
                        linea = st.number_input("Línea de Casino:", value=0.0, step=0.5, key=f"l_{i}")
                    
                    with c_der:
                        st.write("")
                        prob_final = 0.50
                        
                        # RUTA MOBA
                        if categoria == "⚔️ MOBAs (Estrategia)":
                            remontada = st.checkbox("💸 Modelo Oro", key=f"rem_{i}")
                            ajuste_oro = 0
                            if remontada:
                                c_min, c_oro = st.columns(2)
                                min_actual = c_min.number_input("Min:", value=15, key=f"min_{i}")
                                diff_oro = c_oro.number_input("Oro Diff:", value=0, step=500, key=f"oro_{i}")
                                ajuste_oro = calculate_gold_impact(diff_oro, min_actual, slug)
                            prob_base = motor_moba(wr1, wr2, sel_mer, sel_opcion, linea, t1['name'])
                            prob_final = max(0.05, min(0.95, prob_base + ajuste_oro))
                        
                        # RUTA FPS SHOOTERS
                        else:
                            st.markdown("<p style='font-size:11px; color:#10B981;'>Simulador Bayesiano In-Play</p>", unsafe_allow_html=True)
                            f_blood = st.selectbox("Primera Sangre (Ronda):", ["Neutral", "A favor", "En contra"], key=f"fb_{i}")
                            eco_adv = st.selectbox("Economía (Armas):", ["Igualados", "Full Buy vs Eco", "Eco vs Full Buy"], key=f"eco_{i}")
                            prob_final = motor_fps(wr1, wr2, sel_mer, sel_opcion, linea, t1['name'], f_blood, eco_adv)

                    st.markdown(f"""
                    <div class="prob-box">
                        <div style="font-size:10px; text-transform:uppercase;">Probabilidad Algoritmo</div>
                        <div class="prob-number">{prob_final*100:.1f}%</div>
                        <div style="font-size:10px; color:{c_sub};">Cuota Mínima: {1/prob_final:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if 0.75 <= prob_final <= 0.99:
                        st.markdown(f"<div class='sniper-alert'>🎯 ¡SNIPER ALERT!</div>", unsafe_allow_html=True)

                    cuota = st.number_input("Cuota Casino:", value=1.00, step=0.01, key=f"c_{i}")
                    if cuota > 1.01: 
                        if cuota > (1/prob_final):
                            kelly = (((cuota - 1) * prob_final) - (1 - prob_final)) / (cuota - 1)
                            stake = (kelly * 0.25) * bank_actual
                            if stake > 0:
                                st.success(f"🔥 Sugerido: {stake:.2f} U")
                                if st.button("Registrar", key=f"btn_{i}", use_container_width=True):
                                    gestionar_bank(bank_actual - stake)
                                    st.rerun()
                        else: st.warning("❌ Cuota sin valor.")