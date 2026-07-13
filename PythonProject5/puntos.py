"""
app.py - Interfaz Gráfica de Usuario del Simulador de Trazado Vial
Desarrollado en Streamlit con renderizado interactivo en Plotly.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sqlite3
import io
from datetime import datetime
from fpdf import FPDF
import topo_utils as topo

# Configuración Inicial de la Página
st.set_page_config(page_title="Simulador Computacional de Trazado Vial", layout="wide")

# Inicialización de Estados de Sesión (Session State)
if "fase_actual" not in st.session_state:
    st.session_state.fase_actual = 1
if "fases_completadas" not in st.session_state:
    st.session_state.fases_completadas = {i: False for i in range(1, 11)}
if "df_puntos" not in st.session_state:
    st.session_state.df_puntos = None

# Base de datos SQLite temporal local
conn = sqlite3.connect("diseños_viales.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT, ancho_via REAL, presupuesto REAL, 
        longitud REAL, corte_total REAL, relleno_total REAL
    )
""")
conn.commit()

# Título Principal
st.title("🚧 Simulador Computacional de Trazado Vial")
st.caption("Herramienta interactiva de ingeniería para el modelamiento y cubicación geométrica de vías.")

# --- BARRA LATERAL: NAVEGACIÓN SECUENCIAL ---
st.sidebar.header("Flujo Constructivo")

fases_info = {
    1: ("📥 Importación Topográfica", "Clavar los palillos iniciales"),
    2: ("🌌 Nube de Puntos 3D", "Visualizar el enjambre"),
    3: ("📐 Triangulación TIN", "Tejer la red estructural"),
    4: ("🗺️ Superficie MDE", "Ponerle arcilla al esqueleto"),
    5: ("🧱 Maqueta Sólida 3D", "Fundir el bloque de tierra"),
    6: ("⚙️ Parámetros de Diseño", "Definir las directrices viales"),
    7: ("📍 Eje Vial y Rasante", "Trazar la línea de vida"),
    8: ("🚜 Movimiento de Tierras", "Meter el tractor de oruga"),
    9: ("🗄️ Archivero Histórico", "Almacenar diseños estructurales"),
    10: ("📄 Memoria de Cálculo", "Generar certificado oficial")
}

# Dibujar Menú Lateral Dinámico
progreso = sum(1 for f in st.session_state.fases_completadas.values() if f) / 10.0
st.sidebar.progress(progreso)

for fase, (titulo, sub) in fases_info.items():
    # Validación de acceso
    if fase == 1:
        estado_icono = "✅" if st.session_state.fases_completadas[fase] else "🔓"
        deshabilitado = False
    else:
        if st.session_state.fases_completadas[fase]:
            estado_icono = "✅"
            deshabilitado = False
        elif st.session_state.fases_completadas[fase - 1]:
            estado_icono = "🔓"
            deshabilitado = False
        else:
            estado_icono = "🔒"
            deshabilitado = True

    if st.sidebar.button(f"{estado_icono} Fase {fase}: {titulo}", disabled=deshabilitado, key=f"btn_fase_{fase}"):
        st.session_state.fase_actual = fase
        st.rerun()

st.sidebar.markdown(f"**Metáfora actual:**\n*{fases_info[st.session_state.fase_actual][1]}*")

st.write("---")

# --- CONTROLADOR DE FASES ---
fase_act = st.session_state.fase_actual
st.header(f"Fase {fase_act} - {fases_info[fase_act][0]}")

# FASE 1: IMPORTACIÓN
if fase_act == 1:
    st.write("Cargue la libreta topográfica del levantamiento de campo o genere un terreno sintético de prueba.")

    col1, col2 = st.columns(2)
    with col1:
        separador = st.selectbox("Separador de datos", [",", ";", "\t", " "], format_func=lambda
            x: "Coma" if x == "," else "Punto y coma" if x == ";" else "Tabulación" if x == "\t" else "Espacio")
        archivo_cargado = st.file_uploader("Subir archivo CSV/TXT (PUNTO, X, Y, Z, CODIGO)", type=["csv", "txt"])

    with col2:
        st.write("¿No dispone de un levantamiento real?")
        if st.button("✨ Generar datos de ejemplo sintéticos"):
            idx, x, y, z, cod = topo.generar_datos_ejemplo()
            st.session_state.df_puntos = pd.DataFrame({"PUNTO": idx, "X": x, "Y": y, "Z": z, "CODIGO": cod})
            st.success("¡Datos sintéticos generados con éxito!")

    if archivo_cargado is not None:
        try:
            df = pd.read_csv(archivo_cargado, sep=separador)
            # Normalización de alias idiomáticos
            mapeo = {}
            for col in df.columns:
                col_lower = col.lower()
                if col_lower in ['x', 'este', 'easting']:
                    mapeo[col] = 'X'
                elif col_lower in ['y', 'norte', 'northing']:
                    mapeo[col] = 'Y'
                elif col_lower in ['z', 'cota', 'elevacion', 'elevación', 'z']:
                    mapeo[col] = 'Z'
                elif col_lower in ['punto', 'id']:
                    mapeo[col] = 'PUNTO'
                elif col_lower in ['codigo', 'código', 'desc']:
                    mapeo[col] = 'CODIGO'

            df = df.rename(columns=mapeo)
            st.session_state.df_puntos = df[['PUNTO', 'X', 'Y', 'Z', 'CODIGO']]
            st.success("Archivo importado y mapeado correctamente.")
        except Exception as e:
            st.error(f"Error al procesar el archivo estructurado: {e}")

    if st.session_state.df_puntos is not None:
        df = st.session_state.df_puntos
        st.dataframe(df.head(10), use_container_width=True)
        # Estadísticas métricas básicas
        c1, c2, c3 = st.columns(3)
        c1.metric("Número total de puntos", len(df))
        c2.metric("Rango de elevaciones (Z)", f"{df['Z'].min():.2f} - {df['Z'].max():.2f} m")
        c3.metric("Desnivel Máximo del Terreno", f"{(df['Z'].max() - df['Z'].min()):.2f} m")

        if st.button("Confirmar y avanzar"):
            st.session_state.fases_completadas[1] = True
            st.session_state.fase_actual = 2
            st.rerun()

# FASE 2: NUBE DE PUNTOS
elif fase_act == 2:
    df = st.session_state.df_puntos
    st.write("Representación espacial tridimensional del relieve crudo levantado en la estación total.")

    fig = go.Figure(data=[go.Scatter3d(
        x=df['X'], y=df['Y'], z=df['Z'],
        mode='markers',
        marker=dict(size=3, color=df['Z'], colorscale='Earth', showscale=True),
        hovertext=df['CODIGO']
    )])
    fig.update_layout(scene=dict(aspectmode="data"), margin=dict(l=0, r=0, b=0, t=0))
    st.plotly_chart(fig, use_container_width=True)

    if st.button("Confirmar y avanzar"):
        st.session_state.fases_completadas[2] = True
        st.session_state.fase_actual = 3
        st.rerun()

# FASE 3: TRIANGULACIÓN TIN
elif fase_act == 3:
    df = st.session_state.df_puntos
    st.write(
        "Generación de una red de triángulos irregulares (TIN) restringiendo distancias para evitar falsos puentes topográficos.")

    max_l = st.slider("Longitud límite de arista válida (m)", 10, 150, 60)

    triangulos, aristas = topo.filtrar_triangulos_delaunay(df['X'].values, df['Y'].values, max_l)
    st.session_state.triangulos_validos = triangulos
    st.write(f"Triángulos estructurales validados: {len(triangulos)}")

    # Dibujar Wireframe
    x_lines, y_lines, z_lines = [], [], []
    pts = df[['X', 'Y', 'Z']].values
    for ar in aristas:
        x_lines.extend([pts[ar[0]][0], pts[ar[1]][0], None])
        y_lines.extend([pts[ar[0]][1], pts[ar[1]][1], None])
        z_lines.extend([pts[ar[0]][2], pts[ar[1]][2], None])

    fig = go.Figure(
        data=[go.Scatter3d(x=x_lines, y=y_lines, z=z_lines, mode='lines', line=dict(color='gray', width=1))])
    fig.update_layout(scene=dict(aspectmode="data"))
    st.plotly_chart(fig, use_container_width=True)

    if st.button("Confirmar y avanzar"):
        st.session_state.fases_completadas[3] = True
        st.session_state.fase_actual = 4
        st.rerun()

# FASE 4: MDE Y CURVAS DE NIVEL
elif fase_act == 4:
    df = st.session_state.df_puntos
    st.write("Interpolación matemática regular sobre el dominio espacial válido del proyecto.")

    res = st.slider("Resolución de la malla (Celdas por eje)", 20, 100, 50)
    n_curvas = st.slider("Número de curvas de nivel", 10, 50, 25)

    gx, gy, gz = topo.generar_mde(df['X'].values, df['Y'].values, df['Z'].values, st.session_state.triangulos_validos,
                                  res)
    st.session_state.mde = (gx, gy, gz)

    fig = go.Figure(data=[go.Surface(z=gz, x=gx, y=gy, colorscale='Earth',
                                     contours_z=dict(show=True, usecolormap=True, highlightcolor="limegreen",
                                                     project_z=True))])
    fig.update_layout(scene=dict(aspectmode="data"))
    st.plotly_chart(fig, use_container_width=True)

    if st.button("Confirmar y avanzar"):
        st.session_state.fases_completadas[4] = True
        st.session_state.fase_actual = 5
        st.rerun()

# FASE 5: MAQUETA SÓLIDA 3D
elif fase_act == 5:
    gx, gy, gz = st.session_state.mde
    st.write("Extrusión volumétrica tridimensional del lecho geográfico.")

    cota_base = float(np.nanmin(gz))
    vol = topo.calcular_maqueta_volumen(gx, gy, gz, cota_base)

    st.metric("Volumen estimado de la corteza simulada", f"{vol:,.2f} m³")

    # Renderizado simplificado de superficie sólida para visualización ágil
    fig = go.Figure(data=[go.Surface(z=gz, x=gx, y=gy, colorscale='YlOrRd')])
    fig.update_layout(scene=dict(aspectmode="data"))
    st.plotly_chart(fig, use_container_width=True)

    if st.button("Confirmar y avanzar"):
        st.session_state.fases_completadas[5] = True
        st.session_state.fase_actual = 6
        st.rerun()

# FASE 6: PARAMETROS DE DISEÑO
elif fase_act == 6:
    st.write("Definición de las condiciones de diseño geométrico y restricciones presupuestarias.")

    with st.form("param_form"):
        ancho = st.number_input("Ancho de corona / calzada de la vía (m)", min_value=3.0, max_value=30.0, value=7.20)
        presupuesto = st.number_input("Presupuesto máximo de movimiento de tierra permitido (m³)", min_value=1000,
                                      value=50000)
        t_corte = st.number_input("Talud de corte (H:V - ej. 0.5)", min_value=0.1, value=0.5)
        t_relleno = st.number_input("Talud de relleno (H:V - ej. 1.5)", min_value=0.1, value=1.5)

        if st.form_submit_button("Guardar Parámetros Técnicos"):
            st.session_state.params = {"ancho": ancho, "presupuesto": presupuesto, "t_corte": t_corte,
                                       "t_relleno": t_relleno}
            st.session_state.fases_completadas[6] = True
            st.session_state.fase_actual = 7
            st.rerun()

# FASE 7: EJE VIAL Y RASANTE
elif fase_act == 7:
    df = st.session_state.df_puntos
    gx, gy, gz = st.session_state.mde
    st.write("Defina el alineamiento horizontal y vertical del eje vial interactivo.")

    # Puntos de control iniciales por defecto basados en extremos topográficos
    if "pts_control" not in st.session_state:
        st.session_state.pts_control = [
            [float(df['X'].min()), float(df['Y'].min())],
            [float(df['X'].max()), float(df['Y'].max())]
        ]

    st.write("Ulique coordenadas o modifique los puntos de control horizontales:")
    # Botones de inicio rápido
    if st.button("Inicio rápido: Desde cota mínima hacia el Norte"):
        p_min = df.loc[df['Z'].idxmin()]
        st.session_state.pts_control = [[p_min['X'], p_min['Y']], [p_min['X'], df['Y'].max()]]

    sigma = st.slider("Factor de suavizado horizontal (Filtro Gaussiano)", 0.0, 5.0, 1.5)

    # Cálculo automático de geometría del eje
    eje, pks = topo.disenar_eje_vial(st.session_state.pts_control, sigma)

    # Manejo dinámico de pendientes por tramos de 100m
    max_tramos = int(pks[-1] // 100) + 1
    pendientes = []
    st.write("#### Configuración de Pendientes Longitudinales por Tramo de 100m")
    for t_idx in range(max_tramos):
        p_val = st.number_input(f"Pendiente Tramo {t_idx * 100}m - {(t_idx + 1) * 100}m (%)", min_value=-20.0,
                                max_value=20.0, value=2.0, key=f"p_{t_idx}")
        if abs(p_val) > 12.0:
            st.warning(f"⚠️ La pendiente del {p_val}% supera la norma recomendada (Máx 12%).")
        pendientes.append(p_val)

    z_terr, z_ras = topo.calcular_perfil_y_rasante(eje, pks, df['X'].values, df['Y'].values, df['Z'].values, pendientes)

    st.session_state.eje_calculado = (eje, pks, z_terr, z_ras, pendientes)

    # Graficar Perfil Longitudinal 2D
    fig_perfil = go.Figure()
    fig_perfil.add_trace(go.Scatter(x=pks, y=z_terr, name="Terreno Natural", line=dict(color='brown', dash='dash')))
    fig_perfil.add_trace(go.Scatter(x=pks, y=z_ras, name="Subrasante Proyectada", line=dict(color='red', width=3)))
    fig_perfil.update_layout(title="Perfil Longitudinal de Diseño Vertical", xaxis_title="Progresiva (Abscisado)",
                             yaxis_title="Cota (m)")
    st.plotly_chart(fig_perfil, use_container_width=True)

    if st.button("Confirmar Trazado Lineal"):
        st.session_state.fases_completadas[7] = True
        st.session_state.fase_actual = 8
        st.rerun()

# FASE 8: CUBICACIÓN (METER EL TRACTOR)
elif fase_act == 8:
    eje, pks, z_terr, z_ras, pendientes = st.session_state.eje_calculado
    p = st.session_state.params
    df = st.session_state.df_puntos

    st.write("Cálculo formal de áreas y volúmenes acumulados mediante el método de las ordenadas medias (prismatoide).")

    a_c, a_r, v_c, v_r = topo.cubicacion_obra_tierra(pks, z_terr, z_ras, p['ancho'], p['t_corte'], p['t_relleno'])
    v_total = v_c[-1] + v_r[-1]

    # Validación presupuestaria de tierras
    if v_total > p['presupuesto']:
        idx_limite = np.where((v_c + v_r) > p['presupuesto'])[0][0]
        pk_limite = pks[idx_limite]
        st.error(
            f"🚨 El diseño propuesto requiere {v_total:,.2f} m³ y excede el presupuesto físico de {p['presupuesto']:,.2f} m³.")
        st.error(f"La obra alcanza viabilidad presupuestaria únicamente hasta el PK: {pk_limite:.2f} m.")
    else:
        st.success(f"✅ ¡Volumen total compatible con el presupuesto del proyecto! ({v_total:,.2f} m³ utilizados).")

    st.session_state.resultados_cubicacion = (v_c[-1], v_r[-1], v_total)

    # Mostrar Gráfico de Volúmenes Acumulados
    fig_v = go.Figure()
    fig_v.add_trace(go.Scatter(x=pks, y=v_c, name="Corte Acumulado (m³)", fill='tozeroy'))
    fig_v.add_trace(go.Scatter(x=pks, y=v_r, name="Relleno Acumulado (m³)", fill='tozeroy'))
    st.plotly_chart(fig_v, use_container_width=True)

    if st.button("Confirmar Modelamiento Físico"):
        st.session_state.fases_completadas[8] = True
        st.session_state.fase_actual = 9
        st.rerun()

# FASE 9: ARCHIVERO HISTÓRICO SQLITE3
elif fase_act == 9:
    st.write("Base de datos interna de registros históricos de diseños confirmados.")

    vc, vr, vt = st.session_state.resultados_cubicacion
    p = st.session_state.params
    _, pks, _, _, _ = st.session_state.eje_calculado

    if st.button("💾 Guardar Configuración Actual en Base de Datos"):
        cursor.execute(
            "INSERT INTO proyectos (fecha, ancho_via, presupuesto, longitud, corte_total, relleno_total) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), p['ancho'], p['presupuesto'], float(pks[-1]), vc, vr))
        conn.commit()
        st.success("Diseño indexado con firma electrónica temporal.")

    st.write("### Historial de simulaciones en este equipo:")
    historial = pd.read_sql_query("SELECT * FROM proyectos ORDER BY id DESC", conn)
    st.dataframe(historial, use_container_width=True)

    if st.button("Avanzar a la fase final"):
        st.session_state.fases_completadas[9] = True
        st.session_state.fase_actual = 10
        st.rerun()

# FASE 10: MEMORIA DE CÁLCULO PDF
elif fase_act == 10:
    st.write("Generación y exportación de la memoria técnica de cálculo legal.")

    # Preparación de datos del PDF
    p = st.session_state.params
    vc, vr, vt = st.session_state.resultados_cubicacion
    _, pks, _, _, pendientes = st.session_state.eje_calculado

    # Lógica del PDF usando fpdf2
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "MEMORIA TÉCNICA DE CÁLCULO VIAL", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 10, f"Fecha de emisión del informe: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Longitud Proyectada Total de la Vía: {pks[-1]:.2f} m", ln=True)
    pdf.cell(0, 10, f"Ancho de Calzada Establecido: {p['ancho']:.2f} m", ln=True)
    pdf.cell(0, 10, f"Volumen Total de Corte: {vc:,.2f} m³", ln=True)
    pdf.cell(0, 10, f"Volumen Total de Relleno: {vr:,.2f} m³", ln=True)

    pdf_bytes = pdf.output()

    st.download_button(
        label="📥 Descargar Memoria de Cálculo Formal (PDF)",
        data=bytes(pdf_bytes),
        file_name="Memoria_Diseno_Vial.pdf",
        mime="application/pdf"
    )

    st.balloons()