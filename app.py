import streamlit as st
import requests
import os
import math
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y LOGIN BLINDADO
# ==========================================
st.set_page_config(page_title="Quant Elite V16", layout="wide", initial_sidebar_state="expanded")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("""
        <style>
        .stApp { background-color: #05080F; color: #F8FAFC; }
        .login-box { background: #0F172A; border: 1px solid #334155; border-radius: 15px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); text-align: center; margin-top: 10vh; }
        .login-title { color: #10B981; font-size: 28px; font-weight: 900; letter-spacing: 2px; margin-bottom: 5px; }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.markdown("<div class='login-title'>⚡ TERMINAL QUANT V16</div>", unsafe_allow_html=True)
            st.markdown("<p style='color:#64748B; margin-bottom:20px;'>Sistema Autónomo HFT + Sniper</p>", unsafe_allow_html=True)
            
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
# 2. MOTOR DE DATOS ANTI-BLOQUEO
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

# NUEVA FUNCIÓN: Endpoint corregido y cache de 6 horas
@st.cache_data(ttl=21600, show_spinner=False)
def fetch_historical_data(game_slug, team_id):
    """Descarga los últimos 10 partidos terminados del equipo usando un endpoint más estable."""
    url = f"https://api.pandascore.co/{game_slug}/matches"
    params = f"filter[opponent_id]={team_id}&filter[status]=finished&sort=-end_at&per_page=10"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    
    try:
        res = requests.get(f"{url}?{params}", headers=headers)
        if res.status_code == 200:
            historial = res.json()
            if not historial: return [], None, ['unknown']*5
            
            wins = 0
            form = []
            for match in historial:
                # Comparamos IDs convirtiendo todo a string por seguridad
                if str(match.get('winner_id')) == str(team_id):
                    wins += 1
                    form.append('win')
                else:
                    form.append('loss')
                    
            winrate = wins / len(historial)
            while len(form) < 5: form.append('unknown') 
            return historial, winrate, form[:5]
        else:
            return [], None, ['unknown']*5
    except:
        return [], None, ['unknown']*5

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(round(monto, 2)))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

# ==========================================
# 3. MOTOR CUANTITATIVO MULTI-MERCADO
# ==========================================
def motor_cuantitativo_avanzado(hist_t1, hist_t2, wr_t1, wr_t2, mercado, opcion, linea_casino):
    if wr_t1 is None or wr_t2 is None: return 0.50
    
    prob_base = 0.50
    total_wr = wr_t1 + wr_t2
    if total_wr == 0: total_wr = 1 

    if "Ganador" in mercado:
        prob_base = wr_t1 / total_wr if opcion == "Equipo A" else wr_t2 / total_wr

    elif "Handicap" in mercado:
        prob_win = wr_t1 / total_wr if opcion == "Equipo A" else wr_t2 / total_wr
        dificultad = (abs(linea_casino) * 0.025)
        prob_base = prob_win - dificultad if linea_casino < 0 else prob_win + dificultad

    elif "Total" in mercado or "Duración" in mercado:
        momentum_combinado = (wr_t1 + wr_t2) / 2
        if opcion == "Más (+)":
            prob_base = 0.50 + (momentum_combinado - 0.50) * 0.3
            if linea_casino > 0 and linea_casino < 25: prob_base += 0.10 
        else: 
            prob_base = 0.50 - (momentum_combinado - 0.50) * 0.3
            if linea_casino > 35: prob_base += 0.10 

    elif "Primer" in mercado or "Ambos" in mercado:
        prob_win = wr_t1 / total_wr if opcion == "Equipo A" else wr_t2 / total_wr
        prob_base = 0.50 + ((prob_win - 0.50) * 0.7) 

    elif "Kills Equipo" in mercado:
        prob_base = wr_t1 / total_wr if opcion == "Equipo A" else wr_t2 / total_wr

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
    .prob-box {{ background: {c_btn}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; margin-bottom: 15px; }}
    .prob-number {{ font-size: 32px; font-weight: 900; color: {c_acc}; }}
    .stream-btn {{ background-color: #9146FF; color: white !important; padding: 8px 12px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: bold; display: block; margin-top: 15px; text-align: center; transition: 0.2s; }}
    .stream-btn:hover {{ background-color: #772CE8; transform: scale(1.02); }}
    
    .sniper-alert {{ background: rgba(16, 185, 129, 0.15); border: 2px dashed #10B981; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center; color: #10B981; font-weight: bold; font-size: 16px; animation: pulse 1.5s infinite; text-transform: uppercase; letter-spacing: 1px; }}
    
    div.stButton > button {{ background-color: {c_btn}; color: {c_acc}; border: 1px solid {c_border}; font-weight: bold; border-radius: 8px; padding: 10px; }}
    div.stButton > button:hover {{ background-color: {c_acc}; color: {c_bg}; border-color: {c_acc}; }}
    @keyframes pulse {{ 0% {{opacity: 1;}} 50% {{opacity: 0.6;}} 100% {{opacity: 1;}} }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. SIDEBAR Y JUEGOS
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h2 style='color:{c_acc}; text-align:center;'>🏦 Mi Bankroll</h2>", unsafe_allow_html=True)

nuevo_bank = st.sidebar.number_input("Ajustar Saldo (U):", value=float(bank_actual), step=10.0)
if st.sidebar.button("💾 Guardar Saldo", use_container_width=True):
    gestionar_bank(nuevo_bank)
    st.rerun()

st.sidebar.markdown(f"<h1 style='text-align:center; color:{c_text};'>{bank_actual:.2f} U</h1>", unsafe_allow_html=True)

# --- BOTÓN DE PÁNICO (CACHÉ) ---
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Sistema")
if st.sidebar.button("🗑️ Limpiar Caché (Forzar Datos Nuevos)", use_container_width=True):
    st.cache_data.clear() # ¡Esto borra la memoria corrupta!
    st.sidebar.success("✅ Caché limpio. Los datos se actualizarán.")

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
# 6. RADAR QUANT (SNIPER)
# ==========================================
st.markdown(f"<h2 style='color:{c_text};'>📡 Radar Quant: {juego_sel}</h2>", unsafe_allow_html=True)
    
running = call_api_live(slug, "matches/running", "per_page=10")
upcoming = call_api_live(slug, "matches/upcoming", "per_page=40&sort=begin_at")
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
        img1 = t1['image_url'] if t1['image_url'] else 'https://via.placeholder.com/60'
        img2 = t2['image_url'] if t2['image_url'] else 'https://via.placeholder.com/60'
        
        # HISTORIAL CORREGIDO - Carga fresca de 6 horas
        hist_t1, wr_t1, form_t1 = fetch_historical_data(slug, t1['id'])
        hist_t2, wr_t2, form_t2 = fetch_historical_data(slug, t2['id'])
        
        txt_wr1 = f"{wr_t1*100:.0f}%" if wr_t1 is not None else "S/D"
        txt_wr2 = f"{wr_t2*100:.0f}%" if wr_t2 is not None else "S/D"
        
        html_torres_t1 = "".join([f"<div class='tower-plate {res}'></div>" for res in form_t1])
        html_torres_t2 = "".join([f"<div class='tower-plate {res}'></div>" for res in form_t2])

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
                    prob_final = motor_cuantitativo_avanzado(hist_t1, hist_t2, wr_t1, wr_t2, sel_mer, sel_opcion, linea)
                    
                    st.markdown(f"""
                    <div class="prob-box">
                        <div style="font-size:10px; color:{c_text}; text-transform:uppercase;">Probabilidad Algoritmo</div>
                        <div class="prob-number">{prob_final*100:.1f}%</div>
                        <div style="font-size:10px; color:{c_sub};">Cuota Mínima Sugerida: {1/prob_final:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # --- SNIPER ALERT MOSTRADA DIRECTAMENTE AQUÍ ---
                if 0.75 <= prob_final <= 0.99:
                    st.markdown(f"""
                    <div class='sniper-alert'>
                        🎯 ¡SNIPER ALERT!<br>
                        <span style='font-size:12px; color:{c_sub};'>El algoritmo detecta un <b>{prob_final*100:.1f}%</b> de éxito en este mercado. Ejecute operación si la cuota es favorable.</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")
                cuota = st.number_input("Introduce la Cuota del Casino:", value=1.00, step=0.01, key=f"c_{i}")

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