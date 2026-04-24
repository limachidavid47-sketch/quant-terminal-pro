import streamlit as st
import requests
import os
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y LOGIN REMASTERIZADO
# ==========================================
st.set_page_config(page_title="Quant Elite V9", layout="wide", initial_sidebar_state="expanded")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("""
        <style>
        .stApp { background-color: #05080F; color: #F8FAFC; }
        .login-box {
            background: #0F172A; border: 1px solid #334155; border-radius: 15px; 
            padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); text-align: center;
        }
        .login-title { color: #38BDF8; font-size: 28px; font-weight: 900; letter-spacing: 2px; margin-bottom: 5px; }
        .login-sub { color: #64748B; font-size: 12px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }
        </style>
        """, unsafe_allow_html=True)
        
        # Centrado perfecto para la pantalla de login
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.markdown("<div class='login-title'>⚡ QUANT TERMINAL</div>", unsafe_allow_html=True)
            st.markdown("<div class='login-sub'>Acceso Restringido - Nivel 1</div>", unsafe_allow_html=True)
            
            u = st.text_input("ID de Operador", key="login_u")
            p = st.text_input("Clave de Cifrado", type="password", key="login_p")
            
            if st.button("Autenticar Conexión", use_container_width=True):
                if u == st.secrets["usuario"] and p == st.secrets["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else: 
                    st.error("❌ Credenciales rechazadas.")
            st.markdown("</div>", unsafe_allow_html=True)
        return False
    return True

if not check_password(): st.stop()

# ==========================================
# 2. MOTOR DE DATOS CORREGIDO (WINRATES REALES)
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
    # SOLUCIÓN: Filtramos SOLO partidos terminados para que no cuente futuros como derrotas.
    historial = call_api(slug, f"teams/{team_id}/matches", "filter[status]=finished&per_page=10")
    
    if not historial: return 0.50, ['unknown']*5 # Si es equipo nuevo, placas grises
    
    wins = 0
    form = []
    for match in historial:
        # Aseguramos que los IDs se comparen correctamente como texto
        if str(match.get('winner_id')) == str(team_id):
            wins += 1
            form.append('win')
        else:
            form.append('loss')
    
    winrate = wins / len(historial)
    while len(form) < 5: form.append('unknown') # Rellenar si jugó menos de 5 partidas
    
    return winrate, form[:5]

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(round(monto, 2)))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

# ==========================================
# 3. SELECTOR DE TEMAS Y CSS DINÁMICO
# ==========================================
tema = st.sidebar.selectbox("🎨 Tema Visual:", ["Dark Mate (Defecto)", "Blanco Elegante", "Rojo Táctico (Nocturno)"])

# Variables de color dinámicas
if tema == "Blanco Elegante":
    c_bg = "#F8FAFC"; c_card = "#FFFFFF"; c_text = "#0F172A"; c_sub = "#475569"; c_border = "#CBD5E1"; c_acc = "#0284C7"
elif tema == "Rojo Táctico (Nocturno)":
    c_bg = "#0A0000"; c_card = "#1A0505"; c_text = "#FECACA"; c_sub = "#FCA5A5"; c_border = "#7F1D1D"; c_acc = "#EF4444"
else: # Dark Mate
    c_bg = "#0B1120"; c_card = "#1E293B"; c_text = "#F1F5F9"; c_sub = "#94A3B8"; c_border = "#334155"; c_acc = "#38BDF8"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {c_bg}; color: {c_text}; }}
    [data-testid="stSidebar"] {{ background-color: {c_card} !important; border-right: 1px solid {c_border}; }}
    .glass-card {{ background: {c_card}; border: 1px solid {c_border}; border-radius: 12px; padding: 15px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    
    .team-logo {{ width: 55px; height: 55px; object-fit: contain; margin-bottom: 5px; }}
    .team-name {{ font-size: 14px; font-weight: bold; color: {c_text}; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}}
    .winrate-text {{ font-size: 11px; color: #10B981; font-weight: bold; margin-bottom: 5px; }}
    
    .form-container {{ display: flex; gap: 4px; justify-content: center; margin-top: 5px; }}
    .tower-plate {{ width: 12px; height: 6px; border-radius: 2px; }}
    .win {{ background-color: #10B981; }}
    .loss {{ background-color: #EF4444; }}
    .unknown {{ background-color: {c_sub}; opacity: 0.5; }}
    
    .vs-text {{ font-size: 18px; font-weight: bold; color: {c_acc}; margin: 0 10px; }}
    
    .badge-live {{ background: #EF4444; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite;}}
    .badge-time {{ background: {c_acc}; color: {c_bg}; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
    .stream-btn {{
        background-color: #9146FF; color: white !important; padding: 6px 12px; 
        border-radius: 8px; text-decoration: none; font-size: 11px; font-weight: bold;
        display: inline-block; margin-top: 15px; border: 1px solid #772CE8; width: 100%; text-align: center;
    }}
    .stream-btn:hover {{ background-color: #772CE8; }}
    
    div.stButton > button {{ background-color: {c_card}; color: {c_acc}; border: 1px solid {c_border}; border-radius: 8px; font-weight: bold; }}
    div.stButton > button:hover {{ background-color: {c_acc}; color: {c_bg}; border-color: {c_acc}; }}
    @keyframes pulse {{ 0% {{opacity: 1;}} 50% {{opacity: 0.5;}} 100% {{opacity: 1;}} }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR (BANKROLL Y JUEGOS)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h2 style='color:#10B981; text-align:center;'>🏦 Mi Bankroll</h2>", unsafe_allow_html=True)

nuevo_bank = st.sidebar.number_input("Ajustar Saldo (U):", value=float(bank_actual), step=10.0)
if st.sidebar.button("💾 Guardar Saldo", use_container_width=True):
    gestionar_bank(nuevo_bank)
    st.rerun()

st.sidebar.markdown(f"<h1 style='text-align:center; color:{c_text};'>{bank_actual:.2f} U</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")

juegos_config = {
    "League of Legends": {"slug": "lol", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Kills (Global)", "Kills Equipo A", "Kills Equipo B", "Total Dragones", "Ambos Matan Dragón", "Total Torres", "Duración de Partida", "Total Mapas"]},
    "Dota 2": {"slug": "dota2", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Kills (Global)", "Kills Equipo A", "Kills Equipo B", "Primer Roshan", "Total Torres", "Duración de Partida", "Total Mapas"]},
    "Mobile Legends": {"slug": "mobile-legends", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Kills", "Primer Lord", "Duración de Partida", "Total Mapas"]}
}

st.sidebar.markdown(f"<h3 style='color:{c_text};'>🎮 Seleccionar Disciplina</h3>", unsafe_allow_html=True)
juego_sel = st.sidebar.radio("", list(juegos_config.keys()))
slug = juegos_config[juego_sel]["slug"]
mercados_list = juegos_config[juego_sel]["mercados"]

# ==========================================
# 5. RADAR EN VIVO (DATOS REALES)
# ==========================================
st.markdown(f"<h1 style='color:{c_text};'>🔴 Radar En Vivo: {juego_sel}</h1>", unsafe_allow_html=True)
    
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
        
        # --- ESTADÍSTICAS REALES ---
        wr_t1, form_t1 = get_team_stats(slug, t1['id'])
        wr_t2, form_t2 = get_team_stats(slug, t2['id'])
        
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
                <div style="margin-bottom: 10px; font-size: 11px; color: {c_sub}; display: flex; justify-content: space-between;">
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
                    # PROBABILIDAD REAL CRUZADA
                    prob_base = 0.50
                    if "Ganador" in sel_mer or "Kills Equipo" in sel_mer or sel_opcion in [t1['name'], t2['name']]:
                        total_wr = wr_t1 + wr_t2
                        if total_wr > 0:
                            if sel_opcion == t1['name']: prob_base = wr_t1 / total_wr
                            elif sel_opcion == t2['name']: prob_base = wr_t2 / total_wr
                    else:
                        momentum = (wr_t1 + wr_t2) / 2
                        prob_base = 0.50 + (momentum - 0.50) * 0.5 
                    
                    prob_base = max(0.05, min(0.95, prob_base))

                    st.markdown(f"<div style='background:rgba(56,189,248,0.1); padding:8px; border-radius:5px; color:{c_acc}; font-size:12px; margin-bottom:10px; text-align:center; border: 1px solid {c_acc};'><b>Prob. Calculada: {prob_base*100:.1f}%</b></div>", unsafe_allow_html=True)
                    cuota = st.number_input("Cuota:", value=1.85, step=0.01, key=f"c_{i}")

                # MÉTODO KELLY SEGURO (1/4)
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