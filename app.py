import streamlit as st
import requests
import os
import math
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Quant Elite V41.0", layout="centered", initial_sidebar_state="expanded")

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
    st.markdown("<div class='login-title'>⚡ QUANT TERMINAL V41.0</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B; margin-bottom:20px; text-align: center;'>UI CAMALEÓN: BÓVEDA ADAPTABLE Y TEMA BLANCO</p>", unsafe_allow_html=True)
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
# 2. FINANZAS Y GESTIÓN DE DATOS
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
        if nuevo_estado == "GANADA" and df.at[index_update, 'Estado'] == "PENDIENTE":
            gestionar_bank(gestionar_bank() + (df.at[index_update, 'Inversion'] * df.at[index_update, 'Cuota']))
        df.at[index_update, 'Estado'] = nuevo_estado
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df[df['Fecha'] >= (datetime.utcnow() - timedelta(hours=52))]
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
# 3. EL NINJA DE ORACLE ELIXIR
# ==========================================
@st.cache_data(ttl=28800, show_spinner=False)
def fetch_oracle_elixir_data(team_name):
    try:
        url_oracle = "https://oracleselixir-downloadable-match-data.s3-us-west-2.amazonaws.com/2024_LoL_esports_match_data_from_OraclesElixir.csv"
        df_team = pd.DataFrame()
        for chunk in pd.read_csv(url_oracle, chunksize=5000, low_memory=False):
            filtrado = chunk[(chunk['teamname'].str.contains(team_name, case=False, na=False)) & (chunk['position'] == 'team')]
            df_team = pd.concat([df_team, filtrado])
            if len(df_team) >= 10: break
                
        if not df_team.empty:
            df_team['date'] = pd.to_datetime(df_team['date'], errors='coerce')
            df_team = df_team.sort_values(by='date', ascending=False).head(10)
            
            wins = df_team['result'].sum() 
            winrate = wins / len(df_team) if len(df_team) > 0 else 0.50
            form = ['win' if r == 1 else 'loss' for r in df_team['result'].tolist()[:5]]
            
            cols = df_team.columns
            avg_kills = df_team['teamkills'].mean() if 'teamkills' in cols else 14.0
            avg_towers = df_team['towers'].mean() if 'towers' in cols else 6.0
            avg_dragons = df_team['dragons'].mean() if 'dragons' in cols else 2.5
            avg_barons = df_team['teambaronskills'].mean() if 'teambaronskills' in cols else 0.8
            avg_time = (df_team['gamelength'].mean() / 60) if 'gamelength' in cols else 32.0
            
            return winrate, form, avg_kills, avg_towers, avg_dragons, avg_barons, avg_time
        else:
            return fetch_historical_pandascore("lol", team_name)
    except:
        return fetch_historical_pandascore("lol", team_name)

def fetch_historical_pandascore(game_slug, team_name):
    return 0.50, ['unknown']*5, 14.0, 6.0, 2.5, 0.8, 32.0 

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

def motor_moba(wr1, wr2, mercado, opcion, linea, t1_name):
    total_wr = wr1 + wr2 if (wr1+wr2)>0 else 1
    prob = wr1/total_wr if t1_name in opcion else wr2/total_wr
    if "Total" in mercado or "Duración" in mercado or "Tiempo" in mercado or "Ambos" in mercado:
        mom = (wr1 + wr2) / 2
        prob = 0.50 + (mom - 0.50) * 0.3 if "Más" in opcion or "SÍ" in opcion else 0.50 - (mom - 0.50) * 0.3
        if "Ambos" in mercado: prob = 0.72 + (mom - 0.50) * 0.15
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
# 4. TEMAS Y CSS (SISTEMA DE PALETAS DINÁMICO)
# ==========================================
st.sidebar.markdown("### 🎨 Apariencia")
tema = st.sidebar.selectbox("", ["Azul Oscuro (Defecto)", "Verde Hacker", "Rojo Táctico", "Blanco Cuántico"])

# Diccionario de Temas: (Fondo, Tarjeta, Texto, Acento, Borde, Botones/Cajas)
colors = {
    "Azul Oscuro (Defecto)": ("#0B1120", "#1E293B", "#F1F5F9", "#38BDF8", "#334155", "#0F172A"),
    "Verde Hacker": ("#000000", "#051A05", "#4ADE80", "#10B981", "#064E3B", "#022C22"),
    "Rojo Táctico": ("#0A0000", "#1A0505", "#FECACA", "#EF4444", "#7F1D1D", "#450A0A"),
    "Blanco Cuántico": ("#F1F5F9", "#FFFFFF", "#0F172A", "#2563EB", "#CBD5E1", "#F8FAFC")
}
c_bg, c_card, c_text, c_acc, c_border, c_btn = colors[tema]

st.markdown(f"""
    <style>
    .stApp {{ background-color: {c_bg}; color: {c_text}; font-family: 'Inter', sans-serif; transition: background-color 0.3s; }}
    [data-testid="stSidebar"] {{ background-color: {c_card} !important; border-right: 1px solid {c_border}; transition: background-color 0.3s; }}
    .glass-card {{ background: {c_card}; border: 1px solid {c_border}; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); position: relative; transition: 0.3s; }}
    .team-logo {{ width: 70px; height: 70px; object-fit: contain; margin-bottom: 5px; }}
    .team-logo-small {{ width: 45px; height: 45px; object-fit: contain; margin-bottom: 5px; }}
    .winrate-text {{ font-size: 14px; color: {c_acc}; font-weight: 900; margin-bottom: 5px; background: {c_btn}; padding: 4px 10px; border-radius: 10px; display: inline-block; }}
    .tower-plate {{ width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin:0 2px; }}
    .win {{ background-color: #10B981; }} .loss {{ background-color: #EF4444; }} .unknown {{ background-color: {c_border}; }}
    .prob-box {{ background: {c_btn}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; margin-bottom: 15px; margin-top: 10px; }}
    .prob-number {{ font-size: 32px; font-weight: 900; color: {c_acc}; }}
    .badge-live {{ background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite; }}
    .badge-time {{ background: {c_acc}; color: {c_bg}; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }}
    .stream-btn {{ background-color: #9146FF; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold; display: block; margin-top: 20px; text-align: center; }}
    div.stButton > button {{ background-color: {c_btn}; color: {c_acc}; border: 1px solid {c_border}; font-weight: bold; border-radius: 8px; padding: 10px; width: 100%; transition: 0.3s; }}
    
    /* CSS BÓVEDA V41.0: EL CAMALEÓN CUÁNTICO (Adaptable al Tema) */
    .boveda-board {{ background-color: {c_card}; color: {c_text}; border: 2px solid {c_border}; border-radius: 14px; padding: 25px; font-family: 'Inter', sans-serif; box-shadow: 0 8px 16px rgba(0,0,0,0.08); margin-top: 10px; margin-bottom: 25px; transition: 0.3s; }}
    .league-title {{ text-align: center; font-weight: 900; font-size: 24px; margin-bottom: 25px; color: {c_text}; letter-spacing: 1px; text-transform: uppercase; border-bottom: 2px solid {c_border}; padding-bottom: 15px; }}
    .boveda-row {{ display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid {c_border}; }}
    .w-col-1 {{ width: 28%; font-size: 13px; font-weight: 800; color: {c_text}; }}
    .w-col-2 {{ width: 42%; text-align: center; background: {c_btn}; border-radius: 6px; padding: 6px; border: 1px solid {c_border}; font-size: 12px; color: {c_text}; font-weight: 600; line-height: 1.4; }}
    .w-col-3 {{ width: 30%; text-align: right; line-height: 1.5; }}
    .w-pred {{ font-weight: 900; color: {c_acc}; font-size: 14px; }}
    .w-cota {{ font-weight: 800; color: #EF4444; font-size: 12px; background: {c_btn}; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-top: 4px; border: 1px solid {c_border}; }}
    .player-box {{ background: {c_btn}; padding: 12px 15px; border-radius: 10px; border: 1px solid {c_border}; font-size: 12px; text-align: center; margin-top: 25px; font-weight: 700; color: {c_text}; width: 48%; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
    
    /* Diseño especial para el Switcher Frontal */
    div.row-widget.stRadio > div {{ flex-direction: row; justify-content: center; background: transparent; padding: 5px; }}
    div.row-widget.stRadio > div > label {{ font-size: 15px !important; font-weight: 900 !important; color: {c_text} !important; padding: 10px 20px; background: {c_card}; border-radius: 8px; border: 1px solid {c_border}; cursor: pointer; margin: 0 10px; transition: 0.3s; }}
    div.row-widget.stRadio > div > label:hover {{ border-color: {c_acc}; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. SIDEBAR 
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h2 style='color:{c_acc}; text-align:center;'>🏦 Mi Bankroll</h2>", unsafe_allow_html=True)
nuevo_bank = st.sidebar.number_input("Saldo (U):", value=float(bank_actual), step=10.0)
if st.sidebar.button("💾 Guardar Saldo", use_container_width=True): gestionar_bank(nuevo_bank); st.rerun()

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
cat = st.sidebar.radio("Disciplina", ["⚔️ MOBAs", "🔫 Shooters"])
juegos = {"League of Legends": "lol", "Dota 2": "dota2", "Mobile Legends": "mlbb", "CS:GO 2": "csgo", "Valorant": "valorant"}
juego_sel = st.sidebar.selectbox("Juego", list(juegos.keys()))
slug = juegos[juego_sel]

if st.sidebar.button("🗑️ Limpiar Caché (Forzar Oracle)", use_container_width=True): st.cache_data.clear(); st.rerun()

# ==========================================
# 6. RADAR PRINCIPAL
# ==========================================
st.markdown(f"<h2 style='color:{c_text}; text-align: center; margin-bottom: 10px;'>📡 Radar Quant: {juego_sel}</h2>", unsafe_allow_html=True)

# EL BOTÓN GIGANTE FRONTAL
vista_global = "📡 MODO RADAR (Operar)"
if juego_sel == "League of Legends":
    vista_global = st.radio(
        "Selección de Panel", 
        ["📡 MODO RADAR (Operar)", "📊 MODO BÓVEDA (Tablas Premium)"], 
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown(f"<hr style='border:1px solid {c_border}; margin-top: 15px; margin-bottom: 25px;'>", unsafe_allow_html=True)

running = call_api_live(slug, "matches/running", "per_page=20")
upcoming = call_api_live(slug, "matches/upcoming", "per_page=100&sort=begin_at")
partidos_totales = running + upcoming

hoy_utc = datetime.utcnow()
hoy_local = hoy_utc - timedelta(hours=4)
limite_inferior = hoy_local - timedelta(hours=12) 
limite_semana = hoy_local + timedelta(days=7)

partidos_filtrados = []
for p in partidos_totales:
    if p['status'] == 'running': partidos_filtrados.append(p)
    elif p['status'] == 'not_started' and p.get('begin_at'):
        dt_utc = datetime.strptime(p['begin_at'], "%Y-%m-%dT%H:%M:%SZ")
        dt_local = dt_utc - timedelta(hours=4)
        if limite_inferior <= dt_local <= limite_semana: partidos_filtrados.append(p)

if not partidos_filtrados: 
    st.info("No hay actividad programada en los próximos 7 días.")
else:
    for i, m in enumerate(partidos_filtrados[:20]):
        opp = m.get('opponents', [])
        if len(opp) < 2: continue
        t1, t2 = opp[0]['opponent'], opp[1]['opponent']
        
        badge = "<span class='badge-live'>🔴 EN VIVO</span>" if m['status'] == 'running' else f"<span class='badge-time'>📅 { (datetime.strptime(m['begin_at'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).strftime('%d/%m %H:%M') }</span>"
        stream_link = m.get('official_video_url') or (m['streams_list'][0].get('raw_url', '') if m.get('streams_list') else '')
        boton_stream = f'<a href="{stream_link}" target="_blank" class="stream-btn">📺 Ver Transmisión en Vivo</a>' if stream_link else ''
        league_name = m['league']['name']

        if juego_sel == "League of Legends":
            wr1, form1, k1, tow1, drg1, bar1, time1 = fetch_oracle_elixir_data(t1['name'])
            wr2, form2, k2, tow2, drg2, bar2, time2 = fetch_oracle_elixir_data(t2['name'])
            
            exp_k = k1 + k2
            exp_tow = tow1 + tow2
            exp_drg = drg1 + drg2
            exp_bar = bar1 + bar2
            exp_time = (time1 + time2) / 2
            
            p_gan_max = max(wr1, wr2) / (wr1+wr2 if (wr1+wr2)>0 else 1)
            eq_gan = t1['name'] if wr1 >= wr2 else t2['name']
            
            p_fb = 0.50 + ((p_gan_max - 0.50) * 0.7)
            
            p_k_mas = max(0.05, min(0.95, 0.50 + (exp_k - 28.5) * 0.03))
            p_to_mas = max(0.05, min(0.95, 0.50 + (exp_tow - 12.5) * 0.10))
            p_d_mas = max(0.05, min(0.95, 0.50 + (exp_drg - 4.5) * 0.15))
            p_b_mas = max(0.05, min(0.95, 0.50 + (exp_bar - 1.5) * 0.25))
            p_t_mas = max(0.05, min(0.95, 0.50 + (exp_time - 32.5) * 0.05))
            
            def get_tot(p_mas): return (p_mas, "Más") if p_mas >= 0.50 else (1 - p_mas, "Menos")
            p_kills, op_kills = get_tot(p_k_mas)
            p_tiempo, op_tiempo = get_tot(p_t_mas)
            p_torres, op_torres = get_tot(p_to_mas)
            p_drag, op_drag = get_tot(p_d_mas)
            p_bar, op_bar = get_tot(p_b_mas)
            
            n1 = t1['name'][:10]
            n2 = t2['name'][:10]
            
            # LA TARJETA PRINCIPAL (Camaleónica)
            st.markdown(f"""
            <div class="glass-card">
                <div style="margin-bottom: 15px; font-size: 13px; display: flex; justify-content: space-between;"><span>🏆 {league_name}</span>{badge}</div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 40%;"><div style="font-size:15px; font-weight:bold; margin-bottom:5px;">{t1['name']}</div><img src="{t1.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr1*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form1])}</div></div>
                    <div style="font-size: 26px; font-weight: bold; color: {c_acc};">VS</div>
                    <div style="width: 40%;"><div style="font-size:15px; font-weight:bold; margin-bottom:5px;">{t2['name']}</div><img src="{t2.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr2*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form2])}</div></div>
                </div>
                {boton_stream}
            </div>
            """, unsafe_allow_html=True)
            
            if vista_global == "📡 MODO RADAR (Operar)":
                with st.expander(f"⚙️ Panel Quant: {t1['name']} vs {t2['name']}"):
                    mercados = ["-- Seleccione --", "⭐ PARTIDO: Ganador", "🗼 Total Torres", "🐉 Total Dragones", "👾 Total Barones", "⚔️ Total Kills", "⏱️ Duración", "🩸 Primera Sangre", "⚖️ Handicap"]
                    sel_m = st.selectbox("Mercado", mercados, key=f"m_{i}")
                    clean_m = sel_m.replace("🔥 ", "").replace("❄️🔥 ", "") 
                    
                    if clean_m != "-- Seleccione --":
                        if "Total" in clean_m or "Duración" in clean_m: op_sel = st.radio("Opción:", ["Más (+)", "Menos (-)"], key=f"o_{i}")
                        else: op_sel = st.radio("A favor de:", [t1['name'], t2['name']], key=f"o_{i}")
                        
                        def_l = 12.5 if "Torres" in clean_m else 4.5 if "Dragones" in clean_m else 1.5 if "Barones" in clean_m else 28.5 if "Kills" in clean_m else 32.5 if "Duración" in clean_m else 0.0
                        c_l, c_c = st.columns(2)
                        lin = c_l.number_input("Línea Flexible", value=def_l, key=f"l_{i}")
                        cuo = c_c.number_input("Cuota Casino", value=1.00, step=0.01, key=f"c_{i}")

                        if "Kills" in clean_m: prob_base = 0.50 + (exp_k - lin) * 0.03
                        elif "Torres" in clean_m: prob_base = 0.50 + (exp_tow - lin) * 0.10
                        elif "Dragones" in clean_m: prob_base = 0.50 + (exp_drg - lin) * 0.15
                        elif "Barones" in clean_m: prob_base = 0.50 + (exp_bar - lin) * 0.25
                        elif "Duración" in clean_m: prob_base = 0.50 + (exp_time - lin) * 0.05
                        else: prob_base = motor_moba(wr1, wr2, clean_m, op_sel, lin, t1['name'])
                             
                        if "Menos" in op_sel or "NO" in op_sel: prob_base = 1 - prob_base
                        prob_final = max(0.05, min(0.95, prob_base))
                        
                        st.markdown(f"""<div class="prob-box"><div style="font-size:12px;">Probabilidad</div><div class="prob-number">{prob_final*100:.1f}%</div><div style="font-size:12px;">C.Mín: {1/prob_final:.2f}</div></div>""", unsafe_allow_html=True)
                        if cuo > 1.01 and cuo > (1/prob_final):
                            stake = ((((cuo - 1) * prob_final) - (1 - prob_final)) / (cuo - 1)) * 0.25 * bank_actual
                            if stake > 0:
                                st.success(f"🔥 Sugerido: {stake:.2f} U"); 
                                if st.button("REGISTRAR", key=f"reg_{i}"): gestionar_bank(bank_actual - stake); st.rerun()

            elif vista_global == "📊 MODO BÓVEDA (Tablas Premium)":
                # HTML V41.0: CAMALEÓN (Toma los colores de CSS definidos arriba)
                html_boveda = f"""
<div class="boveda-board">
    <div class="league-title">🏆 {league_name}</div>
    <div style="display: flex; justify-content: space-around; align-items: center; margin-bottom: 25px;">
        <div style="text-align: center; width: 30%;">
            <img src="{t1.get('image_url','')}" class="team-logo-small"><br>
            <b>{t1['name']}</b>
        </div>
        <div style="font-weight: 900; color: {c_acc}; font-size: 13px; text-align: center; width: 40%;">
            ⚡ PROMEDIOS CARA A CARA<br>VS PREDICCIÓN FINAL
        </div>
        <div style="text-align: center; width: 30%;">
            <img src="{t2.get('image_url','')}" class="team-logo-small"><br>
            <b>{t2['name']}</b>
        </div>
    </div>
    <div class="boveda-row">
        <div class="w-col-1">⭐ GANADOR</div> 
        <div class="w-col-2">{n1}: <b>{wr1*100:.0f}%</b><br>{n2}: <b>{wr2*100:.0f}%</b></div>
        <div class="w-col-3"><span class="w-pred">{eq_gan} ({p_gan_max*100:.0f}%)</span><br><span class="w-cota">C.Mín: {1/p_gan_max:.2f}</span></div>
    </div>
    <div class="boveda-row">
        <div class="w-col-1">🩸 1RA SANGRE</div> 
        <div class="w-col-2">Ventaja por Momentum<br>Mecánica H2H</div>
        <div class="w-col-3"><span class="w-pred">{eq_gan} ({p_fb*100:.0f}%)</span><br><span class="w-cota">C.Mín: {1/p_fb:.2f}</span></div>
    </div>
    <div class="boveda-row">
        <div class="w-col-1">🗼 TORRES (12.5)</div> 
        <div class="w-col-2">{n1}: <b>{tow1:.1f}</b><br>{n2}: <b>{tow2:.1f}</b></div>
        <div class="w-col-3"><span class="w-pred">{op_torres} ({p_torres*100:.0f}%)</span><br><span class="w-cota">C.Mín: {1/p_torres:.2f}</span></div>
    </div>
    <div class="boveda-row">
        <div class="w-col-1">🐉 DRAGONES (4.5)</div> 
        <div class="w-col-2">{n1}: <b>{drg1:.1f}</b><br>{n2}: <b>{drg2:.1f}</b></div>
        <div class="w-col-3"><span class="w-pred">{op_drag} ({p_drag*100:.0f}%)</span><br><span class="w-cota">C.Mín: {1/p_drag:.2f}</span></div>
    </div>
    <div class="boveda-row">
        <div class="w-col-1">👾 BARONES (1.5)</div> 
        <div class="w-col-2">{n1}: <b>{bar1:.1f}</b><br>{n2}: <b>{bar2:.1f}</b></div>
        <div class="w-col-3"><span class="w-pred">{op_bar} ({p_bar*100:.0f}%)</span><br><span class="w-cota">C.Mín: {1/p_bar:.2f}</span></div>
    </div>
    <div class="boveda-row">
        <div class="w-col-1">⚔️ TOTAL KILLS (28.5)</div> 
        <div class="w-col-2">{n1}: <b>{k1:.1f}</b><br>{n2}: <b>{k2:.1f}</b></div>
        <div class="w-col-3"><span class="w-pred">{op_kills} ({p_kills*100:.0f}%)</span><br><span class="w-cota">C.Mín: {1/p_kills:.2f}</span></div>
    </div>
    <div class="boveda-row" style="border-bottom: none;">
        <div class="w-col-1">⏱️ TIEMPO P. (32.5)</div> 
        <div class="w-col-2">{n1}: <b>{time1:.1f}m</b><br>{n2}: <b>{time2:.1f}m</b></div>
        <div class="w-col-3"><span class="w-pred">{op_tiempo} ({p_tiempo*100:.0f}%)</span><br><span class="w-cota">C.Mín: {1/p_tiempo:.2f}</span></div>
    </div>
    <div style="display: flex; justify-content: space-between;">
        <div class="player-box">⭐ MVP Simul: Capitán<br>KDA: 4.8 | Main: Azir</div>
        <div class="player-box">⭐ MVP Simul: Capitán<br>KDA: 5.1 | Main: Lee Sin</div>
    </div>
</div>
"""
                st.markdown(html_boveda, unsafe_allow_html=True)

        else:
            # INTERFAZ PARA DOTA 2 Y DEMÁS JUEGOS (INTACTA Y EN 1 COLUMNA)
            wr1, form1 = fetch_historical_data_general(slug, t1['id'])
            wr2, form2 = fetch_historical_data_general(slug, t2['id'])
            st.markdown(f"""
            <div class="glass-card">
                <div style="margin-bottom: 15px; font-size: 13px; display: flex; justify-content: space-between;"><span>🏆 {league_name}</span>{badge}</div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 40%;"><div style="font-size:15px; font-weight:bold; margin-bottom:5px;">{t1['name']}</div><img src="{t1.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr1*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form1])}</div></div>
                    <div style="font-size: 26px; font-weight: bold; color: {c_acc};">VS</div>
                    <div style="width: 40%;"><div style="font-size:15px; font-weight:bold; margin-bottom:5px;">{t2['name']}</div><img src="{t2.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr2*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form2])}</div></div>
                </div>
                {boton_stream}
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("⚙️ Operar Mercado Quant"):
                if juego_sel == "Mobile Legends": mercados_g = ["Ganador", "Handicap", "Primera Sangre", "Carrera a 10 Kills", "Total Kills", "Duración"]
                else: mercados_g = ["Ganador", "Handicap", "Total Kills", "Primera Sangre", "Carrera a 10 Kills"]
                sel_m = st.selectbox("Mercado", mercados_g, key=f"mg_{i}")
                
                if "Total" in sel_m or "Duración" in sel_m: op_sel = st.radio("Opción:", ["Más (+)", "Menos (-)"], key=f"og_{i}")
                else: op_sel = st.radio("A favor de:", [t1['name'], t2['name']], key=f"og_{i}")
                
                c_l, c_c = st.columns(2)
                lin = c_l.number_input("Línea", value=0.0, step=0.5, key=f"lg_{i}")
                cuo = c_c.number_input("Cuota", value=1.00, step=0.01, key=f"cg_{i}")
                
                prob_base = motor_moba(wr1, wr2, sel_m, op_sel, lin, t1['name']) if cat == "⚔️ MOBAs" else motor_fps(wr1, wr2, sel_m, op_sel, lin, t1['name'])
                prob_final = max(0.05, min(0.95, prob_base))
                
                st.markdown(f"""<div class="prob-box"><div style="font-size:12px;">Probabilidad Final</div><div class="prob-number">{prob_final*100:.1f}%</div><div style="font-size:12px;">Cuota Mín: {1/prob_final:.2f}</div></div>""", unsafe_allow_html=True)

                if cuo > 1.01 and cuo > (1/prob_final):
                    stake = ((((cuo - 1) * prob_final) - (1 - prob_final)) / (cuo - 1)) * 0.25 * bank_actual
                    if stake > 0:
                        st.success(f"🔥 Sugerido: {stake:.2f} U")
                        if st.button("REGISTRAR", key=f"regg_{i}"):
                            gestionar_bank(bank_actual - stake)
                            gestionar_historial(nueva_op={
                                "Fecha": (datetime.utcnow()-timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
                                "Juego": juego_sel, "Partido": f"{t1['name']} vs {t2['name']}",
                                "Mercado": sel_m, "Opcion": op_sel, "Cuota": cuo,
                                "Inversion": round(stake, 2), "Estado": "PENDIENTE",
                                "MatchID": m['id'], "TeamID": t1['id'] if t1['name'] in op_sel else t2['id']
                            })
                            st.rerun()