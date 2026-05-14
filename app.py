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
st.set_page_config(page_title="Quant Elite V88.10 - Full Operativa", layout="wide", initial_sidebar_state="expanded")

def check_password():
    token = st.query_params.get("token", "")
    if token == "capo": st.session_state["password_correct"] = True
    if st.session_state.get("password_correct", False): return True

    st.markdown("""<style>.stApp { background-color: #05080F; color: #F8FAFC; }</style>""", unsafe_allow_html=True)
    
    html_login = """
    <div style='background: #0F172A; border: 2px solid #10B981; border-radius: 20px; padding: 30px; margin-top: 5vh; box-shadow: 0 0 20px rgba(16, 185, 129, 0.2); text-align: center;'>
    <h2 style='color: #10B981; letter-spacing: 2px;'>⚡ QUANT TERMINAL V88.10</h2>
    <p style='color:#64748B;'>LOL PURE QUANT | CALCULADORA TOTAL | COTAS MÍNIMAS BÓVEDA</p>
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
# 3. EL CEREBRO QUANT LOL (90/10 + 60 DÍAS)
# ==========================================
@st.cache_data(ttl=28800, show_spinner=False)
def load_oracle_database():
    columnas_clave = ['teamname', 'playername', 'position', 'champion', 'date', 'result', 'kills', 'deaths', 'assists', 'teamkills', 'towers', 'opp_towers', 'dragons', 'barons', 'elders', 'ckpm', 'firstblood', 'gamelength', 'golddiffat15']
    if os.path.exists("datos_oracle.zip"):
        try:
            df = pd.read_csv("datos_oracle.zip", compression='zip', low_memory=False)
            df.columns = df.columns.str.strip().str.lower()
            return df[[c for c in columnas_clave if c in df.columns]]
        except: pass
    return pd.DataFrame()

def get_team_stats(team_name, team_id, df_completo):
    if df_completo.empty: return 0.5, ['unknown']*5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0
    core = team_name.lower().split()[0]
    df_t = df_completo[(df_completo['teamname'].str.lower().str.contains(core, na=False)) & (df_completo['position'].str.contains('team', case=False, na=False))].copy()
    df_t['date'] = pd.to_datetime(df_t['date'], errors='coerce')
    df_t = df_t.sort_values(by='date', ascending=False).head(15)
    if df_t.empty: return 0.5, ['unknown']*5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0
    
    sigma = df_t['gamelength'].std() / 60.0 if len(df_t)>2 else 0.0
    ahead = df_t[df_t['golddiffat15'] > 0]
    conv = len(ahead[ahead['result']==1])/len(ahead) if not ahead.empty else 0.5
    behind = df_t[df_t['golddiffat15'] <= 0]
    come = len(behind[behind['result']==1])/len(behind) if not behind.empty else 0.1

    return (df_t['result'].mean(), ['win' if r==1 else 'loss' for r in df_t['result'].tolist()[:5]], 
            df_t['teamkills'].mean(), df_t['towers'].mean(), df_t['opp_towers'].mean(), 
            df_t['dragons'].mean(), df_t['barons'].mean(), df_t['firstblood'].mean(), 
            df_t['gamelength'].mean()/60.0, df_t['golddiffat15'].mean(), conv, come, sigma, df_t['ckpm'].mean())

def get_h2h_data(t1_name, t2_name, df):
    c1, c2 = t1_name.lower().split()[0], t2_name.lower().split()[0]
    h2h = df[df['date'].isin(set(df[df['teamname'].str.lower().str.contains(c1, na=False)]['date']).intersection(set(df[df['teamname'].str.lower().str.contains(c2, na=False)]['date']))) & (df['position'].str.contains('team', case=False, na=False))].copy()
    h2h['date'] = pd.to_datetime(h2h['date'])
    h2h = h2h.sort_values(by='date', ascending=False).head(4)
    if not h2h.empty and (datetime.utcnow() - h2h['date'].max()).days > 60: return pd.DataFrame()
    return h2h

def obtener_friccion_regional(league_name):
    n = league_name.upper()
    if "LPL" in n: return -2.0, 3.5, -1.5 
    if "LCK" in n: return 3.0, -3.5, 1.5 
    return 0.0, 0.0, 0.0

def get_player_stats(team_name, df):
    core = team_name.lower().split()[0]
    tdf = df[df['teamname'].str.lower().str.contains(core, na=False) & (~df['position'].str.contains('team', case=False, na=False))].copy()
    if tdf.empty: return pd.DataFrame()
    st = tdf.groupby('playername').agg({'position':'first','kills':'mean','deaths':'mean','assists':'mean','champion':lambda x: x.value_counts().index[0]}).reset_index()
    st['kda'] = (st['kills']+st['assists'])/st['deaths'].replace(0,1)
    return st.sort_values(by='kda', ascending=False)

# ==========================================
# 4. SIDEBAR Y TEMAS
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#10B981;'>⚙️ V88.10 LOL</h2>", unsafe_allow_html=True)
    tema = st.selectbox("🎨 TEMA", ["Azul Oscuro", "Blanco Cuántico", "Verde Hacker"])
    nuevo_bank = st.number_input("Caja Base (U)", value=float(bank_actual))
    if st.button("💾 Guardar"): gestionar_bank(nuevo_bank); st.rerun()

paletas = {
    "Blanco Cuántico": ["#F8FAFC", "#FFFFFF", "#E2E8F0", "#0F172A", "#2563EB"],
    "Verde Hacker": ["#000000", "#022C22", "#064E3B", "#4ADE80", "#10B981"],
    "Azul Oscuro": ["#05080F", "#0F172A", "#1E293B", "#F8FAFC", "#38BDF8"]
}
c_bg, c_card, c_border, c_text, c_acc = paletas[tema]

st.markdown(f"""<style>
    .stApp {{ background-color: {c_bg}; color: {c_text}; font-family: 'Inter', sans-serif; }}
    .glass-card {{ background: {c_card}; border: 1px solid {c_border}; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    .team-logo {{ width: 60px; height: 60px; object-fit: contain; margin-bottom: 5px; }}
    .winrate-text {{ font-size: 14px; color: {c_acc}; font-weight: 900; background: {c_bg}; padding: 4px 10px; border-radius: 10px; border: 1px solid {c_border}; }}
    .tower-plate {{ width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin:0 2px; }}
    .win {{ background-color: #10B981; }} .loss {{ background-color: #EF4444; }} .unknown {{ background-color: #64748B; }}
    .badge-live {{ background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite; }}
    .stream-btn {{ background-color: #9146FF; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold; display: block; margin-top: 15px; text-align: center; }}
    .prob-box {{ background: {c_card}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; }}
    .prob-number {{ font-size: 32px; font-weight: 900; color: {c_acc}; }}
    .boveda-board {{ background-color: {c_card}; border: 1px solid {c_border}; border-radius: 14px; padding: 20px; margin-bottom: 20px; }}
    .boveda-row {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid {c_border}; }}
    .w-pred {{ font-weight: 900; color: {c_acc}; font-size: 14px; }}
    .w-cota {{ font-weight: bold; color: #EF4444; font-size: 11px; background: {c_bg}; padding: 3px 6px; border-radius: 4px; border: 1px solid #EF4444; margin-top: 4px; display: inline-block; }}
</style>""", unsafe_allow_html=True)

# ==========================================
# 5. RADAR Y BÓVEDA
# ==========================================
st.markdown(f"<h1 style='text-align: center; color: {c_text};'>📡 RADAR TÁCTICO: LEAGUE OF LEGENDS</h1>", unsafe_allow_html=True)
tab_radar, tab_boveda, tab_stats = st.tabs(["📡 PANEL EN VIVO", "📊 BÓVEDA PREMIUM", "🧬 ANALÍTICA PRO"])

df_oracle = load_oracle_database()
partidos = call_api_live("matches", "filter[status]=running,not_started&sort=begin_at&per_page=15")

if not partidos: st.info("Sincronizando...")
else:
    with tab_radar:
        for i, m in enumerate(partidos):
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            l_name = m.get('league', {}).get('name', 'Competición')
            l_img = m.get('league', {}).get('image_url', '')

            # Oracle Data
            wr1, f1, k1, tow1, otow1, drg1, bar1, fb1, time1, gold1, conv1, come1, sig1, ckpm1 = get_team_stats(t1['name'], t1['id'], df_oracle) 
            wr2, f2, k2, tow2, otow2, drg2, bar2, fb2, time2, gold2, conv2, come2, sig2, ckpm2 = get_team_stats(t2['name'], t2['id'], df_oracle) 

            placas1 = "".join([f"<span class='tower-plate {x}'></span>" for x in f1])
            placas2 = "".join([f"<span class='tower-plate {x}'></span>" for x in f2])
            
            streams = m.get('streams_list', [])
            video = streams[0].get('raw_url', '#') if streams else '#'
            btn_html = f"<a href='{video}' target='_blank' class='stream-btn'>📺 Ver Transmisión</a>" if video != '#' else ""

            st.markdown(f"""<div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div style="font-size: 13px; font-weight: bold;"><img src="{l_img}" width="20" style="vertical-align:middle; margin-right:5px;">{l_name}</div>
                    <div class="badge-live">LIVE</div>
                </div>
                <div style="display: flex; justify-content: space-around; text-align: center; align-items: center;">
                    <div style="width: 35%;"><b>{t1['name']}</b><br><img src="{t1.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr1*100:.0f}%</div><br>{placas1}</div>
                    <div style="font-size: 26px; font-weight: 900; color: {c_acc};">VS</div>
                    <div style="width: 35%;"><b>{t2['name']}</b><br><img src="{t2.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr2*100:.0f}%</div><br>{placas2}</div>
                </div>
                {btn_html}
            </div>""", unsafe_allow_html=True)

            with st.expander("🛠️ CALCULADORA QUANT (RESTAURADA)"):
                c1, c2 = st.columns(2)
                m_sel = c1.selectbox("Mercado", ["Ganador", "Total Torres", "Total Kills", "Duración", "Primera Sangre"], key=f"sel_{i}")
                
                # Restauración de Selectores de Equipo y Más/Menos
                if m_sel in ["Ganador", "Primera Sangre"]:
                    op_sel = c2.radio("A favor de:", [t1['name'], t2['name']], key=f"op_{i}", horizontal=True)
                else:
                    op_sel = c2.radio("Opción:", ["Más (+)", "Menos (-)"], key=f"op_{i}", horizontal=True)

                l1, l2 = st.columns(2)
                lin = l1.number_input("Línea", value=32.5 if m_sel=="Duración" else 12.5 if m_sel=="Total Torres" else 28.5, key=f"l_{i}")
                cuo = l2.number_input("Cuota Casino", value=1.85, key=f"c_{i}")

                # Matemática 90/10
                df_h = get_h2h_data(t1['name'], t2['name'], df_oracle)
                p_h = 0.10 if not df_h.empty else 0.0
                if p_h > 0:
                    h_wr = df_h[df_h['teamname'].str.contains(t1['name'].split()[0], case=False, na=False)]['result'].mean()
                    h_time, h_k, h_tow, h_ckpm = df_h['gamelength'].mean()/60.0, df_h['teamkills'].mean(), df_h['towers'].mean(), df_h['ckpm'].mean()
                    h_fb = df_h[df_h['teamname'].str.contains(t1['name'].split()[0], case=False, na=False)]['firstblood'].mean()
                else: h_wr, h_time, h_k, h_tow, h_ckpm, h_fb = 0.5, time1, k1, tow1, (ckpm1+ckpm2)/2, fb1

                b_wr = (wr1 * 0.9) + (h_wr * 0.1)
                b_time = (((time1+time2)/2)*0.9) + (h_time*0.1)
                b_tow = ((tow1+otow1)*0.9) + (h_tow*0.1)
                b_ck = (((ckpm1+ckpm2)/2)*0.9) + (h_ckpm*0.1)
                b_fb = (fb1*0.9) + (h_fb*0.1)

                z_t, z_k, z_tow = obtener_friccion_regional(l_name)
                
                if m_sel == "Ganador": 
                    prob = b_wr if t1['name'] in op_sel else (1-b_wr)
                elif m_sel == "Duración":
                    p_raw = 0.5 + (b_time + z_t - lin)*0.05
                    prob = p_raw if "Más" in op_sel else (1-p_raw)
                elif m_sel == "Total Torres":
                    p_raw = 0.5 + (b_tow + z_tow - lin)*0.1
                    prob = p_raw if "Más" in op_sel else (1-p_raw)
                elif m_sel == "Total Kills":
                    p_raw = 0.5 + (b_time * b_ck * 2 + z_k - lin)*0.03
                    prob = p_raw if "Más" in op_sel else (1-p_raw)
                else: # Primera Sangre
                    p_raw = b_fb / (b_fb + (1-b_fb)) if (b_fb+(1-b_fb))>0 else 0.5
                    prob = p_raw if t1['name'] in op_sel else (1-p_raw)

                prob = max(0.05, min(0.95, prob))
                c_j = 1/prob
                kelly = ((cuo*prob - 1)/(cuo-1)) * 0.25 * bank_actual if cuo > c_j else 0
                col_res = "#10B981" if cuo > c_j else "#EF4444"

                st.markdown(f"""<div class="prob-box" style="border-color:{col_res};">
                    <div class="prob-number" style="color:{col_res};">{prob*100:.1f}%</div>
                    <div style="font-weight:bold;">CUOTA JUSTA (C. MÍN): {c_j:.2f} | STAKE: {max(0, kelly):.2f} U</div>
                </div>""", unsafe_allow_html=True)

    with tab_boveda:
        st.markdown(f"<h3 style='color:{c_acc};'>📊 Bóveda Premium (Cotas Mínimas Incluidas)</h3>", unsafe_allow_html=True)
        for m in partidos:
            opp = m.get('opponents', [])
            if len(opp)<2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            wr1, f1, k1, tow1, otow1, drg1, bar1, fb1, time1, gold1, conv1, come1, sig1, ckpm1 = get_team_stats(t1['name'], t1['id'], df_oracle)
            wr2, f2, k2, tow2, otow2, drg2, bar2, fb2, time2, gold2, conv2, come2, sig2, ckpm2 = get_team_stats(t2['name'], t2['id'], df_oracle)
            
            p_win = wr1 / (wr1+wr2) if (wr1+wr2)>0 else 0.5
            p_fb = fb1 / (fb1+fb2) if (fb1+fb2)>0 else 0.5
            sem = "🔴" if sig1 > 4.5 else "🟢" if sig1 < 3.0 else "🟡"
            
            st.markdown(f"""<div class="boveda-board">
                <div class="boveda-row" style="border-bottom: 2px solid {c_border};"><div><b>{t1['name']} vs {t2['name']}</b></div><div class="w-pred">{m.get('league',{}).get('name')}</div></div>
                <div class="boveda-row"><div>⭐ GANADOR</div><div class="w-pred">{t1['name'] if p_win>=0.5 else t2['name']} ({max(p_win, 1-p_win)*100:.0f}%)</div><div class="w-cota">EXIGIR C.MÍN: {1/max(p_win, 0.05):.2f}</div></div>
                <div class="boveda-row"><div>🩸 FIRST BLOOD</div><div class="w-pred">{t1['name'] if p_fb>=0.5 else t2['name']}</div><div class="w-cota">EXIGIR C.MÍN: {1/max(p_fb, 1-p_fb, 0.05):.2f}</div></div>
                <div class="boveda-row"><div>🛡️ ESCALADO (25+)</div><div class="w-pred">Remontada {t1['name'][:3]}: {come1*100:.0f}% | {t2['name'][:3]}: {come2*100:.0f}%</div><div class="w-cota">VAR: {sig1:.1f}</div></div>
                <div class="boveda-row"><div>🗼 TORRES (12.5)</div><div>Proy: {tow1+otow2:.1f} estructuras</div><div class="w-cota">EXIGIR C.MÍN: {1/0.65:.2f}</div></div>
                <div class="boveda-row" style="border:none;"><div>⏱️ TIEMPO (32.5)</div><div>{time1:.1f}m {sem} | {time2:.1f}m</div><div class="w-cota">OBJ: {drg1+bar1:.1f}</div></div>
            </div>""", unsafe_allow_html=True)

    with tab_stats:
        st.subheader("🧬 Analítica Pro")
        sel_p = st.selectbox("Partido", [f"{p['opponents'][0]['opponent']['name']} vs {p['opponents'][1]['opponent']['name']}" for p in partidos if len(p.get('opponents',[]))>1])
        n1, n2 = sel_p.split(" vs ")
        c_k1, c_k2 = st.columns(2)
        with c_k1: st.dataframe(get_player_stats(n1, df_oracle), hide_index=True)
        with c_k2: st.dataframe(get_player_stats(n2, df_oracle), hide_index=True)
        st.markdown("### ⚔️ Historial H2H")
        st.table(get_h2h_data(n1, n2, df_oracle))