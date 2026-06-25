import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="Hibridación Eolica y H2", layout="wide")

st.title("Trabajo Final Integrador - Mauro Galliani")
st.title("Simulación planta Híbrida Eólica/Hidrógeno - Power-to-Gas")
st.markdown("Simulador del balance entre Generación eólica, Producción de H2 y de CH4 y sus pérdidas.")

# Controles en la barra lateral para mayor limpieza visual
st.sidebar.header("Parámetros del Sistema")
cap_red = st.sidebar.slider("Capacidad de la Red Eléctrica (MW)", 20, 100, 60)
cap_elec = st.sidebar.slider("Capacidad del Electrolizador (MW)", 0, 50, 20)

st.sidebar.header("Ruta Power-to-Gas (PtG)")
ruta_ptg = st.sidebar.radio(
    "Seleccione el vector energético final:",
    ("Hidrógeno Verde (Inyección Directa / Blending)", 
     "Metano Sintético (Reactor Sabatier Industrial)", 
     "Metano Biológico (Almacenamiento Subterráneo - Caso Hychico)")
)

st.sidebar.header("Parámetros Operativos")
factor_agua = st.sidebar.number_input(
    "Consumo de Agua (L/kg H2)", min_value=8.93, max_value=30.0, value=15.0, step=0.5,
    help="Límite estequiométrico: 8.93 L/kg. Promedio industrial por purgas y ósmosis: 15 L/kg."
)

# Generación del perfil eólico sintético
if 'semilla' not in st.session_state:
    st.session_state.semilla = 42

if st.sidebar.button("Generar Nuevo Perfil Eólico"):
    st.session_state.semilla = np.random.randint(0, 10000)

np.random.seed(st.session_state.semilla)
horas = np.arange(0, 25)
p_viento = 50 + 35 * np.sin(horas * np.pi / 12 - np.pi/4) + 10 * np.random.rand(25)
p_viento = np.clip(p_viento, 0, 120)

# Algoritmo de despacho EMS
p_red = np.minimum(p_viento, cap_red)
p_h2 = np.minimum(p_viento - p_red, cap_elec)
p_perdida = p_viento - p_red - p_h2

# Visualización de áreas
fig, ax = plt.subplots(figsize=(12, 6))
ax.fill_between(horas, 0, p_red, color='#4CAF50', label='Inyección a Red', alpha=0.8)
ax.fill_between(horas, p_red, p_red + p_h2, color='#2196F3', label='Producción de H2', alpha=0.8)
ax.fill_between(horas, p_red + p_h2, p_viento, color='#F44336', label='Curtailment (Pérdida)', alpha=0.8)
ax.plot(horas, p_viento, color='black', linewidth=2, label='Generación Eólica Total')
ax.set_xlabel('Horas del día')
ax.set_ylabel('Potencia (MW)')
ax.set_xlim(0, 24)
ax.set_ylim(0, 130)
ax.legend(loc='upper left')
ax.grid(True, linestyle='--', alpha=0.5)
st.pyplot(fig)

# Integración matemática (MWh)
energia_viento = np.trapezoid(p_viento, horas)
energia_red = np.trapezoid(p_red, horas)
energia_h2 = np.trapezoid(p_h2, horas)
energia_perdida = np.trapezoid(p_perdida, horas)

# Cálculos físicos base (Hidrógeno)
produccion_kg_h2 = energia_h2 / 0.05  # 50 kWh/kg
volumen_nm3_h2 = produccion_kg_h2 / 0.08988
consumo_agua_litros = produccion_kg_h2 * factor_agua

# 7. Visualización de los resultados numéricos en la interfaz
st.markdown("### Resumen energético en las 24 Horas")

# Cálculo de porcentajes sobre el total generado
pct_red = (energia_red / energia_viento) * 100 if energia_viento > 0 else 0
pct_h2 = (energia_h2 / energia_viento) * 100 if energia_viento > 0 else 0
pct_perdida = (energia_perdida / energia_viento) * 100 if energia_viento > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Energía Eólica Total posible", f"{energia_viento:.1f} MWh")
col2.metric("Inyección a Red", f"{energia_red:.1f} MWh", f"{pct_red:.1f}% del total", delta_color="off")
col3.metric("Energía para Electrólisis - H2", f"{energia_h2:.1f} MWh", f"{pct_h2:.1f}% del total", delta_color="off")
col4.metric("Energía Perdida (Curtailment)", f"{energia_perdida:.1f} MWh", f"{pct_perdida:.1f}% del total", delta_color="off")

# Lógica condicional de la ruta química seleccionada
st.markdown("### Producción de Gas (Ciclo Químico)")

if "Hidrógeno" in ruta_ptg:
    st.info(f"**Ruta Activa:** Inyección directa o Blending. El gas conserva su estado puro.")
    st.success(f"📦 Producción: **{produccion_kg_h2:.1f} kg de $H_2$** | 🎈 Volumen (0°C, 1atm): **{volumen_nm3_h2:.1f} $Nm^3$** | 💧 Demanda de Agua: **{consumo_agua_litros:.1f} L**")

elif "Metano" in ruta_ptg:
    # Cálculos de Sabatier: 4 moles H2 -> 1 mol CH4
    volumen_nm3_ch4 = volumen_nm3_h2 / 4
    produccion_kg_ch4 = produccion_kg_h2 * 1.989
    demanda_kg_co2 = produccion_kg_h2 * 5.45
    
    if "Sabatier" in ruta_ptg:
        st.warning(f"**Ruta Activa:** Reactor Sabatier. Requiere captura industrial de $CO_2$ y catalizadores metálicos (400°C).")
        st.success(f"🔥 Metano Sintético (e-NG): **{produccion_kg_ch4:.1f} kg** | 🎈 Volumen: **{volumen_nm3_ch4:.1f} $Nm^3$ de $CH_4$**")
        st.error(f"☁️ Demanda de $CO_2$ Externo: **{demanda_kg_co2:.1f} kg** | 💧 Demanda de Agua: **{consumo_agua_litros:.1f} L**")
    else:
        st.warning(f"**Ruta Activa:** Metanación Biológica (Caso Hychico). El proceso ocurre en el subsuelo mediante arqueas metanogénicas, consumiendo el $CO_2$ residual del yacimiento.")
        st.success(f"🦠 Metano Biológico in-situ: **{produccion_kg_ch4:.1f} kg** | 🎈 Volumen: **{volumen_nm3_ch4:.1f} $Nm^3$ de $CH_4$**")
        st.info(f"⛰️ $CO_2$ Consumido del yacimiento: **{demanda_kg_co2:.1f} kg** | 💧 Demanda de Agua (superficie): **{consumo_agua_litros:.1f} L**")

# Memoria Técnica
with st.expander("Bases utilizadas para la estimación"):
    st.markdown("""
    **Algoritmo de despacho de energía (EMS):**
    
    Orden de prioridad: Inyección a Red (prioridad 1) -> Electrólisis (excedentes) -> Curtailment (pérdida).

    **Parámetros adoptados para la Electrólisis**
    * Eficiencia: **50 kWh/kg de $H_2$.** 
 
    **Parámetros adoptados para la creación del Metano:**
    * **Ecuación química:** $4H_2 + CO_2 \\rightarrow CH_4 + 2H_2O$.
    En la metanación biológica, esta reacción es catalizada de forma natural por bacterias que habitan la roca de yacimientos vacíos, utilizando el $CO_2$ atrapado geológicamente.
    """)
