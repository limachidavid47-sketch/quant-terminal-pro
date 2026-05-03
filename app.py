import streamlit as st
import requests
import os
import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN (CLOUD)
# ==========================================
st.set_page_config(page_title="Quant Elite V78.1", layout="wide", initial_sidebar_state="expanded")

def check_password():
    token = st.query_params.get("token", "")
    if token == "capo": st.session_state["password_correct"] = True
    if st.session_state.get("password_correct", False): return True
    
    st.markdown("""<style>.stApp { background-color: #05080F; color: #F8FAFC; }</style>""", unsafe_allow_html=True)
    st.markdown("<div style='background: #0F172A; border: 2px solid #38BDF8; border-radius: 20px; padding: 30px; margin-top: 5vh; text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #38BDF8; letter-spacing: 2px;'>⚡ QUANT TERMINAL CLOUD</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>MOTOR ORIGINAL + NINJA DOTA 2</p>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Operador")
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("AUTENTICAR"):
            if u == st.secrets.get("usuario", "admin") and p == st.secrets.get("password", "quant123"):
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Acceso Denegado.")
    st.markdown("</div>", unsafe_allow_html=True)
    return False

if not check_password(): st.stop()

# ==========================================
# 2. FINANZAS Y API PANDASCORE
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

def gestionar_bank(monto=None):
    if "bank_mem" not in st.session_state: st.session_state["bank_mem"] = 100.0
    if monto is not None: 
        st.session_state["bank_mem"] = round(monto, 2)
        try:
            with open("bank.txt", "w") as f: f.write(str(round(monto, 2)))
        except: pass # Protección para entornos nube de solo lectura
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
# 3. MOTORES DOTA 2 (NINJAS INVISIBLES)
# ==========================================
@st.cache_data(ttl=86400, show_spinner=False)
def obtener_maestria_jugador(account_id, hero_id):
    """Caché de 24h para no saturar la API buscando Mains"""
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
                    if wr_heroe > 0.58: return 0.02  # Main +2%
                    if wr_heroe < 0.45: return -0.02 # Mala práctica -2%
                return 0
        return 0
    except: return 0

@st.cache_data(ttl=300, show_spinner=False)
def motor_dota_trifasico(team_id, match_id=None):
    """Fusión de Macro (Decaimiento) y Micro (Draft, Suplentes, Mains)"""
    if not team_id: return 0.50, 0.50, 0.50, "S/D"
    
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

    mod_jugadores = 0.0
    mod_counters = 0.0
    reporte = "Draft Offline"
    
    if match_id:
        try:
            r_m = requests.get(f"https://api.opendota.com/api/matches/{match_id}", timeout=3).json()
            jugadores = r_m.get('players', [])
            if jugadores:
                anonimos = 0
                for p in jugadores:
                    if (p.get('isRadiant') and r_m.get('radiant_team_id') == team_id) or \
                       (not p.get('isRadiant') and r_m.get('dire_team_id') == team_id):
                        
                        account_id = p.get('account_id')
                        hero_id = p.get('hero_id')
                        if account_id is None: 
                            anonimos += 1
                        else:
                            mod_counters += obtener_maestria_jugador(account_id, hero_id)
                        
                        if hero_id in [1, 5, 8, 15, 22]: mod_counters += 0.015 

                mod_jugadores = -0.06 * anonimos if anonimos > 0 else 0.05 
                mod_counters = max(-0.10, min(0.10, mod_counters)) 
                reporte = f"Mains/Draft: {mod_counters*100:+.1f}% | Titulares: {'NO' if anonimos>0 else 'SÍ'}"
        except: pass

    wr_total = max(0.05, min(0.95, wr_base + mod_jugadores + mod_counters))
    return wr_total * 0.92, wr_total * 0.96, wr_total * 1.02, reporte

# ==========================================
# 4. MOTOR LoL (ORACLE LOCAL)
# ==========================================
@st.cache_data(ttl=28800)
def load_local_db():
    for f in os.listdir('.'):
        if (f.endswith('.csv') or f.endswith('.zip')) and ('oracle' in f.lower() or 'lol' in f.lower()):
            try:
                df = pd.read_csv(f, low_memory=False)
                df.columns = df.columns.str.strip().str.lower()
                return df
            except: pass
    return pd.DataFrame()

def get_team_stats_v78(team_id, team_name, df_comp, game):
    if game != "lol" or df_comp.empty:
        url = f"https://api.pandascore.co/{game}/matches?filter[opponent_id]={team_id}&filter[status]=finished&sort=-end_at&per_page=10"
        try:
            res = requests.get(url, headers={"authorization": f"Bearer {API_KEY}"}).json()
            if not res: return 0.50, ['unknown']*5, 0.50, 0
            wins = sum(1 for m in res if str(m.get('winner_id')) == str(team_id))
            form = ['win' if str(m.get('winner_id')) == str(team_id) else 'loss' for m in res[:5]]
            return (wins/len(res)), form, 0.50, 0
        except: return 0.50, ['unknown']*5, 0.50, 0

    words = [w for w in team_name.lower().split() if len(w) > 3]
    core = words[0] if words else team_name.lower().split()[0]
    
    if 'teamname' not in df_comp.columns: return 0.50, ['unknown']*5, 0.50, 0
    df_t = df_comp[(df_comp['teamname'].astype(str).str.contains(core, case=False, na=False)) & (df_comp['position'] == 'team')].head(15)
    if df_t.empty: return 0.50, ['unknown']*5, 0.50, 0
    
    wr = df_t['result'].mean() if 'result' in df_t.columns else 0.50
    form = ['win' if r == 1 else 'loss' for r in df_t['result'].tolist()[:5]] if 'result' in df_t.columns else ['unknown']*5
    fb = df_t['firstblood'].mean() if 'firstblood' in df_t.columns else 0.50
    gold = df_t['golddiffat15'].mean() if 'golddiffat15' in df_t.columns else 0
    return wr, form, fb, gold

# ==========================================
# 5. ESTÉTICA ORIGINAL V78
# ==========================================
st.markdown("""<style>
    .stApp { background-color: #05080F; color: #F1F5F9; font-family: 'Inter', sans-serif; }
    .glass-card { background: #0F172A; border: 1px solid #1E293B; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.5); }
    .team-logo { width: 60px; height: 60px; object-fit: contain; margin-bottom: 5px; }
    .winrate-text { font-size: 14px; color: #38BDF8; font-weight: 900; background: #1E293B; padding: 4px 10px; border-radius: 10px; display: inline-block; margin-top: 5px; border: 1px solid #334155; }
    .tower-plate { width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin:0 2px; }
    .win { background-color: #10B981; } .loss { background-color: #EF4444; } .unknown { background-color: #334155; }
    .badge-live { background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite; }
    .badge-time { background: #38BDF8; color: #05080F; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }
    .twitch-link { color: #A855F7; text-decoration: none; font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 5px; }
    .prob-box { background: #1E293B; padding: 15px; border-radius: 8px; border: 1px solid #38BDF8; text-align: center; }
    .prob-number { font-size: 32px; font-weight: 900; color: #38BDF8; }
</style>""", unsafe_allow_html=True)

# ==========================================
# 6. SIDEBAR: CENTRO DE MANDO
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#38BDF8;'>⚙️ V78.1 CORE</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center; background:#1E293B; padding:15px; border-radius:10px; border:1px solid #334155; margin-bottom:20px;'>Bankroll<br><span style='color:#10B981; font-weight:900; font-size:24px;'>{bank_actual} U</span></div>", unsafe_allow_html=True)
    
    juegos = {"League of Legends": "lol", "Dota 2": "dota2", "Valorant": "valorant", "Mobile Legends": "mlbb"}
    juego_label = st.selectbox("🎯 Seleccionar Radar", list(juegos.keys()))
    slug = juegos[juego_label]
    
    st.markdown("---")
    nuevo_b = st.number_input("Gestión de Caja (U)", value=float(bank_actual))
    if st.button("💾 Actualizar Bankroll", use_container_width=True): gestionar_bank(nuevo_b); st.rerun()

# ==========================================
# 7. PANTALLA PRINCIPAL: RADAR Y BÓVEDA
# ==========================================
st.markdown(f"<h1 style='text-align: center; color: #F8FAFC;'>📡 RADAR TÁCTICO: {juego_label.upper()}</h1>", unsafe_allow_html=True)

tab_radar, tab_boveda = st.tabs(["📡 PANEL EN VIVO", "📊 BÓVEDA PREMIUM"])

partidos = call_api(slug, "matches", "filter[status]=running,not_started&sort=begin_at&per_page=15")
df_local = load_local_db()

if not partidos:
    st.info(f"No hay partidos programados en las próximas horas para {juego_label}.")
else:
    with tab_radar:
        for i, m in enumerate(partidos):
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            
            video_url = m.get('streams_list', [{}])[0].get('raw_url', '#')
            stream_html = f"<a href='{video_url}' target='_blank' class='twitch-link'>📺 Ver Transmisión</a>" if video_url != '#' else ""
            badge = "<span class='badge-live'>🔴 EN VIVO</span>" if m['status'] == 'running' else f"<span class='badge-time'>{(datetime.strptime(m['begin_at'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).strftime('%H:%M')}</span>"

            wr1, f1, fb1, g1 = get_team_stats_v78(t1['id'], t1['name'], df_local, slug)
            wr2, f2, fb2, g2 = get_team_stats_v78(t2['id'], t2['name'], df_local, slug)

            placas_t1 = "".join([f"<span class='tower-plate {f}'></span>" for f in f1])
            placas_t2 = "".join([f"<span class='tower-plate {f}'></span>" for f in f2])

            st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div style="font-size: 13px; color: #94A3B8; font-weight: bold;">🏆 {m['league']['name']}</div>
                    <div style="display: flex; gap: 15px; align-items: center;">{stream_html} {badge}</div>
                </div>
                
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 35%;">
                        <img src="{t1.get('image_url', '')}" class="team-logo"><br>
                        <div style="font-weight: 900; font-size: 18px; color: #F8FAFC;">{t1['name']}</div>
                        <div class="winrate-text">WR: {wr1*100:.0f}%</div><br>
                        <div style="margin-top: 5px;">{placas_t1}</div>
                    </div>
                    
                    <div style="width: 10%; font-size: 28px; font-weight: 900; color: #334155;">VS</div>
                    
                    <div style="width: 35%;">
                        <img src="{t2.get('image_url', '')}" class="team-logo"><br>
                        <div style="font-weight: 900; font-size: 18px; color: #F8FAFC;">{t2['name']}</div>
                        <div class="winrate-text">WR: {wr2*100:.0f}%</div><br>
                        <div style="margin-top: 5px;">{placas_t2}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🛠️ CALCULADORA QUANT"):
                c1, c2, c3 = st.columns([2, 1, 1])
                
                # MERCADOS DINÁMICOS POR JUEGO
                if juego_label == "Dota 2":
                    mercados = ["⭐ Ganador (Late)", "🏁 Carrera a 10 Kills (Early)", "👾 Primer Roshan (Mid)", "⚖️ Handicap (+1.5) (Late)"]
                else:
                    mercados = ["⭐ Ganador del Partido", "⚖️ Handicap (+1.5)", "🩸 Primera Sangre", "🏁 Carrera a 10 Kills"]
                
                sel_m = c1.selectbox("Seleccionar Mercado", mercados, key=f"merc_{i}")
                opcion = c2.radio("Selección a favor de:", [t1['name'], t2['name']], key=f"op_{i}", horizontal=True)
                cuota_cas = c3.number_input("Cuota Casino", value=1.85, step=0.01, key=f"cuo_{i}")

                # CÁLCULO SEPARADO DOTA 2 vs RESTO
                if juego_label == "Dota 2":
                    e1, m1, l1, rep1 = motor_dota_trifasico(t1['id'], m.get('id'))
                    e2, m2, l2, rep2 = motor_dota_trifasico(t2['id'], m.get('id'))
                    
                    if "Early" in sel_m: p_pura = e1 / (e1 + e2) if t1['name'] in opcion else e2 / (e1 + e2)
                    elif "Mid" in sel_m: p_pura = m1 / (m1 + m2) if t1['name'] in opcion else m2 / (m1 + m2)
                    else: p_pura = l1 / (l1 + l2) if t1['name'] in opcion else l2 / (l1 + l2)
                    
                    if "Handicap" in sel_m: p_final = p_pura + 0.18
                    else: p_final = p_pura
                else:
                    prob_base_t1 = wr1 / (wr1 + wr2 if (wr1+wr2)>0 else 1)
                    p_pura = prob_base_t1 if t1['name'] in opcion else (1 - prob_base_t1)
                    
                    if "Sangre" in sel_m and slug == "lol":
                        p_final = fb1 / (fb1 + fb2 if (fb1+fb2)>0 else 1) if t1['name'] in opcion else fb2 / (fb1 + fb2 if (fb1+fb2)>0 else 1)
                    elif "Handicap" in sel_m: p_final = p_pura + 0.15
                    elif "10 Kills" in sel_m: p_final = 0.50 + ((p_pura - 0.50) * 0.80)
                    else: p_final = p_pura
                
                p_final = max(0.05, min(0.95, p_final))
                c_justa = 1 / p_final
                kelly = ((((cuota_cas * p_final) - 1) / (cuota_cas - 1)) * 0.25 * bank_actual) if cuota_cas > 1.01 else 0
                
                fuego = "🔥 ¡HAY VALOR!" if cuota_cas > c_justa else "❄️ DESCARTAR"
                color = "#10B981" if cuota_cas > c_justa else "#EF4444"
                
                st.markdown(f"""
                <div class="prob-box" style="border-color: {color};">
                    <div style="font-size: 13px; color: #94A3B8;">Probabilidad Matemática</div>
                    <div class="prob-number" style="color: {color};">{p_final*100:.1f}%</div>
                    <div style="margin-top: 10px; font-weight: bold;">
                        <span style="background: #05080F; padding: 4px 8px; border-radius: 4px; border: 1px solid {color};">C. JUSTA: {c_justa:.2f} | {fuego}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if cuota_cas > c_justa: st.success(f"💰 Riesgo Sugerido (Kelly): {max(0.0, kelly):.2f} U")

    with tab_boveda:
        st.markdown("<h3 style='color:#38BDF8;'>📋 Bóveda Premium de Autopsias</h3>", unsafe_allow_html=True)
        for m in partidos:
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            
            if juego_label == "Dota 2":
                e1, m1, l1, rep1 = motor_dota_trifasico(t1['id'], m.get('id'))
                e2, m2, l2, rep2 = motor_dota_trifasico(t2['id'], m.get('id'))
                st.markdown(f"""
                <div style="background:#0F172A; padding:15px; border-radius:10px; margin-bottom:10px; border-left: 5px solid #A855F7;">
                    <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">{t1['name']} <span style="color:#A855F7;">vs</span> {t2['name']}</div>
                    <div style="font-size: 13px; color: #94A3B8;">
                        <b>🛡️ Early:</b> {e1*100:.0f}% / {e2*100:.0f}%<br>
                        <b>⚔️ Mid:</b> {m1*100:.0f}% / {m2*100:.0f}%<br>
                        <b>🏰 Late:</b> {l1*100:.0f}% / {l2*100:.0f}%<br>
                        <i style="color:#38BDF8;">🥷 {t1['name']}: {rep1}</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                wr1, f1, fb1, g1 = get_team_stats_v78(t1['id'], t1['name'], df_local, slug)
                wr2, f2, fb2, g2 = get_team_stats_v78(t2['id'], t2['name'], df_local, slug)
                st.markdown(f"""
                <div style="background:#0F172A; padding:15px; border-radius:10px; margin-bottom:10px; border-left: 5px solid #38BDF8;">
                    <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">{t1['name']} <span style="color:#38BDF8;">vs</span> {t2['name']}</div>
                    <div style="font-size: 13px; color: #94A3B8;">
                        <b>Winrate Real:</b> {wr1*100:.0f}% / {wr2*100:.0f}%<br>
                        <b>Oro al Min 15:</b> {g1:+.0f} / {g2:+.0f}<br>
                        <b>Prob. First Blood:</b> {fb1*100:.0f}% / {fb2*100:.0f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)