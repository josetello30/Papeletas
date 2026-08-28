import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración general
st.set_page_config(page_title="Dashboard de Infracciones", layout="wide")
st.title("Análisis de Papeletas de Tránsito (Ene - Jun 2026)")
st.write("Datos extraidos de la Municipalidad Provincial de Arequipa - MPA")

# 2. Carga y Limpieza de datos optimizada para CSV
@st.cache_data
def load_data():
    archivo = 'Lista de Papeletas impuestas en la fecha de Enero a Junio del 2026 -MPA_0.csv'
    df = pd.read_csv(archivo, sep=';', encoding='latin1')
    df['Fecha Papeleta'] = pd.to_datetime(df['Fecha Papeleta'])
    
    # --- PROCESO DE LIMPIEZA PARA 'Lugar de Intervencion' ---
    if 'Lugar de Intervencion' in df.columns:
        # 1. Convertir a mayúsculas, quitar espacios a los lados y limpiar espacios dobles
        df['Lugar de Intervencion'] = df['Lugar de Intervencion'].astype(str).str.upper().str.strip()
        df['Lugar de Intervencion'] = df['Lugar de Intervencion'].replace(r'\s+', ' ', regex=True)
        
        # 2. Quitar los puntos después de "AV" o "CALLE" para estandarizar
        df['Lugar de Intervencion'] = df['Lugar de Intervencion'].str.replace('AV.', 'AV', regex=False)
        
        # 3. Diccionario de normalización para agrupar las variantes
        reemplazos = {
            'AV ANDRES A. CACERES - J.L.B. Y RIVERO': 'AV ANDRES AVELINO CACERES',
            'AV ANDRES A. CACERES - GRATERSA - J.L.B. Y RIVERO': 'AV ANDRES AVELINO CACERES',
            'AV ANDRES A. CACERES - J. L. B. Y RIVERO': 'AV ANDRES AVELINO CACERES',
            'AV ANDRES AVELINO C.': 'AV ANDRES AVELINO CACERES',
            'AV AVELINO C.': 'AV ANDRES AVELINO CACERES',
            'AV VIDAURRAZAGA - J.L.B. Y RIVERO': 'AV VIDAURRAZAGA'
        }
        
        # 4. Aplicar el reemplazo
        df['Lugar de Intervencion'] = df['Lugar de Intervencion'].replace(reemplazos)
        
    return df

try:
    df = load_data()

    # 3. Panel Lateral: Filtros
    st.sidebar.header("Filtros de Análisis")
    
    calificaciones = df['Calificacion'].dropna().unique().tolist()
    calificacion_sel = st.sidebar.multiselect("Gravedad de Infracción:", calificaciones, default=calificaciones)
    
    estados = df['Estado Papeleta'].dropna().unique().tolist()
    estado_sel = st.sidebar.multiselect("Estado de la Papeleta:", estados, default=estados)

    # Aplicar los filtros
    df_filtrado = df[
        (df['Calificacion'].isin(calificacion_sel)) &
        (df['Estado Papeleta'].isin(estado_sel))
    ].copy()

    # 4. Indicadores Clave
    st.subheader("Indicadores Generales")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Papeletas (Filtradas)", f"{len(df_filtrado):,}")
    
    if not df_filtrado.empty:
        infraccion_comun = df_filtrado['Codigo Infraccion'].mode()[0]
        zona_comun = df_filtrado['Lugar de Intervencion'].mode()[0]
    else:
        infraccion_comun = "N/A"
        zona_comun = "N/A"
        
    col2.metric("Infracción Frecuente", infraccion_comun)
    col3.metric("Lugar más intervenido", zona_comun[:25] + "..." if isinstance(zona_comun, str) and len(zona_comun) > 25 else str(zona_comun))

    # 5. Gráficos Interactivos
    st.divider()
    
    # --- GRÁFICO 1: Zonas con más papeletas (Fila 1 - Ancho Completo) ---
    st.subheader("📍 Análisis por Ubicación")
    if not df_filtrado.empty:
        top_zonas = df_filtrado['Lugar de Intervencion'].value_counts().head(15).reset_index()
        top_zonas.columns = ['Lugar de Intervención', 'Cantidad']
        top_zonas = top_zonas.sort_values('Cantidad', ascending=True)
        
        fig_zonas = px.bar(
            top_zonas, 
            x='Cantidad', 
            y='Lugar de Intervención', 
            orientation='h', 
            text_auto=True, 
            color='Cantidad', 
            color_continuous_scale='Blues',
            title="Top 15 Zonas con Mayor Cantidad de Papeletas"
        )
        st.plotly_chart(fig_zonas, use_container_width=True)
    
    st.divider()
    
    # --- GRÁFICOS 2 y 3: Gravedad y Estado de Pago (Fila 2 - Dividida en 2 columnas) ---
    st.subheader("Detalles y Estado de las Infracciones")
    colA, colB = st.columns(2)
    
    with colA:
        if not df_filtrado.empty:
            conteo_calif = df_filtrado['Calificacion'].value_counts().reset_index()
            conteo_calif.columns = ['Calificacion', 'Cantidad']
            fig_pie_calif = px.pie(
                conteo_calif, 
                names='Calificacion', 
                values='Cantidad', 
                hole=0.4, 
                color_discrete_sequence=px.colors.qualitative.Set2,
                title="Distribución por Gravedad"
            )
            st.plotly_chart(fig_pie_calif, use_container_width=True)

    with colB:
        if not df_filtrado.empty:
            conteo_estado = df_filtrado['Estado Papeleta'].value_counts().reset_index()
            conteo_estado.columns = ['Estado', 'Cantidad']
            
            # Asignamos verde para pagada y rojo/naranja para pendiente
            colores_estado = {'PAGADA': '#00CC96', 'PENDIENTE': '#EF553B'}
            
            fig_pie_estado = px.pie(
                conteo_estado, 
                names='Estado', 
                values='Cantidad', 
                hole=0.4, 
                color='Estado',
                color_discrete_map=colores_estado,
                title="Porcentaje de Papeletas: Pagadas vs Pendientes"
            )
            fig_pie_estado.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie_estado, use_container_width=True)

    st.divider()

    # --- GRÁFICOS 4 y 5: Top Códigos y Evolución Temporal (Fila 3 - Dividida en 2 columnas) ---
    st.subheader("Códigos Frecuentes y Análisis Temporal")
    colC, colD = st.columns(2)
    
    with colC:
        if not df_filtrado.empty:
            top_infrac = df_filtrado['Codigo Infraccion'].value_counts().head(10).reset_index()
            top_infrac.columns = ['Código', 'Cantidad']
            fig_bar = px.bar(
                top_infrac, 
                x='Código', 
                y='Cantidad', 
                text_auto=True, 
                color='Cantidad', 
                color_continuous_scale='Reds',
                title="Top 10 Códigos de Infracción"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with colD:
        if not df_filtrado.empty:
            df_filtrado['Mes'] = df_filtrado['Fecha Papeleta'].dt.to_period('M').astype(str)
            tendencia = df_filtrado.groupby('Mes').size().reset_index(name='Cantidad')
            fig_line = px.line(
                tendencia, 
                x='Mes', 
                y='Cantidad', 
                markers=True,
                title="Tendencia Mensual de Papeletas Impuestas"
            )
            fig_line.update_layout(yaxis=dict(rangemode='tozero'))
            st.plotly_chart(fig_line, use_container_width=True)

    # 6. Tabla de datos
    st.divider()
    st.subheader("Vista Previa del Dataset")
    st.dataframe(df_filtrado.head(50), use_container_width=True)

except Exception as e:
    st.error(f"Error cargando los datos. Detalle: {e}")