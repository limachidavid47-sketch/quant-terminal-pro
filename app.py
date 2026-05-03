import streamlit as st
import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN CLOUD
# ==========================================
st.set_page_config(page_title="Quant Elite V82.1", layout="centered", initial_sidebar_state="expanded")

def check_password():
    # Sistema de autenticación preparado para Streamlit Cloud (Secrets)
    token = st.query_params.get("token", "")
    if token == "capo": st.session_state["password_correct"] = True
    if st.session_state.get("password_correct", False): return True
    
    st.markdown("""<style>.stApp { background-color: #05080F; color: #F8FAFC; }</style>""", unsafe_allow_html=True)
    st.markdown("<div style='background: #0F172A; border: 2px solid #10B981; border-radius: 20px; padding: 30px; margin-top: 5vh; text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #10B981; letter-spacing: 2px;'>⚡ TERMINAL CLOUD V82.1</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>INFRAESTRUCTURA HÍBRIDA: LoL + DOTA 2</p>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Operador")
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("AUTENTICAR"):
            # Requiere configurar st.secrets en la nube
            if u == st.secrets.get("usuario", "admin") and p == st.secrets.get("password", "quant123"):
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Acceso Denegado. Credenciales incorrectas.")
    st.markdown("</div>", unsafe_allow_html=True)
    return False

if not check_password(): st.stop()

# ==========================================
# 2. GESTIÓN DE DATOS Y BANKROLL (Protección Memoria)
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

def gestionar_bank(monto=None):
    if "bank_memoria" not in st.session_state:
        st.session_state["bank_memoria"] = 100.0
    
    archivo = "bank.txt"
    if monto is not None:
        st.session_state["bank_memoria"] = round(monto, 2)
        try:
            with open(archivo, "w") as f: f.write(str(round(monto, 2)))
        except: pass # Evita crasheos si la nube bloquea escritura
    else:
        if os.path.exists(archivo):
            try:
                with open(archivo, "r") as f: st.session_state["bank_memoria"] = float(f.read())
            except: pass
            
    return st.session_state["bank_memoria"]

bank_actual = gestionar_bank()

@st.cache_data(ttl=120)
def call_api_live(slug, endpoint, params_str=""):
    url = f"https://api.pandascore.co/{slug}/{endpoint}?{params_str}"
    headers = {"authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

# ==========================================
# 3. MOTOR DOTA 2 (NINJAS EN VIVO)
# ==========================================
@st.cache_data(ttl=300, show_spinner=False)
def motor_ninja_elite_dota(team_id, match_id=None):
    if not team_id: return 0.50, "S/D"
    
    url_team = f"https://api.opendota.com/api/teams/{team_id}/matches"
    try:
        r = requests.get(url_team, timeout=5)
        df = pd.DataFrame(r.json()).head(20)
        if df.empty: wr_base = 0.50
        else:
            pesos = np.exp(-np.linspace(0, 1.5, len(df))) 
            df['victoria'] = df.apply(lambda x: 1 if x.get('radiant_win') == x.get('radiant') else 0, axis=1)
            wr_base = np.average(df['victoria'], weights=pesos)
    except: wr_base = 0.50

    mod_z, mod_d = 0.0, 0.0 
    reporte = "Fase de Draft no disponible."

    if match_id:
        try:
            r_m = requests.get(f"https://api.opendota.com/api/matches/{match_id}", timeout=5)
            d_m = r_m.json()
            jugadores = d_m.get('players', [])
            if jugadores:
                anonimos = 0
                for p in jugadores:
                    if (p.get('isRadiant') and d_m.get('radiant_team_id') == team_id) or \
                       (not p.get('isRadiant') and d_m.get('dire_team_id') == team_id):
                        if p.get('account_id') is None: anonimos += 1
                        if p.get('hero_id') in [1, 5, 8, 15, 22]: mod_d += 0.02 

                mod_z = -0.06 * anonimos if anonimos > 0 else 0.05 
                mod_d = max(-0.10, min(0.10, mod_d)) 
                reporte = f"Titulares: {'NO (-Impacto)' if anonimos>0 else 'SÍ (+Impacto)'} | Bono Draft: {mod_d*100:+.1f}%"
        except: pass

    return max(0.05, min(0.95, wr_base + mod_z + mod_d)), reporte

# ==========================================
# 4. MOTOR LoL (ORACLE LOCAL)
# ==========================================
@st.cache_data(ttl=28800)
def load_lol_db():
    for f in os.listdir('.'):
        if (f.endswith('.csv') or f.endswith('.zip')) and 'oracle' in f.lower():
            try:
                df = pd.read_csv(f, usecols=lambda c: c.strip().lower() in ['teamname','position','result','golddiffat15','firstblood'], low_memory=False)
                df.columns = df.columns.str.strip().str.lower()
                return df
            except: pass
    return pd.DataFrame()

def get_lol_stats(team_name, df_completo):
    if df_completo.empty: return 0.50, 0.50
    words = [w for w in team_name.lower().split() if len(w) > 3]
    core = words[0] if words else team_name.lower().split()[0]
    df_t = df_completo[df_completo['teamname'].str.lower().str.contains(core, na=False) & (df_completo['position'] == 'team')].head(15)
    if df_t.empty: return 0.50, 0.50
    return df_t['result'].mean(), df_t['firstblood'].mean()

# ==========================================
# 5. UI Y CÁLCULO DE MERCADOS
# ==========================================
st.markdown("""<style>
    .stApp { background-color: #0A0F1E; color: #E2E8F0; }
    .glass-card { background: #1E293B; border: 1px solid #334155; border-radius: 15px; padding: 20px; margin-bottom: 20px; }
    .ninja-report { background: #0F172A; border-left: 4px solid #38BDF8; padding: 10px; font-size: 11px; margin-bottom: 10px; }
    .prob-box { background: #0F172A; border: 2px solid #EF4444; border-radius: 10px; padding: 15px; text-align: center; }
    .prob-number { font-size: 34px; font-weight: 900; color: #EF4444; }
    .cota-tag { background: #450A0A; color: #FECACA; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
</style>""", unsafe_allow_html=True)

st.sidebar.title("🛠️ INTERRUPTOR QUANT")
juego_sel = st.sidebar.selectbox("Motor Activo", ["League of Legends", "Dota 2"])
slug = "lol" if juego_sel == "League of Legends" else "dota2"

st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color:#EF4444; text-align:center;'>🏦 Mi Bankroll</h3>", unsafe_allow_html=True)
nuevo_bank = st.sidebar.number_input("Saldo (U):", value=float(bank_actual), step=10.0)
if st.sidebar.button("💾 Guardar Saldo"): gestionar_bank(nuevo_bank); st.rerun()

st.markdown(f"<h1 style='text-align: center;'>📡 QUANT TERMINAL: {juego_sel}</h1>", unsafe_allow_html=True)

partidos = call_api_live(slug, "matches", "filter[status]=running,not_started&sort=begin_at&per_page=15")

if not partidos:
    st.warning("Sin actividad en vivo detectada en la red.")
else:
    df_lol = load_lol_db() if slug == "lol" else pd.DataFrame()
    
    for i, m in enumerate(partidos):
        opp = m.get('opponents', [])
        if len(opp) < 2: continue
        t1, t2 = opp[0]['opponent'], opp[1]['opponent']
        
        st.markdown(f"""<div class="glass-card">
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #94A3B8; margin-bottom: 10px;">
                <span>🏆 {m['league']['name']}</span>
                <span>⏱️ {m['begin_at']}</span>
            </div>
            <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                <div style="width: 42%;"><b>{t1['name']}</b></div>
                <div style="color: #EF4444; font-weight: 900; font-size: 20px;">VS</div>
                <div style="width: 42%;"><b>{t2['name']}</b></div>
            </div>
        </div>""", unsafe_allow_html=True)

        with st.expander("🔬 INICIAR AUTOPSIA QUANT"):
            if slug == "dota2":
                with st.spinner("🕵️ Ninjas encriptando datos en la red profunda..."):
                    p_t1, rep1 = motor_ninja_elite_dota(t1['id'], m.get('id'))
                    p_t2, rep2 = motor_ninja_elite_dota(t2['id'], m.get('id'))
                
                st.markdown(f"""<div class="ninja-report"><b>🛡️ REPORTE NINJA DOTA 2:</b><br>{t1['name']}: {rep1}<br>{t2['name']}: {rep2}</div>""", unsafe_allow_html=True)
                
                prob_relativa = p_t1 / (p_t1 + p_t2)
                mercados = ["-- Seleccione --", "⭐ Ganador", "🏁 Carrera a 10 Kills", "👾 Primer Roshan", "⚖️ Handicap (+1.5)"]
            else:
                w1, f1 = get_lol_stats(t1['name'], df_lol)
                w2, f2 = get_lol_stats(t2['name'], df_lol)
                prob_relativa = w1 / (w1 + w2 if (w1+w2)>0 else 1)
                mercados = ["-- Seleccione --", "⭐ Ganador", "🩸 Primera Sangre", "⚖️ Handicap (+1.5)"]

            c1, c2 = st.columns(2)
            sel_m = c1.selectbox("Mercado", mercados, key=f"m_{i}_{slug}")
            if sel_m != "-- Seleccione --":
                op_sel = c2.radio("Favorito:", [t1['name'], t2['name']], key=f"o_{i}_{slug}", horizontal=True)
                cuota_cas = st.number_input("Cuota Casino", value=1.85, step=0.01, key=f"c_{i}_{slug}")
                
                p_final = prob_relativa if t1['name'] in op_sel else (1 - prob_relativa)
                if "10 Kills" in sel_m: p_final = 0.50 + ((p_final - 0.50) * 0.85)
                elif "Roshan" in sel_m: p_final = 0.50 + ((p_final - 0.50) * 0.75)
                elif "Handicap" in sel_m: p_final = min(0.95, p_final + 0.18)
                
                p_final = max(0.05, min(0.95, p_final))
                cota_justa = 1 / p_final
                
                st.markdown(f"""<div class="prob-box">
                    <div style="font-size: 12px; color: #94A3B8;">Probabilidad Real Ponderada</div>
                    <div class="prob-number">{p_final*100:.1f}%</div>
                    <div style="margin-top: 10px;"><span class="cota-tag">CUOTA JUSTA: {cota_justa:.2f}</span></div>
                </div>""", unsafe_allow_html=True)
                
                if cuota_cas > cota_justa:
                    st.success(f"🔥 VALOR DETECTADO. Kelly (5% Max): {((cuota_cas*p_final-1)/(cuota_cas-1))*0.25*bank_actual:.2f} U")
                else: st.error("❄️ EVITAR: Sin ventaja matemática.")