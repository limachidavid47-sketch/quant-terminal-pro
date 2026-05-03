import streamlit as st
import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Quant Elite V84.0", layout="wide", initial_sidebar_state="expanded")

def check_password():
    token = st.query_params.get("token", "")
    if token == "capo": st.session_state["password_correct"] = True
    if st.session_state.get("password_correct", False): return True
    st.markdown("""<style>.stApp { background-color: #05080F; color: #F8FAFC; }</style>""", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Operador")
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("AUTENTICAR"):
            if u == st.secrets.get("usuario", "admin") and p == st.secrets.get("password", "quant123"):
                st.session_state["password_correct"] = True
                st.rerun()
    return False

if not check_password(): st.stop()

# ==========================================
# 2. FINANZAS Y API CORE
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

def gestionar_bank(monto=None):
    if "bank_mem" not in st.session_state: st.session_state["bank_mem"] = 100.0
    if monto is not None: st.session_state["bank_mem"] = round(monto, 2)
    return st.session_state["bank_mem"]

bank_actual = gestionar_bank()

@st.cache_data(ttl=120)
def call_api(game, endpoint, params=""):
    url = f"https://api.pandascore.co/{game}/{endpoint}?{params}"
    headers = {"authorization": f"Bearer {API_KEY}"}
    try:
        r = requests.get(url, headers=headers)
        return r.json() if r.status_code == 200 else []
    except: return []

# ==========================================
# 3. MOTOR DOTA 2: TRIFÁSICO & CONSERVADOR
# ==========================================
@st.cache_data(ttl=300, show_spinner=False)
def motor_dota_trifasico(team_id):
    """Analiza Early, Mid y Late game con Probabilidad Conservadora"""
    if not team_id: return 0.50, 0.50, 0.50
    url = f"https://api.opendota.com/api/teams/{team_id}/matches"
    try:
        r = requests.get(url, timeout=5).json()
        df = pd.DataFrame(r).head(20)
        if df.empty: return 0.50, 0.50, 0.50
        
        # Winrate Base (Decaimiento Exponencial)
        pesos = np.exp(-np.linspace(0, 1.2, len(df)))
        df['victoria'] = df.apply(lambda x: 1 if x.get('radiant_win') == x.get('radiant') else 0, axis=1)
        wr_base = np.average(df['victoria'], weights=pesos)
        
        # Cálculo de Fases (Simulación Conservadora)
        p_early = wr_base * 0.92  # Castigo de varianza inicial
        p_mid = wr_base * 0.96    # Estabilidad de objetivos
        p_late = wr_base * 1.02   # El peso de la experiencia
        
        return max(0.05, min(0.95, p_early)), max(0.05, min(0.95, p_mid)), max(0.05, min(0.95, p_late))
    except: return 0.50, 0.50, 0.50

# ==========================================
# 4. MOTOR LoL (ORACLE INTACTO)
# ==========================================
@st.cache_data(ttl=28800)
def load_oracle():
    for f in os.listdir('.'):
        if (f.endswith('.csv') or f.endswith('.zip')) and 'oracle' in f.lower():
            try:
                df = pd.read_csv(f, usecols=lambda c: c.strip().lower() in ['teamname','position','result','golddiffat15','firstblood'], low_memory=False)
                df.columns = df.columns.str.strip().str.lower()
                return df
            except: pass
    return pd.DataFrame()

def get_lol_stats(team_name, df_comp):
    if df_comp.empty: return 0.50, 0.50, 0
    df_t = df_comp[(df_comp['teamname'].str.contains(team_name[:5], case=False, na=False)) & (df_comp['position'] == 'team')].head(15)
    return (df_t['result'].mean(), df_t['firstblood'].mean(), df_t['golddiffat15'].mean()) if not df_t.empty else (0.50, 0.50, 0)

# ==========================================
# 5. ESTILOS Y UI
# ==========================================
st.markdown("""<style>
    .stApp { background-color: #0B1120; color: #F1F5F9; }
    .glass-card { background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
    .prob-box { background: #0F172A; border: 2px solid #EF4444; border-radius: 10px; padding: 15px; text-align: center; }
    .prob-val { font-size: 34px; font-weight: 900; color: #EF4444; }
    .cota-tag { background: #450A0A; color: #FECACA; padding: 4px 10px; border-radius: 5px; font-weight: bold; font-size: 13px; }
    .badge-live { background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite; }
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #38BDF8;'>V84.0 TRIFÁSICA</h2>", unsafe_allow_html=True)
    juego_label = st.selectbox("MOTOR ACTIVO", ["LoL", "Dota 2", "Valorant", "Mobile Legends"])
    slug = {"LoL": "lol", "Dota 2": "dota2", "Valorant": "valorant", "Mobile Legends": "mlbb"}[juego_label]
    st.markdown(f"<div style='text-align: center; background: #0F172A; padding: 15px; border-radius: 10px; border: 1px solid #334155;'>Bankroll: <span style='color:#10B981; font-weight:bold;'>{bank_actual} U</span></div>", unsafe_allow_html=True)
    nuevo_b = st.number_input("Ajustar Capital", value=float(bank_actual))
    if st.button("💾 Guardar"): gestionar_bank(nuevo_b); st.rerun()

# ==========================================
# 6. PANEL DUAL (RADAR & BÓVEDA)
# ==========================================
tab_radar, tab_boveda = st.tabs(["📡 RADAR OPERATIVO", "📊 BÓVEDA DE DATOS"])

partidos = call_api(slug, "matches", "filter[status]=running,not_started&sort=begin_at&per_page=15")
df_oracle = load_oracle() if slug == "lol" else pd.DataFrame()

if not partidos:
    st.info("Sin actividad detectada.")
else:
    with tab_radar:
        for i, m in enumerate(partidos):
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            video_url = m.get('streams_list', [{}])[0].get('raw_url', '#')
            
            st.markdown(f"""<div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 12px; color: #94A3B8;">🏆 {m['league']['name']}</span>
                    <div>{f"<a href='{video_url}' target='_blank' style='color:#A855F7; text-decoration:none; font-weight:bold;'>📺 Live</a>" if video_url != '#' else ""}</div>
                </div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 40%; font-weight:bold; font-size:18px;">{t1['name']}</div>
                    <div style="color:#EF4444; font-weight:900; font-size:22px;">VS</div>
                    <div style="width: 40%; font-weight:bold; font-size:18px;">{t2['name']}</div>
                </div>
            </div>""", unsafe_allow_html=True)

            with st.expander("🔬 ABRIR CALCULADORA QUANT"):
                c1, c2, c3 = st.columns([2, 1, 1])
                if slug == "dota2":
                    e1, m1, l1 = motor_dota_trifasico(t1['id'])
                    e2, m2, l2 = motor_dota_trifasico(t2['id'])
                    mercados = ["Ganador", "Carrera 10 Kills (Early)", "Primer Roshan (Mid)", "Handicap (+1.5) (Late)"]
                    prob_base = l1 / (l1 + l2) # Por defecto Late para ganador
                else:
                    w1, fb1, g1 = get_lol_stats(t1['name'], df_oracle)
                    w2, fb2, g2 = get_lol_stats(t2['name'], df_oracle)
                    prob_base = w1 / (w1 + w2)
                    mercados = ["Ganador", "Primera Sangre", "Handicap (+1.5)"]

                sel_m = c1.selectbox("Mercado", mercados, key=f"m_{i}_{slug}")
                opcion = c2.radio("Favorito:", [t1['name'], t2['name']], key=f"o_{i}_{slug}", horizontal=True)
                cuota_c = c3.number_input("Cuota", value=1.85, key=f"c_{i}_{slug}")

                # Ajuste Trifásico Dota
                if slug == "dota2":
                    if "Early" in sel_m: p_raw = e1 / (e1 + e2) if t1['name'] in opcion else e2 / (e1 + e2)
                    elif "Mid" in sel_m: p_raw = m1 / (m1 + m2) if t1['name'] in opcion else m2 / (m1 + m2)
                    else: p_raw = l1 / (l1 + l2) if t1['name'] in opcion else l2 / (l1 + l2)
                else: p_raw = prob_base if t1['name'] in opcion else (1 - prob_base)

                p_final = max(0.05, min(0.95, p_raw))
                c_justa = 1 / p_final
                kelly = ((((cuota_c * p_final) - 1) / (cuota_c - 1)) * 0.25 * bank_actual) if cuota_c > 1.01 else 0
                
                color = "#10B981" if cuota_c > c_justa else "#EF4444"
                st.markdown(f"""<div class="prob-box" style="border-color:{color};">
                    <div class="prob-val" style="color:{color};">{p_final*100:.1f}%</div>
                    <div style="font-weight:bold;"><span class="cota-tag">COTA MÍN: {c_justa:.2f}</span></div>
                </div>""", unsafe_allow_html=True)
                if cuota_c > c_justa: st.success(f"💰 Sugerencia Kelly: {max(0.0, kelly):.2f} U")

    with tab_boveda:
        for m in partidos:
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            if slug == "dota2":
                e1, m1, l1 = motor_dota_trifasico(t1['id'])
                e2, m2, l2 = motor_dota_trifasico(t2['id'])
                st.markdown(f"""<div class="glass-card" style="border-left: 5px solid #EF4444;">
                    <b>{t1['name']} vs {t2['name']}</b><br>
                    🛡️ Early: {e1*100:.0f}% vs {e2*100:.0f}% | ⚔️ Mid: {m1*100:.0f}% vs {m2*100:.0f}% | 🏰 Late: {l1*100:.0f}% vs {l2*100:.0f}%
                </div>""", unsafe_allow_html=True)
            elif slug == "lol":
                w1, fb1, g1 = get_lol_stats(t1['name'], df_oracle)
                w2, fb2, g2 = get_lol_stats(t2['name'], df_oracle)
                st.markdown(f"""<div class="glass-card" style="border-left: 5px solid #38BDF8;">
                    <b>{t1['name']} vs {t2['name']}</b><br>
                    💰 Oro@15: {g1:+.0f} vs {g2:+.0f} | 🩸 First Blood: {fb1*100:.0f}% vs {fb2*100:.0f}%
                </div>""", unsafe_allow_html=True)