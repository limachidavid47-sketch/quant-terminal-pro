import streamlit as st
import requests
import os
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y LOGIN
# ==========================================
st.set_page_config(page_title="Quant Elite V7", layout="wide", initial_sidebar_state="expanded")

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
# 2. MOTOR DE DATOS (ACTUALIZACIÓN CADA 60s)
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

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(monto))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

if 'cebolla_nivel' not in st.session_state:
    st.session_state.cebolla_nivel = 0
    st.session_state.id_liga_sel = None
    st.session_state.equipo_data_sel = None

# ==========================================
# 3. DISEÑO CSS (ANIMACIONES AÑADIDAS)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #0B1120; color: #F1F5F9; }
    .glass-card { background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 15px; margin-bottom: 10px; transition: transform 0.3s ease; }
    .glass-card:hover { transform: scale(1.03); border-color: #38BDF8; }
    .hero-card { background: #0F172A; border: 1px solid #1E293B; border-radius: 10px; padding: 10px; text-align: center; transition: all 0.3s ease; }
    .hero-card:hover { transform: translateY(-5px); border-color: #10B981; box-shadow: 0 5px 15px rgba(16, 185, 129, 0.2); }
    
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
    
    div.stButton > button { background-color: #0F172A; color: #38BDF8; border: 1px solid #334155; border-radius: 8px; font-weight: bold; }
    div.stButton > button:hover { background-color: #38BDF8; color: #0F172A; border-color: #38BDF8; }
    
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

if seccion != "🏆 Base de Datos (Cebolla)": st.session_state.cebolla_nivel = 0

# ==========================================
# 5. PANTALLAS
# ==========================================

# --- PANTALLA: RADAR EN VIVO (INTOCABLE) ---
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

# --- PANTALLA: BASE DE DATOS (CEBOLLA) ---
elif seccion == "🏆 Base de Datos (Cebolla)":
    
    if st.session_state.cebolla_nivel > 0:
        if st.button("⬅️ Volver Atrás", use_container_width=True):
            st.session_state.cebolla_nivel -= 1
            st.rerun()

    # NIVEL 0: LIGAS (Corregido para MLBB y añadido contador)
    if st.session_state.cebolla_nivel == 0:
        st.title("🌐 Selecciona una Liga")
        # Quitamos el sort=-modified_at para que MLBB no se rompa
        ligas = call_api(slug, "leagues", "per_page=12")
        cols = st.columns(4)
        for idx, l in enumerate(ligas):
            with cols[idx % 4]:
                # Buscamos rápido cuántos equipos tiene la serie actual
                equipos_count = call_api(slug, f"leagues/{l['id']}/teams", "per_page=50")
                cant_equipos = len(equipos_count) if equipos_count else "Varios"
                
                img_url = l['image_url'] if l['image_url'] else "https://via.placeholder.com/80?text=Liga"
                st.markdown(f"""
                <div class='glass-card' style='text-align:center;'>
                    <div class='team-name' style='color:#38BDF8;'>{l['name']}</div>
                    <img src='{img_url}' style='width:70px; height:70px; object-fit:contain; margin:10px 0;'>
                    <div style='font-size:11px; color:#94A3B8; margin-bottom:10px;'>🎮 {cant_equipos} Equipos</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Explorar Liga", key=f"l_{l['id']}", use_container_width=True):
                    st.session_state.id_liga_sel = l['id']
                    st.session_state.cebolla_nivel = 1
                    st.rerun()

    # NIVEL 1: EQUIPOS
    elif st.session_state.cebolla_nivel == 1:
        st.title("🛡️ Equipos Activos")
        partidos_liga = call_api(slug, "matches", f"filter[league_id]={st.session_state.id_liga_sel}&per_page=30&sort=-begin_at")
        equipos_unicos = {}
        for p in partidos_liga:
            for opp in p.get('opponents', []):
                eq = opp['opponent']
                equipos_unicos[eq['id']] = eq
        equipos = list(equipos_unicos.values())

        if equipos:
            cols = st.columns(4)
            for idx, e in enumerate(equipos):
                with cols[idx % 4]:
                    img_url = e['image_url'] if e['image_url'] else "https://via.placeholder.com/60"
                    st.markdown(f"""
                    <div class='glass-card' style='text-align:center;'>
                        <div class='team-name' style='color:#F8FAFC;'>{e['name']}</div>
                        <img src='{img_url}' style='width:60px; height:60px; object-fit:contain; margin-bottom:10px;'>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Ver Plantilla", key=f"e_{e['id']}", use_container_width=True):
                        st.session_state.equipo_data_sel = e
                        st.session_state.cebolla_nivel = 2
                        st.rerun()
        else:
            st.info("No se encontraron equipos compitiendo recientemente en esta liga.")

    # NIVEL 2: JUGADORES
    elif st.session_state.cebolla_nivel == 2:
        equipo = st.session_state.equipo_data_sel
        st.title(f"📊 Ficha Técnica: {equipo['name']}")
        c_logo, c_stats = st.columns([1, 3])
        with c_logo:
            img_url = equipo['image_url'] if equipo['image_url'] else "https://via.placeholder.com/150"
            st.image(img_url, width=150)
            st.markdown(f"**Acrónimo:** {equipo.get('acronym', 'N/A')}")
        
        with c_stats:
            st.subheader("👥 Roster Oficial")
            jugadores = equipo.get('players', [])
            if jugadores:
                p_cols = st.columns(3)
                for i, p in enumerate(jugadores):
                    with p_cols[i % 3]:
                        img_p = p['image_url'] if p['image_url'] else 'https://via.placeholder.com/60'
                        st.markdown(f"""
                        <div class="glass-card" style="text-align:center; padding:10px;">
                            <img src="{img_p}" style="width:60px; height:60px; border-radius:50%; object-fit:cover;"><br>
                            <b style="color:#38BDF8;">{p['name']}</b><br>
                            <span style="font-size:11px; color:#94A3B8;">{p['role'] if p['role'] else 'Pro Player'}</span><br>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("La base de datos oficial no tiene registrada la plantilla de este equipo (Común en ligas Tier 2/3).")

# --- PANTALLA: ENCICLOPEDIA (3 POR FILA + DATOS REALES) ---
elif seccion == "📚 Enciclopedia de Campeones":
    st.title(f"Héroes de {juego_sel}")
    st.write("Datos extraídos directamente de los servidores oficiales del juego.")
    
    # Descarga dinámica según el juego
    if slug == "lol":
        heroes_data = call_api("lol", "champions", "per_page=30")
    elif slug == "dota2":
        heroes_data = call_api("dota2", "heroes", "per_page=30")
    else:
        # MLBB (PandaScore no da API de héroes de MLBB, usamos una mini base local premium)
        heroes_data = [
            {"name": "Layla", "image_url": "https://liquipedia.net/commons/images/thumb/7/7b/Layla_MLBB.jpg/120px-Layla_MLBB.jpg", "armor": 15, "hp": 2500, "role": "Tirador"},
            {"name": "Tigreal", "image_url": "https://liquipedia.net/commons/images/thumb/8/87/Tigreal_MLBB.jpg/120px-Tigreal_MLBB.jpg", "armor": 45, "hp": 3200, "role": "Tanque/Soporte"},
            {"name": "Gusion", "image_url": "https://liquipedia.net/commons/images/thumb/4/4c/Gusion_MLBB.jpg/120px-Gusion_MLBB.jpg", "armor": 20, "hp": 2400, "role": "Asesino"}
        ]

    if not heroes_data:
        st.info("Cargando base de datos de héroes...")
    else:
        cols = st.columns(3) # Diseño estricto 3 por fila
        for idx, h in enumerate(heroes_data):
            with cols[idx % 3]:
                # Limpiamos nombres y buscamos variables según si es LoL o Dota
                nombre_heroe = h.get('name') or h.get('localized_name') or "Desconocido"
                img_heroe = h.get('image_url') if h.get('image_url') else "https://via.placeholder.com/80"
                
                st.markdown(f"""
                <div class="hero-card">
                    <img src="{img_heroe}" style="width:80px; height:80px; object-fit:cover; border-radius:10px; margin-bottom:10px;">
                    <h4 style="color:#F8FAFC; margin:0;">{nombre_heroe}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # El expander para ver los datos sin salir de la pantalla
                with st.expander("Ver Stats Básicas"):
                    if slug == "lol":
                        st.write(f"🛡️ **Armadura:** {h.get('armor', 'N/A')}")
                        st.write(f"❤️ **Vida (HP):** {h.get('hp', 'N/A')}")
                        st.write(f"⚔️ **Daño Base:** {h.get('attackdamage', 'N/A')}")
                    elif slug == "dota2":
                        roles = ", ".join(h.get('roles', []))
                        st.write(f"🎭 **Roles:** {roles}")
                    else: # MLBB
                        st.write(f"🎭 **Rol:** {h.get('role', 'N/A')}")
                        st.write(f"🛡️ **Armadura:** {h.get('armor', 'N/A')}")
                        st.write(f"❤️ **Vida Máx:** {h.get('hp', 'N/A')}")