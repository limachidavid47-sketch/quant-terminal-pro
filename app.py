import streamlit as st
import requests
import os
from datetime import datetime

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(page_title="Quant Terminal Elite", page_icon="⚡", layout="wide")

def check_password():
    def password_entered():
        if st.session_state["username"] == st.secrets["usuario"] and \
           st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center; color: #8AB4F8;'>🔓 Acceso Quant David</h2>", unsafe_allow_html=True)
        st.text_input("Usuario", on_change=password_entered, key="username")
        st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("❌ Credenciales incorrectas")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 2. CSS "ULTRA-PREMIUM" (Logos y Fondos)
# ==========================================
st.markdown("""
    <style>
    /* Fondo con degradado sutil para que no sea un negro plano */
    .stApp { 
        background: radial-gradient(circle at top, #1A1D24 0%, #0E1117 100%); 
        color: #E8EAED; 
    }
    
    /* Tarjetas tipo "Glassmorphism" */
    .match-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        transition: 0.4s ease;
    }
    .match-card:hover {
        border-color: #10B981;
        background: rgba(255, 255, 255, 0.05);
        transform: translateY(-5px);
    }

    /* Estilo de los Logos de Equipos */
    .logo-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 40%;
    }
    .team-logo {
        width: 85px;
        height: 85px;
        object-fit: contain;
        filter: drop-shadow(0 0 12px rgba(255,255,255,0.1));
        margin-bottom: 12px;
    }
    
    .vs-badge {
        background: #1A1D24;
        color: #8AB4F8;
        border: 1px solid #2D323E;
        padding: 5px 12px;
        border-radius: 50px;
        font-weight: bold;
        font-size: 14px;
    }

    .league-tag {
        background: rgba(138, 180, 248, 0.1);
        color: #8AB4F8;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. MOTOR DE DATOS EN VIVO (API)
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

def get_live_data(endpoint, params=None):
    url = f"https://api.pandascore.co/lol/{endpoint}"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        r = requests.get(url, headers=headers, params=params)
        return r.json() if r.status_code == 200 else []
    except: return []

# ==========================================
# 4. NAVEGACIÓN Y DASHBOARD
# ==========================================
st.sidebar.title("⚡ Quant Terminal")
if 'menu' not in st.session_state: st.session_state.menu = "Radar"

st.sidebar.markdown("---")
if st.sidebar.button("🔴 RADAR DE HOY", use_container_width=True): st.session_state.menu = "Radar"
if st.sidebar.button("🏆 EQUIPOS Y LOGOS", use_container_width=True): st.session_state.menu = "Equipos"

# --- PANTALLA: RADAR (Logos Brillantes) ---
if st.session_state.menu == "Radar":
    hoy = datetime.now().strftime("%Y-%m-%d")
    st.markdown(f"<h2>🗓️ Operaciones para hoy <span style='font-size:16px; opacity:0.5;'>({hoy})</span></h2>", unsafe_allow_html=True)
    
    partidos = get_live_data("matches/upcoming", {"per_page": 20, "sort": "begin_at"})
    
    # Filtrar solo partidos de hoy para que no se sature
    partidos_hoy = [p for p in partidos if p['begin_at'].startswith(hoy)]
    
    if not partidos_hoy:
        st.info("No hay más partidos programados por ahora. ¡Descansa el bankroll!")
    else:
        cols = st.columns(2)
        for i, m in enumerate(partidos_hoy):
            with cols[i % 2]:
                opp = m.get('opponents', [])
                if len(opp) < 2: continue
                
                t1, t2 = opp[0]['opponent'], opp[1]['opponent']
                # Si no hay logo, usamos uno por defecto elegante
                logo1 = t1['image_url'] if t1['image_url'] else "https://cdn-icons-png.flaticon.com/512/751/751557.png"
                logo2 = t2['image_url'] if t2['image_url'] else "https://cdn-icons-png.flaticon.com/512/751/751557.png"
                
                st.markdown(f"""
                <div class="match-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="logo-container">
                            <img src="{logo1}" class="team-logo">
                            <span style="font-weight: bold; text-align: center;">{t1['name']}</span>
                        </div>
                        <div class="vs-badge">VS</div>
                        <div class="logo-container">
                            <img src="{logo2}" class="team-logo">
                            <span style="font-weight: bold; text-align: center;">{t2['name']}</span>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 20px;">
                        <span class="league-tag">{m['league']['name']}</span>
                        <p style="font-size: 14px; margin-top: 10px; opacity: 0.6;">⚡ Comienza: {m['begin_at'][11:16]} UTC</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("📊 Abrir Panel de Análisis"):
                    st.write("Calculando probabilidad basada en histórico...")

# --- PANTALLA: EQUIPOS (Buscador con Logos) ---
elif st.session_state.menu == "Equipos":
    st.title("🏆 Galería de Equipos Pro")
    query = st.text_input("🔍 Escribe el nombre de un equipo (Ej: T1, Gen.G, G2):")
    
    if query:
        equipos = get_live_data("teams", {"filter[name]": query})
        if equipos:
            for eq in equipos:
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.image(eq['image_url'] if eq['image_url'] else "https://via.placeholder.com/150", width=120)
                with col2:
                    st.markdown(f"### {eq['name']}")
                    st.markdown(f"**Acrónimo:** {eq['acronym']}")
                    st.markdown(f"**ID de Servidor:** `{eq['id']}`")
                st.markdown("---")