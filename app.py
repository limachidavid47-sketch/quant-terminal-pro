import streamlit as st
import requests
import os
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN INICIAL
# ==========================================
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
# 2. MOTOR DE DATOS
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

@st.cache_data(ttl=60)
def obtener_radar_completo(slug):
    en_vivo = call_api(slug, "matches/running", "per_page=10")
    proximos = call_api(slug, "matches/upcoming", "per_page=20&sort=begin_at")
    return en_vivo + proximos

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(monto))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

# ==========================================
# 3. CSS (BOTÓN DE STREAM AÑADIDO)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #0B1120; color: #F1F5F9; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #0F172A !important; border-right: 1px solid #1E293B; }
    .glass-card { background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    .team-logo { width: 50px; height: 50px; object-fit: contain; }
    .vs-text { font-size: 18px; font-weight: bold; color: #38BDF8; margin: 0 15px; }
    .badge-live { background: #EF4444; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite;}
    .badge-time { background: #38BDF8; color: #0F172A; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    
    /* Diseño del botón de Twitch/YouTube */
    .stream-btn {
        background-color: #9146FF; color: white !important; padding: 6px 12px; 
        border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: bold;
        display: inline-block; margin-top: 10px; border: 1px solid #772CE8;
        transition: 0.3s;
    }
    .stream-btn:hover { background-color: #772CE8; transform: translateY(-2px); }
    
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. BARRA LATERAL
# ==========================================
st.sidebar.markdown(f"<h2 style='text-align: center; color: #10B981;'>🏦 Bankroll: {bank_actual:.2f} U</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

juegos = {
    "League of Legends": {"slug": "lol", "mercados": ["Ganador del Mapa", "Handicap de Kills", "Total Kills (Global)", "Total Dragones", "Total Torres", "1ra Sangre"]},
    "Dota 2": {"slug": "dota2", "mercados": ["Ganador del Mapa", "Handicap de Kills", "Total Kills (Global)", "Total Torres", "Primer Roshan", "1ra Sangre"]},
    "Mobile Legends": {"slug": "mobile-legends", "mercados": ["Ganador del Mapa", "Handicap de Kills", "Total Kills", "Primer Lord", "1ra Sangre"]}
}

st.sidebar.markdown("### 🎮 Disciplina:")
juego_sel = st.sidebar.radio("", list(juegos.keys()))
slug = juegos[juego_sel]["slug"]
mercados_dinamicos = juegos[juego_sel]["mercados"]

# ==========================================
# 5. RADAR (STREAMING Y OPERACIONES)
# ==========================================
st.markdown(f"### 📡 Radar Activo: {juego_sel}")

partidos_totales = obtener_radar_completo(slug)
hoy = datetime.now().strftime("%Y-%m-%d")
partidos_hoy = [p for p in partidos_totales if p['begin_at'].startswith(hoy) or p['status'] == 'running']

if not partidos_hoy:
    st.info(f"No hay partidos activos o programados hoy para {juego_sel}.")
else:
    col1, col2 = st.columns(2)
    
    for i, m in enumerate(partidos_hoy):
        opp = m.get('opponents', [])
        if len(opp) < 2: continue
        
        t1, t2 = opp[0]['opponent'], opp[1]['opponent']
        img1 = t1['image_url'] if t1['image_url'] else 'https://via.placeholder.com/50'
        img2 = t2['image_url'] if t2['image_url'] else 'https://via.placeholder.com/50'
        
        # Extracción inteligente del enlace de Streaming
        stream_link = ""
        if m.get('official_video_url'):
            stream_link = m['official_video_url']
        elif m.get('streams_list') and len(m['streams_list']) > 0:
            stream_link = m['streams_list'][0].get('raw_url', '')
            
        boton_stream = f'<div style="text-align: center;"><a href="{stream_link}" target="_blank" class="stream-btn">📺 Ver Stream en Vivo</a></div>' if stream_link else ''

        if m['status'] == 'running':
            badge = "<span class='badge-live'>🔴 EN VIVO</span>"
        else:
            dt_utc = datetime.strptime(m['begin_at'], "%Y-%m-%dT%H:%M:%SZ")
            hora_bol = (dt_utc - timedelta(hours=4)).strftime("%H:%M")
            badge = f"<span class='badge-time'>🕒 {hora_bol}</span>"

        tarjeta_html = f"""<div class="glass-card">
<div style="margin-bottom: 8px; font-size: 11px; color: #94A3B8; display: flex; justify-content: space-between;">
<span>🏆 {m['league']['name']}</span>{badge}
</div>
<div style="display: flex; justify-content: center; align-items: center;">
<div style="text-align: center; width: 40%;">
<img src="{img1}" class="team-logo"><br>
<span style="font-weight: bold; font-size: 13px;">{t1['name']}</span>
</div>
<div class="vs-text">VS</div>
<div style="text-align: center; width: 40%;">
<img src="{img2}" class="team-logo"><br>
<span style="font-weight: bold; font-size: 13px;">{t2['name']}</span>
</div>
</div>
{boton_stream}
</div>"""

        columna_actual = col1 if i % 2 == 0 else col2
        
        with columna_actual:
            st.markdown(tarjeta_html, unsafe_allow_html=True)
            
            with st.expander(f"⚙️ Operar {t1['acronym'] if t1.get('acronym') else 'T1'} vs {t2['acronym'] if t2.get('acronym') else 'T2'}"):
                sel_mer = st.selectbox("Mercado:", mercados_dinamicos, key=f"m_{i}")
                
                if "Total" in sel_mer or "Handicap" in sel_mer:
                    c_lin, c_op, c_cuo = st.columns([1.2, 1.2, 1])
                    linea = c_lin.number_input("Línea (Ej: 26.5):", value=0.0, step=0.5, key=f"l_{i}")
                    if "Total" in sel_mer:
                        opcion = c_op.selectbox("Opción:", ["Más (+)", "Menos (-)"], key=f"op_{i}")
                    else:
                        opcion = c_op.selectbox("A favor de:", [t1['name'], t2['name']], key=f"op_{i}")
                    cuota = c_cuo.number_input("Cuota:", value=1.85, step=0.01, key=f"c_{i}")
                else:
                    c_op, c_cuo = st.columns([2, 1])
                    opcion = c_op.selectbox("Equipo:", [t1['name'], t2['name']], key=f"op_{i}")
                    cuota = c_cuo.number_input("Cuota:", value=1.85, step=0.01, key=f"c_{i}")

                prob_real = 0.55 
                if cuota > (1/prob_real):
                    kelly = (((cuota - 1) * prob_real) - (1 - prob_real)) / (cuota - 1)
                    stake = (kelly * 0.25) * bank_actual
                    if stake > 0:
                        st.success(f"✅ Valor detectado en **{opcion}**. Apuesta: {stake:.2f} U")
                        if st.button("Aplicar", key=f"btn_{i}", use_container_width=True):
                            gestionar_bank(bank_actual - stake)
                            st.rerun()
                else:
                    st.warning("❌ Cuota sin valor matemático.")