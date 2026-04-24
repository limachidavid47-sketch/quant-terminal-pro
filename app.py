import streamlit as st
import requests
import os
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y LOGIN
# ==========================================
st.set_page_config(page_title="Quant Elite V8", layout="wide", initial_sidebar_state="expanded")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center; color: #38BDF8;'>🔐 Acceso Quant David</h2>", unsafe_allow_html=True)
        u = st.text_input("Usuario", key="login_u")
        p = st.text_input("Contraseña", type="password", key="login_p")
        if st.button("Entrar"):
            if u == st.secrets["usuario"] and p == st.secrets["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("Credenciales incorrectas")
        return False
    return True

if not check_password(): st.stop()

# ==========================================
# 2. MOTOR DE DATOS (API & HISTÓRICOS)
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

# NUEVO MOTOR: Extrae los últimos 10 partidos y saca la estadística real
@st.cache_data(ttl=300) # Se guarda 5 min para no saturar tu API gratuita
def get_team_stats(slug, team_id):
    historial = call_api(slug, f"teams/{team_id}/matches", "per_page=10")
    if not historial: return 0.50, ['loss']*5 # Si no hay datos, asume 50%
    
    wins = 0
    form = []
    for match in historial:
        won = match.get('winner_id') == team_id
        if won: wins += 1
        form.append('win' if won else 'loss')
    
    winrate = wins / len(historial)
    return winrate, form[:5] # Retorna el % real y los últimos 5 para las torres

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(round(monto, 2)))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

# ==========================================
# 3. DISEÑO CSS
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #0B1120; color: #F1F5F9; }
    .glass-card { background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    .team-logo { width: 55px; height: 55px; object-fit: contain; margin-bottom: 5px; }
    .team-name { font-size: 14px; font-weight: bold; color: #F8FAFC; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
    .winrate-text { font-size: 11px; color: #10B981; font-weight: bold; margin-bottom: 5px; }
    .form-container { display: flex; gap: 4px; justify-content: center; margin-top: 5px; }
    .tower-plate { width: 12px; height: 6px; border-radius: 2px; }
    .win { background-color: #10B981; }
    .loss { background-color: #EF4444; }
    .vs-text { font-size: 18px; font-weight: bold; color: #38BDF8; margin: 0 10px; }
    
    .badge-live { background: #EF4444; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite;}
    .badge-time { background: #38BDF8; color: #0F172A; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .stream-btn {
        background-color: #9146FF; color: white !important; padding: 6px 12px; 
        border-radius: 8px; text-decoration: none; font-size: 11px; font-weight: bold;
        display: inline-block; margin-top: 15px; border: 1px solid #772CE8; width: 100%; text-align: center;
    }
    .stream-btn:hover { background-color: #772CE8; }
    
    div.stButton > button { background-color: #0F172A; color: #38BDF8; border: 1px solid #334155; border-radius: 8px; font-weight: bold; }
    div.stButton > button:hover { background-color: #38BDF8; color: #0F172A; border-color: #38BDF8; }
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR (BANKROLL FLEXIBLE Y JUEGOS)
# ==========================================
st.sidebar.markdown("<h2 style='color:#10B981; text-align:center;'>🏦 Mi Bankroll</h2>", unsafe_allow_html=True)

# Input flexible para actualizar el bankroll a mano
nuevo_bank = st.sidebar.number_input("Ajustar Saldo (U):", value=float(bank_actual), step=10.0)
if st.sidebar.button("💾 Guardar Saldo", use_container_width=True):
    gestionar_bank(nuevo_bank)
    st.rerun()

st.sidebar.markdown(f"<h1 style='text-align:center; color:#F8FAFC;'>{bank_actual:.2f} U</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")

juegos_config = {
    "League of Legends": {"slug": "lol", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Kills (Global)", "Kills Equipo A", "Kills Equipo B", "Total Dragones", "Ambos Matan Dragón", "Total Torres", "Duración de Partida", "Total Mapas"]},
    "Dota 2": {"slug": "dota2", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Kills (Global)", "Kills Equipo A", "Kills Equipo B", "Primer Roshan", "Total Torres", "Duración de Partida", "Total Mapas"]},
    "Mobile Legends": {"slug": "mobile-legends", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Kills", "Primer Lord", "Duración de Partida", "Total Mapas"]}
}

st.sidebar.markdown("### 🎮 Seleccionar Disciplina")
juego_sel = st.sidebar.radio("", list(juegos_config.keys()))
slug = juegos_config[juego_sel]["slug"]
mercados_list = juegos_config[juego_sel]["mercados"]

# ==========================================
# 5. RADAR EN VIVO (CON DATOS 100% REALES)
# ==========================================
st.title(f"🔴 Radar En Vivo: {juego_sel}")
    
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
        
        # --- EXTRACCIÓN DE DATOS REALES (Últimos 10 partidos) ---
        wr_t1, form_t1 = get_team_stats(slug, t1['id'])
        wr_t2, form_t2 = get_team_stats(slug, t2['id'])
        
        # Generar HTML de las 5 placas de torre dinámicamente
        html_torres_t1 = "".join([f"<div class='tower-plate {res}'></div>" for res in form_t1])
        html_torres_t2 = "".join([f"<div class='tower-plate {res}'></div>" for res in form_t2])
        
        if m['status'] == 'running':
            badge = "<span class='badge-live'>🔴 EN VIVO</span>"
        else:
            dt_utc = datetime.strptime(m['begin_at'], "%Y-%m-%dT%H:%M:%SZ")
            hora_bol = (dt_utc - timedelta(hours=4)).strftime("%H:%M")
            badge = f"<span class='badge-time'>🕒 {hora_bol}</span>"

        stream_link = ""
        if m.get('official_video_url'): stream_link = m['official_video_url']
        elif m.get('streams_list') and len(m['streams_list']) > 0: stream_link = m['streams_list'][0].get('raw_url', '')
        boton_stream = f'<a href="{stream_link}" target="_blank" class="stream-btn">📺 Ver Partido en Vivo</a>' if stream_link else ''

        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
            <div class="glass-card">
                <div style="margin-bottom: 10px; font-size: 11px; color: #94A3B8; display: flex; justify-content: space-between;">
                    <span>🏆 {m['league']['name']}</span>{badge}
                </div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 40%;">
                        <div class="team-name">{t1['name']}</div>
                        <img src="{img1}" class="team-logo"><br>
                        <div class="winrate-text">WR: {wr_t1*100:.0f}%</div>
                        <div class="form-container">{html_torres_t1}</div>
                    </div>
                    <div class="vs-text">VS</div>
                    <div style="width: 40%;">
                        <div class="team-name">{t2['name']}</div>
                        <img src="{img2}" class="team-logo"><br>
                        <div class="winrate-text">WR: {wr_t2*100:.0f}%</div>
                        <div class="form-container">{html_torres_t2}</div>
                    </div>
                </div>
                {boton_stream}
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"⚙️ Operar Mercados"):
                c_izq, c_der = st.columns(2)
                
                with c_izq:
                    sel_mer = st.selectbox("Mercado:", mercados_list, key=f"mer_{i}")
                    if "Total" in sel_mer or "Duración" in sel_mer:
                        sel_opcion = st.selectbox("Opción:", ["Más (+)", "Menos (-)"], key=f"op_{i}")
                    else:
                        sel_opcion = st.selectbox("A favor de:", [t1['name'], t2['name']], key=f"op_{i}")
                    linea = st.number_input("Línea Casino:", value=0.0, step=0.5, key=f"l_{i}")
                
                with c_der:
                    # --- CÁLCULO DE PROBABILIDAD REAL ---
                    prob_base = 0.50
                    if "Ganador" in sel_mer or "Kills Equipo" in sel_mer or sel_opcion in [t1['name'], t2['name']]:
                        # Normalizamos el WR de los dos equipos
                        total_wr = wr_t1 + wr_t2
                        if total_wr > 0:
                            if sel_opcion == t1['name']: prob_base = wr_t1 / total_wr
                            elif sel_opcion == t2['name']: prob_base = wr_t2 / total_wr
                        else: prob_base = 0.50
                    else:
                        # Para totales (Dragones, Torres, etc.), usamos el momentum conjunto
                        momentum_conjunto = (wr_t1 + wr_t2) / 2
                        prob_base = 0.50 + (momentum_conjunto - 0.50) * 0.5 # Ajuste heurístico
                    
                    # Para evitar 100% o 0% matemático que rompe el Kelly
                    prob_base = max(0.05, min(0.95, prob_base))

                    st.markdown(f"<div style='background:rgba(56,189,248,0.1); padding:8px; border-radius:5px; color:#38BDF8; font-size:12px; margin-bottom:10px; text-align:center;'><b>Prob. Calculada: {prob_base*100:.1f}%</b></div>", unsafe_allow_html=True)
                    cuota = st.number_input("Cuota:", value=1.85, step=0.01, key=f"c_{i}")

                # --- MÉTODO KELLY SEGURO (1/4) ---
                if cuota > (1/prob_base):
                    kelly = (((cuota - 1) * prob_base) - (1 - prob_base)) / (cuota - 1)
                    stake = (kelly * 0.25) * bank_actual
                    if stake > 0:
                        st.success(f"🔥 VALOR DETECTADO. Apuesta Sugerida: {stake:.2f} U")
                        if st.button("Confirmar y Descontar", key=f"btn_{i}", use_container_width=True):
                            gestionar_bank(bank_actual - stake)
                            st.rerun()
                else:
                    st.warning(f"⚠️ Cuota sin valor matemático. (Mínima justa: {1/prob_base:.2f})")