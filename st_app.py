# app.py (actualizado)
import json
import os
import sys
from datetime import datetime, timedelta

import mysql.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Ex3.mysql_queries import queries
from Ex4.comments_neo4j import Neo4jCommentSystem
from Ex5.doc_mongodb import MongoDBPlantDocumentSystem

with open("Ex6/style.css") as file:
    st.markdown(
        f"""
        <style>
        {file.read()}
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_connection_config():
    try:
        with open("connection.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Archivo connection.json no encontrado")
        return None


def init_mysql_connection(config):
    try:
        return mysql.connector.connect(**config)
    except Exception as e:
        st.error(f"Error conectando a MySQL: {e}")
        return None


def init_mongodb_system(config):
    try:
        return MongoDBPlantDocumentSystem(config["uri"], config["database"])
    except Exception as e:
        st.error(f"Error conectando a MongoDB: {e}")
        return None


def init_neo4j_system(config):
    try:
        return Neo4jCommentSystem(config["uri"], config["user"], config["password"])
    except Exception as e:
        st.error(f"Error conectando a Neo4j: {e}")
        return None


def setup_page():
    st.set_page_config(page_title="GreenScape Dashboard", layout="wide", page_icon="🌿")
    st.title("🌿 GreenScape Dashboard")


def render_sidebar():
    st.sidebar.title("Navegación")
    section = st.sidebar.radio(
        "Selecciona una sección:",
        [
            "Consultas SQL",
            "Análisis de Usuario",
            "Conversaciones",
            "Documentos",
            "Gestor de Precios",
        ],
    )

    conn_config = st.session_state.connection_config
    if conn_config:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Estado de Conexiones")
        st.sidebar.write(
            f"✅ MySQL: {conn_config['mysql']['host']}:{conn_config['mysql'].get('port', 3306)}"
        )
        st.sidebar.write(f"✅ MongoDB: Conectado")
        st.sidebar.write(f"✅ Neo4j: Conectado")

    return section


def execute_query(cursor, query):
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error ejecutando consulta: {e}")
        return []


def render_query_section():
    st.header("Selector de Consultas SQL")

    special_queries_tabs = ["Consulta Ñ", "Consulta O", "Consulta P", "Consulta Q"]
    selected_tab = st.selectbox(
        "Selecciona tipo de consulta:", ["Generales"] + special_queries_tabs
    )

    if selected_tab == "Generales":
        selected_query = st.selectbox("Selecciona una consulta:", list(queries.keys()))
        query_text = queries[selected_query]

        st.code(query_text, language="sql")

        if st.button("Ejecutar Consulta General"):
            cursor = st.session_state.mysql_conn.cursor(dictionary=True)
            results = execute_query(cursor, query_text)

            if results:
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)

                if selected_query == "h) Distribución edades":
                    fig = px.pie(
                        df,
                        values="Cantidad",
                        names="Rango_Edad",
                        title="Distribución de Usuarios por Edad",
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("La consulta no devolvió resultados.")

    elif selected_tab == "Consulta Ñ":
        st.subheader("Trigger de Auditoría de Precios")

        cursor = st.session_state.mysql_conn.cursor(dictionary=True)

        cursor.execute("SELECT IDProd, Nombre, Precio FROM Producto ORDER BY Nombre")
        productos = cursor.fetchall()

        producto_dict = {
            f"{p['IDProd']} - {p['Nombre']}": p["IDProd"] for p in productos
        }

        selected_product_name = st.selectbox(
            "Selecciona un producto:", list(producto_dict.keys())
        )
        selected_product_id = producto_dict[selected_product_name]

        cursor.execute(
            "SELECT Precio FROM Producto WHERE IDProd = %s", (selected_product_id,)
        )
        current_price = cursor.fetchone()["Precio"]

        st.metric("Precio Actual", f"${current_price:.2f}")

        new_price = st.number_input(
            "Nuevo Precio:", min_value=0.0, value=float(current_price), step=0.1
        )

        if st.button("Probar Trigger - Actualizar Precio"):
            try:
                cursor.execute(
                    "UPDATE Producto SET Precio = %s WHERE IDProd = %s",
                    (new_price, selected_product_id),
                )
                st.session_state.mysql_conn.commit()
                st.success(
                    "Precio actualizado! El trigger debería haber registrado el cambio."
                )

                st.markdown("---")
                st.subheader("Historial de Auditoría Reciente")

                try:
                    cursor.execute("SHOW TABLES LIKE 'Historial_Precios'")
                    table_exists = cursor.fetchone()

                    if table_exists:
                        cursor.execute(
                            """
                            SELECT * FROM Historial_Precios
                            WHERE IDProd = %s
                            ORDER BY FechaCambio DESC
                            LIMIT 10
                        """,
                            (selected_product_id,),
                        )

                        historial = cursor.fetchall()

                        if historial:
                            df_historial = pd.DataFrame(historial)
                            st.dataframe(df_historial, use_container_width=True)

                            if len(historial) > 1:
                                fig = px.line(
                                    df_historial,
                                    x="FechaCambio",
                                    y="PrecioNuevo",
                                    title="Historial de Cambios de Precio",
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No hay historial de cambios para este producto.")
                    else:
                        st.warning(
                            "La tabla Historial_Precios no existe. Creando trigger..."
                        )

                        create_trigger_sql = """
                        CREATE TABLE IF NOT EXISTS Historial_Precios (
                            IDHistorial INT AUTO_INCREMENT PRIMARY KEY,
                            IDProd INT NOT NULL,
                            PrecioAnterior DECIMAL(10,2),
                            PrecioNuevo DECIMAL(10,2),
                            PorcentajeCambio DECIMAL(5,2),
                            FechaCambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (IDProd) REFERENCES Producto(IDProd) ON DELETE CASCADE
                        );
                        """

                        cursor.execute(create_trigger_sql)

                        trigger_sql = """
                        CREATE TRIGGER IF NOT EXISTS auditoria_precios
                        AFTER UPDATE ON Producto
                        FOR EACH ROW
                        BEGIN
                            IF OLD.Precio != NEW.Precio THEN
                                INSERT INTO Historial_Precios (IDProd, PrecioAnterior, PrecioNuevo, PorcentajeCambio)
                                VALUES (
                                    NEW.IDProd,
                                    OLD.Precio,
                                    NEW.Precio,
                                    ROUND(((NEW.Precio - OLD.Precio) / OLD.Precio) * 100, 2)
                                );
                            END IF;
                        END;
                        """

                        cursor.execute(trigger_sql)
                        st.session_state.mysql_conn.commit()
                        st.success("Tabla y trigger creados exitosamente.")

                except Exception as trigger_error:
                    st.error(f"Error al verificar/crear el trigger: {trigger_error}")

            except Exception as e:
                st.error(f"Error actualizando precio: {e}")

        st.markdown("---")
        st.subheader("Ver Todo el Historial de Auditoría")

        if st.button("Cargar Todo el Historial"):
            try:
                cursor.execute("""
                    SELECT hp.*, p.Nombre as Producto
                    FROM Historial_Precios hp
                    JOIN Producto p ON hp.IDProd = p.IDProd
                    ORDER BY hp.FechaCambio DESC
                    LIMIT 50
                """)

                all_history = cursor.fetchall()

                if all_history:
                    df_all = pd.DataFrame(all_history)
                    st.dataframe(df_all, use_container_width=True)

                    fig = px.scatter(
                        df_all,
                        x="FechaCambio",
                        y="PrecioNuevo",
                        color="Producto",
                        title="Historial de Precios de Todos los Productos",
                        hover_data=["PrecioAnterior", "PorcentajeCambio"],
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay registros en el historial de auditoría.")

            except Exception as e:
                st.error(f"Error cargando historial: {e}")

    elif selected_tab == "Consulta O":
        st.subheader("Procedimiento Almacenado: Análisis de Usuario")

        col1, col2, col3 = st.columns(3)
        with col1:
            user_id = st.number_input(
                "ID Usuario:", min_value=1, value=1, step=1, key="proc_user"
            )
        with col2:
            start_date = st.date_input("Fecha Inicio:", key="proc_start")
        with col3:
            end_date = st.date_input("Fecha Fin:", key="proc_end")

        if st.button("Ejecutar Procedimiento"):
            try:
                cursor = st.session_state.mysql_conn.cursor(dictionary=True)

                cursor.execute(
                    "SHOW PROCEDURE STATUS WHERE Db = 'GreenScape' AND Name = 'sp_analisis_usuario'"
                )
                proc_exists = cursor.fetchone()

                if not proc_exists:
                    st.warning("El procedimiento almacenado no existe. Creándolo...")

                    create_proc_sql = """
                    CREATE PROCEDURE sp_analisis_usuario(
                        IN p_id_usuario INT,
                        IN p_fecha_inicio DATE,
                        IN p_fecha_fin DATE
                    )
                    BEGIN
                        DECLARE total_publicaciones INT;
                        DECLARE total_reacciones_recibidas INT;
                        DECLARE total_comentarios_recibidos INT;
                        DECLARE total_compras INT;
                        DECLARE total_gastado DECIMAL(10,2);

                        SELECT COUNT(*) INTO total_publicaciones
                        FROM Publicacion
                        WHERE IDU = p_id_usuario;

                        SELECT COUNT(*) INTO total_reacciones_recibidas
                        FROM Reaccionar r
                        JOIN Publicacion p ON r.IDPub = p.IDPub
                        WHERE p.IDU = p_id_usuario;

                        SELECT COUNT(*) INTO total_comentarios_recibidos
                        FROM Comentar c
                        JOIN Publicacion p ON c.IDPub = p.IDPub
                        WHERE p.IDU = p_id_usuario;

                        SELECT COUNT(*), COALESCE(SUM(Cantidad * Precio), 0)
                        INTO total_compras, total_gastado
                        FROM Compra
                        WHERE IDUC = p_id_usuario
                        AND Fecha BETWEEN p_fecha_inicio AND p_fecha_fin;

                        SELECT
                            p_id_usuario as ID_Usuario,
                            total_publicaciones as Total_Publicaciones,
                            total_reacciones_recibidas as Total_Reacciones_Recibidas,
                            total_comentarios_recibidos as Total_Comentarios_Recibidos,
                            total_compras as Total_Compras,
                            total_gastado as Total_Gastado;
                    END;
                    """

                    cursor.execute(create_proc_sql)
                    st.session_state.mysql_conn.commit()
                    st.success("Procedimiento creado exitosamente.")

                cursor.callproc("sp_analisis_usuario", [user_id, start_date, end_date])

                for result in cursor.stored_results():
                    results = result.fetchall()
                    if results:
                        df = pd.DataFrame(results)
                        st.dataframe(df, use_container_width=True)

                        metrics_df = df.drop(columns=["ID_Usuario"]).T.reset_index()
                        metrics_df.columns = ["Metrica", "Valor"]

                        fig = go.Figure(
                            data=[
                                go.Bar(x=metrics_df["Metrica"], y=metrics_df["Valor"])
                            ]
                        )
                        fig.update_layout(title="Métricas del Usuario")
                        st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error ejecutando procedimiento: {e}")

    elif selected_tab == "Consulta P":
        st.subheader("Análisis de Influencers")

        if st.button("Identificar Influencers"):
            cursor = st.session_state.mysql_conn.cursor(dictionary=True)

            query = """
            SELECT
                u.IDU,
                u.Nombre,
                u.Email,
                COUNT(DISTINCT p.IDPub) as total_publicaciones,
                COUNT(DISTINCT r.IDU) as total_reacciones_recibidas,
                COUNT(DISTINCT c.IDU) as total_comentarios_recibidos
            FROM Usuario u
            LEFT JOIN Publicacion p ON u.IDU = p.IDU
            LEFT JOIN Reaccionar r ON p.IDPub = r.IDPub
            LEFT JOIN Comentar c ON p.IDPub = c.IDPub
            GROUP BY u.IDU, u.Nombre, u.Email
            ORDER BY total_reacciones_recibidas DESC
            LIMIT 5
            """

            results = execute_query(cursor, query)

            if results:
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)

                fig = px.bar(
                    df,
                    x="Nombre",
                    y=["total_publicaciones", "total_reacciones_recibidas"],
                    title="Top 5 Influencers",
                    barmode="group",
                )
                st.plotly_chart(fig, use_container_width=True)

    elif selected_tab == "Consulta Q":
        st.subheader("Detección de Patrones Sospechosos")

        if st.button("Analizar Vendedores"):
            cursor = st.session_state.mysql_conn.cursor(dictionary=True)

            query = """
            SELECT
                c.IDUV as id_vendedor,
                u.Nombre,
                COUNT(DISTINCT c.IDProd) as productos_vendidos,
                AVG(c.Puntuacion) as promedio_calificacion,
                STDDEV(c.Puntuacion) as desviacion_calificacion,
                COUNT(DISTINCT c.IDUC) as compradores_unicos
            FROM Compra c
            JOIN Usuario u ON c.IDUV = u.IDU
            GROUP BY c.IDUV, u.Nombre
            HAVING COUNT(DISTINCT c.IDProd) > 1
            ORDER BY desviacion_calificacion DESC
            """

            results = execute_query(cursor, query)

            if results:
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)

                df["indice_sospecha"] = (
                    df["desviacion_calificacion"]
                    * df["productos_vendidos"]
                    / df["compradores_unicos"]
                )

                fig = px.scatter(
                    df,
                    x="productos_vendidos",
                    y="desviacion_calificacion",
                    size="indice_sospecha",
                    color="promedio_calificacion",
                    hover_data=["Nombre"],
                    title="Análisis de Vendedores",
                )
                st.plotly_chart(fig, use_container_width=True)


def render_user_analysis_section():
    st.header("Análisis de Usuario")

    col1, col2, col3 = st.columns(3)

    with col1:
        user_id = st.number_input(
            "ID de Usuario:", min_value=1, value=1, step=1, key="analysis_user"
        )

    with col2:
        start_date = st.date_input(
            "Fecha Inicio:",
            value=datetime.now() - timedelta(days=365),
            key="analysis_start",
        )

    with col3:
        end_date = st.date_input("Fecha Fin:", value=datetime.now(), key="analysis_end")

    if st.button("Analizar Usuario", key="analyze_user"):
        cursor = st.session_state.mysql_conn.cursor(dictionary=True)

        st.subheader("Métricas del Usuario")
        metrics_cols = st.columns(4)

        with metrics_cols[0]:
            cursor.execute(
                """
                SELECT COUNT(*) as total
                FROM Publicacion
                WHERE IDU = %s
            """,
                (user_id,),
            )
            publications = cursor.fetchone()["total"]
            st.metric("Publicaciones", publications)

        with metrics_cols[1]:
            cursor.execute(
                """
                SELECT COUNT(DISTINCT IDProd) as total
                FROM Compra
                WHERE IDUC = %s AND Fecha BETWEEN %s AND %s
            """,
                (user_id, start_date, end_date),
            )
            purchases = cursor.fetchone()["total"]
            st.metric("Compras", purchases)

        with metrics_cols[2]:
            cursor.execute(
                """
                SELECT COUNT(*) as total
                FROM Comentar
                WHERE IDU = %s
            """,
                (user_id,),
            )
            comments = cursor.fetchone()["total"]
            st.metric("Comentarios", comments)

        with metrics_cols[3]:
            cursor.execute(
                """
                SELECT COUNT(*) as total
                FROM Reaccionar
                WHERE IDU = %s
            """,
                (user_id,),
            )
            reactions = cursor.fetchone()["total"]
            st.metric("Reacciones", reactions)

        st.markdown("---")
        st.subheader("Publicaciones del Usuario")

        cursor.execute(
            """
            SELECT p.IDPub, p.Texto, COUNT(r.IDU) as Reacciones
            FROM Publicacion p
            LEFT JOIN Reaccionar r ON p.IDPub = r.IDPub
            WHERE p.IDU = %s
            GROUP BY p.IDPub, p.Texto
            ORDER BY Reacciones DESC
        """,
            (user_id,),
        )

        user_posts = cursor.fetchall()
        if user_posts:
            df_posts = pd.DataFrame(user_posts)
            st.dataframe(df_posts, use_container_width=True)

            if len(user_posts) > 1:
                fig = go.Figure(
                    data=[
                        go.Bar(
                            x=[p["IDPub"] for p in user_posts],
                            y=[p["Reacciones"] for p in user_posts],
                        )
                    ]
                )
                fig.update_layout(title="Reacciones por Publicación")
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Historial de Compras")

        cursor.execute(
            """
            SELECT p.Nombre, c.Fecha, c.Cantidad, c.Precio,
                   c.Cantidad * c.Precio as Total
            FROM Compra c
            JOIN Producto p ON c.IDProd = p.IDProd
            WHERE c.IDUC = %s AND c.Fecha BETWEEN %s AND %s
            ORDER BY c.Fecha DESC
        """,
            (user_id, start_date, end_date),
        )

        user_purchases = cursor.fetchall()
        if user_purchases:
            df_purchases = pd.DataFrame(user_purchases)
            st.dataframe(df_purchases, use_container_width=True)

            total_spent = sum(row["Total"] for row in user_purchases)
            st.metric("Total Gastado", f"${total_spent:.2f}")


def render_conversations_section():
    st.header("Gestión de Conversaciones")

    if not st.session_state.neo4j_system:
        st.error("Sistema Neo4j no disponible")
    else:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Crear Comentario")

            user_id = st.number_input(
                "ID Usuario:", min_value=1, value=1, step=1, key="new_comment_user"
            )
            publication_id = st.number_input(
                "ID Publicación:", min_value=1, value=1, step=1, key="new_comment_pub"
            )
            parent_comment = st.number_input(
                "ID Comentario Padre (opcional):",
                min_value=0,
                value=0,
                step=1,
                key="new_comment_parent",
            )

            if parent_comment == 0:
                parent_comment = None

            comment_text = st.text_area(
                "Texto del Comentario:", height=100, key="new_comment_text"
            )

            if st.button("Crear Comentario", key="create_comment"):
                try:
                    st.session_state.neo4j_system.create_comment(
                        user_id, publication_id, comment_text, parent_comment
                    )
                    st.success("Comentario creado exitosamente!")
                except Exception as e:
                    st.error(f"Error creando comentario: {e}")

        with col2:
            st.subheader("Explorar Conversaciones")

            comment_id = st.number_input(
                "ID Comentario Raíz:",
                min_value=1,
                value=1,
                step=1,
                key="explore_comment",
            )

            if st.button("Cargar Conversación", key="load_conversation"):
                try:
                    conversation = st.session_state.neo4j_system.get_full_conversation(
                        comment_id
                    )

                    if conversation:
                        st.markdown(f"### Conversación #{comment_id}")
                        st.markdown(f"**Autor:** {conversation['autor_inicial']}")
                        st.markdown(f"**Texto:** {conversation['texto_inicial']}")

                        st.markdown("---")
                        st.subheader("Respuestas:")

                        for resp in conversation["todas_respuestas"]:
                            indent = "&nbsp;" * 20 * resp["nivel"]
                            st.markdown(
                                f"""
                            <div style="margin-left: {resp["nivel"] * 40}px; border-left: 2px solid #ccc; padding-left: 10px; margin-bottom: 10px;">
                                <strong>{resp["autor"]}</strong> (Nivel {resp["nivel"]}):<br>
                                {resp["texto"]}
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                except Exception as e:
                    print(e)


def render_documents_section():
    st.header("Explorador de Documentos")

    if not st.session_state.mongodb_system:
        st.error("Sistema MongoDB no disponible")
    else:
        tab1, tab2 = st.tabs(["Explorar", "Subir"])

        with tab1:
            plant_id = st.number_input(
                "ID de Planta:", min_value=1, value=1, step=1, key="explore_plant"
            )

            if st.button("Cargar Documentos", key="load_docs"):
                try:
                    documents = st.session_state.mongodb_system.get_plant_documents(
                        plant_id
                    )

                    if documents:
                        st.markdown(f"### Planta #{plant_id}")

                        if documents["main_document"]:
                            with st.expander("📋 Documento Principal", expanded=True):
                                doc = documents["main_document"]
                                st.write(f"**Nombre:** {doc['filename']}")
                                st.write(f"**Tipo:** {doc['type']}")
                                st.write(f"**Tamaño:** {doc['size']} bytes")

                                if doc.get("metadata"):
                                    st.json(doc["metadata"])

                        if documents["secondary_documents"]:
                            st.markdown(
                                f"### 📚 Documentos Secundarios ({len(documents['secondary_documents'])})"
                            )

                            for doc in documents["secondary_documents"]:
                                with st.expander(f"{doc['type']} - {doc['filename']}"):
                                    st.write(f"**ID:** {doc['id']}")
                                    st.write(f"**Tamaño:** {doc['size']} bytes")
                                    st.write(f"**Creado:** {doc['created']}")
                except Exception as e:
                    st.error(f"Error cargando documentos: {e}")

        with tab2:
            st.subheader("Subir Documento")

            doc_plant_id = st.number_input(
                "ID Planta:", min_value=1, value=1, step=1, key="upload_plant"
            )
            doc_type = st.selectbox(
                "Tipo:",
                [
                    "Ficha Tecnica",
                    "Certificado Fitosanitario",
                    "Guía de Riego Estacional",
                    "Manual de Tratamiento de Plagas",
                    "Historial de Crecimiento",
                    "Análisis de Suelo",
                ],
                key="doc_type",
            )

            doc_title = st.text_input("Título:", key="doc_title")
            doc_content = st.text_area("Contenido:", height=200, key="doc_content")

            if st.button("Guardar", key="save_doc"):
                try:
                    if doc_type == "Ficha Tecnica":
                        st.session_state.mongodb_system.insert_main_document(
                            plant_id=doc_plant_id,
                            content=doc_content,
                            filename=f"{doc_title}.json",
                            plant_data={"titulo": doc_title},
                        )
                    else:
                        st.session_state.mongodb_system.insert_secondary_document(
                            plant_id=doc_plant_id,
                            tipo_documento=doc_type,
                            content=doc_content,
                            filename=f"{doc_title}.txt",
                            metadata={"titulo": doc_title},
                        )

                    st.success("Documento guardado!")
                except Exception as e:
                    st.error(f"Error: {e}")


def render_price_manager_section():
    st.header("Gestor de Precios")

    cursor = st.session_state.mysql_conn.cursor(dictionary=True)

    cursor.execute("SELECT IDProd, Nombre, Precio FROM Producto ORDER BY Nombre")
    products = cursor.fetchall()

    product_dict = {f"{p['IDProd']} - {p['Nombre']}": p["IDProd"] for p in products}

    selected_product_name = st.selectbox("Producto:", list(product_dict.keys()))
    selected_product_id = product_dict[selected_product_name]

    cursor.execute(
        "SELECT Precio FROM Producto WHERE IDProd = %s", (selected_product_id,)
    )
    current_price = cursor.fetchone()["Precio"]

    st.metric("Precio Actual", f"${current_price:.2f}")

    new_price = st.number_input(
        "Nuevo Precio:",
        min_value=0.0,
        value=float(current_price),
        step=0.1,
        key="new_price",
    )

    if st.button("Actualizar", key="update_price"):
        try:
            cursor.execute(
                "UPDATE Producto SET Precio = %s WHERE IDProd = %s",
                (new_price, selected_product_id),
            )
            st.session_state.mysql_conn.commit()
            st.success("Precio actualizado!")

            cursor.execute(
                """
                SELECT * FROM Historial_Precios
                WHERE IDProd = %s
                ORDER BY FechaCambio DESC
            """,
                (selected_product_id,),
            )

            history = cursor.fetchall()

            if history:
                df = pd.DataFrame(history)
                st.dataframe(df, use_container_width=True)

                if len(history) > 1:
                    fig = px.line(
                        df,
                        x="FechaCambio",
                        y="PrecioNuevo",
                        title="Historial de Precios",
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay historial.")

        except Exception as e:
            st.error(f"Error: {e}")


def main():
    setup_page()

    if "connection_config" not in st.session_state:
        config = load_connection_config()
        if config:
            st.session_state.connection_config = config
            st.session_state.mysql_conn = init_mysql_connection(config["mysql"])
            st.session_state.mongodb_system = init_mongodb_system(config["mongodb"])
            st.session_state.neo4j_system = init_neo4j_system(config["neo4j"])
        else:
            st.error("No se pudo cargar la configuración")
            return

    section = render_sidebar()

    if not st.session_state.mysql_conn:
        st.error("No hay conexión a MySQL")
        return

    if section == "Consultas SQL":
        render_query_section()
    elif section == "Análisis de Usuario":
        render_user_analysis_section()
    elif section == "Conversaciones":
        render_conversations_section()
    elif section == "Documentos":
        render_documents_section()
    elif section == "Gestor de Precios":
        render_price_manager_section()


if __name__ == "__main__":
    main()
