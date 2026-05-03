import streamlit as st
import requests
import os
import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN (V85.0)
# ==========================================
st.set_page_config(page_title="Quant Elite V85.0", layout="wide", initial_sidebar_state="expanded")

def check_password():
    token = st.query_params.get("token", "")
    if token == "capo": st.session_state["password_correct"] = True
    if st.session_state.get("password_correct", False): return True
    
    st.markdown("""<style>.stApp { background-color: #05080F; color: #F8FAFC; }</style>""", unsafe_allow_html=True)
    st.markdown("<div style='background: #0F172A; border: 2px solid #10B981; border-radius: 20px; padding: 30px; margin-top: 5vh; text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #10B981; letter-spacing: 2px;'>⚡ QUANT TERMINAL TOTAL</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>MOTOR UNIFICADO | NINJA DOTA 2 | ORACLE LOL</p>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Operador")
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("AUTENTICAR"):
            if u == st.secrets.get("usuario", "admin") and p == st.secrets.get("password", "quant123"):
                st.session_state["password_correct"] = True
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    return False

if not check_password(): st.stop()

# ==========================================
# 2. FINANZAS Y API CORE
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
def call_api(game, endpoint, params=""):
    url = f"https://api.pandascore.co/{game}/{endpoint}?{params}"
    headers = {"authorization": f"Bearer {API_KEY}"}
    try:
        r = requests.get(url, headers=headers)
        return r.json() if r.status_code == 200 else []
    except: return []

# ==========================================
# 3. NINJA DOTA 2: MAESTRÍA Y TRIFÁSICO
# ==========================================
@st.cache_data(ttl=86400, show_spinner=False)
def obtener_maestria_jugador(account_id, hero_id):
    if not account_id or not hero_id: return 0
    try:
        url = f"https://api.opendota.com/api/players/{account_id}/heroes"
        data = requests.get(url, timeout=3).json()
        for h in data:
            if str(h.get('hero_id')) == str(hero_id):
                games = h.get('games', 0)
                win = h.get('win', 0)
                if games >= 20: 
                    wr_heroe = win / games
                    if wr_heroe > 0.58: return 0.02 # Bono Main
                    if wr_heroe < 0.45: return -0.02 # Castigo
                return 0
        return 0
    except: return 0

@st.cache_data(ttl=300, show_spinner=False)
def motor_dota_trifasico(team_id, match_id=None):
    if not team_id: return 0.50, 0.50, 0.50, "S/D"
    
    # MACRO: Escalonamiento de Parches
    url_team = f"https://api.opendota.com/api/teams/{team_id}/matches"
    try:
        r = requests.get(url_team, timeout=5).json()
        df = pd.DataFrame(r).head(20)
        if df.empty: wr_base = 0.50
        else:
            pesos = np.exp(-np.linspace(0, 1.2, len(df)))
            df['victoria'] = df.apply(lambda x: 1 if x.get('radiant_win') == x.get('radiant') else 0, axis=1)
            wr_base = np.average(df['victoria'], weights=pesos)
    except: wr_base = 0.50

    # MICRO: Mains y Suplentes
    mod_jug, mod_count, reporte = 0.0, 0.0, "Draft Offline"
    if match_id:
        try:
            r_m = requests.get(f"https://api.opendota.com/api/matches/{match_id}", timeout=3).json()
            jugs = r_m.get('players', [])
            if jugs:
                anonimos = 0
                for p in jugs:
                    if (p.get('isRadiant') and r_m.get('radiant_team_id') == team_id) or \
                       (not p.get('isRadiant') and r_m.get('dire_team_id') == team_id):
                        acc_id, h_id = p.get('account_id'), p.get('hero_id')
                        if acc_id is None: anonimos += 1
                        else: mod_count += obtener_maestria_jugador(acc_id, h_id)
                        if h_id in [1, 5, 8, 15, 22]: mod_count += 0.015 
                mod_jug = -0.06 * anonimos if anonimos > 0 else 0.05 
                reporte = f"Mains: {mod_count*100:+.1f}% | Titulares: {'NO' if anonimos>0 else 'SÍ'}"
        except: pass

    wr_t = max(0.05, min(0.95, wr_base + mod_jug + mod_count))
    return wr_t * 0.92, wr_t * 0.96, wr_t * 1.02, reporte

# ==========================================
# 4. NINJA LOL: ORACLE ELEXIR
# ==========================================
@st.cache_data(ttl=28800)
def load_oracle():
    for f in os.listdir('.'):
        if (f.endswith('.csv') or f.endswith('.zip')) and ('oracle' in f.lower() or 'lol' in f.lower()):
            try: return pd.read_csv(f, low_memory=False)
            except: pass
    return pd.DataFrame()

def get_lol_stats(team_name, df_comp):
    if df_comp.empty: return 0.50, ['unknown']*5, 0.50, 0
    df_comp.columns = df_comp.columns.str.strip().str.lower()
    words = [w for w in team_name.lower().split() if len(w) > 3]
    core = words[0] if words else team_name.lower().split()[0]
    df_t = df_comp[(df_comp['teamname'].astype(str).str.contains(core, case=False, na=False)) & (df_comp['position'] == 'team')].head(15)
    if df_t.empty: return 0.50, ['unknown']*5, 0.50, 0
    wr = df_t['result'].mean()
    form = ['win' if r == 1 else 'loss' for r in df_t['result'].tolist()[:5]]
    fb = df_t['firstblood'].mean() if 'firstblood' in df_t.columns else 0.50
    gold = df_t['golddiffat15'].mean() if 'golddiffat15' in df_t.columns else 0
    return wr, form, fb, gold

# ==========================================
# 5. INTERFAZ V78 (SIN ERRORES DE RENDER)
# ==========================================
st.markdown("""<style>
    .stApp { background-color: #05080F; color: #F1F5F9; font-family: 'Inter', sans-serif; }
    .glass-card { background: #0F172A; border: 1px solid #1E293B; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.5); }
    .team-logo { width: 60px; height: 60px; object-fit: contain; }
    .winrate-text { font-size: 14px; color: #38BDF8; font-weight: 900; background: #1E293B; padding: 4px 10px; border-radius: 10px; display: inline-block; border: 1px solid #334155; }
    .tower-plate { width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin:0 2px; }
    .win { background: #10B981; } .loss { background: #EF4444; } .unknown { background: #334155; }
    .badge-live { background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }
    .prob-box { background: #1E293B; padding: 15px; border-radius: 8px; border: 1px solid #38BDF8; text-align: center; }
    .prob-number { font-size: 32px; font-weight: 900; color: #38BDF8; }
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#38BDF8;'>⚙️ TERMINAL V85</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center; background:#1E293B; padding:15px; border-radius:10px; border:1px solid #334155;'>Bankroll<br><span style='color:#10B981; font-weight:900; font-size:24px;'>{bank_actual} U</span></div>", unsafe_allow_html=True)
    juego_label = st.selectbox("🎯 Radar Activo", ["LoL", "Dota 2", "Valorant", "Mobile Legends"])
    slug = {"LoL": "lol", "Dota 2": "dota2", "Valorant": "valorant", "Mobile Legends": "mlbb"}[juego_label]
    st.markdown("---")
    nuevo_b = st.number_input("Caja", value=float(bank_actual))
    if st.button("💾 Guardar"): gestionar_bank(nuevo_b); st.rerun()

st.markdown(f"<h1 style='text-align: center;'>📡 RADAR TÁCTICO: {juego_label.upper()}</h1>", unsafe_allow_html=True)
tab_radar, tab_boveda = st.tabs(["📡 PANEL EN VIVO", "📊 BÓVEDA PREMIUM"])

partidos = call_api(slug, "matches", "filter[status]=running,not_started&sort=begin_at&per_page=15")
df_oracle = load_oracle() if slug == "lol" else pd.DataFrame()

if not partidos:
    st.info("Sin partidos próximos.")
else:
    with tab_radar:
        for i, m in enumerate(partidos):
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            video = m.get('streams_list', [{}])[0].get('raw_url', '#')
            badge = "<span class='badge-live'>🔴 EN VIVO</span>" if m['status'] == 'running' else "📅 PRÓXIMO"
            
            # Cálculo de Datos
            if slug == "lol": wr1, f1, fb1, g1 = get_lol_stats(t1['name'], df_oracle); wr2, f2, fb2, g2 = get_lol_stats(t2['name'], df_oracle)
            else: wr1, f1 = (0.5, ['unknown']*5); wr2, f2 = (0.5, ['unknown']*5)

            st.markdown(f"""
<div class="glass-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <div style="font-size: 13px; color: #94A3B8; font-weight: bold;">🏆 {m['league']['name']}</div>
        <div style="display: flex; gap: 15px; align-items: center;">{f'<a href="{video}" target="_blank" style="color:#A855F7; text-decoration:none; font-weight:bold;">📺 Live</a>' if video != '#' else ""} {badge}</div>
    </div>
    <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
        <div style="width: 35%;">
            <img src="{t1.get('image_url', '')}" class="team-logo"><br>
            <div style="font-weight: 900; font-size: 18px;">{t1['name']}</div>
            <div class="winrate-text">WR: {wr1*100:.0f}%</div><br>
            <div>{"".join([f"<span class='tower-plate {x}'></span>" for x in f1])}</div>
        </div>
        <div style="font-size: 28px; font-weight: 900; color: #334155;">VS</div>
        <div style="width: 35%;">
            <img src="{t2.get('image_url', '')}" class="team-logo"><br>
            <div style="font-weight: 900; font-size: 18px;">{t2['name']}</div>
            <div class="winrate-text">WR: {wr2*100:.0f}%</div><br>
            <div>{"".join([f"<span class='tower-plate {x}'></span>" for x in f2])}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

            with st.expander("🛠️ CALCULADORA"):
                c1, c2, c3 = st.columns([2, 1, 1])
                if slug == "dota2": mercs = ["⭐ Ganador (Late)", "🏁 Carrera a 10 Kills (Early)", "👾 Primer Roshan (Mid)", "⚖️ Handicap (+1.5)"]
                else: mercs = ["⭐ Ganador", "⚖️ Handicap (+1.5)", "🩸 Primera Sangre", "🏁 Carrera a 10 Kills"]
                
                sel_m = c1.selectbox("Mercado", mercs, key=f"merc_{i}")
                op_sel = c2.radio("A favor de:", [t1['name'], t2['name']], key=f"op_{i}", horizontal=True)
                cuo = c3.number_input("Cuota", value=1.85, key=f"cuo_{i}")

                # Matemática Sagrada
                if slug == "dota2":
                    e1, mid1, l1, rep1 = motor_dota_trifasico(t1['id'], m.get('id'))
                    e2, mid2, l2, rep2 = motor_dota_trifasico(t2['id'], m.get('id'))
                    if "Early" in sel_m: p = e1/(e1+e2) if t1['name'] in op_sel else e2/(e1+e2)
                    elif "Mid" in sel_m: p = mid1/(mid1+mid2) if t1['name'] in op_sel else mid2/(mid1+mid2)
                    else: p = l1/(l1+l2) if t1['name'] in op_sel else l2/(l1+l2)
                    if "Handicap" in sel_m: p = min(0.95, p + 0.18)
                else:
                    p_base = wr1/(wr1+wr2) if t1['name'] in op_sel else wr2/(wr1+wr2)
                    p = p_base + 0.15 if "Handicap" in sel_m else p_base

                p = max(0.05, min(0.95, p))
                c_justa = 1/p
                kelly = ((((cuo*p)-1)/(cuo-1))*0.25*bank_actual) if cuo > c_justa else 0
                color = "#10B981" if cuo > c_justa else "#EF4444"
                
                st.markdown(f"""
                <div class="prob-box" style="border-color:{color};">
                    <div class="prob-number" style="color:{color};">{p*100:.1f}%</div>
                    <div style="font-weight:bold;">C. JUSTA: {c_justa:.2f}</div>
                </div>""", unsafe_allow_html=True)
                if cuo > c_justa: st.success(f"💰 Sugerencia Kelly: {kelly:.2f} U")

    with tab_boveda:
        for m in partidos:
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            if slug == "dota2":
                e1, mid1, l1, rep1 = motor_dota_trifasico(t1['id'], m.get('id'))
                e2, mid2, l2, rep2 = motor_dota_trifasico(t2['id'], m.get('id'))
                st.markdown(f"""
<div style="background:#0F172A; padding:15px; border-radius:10px; border-left: 5px solid #A855F7; margin-bottom:10px;">
    <b>{t1['name']} vs {t2['name']}</b><br>
    <small style="color:#38BDF8;">🛡️ Early: {e1*100:.0f}% | ⚔️ Mid: {mid1*100:.0f}% | 🏰 Late: {l1*100:.0f}%</small><br>
    <small>🥷 {rep1}</small>
</div>""", unsafe_allow_html=True)
            elif slug == "lol":
                wr1, f1, fb1, g1 = get_lol_stats(t1['name'], df_oracle); wr2, f2, fb2, g2 = get_lol_stats(t2['name'], df_oracle)
                st.markdown(f"""
<div style="background:#0F172A; padding:15px; border-radius:10px; border-left: 5px solid #38BDF8; margin-bottom:10px;">
    <b>{t1['name']} vs {t2['name']}</b><br>
    <small>💰 Oro@15: {g1:+.0f} vs {g2:+.0f} | 🩸 FB: {fb1*100:.0f}% vs {fb2*100:.0f}%</small>
</div>""", unsafe_allow_html=True)