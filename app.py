import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y BANKROLL
# ==========================================
st.set_page_config(page_title="Quant Terminal Pro", layout="wide", page_icon="🏦")

def check_password():
    def password_entered():
        if st.session_state["username"] == st.secrets["usuario"] and \
           st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]; del st.session_state["username"]
        else: st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Acceso David Quant</h2>", unsafe_allow_html=True)
        st.text_input("Usuario", on_change=password_entered, key="username")
        st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
        return False
    return True

if not check_password(): st.stop()

# Manejo de Bankroll (Base 100 unidades)
def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(monto))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

# ==========================================
# 2. MOTOR DE DATOS (API)
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

def call_api(endpoint, params={}):
    url = f"https://api.pandascore.co/lol/{endpoint}"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers, params=params)
        return res.json() if res.status_code == 200 else []
    except: return []

# ==========================================
# 3. INTERFAZ Y ESTILOS
# ==========================================
st.markdown("""
    <style>
    .stApp { background: #0E1117; color: #E8EAED; }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px; padding: 20px; margin-bottom: 15px;
    }
    .kelly-box {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid #10B981;
        border-radius: 10px; padding: 15px; text-align: center;
    }
    .team-logo { width: 60px; height: 60px; object-fit: contain; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. NAVEGACIÓN
# ==========================================
st.sidebar.title("📊 Gestión Quant")
st.sidebar.metric("🏦 BANKROLL ACTUAL", f"{bank_actual:.2f} U")
st.sidebar.progress(min(bank_actual/200, 1.0)) # Barra visual de crecimiento

tab1, tab2, tab3 = st.tabs(["🔴 RADAR DIARIO", "🏆 EXPLORADOR & WINRATE", "🧮 CALCULADORA KELLY"])

# ------------------------------------------
# TAB 1: RADAR (PARTIDOS CON LOGOS)
# ------------------------------------------
with tab1:
    hoy = datetime.now().strftime("%Y-%m-%d")
    st.title("🎮 Partidos y Logos en Vivo")
    partidos = call_api("matches/upcoming", {"per_page": 20, "sort": "begin_at"})
    partidos_hoy = [p for p in partidos if p['begin_at'].startswith(hoy)]
    
    if not partidos_hoy:
        st.info("No hay más partidos para hoy.")
    else:
        for m in partidos_hoy:
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            
            with st.container():
                st.markdown(f"""
                <div class="glass-card">
                    <div style="display: flex; justify-content: space-around; align-items: center;">
                        <div style="text-align:center;"><img src="{t1['image_url']}" class="team-logo"><br><b>{t1['name']}</b></div>
                        <div style="font-size:24px; font-weight:bold;">VS</div>
                        <div style="text-align:center;"><img src="{t2['image_url']}" class="team-logo"><br><b>{t2['name']}</b></div>
                    </div>
                    <p style="text-align:center; opacity:0.6; margin-top:10px;">{m['league']['name']}</p>
                </div>
                """, unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: EXPLORADOR & WINRATE (%)
# ------------------------------------------
with tab2:
    st.title("🏆 WinRate y Rendimiento")
    query = st.text_input("🔎 Buscar Equipo para ver Porcentajes (Ej: T1, Gen.G):")
    
    if query:
        equipos = call_api("teams", {"filter[name]": query})
        if equipos:
            eq = equipos[0]
            st.image(eq['image_url'], width=100) if eq['image_url'] else None
            st.subheader(f"Estadísticas de {eq['name']}")
            
            # Obtener últimos 20 partidos para el WinRate
            historial = call_api(f"teams/{eq['id']}/matches", {"per_page": 20})
            if historial:
                victorias = sum(1 for match in historial if match.get('winner_id') == eq['id'])
                total = len(historial)
                wr = victorias / total
                
                st.write(f"**Win Rate (Últimos {total} partidos):**")
                st.progress(wr)
                st.markdown(f"<h2 style='color:#10B981;'>{wr*100:.1f}% de Efectividad</h2>", unsafe_allow_html=True)
            
            # Jugadores
            st.write("**Plantilla Actual:**")
            p_cols = st.columns(len(eq['players']))
            for idx, p in enumerate(eq['players']):
                with p_cols[idx]:
                    st.image(p['image_url'] if p['image_url'] else "https://via.placeholder.com/60")
                    st.caption(p['name'])
        else: st.error("No se encontró el equipo.")

# ------------------------------------------
# TAB 3: CALCULADORA KELLY SEGURO
# ------------------------------------------
with tab3:
    
    st.title("🧮 Propuesta de Apuesta (Kelly Seguro)")
    st.write("Esta calculadora usa **1/4 de Kelly**, la estrategia más segura para evitar la bancarrota.")
    
    col1, col2 = st.columns(2)
    prob_estimada = col1.slider("Tu Probabilidad Estimada (%):", 1, 99, 60) / 100
    cuota_casino = col2.number_input("Cuota del Casino:", value=1.85, step=0.01)
    
    # Lógica de Kelly Seguro (Fractional Kelly)
    # Formula: f = ((cuota - 1) * p - q) / (cuota - 1)
    q = 1 - prob_estimada
    b = cuota_casino - 1
    
    if b > 0:
        f_kelly = (b * prob_estimada - q) / b
        kelly_seguro = f_kelly * 0.25 # Usamos el 25% del Kelly original
        
        monto_apostar = bank_actual * kelly_seguro
        
        if monto_apostar > 0:
            st.markdown(f"""
            <div class="kelly-box">
                <h3 style="color:#10B981; margin:0;">🚀 Propuesta Kelly Seguro</h3>
                <p style="font-size:30px; margin:10px 0;"><b>{monto_apostar:.2f} U</b></p>
                <p>Equivale al <b>{kelly_seguro*100:.2f}%</b> de tu Bankroll</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📥 Ejecutar Apuesta y Actualizar Bankroll"):
                gestionar_bank(bank_actual - monto_apostar)
                st.success("Bankroll actualizado correctamente.")
                st.rerun()
        else:
            st.warning("⚠️ No hay valor suficiente en esta cuota para el modelo Kelly.")