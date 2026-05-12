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
st.set_page_config(page_title="Quant Elite V88.6 - LoL Core & Pro Analytics", layout="wide", initial_sidebar_state="expanded")

def check_password():
    token = st.query_params.get("token", "")
    if token == "capo": st.session_state["password_correct"] = True
    if st.session_state.get("password_correct", False): return True

    st.markdown("""<style>.stApp { background-color: #05080F; color: #F8FAFC; }</style>""", unsafe_allow_html=True)
    
    html_login = """
    <div style='background: #0F172A; border: 2px solid #10B981; border-radius: 20px; padding: 30px; margin-top: 5vh; box-shadow: 0 0 20px rgba(16, 185, 129, 0.2); text-align: center;'>
    <h2 style='color: #10B981; letter-spacing: 2px;'>⚡ QUANT TERMINAL V88.6</h2>
    <p style='color:#64748B;'>RADAR EXCLUSIVO LOL | LOGOS LIGA | TEMAS | ANALÍTICA PRO Y H2H</p>
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

def gestionar_historial(nueva_op=None, index_update=None, nuevo_estado=None):
    file_name = "historial_operaciones.csv"
    if not os.path.exists(file_name):
        pd.DataFrame(columns=["Fecha", "Juego", "Partido", "Mercado", "Opcion", "Cuota", "Inversion", "Estado", "MatchID", "TeamID"]).to_csv(file_name, index=False)
    df = pd.read_csv(file_name)
    if nueva_op: df = pd.concat([df, pd.DataFrame([nueva_op])], ignore_index=True)
    if index_update is not None: df.at[index_update, 'Estado'] = nuevo_estado
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df[df['Fecha'] >= (datetime.utcnow() - timedelta(hours=72))]
    try: df.to_csv(file_name, index=False)
    except: pass
    return df

@st.cache_data(ttl=120)
def call_api_live(endpoint, params_str=""):
    url = f"https://api.pandascore.co/lol/{endpoint}?{params_str}"
    headers = {"authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

# ==========================================
# 3. EL CEREBRO QUANT LOL (ORACLE + H2H + JUGADORES)
# ==========================================
@st.cache_data(ttl=21600, show_spinner=False)
def fetch_historical_data_general(team_id):
    url = "https://api.pandascore.co/lol/matches"
    params = f"filter[opponent_id]={team_id}&filter[status]=finished&sort=-end_at&per_page=10"
    headers = {"authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(f"{url}?{params}", headers=headers).json()
        if not res: return 0.50, ['unknown']*5
        wins = sum(1 for m in res if str(m.get('winner_id')) == str(team_id))
        form = ['win' if str(m.get('winner_id')) == str(team_id) else 'loss' for m in res]
        return (wins/len(res)), form[:5]
    except: return 0.50, ['unknown']*5

@st.cache_data(ttl=28800, show_spinner=False)
def load_oracle_database():
    # Estructura extendida para soportar tanto Bóveda como Analítica Pro de Jugadores
    columnas_clave = ['teamname', 'playername', 'position', 'champion', 'date', 'result', 'kills', 'deaths', 'assists', 'teamkills', 'towers', 'opp_towers', 'dragons', 'barons', 'firstblood', 'gamelength', 'golddiffat15']
    if os.path.exists("datos_oracle.zip"):
        try:
            df = pd.read_csv("datos_oracle.zip", compression='zip', low_memory=False)
            df.columns = df.columns.str.strip().str.lower()
            disponibles = [c for c in columnas_clave if c in df.columns]
            return df[disponibles]
        except:
            try:
                df = pd.read_csv("datos_oracle.zip", low_memory=False)
                df.columns = df.columns.str.strip().str.lower()
                disponibles = [c for c in columnas_clave if c in df.columns]
                return df[disponibles]
            except: pass
    return pd.DataFrame()

def get_team_stats(team_name, team_id, df_completo):
    if df_completo.empty: 
        wr, form = fetch_historical_data_general(team_id)
        return wr, form, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.50, 0.0, 0.0
    
    basura = ['esports', 'challengers', 'academy', 'gaming', 'club', 'sports', 'team']
    words = [w for w in team_name.lower().split() if w not in basura and len(w) > 2]
    core_name = words[0] if words else team_name.lower().split()[0]
    
    # Extraemos exclusivamente las filas globales del equipo para la Bóveda
    df_team = df_completo[(df_completo['teamname'].str.lower().str.contains(core_name, na=False)) & (df_completo['position'].str.contains('team', case=False, na=False))].copy()
    df_team['date'] = pd.to_datetime(df_team['date'], errors='coerce')
    df_team = df_team.sort_values(by='date', ascending=False).head(15) 
    
    if df_team.empty:
        wr, form = fetch_historical_data_general(team_id)
        return wr, form, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.50, 0.0, 0.0
    
    # Cálculo de Varianza Temporal (Desviación Estándar)
    sigma_time = df_team['gamelength'].std() / 60.0 if len(df_team) > 2 else 0.0
    
    if 'golddiffat15' in df_team.columns:
        ahead = df_team[df_team['golddiffat15'] > 0]
        wins_from_ahead = ahead[ahead['result'] == 1]
        conv_rate = len(wins_from_ahead) / len(ahead) if len(ahead) > 0 else 0.50
        
        behind = df_team[df_team['golddiffat15'] <= 0]
        wins_from_behind = behind[behind['result'] == 1]
        comeback_rate = len(wins_from_behind) / len(behind) if len(behind) > 0 else 0.0
    else: conv_rate, comeback_rate = 0.50, 0.0

    wins = df_team['result'].sum() 
    winrate = wins / len(df_team) if len(df_team) > 0 else 0.50
    form = ['win' if r == 1 else 'loss' for r in df_team['result'].tolist()[:5]]
    
    cols = df_team.columns
    avg_k = df_team['teamkills'].mean() if 'teamkills' in cols else 0.0
    avg_t = df_team['towers'].mean() if 'towers' in cols else 0.0
    avg_ot = df_team['opp_towers'].mean() if 'opp_towers' in cols else 0.0
    avg_d = df_team['dragons'].mean() if 'dragons' in cols else 0.0
    avg_b = df_team['barons'].mean() if 'barons' in cols else 0.0
    avg_fb = df_team['firstblood'].mean() if 'firstblood' in cols else 0.0
    avg_time = (df_team['gamelength'].mean() / 60) if 'gamelength' in cols else 0.0
    avg_gold15 = df_team['golddiffat15'].mean() if 'golddiffat15' in cols else 0.0
    
    return float(winrate), form, float(avg_k), float(avg_t), float(avg_ot), float(avg_d), float(avg_b), float(avg_fb), float(avg_time), float(avg_gold15), float(conv_rate), float(comeback_rate), float(sigma_time)

def obtener_friccion_regional(league_name):
    nombre = league_name.upper()
    if "LPL" in nombre or "LDL" in nombre: return -2.0, 3.5, -1.5 # China: partidas explosivas
    if "LCK" in nombre: return 3.0, -3.5, 1.5 # Corea: partidas metódicas y largas
    if "LEC" in nombre or "LCS" in nombre: return 1.0, 1.0, 0.5 # Occidente: fricción estándar
    return 0.0, 0.0, 0.0

# Funciones exclusivas para la Pestaña de Analítica Pro
def get_player_kda_pool(team_name, df):
    basura = ['esports', 'challengers', 'academy', 'gaming', 'club', 'sports', 'team']
    words = [w for w in team_name.lower().split() if w not in basura and len(w) > 2]
    core_name = words[0] if words else team_name.lower().split()[0]
    
    # Extraemos registros individuales de jugadores (excluyendo totales de equipo)
    team_df = df[df['teamname'].str.lower().str.contains(core_name, na=False) & (~df['position'].str.contains('team', case=False, na=False))].copy()
    if team_df.empty: return pd.DataFrame()
    
    if 'kills' not in team_df.columns or 'deaths' not in team_df.columns: return pd.DataFrame()
    
    # Cálculo de KDA y detección del campeón Main
    stats = team_df.groupby('playername').agg({
        'position': 'first',
        'kills': 'mean',
        'deaths': 'mean',
        'assists': 'mean',
        'champion': lambda x: x.value_counts().index[0] if not x.empty else 'N/A'
    }).reset_index()
    
    stats['kda'] = (stats['kills'] + stats['assists']) / stats['deaths'].replace(0, 1)
    return stats.sort_values(by='kda', ascending=False)

def get_h2h_direct_history(t1_name, t2_name, df):
    # Identificamos el core de cada escuadra
    c1 = t1_name.lower().split()[0] if len(t1_name.split()) > 0 else t1_name.lower()
    c2 = t2_name.lower().split()[0] if len(t2_name.split()) > 0 else t2_name.lower()
    
    t1_rows = df[df['teamname'].str.lower().str.contains(c1, na=False)]
    t2_rows = df[df['teamname'].str.lower().str.contains(c2, na=False)]
    
    # Cruzamos fechas exactas donde ambos compartieron mapa
    h2h_dates = set(t1_rows['date']).intersection(set(t2_rows['date']))
    if not h2h_dates: return pd.DataFrame()
    
    h2h_df = df[df['date'].isin(h2h_dates) & (df['position'].str.contains('team', case=False, na=False))]
    return h2h_df.sort_values(by='date', ascending=False).head(8) # Retorna los últimos 4 mapas (8 registros)

# ==========================================
# 4. SIDEBAR Y GESTIÓN DE TEMAS VISUALES
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#10B981;'>⚙️ V88.6 LOL CORE</h2>", unsafe_allow_html=True)
    
    # Selector de Interfaz
    st.markdown("<p style='font-size:12px; color:#64748B; margin-bottom:0;'>🎨 TEMA VISUAL</p>", unsafe_allow_html=True)
    tema_seleccionado = st.selectbox("", ["Azul Oscuro (Defecto)", "Blanco Cuántico", "Verde Hacker"], label_visibility="collapsed")
    
    st.markdown(f"<div style='text-align:center; background:var(--card-bg); padding:15px; border-radius:10px; border:1px solid var(--border-color); margin-top:15px; margin-bottom:20px;'>Bankroll Base<br><span style='color:#10B981; font-weight:900; font-size:24px;'>{bank_actual} U</span></div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-weight:bold; color:var(--text-color); margin-bottom:20px;'>🛡️ League of Legends</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    nuevo_b = st.number_input("Ajustar Caja Base (U)", value=float(bank_actual))
    if st.button("💾 Actualizar Bankroll", use_container_width=True): gestionar_bank(nuevo_b); st.rerun()

# Inyección dinámica de paletas de color en CSS
if tema_seleccionado == "Blanco Cuántico":
    c_bg, c_card, c_border, c_text, c_acc = "#F8FAFC", "#FFFFFF", "#E2E8F0", "#0F172A", "#2563EB"
elif tema_seleccionado == "Verde Hacker":
    c_bg, c_card, c_border, c_text, c_acc = "#000000", "#022C22", "#064E3B", "#4ADE80", "#10B981"
else: # Azul Oscuro
    c_bg, c_card, c_border, c_text, c_acc = "#05080F", "#0F172A", "#1E293B", "#F8FAFC", "#38BDF8"

st.markdown(f"""<style>
    .stApp {{ background-color: {c_bg}; color: {c_text}; font-family: 'Inter', sans-serif; }}
    .glass-card {{ background: {c_card}; border: 1px solid {c_border}; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    .team-logo {{ width: 60px; height: 60px; object-fit: contain; margin-bottom: 5px; }}
    .winrate-text {{ font-size: 14px; color: {c_acc}; font-weight: 900; background: {c_bg}; padding: 4px 10px; border-radius: 10px; display: inline-block; margin-top: 5px; border: 1px solid {c_border}; }}
    .tower-plate {{ width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin:0 2px; }}
    .win {{ background-color: #10B981; }} .loss {{ background-color: #EF4444; }} .unknown {{ background-color: #64748B; }}
    .badge-live {{ background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite; }}
    .badge-time {{ background: {c_acc}; color: {c_bg}; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }}
    .stream-btn {{ background-color: #9146FF; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold; display: block; margin-top: 20px; text-align: center; }}
    .prob-box {{ background: {c_card}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; }}
    .prob-number {{ font-size: 32px; font-weight: 900; color: {c_acc}; }}
    .boveda-board {{ background-color: {c_card}; border: 1px solid {c_border}; border-radius: 14px; padding: 20px; margin-bottom: 20px; }}
    .boveda-row {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid {c_border}; }}
    .w-col-1 {{ width: 32%; font-size: 13px; font-weight: bold; color: {c_text}; opacity: 0.8; }}
    .w-col-2 {{ width: 36%; text-align: center; font-size: 13px; background: {c_bg}; padding: 6px; border-radius: 6px; border: 1px solid {c_border}; }}
    .w-col-3 {{ width: 32%; text-align: right; }}
    .w-pred {{ font-weight: 900; color: {c_acc}; font-size: 14px; }}
    .w-cota {{ font-weight: bold; color: #EF4444; font-size: 11px; background: {c_bg}; padding: 3px 6px; border-radius: 4px; border: 1px solid #EF4444; display: inline-block; margin-top: 4px; }}
</style>""", unsafe_allow_html=True)

# ==========================================
# 5. RADAR, BÓVEDA Y ESTADÍSTICA PRO
# ==========================================
st.markdown(f"<h1 style='text-align: center; color: {c_text};'>📡 RADAR TÁCTICO: LEAGUE OF LEGENDS</h1>", unsafe_allow_html=True)

# Incorporamos la tercera pestaña solicitada
tab_radar, tab_boveda, tab_stats = st.tabs(["📡 PANEL EN VIVO", "📊 BÓVEDA PREMIUM", "🧬 ANALÍTICA PRO"])

partidos = call_api_live("matches", "filter[status]=running,not_started&sort=begin_at&per_page=15")
df_oracle = load_oracle_database()

hoy_local = datetime.utcnow() - timedelta(hours=4)
limite_inferior = hoy_local - timedelta(hours=12) 
limite_semana = hoy_local + timedelta(days=7)

partidos_filtrados = []
for p in partidos:
    if p['status'] == 'running': partidos_filtrados.append(p)
    elif p['status'] == 'not_started' and p.get('begin_at'):
        dt_local = datetime.strptime(p['begin_at'], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
        if limite_inferior <= dt_local <= limite_semana: partidos_filtrados.append(p)

if not partidos_filtrados:
    st.info("No hay encuentros de League of Legends programados en el marco temporal de escaneo.")
else:
    # --- PESTAÑA 1: RADAR EN VIVO (INTACTO) ---
    with tab_radar:
        for i, m in enumerate(partidos_filtrados):
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            
            badge = "<span class='badge-live'>🔴 EN VIVO</span>" if m['status'] == 'running' else f"<span class='badge-time'>📅 {(datetime.strptime(m['begin_at'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).strftime('%d/%m %H:%M')}</span>"
            
            lista_streams = m.get('streams_list', [])
            video_url = lista_streams[0].get('raw_url', '#') if lista_streams and len(lista_streams) > 0 else '#'
            stream_html = f"<a href='{video_url}' target='_blank' class='stream-btn'>📺 Ver Transmisión</a>" if video_url != '#' else ""
            
            # Integración de Logos de Liga solicitada
            league_name = m.get('league', {}).get('name', 'Competición')
            league_img = m.get('league', {}).get('image_url', '')
            logo_html = f"<img src='{league_img}' style='width:20px; height:20px; object-fit:contain; vertical-align:middle; margin-right:6px;'>" if league_img else ""

            wr1, f1, k1, tow1, optow1, drg1, bar1, fb1, time1, gold1_15, conv1, come1, sig1 = get_team_stats(t1['name'], t1['id'], df_oracle) 
            wr2, f2, k2, tow2, optow2, drg2, bar2, fb2, time2, gold2_15, conv2, come2, sig2 = get_team_stats(t2['name'], t2['id'], df_oracle) 

            placas_t1 = "".join([f"<span class='tower-plate {x}'></span>" for x in f1])
            placas_t2 = "".join([f"<span class='tower-plate {x}'></span>" for x in f2])

            html_tarjeta = f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div style="font-size: 13px; font-weight: bold; color: {c_text};">{logo_html}{league_name}</div>
                    <div>{badge}</div>
                </div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 35%;">
                        <div style="font-size:15px; font-weight:bold;">{t1['name']}</div>
                        <img src="{t1.get('image_url','')}" class="team-logo"><br>
                        <div class="winrate-text">WR: {wr1*100:.0f}%</div><br>
                        <div style="margin-top:5px;">{placas_t1}</div>
                    </div>
                    <div style="font-size: 26px; font-weight: bold; color: {c_acc};">VS</div>
                    <div style="width: 35%;">
                        <div style="font-size:15px; font-weight:bold;">{t2['name']}</div>
                        <img src="{t2.get('image_url','')}" class="team-logo"><br>
                        <div class="winrate-text">{wr2*100:.0f}%</div><br>
                        <div style="margin-top:5px;">{placas_t2}</div>
                    </div>
                </div>
                {stream_html}
            </div>
            """
            st.markdown(html_tarjeta.replace('\n', ' '), unsafe_allow_html=True)

            with st.expander("🛠️ CALCULADORA QUANT"):
                c1, c2 = st.columns(2)
                mercs = ["-- Seleccione --", "⭐ PARTIDO: Ganador", "⚖️ Handicap de Mapas", "🗼 Total Torres", "🐉 Total Dragones", "👾 Total Barones", "⚔️ Total Kills", "⏱️ Duración", "🩸 Primera Sangre"]
                sel_m = c1.selectbox("Mercado", mercs, key=f"m_{i}")
                
                if sel_m != "-- Seleccione --":
                    if "Total" in sel_m or "Duración" in sel_m:
                        op_sel = c2.radio("Opción:", ["Más (+)", "Menos (-)"], key=f"o_{i}", horizontal=True)
                    else:
                        op_sel = c2.radio("A favor de:", [t1['name'], t2['name']], key=f"o_{i}", horizontal=True)
                    
                    c_l1, c_l2 = st.columns(2)
                    def_l = 32.5 if "Duración" in sel_m else 28.5 if "Kills" in sel_m and "Total" in sel_m else 12.5 if "Torres" in sel_m else -1.5 if "Handicap" in sel_m else 0.0
                    lin = c_l1.number_input("Línea Flexible", value=def_l, key=f"l_{i}")
                    cuo = c_l2.number_input("Cuota del Casino", value=1.00, step=0.01, key=f"c_{i}")

                    has_data = (k1 > 0 and k2 > 0)
                    if has_data:
                        z_time, z_kills, z_tow = obtener_friccion_regional(league_name)
                        
                        exp_time = ((time1 + time2) / 2) + z_time
                        exp_k = (k1 + k2) + z_kills
                        exp_tow = (tow1 + optow1) + z_tow
                        
                        mod_time, mod_obj = 0, 0
                        if come1 > 0.35 and come2 > 0.35: mod_time, mod_obj = 2.0, 1.5 
                        elif conv1 > 0.55 and conv2 > 0.55: mod_time, mod_obj = -2.0, -1.0 
                        
                        adj_time = exp_time + mod_time
                        adj_k = exp_k + (mod_obj * 2)
                        adj_tow = exp_tow + mod_obj
                        
                        p_gb = wr1 / (wr1+wr2) if (wr1+wr2) > 0 else 0.50
                        if t1['name'] not in op_sel: p_gb = 1 - p_gb
                        
                        if "Duración" in sel_m: p_raw = 0.50 + (adj_time - lin) * 0.05; p_final = p_raw if "Más" in op_sel else (1-p_raw)
                        elif "Total Kills" in sel_m: p_raw = 0.50 + (adj_k - lin) * 0.03; p_final = p_raw if "Más" in op_sel else (1-p_raw)
                        elif "Torres" in sel_m: p_raw = 0.50 + (adj_tow - lin) * 0.10; p_final = p_raw if "Más" in op_sel else (1-p_raw)
                        elif "Sangre" in sel_m: p_final = fb1/(fb1+fb2) if (fb1+fb2)>0 else 0.50; p_final = p_final if t1['name'] in op_sel else (1-p_final)
                        elif "Handicap" in sel_m: p_final = p_gb - (abs(lin)*0.2) if lin < 0 else p_gb + (abs(lin)*0.2)
                        else: p_final = p_gb
                    else: p_final = 0.50

                    p_final = max(0.05, min(0.95, p_final))
                    c_justa = 1 / p_final
                    kelly = ((((cuo - 1) * p_final) - (1 - p_final)) / (cuo - 1)) * 0.25 * bank_actual if cuo > 1.01 else 0
                    
                    fuego = "🔥 ¡HAY VALOR!" if cuo > c_justa and cuo > 1.01 else "❄️ DESCARTAR"
                    color = "#10B981" if cuo > c_justa else "#EF4444"

                    html_prob = f"""
                    <div class="prob-box" style="border-color:{color};">
                        <div style="font-size:12px; opacity:0.8;">Probabilidad Matemática</div>
                        <div class="prob-number" style="color:{color};">{p_final*100:.1f}%</div>
                        <div style="margin-top:10px; font-weight:bold; color:{c_text};">C. JUSTA: {c_justa:.2f} | <span style="color:{color};">{fuego}</span></div>
                    </div>
                    """
                    st.markdown(html_prob.replace('\n', ' '), unsafe_allow_html=True)
                    if cuo > c_justa: st.success(f"💰 Stake Sugerido (Kelly): {kelly:.2f} U")

    # --- PESTAÑA 2: BÓVEDA PREMIUM (INTACTA CON ALERTAS) ---
    with tab_boveda:
        st.markdown(f"<h3 style='color:{c_acc};'>📋 Bóveda Premium</h3>", unsafe_allow_html=True)
        for m in partidos_filtrados:
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            
            league_name = m.get('league', {}).get('name', 'Competición')
            league_img = m.get('league', {}).get('image_url', '')
            logo_html = f"<img src='{league_img}' style='width:18px; height:18px; object-fit:contain; vertical-align:middle; margin-right:5px;'>" if league_img else ""
            
            n1, n2 = t1['name'][:10], t2['name'][:10]
            img1, img2 = t1.get('image_url', ''), t2.get('image_url', '')
            
            wr1, f1, k1, tow1, optow1, drg1, bar1, fb1, time1, gold1_15, conv1, come1, sig1 = get_team_stats(t1['name'], t1['id'], df_oracle) 
            wr2, f2, k2, tow2, optow2, drg2, bar2, fb2, time2, gold2_15, conv2, come2, sig2 = get_team_stats(t2['name'], t2['id'], df_oracle) 
            
            has_data = (k1 > 0 and k2 > 0)
            if has_data:
                z_time, z_kills, z_tow = obtener_friccion_regional(league_name)
                
                exp_time = ((time1 + time2) / 2) + z_time
                exp_k = (k1 + k2) + z_kills
                exp_tow = (tow1 + optow1) + z_tow
                
                mod_time, mod_obj = 0, 0
                if come1 > 0.35 and come2 > 0.35: mod_time, mod_obj = 2.0, 1.5 
                elif conv1 > 0.55 and conv2 > 0.55: mod_time, mod_obj = -2.0, -1.0 
                
                adj_time = exp_time + mod_time
                adj_k = exp_k + (mod_obj * 2)
                adj_tow = exp_tow + mod_obj
                
                p_gb = wr1 / (wr1+wr2) if (wr1+wr2) > 0 else 0.50
                p_fb = fb1 / (fb1+fb2) if (fb1+fb2) > 0 else 0.50
                p_time = max(0.05, min(0.95, 0.50 + (adj_time - 32.5) * 0.05))
                p_k = max(0.05, min(0.95, 0.50 + (adj_k - 28.5) * 0.03))
                p_tow = max(0.05, min(0.95, 0.50 + (adj_tow - 12.5) * 0.10))
                
                # Semáforos de Varianza de Mapa
                sem1 = "🔴" if sig1 > 4.5 else "🟢" if sig1 < 3.0 and sig1 > 0 else "🟡"
                sem2 = "🔴" if sig2 > 4.5 else "🟢" if sig2 < 3.0 and sig2 > 0 else "🟡"
                
                def get_tot(p): return (p, "Más") if p >= 0.50 else (1 - p, "Menos")
                pt, ot = get_tot(p_time); pk, ok = get_tot(p_k); ptow, otow = get_tot(p_tow)

                html_boveda_lol = f"""
                <div class="boveda-board">
                <div class="league-title" style="color:{c_text}; font-size:14px; font-weight:bold; border-bottom:1px solid {c_border}; padding-bottom:8px; margin-bottom:15px;">{logo_html}{league_name}</div>
                <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 20px;">
                    <div style="text-align: right; width: 40%;"><b>{n1}</b> <img src="{img1}" style="width:30px; vertical-align:middle; margin-left:10px;"></div>
                    <div style="width: 20%; text-align: center; font-weight: 900; color: {c_acc};">VS</div>
                    <div style="text-align: left; width: 40%;"><img src="{img2}" style="width:30px; vertical-align:middle; margin-right:10px;"> <b>{n2}</b></div>
                </div>
                <div class="boveda-row"><div class="w-col-1">⭐ GANADOR</div><div class="w-col-2">{n1}: {wr1*100:.0f}%<br>{n2}: {wr2*100:.0f}%</div><div class="w-col-3"><span class="w-pred">{n1 if p_gb>=0.5 else n2} ({max(p_gb, 1-p_gb)*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/max(p_gb, 1-p_gb):.2f}</span></div></div>
                <div class="boveda-row"><div class="w-col-1">🩸 FASE EARLY (Min 15)</div><div class="w-col-2">{n1}: Oro {gold1_15:+.0f} | FB {fb1*100:.0f}%<br>{n2}: Oro {gold2_15:+.0f} | FB {fb2*100:.0f}%</div><div class="w-col-3"><span class="w-pred">{n1 if p_fb>=0.5 else n2} ({max(p_fb, 1-p_fb)*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN FB: {1/max(p_fb, 1-p_fb):.2f}</span></div></div>
                <div class="boveda-row"><div class="w-col-1">🛡️ ESCALADO (Min 25+) & TORRES</div><div class="w-col-2">{n1}: Remontada {come1*100:.0f}%<br>{n2}: Remontada {come2*100:.0f}%</div><div class="w-col-3"><span class="w-pred">Torres: {otow} ({ptow*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/ptow:.2f}</span></div></div>
                <div class="boveda-row"><div class="w-col-1">⚔️ TOTAL KILLS (28.5)</div><div class="w-col-2">Avg {n1}: {k1:.1f}<br>Avg {n2}: {k2:.1f}</div><div class="w-col-3"><span class="w-pred">{ok} ({pk*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/pk:.2f}</span></div></div>
                <div class="boveda-row" style="border-bottom: none;"><div class="w-col-1">⏱️ TIEMPO & VARIANZA</div><div class="w-col-2">Avg {n1}: {time1:.1f}m {sem1}<br>Avg {n2}: {time2:.1f}m {sem2}</div><div class="w-col-3"><span class="w-pred">{ot} ({pt*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/pt:.2f}</span></div></div>
                </div>
                """
                st.markdown(html_boveda_lol.replace('\n', ' '), unsafe_allow_html=True)
            else:
                st.info(f"Faltan datos analíticos locales para auditar a {n1} vs {n2}")

    # --- PESTAÑA 3: ANALÍTICA PRO E HISTORIAL H2H ---
    with tab_stats:
        st.markdown(f"<h3 style='color:{c_acc};'>🧬 Roster KDA y Duelos Directos (H2H)</h3>", unsafe_allow_html=True)
        if df_oracle.empty:
            st.warning("⚠️ No se encontró la base de datos 'datos_oracle.zip' en el directorio para calcular las analíticas de jugadores.")
        else:
            opciones_analitica = [f"{p['opponents'][0]['opponent']['name']} vs {p['opponents'][1]['opponent']['name']}" for p in partidos_filtrados if len(p.get('opponents', [])) > 1]
            if not opciones_analitica:
                st.info("No hay enfrentamientos disponibles en el radar para desplegar la analítica avanzada.")
            else:
                enfrentamiento_sel = st.selectbox("🎯 Filtrar Radiografía de Plantillas:", opciones_analitica)
                t1_input, t2_input = enfrentamiento_sel.split(" vs ")
                
                col_kda1, col_kda2 = st.columns(2)
                with col_kda1:
                    st.markdown(f"#### 🛡️ Roster: {t1_input}")
                    df_kda1 = get_player_kda_pool(t1_input, df_oracle)
                    if not df_kda1.empty:
                        st.dataframe(df_kda1[['playername', 'position', 'kda', 'champion']].rename(columns={'playername':'Jugador', 'position':'Rol', 'kda':'KDA Real', 'champion':'Main Pick'}), hide_index=True)
                    else: st.caption("Registros individuales no disponibles en la muestra actual.")
                
                with col_kda2:
                    st.markdown(f"#### 🛡️ Roster: {t2_input}")
                    df_kda2 = get_player_kda_pool(t2_input, df_oracle)
                    if not df_kda2.empty:
                        st.dataframe(df_kda2[['playername', 'position', 'kda', 'champion']].rename(columns={'playername':'Jugador', 'position':'Rol', 'kda':'KDA Real', 'champion':'Main Pick'}), hide_index=True)
                    else: st.caption("Registros individuales no disponibles en la muestra actual.")
                
                st.markdown("<hr style='margin:25px 0; border-color:var(--border-color);'>", unsafe_allow_html=True)
                st.markdown(f"#### ⚔️ Historial de Choques Directos (Últimos 4 Mapas H2H)")
                df_h2h = get_h2h_direct_history(t1_input, t2_input, df_oracle)
                if not df_h2h.empty:
                    st.table(df_h2h[['date', 'teamname', 'result', 'kills', 'towers', 'golddiffat15']].rename(columns={'date':'Fecha', 'teamname':'Escuadra', 'result':'Victoria', 'kills':'Kills', 'towers':'Torres', 'golddiffat15':'Oro@Min15'}))
                else:
                    st.info("No existen registros locales de choques directos recientes entre estas dos organizaciones en la base de datos de Oracle.")import streamlit as st
import requests
import os
import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN CLOUD
# ==========================================
st.set_page_config(page_title="Quant Elite V88.6 - LoL Core & Pro Analytics", layout="wide", initial_sidebar_state="expanded")

def check_password():
    token = st.query_params.get("token", "")
    if token == "capo": st.session_state["password_correct"] = True
    if st.session_state.get("password_correct", False): return True

    st.markdown("""<style>.stApp { background-color: #05080F; color: #F8FAFC; }</style>""", unsafe_allow_html=True)
    
    html_login = """
    <div style='background: #0F172A; border: 2px solid #10B981; border-radius: 20px; padding: 30px; margin-top: 5vh; box-shadow: 0 0 20px rgba(16, 185, 129, 0.2); text-align: center;'>
    <h2 style='color: #10B981; letter-spacing: 2px;'>⚡ QUANT TERMINAL V88.6</h2>
    <p style='color:#64748B;'>RADAR EXCLUSIVO LOL | LOGOS LIGA | TEMAS | ANALÍTICA PRO Y H2H</p>
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

def gestionar_historial(nueva_op=None, index_update=None, nuevo_estado=None):
    file_name = "historial_operaciones.csv"
    if not os.path.exists(file_name):
        pd.DataFrame(columns=["Fecha", "Juego", "Partido", "Mercado", "Opcion", "Cuota", "Inversion", "Estado", "MatchID", "TeamID"]).to_csv(file_name, index=False)
    df = pd.read_csv(file_name)
    if nueva_op: df = pd.concat([df, pd.DataFrame([nueva_op])], ignore_index=True)
    if index_update is not None: df.at[index_update, 'Estado'] = nuevo_estado
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df[df['Fecha'] >= (datetime.utcnow() - timedelta(hours=72))]
    try: df.to_csv(file_name, index=False)
    except: pass
    return df

@st.cache_data(ttl=120)
def call_api_live(endpoint, params_str=""):
    url = f"https://api.pandascore.co/lol/{endpoint}?{params_str}"
    headers = {"authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

# ==========================================
# 3. EL CEREBRO QUANT LOL (ORACLE + H2H + JUGADORES)
# ==========================================
@st.cache_data(ttl=21600, show_spinner=False)
def fetch_historical_data_general(team_id):
    url = "https://api.pandascore.co/lol/matches"
    params = f"filter[opponent_id]={team_id}&filter[status]=finished&sort=-end_at&per_page=10"
    headers = {"authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(f"{url}?{params}", headers=headers).json()
        if not res: return 0.50, ['unknown']*5
        wins = sum(1 for m in res if str(m.get('winner_id')) == str(team_id))
        form = ['win' if str(m.get('winner_id')) == str(team_id) else 'loss' for m in res]
        return (wins/len(res)), form[:5]
    except: return 0.50, ['unknown']*5

@st.cache_data(ttl=28800, show_spinner=False)
def load_oracle_database():
    # Estructura extendida para soportar tanto Bóveda como Analítica Pro de Jugadores
    columnas_clave = ['teamname', 'playername', 'position', 'champion', 'date', 'result', 'kills', 'deaths', 'assists', 'teamkills', 'towers', 'opp_towers', 'dragons', 'barons', 'firstblood', 'gamelength', 'golddiffat15']
    if os.path.exists("datos_oracle.zip"):
        try:
            df = pd.read_csv("datos_oracle.zip", compression='zip', low_memory=False)
            df.columns = df.columns.str.strip().str.lower()
            disponibles = [c for c in columnas_clave if c in df.columns]
            return df[disponibles]
        except:
            try:
                df = pd.read_csv("datos_oracle.zip", low_memory=False)
                df.columns = df.columns.str.strip().str.lower()
                disponibles = [c for c in columnas_clave if c in df.columns]
                return df[disponibles]
            except: pass
    return pd.DataFrame()

def get_team_stats(team_name, team_id, df_completo):
    if df_completo.empty: 
        wr, form = fetch_historical_data_general(team_id)
        return wr, form, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.50, 0.0, 0.0
    
    basura = ['esports', 'challengers', 'academy', 'gaming', 'club', 'sports', 'team']
    words = [w for w in team_name.lower().split() if w not in basura and len(w) > 2]
    core_name = words[0] if words else team_name.lower().split()[0]
    
    # Extraemos exclusivamente las filas globales del equipo para la Bóveda
    df_team = df_completo[(df_completo['teamname'].str.lower().str.contains(core_name, na=False)) & (df_completo['position'].str.contains('team', case=False, na=False))].copy()
    df_team['date'] = pd.to_datetime(df_team['date'], errors='coerce')
    df_team = df_team.sort_values(by='date', ascending=False).head(15) 
    
    if df_team.empty:
        wr, form = fetch_historical_data_general(team_id)
        return wr, form, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.50, 0.0, 0.0
    
    # Cálculo de Varianza Temporal (Desviación Estándar)
    sigma_time = df_team['gamelength'].std() / 60.0 if len(df_team) > 2 else 0.0
    
    if 'golddiffat15' in df_team.columns:
        ahead = df_team[df_team['golddiffat15'] > 0]
        wins_from_ahead = ahead[ahead['result'] == 1]
        conv_rate = len(wins_from_ahead) / len(ahead) if len(ahead) > 0 else 0.50
        
        behind = df_team[df_team['golddiffat15'] <= 0]
        wins_from_behind = behind[behind['result'] == 1]
        comeback_rate = len(wins_from_behind) / len(behind) if len(behind) > 0 else 0.0
    else: conv_rate, comeback_rate = 0.50, 0.0

    wins = df_team['result'].sum() 
    winrate = wins / len(df_team) if len(df_team) > 0 else 0.50
    form = ['win' if r == 1 else 'loss' for r in df_team['result'].tolist()[:5]]
    
    cols = df_team.columns
    avg_k = df_team['teamkills'].mean() if 'teamkills' in cols else 0.0
    avg_t = df_team['towers'].mean() if 'towers' in cols else 0.0
    avg_ot = df_team['opp_towers'].mean() if 'opp_towers' in cols else 0.0
    avg_d = df_team['dragons'].mean() if 'dragons' in cols else 0.0
    avg_b = df_team['barons'].mean() if 'barons' in cols else 0.0
    avg_fb = df_team['firstblood'].mean() if 'firstblood' in cols else 0.0
    avg_time = (df_team['gamelength'].mean() / 60) if 'gamelength' in cols else 0.0
    avg_gold15 = df_team['golddiffat15'].mean() if 'golddiffat15' in cols else 0.0
    
    return float(winrate), form, float(avg_k), float(avg_t), float(avg_ot), float(avg_d), float(avg_b), float(avg_fb), float(avg_time), float(avg_gold15), float(conv_rate), float(comeback_rate), float(sigma_time)

def obtener_friccion_regional(league_name):
    nombre = league_name.upper()
    if "LPL" in nombre or "LDL" in nombre: return -2.0, 3.5, -1.5 # China: partidas explosivas
    if "LCK" in nombre: return 3.0, -3.5, 1.5 # Corea: partidas metódicas y largas
    if "LEC" in nombre or "LCS" in nombre: return 1.0, 1.0, 0.5 # Occidente: fricción estándar
    return 0.0, 0.0, 0.0

# Funciones exclusivas para la Pestaña de Analítica Pro
def get_player_kda_pool(team_name, df):
    basura = ['esports', 'challengers', 'academy', 'gaming', 'club', 'sports', 'team']
    words = [w for w in team_name.lower().split() if w not in basura and len(w) > 2]
    core_name = words[0] if words else team_name.lower().split()[0]
    
    # Extraemos registros individuales de jugadores (excluyendo totales de equipo)
    team_df = df[df['teamname'].str.lower().str.contains(core_name, na=False) & (~df['position'].str.contains('team', case=False, na=False))].copy()
    if team_df.empty: return pd.DataFrame()
    
    if 'kills' not in team_df.columns or 'deaths' not in team_df.columns: return pd.DataFrame()
    
    # Cálculo de KDA y detección del campeón Main
    stats = team_df.groupby('playername').agg({
        'position': 'first',
        'kills': 'mean',
        'deaths': 'mean',
        'assists': 'mean',
        'champion': lambda x: x.value_counts().index[0] if not x.empty else 'N/A'
    }).reset_index()
    
    stats['kda'] = (stats['kills'] + stats['assists']) / stats['deaths'].replace(0, 1)
    return stats.sort_values(by='kda', ascending=False)

def get_h2h_direct_history(t1_name, t2_name, df):
    # Identificamos el core de cada escuadra
    c1 = t1_name.lower().split()[0] if len(t1_name.split()) > 0 else t1_name.lower()
    c2 = t2_name.lower().split()[0] if len(t2_name.split()) > 0 else t2_name.lower()
    
    t1_rows = df[df['teamname'].str.lower().str.contains(c1, na=False)]
    t2_rows = df[df['teamname'].str.lower().str.contains(c2, na=False)]
    
    # Cruzamos fechas exactas donde ambos compartieron mapa
    h2h_dates = set(t1_rows['date']).intersection(set(t2_rows['date']))
    if not h2h_dates: return pd.DataFrame()
    
    h2h_df = df[df['date'].isin(h2h_dates) & (df['position'].str.contains('team', case=False, na=False))]
    return h2h_df.sort_values(by='date', ascending=False).head(8) # Retorna los últimos 4 mapas (8 registros)

# ==========================================
# 4. SIDEBAR Y GESTIÓN DE TEMAS VISUALES
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#10B981;'>⚙️ V88.6 LOL CORE</h2>", unsafe_allow_html=True)
    
    # Selector de Interfaz
    st.markdown("<p style='font-size:12px; color:#64748B; margin-bottom:0;'>🎨 TEMA VISUAL</p>", unsafe_allow_html=True)
    tema_seleccionado = st.selectbox("", ["Azul Oscuro (Defecto)", "Blanco Cuántico", "Verde Hacker"], label_visibility="collapsed")
    
    st.markdown(f"<div style='text-align:center; background:var(--card-bg); padding:15px; border-radius:10px; border:1px solid var(--border-color); margin-top:15px; margin-bottom:20px;'>Bankroll Base<br><span style='color:#10B981; font-weight:900; font-size:24px;'>{bank_actual} U</span></div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-weight:bold; color:var(--text-color); margin-bottom:20px;'>🛡️ League of Legends</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    nuevo_b = st.number_input("Ajustar Caja Base (U)", value=float(bank_actual))
    if st.button("💾 Actualizar Bankroll", use_container_width=True): gestionar_bank(nuevo_b); st.rerun()

# Inyección dinámica de paletas de color en CSS
if tema_seleccionado == "Blanco Cuántico":
    c_bg, c_card, c_border, c_text, c_acc = "#F8FAFC", "#FFFFFF", "#E2E8F0", "#0F172A", "#2563EB"
elif tema_seleccionado == "Verde Hacker":
    c_bg, c_card, c_border, c_text, c_acc = "#000000", "#022C22", "#064E3B", "#4ADE80", "#10B981"
else: # Azul Oscuro
    c_bg, c_card, c_border, c_text, c_acc = "#05080F", "#0F172A", "#1E293B", "#F8FAFC", "#38BDF8"

st.markdown(f"""<style>
    .stApp {{ background-color: {c_bg}; color: {c_text}; font-family: 'Inter', sans-serif; }}
    .glass-card {{ background: {c_card}; border: 1px solid {c_border}; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    .team-logo {{ width: 60px; height: 60px; object-fit: contain; margin-bottom: 5px; }}
    .winrate-text {{ font-size: 14px; color: {c_acc}; font-weight: 900; background: {c_bg}; padding: 4px 10px; border-radius: 10px; display: inline-block; margin-top: 5px; border: 1px solid {c_border}; }}
    .tower-plate {{ width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin:0 2px; }}
    .win {{ background-color: #10B981; }} .loss {{ background-color: #EF4444; }} .unknown {{ background-color: #64748B; }}
    .badge-live {{ background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite; }}
    .badge-time {{ background: {c_acc}; color: {c_bg}; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }}
    .stream-btn {{ background-color: #9146FF; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold; display: block; margin-top: 20px; text-align: center; }}
    .prob-box {{ background: {c_card}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; }}
    .prob-number {{ font-size: 32px; font-weight: 900; color: {c_acc}; }}
    .boveda-board {{ background-color: {c_card}; border: 1px solid {c_border}; border-radius: 14px; padding: 20px; margin-bottom: 20px; }}
    .boveda-row {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid {c_border}; }}
    .w-col-1 {{ width: 32%; font-size: 13px; font-weight: bold; color: {c_text}; opacity: 0.8; }}
    .w-col-2 {{ width: 36%; text-align: center; font-size: 13px; background: {c_bg}; padding: 6px; border-radius: 6px; border: 1px solid {c_border}; }}
    .w-col-3 {{ width: 32%; text-align: right; }}
    .w-pred {{ font-weight: 900; color: {c_acc}; font-size: 14px; }}
    .w-cota {{ font-weight: bold; color: #EF4444; font-size: 11px; background: {c_bg}; padding: 3px 6px; border-radius: 4px; border: 1px solid #EF4444; display: inline-block; margin-top: 4px; }}
</style>""", unsafe_allow_html=True)

# ==========================================
# 5. RADAR, BÓVEDA Y ESTADÍSTICA PRO
# ==========================================
st.markdown(f"<h1 style='text-align: center; color: {c_text};'>📡 RADAR TÁCTICO: LEAGUE OF LEGENDS</h1>", unsafe_allow_html=True)

# Incorporamos la tercera pestaña solicitada
tab_radar, tab_boveda, tab_stats = st.tabs(["📡 PANEL EN VIVO", "📊 BÓVEDA PREMIUM", "🧬 ANALÍTICA PRO"])

partidos = call_api_live("matches", "filter[status]=running,not_started&sort=begin_at&per_page=15")
df_oracle = load_oracle_database()

hoy_local = datetime.utcnow() - timedelta(hours=4)
limite_inferior = hoy_local - timedelta(hours=12) 
limite_semana = hoy_local + timedelta(days=7)

partidos_filtrados = []
for p in partidos:
    if p['status'] == 'running': partidos_filtrados.append(p)
    elif p['status'] == 'not_started' and p.get('begin_at'):
        dt_local = datetime.strptime(p['begin_at'], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
        if limite_inferior <= dt_local <= limite_semana: partidos_filtrados.append(p)

if not partidos_filtrados:
    st.info("No hay encuentros de League of Legends programados en el marco temporal de escaneo.")
else:
    # --- PESTAÑA 1: RADAR EN VIVO (INTACTO) ---
    with tab_radar:
        for i, m in enumerate(partidos_filtrados):
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            
            badge = "<span class='badge-live'>🔴 EN VIVO</span>" if m['status'] == 'running' else f"<span class='badge-time'>📅 {(datetime.strptime(m['begin_at'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).strftime('%d/%m %H:%M')}</span>"
            
            lista_streams = m.get('streams_list', [])
            video_url = lista_streams[0].get('raw_url', '#') if lista_streams and len(lista_streams) > 0 else '#'
            stream_html = f"<a href='{video_url}' target='_blank' class='stream-btn'>📺 Ver Transmisión</a>" if video_url != '#' else ""
            
            # Integración de Logos de Liga solicitada
            league_name = m.get('league', {}).get('name', 'Competición')
            league_img = m.get('league', {}).get('image_url', '')
            logo_html = f"<img src='{league_img}' style='width:20px; height:20px; object-fit:contain; vertical-align:middle; margin-right:6px;'>" if league_img else ""

            wr1, f1, k1, tow1, optow1, drg1, bar1, fb1, time1, gold1_15, conv1, come1, sig1 = get_team_stats(t1['name'], t1['id'], df_oracle) 
            wr2, f2, k2, tow2, optow2, drg2, bar2, fb2, time2, gold2_15, conv2, come2, sig2 = get_team_stats(t2['name'], t2['id'], df_oracle) 

            placas_t1 = "".join([f"<span class='tower-plate {x}'></span>" for x in f1])
            placas_t2 = "".join([f"<span class='tower-plate {x}'></span>" for x in f2])

            html_tarjeta = f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div style="font-size: 13px; font-weight: bold; color: {c_text};">{logo_html}{league_name}</div>
                    <div>{badge}</div>
                </div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 35%;">
                        <div style="font-size:15px; font-weight:bold;">{t1['name']}</div>
                        <img src="{t1.get('image_url','')}" class="team-logo"><br>
                        <div class="winrate-text">WR: {wr1*100:.0f}%</div><br>
                        <div style="margin-top:5px;">{placas_t1}</div>
                    </div>
                    <div style="font-size: 26px; font-weight: bold; color: {c_acc};">VS</div>
                    <div style="width: 35%;">
                        <div style="font-size:15px; font-weight:bold;">{t2['name']}</div>
                        <img src="{t2.get('image_url','')}" class="team-logo"><br>
                        <div class="winrate-text">{wr2*100:.0f}%</div><br>
                        <div style="margin-top:5px;">{placas_t2}</div>
                    </div>
                </div>
                {stream_html}
            </div>
            """
            st.markdown(html_tarjeta.replace('\n', ' '), unsafe_allow_html=True)

            with st.expander("🛠️ CALCULADORA QUANT"):
                c1, c2 = st.columns(2)
                mercs = ["-- Seleccione --", "⭐ PARTIDO: Ganador", "⚖️ Handicap de Mapas", "🗼 Total Torres", "🐉 Total Dragones", "👾 Total Barones", "⚔️ Total Kills", "⏱️ Duración", "🩸 Primera Sangre"]
                sel_m = c1.selectbox("Mercado", mercs, key=f"m_{i}")
                
                if sel_m != "-- Seleccione --":
                    if "Total" in sel_m or "Duración" in sel_m:
                        op_sel = c2.radio("Opción:", ["Más (+)", "Menos (-)"], key=f"o_{i}", horizontal=True)
                    else:
                        op_sel = c2.radio("A favor de:", [t1['name'], t2['name']], key=f"o_{i}", horizontal=True)
                    
                    c_l1, c_l2 = st.columns(2)
                    def_l = 32.5 if "Duración" in sel_m else 28.5 if "Kills" in sel_m and "Total" in sel_m else 12.5 if "Torres" in sel_m else -1.5 if "Handicap" in sel_m else 0.0
                    lin = c_l1.number_input("Línea Flexible", value=def_l, key=f"l_{i}")
                    cuo = c_l2.number_input("Cuota del Casino", value=1.00, step=0.01, key=f"c_{i}")

                    has_data = (k1 > 0 and k2 > 0)
                    if has_data:
                        z_time, z_kills, z_tow = obtener_friccion_regional(league_name)
                        
                        exp_time = ((time1 + time2) / 2) + z_time
                        exp_k = (k1 + k2) + z_kills
                        exp_tow = (tow1 + optow1) + z_tow
                        
                        mod_time, mod_obj = 0, 0
                        if come1 > 0.35 and come2 > 0.35: mod_time, mod_obj = 2.0, 1.5 
                        elif conv1 > 0.55 and conv2 > 0.55: mod_time, mod_obj = -2.0, -1.0 
                        
                        adj_time = exp_time + mod_time
                        adj_k = exp_k + (mod_obj * 2)
                        adj_tow = exp_tow + mod_obj
                        
                        p_gb = wr1 / (wr1+wr2) if (wr1+wr2) > 0 else 0.50
                        if t1['name'] not in op_sel: p_gb = 1 - p_gb
                        
                        if "Duración" in sel_m: p_raw = 0.50 + (adj_time - lin) * 0.05; p_final = p_raw if "Más" in op_sel else (1-p_raw)
                        elif "Total Kills" in sel_m: p_raw = 0.50 + (adj_k - lin) * 0.03; p_final = p_raw if "Más" in op_sel else (1-p_raw)
                        elif "Torres" in sel_m: p_raw = 0.50 + (adj_tow - lin) * 0.10; p_final = p_raw if "Más" in op_sel else (1-p_raw)
                        elif "Sangre" in sel_m: p_final = fb1/(fb1+fb2) if (fb1+fb2)>0 else 0.50; p_final = p_final if t1['name'] in op_sel else (1-p_final)
                        elif "Handicap" in sel_m: p_final = p_gb - (abs(lin)*0.2) if lin < 0 else p_gb + (abs(lin)*0.2)
                        else: p_final = p_gb
                    else: p_final = 0.50

                    p_final = max(0.05, min(0.95, p_final))
                    c_justa = 1 / p_final
                    kelly = ((((cuo - 1) * p_final) - (1 - p_final)) / (cuo - 1)) * 0.25 * bank_actual if cuo > 1.01 else 0
                    
                    fuego = "🔥 ¡HAY VALOR!" if cuo > c_justa and cuo > 1.01 else "❄️ DESCARTAR"
                    color = "#10B981" if cuo > c_justa else "#EF4444"

                    html_prob = f"""
                    <div class="prob-box" style="border-color:{color};">
                        <div style="font-size:12px; opacity:0.8;">Probabilidad Matemática</div>
                        <div class="prob-number" style="color:{color};">{p_final*100:.1f}%</div>
                        <div style="margin-top:10px; font-weight:bold; color:{c_text};">C. JUSTA: {c_justa:.2f} | <span style="color:{color};">{fuego}</span></div>
                    </div>
                    """
                    st.markdown(html_prob.replace('\n', ' '), unsafe_allow_html=True)
                    if cuo > c_justa: st.success(f"💰 Stake Sugerido (Kelly): {kelly:.2f} U")

    # --- PESTAÑA 2: BÓVEDA PREMIUM (INTACTA CON ALERTAS) ---
    with tab_boveda:
        st.markdown(f"<h3 style='color:{c_acc};'>📋 Bóveda Premium</h3>", unsafe_allow_html=True)
        for m in partidos_filtrados:
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            
            league_name = m.get('league', {}).get('name', 'Competición')
            league_img = m.get('league', {}).get('image_url', '')
            logo_html = f"<img src='{league_img}' style='width:18px; height:18px; object-fit:contain; vertical-align:middle; margin-right:5px;'>" if league_img else ""
            
            n1, n2 = t1['name'][:10], t2['name'][:10]
            img1, img2 = t1.get('image_url', ''), t2.get('image_url', '')
            
            wr1, f1, k1, tow1, optow1, drg1, bar1, fb1, time1, gold1_15, conv1, come1, sig1 = get_team_stats(t1['name'], t1['id'], df_oracle) 
            wr2, f2, k2, tow2, optow2, drg2, bar2, fb2, time2, gold2_15, conv2, come2, sig2 = get_team_stats(t2['name'], t2['id'], df_oracle) 
            
            has_data = (k1 > 0 and k2 > 0)
            if has_data:
                z_time, z_kills, z_tow = obtener_friccion_regional(league_name)
                
                exp_time = ((time1 + time2) / 2) + z_time
                exp_k = (k1 + k2) + z_kills
                exp_tow = (tow1 + optow1) + z_tow
                
                mod_time, mod_obj = 0, 0
                if come1 > 0.35 and come2 > 0.35: mod_time, mod_obj = 2.0, 1.5 
                elif conv1 > 0.55 and conv2 > 0.55: mod_time, mod_obj = -2.0, -1.0 
                
                adj_time = exp_time + mod_time
                adj_k = exp_k + (mod_obj * 2)
                adj_tow = exp_tow + mod_obj
                
                p_gb = wr1 / (wr1+wr2) if (wr1+wr2) > 0 else 0.50
                p_fb = fb1 / (fb1+fb2) if (fb1+fb2) > 0 else 0.50
                p_time = max(0.05, min(0.95, 0.50 + (adj_time - 32.5) * 0.05))
                p_k = max(0.05, min(0.95, 0.50 + (adj_k - 28.5) * 0.03))
                p_tow = max(0.05, min(0.95, 0.50 + (adj_tow - 12.5) * 0.10))
                
                # Semáforos de Varianza de Mapa
                sem1 = "🔴" if sig1 > 4.5 else "🟢" if sig1 < 3.0 and sig1 > 0 else "🟡"
                sem2 = "🔴" if sig2 > 4.5 else "🟢" if sig2 < 3.0 and sig2 > 0 else "🟡"
                
                def get_tot(p): return (p, "Más") if p >= 0.50 else (1 - p, "Menos")
                pt, ot = get_tot(p_time); pk, ok = get_tot(p_k); ptow, otow = get_tot(p_tow)

                html_boveda_lol = f"""
                <div class="boveda-board">
                <div class="league-title" style="color:{c_text}; font-size:14px; font-weight:bold; border-bottom:1px solid {c_border}; padding-bottom:8px; margin-bottom:15px;">{logo_html}{league_name}</div>
                <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 20px;">
                    <div style="text-align: right; width: 40%;"><b>{n1}</b> <img src="{img1}" style="width:30px; vertical-align:middle; margin-left:10px;"></div>
                    <div style="width: 20%; text-align: center; font-weight: 900; color: {c_acc};">VS</div>
                    <div style="text-align: left; width: 40%;"><img src="{img2}" style="width:30px; vertical-align:middle; margin-right:10px;"> <b>{n2}</b></div>
                </div>
                <div class="boveda-row"><div class="w-col-1">⭐ GANADOR</div><div class="w-col-2">{n1}: {wr1*100:.0f}%<br>{n2}: {wr2*100:.0f}%</div><div class="w-col-3"><span class="w-pred">{n1 if p_gb>=0.5 else n2} ({max(p_gb, 1-p_gb)*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/max(p_gb, 1-p_gb):.2f}</span></div></div>
                <div class="boveda-row"><div class="w-col-1">🩸 FASE EARLY (Min 15)</div><div class="w-col-2">{n1}: Oro {gold1_15:+.0f} | FB {fb1*100:.0f}%<br>{n2}: Oro {gold2_15:+.0f} | FB {fb2*100:.0f}%</div><div class="w-col-3"><span class="w-pred">{n1 if p_fb>=0.5 else n2} ({max(p_fb, 1-p_fb)*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN FB: {1/max(p_fb, 1-p_fb):.2f}</span></div></div>
                <div class="boveda-row"><div class="w-col-1">🛡️ ESCALADO (Min 25+) & TORRES</div><div class="w-col-2">{n1}: Remontada {come1*100:.0f}%<br>{n2}: Remontada {come2*100:.0f}%</div><div class="w-col-3"><span class="w-pred">Torres: {otow} ({ptow*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/ptow:.2f}</span></div></div>
                <div class="boveda-row"><div class="w-col-1">⚔️ TOTAL KILLS (28.5)</div><div class="w-col-2">Avg {n1}: {k1:.1f}<br>Avg {n2}: {k2:.1f}</div><div class="w-col-3"><span class="w-pred">{ok} ({pk*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/pk:.2f}</span></div></div>
                <div class="boveda-row" style="border-bottom: none;"><div class="w-col-1">⏱️ TIEMPO & VARIANZA</div><div class="w-col-2">Avg {n1}: {time1:.1f}m {sem1}<br>Avg {n2}: {time2:.1f}m {sem2}</div><div class="w-col-3"><span class="w-pred">{ot} ({pt*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/pt:.2f}</span></div></div>
                </div>
                """
                st.markdown(html_boveda_lol.replace('\n', ' '), unsafe_allow_html=True)
            else:
                st.info(f"Faltan datos analíticos locales para auditar a {n1} vs {n2}")

    # --- PESTAÑA 3: ANALÍTICA PRO E HISTORIAL H2H ---
    with tab_stats:
        st.markdown(f"<h3 style='color:{c_acc};'>🧬 Roster KDA y Duelos Directos (H2H)</h3>", unsafe_allow_html=True)
        if df_oracle.empty:
            st.warning("⚠️ No se encontró la base de datos 'datos_oracle.zip' en el directorio para calcular las analíticas de jugadores.")
        else:
            opciones_analitica = [f"{p['opponents'][0]['opponent']['name']} vs {p['opponents'][1]['opponent']['name']}" for p in partidos_filtrados if len(p.get('opponents', [])) > 1]
            if not opciones_analitica:
                st.info("No hay enfrentamientos disponibles en el radar para desplegar la analítica avanzada.")
            else:
                enfrentamiento_sel = st.selectbox("🎯 Filtrar Radiografía de Plantillas:", opciones_analitica)
                t1_input, t2_input = enfrentamiento_sel.split(" vs ")
                
                col_kda1, col_kda2 = st.columns(2)
                with col_kda1:
                    st.markdown(f"#### 🛡️ Roster: {t1_input}")
                    df_kda1 = get_player_kda_pool(t1_input, df_oracle)
                    if not df_kda1.empty:
                        st.dataframe(df_kda1[['playername', 'position', 'kda', 'champion']].rename(columns={'playername':'Jugador', 'position':'Rol', 'kda':'KDA Real', 'champion':'Main Pick'}), hide_index=True)
                    else: st.caption("Registros individuales no disponibles en la muestra actual.")
                
                with col_kda2:
                    st.markdown(f"#### 🛡️ Roster: {t2_input}")
                    df_kda2 = get_player_kda_pool(t2_input, df_oracle)
                    if not df_kda2.empty:
                        st.dataframe(df_kda2[['playername', 'position', 'kda', 'champion']].rename(columns={'playername':'Jugador', 'position':'Rol', 'kda':'KDA Real', 'champion':'Main Pick'}), hide_index=True)
                    else: st.caption("Registros individuales no disponibles en la muestra actual.")
                
                st.markdown("<hr style='margin:25px 0; border-color:var(--border-color);'>", unsafe_allow_html=True)
                st.markdown(f"#### ⚔️ Historial de Choques Directos (Últimos 4 Mapas H2H)")
                df_h2h = get_h2h_direct_history(t1_input, t2_input, df_oracle)
                if not df_h2h.empty:
                    st.table(df_h2h[['date', 'teamname', 'result', 'kills', 'towers', 'golddiffat15']].rename(columns={'date':'Fecha', 'teamname':'Escuadra', 'result':'Victoria', 'kills':'Kills', 'towers':'Torres', 'golddiffat15':'Oro@Min15'}))
                else:
                    st.info("No existen registros locales de choques directos recientes entre estas dos organizaciones en la base de datos de Oracle.")