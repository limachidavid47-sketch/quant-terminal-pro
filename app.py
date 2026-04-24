import streamlit as st
import requests
import os
import math
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y LOGIN
# ==========================================
st.set_page_config(page_title="Quant Elite V14", layout="wide", initial_sidebar_state="expanded")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("""
        <style>
        .stApp { background-color: #05080F; color: #F8FAFC; }
        .login-box { background: #0F172A; border: 1px solid #334155; border-radius: 15px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); text-align: center; }
        .login-title { color: #10B981; font-size: 28px; font-weight: 900; letter-spacing: 2px; margin-bottom: 5px; }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.markdown("<div class='login-title'>⚡ TERMINAL QUANT V14</div>", unsafe_allow_html=True)
            st.markdown("<p style='color:#64748B; margin-bottom:20px;'>Motor Analítico Multi-Mercado</p>", unsafe_allow_html=True)
            
            u = st.text_input("Usuario", key="login_u")
            p = st.text_input("Contraseña", type="password", key="login_p")
            
            if st.button("Iniciar Conexión", use_container_width=True):
                if u == st.secrets["usuario"] and p == st.secrets["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else: st.error("❌ Acceso Denegado.")
            st.markdown("</div>", unsafe_allow_html=True)
        return False
    return True

if not check_password(): st.stop()

# ==========================================
# 2. EXTRACCIÓN DE DATOS CRUDOS (RAW DATA)
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
def get_raw_history(slug, team_id):
    """Descarga los últimos 25 partidos, filtra los 10 terminados y devuelve TODA la data cruda."""
    historial_raw = call_api(slug, f"teams/{team_id}/matches", "per_page=25")
    if not historial_raw: return [], 0.50, ['unknown']*5
    
    historial_limpio = [m for m in historial_raw if m.get('status') == 'finished' and m.get('winner_id')]
    historial_limpio = historial_limpio[:10] # Nos quedamos con los 10 útiles
    
    if not historial_limpio: return [], 0.50, ['unknown']*5
    
    wins = 0
    form = []
    for match in historial_limpio:
        if str(match.get('winner_id')) == str(team_id):
            wins += 1
            form.append('win')
        else:
            form.append('loss')
            
    winrate = wins / len(historial_limpio)
    while len(form) < 5: form.append('unknown') 
    
    return historial_limpio, winrate, form[:5]

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(round(monto, 2)))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

# ==========================================
# 3. MOTOR CUANTITATIVO (EL TRABAJO SUCIO)
# ==========================================
def motor_cuantitativo_avanzado(hist_t1, hist_t2, wr_t1, wr_t2, mercado, opcion, linea_casino):
    """
    Toma la data de las últimas 10 partidas de ambos y calcula la probabilidad EXACTA
    según el mercado seleccionado.
    """
    # Si no hay data suficiente, volvemos a la media neutral
    if not hist_t1 or not hist_t2: return 0.50
    
    prob_base = 0.50
    total_wr = wr_t1 + wr_t2
    if total_wr == 0: total_wr = 1 # Evitar división por cero

    # 1. MERCADO: GANADOR DEL PARTIDO
    if "Ganador" in mercado:
        if opcion == "Equipo A": prob_base = wr_t1 / total_wr
        else: prob_base = wr_t2 / total_wr

    # 2. MERCADO: HANDICAP
    elif "Handicap" in mercado:
        # Castigamos la probabilidad base según lo grande que sea la línea del casino
        # Ej: Un handicap de -5.5 kills reduce la probabilidad de ganar la apuesta en un ~15%
        prob_win = wr_t1 / total_wr if opcion == "Equipo A" else wr_t2 / total_wr
        dificultad = (abs(linea_casino) * 0.025) # 2.5% de castigo por cada punto de handicap
        prob_base = prob_win - dificultad if linea_casino < 0 else prob_win + dificultad

    # 3. MERCADO: TOTAL KILLS / TOTAL TORRES / DURACIÓN (LÍNEAS OVER/UNDER)
    elif "Total" in mercado or "Duración" in mercado:
        # Simulamos la agresividad basada en el WinRate combinado. 
        # Equipos que ganan mucho (WR alto combinado) suelen hacer partidas más limpias y rápidas.
        momentum_combinado = (wr_t1 + wr_t2) / 2
        
        # Si la línea del casino es muy baja, el "Más (+)" es muy probable
        # Aquí cruzamos la línea del casino con el momentum histórico
        if opcion == "Más (+)":
            prob_base = 0.50 + (momentum_combinado - 0.50) * 0.3
            if linea_casino > 0 and linea_casino < 25: prob_base += 0.10 # Línea baja = Over fácil
        else: # Menos (-)
            prob_base = 0.50 - (momentum_combinado - 0.50) * 0.3
            if linea_casino > 35: prob_base += 0.10 # Línea alta = Under fácil

    # 4. MERCADO: PRIMEROS OBJETIVOS (Roshan, Dragón, Lord, 1ra Sangre)
    elif "Primer" in mercado or "Ambos" in mercado:
        # El control temprano de objetivos está altamente correlacionado con el WinRate,
        # pero es más volátil que ganar el partido. Comprimimos la ventaja.
        prob_win = wr_t1 / total_wr if opcion == "Equipo A" else wr_t2 / total_wr
        prob_base = 0.50 + ((prob_win - 0.50) * 0.7) # Factor de volatilidad (70% del WR real)

    # 5. MERCADO: KILLS POR EQUIPO
    elif "Kills Equipo" in mercado:
        prob_win = wr_t1 / total_wr if opcion == "Equipo A" else wr_t2 / total_wr
        # Generalmente, el equipo que gana hace más kills.
        prob_base = prob_win

    # Topamos los límites para evitar apuestas irracionales de Kelly
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
    .prob-box {{ background: {c_btn}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; margin-bottom: 15px; }}
    .prob-number {{ font-size: 28px; font-weight: bold; color: {c_acc}; }}
    .stream-btn {{ background-color: #9146FF; color: white !important; padding: 6px 12px; border-radius: 8px; text-decoration: none; font-size: 11px; font-weight: bold; display: inline-block; margin-top: 15px; border: 1px solid #772CE8; width: 100%; text-align: center; transition: 0.2s; }}
    .stream-btn:hover {{ background-color: #772CE8; }}
    .sniper-alert {{ background: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; padding: 8px; border-radius: 8px; margin-bottom: 10px; text-align: center; color: #10B981; font-weight: bold; font-size: 12px; animation: pulse 2s infinite; }}
    div.stButton > button {{ background-color: {c_btn}; color: {c_acc}; border: 1px solid {c_border}; font-weight: bold; }}
    div.stButton > button:hover {{ background-color: {c_acc}; color: {c_bg}; }}
    @keyframes pulse {{ 0% {{opacity: 1;}} 50% {{opacity: 0.5;}} 100% {{opacity: 1;}} }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. SIDEBAR
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
    "League of Legends": {"slug": "lol", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Dragones", "Primer Dragón", "Kills Equipo A", "Kills Equipo B", "Duración de Partida"]},
    "Dota 2": {"slug": "dota2", "mercados": ["Ganador del Partido", "Handicap de Kills", "Primer Roshan", "Total Torres", "Kills Equipo A", "Kills Equipo B", "Duración de Partida"]},
    "Mobile Legends": {"slug": "mobile-legends", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Kills", "Primer Lord", "Duración de Partida"]}
}

st.sidebar.markdown(f"<h3 style='color:{c_text};'>🎮 Disciplina</h3>", unsafe_allow_html=True)
juego_sel = st.sidebar.radio("", list(juegos_config.keys()))
slug = juegos_config[juego_sel]["slug"]
mercados_list = juegos_config[juego_sel]["mercados"]

# ==========================================
# 6. RADAR QUANT (SNIPER Y MOTOR 10 PARTIDAS)
# ==========================================
st.markdown(f"<h2 style='color:{c_text};'>📡 Radar Quant: {juego_sel}</h2>", unsafe_allow_html=True)
    
running = call_api(slug, "matches/running", "per_page=10")
upcoming = call_api(slug, "matches/upcoming", "per_page=40&sort=begin_at")
partidos_totales = running + upcoming

hoy = datetime.now()
str_hoy = hoy.strftime("%Y-%m-%d")
str_mañana = (hoy + timedelta(days=1)).strftime("%Y-%m-%d")

partidos_filtrados = [p for p in partidos_totales if p['status'] == 'running' or p['begin_at'].startswith(str_hoy) or p['begin_at'].startswith(str_mañana)]
partidos_mostrar = partidos_filtrados[:16]

if not partidos_mostrar:
    st.info("No hay partidos oficiales programados para las próximas 48 horas.")
else:
    col1, col2 = st.columns(2)
    for i, m in enumerate(partidos_mostrar):
        opp = m.get('opponents', [])
        if len(opp) < 2: continue
        
        t1, t2 = opp[0]['opponent'], opp[1]['opponent']
        img1 = t1['image_url'] if t1['image_url'] else 'https://via.placeholder.com/55'
        img2 = t2['image_url'] if t2['image_url'] else 'https://via.placeholder.com/55'
        
        # EL TRABAJO SUCIO: Traemos data cruda, winrate y forma de las últimas 10
        hist_t1, wr_t1, form_t1 = get_raw_history(slug, t1['id'])
        hist_t2, wr_t2, form_t2 = get_raw_history(slug, t2['id'])
        
        txt_wr1 = f"{wr_t1*100:.0f}%" if hist_t1 else "S/D"
        txt_wr2 = f"{wr_t2*100:.0f}%" if hist_t2 else "S/D"
        
        html_torres_t1 = "".join([f"<div class='tower-plate {res}'></div>" for res in form_t1])
        html_torres_t2 = "".join([f"<div class='tower-plate {res}'></div>" for res in form_t2])
        
        # ALERTA SNIPER BASE (75% a 99%)
        val_wr1 = wr_t1 if hist_t1 else 0.50
        val_wr2 = wr_t2 if hist_t2 else 0.50
        prob_base_t1 = val_wr1 / (val_wr1 + val_wr2) if (val_wr1 + val_wr2) > 0 else 0.50
        prob_base_t2 = val_wr2 / (val_wr1 + val_wr2) if (val_wr1 + val_wr2) > 0 else 0.50

        alerta_html = ""
        if 0.75 <= prob_base_t1 <= 0.99:
            alerta_html = f"<div class='sniper-alert'>🎯 ALERTA SNIPER: {t1['name']} tiene ventaja crítica ({prob_base_t1*100:.1f}%)</div>"
        elif 0.75 <= prob_base_t2 <= 0.99:
            alerta_html = f"<div class='sniper-alert'>🎯 ALERTA SNIPER: {t2['name']} tiene ventaja crítica ({prob_base_t2*100:.1f}%)</div>"

        # TIEMPO Y STREAMING
        if m['status'] == 'running':
            badge = "<span class='badge-live'>🔴 EN VIVO</span>"
        else:
            dt_utc = datetime.strptime(m['begin_at'], "%Y-%m-%dT%H:%M:%SZ")
            dt_bol = dt_utc - timedelta(hours=4)
            badge = f"<span class='badge-time'>🕒 Hoy {dt_bol.strftime('%H:%M')}</span>" if dt_bol.strftime("%Y-%m-%d") == str_hoy else f"<span class='badge-time'>📅 {dt_bol.strftime('%d/%m')} 🕒 {dt_bol.strftime('%H:%M')}</span>"

        stream_link = m.get('official_video_url') or (m['streams_list'][0].get('raw_url') if m.get('streams_list') else '')
        boton_stream = f'<a href="{stream_link}" target="_blank" class="stream-btn">📺 Ver Transmisión Oficial</a>' if stream_link else ''

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
                {boton_stream}
            </div>
            {alerta_html}
            """, unsafe_allow_html=True)

            with st.expander(f"⚙️ Analítica Multi-Mercado"):
                sel_mer = st.selectbox("Mercado a Evaluar:", mercados_list, key=f"mer_{i}")
                
                c_izq, c_der = st.columns(2)
                with c_izq:
                    if "Total" in sel_mer or "Duración" in sel_mer:
                        sel_opcion = st.selectbox("Opción:", ["Más (+)", "Menos (-)"], key=f"op_{i}")
                    else:
                        sel_opcion = st.selectbox("A favor de:", ["Equipo A", "Equipo B"], key=f"op_{i}")
                    linea = st.number_input("Línea del Casino:", value=0.0, step=0.5, key=f"l_{i}")
                
                with c_der:
                    # PROCESAMIENTO MATEMÁTICO REAL
                    prob_final = motor_cuantitativo_avanzado(hist_t1, hist_t2, val_wr1, val_wr2, sel_mer, sel_opcion, linea)
                    
                    st.markdown(f"""
                    <div class="prob-box">
                        <div style="font-size:10px; color:{c_text}; text-transform:uppercase;">Probabilidad Calculada</div>
                        <div class="prob-number">{prob_final*100:.1f}%</div>
                        <div style="font-size:10px; color:{c_sub};">Cuota Mínima Sugerida: {1/prob_final:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    cuota = st.number_input("Cuota que pagan:", value=1.00, step=0.01, key=f"c_{i}")

                if cuota > 1.01: 
                    if cuota > (1/prob_final):
                        kelly = (((cuota - 1) * prob_final) - (1 - prob_final)) / (cuota - 1)
                        stake = (kelly * 0.25) * bank_actual
                        if stake > 0:
                            st.success(f"🔥 BINGO. Apuesta Sugerida: {stake:.2f} U")
                            if st.button("Registrar Operación", key=f"btn_{i}", use_container_width=True):
                                gestionar_bank(bank_actual - stake)
                                st.rerun()
                    else:
                        st.warning(f"❌ Cuota basura. El algoritmo exige {1/prob_final:.2f}+")