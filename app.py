# -*- coding: utf-8 -*-
"""
Created on Fri Nov 28 14:49:57 2025

@author: Usuario
"""

import streamlit as st
import pandas as pd
import altair as alt
from databricks import sql
import math
import numpy as np



# ==========================

# CONFIGURACIÓN DE LA APP

# ==========================

st.set_page_config(
page_title="Calculadora Coveñas",
page_icon="🧮",
layout="wide"
)

st.title("🧮 Calculadora bombas booster Coveñas")
st.write("Ingresa valores y observa resultados y gráficos en tiempo real.")

# ==========================

# PANEL DE ENTRADA

# ==========================

st.sidebar.image("logo_cenit.png", caption="Eficiencia energética", width=160)
st.sidebar.header("📡 Señales")




vis_30 = st.sidebar.number_input("Viscosidad 30", value=62.13)
vis_50 = st.sidebar.number_input("Viscosidad 50", value=20.07)
temp = st.sidebar.number_input("Temperatura", value=97.42)
numero_bombas = st.sidebar.number_input("Numero de bombas", value=7.0)
flujo = st.sidebar.number_input("Flujo", value=7153.11)
p_desc_1 = st.sidebar.number_input("Presion descarga BB1", value=112.47	)
p_desc_2 = st.sidebar.number_input("Presion descarga BB2", value=113.05	)
p_desc_3 = st.sidebar.number_input("Presion descarga BB3", value=113.18	)
p_desc_4 = st.sidebar.number_input("Presion descarga BB4", value=112.82	)
p_desc_5 = st.sidebar.number_input("Presion descarga BB5", value=112.49	)
p_desc_6 = st.sidebar.number_input("Presion descarga BB6", value=112.53)
p_desc_7 = st.sidebar.number_input("Presion descarga BB7", value=114.43)


# ==========================

# CÁLCULOS

# ==========================


def viscosidad_correcion(vis_30,vis_50, temp):

    B = (
        (math.log10(math.log10(vis_30 + 0.7)) - math.log10(math.log10(vis_50 + 0.7)))
        / (math.log10(50 + 273.15) - math.log10(30 + 273.15))
    )
    A =  (math.log10(math.log10(vis_30 + 0.7)) + B * math.log10(30 + 273.15))
    
    kelvin = (temp - 32) * 5/9 + 273.15

    viscosidad_corregida= 10 ** (10 ** (A - B * math.log10(kelvin))) - 0.7

    
    return viscosidad_corregida


## Datos_fijos

k=16.5
HBEP=	91.40910664
QBEP_W=	178.4450552
N=1770
FC=	1.424270025
PSI_Tank=0

viscosidad_corregida=viscosidad_correcion(vis_30,vis_50, temp)
B= k* ((viscosidad_corregida**0.5 * HBEP**0.0625) / (QBEP_W**0.375 * N**0.25))
Cq=math.e ** (-0.165 * (math.log10(B) ** 3.15))
ceff= B**(-0.0547 * (B ** 0.69))
flujo_bb=flujo/numero_bombas
flujo_agua=flujo_bb/Cq
flujo_m3=flujo_bb/6.28
ch= 1 - (1 - Cq) * (flujo_m3 / QBEP_W) ** 0.75
TDH_agua=-2.16572E-08*flujo_agua**3 + 3.48924E-05*flujo_agua**2 + -0.070593309*flujo_agua + 159.1672173
eficiencia_agua=5.02041E-11*flujo_agua**3 + -7.74263E-07*flujo_agua**2 + 0.001537068*flujo_agua
TDH_psig=ch*TDH_agua*FC
eficiencia=ceff*eficiencia_agua


presiones_descarga = [p_desc_1, p_desc_2, p_desc_3, p_desc_4, p_desc_5, p_desc_6, p_desc_7] 
valores_filtrados = [pres for pres in presiones_descarga if pres >= 50]
# Calcular promedio (si hay valores)
if valores_filtrados:
    promedio_si = np.mean(valores_filtrados)
else:
    promedio_si = 0  # Excel devuelve error si no hay valores, aquí lo manejamos como 0

TDH_real= (promedio_si - PSI_Tank) / ch / FC
BEP=flujo_bb/1120.634947


consumo_eje = (flujo_bb* promedio_si * 6.891 * 0.16 / 3600) / eficiencia 

try:
    factor_carga = consumo_eje / 93.2124839
except ZeroDivisionError:
    factor_carga = None
    
    
m = min(factor_carga, 1)
eficiencia_motor =  0.99078  * (m**2 +  1.83890  * m) / (m**2 +  1.89782  * m +  0.00991 )

consumo_bb=(consumo_eje*numero_bombas)/eficiencia_motor

# ==========================

# PANEL DE RESULTADOS

# ==========================

st.header("✨ Panel de Resultados")


# ==========================
# BOTÓN ACTUALIZAR GRÁFICA
# ==========================

st.header("🔄 Actualizar gráfica desde Databricks")

if st.button("Actualizar gráfica"):
    with st.spinner("Consultando Databricks y actualizando datos..."):
        try: 
                data_2025= pd.read_excel('BD_CENIT_2025.xlsx')
                df_databricks=data_2025[['Estampa de tiempo','COV_FIT_1315A', 'COV_TIT_1317A', 'COV_VIS_1314',
                                  'COV_PT_1401B', 'COV_PT_1402B', 'COV_PT_1403B', 'COV_PT_1404B',
                                  'COV_PT_1405B', 'COV_PT_1406B', 'COV_PT_1407B']]
                
                #Calculo de variables 
                viscosidad_corregida_df = df_databricks["COV_VIS_1314"]
                flujo = df_databricks["COV_FIT_1315A"]
                p_desc_1 = df_databricks["COV_PT_1401B"]
                p_desc_2 = df_databricks["COV_PT_1402B"]
                p_desc_3 = df_databricks["COV_PT_1403B"]
                p_desc_4 = df_databricks["COV_PT_1404B"]
                p_desc_5 = df_databricks["COV_PT_1405B"]
                p_desc_6 = df_databricks["COV_PT_1406B"]
                p_desc_7 = df_databricks["COV_PT_1407B"]
                
                df_databricks["B"] =  k*((viscosidad_corregida_df**0.5 * HBEP**0.0625) /
                (QBEP_W**0.375 * N**0.25))
                
                df_databricks["Cq"] = np.exp(-0.165 * (np.log10(df_databricks["B"]) ** 3.15))
    
                df_databricks["ceff"] = df_databricks["B"] ** (-0.0547 * (df_databricks["B"] ** 0.69))
    
                columnas_presiones = ["COV_PT_1401B","COV_PT_1402B","COV_PT_1403B",
                        "COV_PT_1404B","COV_PT_1405B","COV_PT_1406B","COV_PT_1407B"]
                    
                df_databricks["numero_bombas"] = (df_databricks[columnas_presiones] >= 80).sum(axis=1)
                
                
                df_databricks["flujo_bb"] = flujo / df_databricks["numero_bombas"]
                
                df_databricks["flujo_agua"] = df_databricks["flujo_bb"] / df_databricks["Cq"]
    
                df_databricks["flujo_m3"] = df_databricks["flujo_bb"] / 6.28
                
                df_databricks["ch"] = 1 - (1 - df_databricks["Cq"]) * (df_databricks["flujo_m3"] / QBEP_W) ** 0.75
                
                df_databricks["TDH_agua"] = (
                    -2.16572e-08 * df_databricks["flujo_agua"]**3 +
                    3.48924e-05 * df_databricks["flujo_agua"]**2 -
                    0.070593309 * df_databricks["flujo_agua"] +
                    159.1672173
                )
                
        
                df_databricks["eficiencia_agua"] = (
                    5.02041e-11 * df_databricks["flujo_agua"]**3 -
                    7.74263e-07 * df_databricks["flujo_agua"]**2 +
                    0.001537068 * df_databricks["flujo_agua"]
                )
                
             
                df_databricks["TDH_psig"] = df_databricks["ch"] * df_databricks["TDH_agua"] * FC
                
             
                df_databricks["eficiencia"] = df_databricks["ceff"] * df_databricks["eficiencia_agua"]
                
                df_databricks['eficiencia_porc']=df_databricks['eficiencia']*100
         
                
                columnas_presiones = [
                    "COV_PT_1401B","COV_PT_1402B","COV_PT_1403B",
                    "COV_PT_1404B","COV_PT_1405B","COV_PT_1406B","COV_PT_1407B"
                ]
                
                df_databricks["promedio_si"] = (
                    df_databricks[columnas_presiones]
                    .where(df_databricks[columnas_presiones] >= 50)
                    .mean(axis=1)
                    .fillna(0)
                )
                
                # ----- TDH_real -----
                df_databricks["TDH_real"] = (df_databricks["promedio_si"] - PSI_Tank) / df_databricks["ch"] / FC
                
                # ----- BEP -----
                df_databricks["BEP"] = df_databricks["flujo_bb"] / 1120.634947
                
                # ----- consumo_eje -----
                df_databricks["consumo_eje"] = (
                    (df_databricks["flujo_bb"] * df_databricks["promedio_si"] * 6.891 * 0.16 / 3600) / df_databricks["eficiencia"]
                )
                
                # ====== Factor de carga (evita división por cero) ======
                df_databricks["factor_carga"] = df_databricks["consumo_eje"] / 93.2124839
                df_databricks.loc[np.isinf(df_databricks["factor_carga"]), "factor_carga"] = np.nan
                
                # ----- m -----
                df_databricks["m"] = df_databricks["factor_carga"].clip(upper=1)
                
                # ----- eficiencia_motor -----
                df_databricks["eficiencia_motor"] = (
                    0.99078 * (df_databricks["m"]**2 + 1.83890 * df_databricks["m"]) /
                    (df_databricks["m"]**2 + 1.89782 * df_databricks["m"] + 0.00991)
                )
                
                # ----- Consumo total -----
                df_databricks["consumo_bb"] = (df_databricks["consumo_eje"] * numero_bombas) / df_databricks["eficiencia_motor"]
    
    
                # Guardar en session state
                st.session_state["df_databricks"] = df_databricks
        
                st.success("Datos actualizados correctamente.")
                #st.dataframe(df_databricks)

        except Exception as e:
            st.error(f"Error al ejecutar consulta: {e}")


# ==========================
# GRÁFICA SCATTER
# ==========================

st.header("📈 Gráfica: Flujo por Bomba vs TDH Real (doble eje)")

# Verificar si existe df_databricks en memoria
if "df_databricks" in st.session_state:

    df_plot = st.session_state["df_databricks"]

    # --- Scatter 1 (EJE IZQUIERDO) ---
    scatter_tdh = (
        alt.Chart(df_plot)
        .mark_circle(size=120, color="#C8DE26")
        .encode(
            x=alt.X("flujo_agua:Q", title="Flujo por Bomba [bbl/d]",scale=alt.Scale(domain=[0,1500])),
            y=alt.Y("TDH_real:Q", title="TDH Real [psig]"),
            tooltip=[
                alt.Tooltip("flujo_agua", title="Flujo Agua", format=".2f"),
                alt.Tooltip("TDH_real", title="TDH Real", format=".2f"),
            ]
        )
    )

    # --- Scatter 2 (EJE DERECHO) ---
    scatter_efic = (
        alt.Chart(df_plot)
        .mark_circle(size=120, color="#1f77b4")
        .encode(
            x=alt.X("flujo_agua:Q",scale=alt.Scale(domain=[0,1500])),
            y=alt.Y("eficiencia_porc:Q",
                    title="Eficiencia",
                    axis=alt.Axis(titleColor="#1f77b4", orient="right")),
            tooltip=[
                alt.Tooltip("flujo_agua", title="Flujo Agua", format=".2f"),
                alt.Tooltip("eficiencia_porc", title="Eficiencia", format=".3f"),
            ]
        )
    )

    # --- puntos--
    points = pd.DataFrame({
        "flujo_agua": [0, 571.4285714, 857.1428571, 1142.857143, 1428.571429],
        "eficiencia_porc": [0, 64, 77, 82.8, 76],
        "TDH_real":[159.1056, 126.7968, 109.4232, 92.6592, 66.1416] 
        })

    x_fit = points["flujo_agua"].values
    y_fit_efi = points["eficiencia_porc"].values
    y_fit_tdh=points["TDH_real"].values
    
    # Calcular coeficientes del polinomio cúbico
    coef_efi = np.polyfit(x_fit, y_fit_efi, 3)
    poly_efi = np.poly1d(coef_efi)


    coef_tdh = np.polyfit(x_fit, y_fit_tdh, 3)
    poly_tdh = np.poly1d(coef_tdh)
    
    # Generar valores suavizados para la curva
    x_graf = np.linspace(x_fit.min(), 1500, 200)
    y_graf_efi = poly_efi(x_graf)
    y_graf_tdh= poly_tdh(x_graf)
    
    # --- Línea de tendencia cúbica ---
    trend_efic = (
        alt.Chart(pd.DataFrame({"flujo_agua": x_graf, "eficiencia_porc": y_graf_efi}))
        .mark_line(color="black", strokeDash=[5,2])
        .encode(
            x="flujo_agua:Q",
            y="eficiencia_porc:Q",
        )
    )
    

    trend_tdh = (
        alt.Chart(pd.DataFrame({"flujo_agua": x_graf, "TDH_real": y_graf_tdh}))
        .mark_line(color="red", strokeDash=[5,2])
        .encode(
            x="flujo_agua:Q",
            y="TDH_real:Q",
        )
    )


    scatter_point_efic = (
        alt.Chart(points)
        .mark_point(size=200, color="black", shape="triangle-up")
        .encode(
            x="flujo_agua:Q",
            y="eficiencia_porc:Q",
            tooltip=[
                alt.Tooltip("flujo_agua", title="Flujo Agua", format=".2f"),
                alt.Tooltip("eficiencia_porc", title="Eficiencia", format=".2f"),
            ]
        )
    )
    
    
    scatter_point_tdh = (
        alt.Chart(points)
        .mark_point(size=100, color="red", shape="triangle-up")
        .encode(
            x="flujo_agua:Q",
            y="TDH_real:Q",
            tooltip=[
                alt.Tooltip("flujo_agua", title="Flujo Agua", format=".2f"),
                alt.Tooltip("TDH_real", title="TDH Real", format=".2f"),
            ]
        )
    )
    
    # --- Grupo TDH 
    tdh_group = alt.layer(
        scatter_tdh,
        trend_tdh,
        scatter_point_tdh
    )
    
    # --- Grupo Eficiencia 
    efic_group = alt.layer(
        scatter_efic,
        trend_efic,
        scatter_point_efic
    )
    
    # --- Combinar ambos grupos con doble eje
    combined_chart = alt.layer(
        tdh_group,
        efic_group
    ).resolve_scale(
        y='independent'
    )
    
    st.altair_chart(combined_chart, use_container_width=True)


else:
    st.info("🔄 Presiona **Actualizar gráfica** para cargar los datos.")


st.header("Calculos ")

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    st.info("**Consumo [kWh]**")
    st.metric(label="", value=f"{consumo_bb:.2f}")

with col2:
    st.info("**Eficiencia[%]**")
    st.metric(label="", value=f"{eficiencia*100:.2f}")

with col3:
    st.info("**BEP[%]**")
    st.metric(label="", value=f"{BEP*100:.2f}")

with col4:
    st.info("**Viscosidad corregida**")
    st.metric(label="", value=f"{viscosidad_corregida:.2f}")





