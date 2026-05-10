import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="Hibridación Eolica y H2", layout="wide")

st.title("Trabajo Final Integrador - Mauro Galliani")
st.title("Análisis de Hibridación Eólica con Hidrógeno verde")
st.markdown("Simulador de balance entre Generación eólica, Producción de H2 y sus pérdidas.")
st.markdown("(versión de prueba hasta definir objetivos del trabajo)")

# Controles en la barra lateral para mayor limpieza visual
st.sidebar.header("Parámetros del Sistema")
cap_red = st.sidebar.slider("Capacidad de la Red Eléctrica (MW)", 20, 100, 60)
cap_elec = st.sidebar.slider("Capacidad del Electrolizador (MW)", 0, 50, 20)

# Generación del perfil eólico sintético (24 horas)
# 1. Gestión de memoria para la semilla aleatoria
if 'semilla' not in st.session_state:
    st.session_state.semilla = 42  # Valor inicial por defecto

# 2. Botón para forzar una nueva semilla
if st.sidebar.button("Generar Nuevo Perfil Eólico"):
    # Genera un número entero aleatorio nuevo y lo guarda en memoria
    st.session_state.semilla = np.random.randint(0, 10000)

# 3. Generación del perfil eólico sintético (24 horas)
np.random.seed(st.session_state.semilla) # Aplica la semilla guardada
horas = np.arange(0, 25)
p_viento = 50 + 35 * np.sin(horas * np.pi / 12 - np.pi/4) + 10 * np.random.rand(25)
p_viento = np.clip(p_viento, 0, 120)

# Lógica matemática del EMS (Prioridad de despacho)
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

# 5. Cálculos de integración energética (Área bajo la curva)
# Utilizamos la regla del trapecio (np.trapezoid) para integrar MW a MWh
energia_viento = np.trapezoid(p_viento, horas)
energia_red = np.trapezoid(p_red, horas)
energia_h2 = np.trapezoid(p_h2, horas)
energia_perdida = np.trapezoid(p_perdida, horas)

# 6. Cálculo de producción física de Hidrógeno
# Asumimos una eficiencia de 50 kWh/kg (0.05 MWh/kg)
produccion_kg_h2 = energia_h2 / 0.05

# 7. Visualización de los resultados numéricos en la interfaz
st.markdown("### Resumen energético en las 24 Horas")

# Cálculo de porcentajes sobre el total generado
pct_red = (energia_red / energia_viento) * 100
pct_h2 = (energia_h2 / energia_viento) * 100
pct_perdida = (energia_perdida / energia_viento) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("Energía Eólica Total posible", f"{energia_viento:.1f} MWh")
col2.metric("Inyección a Red", f"{energia_red:.1f} MWh", f"{pct_red:.1f}% del total", delta_color="off")
col3.metric("Energía para Electrólisis", f"{energia_h2:.1f} MWh", f"{pct_h2:.1f}% del total", delta_color="off")
col4.metric("Energía Perdida (Curtailment)", f"{energia_perdida:.1f} MWh", f"{pct_perdida:.1f}% del total", delta_color="off")

st.info(f"Producción estimada de Hidrógeno Verde: **{produccion_kg_h2:.1f} kg** (Asumiendo 50 kWh/kg)")
