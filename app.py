import streamlit as st
import requests
import os
import math
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Quant Elite V34.6", layout="wide", initial_sidebar_state="expanded")

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
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>⚡ QUANT TERMINAL V34.6</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748B; margin-bottom:20px; text-align: center;'>PARCHE ANTI-CRASH APLICADO</p>", unsafe_allow_html=True)
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

@st.cache_data(ttl=21600, show_spinner=False)
def fetch_historical_data(game_slug, team_id):
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

@st.cache_data(ttl=60)
def call_api_live(game_slug, endpoint, params_str=""):
    url = f"https://api.pandascore.co/{game_slug}/{endpoint}?{params_str}"
    headers = {"accept": "application/json", "authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

# ==========================================
# 3. MOTOR MATEMÁTICO INTEGRAL
# ==========================================
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
# 4. TEMAS Y CSS 
# ==========================================
st.sidebar.markdown("### 🎨 Apariencia")
tema = st.sidebar.selectbox("", ["Azul Oscuro (Defecto)", "Verde Hacker", "Rojo Táctico"])
colors = {"Azul Oscuro (Defecto)": ("#0B1120", "#1E293B", "#F1F5F9", "#38BDF8"), "Verde Hacker": ("#000000", "#051A05", "#4ADE80", "#10B981"), "Rojo Táctico": ("#0A0000", "#1A0505", "#FECACA", "#EF4444")}
c_bg, c_card, c_text, c_acc = colors[tema]
c_sub, c_border, c_btn = "#94A3B8", "#334155", "#0F172A"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {c_bg}; color: {c_text}; font-family: 'Inter', sans-serif; }}
    [data-testid="stSidebar"] {{ background-color: {c_card} !important; border-right: 1px solid {c_border}; }}
    .glass-card {{ background: {c_card}; border: 1px solid {c_border}; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); position: relative; }}
    .team-logo {{ width: 60px; height: 60px; object-fit: contain; margin-bottom: 5px; }}
    .winrate-text {{ font-size: 13px; color: {c_acc}; font-weight: 900; margin-bottom: 5px; background: {c_btn}; padding: 2px 8px; border-radius: 10px; display: inline-block; }}
    .tower-plate {{ width: 14px; height: 8px; border-radius: 2px; display: inline-block; margin:0 2px; }}
    .win {{ background-color: #10B981; }} .loss {{ background-color: #EF4444; }} .unknown {{ background-color: #475569; }}
    .prob-box {{ background: {c_btn}; padding: 15px; border-radius: 8px; border: 1px solid {c_acc}; text-align: center; margin-bottom: 15px; }}
    .prob-number {{ font-size: 32px; font-weight: 900; color: {c_acc}; }}
    .badge-live {{ background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; animation: pulse 2s infinite; }}
    .badge-time {{ background: {c_acc}; color: {c_bg}; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }}
    .stream-btn {{ background-color: #9146FF; color: white !important; padding: 8px 12px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: bold; display: block; margin-top: 15px; text-align: center; }}
    div.stButton > button {{ background-color: {c_btn}; color: {c_acc}; border: 1px solid {c_border}; font-weight: bold; border-radius: 8px; padding: 10px; width: 100%; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. SIDEBAR: FINANZAS Y AUDITORÍA
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
        st.sidebar.markdown(f'<div style="border-left:4px solid {color}; background:#1E293B; padding:8px; border-radius:5px; margin-bottom:5px; font-size:11px;"><b>{row["Partido"]}</b><br>{row["Mercado"][:20]}... ({est})</div>', unsafe_allow_html=True)
        if est == "PENDIENTE":
            c_g, c_p = st.sidebar.columns(2)
            if c_g.button("✅", key=f"w_{idx}"): gestionar_historial(index_update=idx, nuevo_estado="GANADA"); st.rerun()
            if c_p.button("❌", key=f"l_{idx}"): gestionar_historial(index_update=idx, nuevo_estado="PERDIDA"); st.rerun()

# ==========================================
# 6. MOTOR DE DATOS Y RADAR
# ==========================================
st.sidebar.markdown("---")
cat = st.sidebar.radio("Disciplina", ["⚔️ MOBAs", "🔫 Shooters"])
juegos = {"League of Legends": "lol", "Dota 2": "dota2", "Mobile Legends": "mlbb", "CS:GO 2": "csgo", "Valorant": "valorant"}
juego_sel = st.sidebar.selectbox("Juego", list(juegos.keys()))
slug = juegos[juego_sel]

if st.sidebar.button("🗑️ Limpiar Caché", use_container_width=True): st.cache_data.clear(); st.rerun()

st.markdown(f"<h2 style='color:{c_text};'>📡 Radar Quant: {juego_sel}</h2>", unsafe_allow_html=True)

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
    c1, c2 = st.columns(2)
    for i, m in enumerate(partidos_filtrados[:16]):
        opp = m.get('opponents', [])
        if len(opp) < 2: continue
        t1, t2 = opp[0]['opponent'], opp[1]['opponent']
        
        wr1, form1 = fetch_historical_data(slug, t1['id'])
        wr2, form2 = fetch_historical_data(slug, t2['id'])

        badge = "<span class='badge-live'>🔴 EN VIVO</span>" if m['status'] == 'running' else f"<span class='badge-time'>📅 { (datetime.strptime(m['begin_at'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).strftime('%d/%m %H:%M') }</span>"
        
        stream_link = m.get('official_video_url') or (m['streams_list'][0].get('raw_url', '') if m.get('streams_list') else '')
        boton_stream = f'<a href="{stream_link}" target="_blank" class="stream-btn">📺 Ver Transmisión en Vivo</a>' if stream_link else ''

        with (c1 if i % 2 == 0 else c2):
            st.markdown(f"""
            <div class="glass-card">
                <div style="margin-bottom: 10px; font-size: 11px; display: flex; justify-content: space-between;"><span>🏆 {m['league']['name']}</span>{badge}</div>
                <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
                    <div style="width: 40%;"><div style="font-size:12px; font-weight:bold;">{t1['name']}</div><img src="{t1.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr1*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form1])}</div></div>
                    <div style="font-size: 20px; font-weight: bold; color: {c_acc};">VS</div>
                    <div style="width: 40%;"><div style="font-size:12px; font-weight:bold;">{t2['name']}</div><img src="{t2.get('image_url','')}" class="team-logo"><br><div class="winrate-text">{wr2*100:.0f}%</div><div>{"".join([f"<div class='tower-plate {x}'></div>" for x in form2])}</div></div>
                </div>
                {boton_stream}
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"⚙️ Operar Mercado Quant"):
                if juego_sel == "League of Legends":
                    p_gan_max = max(wr1, wr2) / (wr1+wr2 if (wr1+wr2)>0 else 1)
                    p_m = 0.5 + (((wr1+wr2)/2) - 0.5)*0.3
                    p_tot_max = max(p_m, 1-p_m)
                    
                    def get_ico(p): return "🔥 " if p >= 0.75 else ""

                    mercados = [
                        "-- Seleccione --",
                        f"{get_ico(p_gan_max)}⭐ PARTIDO: Ganador",
                        f"{get_ico(p_tot_max)}🗼 Total Torres",
                        f"{get_ico(p_tot_max)}🐉 Total Dragones",
                        f"{get_ico(p_tot_max)}👾 Total Barones",
                        f"{get_ico(p_tot_max)}⚔️ Total Kills",
                        f"{get_ico(p_tot_max)}⏱️ Duración",
                        "🤝 Ambos Asesinan Dragón",
                        "🩸 Primera Sangre",
                        "🏁 Carrera a 5 Kills",
                        "🏁 Carrera a 10 Kills",
                        "🏁 Carrera a 15 Kills",
                        "⚖️ Handicap"
                    ]
                elif juego_sel == "Mobile Legends":
                    mercados = ["Ganador", "Handicap", "Primera Sangre", "Carrera a 10 Kills", "Total Kills", "Duración"]
                else:
                    mercados = ["Ganador", "Handicap", "Total Kills", "Primera Sangre", "Carrera a 10 Kills"]

                sel_m = st.selectbox("Mercado", mercados, key=f"m_{i}")
                clean_m = sel_m.replace("🔥 ", "") 
                
                # INYECTOR DE MOMENTUM (SOLO LOL) - CON PARCHE ANTI-CRASH
                ajuste_mapa_2 = 0
                res_m1 = "Ninguno" # <- AQUÍ ESTÁ EL ESCUDO CONTRA EL ERROR ROJO
                
                if juego_sel == "League of Legends" and "PARTIDO" not in clean_m and clean_m != "-- Seleccione --":
                    st.markdown(f"<div style='border-top:1px solid {c_border}; margin-top:5px; padding-top:5px;'></div>", unsafe_allow_html=True)
                    if st.radio("📍 Operando en:", ["Mapa 1", "Mapa 2+"], horizontal=True, key=f"ctx_{i}") == "Mapa 2+":
                        res_m1 = st.selectbox("¿Quién ganó el Mapa Anterior?", ["Ninguno", t1['name'], t2['name']], key=f"m1_{i}")
                        if res_m1 != "Ninguno":
                            es_t1_fav = wr1 >= wr2
                            if "Total" in clean_m or "Duración" in clean_m:
                                ajuste_mapa_2 = +0.03 
                            else:
                                if res_m1 == t1['name']: ajuste_mapa_2 = (-0.02 if es_t1_fav else 0.01)
                                elif res_m1 == t2['name']: ajuste_mapa_2 = (-0.02 if not es_t1_fav else 0.01)

                # LAS DOS CARAS DE LA MONEDA (OPCIONES LIBRES)
                if clean_m != "-- Seleccione --":
                    if "Total" in clean_m or "Duración" in clean_m or "Tiempo" in clean_m: 
                        op_sel = st.radio("Opción:", ["Más (+)", "Menos (-)"], key=f"o_{i}")
                        if "Menos" in op_sel: ajuste_mapa_2 = -ajuste_mapa_2
                    elif "Ambos" in clean_m: 
                        op_sel = st.radio("Opción:", ["SÍ", "NO"], key=f"o_{i}")
                    else: 
                        op_sel = st.radio("A favor de:", [t1['name'], t2['name']], key=f"o_{i}")
                        if res_m1 != "Ninguno" and op_sel == t2['name'] and ajuste_mapa_2 != 0:
                             ajuste_mapa_2 = -ajuste_mapa_2 

                    def_l = 0.0
                    if "Torres" in clean_m: def_l = 12.5
                    elif "Dragones" in clean_m: def_l = 4.5
                    elif "Barones" in clean_m: def_l = 1.5
                    elif "Kills" in clean_m and "Total" in clean_m: def_l = 28.5
                    elif "Duración" in clean_m: def_l = 32.5

                    c_l, c_c = st.columns(2)
                    lin = c_l.number_input("Línea (Flexible)", value=def_l, key=f"l_{i}")
                    cuo = c_c.number_input("Cuota Casino", value=1.00, step=0.01, key=f"c_{i}")

                    prob_base = motor_moba(wr1, wr2, clean_m, op_sel, lin, t1['name']) if cat == "⚔️ MOBAs" else motor_fps(wr1, wr2, clean_m, op_sel, lin, t1['name'])
                    prob_final = max(0.05, min(0.95, prob_base + ajuste_mapa_2))
                    
                    st.markdown(f"""<div class="prob-box"><div style="font-size:10px;">Probabilidad Final</div><div class="prob-number">{prob_final*100:.1f}%</div><div style="font-size:10px;">Cuota Mín: {1/prob_final:.2f}</div></div>""", unsafe_allow_html=True)

                    if cuo > 1.01:
                        if cuo > (1/prob_final):
                            kelly = (((cuo - 1) * prob_final) - (1 - prob_final)) / (cuo - 1)
                            stake = (kelly * 0.25) * bank_actual
                            if stake > 0:
                                st.success(f"🔥 Inversión Sugerida: {stake:.2f} U")
                                if st.button("REGISTRAR DISPARO", key=f"reg_{i}"):
                                    gestionar_bank(bank_actual - stake)
                                    gestionar_historial(nueva_op={
                                        "Fecha": (datetime.utcnow()-timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
                                        "Juego": juego_sel, "Partido": f"{t1['name']} vs {t2['name']}",
                                        "Mercado": clean_m, "Opcion": op_sel, "Cuota": cuo,
                                        "Inversion": round(stake, 2), "Estado": "PENDIENTE",
                                        "MatchID": m['id'], "TeamID": t1['id'] if t1['name'] in op_sel else t2['id']
                                    })
                                    st.rerun()
                        else:
                            st.error("❌ Cuota sin valor matemático. ¡No operar!")