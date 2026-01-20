import json

import mysql.connector as mq
import mysql_queries as queries
import pandas as pd
import streamlit as st

with open("connection.json", "r") as file:
    db_connection = json.load(file)


def get_db_connection(connection=db_connection):
    return mq.connect(**connection["mysql"])


def mysql_run_query(query: str) -> list[tuple]:
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


def handle_query_trigger_auditoria():
    st.markdown("## 🔧 Trigger de Auditoría de Precios")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = DATABASE() AND trigger_name = 'auditoria_precios'"
    )
    trigger_exists = cursor.fetchone()[0] > 0

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Historial_Precios (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            IDProd INT NOT NULL,
            Precio_Anterior FLOAT,
            Precio_Nuevo FLOAT,
            Fecha_Cambio DATETIME DEFAULT CURRENT_TIMESTAMP,
            Porcentaje_Cambio FLOAT,
            FOREIGN KEY (IDProd) REFERENCES Producto(IDProd)
        );
    """)
    create_trigger_query = """
        CREATE TRIGGER auditoria_precios
        AFTER UPDATE ON Producto
        FOR EACH ROW
        BEGIN
            IF OLD.Precio <> NEW.Precio THEN
                INSERT INTO Historial_Precios (IDProd, Precio_Anterior, Precio_Nuevo, Porcentaje_Cambio)
                VALUES (
                    NEW.IDProd,
                    OLD.Precio,
                    NEW.Precio,
                    ROUND(((NEW.Precio - OLD.Precio) / OLD.Precio * 100), 2)
                );
            END IF;
        END
    """
    with st.expander("Query Code"):
        st.code(create_trigger_query)
    if not trigger_exists:
        try:
            cursor.execute("SET GLOBAL log_bin_trust_function_creators = 1;")
            cursor.execute(create_trigger_query)
            st.success("✅ Trigger creado exitosamente.")
        except Exception as e:
            st.warning(f"⚠️ No se pudo crear el trigger automático: {str(e)[:100]}")

    st.markdown("### 📋 Lista de Productos con Precios Actuales")
    cursor.execute("SELECT IDProd, Nombre, Precio FROM Producto ORDER BY Nombre")
    productos = cursor.fetchall()

    if productos:
        df_productos = pd.DataFrame(
            productos, columns=["ID", "Producto", "Precio Actual"]
        )
        st.dataframe(df_productos, use_container_width=True)

        st.markdown("### ✏️ Modificar Precio de Producto")

        col1, col2 = st.columns(2)
        with col1:
            selected_id = st.selectbox(
                "Selecciona un producto:",
                options=[f"{p[0]} - {p[1]}" for p in productos],
                key="product_select",
            )
            selected_id = int(selected_id.split(" - ")[0])

            cursor.execute(
                "SELECT Precio FROM Producto WHERE IDProd = %s", (selected_id,)
            )
            current_price = cursor.fetchone()[0]
            st.metric("Precio Actual", f"${current_price:.2f}")

        with col2:
            new_price = st.number_input(
                "Nuevo Precio:",
                min_value=0.01,
                value=float(current_price),
                step=0.01,
                format="%.2f",
                key="new_price_input",
            )

        if st.button(
            "💾 Actualizar Precio",
            key="update_price",
            disabled=(current_price == new_price),
        ):
            try:
                cursor.execute(
                    "SELECT Precio FROM Producto WHERE IDProd = %s", (selected_id,)
                )
                old_price = cursor.fetchone()[0]

                percent_change = 0
                if old_price > 0:
                    percent_change = round(
                        ((new_price - old_price) / old_price * 100), 2
                    )

                cursor.execute(
                    "UPDATE Producto SET Precio = %s WHERE IDProd = %s",
                    (new_price, selected_id),
                )

                conn.commit()
                st.success(
                    f"✅ Precio actualizado exitosamente de \${old_price:.2f} a \${new_price:.2f}"
                )

                st.markdown("### 📜 Historial de Cambios de Precio")
                cursor.execute(
                    """
                    SELECT
                        Fecha_Cambio,
                        Precio_Anterior,
                        Precio_Nuevo,
                        Porcentaje_Cambio
                    FROM Historial_Precios
                    WHERE IDProd = %s
                    ORDER BY Fecha_Cambio DESC
                """,
                    (selected_id,),
                )

                historial = cursor.fetchall()
                if historial:
                    df_historial = pd.DataFrame(
                        historial,
                        columns=[
                            "Fecha y Hora",
                            "Precio Anterior",
                            "Precio Nuevo",
                            "% Cambio",
                        ],
                    )
                    st.dataframe(df_historial, use_container_width=True)

                else:
                    st.info("No hay historial de cambios para este producto.")

            except Exception as e:
                st.error(f"❌ Error al actualizar el precio: {str(e)}")

        st.markdown("### 📊 Tabla Completa de Auditoría")

        cursor.execute("""
            SELECT
                hp.IDProd,
                p.Nombre AS Producto,
                hp.Precio_Anterior,
                hp.Precio_Nuevo,
                hp.Fecha_Cambio,
                hp.Porcentaje_Cambio
            FROM Historial_Precios hp
            JOIN Producto p ON hp.IDProd = p.IDProd
            ORDER BY hp.Fecha_Cambio DESC
            LIMIT 50
        """)

        audit_data = cursor.fetchall()
        if audit_data:
            df_audit = pd.DataFrame(
                audit_data,
                columns=[
                    "ID Producto",
                    "Producto",
                    "Precio Anterior",
                    "Precio Nuevo",
                    "Fecha",
                    "% Cambio",
                ],
            )
            st.dataframe(df_audit, use_container_width=True)

            if len(df_audit) > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Cambios", len(audit_data))
                with col2:
                    avg_change = df_audit["% Cambio"].mean()
                    st.metric("Cambio Promedio", f"{avg_change:.1f}%")
                with col3:
                    most_changed_idx = df_audit["% Cambio"].abs().idxmax()
                    most_changed = df_audit.loc[most_changed_idx]
                    st.metric("Mayor Cambio", f"{most_changed['% Cambio']:.1f}%")

    cursor.close()
    conn.close()


def handle_query_stored_procedure():
    st.markdown("## 👤 Análisis de Actividad de Usuario")
    st.markdown(
        "Utiliza el procedimiento almacenado para analizar la actividad de un usuario en un período específico."
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get list of users for dropdown
    cursor.execute("SELECT IDU, Nombre FROM Usuario ORDER BY Nombre")
    usuarios = cursor.fetchall()

    # Create enhanced analysis function with time series data
    def analizar_usuario_con_series_temporales(user_id, fecha_inicio, fecha_fin):
        """Enhanced analysis function that includes time series data"""
        results = {}
        time_series_data = {}

        # Convert dates to string for SQL queries
        fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
        fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")

        # 1. Time series: Publications over time (using reaction dates as proxy)
        try:
            cursor.execute(
                """
                    SELECT
                        DATE(r.Fecha) as Dia,
                        COUNT(DISTINCT p.IDPub) as Publicaciones
                    FROM Publicacion p
                    LEFT JOIN Reaccionar r ON p.IDPub = r.IDPub
                    WHERE p.IDU = %s
                        AND r.Fecha BETWEEN %s AND %s
                    GROUP BY DATE(r.Fecha)
                    ORDER BY Dia
                """,
                (user_id, fecha_inicio_str, fecha_fin_str),
            )
            publications_ts = cursor.fetchall()
            if publications_ts:
                time_series_data["publicaciones"] = publications_ts
        except Exception as e:
            st.warning(f"No se pudieron obtener datos de publicaciones: {str(e)[:100]}")

        # 2. Time series: Reactions given over time
        try:
            cursor.execute(
                """
                    SELECT
                        DATE(Fecha) as Dia,
                        COUNT(*) as Reacciones_Dadas,
                        COUNT(CASE WHEN Tipo IN ('Me gusta', 'Me encanta', 'Me asombra', 'Me divierte') THEN 1 END) as Positivas,
                        COUNT(CASE WHEN Tipo IN ('Me enoja', 'Me entristece') THEN 1 END) as Negativas
                    FROM Reaccionar
                    WHERE IDU = %s
                        AND Fecha BETWEEN %s AND %s
                    GROUP BY DATE(Fecha)
                    ORDER BY Dia
                """,
                (user_id, fecha_inicio_str, fecha_fin_str),
            )
            reactions_given_ts = cursor.fetchall()
            if reactions_given_ts:
                time_series_data["reacciones_dadas"] = reactions_given_ts
        except Exception as e:
            st.warning(
                f"No se pudieron obtener datos de reacciones dadas: {str(e)[:100]}"
            )

        # 3. Time series: Reactions received over time
        try:
            cursor.execute(
                """
                    SELECT
                        DATE(r.Fecha) as Dia,
                        COUNT(*) as Reacciones_Recibidas,
                        COUNT(CASE WHEN r.Tipo IN ('Me gusta', 'Me encanta', 'Me asombra', 'Me divierte') THEN 1 END) as Positivas,
                        COUNT(CASE WHEN r.Tipo IN ('Me enoja', 'Me entristece') THEN 1 END) as Negativas
                    FROM Reaccionar r
                    JOIN Publicacion p ON r.IDPub = p.IDPub
                    WHERE p.IDU = %s
                        AND r.Fecha BETWEEN %s AND %s
                    GROUP BY DATE(r.Fecha)
                    ORDER BY Dia
                """,
                (user_id, fecha_inicio_str, fecha_fin_str),
            )
            reactions_received_ts = cursor.fetchall()
            if reactions_received_ts:
                time_series_data["reacciones_recibidas"] = reactions_received_ts
        except Exception as e:
            st.warning(
                f"No se pudieron obtener datos de reacciones recibidas: {str(e)[:100]}"
            )

        # 4. Time series: Comments over time (using reaction dates as proxy)
        try:
            cursor.execute(
                """
                    SELECT
                        DATE(r.Fecha) as Dia,
                        COUNT(DISTINCT c.IDPub) as Comentarios
                    FROM Comentar c
                    LEFT JOIN Reaccionar r ON c.IDPub = r.IDPub
                    WHERE c.IDU = %s
                        AND r.Fecha BETWEEN %s AND %s
                    GROUP BY DATE(r.Fecha)
                    ORDER BY Dia
                """,
                (user_id, fecha_inicio_str, fecha_fin_str),
            )
            comments_ts = cursor.fetchall()
            if comments_ts:
                time_series_data["comentarios"] = comments_ts
        except Exception as e:
            st.warning(f"No se pudieron obtener datos de comentarios: {str(e)[:100]}")

        # 5. Time series: Purchases over time
        try:
            cursor.execute(
                """
                    SELECT
                        DATE(Fecha) as Dia,
                        COUNT(*) as Compras,
                        SUM(Cantidad) as Unidades,
                        SUM(Precio * Cantidad) as Monto
                    FROM Compra
                    WHERE IDUC = %s
                        AND Fecha BETWEEN %s AND %s
                    GROUP BY DATE(Fecha)
                    ORDER BY Dia
                """,
                (user_id, fecha_inicio_str, fecha_fin_str),
            )
            purchases_ts = cursor.fetchall()
            if purchases_ts:
                time_series_data["compras"] = purchases_ts
        except Exception as e:
            st.warning(f"No se pudieron obtener datos de compras: {str(e)[:100]}")

        # 6. Time series: Contributions over time
        try:
            cursor.execute(
                """
                    SELECT
                        DATE(Fecha) as Dia,
                        COUNT(*) as Contribuciones
                    FROM Contribucion
                    WHERE IDU = %s
                        AND Fecha BETWEEN %s AND %s
                    GROUP BY DATE(Fecha)
                    ORDER BY Dia
                """,
                (user_id, fecha_inicio_str, fecha_fin_str),
            )
            contributions_ts = cursor.fetchall()
            if contributions_ts:
                time_series_data["contribuciones"] = contributions_ts
        except Exception as e:
            st.warning(
                f"No se pudieron obtener datos de contribuciones: {str(e)[:100]}"
            )

        # Summary statistics
        results["Total_Publicaciones"] = sum(
            [p[1] for p in time_series_data.get("publicaciones", [])]
        )
        results["Reacciones_Dadas"] = sum(
            [r[1] for r in time_series_data.get("reacciones_dadas", [])]
        )
        results["Reacciones_Recibidas"] = sum(
            [r[1] for r in time_series_data.get("reacciones_recibidas", [])]
        )
        results["Comentarios_Realizados"] = sum(
            [c[1] for c in time_series_data.get("comentarios", [])]
        )
        results["Total_Compras"] = sum(
            [p[1] for p in time_series_data.get("compras", [])]
        )
        results["Monto_Gastado"] = sum(
            [p[3] for p in time_series_data.get("compras", []) if len(p) > 3]
        )
        results["Total_Contribuciones"] = sum(
            [c[1] for c in time_series_data.get("contribuciones", [])]
        )

        # Planta más comprada
        try:
            cursor.execute(
                """
                    SELECT IDProd
                    FROM Compra
                    WHERE IDUC = %s
                        AND Fecha BETWEEN %s AND %s
                    GROUP BY IDProd
                    ORDER BY SUM(Cantidad) DESC
                    LIMIT 1
                """,
                (user_id, fecha_inicio_str, fecha_fin_str),
            )
            planta_comprada = cursor.fetchone()
            results["Planta_Mas_Comprada"] = (
                planta_comprada[0] if planta_comprada else None
            )
        except:
            results["Planta_Mas_Comprada"] = None

        # Planta más contribuida
        try:
            cursor.execute(
                """
                    SELECT IDProd
                    FROM Contribucion
                    WHERE IDU = %s
                        AND Fecha BETWEEN %s AND %s
                    GROUP BY IDProd
                    ORDER BY COUNT(*) DESC
                    LIMIT 1
                """,
                (user_id, fecha_inicio_str, fecha_fin_str),
            )
            planta_contribuida = cursor.fetchone()
            results["Planta_Mas_Contribuida"] = (
                planta_contribuida[0] if planta_contribuida else None
            )
        except:
            results["Planta_Mas_Contribuida"] = None

        # Create combined time series DataFrame
        ts_dataframes = {}

        # Convert each time series to DataFrame
        for key, data in time_series_data.items():
            if data:
                try:
                    if key == "publicaciones":
                        columns = ["Fecha", "Cantidad"]
                    elif key == "reacciones_dadas":
                        columns = ["Fecha", "Total", "Positivas", "Negativas"]
                    elif key == "reacciones_recibidas":
                        columns = ["Fecha", "Total", "Positivas", "Negativas"]
                    elif key == "comentarios":
                        columns = ["Fecha", "Cantidad"]
                    elif key == "compras":
                        columns = ["Fecha", "Transacciones", "Unidades", "Monto"]
                    elif key == "contribuciones":
                        columns = ["Fecha", "Cantidad"]

                    df = pd.DataFrame(data, columns=columns)
                    df["Fecha"] = pd.to_datetime(df["Fecha"])
                    ts_dataframes[key] = df
                except Exception as e:
                    st.warning(f"Error procesando datos de {key}: {str(e)[:100]}")

        return results, ts_dataframes

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_user = st.selectbox(
            "Usuario:",
            options=[f"{u[0]} - {u[1]}" for u in usuarios],
            key="user_select",
        )
        user_id = int(selected_user.split(" - ")[0])

    with col2:
        fecha_inicio = st.date_input(
            "Fecha Inicio:", value=pd.to_datetime("2023-01-01"), key="fecha_inicio"
        )

    with col3:
        fecha_fin = st.date_input(
            "Fecha Fin:", value=pd.to_datetime("2024-12-31"), key="fecha_fin"
        )

    # Add time granularity selector
    granularidad = st.selectbox(
        "Granularidad del análisis temporal:",
        ["Diario", "Semanal", "Mensual"],
        key="granularidad",
    )

    if st.button("📊 Analizar Usuario", key="analyze_user"):
        try:
            resultados, series_temporales = analizar_usuario_con_series_temporales(
                user_id, fecha_inicio, fecha_fin
            )

            st.success("✅ Análisis completado exitosamente")

            # Display summary metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("📝 Publicaciones", resultados["Total_Publicaciones"])
                st.metric("❤️ Reacciones Dadas", resultados["Reacciones_Dadas"])
                st.metric("👍 Reacciones Recibidas", resultados["Reacciones_Recibidas"])

            with col2:
                st.metric("💬 Comentarios", resultados["Comentarios_Realizados"])
                st.metric("🛒 Compras Realizadas", resultados["Total_Compras"])
                st.metric("💰 Monto Gastado", f"${resultados['Monto_Gastado']:.2f}")

            with col3:
                st.metric("🌱 Contribuciones", resultados["Total_Contribuciones"])

                # Get plant names for IDs
                if resultados["Planta_Mas_Comprada"]:
                    try:
                        cursor.execute(
                            "SELECT Nombre FROM Producto WHERE IDProd = %s",
                            (resultados["Planta_Mas_Comprada"],),
                        )
                        planta_comprada = cursor.fetchone()
                        if planta_comprada:
                            st.metric("🏆 Planta Más Comprada", planta_comprada[0])
                    except:
                        pass

                if resultados["Planta_Mas_Contribuida"]:
                    try:
                        cursor.execute(
                            "SELECT Nombre FROM Producto WHERE IDProd = %s",
                            (resultados["Planta_Mas_Contribuida"],),
                        )
                        planta_contribuida = cursor.fetchone()
                        if planta_contribuida:
                            st.markdown("**🌿 Planta Más Contribuida:**")
                            st.info(planta_contribuida[0])
                    except:
                        pass

            # Create summary dataframe
            st.markdown("### 📋 Resumen de Actividad")
            df_summary = pd.DataFrame(
                {
                    "Métrica": [
                        "Publicaciones",
                        "Reacciones Dadas",
                        "Reacciones Recibidas",
                        "Comentarios",
                        "Compras",
                        "Monto Gastado",
                        "Contribuciones",
                    ],
                    "Valor": [
                        resultados["Total_Publicaciones"],
                        resultados["Reacciones_Dadas"],
                        resultados["Reacciones_Recibidas"],
                        resultados["Comentarios_Realizados"],
                        resultados["Total_Compras"],
                        resultados["Monto_Gastado"],
                        resultados["Total_Contribuciones"],
                    ],
                }
            )
            st.dataframe(df_summary, use_container_width=True)

            # TIME SERIES VISUALIZATIONS
            if series_temporales:
                st.markdown("## 📈 Análisis Temporal de Actividad")

                # Create combined time series DataFrame for plotting
                all_dates = pd.date_range(start=fecha_inicio, end=fecha_fin, freq="D")
                combined_df = pd.DataFrame(index=all_dates)

                # Add each activity type
                for key, df in series_temporales.items():
                    if not df.empty:
                        try:
                            # Set index and resample based on granularity
                            df_temp = df.set_index("Fecha")

                            if granularidad == "Semanal":
                                df_resampled = df_temp.resample("W").sum()
                            elif granularidad == "Mensual":
                                df_resampled = df_temp.resample("M").sum()
                            else:  # Diario
                                df_resampled = df_temp

                            # Merge with combined DataFrame
                            for col in df_resampled.columns:
                                combined_df = combined_df.join(
                                    df_resampled[col].rename(f"{key}_{col}"), how="left"
                                )
                        except Exception as e:
                            st.warning(f"Error procesando {key}: {str(e)[:100]}")

                # Fill NaN with 0
                combined_df = combined_df.fillna(0)

                # Plot 1: Activity timeline (main activities)
                st.markdown(f"### 📊 Línea de Tiempo de Actividad ({granularidad})")

                # Prepare data for main activity plot
                activity_columns = []
                if "publicaciones_Cantidad" in combined_df.columns:
                    activity_columns.append("publicaciones_Cantidad")
                if "comentarios_Cantidad" in combined_df.columns:
                    activity_columns.append("comentarios_Cantidad")
                if "contribuciones_Cantidad" in combined_df.columns:
                    activity_columns.append("contribuciones_Cantidad")

                if activity_columns:
                    activity_data = combined_df[activity_columns].copy()
                    activity_data.columns = [
                        col.replace("_Cantidad", "").title()
                        for col in activity_data.columns
                    ]

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### 📅 Actividad General")
                        st.line_chart(activity_data)

                    with col2:
                        st.markdown("#### 📊 Distribución Acumulada")
                        # Calculate cumulative sum
                        cumulative_data = activity_data.cumsum()
                        st.area_chart(cumulative_data)

                # Plot 2: Reactions timeline
                st.markdown(f"### ❤️ Reacciones ({granularidad})")

                reaction_columns = []
                if "reacciones_dadas_Total" in combined_df.columns:
                    reaction_columns.append("reacciones_dadas_Total")
                if "reacciones_recibidas_Total" in combined_df.columns:
                    reaction_columns.append("reacciones_recibidas_Total")

                if reaction_columns:
                    reaction_data = combined_df[reaction_columns].copy()
                    reaction_data.columns = [
                        col.replace("_Total", "").replace("_", " ").title()
                        for col in reaction_data.columns
                    ]

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### 📈 Reacciones Totales")
                        st.line_chart(reaction_data)

                    with col2:
                        # Positive vs Negative reactions
                        if (
                            "reacciones_dadas_Positivas" in combined_df.columns
                            and "reacciones_dadas_Negativas" in combined_df.columns
                        ):
                            st.markdown(
                                "#### 😊/😠 Reacciones Dadas (Positivas vs Negativas)"
                            )
                            pos_neg_data = combined_df[
                                [
                                    "reacciones_dadas_Positivas",
                                    "reacciones_dadas_Negativas",
                                ]
                            ].copy()
                            pos_neg_data.columns = ["Positivas", "Negativas"]
                            st.bar_chart(pos_neg_data)

                # Plot 3: Purchases timeline
                if "compras_Monto" in combined_df.columns:
                    st.markdown(f"### 🛍️ Compras ({granularidad})")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### 💰 Gasto Total")
                        purchase_data = combined_df[["compras_Monto"]].copy()
                        purchase_data.columns = ["Monto Gastado ($)"]
                        st.line_chart(purchase_data)

                    with col2:
                        if "compras_Unidades" in combined_df.columns:
                            st.markdown("#### 📦 Unidades Compradas")
                            units_data = combined_df[["compras_Unidades"]].copy()
                            units_data.columns = ["Unidades"]
                            st.bar_chart(units_data)

                # Plot 4: Heatmap of activity by day of week
                st.markdown("### 🔥 Patrones de Actividad Semanal")

                # Create a DataFrame with day of week information
                if not combined_df.empty:
                    combined_df_copy = combined_df.copy()
                    combined_df_copy["Dia_Semana"] = combined_df_copy.index.day_name()
                    combined_df_copy["Numero_Dia"] = combined_df_copy.index.dayofweek

                    # Map Spanish day names
                    dia_map = {
                        "Monday": "Lunes",
                        "Tuesday": "Martes",
                        "Wednesday": "Miércoles",
                        "Thursday": "Jueves",
                        "Friday": "Viernes",
                        "Saturday": "Sábado",
                        "Sunday": "Domingo",
                    }
                    combined_df_copy["Dia_Semana"] = combined_df_copy["Dia_Semana"].map(
                        dia_map
                    )

                    # Calculate total activity per day
                    activity_cols = []
                    for col in combined_df_copy.columns:
                        if (
                            "Cantidad" in col
                            or "Total" in col
                            or "Transacciones" in col
                        ):
                            activity_cols.append(col)

                    if activity_cols:
                        combined_df_copy["Actividad_Total"] = combined_df_copy[
                            activity_cols
                        ].sum(axis=1)

                        # Group by day of week
                        actividad_por_dia = (
                            combined_df_copy.groupby(["Numero_Dia", "Dia_Semana"])[
                                "Actividad_Total"
                            ]
                            .sum()
                            .reset_index()
                        )
                        actividad_por_dia = actividad_por_dia.sort_values("Numero_Dia")

                        # Display as bar chart
                        st.bar_chart(
                            actividad_por_dia.set_index("Dia_Semana")["Actividad_Total"]
                        )

                # Plot 5: Activity distribution by time period
                st.markdown("### 📊 Distribución Temporal")

                # Calculate monthly activity
                if not combined_df.empty:
                    monthly_activity = combined_df.resample("M").sum()

                    # Select relevant columns for monthly summary
                    summary_cols = []
                    if "publicaciones_Cantidad" in monthly_activity.columns:
                        summary_cols.append("publicaciones_Cantidad")
                    if "reacciones_dadas_Total" in monthly_activity.columns:
                        summary_cols.append("reacciones_dadas_Total")
                    if "reacciones_recibidas_Total" in monthly_activity.columns:
                        summary_cols.append("reacciones_recibidas_Total")
                    if "compras_Monto" in monthly_activity.columns:
                        summary_cols.append("compras_Monto")
                    if "contribuciones_Cantidad" in monthly_activity.columns:
                        summary_cols.append("contribuciones_Cantidad")

                    if summary_cols:
                        monthly_summary = monthly_activity[summary_cols].copy()
                        monthly_summary.columns = [
                            col.split("_")[0].title() for col in monthly_summary.columns
                        ]

                        # Display as expanded dataframe
                        with st.expander("📅 Resumen Mensual Detallado"):
                            st.dataframe(monthly_summary, use_container_width=True)

                        # Display heatmap-like visualization
                        st.markdown(
                            "#### 🗓️ Calendario de Actividad (Promedio Diario por Mes)"
                        )

                        # Calculate average daily activity per month
                        days_in_month = monthly_activity.index.days_in_month
                        heatmap_data = monthly_summary.copy()

                        # Divide each column by days in month, only for columns that exist
                        for col in heatmap_data.columns:
                            if col in heatmap_data.columns:  # Redundant check but safe
                                heatmap_data[col] = (
                                    heatmap_data[col] / days_in_month.values
                                )

                        # Create a heatmap-style visualization
                        fig_data = heatmap_data.T  # Transpose for better visualization
                        try:
                            st.dataframe(
                                fig_data.style.background_gradient(cmap="YlOrRd"),
                                use_container_width=True,
                            )
                        except:
                            st.dataframe(fig_data, use_container_width=True)

                # Additional visualization: Activity intensity over time
                st.markdown("### 📶 Intensidad de Actividad")

                # Calculate rolling average of total activity
                if not combined_df.empty:
                    # Sum all activity columns
                    all_activity_cols = [
                        col
                        for col in combined_df.columns
                        if "Cantidad" in col or "Total" in col or "Transacciones" in col
                    ]
                    if all_activity_cols:
                        combined_df["Actividad_Total_Diaria"] = combined_df[
                            all_activity_cols
                        ].sum(axis=1)

                        # Calculate 7-day rolling average
                        combined_df["Media_Movil_7_Dias"] = (
                            combined_df["Actividad_Total_Diaria"]
                            .rolling(window=7)
                            .mean()
                        )

                        # Plot rolling average
                        rolling_data = combined_df[
                            ["Actividad_Total_Diaria", "Media_Movil_7_Dias"]
                        ].dropna()
                        rolling_data.columns = [
                            "Actividad Diaria",
                            "Media Móvil (7 días)",
                        ]

                        st.line_chart(rolling_data)

                        # Display activity statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            max_activity = rolling_data["Actividad Diaria"].max()
                            st.metric(
                                "📈 Máxima Actividad Diaria", f"{max_activity:.0f}"
                            )
                        with col2:
                            avg_activity = rolling_data["Actividad Diaria"].mean()
                            st.metric(
                                "📊 Actividad Promedio Diaria", f"{avg_activity:.1f}"
                            )
                        with col3:
                            active_days = (rolling_data["Actividad Diaria"] > 0).sum()
                            total_days = len(rolling_data)
                            percentage = (
                                (active_days / total_days * 100)
                                if total_days > 0
                                else 0
                            )
                            st.metric(
                                "📅 Días Activos",
                                f"{active_days}/{total_days} ({percentage:.1f}%)",
                            )

            else:
                st.warning(
                    "⚠️ No se encontraron datos temporales para este usuario en el período especificado."
                )

        except Exception as e:
            st.error(f"❌ Error en el análisis: {str(e)[:200]}")

        finally:
            cursor.close()
            conn.close()


def handle_query_influencers():
    st.markdown("## 🌟 Análisis de Influencers y su Impacto en Ventas")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        WITH InteraccionesUsuario AS (
            SELECT
                p.IDU,
                SUM(
                    CASE
                        WHEN r.Tipo = 'Me gusta' THEN 1
                        WHEN r.Tipo = 'Me encanta' THEN 2
                        WHEN r.Tipo = 'Me asombra' THEN 1.5
                        ELSE 0
                    END
                ) AS Peso_Reacciones,
                COUNT(DISTINCT c.IDPub) * 2 AS Peso_Comentarios
            FROM Publicacion p
            LEFT JOIN Reaccionar r ON p.IDPub = r.IDPub
            LEFT JOIN Comentar c ON p.IDPub = c.IDPub
            GROUP BY p.IDU
        )
        SELECT
            iu.IDU,
            u.Nombre,
            (iu.Peso_Reacciones + iu.Peso_Comentarios) AS Puntaje_Interacciones
        FROM InteraccionesUsuario iu
        JOIN Usuario u ON iu.IDU = u.IDU
        ORDER BY Puntaje_Interacciones DESC
        LIMIT 5
    """)

    influencers = cursor.fetchall()

    if influencers:
        st.success(f"✅ Se identificaron {len(influencers)} influencers principales")

        df_influencers = pd.DataFrame(
            influencers, columns=["ID", "Nombre", "Puntaje de Interacción"]
        )
        st.markdown("### 🏆 Top 5 Influencers")
        st.dataframe(df_influencers, use_container_width=True)

        selected_influencer = st.selectbox(
            "Selecciona un influencer para análisis detallado:",
            options=[f"{inf[0]} - {inf[1]}" for inf in influencers],
            key="influencer_select",
        )

        influencer_id = int(selected_influencer.split(" - ")[0])

        if st.button("🔍 Analizar Impacto", key="analyze_impact"):
            cursor.execute(
                """
                SELECT
                    c.IDProd,
                    pr.Nombre AS Planta,
                    COUNT(*) AS Total_Contribuciones,
                    (SELECT AVG(Puntuacion) FROM Compra WHERE IDProd = c.IDProd) AS Calificacion_Promedio
                FROM Contribucion c
                JOIN Producto pr ON c.IDProd = pr.IDProd
                WHERE c.IDU = %s
                GROUP BY c.IDProd, pr.Nombre
                ORDER BY Total_Contribuciones DESC
                LIMIT 5
            """,
                (influencer_id,),
            )

            plantas_interactuadas = cursor.fetchall()

            if plantas_interactuadas:
                st.markdown("### 🌿 Plantas Más Interactuadas")
                df_plantas = pd.DataFrame(
                    plantas_interactuadas,
                    columns=["ID", "Planta", "Contribuciones", "Calificación Promedio"],
                )
                st.dataframe(df_plantas, use_container_width=True)

                st.markdown("### 📈 Análisis de Impacto Simplificado")

                impact_data = []
                for planta in plantas_interactuadas[:3]:
                    planta_id = planta[0]
                    planta_nombre = planta[1]

                    cursor.execute(
                        """
                        SELECT Fecha
                        FROM Contribucion
                        WHERE IDU = %s AND IDProd = %s
                        ORDER BY Fecha DESC
                        LIMIT 2
                    """,
                        (influencer_id, planta_id),
                    )

                    fechas_actividad = cursor.fetchall()

                    for fecha_act in fechas_actividad:
                        fecha_actividad = fecha_act[0]

                        cursor.execute(
                            """
                            SELECT
                                SUM(CASE
                                    WHEN Fecha BETWEEN DATE_SUB(%s, INTERVAL 14 DAY) AND %s
                                    THEN Cantidad ELSE 0
                                END) AS Ventas_Antes,
                                SUM(CASE
                                    WHEN Fecha BETWEEN %s AND DATE_ADD(%s, INTERVAL 14 DAY)
                                    THEN Cantidad ELSE 0
                                END) AS Ventas_Despues
                            FROM Compra
                            WHERE IDProd = %s
                                AND Fecha BETWEEN DATE_SUB(%s, INTERVAL 28 DAY)
                                    AND DATE_ADD(%s, INTERVAL 28 DAY)
                        """,
                            (
                                fecha_actividad,
                                fecha_actividad,
                                fecha_actividad,
                                fecha_actividad,
                                planta_id,
                                fecha_actividad,
                                fecha_actividad,
                            ),
                        )

                        resultado = cursor.fetchone()

                        if resultado:
                            ventas_antes = resultado[0] or 0
                            ventas_despues = resultado[1] or 0
                            incremento = 0
                            if ventas_antes > 0:
                                incremento = round(
                                    (
                                        (ventas_despues - ventas_antes)
                                        / ventas_antes
                                        * 100
                                    ),
                                    2,
                                )

                            impact_data.append(
                                {
                                    "Planta": planta_nombre,
                                    "Fecha Actividad": fecha_actividad,
                                    "Ventas (2 semanas antes)": ventas_antes,
                                    "Ventas (2 semanas después)": ventas_despues,
                                    "Incremento %": incremento,
                                }
                            )

                if impact_data:
                    df_impacto = pd.DataFrame(impact_data)
                    st.dataframe(df_impacto, use_container_width=True)

                    if len(df_impacto) > 0:
                        avg_increase = df_impacto["Incremento %"].mean()
                        max_increase = df_impacto["Incremento %"].max()

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("📈 Incremento Promedio", f"{avg_increase:.1f}%")
                        with col2:
                            st.metric("🚀 Máximo Incremento", f"{max_increase:.1f}%")

                st.markdown("### 🔄 Tasa de Conversión Estimada")
                cursor.execute(
                    """
                    WITH ReaccionesInfluencer AS (
                        SELECT DISTINCT r.IDU
                        FROM Reaccionar r
                        JOIN Publicacion p ON r.IDPub = p.IDPub
                        WHERE p.IDU = %s
                    ),
                    ComprasSeguidores AS (
                        SELECT COUNT(DISTINCT c.IDUC) AS Compraron
                        FROM Compra c
                        WHERE c.IDUC IN (SELECT IDU FROM ReaccionesInfluencer)
                    )
                    SELECT
                        (SELECT COUNT(*) FROM ReaccionesInfluencer) AS Total_Seguidores,
                        Compraron,
                        ROUND(Compraron * 100.0 / NULLIF((SELECT COUNT(*) FROM ReaccionesInfluencer), 0), 2) AS Tasa_Conversion
                    FROM ComprasSeguidores
                """,
                    (influencer_id,),
                )

                conversion = cursor.fetchone()
                if conversion:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("👥 Seguidores que Reaccionaron", conversion[0])
                    with col2:
                        st.metric("🛍️ Seguidores que Compraron", conversion[1])
                    with col3:
                        st.metric("📊 Tasa de Conversión Estimada", f"{conversion[2]}%")

            else:
                st.warning(
                    "No se encontraron plantas interactuadas por este influencer."
                )

    cursor.close()
    conn.close()


def handle_query_anomalous_patterns():
    st.markdown("# 🕵️ Detección de Patrones Anómalos en Vendedores")

    def no_anomaly_found():
        st.success("✅ No se encontraron patrones anomalos.")

    conn = get_db_connection()
    cursor = conn.cursor()

    st.markdown("## 📊 Patrón 1: Variaciones de Precio Significativas")
    col1, col2 = st.columns(2)
    with col1:
        stddev_lower = st.slider(
            "Cota inferior de la desviación estándar", value=30, key="stddev_lowera"
        )
    with col2:
        stddev_upper = st.slider(
            "Cota superior de la desviación estándar", value=100, key="stddev_uppera"
        )
    query_a = """
        SELECT
            IDUV AS Vendedor,
            COUNT(DISTINCT IDProd) AS Productos_Diferentes,
            AVG(Precio) AS Precio_Promedio,
            STDDEV(Precio) AS Desviacion_Precio
        FROM Compra
        GROUP BY IDUV
        HAVING Desviacion_Precio > %s AND Desviacion_Precio <= %s
        ORDER BY Desviacion_Precio DESC
    """
    with st.expander("Query Code"):
        st.code(query_a)
    cursor.execute(query_a, (stddev_lower, stddev_upper))

    pattern1 = cursor.fetchall()
    if pattern1:
        df_pattern1 = pd.DataFrame(
            pattern1,
            columns=[
                "ID Vendedor",
                "Productos Diferentes",
                "Precio Promedio",
                "Desviación de Precio",
            ],
        )
        st.dataframe(df_pattern1, use_container_width=True, height=300)
    else:
        no_anomaly_found()

    st.divider()

    st.markdown("## ⚖️ Patrón 2: Patrones de Calificación")
    col1, col2, col3 = st.columns(3)
    with col1:
        stddev_lower = st.slider(
            "Cota inferior de la desviación estándar",
            min_value=0,
            max_value=2,
            value=0,
            key="stddev_lowerb",
        )
    with col2:
        stddev_upper = st.slider(
            "Cota superior de la desviación estándar",
            min_value=0,
            max_value=2,
            value=2,
            key="stddev_upperb",
        )
    with col3:
        total = st.number_input("Minimo de Calificiones", step=1)

    query_b = """
        SELECT
            IDUV AS Vendedor,
            COUNT(*) AS Total_Calificaciones,
            AVG(Puntuacion) AS Calificacion_Promedio,
            STDDEV(Puntuacion) AS Desviacion_Calificacion
        FROM Compra
        WHERE Puntuacion IS NOT NULL
        GROUP BY IDUV
        HAVING  Total_Calificaciones >= %s AND
                Desviacion_Calificacion >= %s AND
                Desviacion_Calificacion <= %s
        ORDER BY Desviacion_Calificacion DESC
    """
    with st.expander("Query Code"):
        st.code(query_b)
    cursor.execute(query_b, (total, stddev_lower, stddev_upper))

    pattern2 = cursor.fetchall()
    if pattern2:
        df_pattern2 = pd.DataFrame(
            pattern2,
            columns=[
                "ID Vendedor",
                "Total Calificaciones",
                "Calificación Promedio",
                "Desviación Calificación",
            ],
        )
        st.dataframe(df_pattern2, use_container_width=True, height=300)
    else:
        no_anomaly_found()

    st.divider()

    st.markdown("## 👥 Patrón 3: Patrones de Compradores")

    query_c = """
        SELECT
            IDUV AS Vendedor,
            COUNT(DISTINCT IDUC) AS Compradores_Unicos
        FROM Compra
        GROUP BY IDUV
        HAVING Compradores_Unicos >= %s AND Compradores_Unicos <= %s
        ORDER BY Compradores_Unicos ASC
    """

    col1, col2 = st.columns(2)
    with col1:
        unique_buyers_lower = st.number_input(
            "Mínimo de Compradores Únicos", value=0, step=1
        )
    with col2:
        unique_buyers_upper = st.number_input(
            "Máximo de Compradores Únicos", value=50, step=1
        )
    with st.expander("Query Code"):
        st.code(query_c)
    cursor.execute(query_c, (unique_buyers_lower, unique_buyers_upper))

    pattern3 = cursor.fetchall()
    if pattern3:
        df_pattern3 = pd.DataFrame(
            pattern3,
            columns=["ID Vendedor", "Compradores Únicos"],
        )
        st.dataframe(df_pattern3, use_container_width=True, height=300)

    st.divider()
    # st.markdown("### 🎯 Resumen de Hallazgos")

    suspicious_sellers = {}

    for seller in pattern1[:5]:
        seller_id = seller[0]
        if seller_id not in suspicious_sellers:
            suspicious_sellers[seller_id] = {"Patrones": [], "Evidencias": []}
        suspicious_sellers[seller_id]["Patrones"].append("Alta variación de precios")
        suspicious_sellers[seller_id]["Evidencias"].append(
            f"Desviación: {seller[3]:.2f}"
        )

    for seller in pattern2[:5]:
        seller_id = seller[0]
        if seller_id not in suspicious_sellers:
            suspicious_sellers[seller_id] = {"Patrones": [], "Evidencias": []}
        suspicious_sellers[seller_id]["Patrones"].append(
            "Calificaciones inconsistentes"
        )
        suspicious_sellers[seller_id]["Evidencias"].append(
            f"Desv. calificación: {seller[3]:.2f}"
        )

    for seller in pattern3[:5]:
        seller_id = seller[0]
        if seller_id not in suspicious_sellers:
            suspicious_sellers[seller_id] = {"Patrones": [], "Evidencias": []}
        suspicious_sellers[seller_id]["Patrones"].append("Pocos compradores únicos")
        suspicious_sellers[seller_id]["Evidencias"].append(f"Compradores: {seller[1]}")

    if suspicious_sellers:
        suspicious_list = []
        for seller_id, data in suspicious_sellers.items():
            cursor.execute("SELECT Nombre FROM Usuario WHERE IDU = %s", (seller_id,))
            seller_name = cursor.fetchone()
            name = seller_name[0] if seller_name else f"Vendedor {seller_id}"

            suspicious_list.append(
                {
                    "ID Vendedor": seller_id,
                    "Nombre": name,
                    "Patrones Detectados": len(data["Patrones"]),
                    "Evidencias": "; ".join(data["Evidencias"]),
                }
            )

        df_suspicious = pd.DataFrame(suspicious_list)
        df_suspicious = df_suspicious.sort_values(
            "Patrones Detectados", ascending=False
        )

        st.markdown("## 🔴 Vendedores con Patrones Sospechosos")
        st.dataframe(df_suspicious, use_container_width=True)
    else:
        st.success("✅ No se encontraron patrones anómalos significativos.")

    cursor.close()
    conn.close()


def show_query_selector(selected_query=None):
    st.markdown("## 📊 Selector de Consultas SQL")

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

    if not selected_query:
        selected_query = st.selectbox(
            "Selecciona una consulta:", list(options.keys()), key="query_selector"
        )
        selected_query = options[selected_query]

    if selected_query == "ñ":
        handle_query_trigger_auditoria()
    elif selected_query == "o":
        handle_query_stored_procedure()
    elif selected_query == "p":
        handle_query_influencers()
    elif selected_query == "q":
        handle_query_anomalous_patterns()
    else:
        query_text = queries.queries[selected_query]
        with st.expander("Query Code"):
            st.code(query_text)
        st.session_state.query_results = mysql_get_query_results(selected_query)
        if st.session_state.query_results is not None:
            st.markdown("### 📋 Resultados de la Consulta")
            st.success("✅ Consulta ejecutada correctamente.")

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
