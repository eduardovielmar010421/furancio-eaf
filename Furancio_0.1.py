import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="Furancio EAF - Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 1rem; padding-left: 2rem; padding-right: 2rem; }
        .stApp { background-color: #0b0f19; color: #c9d1d9; }
        [data-testid="stSidebar"] { background-color: #161b22; }
        h1, h2, h3, h4 { color: #f0f6fc; }
        .stTabs [data-baseweb="tab-list"] { gap: 20px; }
        .stTabs [data-baseweb="tab"] { height: 50px; background-color: #161b22; border-radius: 4px 4px 0px 0px; padding: 10px 20px; color: #c9d1d9; }
        .stTabs [aria-selected="true"] { background-color: #0d1321; border-bottom: 2px solid #58a6ff; color: #58a6ff !important; font-weight: bold; }
        
        /* Estilos de Tarjetas e Indicadores */
        .kpi-card { background-color: #0d1321; border: 1px solid #30363d; border-radius: 8px; padding: 12px; text-align: center; margin-bottom: 10px; }
        .kpi-title { color: #8b949e; font-size: 11px; text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }
        .kpi-value { color: #58a6ff; font-size: 18px; font-weight: bold; margin: 0; }
        .live-card { background: linear-gradient(135deg, #1f242d 0%, #0d1321 100%); border: 1px solid #58a6ff; border-radius: 8px; padding: 14px; margin-bottom: 15px; }
        .section-header { color: #8b949e; font-size: 13px; font-weight: bold; border-bottom: 1px solid #21262d; padding-bottom: 4px; margin-top: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("Furancio EAF hola jeje equisde - Consola Analítica")

try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    client = None

# ==========================================
# 2. CARGA DE DATOS
# ==========================================
@st.cache_data
def load_data():
    try:
        df_escorias = pd.read_excel("Escorias.xlsx", header=11, engine='openpyxl')
        df_reporte = pd.read_excel("reporteporcolada.xlsx", header=17, engine='openpyxl')
        df_toda = pd.read_excel("Todalainfo.xlsx", header=13, engine='openpyxl')
        return df_escorias, df_reporte, df_toda
    except Exception as e:
        st.error(f"🛑 Error crítico al leer los archivos Excel: {e}")
        st.stop()

df_escorias, df_reporte, df_toda = load_data()

# ==========================================
# 3. VALIDACIÓN Y LIMPIEZA DE COLUMNAS
# ==========================================
COL_TECNICO = 'Jefe de Produccion' 
COL_GRADO = 'Grado Obtenido'

if COL_TECNICO not in df_toda.columns or COL_GRADO not in df_toda.columns:
    st.error(f"❌ No se encuentran las columnas requeridas en Todalainfo.xlsx")
    st.stop()

df_toda[COL_TECNICO] = df_toda[COL_TECNICO].astype(str).str.strip()
df_toda[COL_GRADO] = df_toda[COL_GRADO].astype(str).str.strip()

# ==========================================
# 4. SEGMENTADORES (FILTROS)
# ==========================================
st.sidebar.header("Filtros / Segmentadores")

lista_tecnicos = df_toda[COL_TECNICO].dropna().unique().tolist()
tecnicos_seleccionados = st.sidebar.multiselect("Filtrar por Técnico:", options=lista_tecnicos, default=lista_tecnicos)

lista_grados = df_toda[COL_GRADO].dropna().unique().tolist()
grados_seleccionados = st.sidebar.multiselect("Filtrar por Grado:", options=lista_grados, default=lista_grados)

df_filtrado = df_toda[
    (df_toda[COL_TECNICO].isin(tecnicos_seleccionados)) &
    (df_toda[COL_GRADO].isin(grados_seleccionados))
]

# ==========================================
# 5. CÁLCULO DE KPIs Y EN VIVO
# ==========================================
col_colada_rep = 'No.Colada' if 'No.Colada' in df_reporte.columns else 'No. Colada'
col_grado_rep = 'Grado Acero' if 'Grado Acero' in df_reporte.columns else COL_GRADO

ultima_colada = "N/D"
grado_ultima = "N/D"

if len(df_reporte) > 0 and col_colada_rep in df_reporte.columns and col_grado_rep in df_reporte.columns:
    df_valido_rep = df_reporte.dropna(subset=[col_colada_rep, col_grado_rep])
    if len(df_valido_rep) > 0:
        ultima_colada = df_valido_rep.iloc[-1][col_colada_rep]
        grado_ultima = str(df_valido_rep.iloc[-1][col_grado_rep]).strip()

if (ultima_colada == "N/D" or grado_ultima in ["N/D", "nan", "NaN"]) and len(df_filtrado) > 0:
    ultima_colada = df_filtrado.iloc[-1].get('No. Colada', "N/D")
    grado_ultima = str(df_filtrado.iloc[-1].get(COL_GRADO, "N/D")).strip()

if grado_ultima in ["nan", "NaN", ""]:
    grado_ultima = "N/D"

suma_tpqb = df_filtrado['TPQB[+]'].sum() if 'TPQB[+]' in df_filtrado.columns else 0
prom_rdmto = df_filtrado['% RDMTO'].mean() if '% RDMTO' in df_filtrado.columns else 0
prom_vac_vac = df_filtrado['Min VAC/VAC'].mean() if 'Min VAC/VAC' in df_filtrado.columns else 0
prom_kwh_tcm = df_filtrado['KWh TCM[+]'].mean() if 'KWh TCM[+]' in df_filtrado.columns else 0
prom_kwh_tpqb = df_filtrado['KWh TPQB'].mean() if 'KWh TPQB' in df_filtrado.columns else 0
prom_tpqb_col = df_filtrado['TPQB/Col'].mean() if 'TPQB/Col' in df_filtrado.columns else 0
prom_aux = df_filtrado['Min Aux'].mean() if 'Min Aux' in df_filtrado.columns else 0
total_coladas_analizadas = len(df_filtrado)

# ==========================================
# 6. INTERFAZ PRINCIPAL (3 COLUMNAS)
# ==========================================
col1, col2, col3 = st.columns([1.1, 2.0, 1.0])

with col1:
    st.subheader("Planta en Tiempo Real")
    st.markdown(f"""
        <div class="live-card">
            <div class="kpi-title">Última Colada Procesada</div>
            <div style="font-size: 24px; font-weight: bold; color: #f0f6fc; margin: 2px 0;">#{ultima_colada}</div>
            <div class="kpi-title" style="margin-top: 8px;">Grado de Acero</div>
            <div style="font-size: 15px; font-weight: 600; color: #3fb950;">{grado_ultima}</div>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Métricas e Indicadores")
    st.markdown('<div class="section-header">Producción y Rendimiento</div>', unsafe_allow_html=True)
    g1_c1, g1_c2 = st.columns(2)
    with g1_c1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Suma TPQB Total</div>
                <div class="kpi-value">{suma_tpqb:,.1f} t</div>
            </div>
        """, unsafe_allow_html=True)
    with g1_c2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Prom. TPQB / Col</div>
                <div class="kpi-value">{prom_tpqb_col:,.1f} t</div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown(f"""
        <div class="kpi-card" style="margin-bottom: 15px;">
            <div class="kpi-title">Promedio % Rendimiento Chatarra (%RDMTO)</div>
            <div class="kpi-value" style="color:#3fb950;">{prom_rdmto:.2f}%</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Tiempos de Ciclo</div>', unsafe_allow_html=True)
    g2_c1, g2_c2 = st.columns(2)
    with g2_c1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Prom. VAC / VAC</div>
                <div class="kpi-value">{prom_vac_vac:.1f} min</div>
            </div>
        """, unsafe_allow_html=True)
    with g2_c2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Prom. Tiempo Aux</div>
                <div class="kpi-value">{prom_aux:.1f} min</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Consumos Eléctricos</div>', unsafe_allow_html=True)
    g3_c1, g3_c2 = st.columns(2)
    with g3_c1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Prom. KWh TCM</div>
                <div class="kpi-value">{prom_kwh_tcm:,.1f}</div>
            </div>
        """, unsafe_allow_html=True)
    with g3_c2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Prom. KWh TPQB</div>
                <div class="kpi-value">{prom_kwh_tpqb:,.1f}</div>
            </div>
        """, unsafe_allow_html=True)

with col2:
    st.subheader("Dashboard Furancio")
    tab_proceso, tab_produccion, tab_escoria = st.tabs(["🔥 Proceso EAF", "📊 Producción", "🧪 Análisis Escoria"])
    
    with tab_proceso:
        if 'No. Colada' in df_filtrado.columns and 'KWh TPQB' in df_filtrado.columns and 'KWh TCM[+]' in df_filtrado.columns:
            df_linea = df_filtrado.sort_values(by='No. Colada')
            df_melted = df_linea.melt(
                id_vars=['No. Colada'],
                value_vars=['KWh TPQB', 'KWh TCM[+]'],
                var_name='Métrica',
                value_name='KWh'
            )
            fig_linea = px.line(
                df_melted, x='No. Colada', y='KWh', color='Métrica',
                title="Comportamiento por Colada: KWh TPQB y KWh TCM",
                template="plotly_dark", markers=False
            )
            fig_linea.add_hline(y=340, line_dash="dash", line_color="#8b949e", layer="below")
            fig_linea.add_hline(y=360, line_dash="dash", line_color="#f85149", layer="below")
            fig_linea.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=380)
            st.plotly_chart(fig_linea, use_container_width=True)
        else:
            st.info("💡 Las columnas requeridas para el gráfico de líneas no están disponibles.")
            
    with tab_produccion:
        conteo_prod = df_filtrado[COL_TECNICO].value_counts().reset_index()
        conteo_prod.columns = ['Técnico', 'Total de Coladas']
        fig_prod = px.bar(
            conteo_prod, x='Técnico', y='Total de Coladas', text='Total de Coladas',
            title="Rendimiento: Volumen de Coladas por Operador",
            template="plotly_dark", color_discrete_sequence=['#58a6ff']
        )
        fig_prod.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
        st.plotly_chart(fig_prod, use_container_width=True)

    with tab_escoria:
        st.dataframe(df_escorias.head(10), use_container_width=True, hide_index=True)

with col3:
    st.subheader("Asesor IA (Gemini)")
    
    with st.container(height=720):
        
        prompt_maestro = f"""
Actúa como un Ingeniero Metalurgista Senior y Asesor de Operaciones experto en la optimización de Hornos de Arco Eléctrico (EAF) y Acería. 
Analiza de manera integral los datos operativos y estadísticos actuales de la planta bajo los filtros aplicados:

[CONTEXTO DE PLANTA Y ESTADÍSTICAS FILTRADAS]
- Total de coladas bajo análisis en este filtro: {total_coladas_analizadas}
- Última Colada Procesada: #{ultima_colada} (Grado de Acero: {grado_ultima})
- Promedio de Consumo Energético KWh / TPQB: {prom_kwh_tpqb:.1f} (Límites operativos de referencia: 340 - 360 KWh)
- Promedio de Consumo Energético KWh / TCM: {prom_kwh_tcm:.1f}
- Promedio de Rendimiento de Chatarra (% RDMTO): {prom_rdmto:.2f}%
- Promedio de Tiempo Vaciado a Vaciado (Min VAC/VAC): {prom_vac_vac:.1f} min
- Promedio de Tiempos Auxiliares (Min Aux): {prom_aux:.1f} min
- Producción Total Acumulada (TPQB): {suma_tpqb:,.1f} t
- Promedio por Colada (TPQB/Col): {prom_tpqb_col:,.1f} t

[INSTRUCCIÓN CRÍTICA PARA EL DÍA A DÍA]
No me des descripciones obvias. Proporciona un diagnóstico operativo conciso, accionable y de alto valor industrial dividido exactamente en:
1. **Análisis de Desviación Energética y Tiempos**: Evalúa si el KWh/TPQB está rebasando o cumpliendo el rango óptimo (340-360) y el impacto de los tiempos VAC/VAC o Auxiliares.
2. **Impacto en Rendimiento**: Relaciona el % de rendimiento de chatarra con la estabilidad del proceso.
3. **Acción Correctiva Inmediata para el Turno**: Una recomendación táctica y directa enfocada a la práctica de horno que el jefe de turno o los operadores deban aplicar hoy mismo para mejorar eficiencia o cuidar refractario/energía.
"""

        if st.button("🔄 Generar Diagnóstico"):
            with st.spinner("Analizando operación de acería..."):
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_maestro,
                    )
                    st.session_state["diagnostico"] = response.text
                except Exception:
                    st.session_state["diagnostico"] = "⏳ Servidor saturado, intenta de nuevo."
        
        if "diagnostico" in st.session_state:
            st.markdown(f'<div style="background-color:#161b22; padding:12px; border-radius:6px; border: 1px solid #30363d; margin-bottom: 10px;"><p style="color:#c9d1d9; font-size:12px; margin:0; white-space: pre-wrap;">{st.session_state["diagnostico"]}</p></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        user_request = st.text_input("💬 Pregunta al Asesor:", key="chat")
        if st.button("✉️ Enviar"):
            if user_request:
                with st.spinner("Procesando consulta técnica..."):
                    try:
                        chat_prompt = f"{prompt_maestro}\n\n[CONSULTA ESPECÍFica DEL OPERADOR/INGENIERO]\n{user_request}\n\nResponde con rigor técnico, enfoque operativo de piso y brevedad."
                        chat_res = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=chat_prompt
                        )
                        st.session_state["chat_respuesta"] = chat_res.text
                    except Exception:
                        st.error("Conexión rechazada.")
                        
        if "chat_respuesta" in st.session_state:
            st.info(st.session_state["chat_respuesta"])

# ==========================================
# 7. TABLA INFERIOR
# ==========================================
st.markdown("---")
with st.expander("🔍 Ver base de datos filtrada (Todalainfo.xlsx)"):
    st.dataframe(df_filtrado, use_container_width=True)
