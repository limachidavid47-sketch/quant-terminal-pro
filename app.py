import streamlit as st
import requests
import os
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN ULTRA
# ==========================================
st.set_page_config(page_title="Quant Terminal Ultra", layout="wide", initial_sidebar_state="collapsed")

def check_password():
    def password_entered():
        if st.session_state["username"] == st.secrets["usuario"] and \
           st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]; del st.session_state["username"]
        else: st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center; color: #10B981;'>⚡ Quant Access</h2>", unsafe_allow_html=True)
        st.text_input("Usuario", on_change=password_entered, key="username")
        st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
        return False
    return True

if not check_password(): st.stop()

# ==========================================
# 2. MOTORES DE DATOS Y CACHÉ (ANTI-BLOQUEO API)
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

# Usamos caché para no agotar tus peticiones gratuitas a PandaScore
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
# 3. CSS GLASSMORPHISM
# ==========================================
st.markdown("""
    <style>
    .stApp { background: #0B0E14; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    .glass-card {
        background: linear-gradient(145deg, rgba(30,41,59,0.5) 0%, rgba(15,23,42,0.8) 100%);
        border: 1px solid #334155; border-radius: 16px; padding: 20px; margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5); backdrop-filter: blur(10px);
    }
    .team-logo { width: 70px; height: 70px; object-fit: contain; filter: drop-shadow(0 0 10px rgba(255,255,255,0.1)); }
    .vs-text { font-size: 20px; font-weight: 900; color: #3B82F6; }
    .badge-live { background: #EF4444; color: white; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 12px; }
    .badge-time { background: #10B981; color: white; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SELECTOR MULTI-JUEGO Y MERCADOS
# ==========================================
st.markdown("<h2 style='text-align: center; color: #F8FAFC;'>🌐 Radar Táctico Global</h2>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align: center; color: #10B981;'>🏦 Bankroll: {bank_actual:.2f} U</h4>", unsafe_allow_html=True)

juegos = {
    "League of Legends": {"slug": "lol", "mercados": ["Ganador del Mapa", "1ra Sangre", "Primer Dragón", "Handicap Kills", "Duración del Mapa (+32.5)", "Total Torres"]},
    "Dota 2": {"slug": "dota2", "mercados": ["Ganador del Mapa", "1ra Sangre", "Primer Roshan", "Handicap Kills", "Duración del Mapa (+38.5)", "Total Kills (+45.5)"]},
    "Mobile Legends": {"slug": "mobile-legends", "mercados": ["Ganador del Mapa", "1ra Sangre", "Primer Lord/Tortuga", "Handicap Kills", "Duración del Mapa (+15.5)"]}
}

cols_juegos = st.columns(3)
if 'juego_activo' not in st.session_state: st.session_state.juego_activo = "League of Legends"

for idx, nombre in enumerate(juegos.keys()):
    with cols_juegos[idx]:
        if st.button(f"🕹️ {nombre}", use_container_width=True):
            st.session_state.juego_activo = nombre

juego_actual = juegos[st.session_state.juego_activo]
slug = juego_actual["slug"]
mercados_dinamicos = juego_actual["mercados"]

st.markdown("---")

# ==========================================
# 5. MOTOR DE PARTIDOS Y CÁLCULO DE WINRATE
# ==========================================
hoy = datetime.now().strftime("%Y-%m-%d")
partidos = call_api(slug, "matches/upcoming", "per_page=15&sort=begin_at")
partidos_hoy = [p for p in partidos if p['begin_at'].startswith(hoy)]

if not partidos_hoy:
    st.info(f"No hay partidos programados para hoy en {st.session_state.juego_activo}.")
else:
    cols = st.columns(2)
    for i, m in enumerate(partidos_hoy):
        with cols[i % 2]:
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            
            # Hora Bolivia (-4)
            dt_utc = datetime.strptime(m['begin_at'], "%Y-%m-%dT%H:%M:%SZ")
            hora_bol = (dt_utc - timedelta(hours=4)).strftime("%H:%M")
            
            st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                    <span style="font-size: 11px; color: #94A3B8;">{m['league']['name']}</span>
                    <span class="badge-time">🕒 {hora_bol}</span>
                </div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width:40%;">
                        <img src="{t1['image_url'] if t1['image_url'] else 'https://via.placeholder.com/70'}" class="team-logo"><br><b>{t1['name']}</b>
                    </div>
                    <div class="vs-text">VS</div>
                    <div style="width:40%;">
                        <img src="{t2['image_url'] if t2['image_url'] else 'https://via.placeholder.com/70'}" class="team-logo"><br><b>{t2['name']}</b>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # --- PANEL INTELIGENTE DE OPERACIÓN ---
            with st.expander("🔬 Analizar Estadísticas y Operar"):
                # Calculamos WinRate de las últimas 10 partidas de cada equipo EN VIVO
                historial_t1 = call_api(slug, f"teams/{t1['id']}/matches", "per_page=10")
                historial_t2 = call_api(slug, f"teams/{t2['id']}/matches", "per_page=10")
                
                wr_t1 = sum(1 for match in historial_t1 if match.get('winner_id') == t1['id']) / 10 if historial_t1 else 0.5
                wr_t2 = sum(1 for match in historial_t2 if match.get('winner_id') == t2['id']) / 10 if historial_t2 else 0.5
                
                # Visualización de fuerza
                st.markdown(f"**🔥 Últimas 10 partidas:**")
                st.progress(wr_t1, text=f"{t1['name']}: {wr_t1*100:.0f}% WinRate")
                st.progress(wr_t2, text=f"{t2['name']}: {wr_t2*100:.0f}% WinRate")
                
                # Selector de Mercado adaptado al juego
                mer = st.selectbox("Mercado:", mercados_dinamicos, key=f"m_{i}")
                
                c1, c2 = st.columns(2)
                cuota_casino = c1.number_input("Cuota Casino:", value=1.85, step=0.01, key=f"c_{i}")
                
                # Logica de valor cruzado
                equipo_fuerte = t1['name'] if wr_t1 > wr_t2 else t2['name']
                prob_real = max(wr_t1, wr_t2)
                
                # Ajuste de seguridad si no hay datos
                if prob_real == 0: prob_real = 0.5
                
                if cuota_casino > (1/prob_real):
                    # Kelly Seguro (1/4)
                    b = cuota_casino - 1
                    f_kelly = ((b * prob_real) - (1 - prob_real)) / b
                    stake = (f_kelly * 0.25) * bank_actual
                    
                    if stake > 0:
                        st.success(f"✅ ¡Ventaja Matemática en {equipo_fuerte}!")
                        st.markdown(f"💰 **Stake Sugerido (Kelly):** {stake:.2f} U")
                        if st.button("🚀 Ejecutar y Descontar", key=f"btn_{i}", use_container_width=True):
                            gestionar_bank(bank_actual - stake)
                            st.rerun()
                else:
                    st.error(f"❌ Cuota sin valor. El WinRate no justifica el riesgo.")