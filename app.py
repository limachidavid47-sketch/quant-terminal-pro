import streamlit as st
import requests
import os
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN (MENÚ ARREGLADO PARA CELULAR)
# ==========================================
# Cambiamos "collapsed" por "auto" para que en el celular se vea bien
st.set_page_config(page_title="Quant Elite", layout="wide", initial_sidebar_state="auto")

def check_password():
    def password_entered():
        if st.session_state["username"] == st.secrets["usuario"] and \
           st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]; del st.session_state["username"]
        else: st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center; color: #38BDF8;'>⚡ Acceso Quant</h2>", unsafe_allow_html=True)
        st.text_input("Usuario", on_change=password_entered, key="username")
        st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
        return False
    return True

if not check_password(): st.stop()

# ==========================================
# 2. MOTOR DE DATOS EN VIVO (SOLUCIÓN API)
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

# TTL bajado a 60 segundos para que se actualice rapidísimo
@st.cache_data(ttl=60) 
def call_api(game_slug, endpoint, params_str=""):
    url = f"https://api.pandascore.co/{game_slug}/{endpoint}?{params_str}"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

# LA SOLUCIÓN AL PROBLEMA DE LOS PARTIDOS QUE DESAPARECEN
@st.cache_data(ttl=60)
def obtener_radar_completo(slug):
    # 1. Buscamos los que están jugando AHORA MISMO (BO3)
    en_vivo = call_api(slug, "matches/running", "per_page=10")
    # 2. Buscamos los que vienen DESPUÉS
    proximos = call_api(slug, "matches/upcoming", "per_page=15&sort=begin_at")
    # 3. Juntamos ambas listas
    return en_vivo + proximos

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(monto))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

# ==========================================
# 3. NUEVO CSS (MIDNIGHT BLUE - MUCHO MÁS ELEGANTE)
# ==========================================
st.markdown("""
    <style>
    /* Fondo Azul Medianoche Oscuro */
    .stApp { background-color: #0B1120; color: #F1F5F9; font-family: 'Inter', sans-serif; }
    
    /* Tarjetas Minimalistas (Mejores en celular) */
    .glass-card {
        background: #1E293B; border: 1px solid #334155; 
        border-radius: 12px; padding: 15px; margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    
    /* Logos ajustados para no aplastarse en celular */
    .team-logo { width: 55px; height: 55px; object-fit: contain; }
    
    /* Textos y Badges */
    .vs-text { font-size: 16px; font-weight: bold; color: #64748B; padding: 0 10px; }
    .badge-live { background: #EF4444; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite;}
    .badge-time { background: #38BDF8; color: #0F172A; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. BARRA LATERAL (JUEGOS Y BANK)
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #38BDF8;'>🏦 Bankroll: {:.2f} U</h2>".format(bank_actual), unsafe_allow_html=True)
st.sidebar.markdown("---")

juegos = {
    "League of Legends": {"slug": "lol", "mercados": ["Ganador", "1ra Sangre", "Primer Dragón", "Handicap Kills"]},
    "Dota 2": {"slug": "dota2", "mercados": ["Ganador", "1ra Sangre", "Primer Roshan", "Handicap Kills"]},
    "Mobile Legends": {"slug": "mobile-legends", "mercados": ["Ganador", "1ra Sangre", "Primer Lord", "Handicap Kills"]}
}

st.sidebar.markdown("### 🎮 Disciplina:")
juego_sel = st.sidebar.radio("", list(juegos.keys()))
slug = juegos[juego_sel]["slug"]
mercados_dinamicos = juegos[juego_sel]["mercados"]

# ==========================================
# 5. RENDERIZADO DEL RADAR
# ==========================================
st.markdown(f"### 📡 Radar Activo: {juego_sel}")

# Llamamos a nuestra nueva función infalible
partidos_totales = obtener_radar_completo(slug)

# Filtramos solo los de hoy
hoy = datetime.now().strftime("%Y-%m-%d")
partidos_hoy = [p for p in partidos_totales if p['begin_at'].startswith(hoy)]

if not partidos_hoy:
    st.info(f"No hay partidos activos o programados hoy para {juego_sel}.")
else:
    for i, m in enumerate(partidos_hoy):
        opp = m.get('opponents', [])
        if len(opp) < 2: continue
        
        t1, t2 = opp[0]['opponent'], opp[1]['opponent']
        
        # Etiqueta de tiempo o EN VIVO
        if m['status'] == 'running':
            badge = "<span class='badge-live'>🔴 EN VIVO (Jugando)</span>"
        else:
            dt_utc = datetime.strptime(m['begin_at'], "%Y-%m-%dT%H:%M:%SZ")
            hora_bol = (dt_utc - timedelta(hours=4)).strftime("%H:%M")
            badge = f"<span class='badge-time'>🕒 Hoy a las {hora_bol}</span>"

        # Tarjeta diseñada para que no se rompa en celular
        st.markdown(f"""
        <div class="glass-card">
            <div style="margin-bottom: 10px; font-size: 12px; color: #94A3B8; display: flex; justify-content: space-between;">
                <span>🏆 {m['league']['name']}</span>
                {badge}
            </div>
            
            <div style="display: flex; justify-content: center; align-items: center;">
                <div style="text-align: center; width: 40%;">
                    <img src="{t1['image_url'] if t1['image_url'] else 'https://via.placeholder.com/55'}" class="team-logo"><br>
                    <span style="font-weight: bold; font-size: 14px;">{t1['name']}</span>
                </div>
                
                <div class="vs-text">VS</div>
                
                <div style="text-align: center; width: 40%;">
                    <img src="{t2['image_url'] if t2['image_url'] else 'https://via.placeholder.com/55'}" class="team-logo"><br>
                    <span style="font-weight: bold; font-size: 14px;">{t2['name']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Panel de Operación
        with st.expander(f"⚙️ Operar {t1['name']} vs {t2['name']}"):
            c1, c2 = st.columns(2)
            mer = c1.selectbox("Mercado:", mercados_dinamicos, key=f"m_{i}")
            cuota = c2.number_input("Cuota:", value=1.85, step=0.01, key=f"c_{i}")
            
            # Cálculo rápido de Kelly
            prob_real = 0.55 # Base, puedes cambiarlo con tu análisis
            if cuota > (1/prob_real):
                b = cuota - 1
                kelly = ((b * prob_real) - (1 - prob_real)) / b
                stake = (kelly * 0.25) * bank_actual
                if stake > 0:
                    st.success(f"✅ Hay Valor. Stake Recomendado: {stake:.2f} U")
                    if st.button("Aplicar al Bankroll", key=f"btn_{i}"):
                        gestionar_bank(bank_actual - stake)
                        st.rerun()
            else:
                st.warning("❌ Riesgo muy alto para esta cuota.")