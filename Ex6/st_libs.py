import os
import sys

from typing_extensions import Any

sys.path.append("Ex3")
sys.path.append("Ex4")
sys.path.append("Ex5")

import json

import mysql.connector as mq
import mysql_queries as queries
import pandas as pd
import streamlit as st

with open("connection.json", "r") as file:
    db_connection = json.load(file)


def get_db_connection(connection=db_connection):
    return mq.connect(**connection)


def mysql_run_query(
    query: str, connection: dict[str, Any] = db_connection
) -> list[tuple]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    return results


def mysql_get_query_results(inciso: str):
    """Corre las queries del ejercicio y retorna una tabla en pandas"""
    query = queries.queries[inciso]
    columns = queries.columns[inciso]
    results = mysql_run_query(query)
    if results:
        col_amount = len(results[0])
        if len(columns) < col_amount:
            columns = list(range(1, col_amount + 1))
        return pd.DataFrame(results, columns=columns)


def query_selector_section():
    st.markdown("## 📊 Selector de Consultas SQL")
    st.markdown(
        "Selecciona una consulta del ejercicio 3 para ejecutarla y visualizar los resultados."
    )
    options = {
        "a) Listar todos los productos disponibles": "a",
        "b) Contar las reacciones por publicación": "b",
        "c) Tipos de plantas preferidos": "c",
        "d) Usuarios activos en contribuciones y reacciones": "d",
        "e) Publicaciones más populares": "e",
        "f) Contribuciones constantes": "f",
        "g) Promedio de actividad": "g",
        "h) Distribución de edades": "h",
        "i) Productos sin incremento en ventas mensuales": "i",
        "j) Tendencias de contribución según clima": "j",
        "k) Cambio de preferencia en categorías": "k",
        "l) Compras contradictorias": "l",
        "m) Usuarios de solo texto": "m",
        "n) Vendedores mejor calificados": "n",
        "ñ) Trigger de auditoría de precios": "ñ",
        "o) Procedimiento almacenado - Análisis de usuario": "o",
        "p) Análisis de influencers": "p",
        "q) Detección de patrones anómalos": "q",
    }

    selected_query = st.selectbox(
        "Selecciona una consulta:", list(options.keys()), key="query_selector"
    )
    selected_query = options[selected_query]

    col1, col2 = st.columns(2)
    with col1:
        execute_button = st.button("🚀 Ejecutar Consulta", use_container_width=True)
    with col2:
        clear_button = st.button("🧹 Limpiar Resultados", use_container_width=True)
    if execute_button:
        with st.spinner("Ejecutando consulta..."):
            st.session_state.query_results = mysql_get_query_results(selected_query)
            st.success("✅ Consulta ejecutada correctamente.")
    if st.session_state.query_results is not None:
        st.markdown("### 📋 Resultados de la Consulta")
        st.dataframe(
            st.session_state.query_results, use_container_width=True, height=400
        )
        col_stats1, col_stats2 = st.columns(2)
        with col_stats1:
            st.metric("Total Filas", len(st.session_state.query_results))
        with col_stats2:
            st.metric("Total Columnas", len(st.session_state.query_results.columns))
    else:
        st.warning("Ningun elemento coincide con esta consulta")
    if clear_button and st.session_state.query_results is not None:
        st.session_state.query_results = None
        st.rerun()


def create_sidebar():
    with st.sidebar:
        st.markdown(
            """
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="color: #0a5c36; margin-bottom: 0;">🌿</h1>
            <h2 style="color: #0a5c36; margin-top: 0;">GreenScape</h2>
            <p style="color: #2e7d32; font-size: 14px;">Plataforma de Análisis de Datos</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        page_options = {
            "🏠 Dashboard": "Dashboard",
            "📊 Consultas SQL": "Consultas SQL",
            "👤 Análisis de Usuario": "Análisis de Usuario",
            "💬 Conversaciones": "Conversaciones",
            "📚 Documentos": "Documentos",
            "💰 Gestor de Precios": "Gestor de Precios",
            "⚙️ Configuración": "Configuración",
        }

        for icon_text, page_name in page_options.items():
            if st.button(
                icon_text,
                key=f"nav_{page_name}",
                use_container_width=True,
                type="secondary"
                if st.session_state.current_page != page_name
                else "primary",
            ):
                st.session_state.current_page = page_name
                st.rerun()

        st.markdown("---")

        connection_status = "🟢 Conectado" if get_db_connection() else "🔴 Desconectado"
        st.markdown(f"**Base de datos:** {connection_status}")

        st.markdown("**Métricas:**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("👥 **2,548**")
            st.caption("Usuarios")
        with col2:
            st.markdown("🌿 **1,235**")
            st.caption("Plantas")

        st.markdown("---")

        st.markdown(f"**Página actual:** {st.session_state.current_page}")

        if st.button("🔄 Recargar Página", use_container_width=True):
            st.rerun()


def conversation_management_section():
    st.markdown("## 💬 Gestión de Conversaciones")
    st.markdown("Crea y navega por hilos de conversación en los comentarios.")
