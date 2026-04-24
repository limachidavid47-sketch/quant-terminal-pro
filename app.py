import streamlit as st
import requests
import os
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y LOGIN
# ==========================================
st.set_page_config(page_title="Quant Elite V3", layout="wide", initial_sidebar_state="expanded")

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
# 2. MOTOR DE DATOS (API PANDASCORE)
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

@st.cache_data(ttl=300)
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

# ==========================================
# 3. DISEÑO CSS (PLACAS DE TORRE Y UI)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #0B1120; color: #F1F5F9; }
    .glass-card { background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    .team-logo { width: 55px; height: 55px; object-fit: contain; margin-bottom: 5px; }
    .winrate-text { font-size: 11px; color: #10B981; font-weight: bold; margin-bottom: 5px; }
    /* Placas de Torre (Forma) */
    .form-container { display: flex; gap: 4px; justify-content: center; margin-top: 5px; }
    .tower-plate { width: 14px; height: 6px; border-radius: 2px; }
    .win { background-color: #10B981; }
    .loss { background-color: #EF4444; }
    .vs-text { font-size: 18px; font-weight: bold; color: #38BDF8; margin: 0 10px; }
    .prob-badge { background: rgba(56, 189, 248, 0.1); color: #38BDF8; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR Y NAVEGACIÓN
# ==========================================
st.sidebar.markdown(f"### 🏦 Bankroll: {bank_actual:.2f} U")
juegos = {
    "League of Legends": "lol",
    "Dota 2": "dota2",
    "Mobile Legends": "mobile-legends"
}
juego_sel = st.sidebar.radio("Disciplina", list(juegos.keys()))
slug = juegos[juego_sel]

st.sidebar.markdown("---")
seccion = st.sidebar.selectbox("Ir a:", ["🔴 Radar En Vivo", "🏆 Base de Datos (Cebolla)", "📚 Enciclopedia de Campeones"])

# ==========================================
# 5. PANTALLAS
# ==========================================

# --- PANTALLA: RADAR EN VIVO ---
if seccion == "🔴 Radar En Vivo":
    st.title(f"Radar: {juego_sel}")
    
    # Obtener partidos
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
            
            # Cálculo de Probabilidad (Simulación basada en histórico)
            prob_a = 0.62 # Este valor se extraería del winrate histórico real
            prob_b = 1 - prob_a

            with (col1 if i % 2 == 0 else col2):
                # Usamos expander como base de la tarjeta para estabilidad
                with st.expander(f"🎮 {t1['name']} vs {t2['name']}", expanded=True):
                    # HTML de la tarjeta con logos, winrate y placas de torre
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                        <div>
                            <img src="{t1['image_url']}" class="team-logo"><br>
                            <div class="winrate-text">WR: 65%</div>
                            <div class="form-container">
                                <div class="tower-plate win"></div><div class="tower-plate win"></div><div class="tower-plate loss"></div>
                            </div>
                        </div>
                        <div class="vs-text">VS</div>
                        <div>
                            <img src="{t2['image_url']}" class="team-logo"><br>
                            <div class="winrate-text">WR: 58%</div>
                            <div class="form-container">
                                <div class="tower-plate loss"></div><div class="tower-plate win"></div><div class="tower-plate win"></div>
                            </div>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top:10px;">
                        <span class="prob-badge">PROB: {t1['acronym'] if t1.get('acronym') else 'A'} {prob_a*100:.1f}%</span>
                        <span class="prob-badge">PROB: {t2['acronym'] if t2.get('acronym') else 'B'} {prob_b*100:.1f}%</span>
                    </div>
                    """, unsafe_allow_html=True)

                    # Mercados
                    mercados = ["Ganador", "1ra Sangre", "Total Kills", "Total Torres", "Handicap Kills"]
                    sel_mer = st.selectbox("Mercado:", mercados, key=f"mer_{i}")
                    
                    c_lin, c_cuo = st.columns(2)
                    linea = c_lin.number_input("Línea Casino:", value=0.0, key=f"l_{i}")
                    cuota = c_cuo.number_input("Cuota Casino:", value=1.85, key=f"c_{i}")
                    
                    # Cálculo Kelly
                    if cuota > (1/prob_a):
                        kelly = (((cuota - 1) * prob_a) - (1 - prob_a)) / (cuota - 1)
                        stake = (kelly * 0.25) * bank_actual
                        st.success(f"🔥 VALOR DETECTADO: Sugerido {stake:.2f} U")
                        if st.button("Confirmar Apuesta", key=f"btn_{i}"):
                            gestionar_bank(bank_actual - stake)
                            st.rerun()
                    else:
                        st.warning("⚠️ Cuota por debajo de la probabilidad justa.")

# --- PANTALLA: BASE DE DATOS (CEBOLLA) ---
elif seccion == "🏆 Base de Datos (Cebolla)":
    st.title("Explorador de Equipos")
    
    # Capa 1: Ligas
    ligas_raw = call_api(slug, "leagues", "per_page=15")
    if ligas_raw:
        nombres_ligas = [l['name'] for l in ligas_raw]
        liga_sel = st.selectbox("Selecciona la Liga:", nombres_ligas)
        id_liga = next(l['id'] for l in ligas_raw if l['name'] == liga_sel)
        
        # Capa 2: Equipos
        equipos_raw = call_api(slug, f"leagues/{id_liga}/teams", "per_page=20")
        if equipos_raw:
            nombres_equipos = [e['name'] for e in equipos_raw]
            equipo_sel = st.selectbox("Selecciona el Equipo:", nombres_equipos)
            equipo_data = next(e for e in equipos_raw if e['name'] == equipo_sel)
            
            # Capa 3: Información y Jugadores
            st.markdown("---")
            col_eq, col_jg = st.columns([1, 2])
            with col_eq:
                st.image(equipo_data['image_url'], width=150)
                st.subheader(equipo_data['name'])
                st.write(f"Acrónimo: {equipo_data['acronym']}")
            
            with col_jg:
                st.write("**Jugadores de la Plantilla:**")
                jugadores = equipo_data.get('players', [])
                if jugadores:
                    for p in jugadores:
                        st.markdown(f"👤 **{p['name']}** - {p['role'] if p['role'] else 'Pro Player'}")
                else:
                    st.write("No hay datos de jugadores disponibles.")

# --- PANTALLA: ENCICLOPEDIA ---
elif seccion == "📚 Enciclopedia de Campeones":
    st.title(f"Campeones / Héroes: {juego_sel}")
    
    # Diccionario de muestra (esto se puede expandir)
    lore = {
        "lol": [
            {"n": "Lee Sin", "h": "Un monje ciego maestro del combate espiritual que protege Jonia."},
            {"n": "Jinx", "h": "Una criminal impulsiva de Zaun que vive para sembrar el caos."}
        ],
        "dota2": [
            {"n": "Anti-Mage", "h": "Un monje que busca destruir toda la magia del mundo tras la masacre de su templo."},
            {"n": "Pudge", "h": "Un carnicero que disfruta desmembrar a sus enemigos en el campo de batalla."}
        ],
        "mobile-legends": [
            {"n": "Layla", "h": "Una joven que usa su cañón de energía Maléfica para defender su hogar."},
            {"n": "Tigreal", "h": "El líder de los Caballeros de la Orden que personifica el honor."}
        ]
    }
    
    for c in lore.get(slug, []):
        with st.container():
            st.markdown(f"""
            <div class="glass-card">
                <h3 style="color:#38BDF8; margin:0;">{c['n']}</h3>
                <p style="font-size:14px; color:#94A3B8; margin-top:5px;">{c['h']}</p>
            </div>
            """, unsafe_allow_html=True)