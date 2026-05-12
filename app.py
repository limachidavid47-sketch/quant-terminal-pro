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
st.set_page_config(page_title="Quant Elite V88.4 - LoL Core", layout="wide", initial_sidebar_state="expanded")

def check_password():
    token = st.query_params.get("token", "")
    if token == "capo": st.session_state["password_correct"] = True
    if st.session_state.get("password_correct", False): return True

    st.markdown("""<style>.stApp { background-color: #05080F; color: #F8FAFC; }</style>""", unsafe_allow_html=True)
    
    html_login = """
    <div style='background: #0F172A; border: 2px solid #10B981; border-radius: 20px; padding: 30px; margin-top: 5vh; box-shadow: 0 0 20px rgba(16, 185, 129, 0.2); text-align: center;'>
    <h2 style='color: #10B981; letter-spacing: 2px;'>⚡ QUANT TERMINAL V88.4</h2>
    <p style='color:#64748B;'>RADAR EXCLUSIVO LEAGUE OF LEGENDS | ESCALADO PURE QUANT</p>
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
# 3. EL CEREBRO QUANT LOL 
# ==========================================
def motor_moba(wr1, wr2, mercado, opcion, linea, t1_name):
    total_wr = wr1 + wr2 if (wr1+wr2)>0 else 1
    prob = wr1/total_wr if t1_name in opcion else wr2/total_wr
    if "Total" in mercado or "Duración" in mercado:
        mom = (wr1 + wr2) / 2
        prob = 0.50 + (mom - 0.50) * 0.3 if "Más" in opcion else 0.50 - (mom - 0.50) * 0.3
    elif "Sangre" in mercado:
        prob = 0.50 + (( (wr1/total_wr if t1_name in opcion else wr2/total_wr) - 0.50) * 0.7)
    return max(0.05, min(0.95, prob))

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
    columnas_clave = ['teamname', 'position', 'date', 'result', 'teamkills', 'towers', 'opp_towers', 'dragons', 'barons', 'firstblood', 'gamelength', 'ckpm', 'golddiffat15']
    if os.path.exists("datos_oracle.zip"):
        try:
            df = pd.read_csv("datos_oracle.zip", compression='zip', usecols=lambda c: c.strip().lower() in columnas_clave, low_memory=False)
            df.columns = df.columns.str.strip().str.lower()
            return df
        except:
            try:
                df = pd.read_csv("datos_oracle.zip", usecols=lambda c: c.strip().lower() in columnas_clave, low_memory=False)
                df.columns = df.columns.str.strip().str.lower()
                return df
            except: pass
    return pd.DataFrame()

def get_team_stats(team_name, team_id, df_completo):
    if df_completo.empty: 
        wr, form = fetch_historical_data_general(team_id)
        return wr, form, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.50, 0.0
    
    basura = ['esports', 'challengers', 'academy', 'gaming', 'club', 'sports', 'team']
    words = [w for w in team_name.lower().split() if w not in basura and len(w) > 2]
    core_name = words[0] if words else team_name.lower().split()[0]
    
    df_team = df_completo[(df_completo['teamname'].str.lower().str.contains(core_name, na=False)) & (df_completo['position'] == 'team')].copy()
    df_team['date'] = pd.to_datetime(df_team['date'], errors='coerce')
    df_team = df_team.sort_values(by='date', ascending=False).head(15) 
    
    if df_team.empty:
        wr, form = fetch_historical_data_general(team_id)
        return wr, form, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.50, 0.0
    
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
    
    return float(winrate), form, float(avg_k), float(avg_t), float(avg_ot), float(avg_d), float(avg_b), float(avg_fb), float(avg_time), float(avg_gold15), float(conv_rate), float(comeback_rate)

# ==========================================
# 4. ESTÉTICA Y CSS
# ==========================================
st.markdown("""<style>
    .stApp { background-color: #05080F; color: #F1F5F9; font-family: 'Inter', sans-serif; }
    .glass-card { background: #0F172A; border: 1px solid #1E293B; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.5); position: relative; transition: 0.3s; }
    .team-logo { width: 60px; height: 60px; object-fit: contain; margin-bottom: 5px; }
    .winrate-text { font-size: 14px; color: #38BDF8; font-weight: 900; background: #1E293B; padding: 4px 10px; border-radius: 10px; display: inline-block; margin-top: 5px; border: 1px solid #334155; }
    .tower-plate { width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin:0 2px; }
    .win { background-color: #10B981; } .loss { background-color: #EF4444; } .unknown { background-color: #334155; }
    .badge-live { background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite; }
    .badge-time { background: #38BDF8; color: #05080F; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }
    .stream-btn { background-color: #9146FF; color: white !important; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold; display: block; margin-top: 20px; text-align: center; }
    .prob-box { background: #1E293B; padding: 15px; border-radius: 8px; border: 1px solid #38BDF8; text-align: center; }
    .prob-number { font-size: 32px; font-weight: 900; color: #38BDF8; }
    .boveda-board { background-color: #0F172A; border: 1px solid #1E293B; border-radius: 14px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    .boveda-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #1E293B; }
    .w-col-1 { width: 30%; font-size: 13px; font-weight: bold; color: #94A3B8; }
    .w-col-2 { width: 40%; text-align: center; font-size: 13px; background: #1E293B; padding: 6px; border-radius: 6px; }
    .w-col-3 { width: 30%; text-align: right; }
    .w-pred { font-weight: 900; color: #38BDF8; font-size: 14px; }
    .w-cota { font-weight: bold; color: #EF4444; font-size: 11px; background: #1E293B; padding: 3px 6px; border-radius: 4px; border: 1px solid #EF4444; display: inline-block; margin-top: 4px; }
</style>""", unsafe_allow_html=True)

# ==========================================
# 5. SIDEBAR: CENTRO DE MANDO LOL
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#38BDF8;'>⚙️ V88.4 LOL CORE</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center; background:#1E293B; padding:15px; border-radius:10px; border:1px solid #334155; margin-bottom:20px;'>Bankroll<br><span style='color:#10B981; font-weight:900; font-size:24px;'>{bank_actual} U</span></div>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align:center; color:#94A3B8; font-size:12px;'>Radar Activo</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-weight:bold; color:#F8FAFC; margin-bottom:20px;'>🛡️ League of Legends</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    nuevo_b = st.number_input("Gestión de Caja (U)", value=float(bank_actual))
    if st.button("💾 Actualizar Bankroll", use_container_width=True): gestionar_bank(nuevo_b); st.rerun()

# ==========================================
# 6. RADAR Y BÓVEDA EXCLUSIVOS
# ==========================================
st.markdown("<h1 style='text-align: center; color: #F8FAFC;'>📡 RADAR TÁCTICO: LEAGUE OF LEGENDS</h1>", unsafe_allow_html=True)

tab_radar, tab_boveda = st.tabs(["📡 PANEL EN VIVO", "📊 BÓVEDA PREMIUM"])

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
    st.info("No hay encuentros de League of Legends en el marco temporal de escaneo.")
else:
    with tab_radar:
        for i, m in enumerate(partidos_filtrados):
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            
            badge = "<span class='badge-live'>🔴 EN VIVO</span>" if m['status'] == 'running' else f"<span class='badge-time'>📅 {(datetime.strptime(m['begin_at'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).strftime('%d/%m %H:%M')}</span>"
            
            lista_streams = m.get('streams_list', [])
            video_url = lista_streams[0].get('raw_url', '#') if lista_streams and len(lista_streams) > 0 else '#'
            stream_html = f"<a href='{video_url}' target='_blank' class='stream-btn'>📺 Ver Transmisión</a>" if video_url != '#' else ""
            
            league_name = m.get('league', {}).get('name', 'Competición')

            wr1, f1, k1, tow1, optow1, drg1, bar1, fb1, time1, gold1_15, conv1, come1 = get_team_stats(t1['name'], t1['id'], df_oracle) 
            wr2, f2, k2, tow2, optow2, drg2, bar2, fb2, time2, gold2_15, conv2, come2 = get_team_stats(t2['name'], t2['id'], df_oracle) 

            placas_t1 = "".join([f"<span class='tower-plate {x}'></span>" for x in f1])
            placas_t2 = "".join([f"<span class='tower-plate {x}'></span>" for x in f2])

            html_tarjeta = f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div style="font-size: 13px; color: #94A3B8; font-weight: bold;">🏆 {league_name}</div>
                    <div>{badge}</div>
                </div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 35%;">
                        <div style="font-size:15px; font-weight:bold;">{t1['name']}</div>
                        <img src="{t1.get('image_url','')}" class="team-logo"><br>
                        <div class="winrate-text">WR: {wr1*100:.0f}%</div><br>
                        <div style="margin-top:5px;">{placas_t1}</div>
                    </div>
                    <div style="font-size: 26px; font-weight: bold; color: #334155;">VS</div>
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
                        exp_time = (time1 + time2) / 2
                        exp_k = k1 + k2; exp_tow = tow1 + optow1
                        
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
                        <div style="font-size:12px; color:#94A3B8;">Probabilidad Matemática</div>
                        <div class="prob-number" style="color:{color};">{p_final*100:.1f}%</div>
                        <div style="margin-top:10px; font-weight:bold;">C. JUSTA: {c_justa:.2f} | {fuego}</div>
                    </div>
                    """
                    st.markdown(html_prob.replace('\n', ' '), unsafe_allow_html=True)
                    
                    if cuo > c_justa: st.success(f"💰 Stake Sugerido (Kelly): {kelly:.2f} U")

    with tab_boveda:
        st.markdown("<h3 style='color:#38BDF8;'>📋 Bóveda Premium</h3>", unsafe_allow_html=True)
        for m in partidos_filtrados:
            opp = m.get('opponents', [])
            if len(opp) < 2: continue
            t1, t2 = opp[0]['opponent'], opp[1]['opponent']
            league_name = m.get('league', {}).get('name', 'Competición')
            n1, n2 = t1['name'][:10], t2['name'][:10]
            img1, img2 = t1.get('image_url', ''), t2.get('image_url', '')
            
            wr1, f1, k1, tow1, optow1, drg1, bar1, fb1, time1, gold1_15, conv1, come1 = get_team_stats(t1['name'], t1['id'], df_oracle) 
            wr2, f2, k2, tow2, optow2, drg2, bar2, fb2, time2, gold2_15, conv2, come2 = get_team_stats(t2['name'], t2['id'], df_oracle) 
            
            has_data = (k1 > 0 and k2 > 0)
            if has_data:
                exp_time = (time1 + time2) / 2
                exp_k = k1 + k2; exp_tow = tow1 + optow1
                
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
                
                def get_tot(p): return (p, "Más") if p >= 0.50 else (1 - p, "Menos")
                pt, ot = get_tot(p_time); pk, ok = get_tot(p_k); ptow, otow = get_tot(p_tow)

                html_boveda_lol = f"""
                <div class="boveda-board">
                <div class="league-title">🏆 {league_name}</div>
                <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 20px;">
                    <div style="text-align: right; width: 40%;"><b>{n1}</b> <img src="{img1}" style="width:30px; vertical-align:middle; margin-left:10px;"></div>
                    <div style="width: 20%; text-align: center; font-weight: 900; color: #334155;">VS</div>
                    <div style="text-align: left; width: 40%;"><img src="{img2}" style="width:30px; vertical-align:middle; margin-right:10px;"> <b>{n2}</b></div>
                </div>
                <div class="boveda-row"><div class="w-col-1">⭐ GANADOR</div><div class="w-col-2">{n1}: {wr1*100:.0f}%<br>{n2}: {wr2*100:.0f}%</div><div class="w-col-3"><span class="w-pred">{n1 if p_gb>=0.5 else n2} ({max(p_gb, 1-p_gb)*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/max(p_gb, 1-p_gb):.2f}</span></div></div>
                <div class="boveda-row"><div class="w-col-1">🩸 FASE EARLY (Min 15)</div><div class="w-col-2">{n1}: Oro {gold1_15:+.0f} | FB {fb1*100:.0f}%<br>{n2}: Oro {gold2_15:+.0f} | FB {fb2*100:.0f}%</div><div class="w-col-3"><span class="w-pred">{n1 if p_fb>=0.5 else n2} ({max(p_fb, 1-p_fb)*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN FB: {1/max(p_fb, 1-p_fb):.2f}</span></div></div>
                <div class="boveda-row"><div class="w-col-1">🛡️ ESCALADO (Min 25+) & TORRES</div><div class="w-col-2">{n1}: Remontada {come1*100:.0f}%<br>{n2}: Remontada {come2*100:.0f}%</div><div class="w-col-3"><span class="w-pred">Torres: {otow} ({ptow*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/ptow:.2f}</span></div></div>
                <div class="boveda-row"><div class="w-col-1">⚔️ TOTAL KILLS (28.5)</div><div class="w-col-2">Avg {n1}: {k1:.1f}<br>Avg {n2}: {k2:.1f}</div><div class="w-col-3"><span class="w-pred">{ok} ({pk*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/pk:.2f}</span></div></div>
                <div class="boveda-row" style="border-bottom: none;"><div class="w-col-1">⏱️ TIEMPO (32.5)</div><div class="w-col-2">Avg {n1}: {time1:.1f}m<br>Avg {n2}: {time2:.1f}m</div><div class="w-col-3"><span class="w-pred">{ot} ({pt*100:.0f}%)</span><br><span class="w-cota">EXIGIR C.MÍN: {1/pt:.2f}</span></div></div>
                </div>
                """
                st.markdown(html_boveda_lol.replace('\n', ' '), unsafe_allow_html=True)
            else:
                st.info(f"Faltan datos de Oracle para {n1} vs {n2}")