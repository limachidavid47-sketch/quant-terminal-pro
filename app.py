import streamlit as st
import requests
import os
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y LOGIN
# ==========================================
st.set_page_config(page_title="Quant Elite V5", layout="wide", initial_sidebar_state="expanded")

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
# 2. MOTOR DE DATOS
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

@st.cache_data(ttl=120)
def call_api(game_slug, endpoint, params_str=""):
    url = f"https://api.pandascore.co/{game_slug}/{endpoint}?{params_str}"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(monto))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

# Inicializador de estado para la cebolla
if 'cebolla_nivel' not in st.session_state:
    st.session_state.cebolla_nivel = 0 # 0=Ligas, 1=Equipos, 2=Jugadores
    st.session_state.id_liga_sel = None
    st.session_state.id_equipo_sel = None

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
    .tower-plate { width: 14px; height: 6px; border-radius: 2px; }
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
    
    .btn-cebolla { background-color: #1E293B; border: 1px solid #38BDF8; color: white; padding: 10px; border-radius: 8px; width: 100%; text-align: center; font-weight: bold; transition: 0.3s; cursor: pointer;}
    .btn-cebolla:hover { background-color: #38BDF8; color: #0B1120; }
    
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR Y MENÚ
# ==========================================
st.sidebar.markdown(f"### 🏦 Bankroll: {bank_actual:.2f} U")
juegos_config = {
    "League of Legends": {"slug": "lol", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Kills (Global)", "Kills Equipo A", "Kills Equipo B", "Total Dragones", "Ambos Matan Dragón", "Total Torres", "Duración de Partida", "Total Mapas"]},
    "Dota 2": {"slug": "dota2", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Kills (Global)", "Kills Equipo A", "Kills Equipo B", "Primer Roshan", "Total Torres", "Duración de Partida", "Total Mapas"]},
    "Mobile Legends": {"slug": "mobile-legends", "mercados": ["Ganador del Partido", "Handicap de Kills", "Total Kills", "Primer Lord", "Duración de Partida", "Total Mapas"]}
}

juego_sel = st.sidebar.radio("Disciplina", list(juegos_config.keys()))
slug = juegos_config[juego_sel]["slug"]
mercados_list = juegos_config[juego_sel]["mercados"]

st.sidebar.markdown("---")
seccion = st.sidebar.selectbox("Ir a:", ["🔴 Radar En Vivo", "🏆 Base de Datos (Cebolla)", "📚 Enciclopedia de Campeones"])

# Resetear la cebolla si cambias de sección
if seccion != "🏆 Base de Datos (Cebolla)":
    st.session_state.cebolla_nivel = 0

# ==========================================
# 5. PANTALLAS
# ==========================================

if seccion == "🔴 Radar En Vivo":
    st.title(f"Radar: {juego_sel}")
    
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
                            <div class="winrate-text">WR: 65%</div>
                            <div class="form-container">
                                <div class="tower-plate win"></div><div class="tower-plate win"></div><div class="tower-plate loss"></div>
                            </div>
                        </div>
                        <div class="vs-text">VS</div>
                        <div style="width: 40%;">
                            <div class="team-name">{t2['name']}</div>
                            <img src="{img2}" class="team-logo"><br>
                            <div class="winrate-text">WR: 58%</div>
                            <div class="form-container">
                                <div class="tower-plate loss"></div><div class="tower-plate win"></div><div class="tower-plate win"></div>
                            </div>
                        </div>
                    </div>
                    {boton_stream}
                </div>
                """, unsafe_allow_html=True)

                # --- PANEL DE OPERACIÓN CON SELECTOR AÑADIDO ---
                with st.expander(f"⚙️ Operar Mercados"):
                    c_izq, c_der = st.columns(2)
                    
                    with c_izq:
                        sel_mer = st.selectbox("Mercado:", mercados_list, key=f"mer_{i}")
                        
                        # AQUÍ LA SOLUCIÓN: Selector dinámico de equipo o Más/Menos
                        if "Total" in sel_mer or "Duración" in sel_mer:
                            sel_opcion = st.selectbox("Opción:", ["Más (+)", "Menos (-)"], key=f"op_{i}")
                        else:
                            sel_opcion = st.selectbox("A favor de:", [t1['name'], t2['name']], key=f"op_{i}")
                            
                        linea = st.number_input("Línea Casino:", value=0.0, step=0.5, key=f"l_{i}")
                    
                    with c_der:
                        prob_base = 0.62 
                        if "Dragones" in sel_mer: prob_base = 0.55
                        elif "Duración" in sel_mer: prob_base = 0.58
                        elif "Mapas" in sel_mer: prob_base = 0.52
                        
                        st.markdown(f"<div style='background:rgba(56,189,248,0.1); padding:8px; border-radius:5px; color:#38BDF8; font-size:12px; margin-bottom:10px; text-align:center;'><b>Prob. Calculada: {prob_base*100:.1f}%</b></div>", unsafe_allow_html=True)
                        cuota = st.number_input("Cuota:", value=1.85, step=0.01, key=f"c_{i}")

                    if cuota > (1/prob_base):
                        kelly = (((cuota - 1) * prob_base) - (1 - prob_base)) / (cuota - 1)
                        stake = (kelly * 0.25) * bank_actual
                        if stake > 0:
                            st.success(f"🔥 VALOR en {sel_opcion}. Sugerido: {stake:.2f} U")
                            if st.button("Confirmar Apuesta", key=f"btn_{i}", use_container_width=True):
                                gestionar_bank(bank_actual - stake)
                                st.rerun()
                    else:
                        st.warning(f"⚠️ Cuota sin valor (Mínima justa: {1/prob_base:.2f})")

# --- PANTALLA: BASE DE DATOS (CEBOLLA VISUAL) ---
elif seccion == "🏆 Base de Datos (Cebolla)":
    
    # BOTÓN PARA VOLVER ATRÁS
    if st.session_state.cebolla_nivel > 0:
        if st.button("⬅️ Volver Atrás", use_container_width=True):
            st.session_state.cebolla_nivel -= 1
            st.rerun()

    # NIVEL 0: LIGAS (Tarjetas)
    if st.session_state.cebolla_nivel == 0:
        st.title("🌐 Selecciona una Liga")
        ligas = call_api(slug, "leagues", "per_page=12")
        cols = st.columns(4)
        for idx, l in enumerate(ligas):
            with cols[idx % 4]:
                st.markdown(f"<div class='glass-card' style='text-align:center;'><img src='{l['image_url']}' style='width:60px; height:60px; object-fit:contain;'></div>", unsafe_allow_html=True)
                if st.button(f"{l['name']}", key=f"btn_lig_{l['id']}", use_container_width=True):
                    st.session_state.id_liga_sel = l['id']
                    st.session_state.cebolla_nivel = 1
                    st.rerun()

    # NIVEL 1: EQUIPOS (Tarjetas)
    elif st.session_state.cebolla_nivel == 1:
        st.title("🛡️ Selecciona un Equipo")
        equipos = call_api(slug, f"leagues/{st.session_state.id_liga_sel}/teams", "per_page=16")
        if equipos:
            cols = st.columns(4)
            for idx, e in enumerate(equipos):
                with cols[idx % 4]:
                    st.markdown(f"<div class='glass-card' style='text-align:center;'><img src='{e['image_url']}' style='width:60px; height:60px; object-fit:contain;'></div>", unsafe_allow_html=True)
                    if st.button(f"{e['name']}", key=f"btn_eq_{e['id']}", use_container_width=True):
                        st.session_state.id_equipo_sel = e
                        st.session_state.cebolla_nivel = 2
                        st.rerun()
        else:
            st.info("No hay equipos disponibles para esta liga en este momento.")

    # NIVEL 2: JUGADORES Y ESTADÍSTICAS
    elif st.session_state.cebolla_nivel == 2:
        equipo = st.session_state.id_equipo_sel
        st.title(f"📊 Ficha Técnica: {equipo['name']}")
        
        c_logo, c_stats = st.columns([1, 3])
        with c_logo:
            st.image(equipo['image_url'], width=150)
            st.markdown(f"**Acrónimo:** {equipo.get('acronym', 'N/A')}")
        
        with c_stats:
            st.subheader("👥 Roster Oficial")
            jugadores = equipo.get('players', [])
            if jugadores:
                p_cols = st.columns(3)
                for i, p in enumerate(jugadores):
                    with p_cols[i % 3]:
                        st.markdown(f"""
                        <div class="glass-card" style="text-align:center; padding:10px;">
                            <img src="{p['image_url'] if p['image_url'] else 'https://via.placeholder.com/60'}" style="width:60px; height:60px; border-radius:50%; object-fit:cover;"><br>
                            <b style="color:#38BDF8;">{p['name']}</b><br>
                            <span style="font-size:11px; color:#94A3B8;">{p['role'] if p['role'] else 'Pro Player'}</span><br>
                            <span style="font-size:10px; color:#10B981;">Main: Calculando...</span>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("El equipo no ha hecho pública su plantilla actual.")

# --- PANTALLA: ENCICLOPEDIA ---
elif seccion == "📚 Enciclopedia de Campeones":
    st.title(f"Héroes de {juego_sel}")
    lore = {
        "lol": [{"n": "Lee Sin", "h": "Monje ciego maestro del combate espiritual."}, {"n": "Jinx", "h": "Criminal de Zaun amante del caos."}],
        "dota2": [{"n": "Anti-Mage", "h": "Monje que busca destruir toda la magia."}, {"n": "Pudge", "h": "Carnicero del campo de batalla."}],
        "mobile-legends": [{"n": "Layla", "h": "Defensora con cañón de energía."}, {"n": "Tigreal", "h": "Líder honorífico de los Caballeros."}]
    }
    for c in lore.get(slug, []):
        st.markdown(f"<div class='glass-card'><h3 style='color:#38BDF8;'>{c['n']}</h3><p>{c['h']}</p></div>", unsafe_allow_html=True)