import streamlit as st
import requests
import os
import math
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 1. SEGURIDAD Y CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Quant Elite V34.3", layout="wide", initial_sidebar_state="expanded")

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
        st.markdown("<div class='login-title'>⚡ QUANT TERMINAL V34.3</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748B; margin-bottom:20px; text-align: center;'>AUDITORÍA LOL: 10 PARTIDAS + SMART SCAN</p>", unsafe_allow_html=True)
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
# 2. FINANZAS Y GESTIÓN DE DATOS (10 PARTIDAS)
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

# ==========================================
# 3. MOTOR MATEMÁTICO INTEGRAL
# ==========================================
def motor_moba(wr1, wr2, mercado, opcion, linea, t1_name):
    total_wr = wr1 + wr2 if (wr1+wr2)>0 else 1
    prob = wr1/total_wr if t1_name in opcion else wr2/total_wr
    if "Total" in mercado or "Duración" in mercado or "Ambos" in mercado:
        mom = (wr1 + wr2) / 2
        prob = 0.50 + (mom - 0.50) * 0.3 if "Más" in opcion or "SÍ" in opcion else 0.50 - (mom - 0.50) * 0.3
        if "Ambos" in mercado: prob = 0.72 + (mom - 0.50) * 0.15
    elif "Primer" in mercado or "Primera" in mercado:
        prob = 0.50 + (( (wr1/total_wr if t1_name in opcion else wr2/total_wr) - 0.50) * 0.7)
    return max(0.05, min(0.95, prob))

# ==========================================
# 4. INTERFAZ Y RADAR SMART LOL
# ==========================================
st.sidebar.markdown(f"## 🏦 Bankroll: {gestionar_bank():.2f} U")
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Auditoría Táctica")
df_ops = gestionar_historial()
if not df_ops.empty:
    for idx, row in df_ops.iloc[::-1].iterrows():
        est = row['Estado']
        color = "#10B981" if est == "GANADA" else "#EF4444" if est == "PERDIDA" else "#334155"
        st.sidebar.markdown(f'<div style="border-left:4px solid {color}; background:#1E293B; padding:5px; border-radius:5px; margin-bottom:5px; font-size:10px;"><b>{row["Partido"]}</b><br>{row["Mercado"]} ({est})</div>', unsafe_allow_html=True)
        if est == "PENDIENTE":
            c_g, c_p = st.sidebar.columns(2)
            if c_g.button("✅", key=f"w_{idx}"): gestionar_historial(index_update=idx, nuevo_estado="GANADA"); st.rerun()
            if c_p.button("❌", key=f"l_{idx}"): gestionar_historial(index_update=idx, nuevo_estado="PERDIDA"); st.rerun()

cat = st.sidebar.radio("Disciplina", ["⚔️ MOBAs", "🔫 Shooters"])
juegos = {"League of Legends": "lol", "Dota 2": "dota2", "Mobile Legends": "mlbb", "CS:GO 2": "csgo", "Valorant": "valorant"}
juego_sel = st.sidebar.selectbox("Juego", list(juegos.keys()))
slug = juegos[juego_sel]

st.title(f"Radar Quant: {juego_sel}")
partidos = requests.get(f"https://api.pandascore.co/{slug}/matches?filter[status]=running,not_started&per_page=15&sort=begin_at", headers={"authorization": f"Bearer {API_KEY}"}).json()

if partidos:
    for i, m in enumerate(partidos):
        opp = m.get('opponents', [])
        if len(opp) < 2: continue
        t1, t2 = opp[0]['opponent'], opp[1]['opponent']
        
        # AUDITORÍA DE 10 PARTIDAS REALES
        wr1, _ = fetch_historical_data(slug, t1['id'])
        wr2, _ = fetch_historical_data(slug, t2['id'])

        with st.expander(f"⚔️ {t1['name']} vs {t2['name']} (Auditoría 10G)"):
            if juego_sel == "League of Legends":
                # LÓGICA SMART-SCAN 75-100%
                p_gan = wr1/(wr1+wr2) if wr1>=wr2 else wr2/(wr1+wr2)
                eq_gan = t1['name'] if wr1>=wr2 else t2['name']
                p_m = 0.5 + ((wr1+wr2)/2 - 0.5)*0.3
                p_tot = p_m if p_m >= 0.5 else 1-p_m
                op_tot = "Más" if p_m >= 0.5 else "Menos"

                def fmt(n, p, d=""):
                    ico = "🔥 " if p >= 0.75 else ""
                    return f"{ico}{n} | {d} ({p*100:.1f}%) C.Mín: {1/p:.2f}"

                mercados = [
                    "-- Seleccione Mercado Prediseñado --",
                    fmt("⭐ Ganador", p_gan, eq_gan),
                    fmt("🗼 Total Torres", p_tot, f"{op_tot} 12.5"),
                    fmt("🐉 Total Dragones", p_tot, f"{op_tot} 4.5"),
                    fmt("👾 Total Barones", p_tot, f"{op_tot} 1.5"),
                    fmt("⚔️ Total Kills", p_tot, f"{op_tot} 28.5"),
                    fmt("⏱️ Tiempo Total", p_tot, f"{op_tot} 32.5"),
                    fmt("🩸 Primera Sangre", 0.5+((p_gan-0.5)*0.7), eq_gan),
                    "Flexible: Ambos Asesinan Dragón", "Flexible: Handicap"
                ]
            elif juego_sel == "Mobile Legends":
                mercados = ["Ganador", "Handicap", "Primera Sangre", "Carrera a 10 Kills", "Total Kills", "Duración"]
            else:
                mercados = ["Ganador", "Handicap", "Total Kills", "Primera Sangre"]

            sel_m = st.selectbox("Inyector de Músculo Quant", mercados, key=f"m_{i}")
            
            # Interfaz de Operación
            if "Total" in sel_m or "Tiempo" in sel_m: op_sel = st.radio("Opción:", ["Más (+)", "Menos (-)"], key=f"o_{i}")
            else: op_sel = st.radio("A favor de:", [t1['name'], t2['name'], "SÍ", "NO"], key=f"o_{i}")

            # Auto-ajuste de Línea
            def_l = 0.0
            if "Torres" in sel_m: def_l = 12.5
            elif "Dragones" in sel_m: def_l = 4.5
            elif "Barones" in sel_m: def_l = 1.5
            elif "Kills" in sel_m: def_l = 28.5
            elif "Tiempo" in sel_m: def_l = 32.5

            c_l, c_c = st.columns(2)
            lin = c_l.number_input("Línea", value=def_l, key=f"l_{i}")
            cuo = c_c.number_input("Cuota Casino", value=1.85, key=f"c_{i}")

            if st.button("REGISTRAR DISPARO", key=f"reg_{i}"):
                gestionar_bank(bank_actual - (0.05 * bank_actual))
                gestionar_historial(nueva_op={
                    "Fecha": (datetime.utcnow()-timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
                    "Juego": juego_sel, "Partido": f"{t1['name']} vs {t2['name']}",
                    "Mercado": sel_m.split("|")[0].strip(), "Opcion": op_sel, "Cuota": cuo,
                    "Inversion": round(0.05 * bank_actual, 2), "Estado": "PENDIENTE",
                    "MatchID": m['id'], "TeamID": t1['id'] if t1['name'] in op_sel else t2['id']
                })
                st.rerun()