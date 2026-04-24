import streamlit as st
import requests
import os
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y ACCESO (DASHBOARD PRIVADO)
# ==========================================
st.set_page_config(page_title="Quant Terminal Elite", layout="wide", initial_sidebar_state="expanded")

def check_password():
    def password_entered():
        if st.session_state["username"] == st.secrets["usuario"] and \
           st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else: st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center; color: #8AB4F8;'>🔑 Terminal Privada David</h2>", unsafe_allow_html=True)
        st.text_input("Usuario", on_change=password_entered, key="username")
        st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state: st.error("❌ Acceso Denegado")
        return False
    return True

if not check_password(): st.stop()

# ==========================================
# 2. CONFIGURACIÓN DE MOTORES (API & BANK)
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

def call_api(endpoint, params={}):
    url = f"https://api.pandascore.co/lol/{endpoint}"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers, params=params)
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
# 3. DISEÑO "TRADING DARK MODE"
# ==========================================
st.markdown("""
    <style>
    .stApp { background: #0E1117; color: #E8EAED; }
    [data-testid="stSidebar"] { background-color: #161B22 !important; }
    .match-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px; padding: 25px; margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }
    .team-logo { width: 80px; height: 80px; object-fit: contain; filter: drop-shadow(0 0 10px rgba(255,255,255,0.1)); }
    .vs-text { font-size: 24px; font-weight: bold; color: #58A6FF; text-shadow: 0 0 10px rgba(88,166,255,0.3); }
    .time-badge { background: #238636; color: white; padding: 4px 12px; border-radius: 6px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. NAVEGACIÓN LATERAL
# ==========================================
st.sidebar.title("⚡ Quant System")
menu = st.sidebar.radio("Navegación:", ["🔴 RADAR EN VIVO", "🏆 EXPLORADOR & STATS", "📊 CALCULADORA KELLY"])
st.sidebar.markdown("---")
st.sidebar.metric("🏦 MI BANKROLL", f"{bank_actual:.2f} U")

# ==========================================
# 5. PANTALLA 1: RADAR (CON TUS MERCADOS)
# ==========================================
if menu == "🔴 RADAR EN VIVO":
    hoy = datetime.now().strftime("%Y-%m-%d")
    st.title(f"🎮 Operaciones de Hoy ({hoy})")
    
    partidos = call_api("matches/upcoming", {"per_page": 25, "sort": "begin_at"})
    partidos_hoy = [p for p in partidos if p['begin_at'].startswith(hoy)]
    
    if not partidos_hoy:
        st.info("No hay partidos programados para el resto del día.")
    else:
        # LISTA DE MERCADOS SOLICITADOS
        mercados_pro = [
            "Ganador del Mapa", "1ra Sangre (Primer Kill)", "Handicap de Kills", 
            "Total Kills - Global (Más/Menos)", "Kills Equipo A (Más/Menos)", 
            "Kills Equipo B (Más/Menos)", "Total Dragones (Más/Menos)", 
            "Ambos Matan Dragón (Sí/No)", "Total Torres (Más/Menos)", "Duración del Mapa (Más/Menos)"
        ]
        
        # DISEÑO 2 COLUMNAS
        cols = st.columns(2)
        for i, m in enumerate(partidos_hoy):
            with cols[i % 2]:
                opp = m.get('opponents', [])
                if len(opp) < 2: continue
                
                t1, t2 = opp[0]['opponent'], opp[1]['opponent']
                
                # Reloj Bolivia (-4 UTC)
                dt_utc = datetime.strptime(m['begin_at'], "%Y-%m-%dT%H:%M:%SZ")
                hora_bol = (dt_utc - timedelta(hours=4)).strftime("%H:%M")
                
                st.markdown(f"""
                <div class="match-card">
                    <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                        <div style="width:40%;">
                            <img src="{t1['image_url']}" class="team-logo"><br><br><b>{t1['name']}</b>
                        </div>
                        <div class="vs-text">VS</div>
                        <div style="width:40%;">
                            <img src="{t2['image_url']}" class="team-logo"><br><br><b>{t2['name']}</b>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 20px;">
                        <span class="time-badge">🕒 {hora_bol} (Bolivia)</span>
                        <p style="font-size: 13px; margin-top: 10px; opacity: 0.6;">{m['league']['name']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"📈 OPERAR: {t1['name']} vs {t2['name']}"):
                    sel_mer = st.selectbox("Seleccionar Mercado:", mercados_pro, key=f"mer_{i}")
                    c1, c2 = st.columns(2)
                    cuo = c1.number_input("Cuota Casino:", value=1.85, step=0.01, key=f"q_{i}")
                    prob = c2.slider("Tu Prob. (%):", 10, 95, 55, key=f"p_{i}") / 100
                    
                    # Cálculo rápido de valor
                    if cuo > (1/prob):
                        st.success(f"✅ VALOR DETECTADO (Justa: {1/prob:.2f})")
                        if st.button(f"Confirmar {sel_mer} #{i}", use_container_width=True):
                            st.write("Registrado en historial...")
                    else:
                        st.warning(f"❌ Sin valor (Cuota justa: {1/prob:.2f})")

# ==========================================
# 6. PANTALLA 2: EXPLORADOR (WINRATE & LOGOS)
# ==========================================
elif menu == "🏆 EXPLORADOR & STATS":
    st.title("🏆 Análisis de Equipos y Ligas")
    busqueda = st.text_input("🔎 Buscar Equipo (Ej: T1, Gen.G, G2):")
    
    if busqueda:
        eqs = call_api("teams", {"filter[name]": busqueda})
        if eqs:
            for eq in eqs:
                col_img, col_info = st.columns([1, 4])
                with col_img: st.image(eq['image_url'], width=120)
                with col_info:
                    st.header(eq['name'])
                    # WinRate últimos 10
                    matches = call_api(f"teams/{eq['id']}/matches", {"per_page": 10})
                    wins = sum(1 for match in matches if match.get('winner_id') == eq['id'])
                    wr = (wins / 10) * 100 if matches else 0
                    st.write(f"**Win Rate Reciente:** {wr}%")
                    st.progress(wr/100)
                
                st.write("**Plantilla de Jugadores:**")
                p_cols = st.columns(5)
                for p_idx, p in enumerate(eq.get('players', [])):
                    with p_cols[p_idx % 5]:
                        st.image(p['image_url'] if p['image_url'] else "https://via.placeholder.com/80")
                        st.caption(f"**{p['name']}**")
                st.markdown("---")

# ==========================================
# 7. PANTALLA 3: CALCULADORA KELLY (1/4 SEGURA)
# ==========================================
elif menu == "📊 CALCULADORA KELLY":
    st.title("🧮 Criterio de Kelly (Gestión de 100 U)")
    st.info("Recomendamos usar 1/4 de Kelly para máxima seguridad del Bankroll.")
    
    c1, c2 = st.columns(2)
    p_est = c1.slider("Probabilidad estimada por tu modelo (%):", 5, 95, 50) / 100
    c_cas = c2.number_input("Cuota ofrecida por el casino:", value=2.00)
    
    b = c_cas - 1
    if b > 0:
        f_kelly = ((b * p_est) - (1 - p_est)) / b
        stake_final = f_kelly * 0.25 * bank_actual # 1/4 Kelly
        
        if stake_final > 0:
            st.metric("STAKE SUGERIDO", f"{stake_final:.2f} U")
            if st.button("📥 Ejecutar Apuesta y actualizar Bank"):
                gestionar_bank(bank_actual - stake_final)
                st.success("Bankroll actualizado.")
                st.rerun()
        else:
            st.error("⚠️ NO APOSTAR: El modelo no detecta ventaja matemática.")