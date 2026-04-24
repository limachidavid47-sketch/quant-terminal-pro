import streamlit as st
import requests
import os
import math
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y LOGIN BLINDADO
# ==========================================
st.set_page_config(page_title="Quant Elite V11", layout="wide", initial_sidebar_state="expanded")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("""
        <style>
        .stApp { background-color: #05080F; color: #F8FAFC; }
        .login-box {
            background: #0F172A; border: 1px solid #334155; border-radius: 15px; 
            padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); text-align: center;
        }
        .login-title { color: #10B981; font-size: 28px; font-weight: 900; letter-spacing: 2px; margin-bottom: 5px; }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.markdown("<div class='login-title'>⚡ TERMINAL QUANT V11</div>", unsafe_allow_html=True)
            st.markdown("<p style='color:#64748B; margin-bottom:20px;'>Acceso de Operador (Motor Económico)</p>", unsafe_allow_html=True)
            
            u = st.text_input("Usuario", key="login_u")
            p = st.text_input("Contraseña", type="password", key="login_p")
            
            if st.button("Iniciar Conexión", use_container_width=True):
                if u == st.secrets["usuario"] and p == st.secrets["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else: 
                    st.error("❌ Acceso Denegado.")
            st.markdown("</div>", unsafe_allow_html=True)
        return False
    return True

if not check_password(): st.stop()

# ==========================================
# 2. MOTOR DE DATOS (HONESTIDAD EN WINRATES)
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

@st.cache_data(ttl=60)
def call_api(game_slug, endpoint, params_str=""):
    url = f"https://api.pandascore.co/{game_slug}/{endpoint}?{params_str}"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

@st.cache_data(ttl=300)
def get_team_stats(slug, team_id):
    historial = call_api(slug, f"teams/{team_id}/matches", "sort=-end_at&filter[status]=finished&per_page=10")
    if not historial: return None, ['unknown']*5
    
    wins = 0
    form = []
    for match in historial:
        if str(match.get('winner_id')) == str(team_id):
            wins += 1
            form.append('win')
        else:
            form.append('loss')
    
    winrate = wins / len(historial)
    while len(form) < 5: form.append('unknown') 
    return winrate, form[:5]

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(round(monto, 2)))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

# ==========================================
# 3. TEMAS VISUALES
# ==========================================
st.sidebar.markdown("### 🎨 Apariencia")
tema = st.sidebar.selectbox("", ["Azul Oscuro (Defecto)", "Verde Hacker", "Blanco Elegante", "Rojo Táctico"])

if tema == "Blanco Elegante":
    c_bg = "#F8FAFC"; c_card = "#FFFFFF"; c_text = "#0F172A"; c_sub = "#475569"; c_border = "#CBD5E1"; c_acc = "#0284C7"; c_btn = "#E2E8F0"
elif tema == "Rojo Táctico":
    c_bg = "#0A0000"; c_card = "#1A0505"; c_text = "#FECACA"; c_sub = "#FCA5A5"; c_border = "#7F1D1D"; c_acc = "#EF4444"; c_btn = "#450A0A"
elif tema == "Verde Hacker":
    c_bg = "#000000"; c_card = "#051A05"; c_text = "#4ADE80"; c_sub = "#22C55E"; c_border = "#14532D"; c_acc = "#10B981"; c_btn = "#064E3B"
else: # Azul Oscuro
    c_bg = "#0B1120"; c_card = "#1E293B"; c_text = "#F1F5F9"; c_sub = "#94A3B8"; c_border = "#334155"; c_acc = "#38BDF8"; c_btn = "#0F172A"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {c_bg}; color: {c_text}; }}
    [data-testid="stSidebar"] {{ background-color: {c_card} !important; border-right: 1px solid {c_border}; }}
    .glass-card {{ background: {c_card}; border: 1px solid {c_border}; border-radius: 12px; padding: 15px; margin-bottom: 10px; }}
    .team-logo {{ width: 55px; height: 55px; object-fit: contain; margin-bottom: 5px; }}
    .team-name {{ font-size: 14px; font-weight: bold; color: {c_text}; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}}
    .winrate-text {{ font-size: 12px; color: {c_acc}; font-weight: bold; margin-bottom: 5px; }}
    .form-container {{ display: flex; gap: 4px; justify-content: center; margin-top: 5px; }}
    .tower-plate {{ width: 12px; height: 6px; border-radius: 2px; }}
    .win {{ background-color: #10B981; }}
    .loss {{ background-color: #EF4444; }}
    .unknown {{ background-color: #475569; opacity: 0.3; }}
    .vs-text {{ font-size: 18px; font-weight: bold; color: {c_acc}; margin: 0 10px; }}
    .badge-live {{ background: #EF4444; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite;}}
    .badge-time {{ background: {c_acc}; color: {c_bg}; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
    .prob-box {{ background: {c_btn}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; margin-bottom: 15px; transition: all 0.3s ease; }}
    .prob-number {{ font-size: 28px; font-weight: bold; color: {c_acc}; }}
    div.stButton > button {{ background-color: {c_btn}; color: {c_acc}; border: 1px solid {c_border}; font-weight: bold; }}
    div.stButton > button:hover {{ background-color: {c_acc}; color: {c_bg}; }}
    @keyframes pulse {{ 0% {{opacity: 1;}} 50% {{opacity: 0.5;}} 100% {{opacity: 1;}} }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR (BANKROLL Y JUEGOS)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h2 style='color:{c_acc}; text-align:center;'>🏦 Mi Bankroll</h2>", unsafe_allow_html=True)

nuevo_bank = st.sidebar.number_input("Ajustar Saldo (U):", value=float(bank_actual), step=10.0)
if st.sidebar.button("💾 Guardar Saldo", use_container_width=True):
    gestionar_bank(nuevo_bank)
    st.rerun()

st.sidebar.markdown(f"<h1 style='text-align:center; color:{c_text};'>{bank_actual:.2f} U</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")

juegos_config = {
    "League of Legends": {"slug": "lol", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Dragones", "Kills Equipo A", "Kills Equipo B"]},
    "Dota 2": {"slug": "dota2", "mercados": ["Ganador del Partido", "Handicap de Kills", "Primer Roshan", "Kills Equipo A", "Kills Equipo B"]},
    "Mobile Legends": {"slug": "mobile-legends", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Kills", "Primer Lord"]}
}

st.sidebar.markdown(f"<h3 style='color:{c_text};'>🎮 Disciplina</h3>", unsafe_allow_html=True)
juego_sel = st.sidebar.radio("", list(juegos_config.keys()))
slug = juegos_config[juego_sel]["slug"]
mercados_list = juegos_config[juego_sel]["mercados"]

# ==========================================
# 5. ALGORITMO DE VENTAJA DE ORO
# ==========================================
def calculate_gold_impact(gold_diff, minute, game_slug):
    """
    Calcula cómo la diferencia de oro impacta la probabilidad según el minuto.
    Retorna un ajuste a la probabilidad base (ej. +0.15 o -0.20).
    """
    if minute <= 0: return 0
    
    # 1. Normalizar el oro según el juego (En Dota hay más oro total que en LoL)
    divisor_oro = 10000 if game_slug == "dota2" else 8000
    impacto_bruto = gold_diff / divisor_oro
    
    # 2. Factor de Decadencia por Tiempo (Logístico)
    # 3k oro al min 10 es letal (multiplicador alto). 3k al min 40 no es nada (multiplicador bajo).
    # Fórmula: Impacto = Impacto Bruto * (1 / (1 + (minuto / 25)^2))
    # Esto hace que el impacto del oro caiga rápidamente después del minuto 25-30.
    time_decay = 1 / (1 + (minute / 25)**2)
    
    # Ajuste final limitado entre -40% y +40%
    impacto_final = max(-0.40, min(0.40, impacto_bruto * time_decay))
    return impacto_final

# ==========================================
# 6. RADAR EN VIVO
# ==========================================
st.markdown(f"<h2 style='color:{c_text};'>📡 Radar Quant: {juego_sel}</h2>", unsafe_allow_html=True)
    
running = call_api(slug, "matches/running", "per_page=10")
upcoming = call_api(slug, "matches/upcoming", "per_page=20&sort=begin_at")
partidos_totales = running + upcoming
hoy = datetime.now().strftime("%Y-%m-%d")
partidos_hoy = [p for p in partidos_totales if p['begin_at'].startswith(hoy) or p['status'] == 'running']

if not partidos_hoy:
    st.info("No hay partidos oficiales programados para hoy.")
else:
    col1, col2 = st.columns(2)
    for i, m in enumerate(partidos_hoy):
        opp = m.get('opponents', [])
        if len(opp) < 2: continue
        
        t1, t2 = opp[0]['opponent'], opp[1]['opponent']
        img1 = t1['image_url'] if t1['image_url'] else 'https://via.placeholder.com/55'
        img2 = t2['image_url'] if t2['image_url'] else 'https://via.placeholder.com/55'
        
        wr_t1, form_t1 = get_team_stats(slug, t1['id'])
        wr_t2, form_t2 = get_team_stats(slug, t2['id'])
        
        txt_wr1 = f"{wr_t1*100:.0f}%" if wr_t1 is not None else "S/D"
        txt_wr2 = f"{wr_t2*100:.0f}%" if wr_t2 is not None else "S/D"
        
        html_torres_t1 = "".join([f"<div class='tower-plate {res}'></div>" for res in form_t1])
        html_torres_t2 = "".join([f"<div class='tower-plate {res}'></div>" for res in form_t2])
        
        if m['status'] == 'running':
            badge = "<span class='badge-live'>🔴 EN VIVO</span>"
        else:
            dt_utc = datetime.strptime(m['begin_at'], "%Y-%m-%dT%H:%M:%SZ")
            hora_bol = (dt_utc - timedelta(hours=4)).strftime("%H:%M")
            badge = f"<span class='badge-time'>🕒 {hora_bol}</span>"

        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
            <div class="glass-card">
                <div style="margin-bottom: 10px; font-size: 11px; color: {c_sub}; display: flex; justify-content: space-between;">
                    <span>🏆 {m['league']['name']}</span>{badge}
                </div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 40%;">
                        <div class="team-name">{t1['name']}</div>
                        <img src="{img1}" class="team-logo"><br>
                        <div class="winrate-text">WR: {txt_wr1}</div>
                        <div class="form-container">{html_torres_t1}</div>
                    </div>
                    <div class="vs-text">VS</div>
                    <div style="width: 40%;">
                        <div class="team-name">{t2['name']}</div>
                        <img src="{img2}" class="team-logo"><br>
                        <div class="winrate-text">WR: {txt_wr2}</div>
                        <div class="form-container">{html_torres_t2}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"⚙️ Operar & Simulación Económica"):
                sel_mer = st.selectbox("Mercado:", mercados_list, key=f"mer_{i}")
                
                c_izq, c_der = st.columns(2)
                with c_izq:
                    if "Total" in sel_mer or "Duración" in sel_mer:
                        sel_opcion = st.selectbox("Opción:", ["Más (+)", "Menos (-)"], key=f"op_{i}")
                    else:
                        sel_opcion = st.selectbox("A favor de:", [t1['name'], t2['name']], key=f"op_{i}")
                    linea = st.number_input("Línea Casino:", value=0.0, step=0.5, key=f"l_{i}")
                
                with c_der:
                    st.write("")
                    remontada = st.checkbox("💸 Modelo Económico (Oro)", key=f"rem_{i}", help="Ajusta la probabilidad insertando la ventaja de oro en vivo.")

                ajuste_oro = 0
                if remontada:
                    st.markdown(f"<div style='border-top:1px solid {c_border}; margin:10px 0;'></div>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:{c_text}; font-size:12px;'>Inserte la ventaja actual del equipo seleccionado ({sel_opcion}):</p>", unsafe_allow_html=True)
                    c_min, c_oro = st.columns(2)
                    min_actual = c_min.number_input("Minuto de Partida:", min_value=1, max_value=60, value=15, key=f"min_{i}")
                    # Positivo = Oro a favor / Negativo = Oro en contra
                    diff_oro = c_oro.number_input("Dif. de Oro (Ej: -2500):", value=0, step=500, key=f"oro_{i}")
                    
                    ajuste_oro = calculate_gold_impact(diff_oro, min_actual, slug)

                # --- CÁLCULO FINAL DE PROBABILIDAD ---
                val_wr1 = wr_t1 if wr_t1 is not None else 0.50
                val_wr2 = wr_t2 if wr_t2 is not None else 0.50
                
                prob_base = 0.50
                if "Ganador" in sel_mer or "Kills Equipo" in sel_mer or sel_opcion in [t1['name'], t2['name']]:
                    total_wr = val_wr1 + val_wr2
                    if total_wr > 0:
                        if sel_opcion == t1['name']: prob_base = val_wr1 / total_wr
                        elif sel_opcion == t2['name']: prob_base = val_wr2 / total_wr
                else:
                    prob_base = 0.50 + (((val_wr1 + val_wr2) / 2) - 0.50) * 0.5 
                
                # Aplicamos el motor económico si está activado
                prob_final = prob_base + ajuste_oro
                prob_final = max(0.05, min(0.95, prob_final))

                st.markdown(f"""
                <div class="prob-box">
                    <div style="font-size:12px; color:{c_text}; text-transform:uppercase;">Probabilidad Calculada</div>
                    <div class="prob-number">{prob_final*100:.1f}%</div>
                    <div style="font-size:10px; color:{c_sub};">Cuota Mínima Sugerida: {1/prob_final:.2f}</div>
                </div>
                """, unsafe_allow_html=True)

                cuota = st.number_input("Cuota Casino:", value=1.00, step=0.01, key=f"c_{i}")

                if cuota > 1.01: 
                    if cuota > (1/prob_final):
                        kelly = (((cuota - 1) * prob_final) - (1 - prob_final)) / (cuota - 1)
                        stake = (kelly * 0.25) * bank_actual
                        if stake > 0:
                            st.success(f"🔥 VALOR. Apuesta Sugerida: {stake:.2f} U")
                            if st.button("Ejecutar Operación", key=f"btn_{i}", use_container_width=True):
                                gestionar_bank(bank_actual - stake)
                                st.rerun()
                    else:
                        st.warning(f"❌ Sin valor matemático.")