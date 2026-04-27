import streamlit as st
import requests
import os
import math
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Quant Elite V57.0", layout="centered", initial_sidebar_state="expanded")

def check_password():
    token = st.query_params.get("token", "")
    if token == "capo": st.session_state["password_correct"] = True
    if st.session_state.get("password_correct", False): return True

    st.markdown("""
    <style>
    .stApp { background-color: #05080F; color: #F8FAFC; }
    .login-box { background: #0F172A; border: 2px solid #10B981; border-radius: 20px; padding: 30px; margin-top: 5vh; box-shadow: 0 0 20px rgba(16, 185, 129, 0.2); }
    .login-title { color: #10B981; font-size: 26px; font-weight: 900; letter-spacing: 2px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<div class='login-title'>⚡ QUANT TERMINAL V57.0</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B; margin-bottom:20px; text-align: center;'>UI PURA | BUG BLANCO FULMINADO | CARRERAS EN BÓVEDA</p>", unsafe_allow_html=True)
    with st.form("login_form"):
        u = st.text_input("Operador")
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("AUTENTICAR"):
            if u == st.secrets.get("usuario", "") and p == st.secrets.get("password", ""):
                st.session_state["password_correct"] = True
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    return False

if not check_password(): st.stop()

# ==========================================
# 2. FINANZAS Y GESTIÓN DE DATOS (MANUAL)
# ==========================================
API_KEY = "F163TaN2efiwM8Ejb3xj0FWaeFAWzQgjbW8bPcuQwi9-ct_ZD4g"

def gestionar_bank(monto=None):
    if not os.path.exists("bank.txt"):
        with open("bank.txt", "w") as f: f.write("100.0")
    if monto is not None:
        with open("bank.txt", "w") as f: f.write(str(round(monto, 2)))
    with open("bank.txt", "r") as f: return float(f.read())

bank_actual = gestionar_bank()

def gestionar_historial(nueva_op=None, index_update=None, nuevo_estado=None):
    file_name = "historial_operaciones.csv"
    if not os.path.exists(file_name):
        pd.DataFrame(columns=["Fecha", "Juego", "Partido", "Mercado", "Opcion", "Cuota", "Inversion", "Estado", "MatchID", "TeamID"]).to_csv(file_name, index=False)
    df = pd.read_csv(file_name)
    if nueva_op: df = pd.concat([df, pd.DataFrame([nueva_op])], ignore_index=True)
    if index_update is not None:
        df.at[index_update, 'Estado'] = nuevo_estado
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df[df['Fecha'] >= (datetime.utcnow() - timedelta(hours=72))]
    df.to_csv(file_name, index=False)
    return df

@st.cache_data(ttl=120)
def call_api_live(game_slug, endpoint, params_str=""):
    url = f"https://api.pandascore.co/{game_slug}/{endpoint}?{params_str}"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

# ==========================================
# 3. EL CEREBRO QUANT (24 MAPAS, SIN MVP)
# ==========================================
@st.cache_data(ttl=21600, show_spinner=False)
def fetch_historical_data_general(game_slug, team_id):
    url = f"https://api.pandascore.co/{game_slug}/matches"
    params = f"filter[opponent_id]={team_id}&filter[status]=finished&sort=-end_at&per_page=10"
    headers = {"authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(f"{url}?{params}", headers=headers).json()
        if not res: return 0.50, ['unknown']*5
        wins = sum(1 for m in res if str(m.get('winner_id')) == str(team_id))
        form = ['win' if str(m.get('winner_id')) == str(team_id) else 'loss' for m in res]
        return (wins/len(res)), form[:5]
    except: return 0.50, ['unknown']*5

def get_fallback_stats(team_id):
    wr, form = fetch_historical_data_general("lol", team_id)
    return wr, form, 0, 0, 0, 0, 0, 0, 0, {}

@st.cache_data(ttl=28800, show_spinner=False)
def load_oracle_database():
    columnas_clave = ['teamname', 'position', 'date', 'result', 'teamkills', 'towers', 'opp_towers', 'dragons', 'barons', 'firstblood', 'gamelength', 'playername']
    
    if os.path.exists("datos_oracle.zip"):
        try:
            df = pd.read_csv("datos_oracle.zip", compression='zip', usecols=lambda c: c.strip().lower() in columnas_clave, low_memory=False)
            df.columns = df.columns.str.strip().str.lower()
            return df, "OK (Leído desde ZIP Local)"
        except:
            try:
                df = pd.read_csv("datos_oracle.zip", usecols=lambda c: c.strip().lower() in columnas_clave, low_memory=False)
                df.columns = df.columns.str.strip().str.lower()
                return df, "OK (Leído desde ZIP como CSV)"
            except: pass

    if os.path.exists("datos_oracle.csv"):
        try:
            df = pd.read_csv("datos_oracle.csv", usecols=lambda c: c.strip().lower() in columnas_clave, low_memory=False)
            df.columns = df.columns.str.strip().str.lower()
            return df, "OK (Leído desde CSV Local)"
        except: pass

    try:
        url_aws = f"https://oracleselixir-downloadable-match-data.s3-us-west-2.amazonaws.com/{datetime.utcnow().year}_LoL_esports_match_data_from_OraclesElixir.csv"
        df = pd.read_csv(url_aws, usecols=lambda c: c.strip().lower() in columnas_clave, low_memory=False)
        df.columns = df.columns.str.strip().str.lower()
        return df, "OK (Descarga de Emergencia AWS)"
    except Exception as e:
        return pd.DataFrame(), f"Error Fatal: No se encontró el archivo. {e}"

def get_team_stats(team_name, team_id, df_completo):
    if df_completo.empty: return get_fallback_stats(team_id)
    
    basura = ['esports', 'challengers', 'academy', 'gaming', 'club', 'sports', 'youth', 'team', 'hanjin', 'dplus', 'oksavebank']
    words = [w for w in team_name.lower().split() if w not in basura and len(w) > 2]
    core_name = words[0] if words else team_name.lower().split()[0]
    
    df_all_team = df_completo[df_completo['teamname'].str.lower().str.contains(core_name, na=False)]
    if df_all_team.empty: return get_fallback_stats(team_id)

    # 24 MAPAS EQUIPO
    df_team = df_all_team[df_all_team['position'] == 'team']
    df_team['date'] = pd.to_datetime(df_team['date'], errors='coerce')
    df_team = df_team.sort_values(by='date', ascending=False).head(24) 
    
    if df_team.empty: return get_fallback_stats(team_id)
    
    # WINRATE INDIVIDUAL (CARRERAS KILLS)
    df_players = df_all_team[df_all_team['position'] != 'team']
    df_players['date'] = pd.to_datetime(df_players['date'], errors='coerce')
    df_players = df_players.sort_values(by='date', ascending=False).head(120) 
    
    roster = {}
    if not df_players.empty:
        for pos in ['top', 'jng', 'mid', 'bot', 'sup']:
            df_pos = df_players[df_players['position'] == pos]
            if not df_pos.empty:
                p_name = df_pos['playername'].mode()[0] if 'playername' in df_pos.columns and not df_pos['playername'].empty else "Unknown"
                p_wr = df_pos[df_pos['playername'] == p_name]['result'].mean() if p_name != "Unknown" else 0.0
                roster[pos] = (p_name, p_wr)
            else:
                roster[pos] = ("S/D", 0.0)

    wins = df_team['result'].sum() 
    winrate = wins / len(df_team) if len(df_team) > 0 else 0.50
    form = ['win' if r == 1 else 'loss' for r in df_team['result'].tolist()[:5]]
    
    cols = df_team.columns
    avg_kills = df_team['teamkills'].mean() if 'teamkills' in cols else 0
    avg_towers = df_team['towers'].mean() if 'towers' in cols else 0
    avg_opp_towers = df_team['opp_towers'].mean() if 'opp_towers' in cols else 0
    avg_dragons = df_team['dragons'].mean() if 'dragons' in cols else 0
    avg_barons = df_team['barons'].mean() if 'barons' in cols else 0
    avg_fb = df_team['firstblood'].mean() if 'firstblood' in cols else 0
    avg_time = (df_team['gamelength'].mean() / 60) if 'gamelength' in cols else 0
    
    return winrate, form, avg_kills, avg_towers, avg_opp_towers, avg_dragons, avg_barons, avg_fb, avg_time, roster

def motor_moba(wr1, wr2, mercado, opcion, linea, t1_name):
    total_wr = wr1 + wr2 if (wr1+wr2)>0 else 1
    prob = wr1/total_wr if t1_name in opcion else wr2/total_wr
    if "Total" in mercado or "Duración" in mercado or "Tiempo" in mercado or "Ambos" in mercado:
        mom = (wr1 + wr2) / 2
        prob = 0.50 + (mom - 0.50) * 0.3 if "Más" in opcion or "SÍ" in opcion else 0.50 - (mom - 0.50) * 0.3
    elif "Primer" in mercado or "Primera" in mercado:
        prob = 0.50 + (( (wr1/total_wr if t1_name in opcion else wr2/total_wr) - 0.50) * 0.7)
    elif "Carrera" in mercado:
        var = 0.60 if "5" in mercado else 0.75 if "10" in mercado else 0.85
        prob = 0.50 + (( (wr1/total_wr if t1_name in opcion else wr2/total_wr) - 0.50) * var)
    return max(0.05, min(0.95, prob))

def motor_fps(wr1, wr2, mercado, opcion, linea, t1_name):
    total_wr = wr1 + wr2 if (wr1 + wr2) > 0 else 1
    prob = wr1/total_wr if opcion == t1_name else wr2/total_wr
    if "Handicap" in mercado: prob = prob - (abs(linea)*0.15) if linea < 0 else prob + (abs(linea)*0.15)
    elif "Total" in mercado: prob = 0.5 + ((wr1+wr2)/2 - 0.5)*0.4 if "Más" in opcion else 0.5 - ((wr1+wr2)/2 - 0.5)*0.4
    return max(0.05, min(0.95, prob))

# ==========================================
# 4. TEMAS Y CSS 
# ==========================================
st.sidebar.markdown("### 🎨 Apariencia")
tema = st.sidebar.selectbox("", ["Azul Oscuro (Defecto)", "Verde Hacker", "Rojo Táctico", "Blanco Cuántico"])

colors = {
    "Azul Oscuro (Defecto)": ("#0B1120", "#1E293B", "#F1F5F9", "#38BDF8", "#334155", "#0F172A", "#94A3B8"),
    "Verde Hacker": ("#000000", "#051A05", "#4ADE80", "#10B981", "#064E3B", "#022C22", "#4ADE80"),
    "Rojo Táctico": ("#0A0000", "#1A0505", "#FECACA", "#EF4444", "#7F1D1D", "#450A0A", "#FECACA"),
    "Blanco Cuántico": ("#F1F5F9", "#FFFFFF", "#0F172A", "#2563EB", "#CBD5E1", "#F8FAFC", "#64748B")
}
c_bg, c_card, c_text, c_acc, c_border, c_btn, c_sub = colors[tema]

st.markdown(f"""
    <style>
    .stApp {{ background-color: {c_bg}; color: {c_text}; font-family: 'Inter', sans-serif; transition: background-color 0.3s; }}
    [data-testid="stSidebar"] {{ background-color: {c_card} !important; border-right: 1px solid {c_border}; transition: background-color 0.3s; }}
    .glass-card {{ background: {c_card}; border: 1px solid {c_border}; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); position: relative; transition: 0.3s; }}
    .team-logo {{ width: 70px; height: 70px; object-fit: contain; margin-bottom: 5px; }}
    .winrate-text {{ font-size: 14px; color: {c_acc}; font-weight: 900; background: {c_btn}; padding: 4px 10px; border-radius: 10px; display: inline-block; }}
    .tower-plate {{ width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin:0 2px; }}
    .win {{ background-color: #10B981; }} .loss {{ background-color: #EF4444; }} .unknown {{ background-color: {c_border}; }}
    .prob-box {{ background: {c_btn}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; margin-bottom: 15px; }}
    .prob-number {{ font-size: 32px; font-weight: 900; color: {c_acc}; }}
    .badge-live {{ background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite; }}
    .badge-time {{ background: {c_acc}; color: {c_bg}; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }}
    .stream-btn {{ background-color: #9146FF; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold; display: block; margin-top: 20px; text-align: center; }}
    div.stButton > button {{ background-color: {c_btn}; color: {c_acc}; border: 1px solid {c_border}; font-weight: bold; border-radius: 8px; padding: 10px; width: 100%; transition: 0.3s; }}
    
    .boveda-board {{ background-color: {c_card}; color: {c_text}; border: 2px solid {c_border}; border-radius: 14px; padding: 25px; margin-bottom: 25px; transition: 0.3s; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
    .league-title {{ text-align: center; font-weight: 900; font-size: 24px; margin-bottom: 25px; border-bottom: 2px solid {c_border}; padding-bottom: 15px; }}
    .boveda-row {{ display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid {c_border}; }}
    .w-col-1 {{ width: 28%; font-size: 13px; font-weight: 800; }}
    .w-col-2 {{ width: 42%; text-align: center; background: {c_btn}; border-radius: 6px; padding: 6px; border: 1px solid {c_border}; font-size: 12px; font-weight: 600; }}
    .w-col-3 {{ width: 30%; text-align: right; line-height: 1.5; }}
    .w-pred {{ font-weight: 900; color: {c_acc}; font-size: 14px; }}
    .w-cota {{ font-weight: 800; color: #EF4444; font-size: 11px; background: {c_btn}; padding: 3px 6px; border-radius: 4px; display: inline-block; margin-top: 4px; border: 1px solid {c_border}; letter-spacing: 0.5px; }}
    
    .sticky-panel {{ position: sticky; top: 0; z-index: 999; background-color: {c_bg}; padding: 10px 0; border-bottom: 1px solid {c_border}; }}

    div.row-widget.stRadio > div {{ flex-direction: row; justify-content: center; background: transparent; padding: 5px; }}
    div.row-widget.stRadio > div > label {{ font-size: 14px !important; font-weight: 800 !important; color: {c_text} !important; padding: 6px 15px; background: {c_btn}; border-radius: 6px; border: 1px solid {c_border}; cursor: pointer; margin: 0 5px; transition: 0.3s; }}
    div.row-widget.stRadio > div > label:hover {{ border-color: {c_acc}; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. SIDEBAR 
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h2 style='color:{c_acc}; text-align:center;'>🏦 Mi Bankroll (MANUAL)</h2>", unsafe_allow_html=True)
nuevo_bank = st.sidebar.number_input("Saldo (U):", value=float(bank_actual), step=10.0)
if st.sidebar.button("💾 Guardar Saldo Seguro", use_container_width=True): gestionar_bank(nuevo_bank); st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Auditoría Táctica")
df_ops = gestionar_historial()
if not df_ops.empty:
    for idx, row in df_ops.iloc[::-1].iterrows():
        est = row['Estado']
        color = "#10B981" if est == "GANADA" else "#EF4444" if est == "PERDIDA" else "#334155"
        st.sidebar.markdown(f'<div style="border-left:4px solid {color}; background:{c_btn}; padding:8px; border-radius:5px; margin-bottom:5px; font-size:11px; color:{c_text};"><b>{row["Partido"]}</b><br>{row["Mercado"][:20]}... ({est})</div>', unsafe_allow_html=True)
        if est == "PENDIENTE":
            c_g, c_p = st.sidebar.columns(2)
            if c_g.button("✅", key=f"w_{idx}"): gestionar_historial(index_update=idx, nuevo_estado="GANADA"); st.rerun()
            if c_p.button("❌", key=f"l_{idx}"): gestionar_historial(index_update=idx, nuevo_estado="PERDIDA"); st.rerun()

st.sidebar.markdown("---")
juegos = {"League of Legends": "lol", "Dota 2": "dota2", "Mobile Legends": "mlbb", "CS:GO 2": "csgo", "Valorant": "valorant"}
juego_sel = st.sidebar.selectbox("Juego", list(juegos.keys()))
slug = juegos[juego_sel]

if st.sidebar.button("🗑️ Forzar Actualización Datos", use_container_width=True): st.cache_data.clear(); st.rerun()

# ==========================================
# 6. RADAR PRINCIPAL
# ==========================================
st.markdown(f"<h2 style='color:{c_text}; text-align: center; margin-bottom: 10px;'>📡 Radar Quant: {juego_sel}</h2>", unsafe_allow_html=True)

st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
vista_global = "📡 MODO RADAR (Operar)"
if juego_sel == "League of Legends":
    vista_global = st.radio(
        "Selección de Panel", 
        ["📡 MODO RADAR (Operar)", "📊 MODO BÓVEDA (Tablas Premium)"], 
        horizontal=True,
        label_visibility="collapsed"
    )
st.markdown('</div>', unsafe_allow_html=True)

if juego_sel == "League of Legends":
    df_oracle, oracle_status = load_oracle_database()
    if "OK" in oracle_status:
        pass 
    else:
        st.error(f"🚨 ALERTA DEL SISTEMA: {oracle_status}")

running = call_api_live(slug, "matches/running", "per_page=20")
upcoming = call_api_live(slug, "matches/upcoming", "per_page=100&sort=begin_at")
partidos_totales = running + upcoming

hoy_local = datetime.utcnow() - timedelta(hours=4)
limite_inferior = hoy_local - timedelta(hours=12) 
limite_semana = hoy_local + timedelta(days=7)

partidos_filtrados = []
for p in partidos_totales:
    if p['status'] == 'running': partidos_filtrados.append(p)
    elif p['status'] == 'not_started' and p.get('begin_at'):
        dt_local = datetime.strptime(p['begin_at'], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
        if limite_inferior <= dt_local <= limite_semana: partidos_filtrados.append(p)

if not partidos_filtrados: 
    st.info("No hay actividad programada.")
else:
    for i, m in enumerate(partidos_filtrados[:20]):
        opp = m.get('opponents', [])
        if len(opp) < 2: continue
        t1, t2 = opp[0]['opponent'], opp[1]['opponent']
        
        badge = "<span class='badge-live'>🔴 EN VIVO</span>" if m['status'] == 'running' else f"<span class='badge-time'>📅 { (datetime.strptime(m['begin_at'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).strftime('%d/%m %H:%M') }</span>"
        stream_link = m.get('official_video_url') or (m['streams_list'][0].get('raw_url', '') if m.get('streams_list') else '')
        boton_stream = f'<a href="{stream_link}" target="_blank" class="stream-btn">📺 Ver Transmisión en YouTube/Twitch</a>' if stream_link else ''
        league_name = m['league']['name']

        if juego_sel == "League of Legends":
            wr1, form1, k1, tow1, optow1, drg1, bar1, fb1, time1, roster1 = get_team_stats(t1['name'], t1['id'], df_oracle) 
            wr2, form2, k2, tow2, optow2, drg2, bar2, fb2, time2, roster2 = get_team_stats(t2['name'], t2['id'], df_oracle) 
            
            p_gan_max = max(wr1, wr2) / (wr1+wr2 if (wr1+wr2)>0 else 1)
            eq_gan = t1['name'] if wr1 >= wr2 else t2['name']
            
            has_data = (k1 > 0 and k2 > 0)
            
            if has_data:
                p_fb_real = max(0.05, min(0.95, fb1 / (fb1 + fb2 if (fb1+fb2)>0 else 1)))
                eq_fb = t1['name'] if fb1 >= fb2 else t2['name']
                
                exp_tow = ((tow1 + optow1) + (tow2 + optow2)) / 2
                exp_k, exp_drg, exp_bar, exp_time = (k1+k2), (drg1+drg2), (bar1+bar2), (time1+time2)/2
                
                p_k_mas = max(0.05, min(0.95, 0.50 + (exp_k - 28.5) * 0.03))
                p_to_mas = max(0.05, min(0.95, 0.50 + (exp_tow - 12.5) * 0.10))
                p_d_mas = max(0.05, min(0.95, 0.50 + (exp_drg - 4.5) * 0.15))
                p_b_mas = max(0.05, min(0.95, 0.50 + (exp_bar - 1.5) * 0.25))
                p_t_mas = max(0.05, min(0.95, 0.50 + (exp_time - 32.5) * 0.05))

                def get_tot(p_mas): return (p_mas, "Más") if p_mas >= 0.50 else (1 - p_mas, "Menos")
                p_kills, op_kills = get_tot(p_k_mas); p_tiempo, op_tiempo = get_tot(p_t_mas)
                p_torres, op_torres = get_tot(p_to_mas); p_drag, op_drag = get_tot(p_d_mas)
                p_bar, op_bar = get_tot(p_b_mas)

                # 🏁 MATEMÁTICA DE CARRERAS (BÓVEDA)
                valid_wr1 = [x[1] for x in roster1.values() if x[0] != "S/D"]
                avg_r_wr1 = sum(valid_wr1)/len(valid_wr1) if valid_wr1 else wr1
                
                valid_wr2 = [x[1] for x in roster2.values() if x[0] != "S/D"]
                avg_r_wr2 = sum(valid_wr2)/len(valid_wr2) if valid_wr2 else wr2
                
                p_c5_base = motor_moba(avg_r_wr1, avg_r_wr2, "Carrera a 5", t1['name'], 0, t1['name'])
                p_c10_base = motor_moba(avg_r_wr1, avg_r_wr2, "Carrera a 10", t1['name'], 0, t1['name'])
                
                p_c5 = max(0.05, min(0.95, p_c5_base))
                p_c10 = max(0.05, min(0.95, p_c10_base))

                eq_c5 = t1['name'] if p_c5 >= 0.5 else t2['name']
                eq_c10 = t1['name'] if p_c10 >= 0.5 else t2['name']
                
                res_c5 = f'<span class="w-pred">{eq_c5} ({max(p_c5, 1-p_c5)*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/max(p_c5, 1-p_c5):.2f}</span>'
                res_c10 = f'<span class="w-pred">{eq_c10} ({max(p_c10, 1-p_c10)*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/max(p_c10, 1-p_c10):.2f}</span>'

                res_fb = f'<span class="w-pred">{eq_fb} ({p_fb_real*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/p_fb_real:.2f}</span>'
                res_tow = f'<span class="w-pred">{op_torres} ({p_torres*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/p_torres:.2f}</span>'
                res_drg = f'<span class="w-pred">{op_drag} ({p_drag*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/p_drag:.2f}</span>'
                res_bar = f'<span class="w-pred">{op_bar} ({p_bar*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/p_bar:.2f}</span>'
                res_kil = f'<span class="w-pred">{op_kills} ({p_kills*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/p_kills:.2f}</span>'
                res_tim = f'<span class="w-pred">{op_tiempo} ({p_tiempo*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/p_tiempo:.2f}</span>'
            else:
                sd_html = f'<span style="color:{c_sub}; font-weight:bold;">S/D (Faltan Datos)</span>'
                res_fb = res_tow = res_drg = res_bar = res_kil = res_tim = res_c5 = res_c10 = sd_html
                k1 = k2 = tow1 = optow1 = tow2 = optow2 = drg1 = drg2 = bar1 = bar2 = time1 = time2 = "S/D"

            st.markdown(f"""<div class="glass-card">
                <div style="margin-bottom: 15px; font-size: 13px; display: flex; justify-content: space-between;"><span>🏆 {league_name}</span>{badge}</div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 40%;"><div style="font-size:15px; font-weight:bold;">{t1['name']}</div><img src="{t1.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr1*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form1])}</div></div>
                    <div style="font-size: 26px; font-weight: bold; color: {c_acc};">VS</div>
                    <div style="width: 40%;"><div style="font-size:15px; font-weight:bold;">{t2['name']}</div><img src="{t2.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr2*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form2])}</div></div>
                </div>
                {boton_stream}
            </div>""", unsafe_allow_html=True)
            
            if vista_global == "📡 MODO RADAR (Operar)":
                # ⚡ PANEL PLANO (CERO PESTAÑAS, CERO HTML BASURA)
                with st.container(border=True):
                    st.markdown(f"<div style='font-size:12px; font-weight:900; color:{c_acc}; margin-bottom:10px; text-transform:uppercase;'>⚡ Panel de Cálculo y Riesgo</div>", unsafe_allow_html=True)
                    
                    mercados = ["-- Seleccione --", "⭐ PARTIDO: Ganador", "🗼 Total Torres", "🐉 Total Dragones", "👾 Total Barones", "⚔️ Total Kills", "⏱️ Duración", "🩸 Primera Sangre", "🏁 Carrera a 5 Kills", "🏁 Carrera a 10 Kills"]
                    
                    c_m1, c_m2 = st.columns(2)
                    sel_m = c_m1.selectbox("Mercado", mercados, key=f"m_{i}", label_visibility="collapsed")
                    
                    if sel_m != "-- Seleccione --":
                        key_radio = f"o_{i}_{sel_m}"
                        key_linea = f"l_{i}_{sel_m}"
                        key_cuota = f"c_{i}_{sel_m}"
                        key_boton = f"reg_{i}_{sel_m}"

                        if "Total" in sel_m or "Duración" in sel_m: op_sel = c_m2.radio("Opción:", ["Más (+)", "Menos (-)"], key=key_radio, horizontal=True, label_visibility="collapsed")
                        else: op_sel = c_m2.radio("A favor de:", [t1['name'], t2['name']], key=key_radio, horizontal=True, label_visibility="collapsed")
                        
                        c_l1, c_l2 = st.columns(2)
                        def_l = 12.5 if "Torres" in sel_m else 4.5 if "Dragones" in sel_m else 1.5 if "Barones" in sel_m else 28.5 if "Kills" in sel_m else 32.5 if "Duración" in sel_m else 0.0
                        lin = c_l1.number_input("Línea Flexible", value=def_l, key=key_linea)
                        cuo = c_l2.number_input("Cuota del Casino", value=1.00, step=0.01, key=key_cuota)
                        
                        if has_data:
                            if "Carrera" in sel_m:
                                valid_w1 = [x[1] for x in roster1.values() if x[0] != "S/D"]
                                roster_wr1 = sum(valid_w1)/len(valid_w1) if valid_w1 else wr1
                                valid_w2 = [x[1] for x in roster2.values() if x[0] != "S/D"]
                                roster_wr2 = sum(valid_w2)/len(valid_w2) if valid_w2 else wr2
                                prob_base = motor_moba(roster_wr1, roster_wr2, sel_m, op_sel, lin, t1['name'])
                            elif "Kills" in sel_m and "Total" in sel_m: prob_base = 0.50 + (exp_k - lin) * 0.03
                            elif "Torres" in sel_m: prob_base = 0.50 + (exp_tow - lin) * 0.10
                            elif "Dragones" in sel_m: prob_base = 0.50 + (exp_drg - lin) * 0.15
                            elif "Barones" in sel_m: prob_base = 0.50 + (exp_bar - lin) * 0.25
                            elif "Duración" in sel_m: prob_base = 0.50 + (exp_time - lin) * 0.05
                            elif "Sangre" in sel_m: prob_base = p_fb_real if t1['name'] in op_sel else (1 - p_fb_real)
                            else: prob_base = motor_moba(wr1, wr2, sel_m, op_sel, lin, t1['name'])
                        else:
                            prob_base = motor_moba(wr1, wr2, sel_m, op_sel, lin, t1['name'])

                        prob_final = max(0.05, min(0.95, prob_base))
                        
                        kelly_calc = ((((cuo - 1) * prob_final) - (1 - prob_final)) / (cuo - 1)) * 0.25 * bank_actual if cuo > 1.01 else 0
                        stake_sugerido = max(2.0, min(kelly_calc, bank_actual * 0.05)) if kelly_calc > 0 else 0
                        
                        fuego = "🔥 ¡CUOTA VIABLE!" if cuo > (1/prob_final) and cuo > 1.01 else "❄️ Casino abusivo (Evitar)"
                        color_fuego = "#10B981" if "🔥" in fuego else "#EF4444"

                        st.markdown(f"""<div class="prob-box">
                            <div style="font-size:12px;">Probabilidad Final</div>
                            <div class="prob-number">{prob_final*100:.1f}%</div>
                            <div style="font-size:13px; margin-top:5px; color:{c_text}; font-weight:bold;">EXIGIR COTA MÍN: {1/prob_final:.2f}</div>
                            <div style="font-size:14px; margin-top:8px; color:{color_fuego}; font-weight:900;">{fuego}</div>
                        </div>""", unsafe_allow_html=True)

                        if "🔥" in fuego:
                            st.success(f"💰 Sugerencia de Inversión (Kelly): {stake_sugerido:.2f} U")
                            if st.button("REGISTRAR EN AUDITORÍA", key=key_boton):
                                gestionar_historial(nueva_op={
                                    "Fecha": (datetime.utcnow()-timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
                                    "Juego": juego_sel, "Partido": f"{t1['name']} vs {t2['name']}",
                                    "Mercado": sel_m, "Opcion": op_sel, "Cuota": cuo,
                                    "Inversion": round(stake_sugerido, 2), "Estado": "PENDIENTE",
                                    "MatchID": m['id'], "TeamID": t1['id'] if t1['name'] in op_sel else t2['id']
                                })
                                st.rerun()

            elif vista_global == "📊 MODO BÓVEDA (Tablas Premium)":
                n1, n2 = t1['name'][:10], t2['name'][:10]
                st.markdown(f"""<div class="boveda-board">
                    <div class="league-title">🏆 {league_name}</div>
                    <div class="boveda-row"><div class="w-col-1">⭐ GANADOR</div><div class="w-col-2">{n1}: {wr1*100:.0f}%<br>{n2}: {wr2*100:.0f}%</div><div class="w-col-3"><span class="w-pred">{eq_gan} ({p_gan_max*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/p_gan_max:.2f}</span></div></div>
                    <div class="boveda-row"><div class="w-col-1">🩸 1RA SANGRE</div><div class="w-col-2">Historial Directo<br>24 Mapas Real</div><div class="w-col-3">{res_fb}</div></div>
                    <div class="boveda-row"><div class="w-col-1">🏁 C. 5 KILLS</div><div class="w-col-2">Algoritmo Roster<br>(Rol a Rol)</div><div class="w-col-3">{res_c5}</div></div>
                    <div class="boveda-row"><div class="w-col-1">🏁 C. 10 KILLS</div><div class="w-col-2">Algoritmo Roster<br>(Rol a Rol)</div><div class="w-col-3">{res_c10}</div></div>
                    <div class="boveda-row"><div class="w-col-1">🗼 TORRES (12.5)</div><div class="w-col-2">{n1}: +{tow1 if not has_data else f"{tow1:.1f}"} / -{optow1 if not has_data else f"{optow1:.1f}"}<br>{n2}: +{tow2 if not has_data else f"{tow2:.1f}"} / -{optow2 if not has_data else f"{optow2:.1f}"}</div><div class="w-col-3">{res_tow}</div></div>
                    <div class="boveda-row"><div class="w-col-1">🐉 DRAGONES (4.5)</div><div class="w-col-2">{n1}: {drg1 if not has_data else f"{drg1:.1f}"}<br>{n2}: {drg2 if not has_data else f"{drg2:.1f}"}</div><div class="w-col-3">{res_drg}</div></div>
                    <div class="boveda-row"><div class="w-col-1">👾 BARONES (1.5)</div><div class="w-col-2">{n1}: {bar1 if not has_data else f"{bar1:.1f}"}<br>{n2}: {bar2 if not has_data else f"{bar2:.1f}"}</div><div class="w-col-3">{res_bar}</div></div>
                    <div class="boveda-row"><div class="w-col-1">⚔️ TOTAL KILLS (28.5)</div><div class="w-col-2">{n1}: {k1 if not has_data else f"{k1:.1f}"}<br>{n2}: {k2 if not has_data else f"{k2:.1f}"}</div><div class="w-col-3">{res_kil}</div></div>
                    <div class="boveda-row" style="border-bottom: none;"><div class="w-col-1">⏱️ TIEMPO (32.5)</div><div class="w-col-2">{n1}: {time1 if not has_data else f"{time1:.1f}m"}<br>{n2}: {time2 if not has_data else f"{time2:.1f}m"}</div><div class="w-col-3">{res_tim}</div></div>
                </div>""", unsafe_allow_html=True)

        else:
            # INTERFAZ PARA OTROS JUEGOS (PLANA)
            wr1, form1 = fetch_historical_data_general(slug, t1['id'])
            wr2, form2 = fetch_historical_data_general(slug, t2['id'])
            st.markdown(f"""<div class="glass-card">
                <div style="margin-bottom: 15px; font-size: 13px; display: flex; justify-content: space-between;"><span>🏆 {league_name}</span>{badge}</div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 40%;"><div style="font-size:15px; font-weight:bold;">{t1['name']}</div><img src="{t1.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr1*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form1])}</div></div>
                    <div style="font-size: 26px; font-weight: bold; color: {c_acc};">VS</div>
                    <div style="width: 40%;"><div style="font-size:15px; font-weight:bold;">{t2['name']}</div><img src="{t2.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr2*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form2])}</div></div>
                </div>
                {boton_stream}
            </div>""", unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown(f"<div style='font-size:12px; font-weight:900; color:{c_acc}; margin-bottom:10px; text-transform:uppercase;'>⚡ Panel de Cálculo y Riesgo</div>", unsafe_allow_html=True)
                
                if juego_sel == "Mobile Legends": mercados_g = ["-- Seleccione --", "Ganador", "Handicap", "Primera Sangre", "Carrera a 10 Kills", "Total Kills", "Duración"]
                else: mercados_g = ["-- Seleccione --", "Ganador", "Handicap", "Total Kills", "Primera Sangre", "Carrera a 10 Kills"]
                
                c_m1, c_m2 = st.columns(2)
                sel_m = c_m1.selectbox("Mercado", mercados_g, key=f"mg_{i}", label_visibility="collapsed")
                
                if sel_m != "-- Seleccione --":
                    key_radio = f"og_{i}_{sel_m}"
                    key_linea = f"lg_{i}_{sel_m}"
                    key_cuota = f"cg_{i}_{sel_m}"
                    key_boton = f"regg_{i}_{sel_m}"

                    if "Total" in sel_m or "Duración" in sel_m: op_sel = c_m2.radio("Opción:", ["Más (+)", "Menos (-)"], key=key_radio, horizontal=True, label_visibility="collapsed")
                    else: op_sel = c_m2.radio("A favor de:", [t1['name'], t2['name']], key=key_radio, horizontal=True, label_visibility="collapsed")
                    
                    c_l1, c_l2 = st.columns(2)
                    lin = c_l1.number_input("Línea Flexible", value=0.0, step=0.5, key=key_linea)
                    cuo = c_l2.number_input("Cuota del Casino", value=1.00, step=0.01, key=key_cuota)
                    
                    prob_base = motor_moba(wr1, wr2, sel_m, op_sel, lin, t1['name']) if cat == "⚔️ MOBAs" else motor_fps(wr1, wr2, sel_m, op_sel, lin, t1['name'])
                    prob_final = max(0.05, min(0.95, prob_base))
                    
                    kelly_calc = ((((cuo - 1) * prob_final) - (1 - prob_final)) / (cuo - 1)) * 0.25 * bank_actual if cuo > 1.01 else 0
                    stake_sugerido = max(2.0, min(kelly_calc, bank_actual * 0.05)) if kelly_calc > 0 else 0
                    
                    fuego = "🔥 ¡CUOTA VIABLE!" if cuo > (1/prob_final) and cuo > 1.01 else "❄️ Casino abusivo (Evitar)"
                    color_fuego = "#10B981" if "🔥" in fuego else "#EF4444"

                    st.markdown(f"""<div class="prob-box">
                        <div style="font-size:12px;">Probabilidad Final</div>
                        <div class="prob-number">{prob_final*100:.1f}%</div>
                        <div style="font-size:13px; margin-top:5px; color:{c_text}; font-weight:bold;">EXIGIR COTA MÍN: {1/prob_final:.2f}</div>
                        <div style="font-size:14px; margin-top:8px; color:{color_fuego}; font-weight:900;">{fuego}</div>
                    </div>""", unsafe_allow_html=True)

                    if "🔥" in fuego:
                        st.success(f"💰 Sugerencia de Inversión (Kelly): {stake_sugerido:.2f} U")
                        if st.button("REGISTRAR EN AUDITORÍA", key=key_boton):
                            gestionar_historial(nueva_op={
                                "Fecha": (datetime.utcnow()-timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
                                "Juego": juego_sel, "Partido": f"{t1['name']} vs {t2['name']}",
                                "Mercado": sel_m, "Opcion": op_sel, "Cuota": cuo,
                                "Inversion": round(stake_sugerido, 2), "Estado": "PENDIENTE",
                                "MatchID": m['id'], "TeamID": t1['id'] if t1['name'] in op_sel else t2['id']
                            })
                            st.rerun()