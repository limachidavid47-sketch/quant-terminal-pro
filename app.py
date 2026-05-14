import streamlit as st
import requests
import os
import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN CLOUD
# ==========================================
st.set_page_config(page_title="Quant Elite V88.8 - LoL Core & Pro Analytics", layout="wide", initial_sidebar_state="expanded")

def check_password():
    token = st.query_params.get("token", "")
    if token == "capo": st.session_state["password_correct"] = True
    if st.session_state.get("password_correct", False): return True

    st.markdown("""<style>.stApp { background-color: #05080F; color: #F8FAFC; }</style>""", unsafe_allow_html=True)
    
    html_login = """
    <div style='background: #0F172A; border: 2px solid #10B981; border-radius: 20px; padding: 30px; margin-top: 5vh; box-shadow: 0 0 20px rgba(16, 185, 129, 0.2); text-align: center;'>
    <h2 style='color: #10B981; letter-spacing: 2px;'>⚡ QUANT TERMINAL V88.8</h2>
    <p style='color:#64748B;'>LOL PURE QUANT | H2H 60 DÍAS (10%) | INTERFAZ BLINDADA</p>
    </div>
    """
    st.markdown(html_login.replace('\n', ' '), unsafe_allow_html=True)
    
    with st.form("login_form"):
        u = st.text_input("Operador")
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("AUTENTICAR"):
            if u == st.secrets.get("usuario", "admin") and p == st.secrets.get("password", "quant123"):
                st.session_state["password_correct"] = True
                st.rerun()
    return False

if not check_password(): st.stop()

# ==========================================
# 2. FINANZAS Y GESTIÓN DE DATOS 
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

def gestionar_bank(monto=None):
    if "bank_mem" not in st.session_state: st.session_state["bank_mem"] = 100.0
    if monto is not None:
        st.session_state["bank_mem"] = round(monto, 2)
        try:
            with open("bank.txt", "w") as f: f.write(str(round(monto, 2)))
        except: pass
    elif os.path.exists("bank.txt"):
        try:
            with open("bank.txt", "r") as f: st.session_state["bank_mem"] = float(f.read())
        except: pass
    return st.session_state["bank_mem"]

bank_actual = gestionar_bank()

@st.cache_data(ttl=120)
def call_api_live(endpoint, params_str=""):
    url = f"https://api.pandascore.co/lol/{endpoint}?{params_str}"
    headers = {"authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

# ==========================================
# 3. EL CEREBRO QUANT LOL (ORACLE + H2H 60D + ANALYTICS)
# ==========================================
@st.cache_data(ttl=28800, show_spinner=False)
def load_oracle_database():
    columnas_clave = ['teamname', 'playername', 'position', 'champion', 'date', 'result', 'kills', 'deaths', 'assists', 'teamkills', 'towers', 'opp_towers', 'dragons', 'barons', 'elders', 'ckpm', 'firstblood', 'gamelength', 'golddiffat15']
    if os.path.exists("datos_oracle.zip"):
        try:
            df = pd.read_csv("datos_oracle.zip", compression='zip', low_memory=False)
            df.columns = df.columns.str.strip().str.lower()
            return df[[c for c in columnas_clave if c in df.columns]]
        except:
            try:
                df = pd.read_csv("datos_oracle.zip", low_memory=False)
                df.columns = df.columns.str.strip().str.lower()
                return df[[c for c in columnas_clave if c in df.columns]]
            except: pass
    return pd.DataFrame()

def get_team_stats(team_name, team_id, df_completo):
    if df_completo.empty: return 0.5, ['unknown']*5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0
    
    core_name = team_name.lower().split()[0]
    df_team = df_completo[(df_completo['teamname'].str.lower().str.contains(core_name, na=False)) & (df_completo['position'].str.contains('team', case=False, na=False))].copy()
    df_team['date'] = pd.to_datetime(df_team['date'], errors='coerce')
    df_team = df_team.sort_values(by='date', ascending=False).head(15) 
    
    if df_team.empty: return 0.5, ['unknown']*5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0
    
    sigma_time = df_team['gamelength'].std() / 60.0 if len(df_team) > 2 else 0.0
    conv_rate = len(df_team[(df_team['golddiffat15'] > 0) & (df_team['result'] == 1)]) / len(df_team[df_team['golddiffat15'] > 0]) if not df_team[df_team['golddiffat15'] > 0].empty else 0.5
    comeback_rate = len(df_team[(df_team['golddiffat15'] <= 0) & (df_team['result'] == 1)]) / len(df_team[df_team['golddiffat15'] <= 0]) if not df_team[df_team['golddiffat15'] <= 0].empty else 0.0

    return (df_team['result'].mean(), 
            ['win' if r == 1 else 'loss' for r in df_team['result'].tolist()[:5]], 
            df_team['teamkills'].mean(), df_team['towers'].mean(), df_team['opp_towers'].mean(), 
            df_team['dragons'].mean(), df_team['barons'].mean(), df_team['firstblood'].mean(), 
            df_team['gamelength'].mean()/60.0, df_team['golddiffat15'].mean(), conv_rate, comeback_rate, sigma_time, df_team['ckpm'].mean())

def get_h2h_direct_history(t1_name, t2_name, df):
    c1, c2 = t1_name.lower().split()[0], t2_name.lower().split()[0]
    h2h_df = df[df['date'].isin(set(df[df['teamname'].str.lower().str.contains(c1, na=False)]['date']).intersection(set(df[df['teamname'].str.lower().str.contains(c2, na=False)]['date']))) & (df['position'].str.contains('team', case=False, na=False))].copy()
    h2h_df['date'] = pd.to_datetime(h2h_df['date'])
    h2h_reciente = h2h_df.sort_values(by='date', ascending=False).head(4) # 2 mapas
    
    if not h2h_reciente.empty and (datetime.utcnow() - h2h_reciente['date'].max()).days > 60: return pd.DataFrame()
    return h2h_reciente

def obtener_friccion_regional(league_name):
    n = league_name.upper()
    if "LPL" in n: return -2.0, 3.5, -1.5 
    if "LCK" in n: return 3.0, -3.5, 1.5 
    return 0.0, 0.0, 0.0

def get_player_kda_pool(team_name, df):
    core = team_name.lower().split()[0]
    team_df = df[df['teamname'].str.lower().str.contains(core, na=False) & (~df['position'].str.contains('team', case=False, na=False))].copy()
    if team_df.empty: return pd.DataFrame()
    stats = team_df.groupby('playername').agg({'position': 'first', 'kills': 'mean', 'deaths': 'mean', 'assists': 'mean', 'champion': lambda x: x.value_counts().index[0]}).reset_index()
    stats['kda'] = (stats['kills'] + stats['assists']) / stats['deaths'].replace(0, 1)
    return stats.sort_values(by='kda', ascending=False)

# ==========================================
# 4. INTERFAZ Y ESTILOS
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#10B981;'>⚙️ V88.8 LOL CORE</h2>", unsafe_allow_html=True)
    tema = st.selectbox("🎨 TEMA", ["Azul Oscuro", "Blanco Cuántico", "Verde Hacker"])
    nuevo_b = st.number_input("Bankroll Base (U)", value=float(bank_actual))
    if st.button("💾 Guardar"): gestionar_bank(nuevo_b); st.rerun()

# Colores dinámicos
paletas = {
    "Blanco Cuántico": ["#F8FAFC", "#FFFFFF", "#E2E8F0", "#0F172A", "#2563EB"],
    "Verde Hacker": ["#000000", "#022C22", "#064E3B", "#4ADE80", "#10B981"],
    "Azul Oscuro": ["#05080F", "#0F172A", "#1E293B", "#F8FAFC", "#38BDF8"]
}
c_bg, c_card, c_border, c_text, c_acc = paletas[tema]

st.markdown(f"""<style>
    .stApp {{ background-color: {c_bg}; color: {c_text}; font-family: 'Inter', sans-serif; }}
    .glass-card {{ background: {c_card}; border: 1px solid {c_border}; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
    .team-logo {{ width: 60px; height: 60px; object-fit: contain; }}
    .winrate-text {{ font-size: 14px; color: {c_acc}; font-weight: 900; background: {c_bg}; padding: 4px 10px; border-radius: 10px; border: 1px solid {c_border}; }}
    .tower-plate {{ width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin:0 2px; }}
    .win {{ background-color: #10B981; }} .loss {{ background-color: #EF4444; }} .unknown {{ background-color: #64748B; }}
    .badge-live {{ background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite; }}
    .prob-box {{ background: {c_card}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; }}
    .prob-number {{ font-size: 32px; font-weight: 900; color: {c_acc}; }}
    .boveda-board {{ background-color: {c_card}; border: 1px solid {c_border}; border-radius: 14px; padding: 20px; margin-bottom: 20px; }}
    .boveda-row {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid {c_border}; }}
    .w-pred {{ font-weight: 900; color: {c_acc}; }}
    .w-cota {{ font-weight: bold; color: #EF4444; font-size: 11px; background: {c_bg}; padding: 3px 6px; border-radius: 4px; border: 1px solid #EF4444; }}
</style>""", unsafe_allow_html=True)

# ==========================================
# 5. RADAR, BÓVEDA Y ANALYTICS
# ==========================================
st.markdown(f"<h1 style='text-align: center; color: {c_text};'>📡 RADAR TÁCTICO: LEAGUE OF LEGENDS</h1>", unsafe_allow_html=True)
tab_radar, tab_boveda, tab_stats = st.tabs(["📡 PANEL EN VIVO", "📊 BÓVEDA PREMIUM", "🧬 ANALÍTICA PRO"])

partidos = call_api_live("matches", "filter[status]=running,not_started&sort=begin_at&per_page=15")
df_oracle = load_oracle_database()

if not partidos: st.info("Escaneando servidores...")
else:
    with tab_radar:
        for i, m in enumerate(partidos):
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            league_name = m.get('league', {}).get('name', 'League')
            league_img = m.get('league', {}).get('image_url', '')

            wr1, f1, k1, tow1, optow1, drg1, bar1, fb1, time1, gold1_15, conv1, come1, sig1, ckpm1 = get_team_stats(t1['name'], t1['id'], df_oracle) 
            wr2, f2, k2, tow2, optow2, drg2, bar2, fb2, time2, gold2_15, conv2, come2, sig2, ckpm2 = get_team_stats(t2['name'], t2['id'], df_oracle) 

            # H2H 60 Días / 10% Peso
            df_h2h = get_h2h_direct_history(t1['name'], t2['name'], df_oracle)
            peso_h2h = 0.10 if not df_h2h.empty else 0.0
            
            if peso_h2h > 0:
                h2h_wr = df_h2h[df_h2h['teamname'].str.contains(t1['name'].split()[0], case=False, na=False)]['result'].mean()
                h2h_time, h2h_k, h2h_tow, h2h_ckpm = df_h2h['gamelength'].mean()/60.0, df_h2h['teamkills'].mean(), df_h2h['towers'].mean(), df_h2h['ckpm'].mean()
                h2h_fb = df_h2h[df_h2h['teamname'].str.contains(t1['name'].split()[0], case=False, na=False)]['firstblood'].mean()
            else: h2h_wr, h2h_time, h2h_k, h2h_tow, h2h_ckpm, h2h_fb = 0.5, time1, k1, tow1, (ckpm1+ckpm2)/2, fb1

            st.markdown(f"""<div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="font-size: 13px; font-weight: bold;"><img src="{league_img}" width="20" style="vertical-align:middle; margin-right:5px;">{league_name}</div>
                    <div class="badge-live">LIVE</div>
                </div>
                <div style="display: flex; justify-content: space-around; text-align: center; align-items: center;">
                    <div style="width: 40%;"><b>{t1['name']}</b><br><img src="{t1.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr1*100:.0f}%</div></div>
                    <div style="font-size: 24px; font-weight: 900; color: {c_acc};">VS</div>
                    <div style="width: 40%;"><b>{t2['name']}</b><br><img src="{t2.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr2*100:.0f}%</div></div>
                </div>
            </div>""", unsafe_allow_html=True)

            with st.expander("🛠️ CALCULADORA QUANT (90/10)"):
                m_sel = st.selectbox("Mercado", ["Ganador", "Total Torres", "Total Kills", "Duración", "Primera Sangre"], key=f"m_{i}")
                lin = st.number_input("Línea", value=32.5 if m_sel=="Duración" else 12.5 if m_sel=="Total Torres" else 28.5, key=f"l_{i}")
                cuo = st.number_input("Cuota Casino", value=1.85, key=f"c_{i}")

                # BLENDING 90/10
                b_wr = (wr1 * 0.9) + (h2h_wr * 0.1)
                b_time = (((time1+time2)/2) * 0.9) + (h2h_time * 0.1)
                b_tow = (((tow1+optow1)) * 0.9) + (h2h_tow * 0.1)
                b_ckpm = (((ckpm1+ckpm2)/2) * 0.9) + (h2h_ckpm * 0.1)
                b_fb = (fb1 * 0.9) + (h2h_fb * 0.1)

                z_t, z_k, z_tow = obtener_friccion_regional(league_name)
                
                if m_sel == "Ganador": p = b_wr
                elif m_sel == "Duración": p = 0.5 + (b_time + z_t - lin) * 0.05
                elif m_sel == "Total Torres": p = 0.5 + (b_tow + z_tow - lin) * 0.1
                elif m_sel == "Total Kills": p = 0.5 + (b_time * b_ckpm * 2 + z_k - lin) * 0.03
                else: p = b_fb / (b_fb + (1-b_fb))

                p = max(0.05, min(0.95, p))
                c_j = 1/p
                kelly = ((cuo*p - 1)/(cuo-1)) * 0.25 * bank_actual if cuo > c_j else 0
                
                color = "#10B981" if cuo > c_j else "#EF4444"
                st.markdown(f"""<div class="prob-box" style="border-color:{color};">
                    <div class="prob-number" style="color:{color};">{p*100:.1f}%</div>
                    <div style="font-weight:bold;">CUOTA JUSTA: {c_j:.2f} | STAKE: {max(0, kelly):.2f} U</div>
                </div>""", unsafe_allow_html=True)

    with tab_boveda:
        for m in partidos:
            opp = m.get('opponents', [])
            if len(opp)<2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            wr1, f1, k1, tow1, optow1, drg1, bar1, fb1, time1, gold1_15, conv1, come1, sig1, ckpm1 = get_team_stats(t1['name'], t1['id'], df_oracle)
            wr2, f2, k2, tow2, optow2, drg2, bar2, fb2, time2, gold2_15, conv2, come2, sig2, ckpm2 = get_team_stats(t2['name'], t2['id'], df_oracle)
            sem1 = "🔴" if sig1 > 4.5 else "🟢"
            
            st.markdown(f"""<div class="boveda-board">
                <div class="boveda-row"><div><b>{t1['name']} vs {t2['name']}</b></div><div class="w-pred">{m.get('league',{}).get('name')}</div></div>
                <div class="boveda-row"><div>⭐ GANADOR</div><div class="w-pred">{t1['name'] if wr1>wr2 else t2['name']} ({max(wr1,wr2)*100:.0f}%)</div></div>
                <div class="boveda-row"><div>⏱️ TIEMPO & VAR</div><div>{time1:.1f}m {sem1} | {time2:.1f}m</div></div>
                <div class="boveda-row" style="border:none;"><div>🩸 FIRST BLOOD</div><div class="w-pred">{t1['name'] if fb1>fb2 else t2['name']}</div></div>
            </div>""", unsafe_allow_html=True)

    with tab_stats:
        st.subheader("🧬 Analítica Pro (H2H 60 Días)")
        if not partidos: st.info("Sin datos.")
        else:
            sel = st.selectbox("Partido", [f"{p['opponents'][0]['opponent']['name']} vs {p['opponents'][1]['opponent']['name']}" for p in partidos if len(p.get('opponents',[]))>1])
            n1, n2 = sel.split(" vs ")
            c1, c2 = st.columns(2)
            with c1: st.dataframe(get_player_kda_pool(n1, df_oracle), hide_index=True)
            with c2: st.dataframe(get_player_kda_pool(n2, df_oracle), hide_index=True)
            st.markdown("---")
            st.markdown("### ⚔️ Historial Directo (Últimos 2 Mapas)")
            st.table(get_h2h_direct_history(n1, n2, df_oracle))