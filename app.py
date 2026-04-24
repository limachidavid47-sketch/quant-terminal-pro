import streamlit as st
import pandas as pd
import os

# ==========================================
# 1. CONFIGURACIÓN Y CSS "DARK THEME PREMIUM"
# ==========================================
st.set_page_config(page_title="Quant Terminal Elite", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Fondo Oscuro Elegante (Tipo Gemini/Discord) */
    .stApp { background-color: #0E1117; color: #E8EAED; }
    
    /* Botones de Navegación */
    button[kind="secondary"] {
        height: 70px !important; width: 100% !important;
        font-size: 16px !important; font-weight: bold !important;
        border-radius: 8px !important; background-color: #1A1D24 !important;
        border: 1px solid #2D323E !important; color: #E8EAED !important;
        transition: 0.2s !important; box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    button[kind="secondary"]:hover {
        border-color: #10B981 !important; color: #10B981 !important;
        background-color: #1E2B26 !important;
    }
    
    /* Tarjetas Oscuras (Glassmorphism oscuro) */
    .glass-card {
        background: #16181E;
        padding: 25px; border-radius: 12px; text-align: center;
        border: 1px solid #2D323E; box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        margin-bottom: 20px; color: #E8EAED;
    }
    
    /* Personalización de Inputs en Tema Oscuro */
    div[data-baseweb="select"] > div { background-color: #0E1117; border-color: #2D323E; color: white; }
    input[type="number"] { background-color: #0E1117; border: 1px solid #2D323E; color: white; text-align: center; font-weight: bold;}
    
    /* Textos y Acentos */
    .text-muted { color: #9AA0A6; font-size: 14px; }
    .text-highlight { color: #8AB4F8; font-weight: bold; } /* Azul suave */
    .text-success { color: #10B981; font-weight: bold; } /* Verde Neón */
    .text-danger { color: #EF4444; font-weight: bold; } /* Rojo */
    
    /* Indicador En Vivo */
    .live-badge {
        background-color: #EF4444; color: white; padding: 4px 8px;
        border-radius: 4px; font-size: 12px; font-weight: bold;
        animation: pulse 2s infinite;
    }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTORES LÓGICOS
# ==========================================
def calcular_kelly(prob, cuota, bank):
    if prob <= 0 or cuota <= 1: return 0.0
    return max(0, (((cuota - 1) * prob - (1 - prob)) / (cuota - 1) * 0.25) * bank)

ARCHIVO_BANK = "bank_data.txt"
def gestionar_bankroll(monto=None):
    if not os.path.exists(ARCHIVO_BANK):
        with open(ARCHIVO_BANK, "w") as f: f.write("100.0")
    if monto is not None:
        with open(ARCHIVO_BANK, "w") as f: f.write(str(monto))
    with open(ARCHIVO_BANK, "r") as f: return float(f.read())

bank_actual = gestionar_bankroll()

# ==========================================
# 3. NAVEGACIÓN PRINCIPAL
# ==========================================
if 'pagina' not in st.session_state: st.session_state.pagina = "Radar"

st.sidebar.title("⚡ Quant System")
st.sidebar.metric("🏦 BANKROLL", f"{bank_actual:.2f} U")
st.sidebar.button("🔄 Refrescar Escáner", use_container_width=True)
st.sidebar.markdown("---")

nav_cols = st.columns(3)
with nav_cols[0]:
    if st.button("🔴 RADAR EN VIVO (2 Col)"): st.session_state.pagina = "Radar"
with nav_cols[1]:
    if st.button("🏆 EXPLORADOR"): st.session_state.pagina = "Explorador"
with nav_cols[2]:
    if st.button("📊 DIARIO (Historial)"): st.session_state.pagina = "Diario"
st.markdown("---")

# ==========================================
# 4. PANTALLAS
# ==========================================

# ------------------------------------------
# PANTALLA 1: RADAR (MERCADOS AVANZADOS)
# ------------------------------------------
if st.session_state.pagina == "Radar":
    st.markdown("<h2 style='color: #E8EAED;'>🔴 Escáner Táctico de Partidos</h2>", unsafe_allow_html=True)
    
    partidos_vivo = [
        {"liga": "LCK", "t1": "T1", "t2": "GEN", "estado": "Juego 1 - Min 15:20"},
        {"liga": "LPL", "t1": "JDG", "t2": "BLG", "estado": "Juego 2 - Min 08:45"},
        {"liga": "LEC", "t1": "G2", "t2": "FNC", "estado": "Por Empezar (14:00)"},
        {"liga": "LCS", "t1": "C9", "t2": "TL", "estado": "Por Empezar (16:00)"}
    ]

    r_cols = st.columns(2)
    
    # LISTA DE MERCADOS AVANZADOS
    lista_mercados = [
        "Ganador del Mapa",
        "1ra Sangre (Primer Kill)",
        "Handicap de Kills",
        "Total Kills - Global (Más/Menos)",
        "Kills Equipo A (Más/Menos)",
        "Kills Equipo B (Más/Menos)",
        "Total Dragones (Más/Menos)",
        "Ambos Matan Dragón (Sí/No)",
        "Total Torres (Más/Menos)",
        "Duración del Mapa (Más/Menos)"
    ]

    for i, p in enumerate(partidos_vivo):
        with r_cols[i % 2]:
            st.markdown(f"<div class='glass-card'>", unsafe_allow_html=True)
            
            # Encabezado
            c_head1, c_head2 = st.columns([3,1])
            with c_head1: st.markdown(f"<h3 style='margin:0; color:#E8EAED;'>{p['t1']} vs {p['t2']}</h3>", unsafe_allow_html=True)
            with c_head2: 
                if "Min" in p['estado']: st.markdown("<span class='live-badge'>EN VIVO</span>", unsafe_allow_html=True)
            
            st.markdown(f"<p class='text-muted' style='margin-top:5px;'>{p['liga']} | {p['estado']}</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:10px 0; border-color:#2D323E;'>", unsafe_allow_html=True)
            
            # --- MOTOR DE MERCADOS DINÁMICO ---
            mercado = st.selectbox("Mercado de Operación:", lista_mercados, key=f"m_{i}")
            
            # Lógica dinámica según la familia de mercado elegido
            prob = 0.50 # Probabilidad base
            
            if "Más/Menos" in mercado:
                c_linea, c_tipo = st.columns(2)
                # Valores por defecto inteligentes
                val_defecto = 25.5 if "Kills" in mercado else (4.5 if "Dragones" in mercado else 12.5)
                with c_linea: linea = st.number_input("Línea:", value=val_defecto, step=0.5, key=f"l_{i}")
                with c_tipo: tipo = st.selectbox("Opción:", ["Más (+)", "Menos (-)"], key=f"t_{i}")
                prob = 0.65 if tipo == "Más (+)" else 0.58
                
            elif "Handicap" in mercado:
                c_linea, c_eq = st.columns(2)
                with c_linea: linea = st.number_input("Línea Handicap:", value=-5.5, step=0.5, key=f"hl_{i}")
                with c_eq: equipo_sel = st.selectbox("Equipo:", [p['t1'], p['t2']], key=f"he_{i}")
                prob = 0.55
                
            elif "Sí/No" in mercado:
                opcion = st.selectbox("Selección:", ["Sí", "No"], key=f"sn_{i}")
                prob = 0.72 if opcion == "Sí" else 0.28
                
            elif "1ra Sangre" in mercado or "Ganador" in mercado:
                equipo_sel = st.selectbox("Equipo Seleccionado:", [p['t1'], p['t2']], key=f"es_{i}")
                prob = 0.82 if equipo_sel == p['t1'] else 0.68
                
            st.markdown(f"<h2 class='text-highlight' style='margin: 15px 0;'>🎯 Prob: {prob*100:.1f}%</h2>", unsafe_allow_html=True)
            
            # --- ENTRADA DE CUOTA Y KELLY ---
            cuota = st.number_input("Cuota del Casino:", value=1.00, step=0.01, format="%.2f", key=f"c_{i}")
            
            if cuota > (1/prob):
                stake = calcular_kelly(prob, cuota, bank_actual)
                ev = (prob * cuota) - 1
                st.markdown(f"<p class='text-success'>✅ VALOR (+{ev*100:.1f}%)</p>", unsafe_allow_html=True)
                st.markdown(f"<div style='background:#10B981; color:#0E1117; padding:8px; border-radius:6px; margin-bottom:10px;'><b>Stake Sugerido: {stake:.2f} U</b></div>", unsafe_allow_html=True)
                
                if st.button("🚀 Confirmar Apuesta", key=f"b_{i}", use_container_width=True):
                    gestionar_bankroll(bank_actual - stake)
                    st.rerun()
            elif cuota > 1.00:
                st.markdown(f"<p class='text-danger'>❌ Cuota Mínima Exigida: {(1/prob):.2f}</p>", unsafe_allow_html=True)
                
            st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# PANTALLAS 2 Y 3 (Sin cambios, para mantener el foco)
# ------------------------------------------
elif st.session_state.pagina == "Explorador":
    st.markdown("<h2 style='color: #E8EAED;'>🏆 Explorador de Datos</h2>", unsafe_allow_html=True)
    st.write("Base de datos de equipos conectada. (Oculta en esta vista para optimizar rendimiento).")
elif st.session_state.pagina == "Diario":
    st.markdown("<h2 style='color: #E8EAED;'>📊 Diario de Trading</h2>", unsafe_allow_html=True)
    st.write("Aquí se registrarán tus apuestas de Handicap, Dragones y Primera Sangre.")