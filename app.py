import streamlit as st
import pandas as pd
import plotly.express as px
from main import extract_sql_data, audit_data, load_data_to_sql, SERVER_NAME, DATABASE_NAME

st.set_page_config(page_title="Data Quality Pipeline", layout="wide")

def main():
    st.markdown("""
        <style>
        .main-header { font-size: 2.5rem; font-weight: 800; color: #4f46e5; margin-bottom: 0;}
        .sub-header { font-size: 1.1rem; color: #6b7280; margin-bottom: 2rem;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="main-header">Automated Data Quality Pipeline</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Motor Automatizado de Auditoría e Integridad de Datos</p>', unsafe_allow_html=True)

    df_raw = extract_sql_data(SERVER_NAME, DATABASE_NAME)

    if df_raw is not None:
        df_clean, df_corrupt = audit_data(df_raw)
        
        total = len(df_raw) 
        total_clean = len(df_clean)
        total_corrupt = len(df_corrupt)
        salud = (total_clean / total) * 100 if total > 0 else 0

        with st.sidebar:
            st.title("Panel de Control")
            st.markdown("---")
            
            st.subheader("Base de Datos")
            if st.button("Sincronizar con SQL Server", type="primary", use_container_width=True):
                with st.spinner("Indexando registros en SQL Server..."):
                    load_data_to_sql(df_clean, df_corrupt, SERVER_NAME, DATABASE_NAME)
                st.success("Tablas actualizadas en BD.")
            
            st.markdown("---")
            if st.button("Recalcular Métricas", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
                
            st.markdown("---")
            st.info("El sistema separa registros huérfanos y los aísla para mantener el Single Source of Truth impecable.")

        if salud >= 90:
            st.success(f"ESTADO GLOBAL: ÓPTIMO | Nivel de Confiabilidad: {salud:.1f}%")
        elif salud >= 70:
            st.warning(f"ESTADO GLOBAL: MODERADO | Nivel de Confiabilidad: {salud:.1f}% (Requiere revisión)")
        else:
            st.error(f"ESTADO GLOBAL: CRÍTICO | Nivel de Confiabilidad: {salud:.1f}% (Intervención requerida)")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Volumen Procesado", f"{total:,}", "Filas leídas")
        col2.metric("Data Confiable", f"{total_clean:,}", f"{salud:.1f}% del total")
        col3.metric("Anomalías Aisladas", f"{total_corrupt:,}", f"{(100-salud):.1f}% de merma", delta_color="inverse")
        col4.metric("Tablas en Riesgo", "1", "dbo.VentasCrudas")

        st.markdown("<br>", unsafe_allow_html=True)

        tab_dash, tab_data, tab_export = st.tabs(["Dashboard Analítico", "Visor de Data", "Extracción de Lotes"])

        with tab_dash:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("#### Distribución de Salud de Datos")
                fig_health = px.pie(
                    names=['Data Validada', 'Data Corrupta'],
                    values=[total_clean, total_corrupt],
                    hole=0.6,
                    color_discrete_sequence=['#10b981', '#ef4444']
                )
                fig_health.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350)
                st.plotly_chart(fig_health, use_container_width=True)

            with col_chart2:
                st.markdown("#### Frecuencia de Anomalías por Producto")
                if not df_corrupt.empty:
                    df_chart = df_corrupt['Producto'].fillna('NULL_VALUE').value_counts().reset_index()
                    df_chart.columns = ['Producto', 'Impacto']
                    fig_bar = px.bar(
                        df_chart, 
                        x='Impacto', 
                        y='Producto', 
                        orientation='h',
                        color='Impacto', 
                        color_continuous_scale='Reds',
                        text='Impacto'
                    )
                    fig_bar.update_layout(
                        margin=dict(t=20, b=20, l=20, r=20), 
                        height=350,
                        yaxis={'categoryorder':'total ascending'}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("No se detectaron anomalías en dimensiones de producto.")

        with tab_data:
            st.markdown("#### Matriz de Inspección de Registros")
            vista_opcion = st.radio(
                "Filtro de visualización:", 
                ["Anomalías Detectadas (Cuarentena)", "Data Validada (Apta para BI)"], 
                horizontal=True
            )

            if "Anomalías" in vista_opcion:
                st.dataframe(df_corrupt.reset_index(drop=True), height=400, use_container_width=True)
            else:
                st.dataframe(df_clean.reset_index(drop=True), height=400, use_container_width=True)

        with tab_export:
            st.markdown("#### Centro de Extracción y Respaldo")
            st.write("Genera archivos planos (.csv) de los lotes procesados para auditorías externas.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            
            csv_raw = df_raw.to_csv(index=False).encode('utf-8')
            csv_clean = df_clean.to_csv(index=False).encode('utf-8')
            csv_corrupt = df_corrupt.to_csv(index=False).encode('utf-8')
            
            b1.download_button("Descargar Lote Original", data=csv_raw, file_name='RAW_ventas.csv', mime='text/csv', use_container_width=True)
            b2.download_button("Descargar Lote Validado", data=csv_clean, file_name='CLEAN_ventas.csv', mime='text/csv', use_container_width=True)
            b3.download_button("Descargar Matriz de Errores", data=csv_corrupt, file_name='CORRUPT_ventas.csv', mime='text/csv', use_container_width=True)

    else:
        st.error("Fallo crítico: No se pudo establecer conexión con la instancia de SQL Server. Revise las credenciales y el estado del motor.")

if __name__ == "__main__":
    main()