import pandas as pd
import streamlit as st
from st_queries import get_db_connection


def show_product_manager():
    """
    Gestor de precios de productos:
    • Mostrar una lista de productos con sus precios actuales
    • Permitir al usuario seleccionar un producto y cambiar su precio
    • Después de actualizar el precio, consultar y mostrar el historial de cambios de precio registrado por el trigger de auditoría
    • Visualizar la tabla de auditoría con los cambios históricos de precios para el producto seleccionado
    """
    st.markdown("## 💰 Gestor de Precios de Productos")
    st.markdown(
        "Interfaz para gestionar precios de productos y visualizar el historial de cambios."
    )

    # Section 1: Setup and initialization
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create audit table if not exists
    try:
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
        conn.commit()
        st.success("✅ Tabla de auditoría creada/verificada")
    except Exception as e:
        st.warning(f"⚠️ Error al crear tabla de auditoría: {str(e)[:100]}")

    # Section 2: List all products with current prices
    st.markdown("### 📋 Lista de Productos con Precios Actuales")

    try:
        cursor.execute("""
            SELECT
                p.IDProd,
                p.Nombre,
                p.Precio AS Precio_Actual,
                COUNT(hp.ID) AS Cambios_Historicos,
                COALESCE(MAX(hp.Fecha_Cambio), 'Sin cambios') AS Ultimo_Cambio
            FROM Producto p
            LEFT JOIN Historial_Precios hp ON p.IDProd = hp.IDProd
            GROUP BY p.IDProd, p.Nombre, p.Precio
            ORDER BY p.Nombre
        """)

        productos = cursor.fetchall()

        if productos:
            # Create DataFrame for display
            df_productos = pd.DataFrame(
                productos,
                columns=[
                    "ID",
                    "Producto",
                    "Precio Actual",
                    "Cambios Históricos",
                    "Último Cambio",
                ],
            )

            # Display products table with sorting capability
            st.dataframe(
                df_productos,
                use_container_width=True,
                column_config={
                    "Precio Actual": st.column_config.NumberColumn(format="$%.2f"),
                    "Cambios Históricos": st.column_config.NumberColumn(format="%d"),
                },
            )

            # Summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Productos", len(df_productos))
            with col2:
                precio_promedio = df_productos["Precio Actual"].mean()
                st.metric("Precio Promedio", f"${precio_promedio:.2f}")
            with col3:
                productos_con_cambios = df_productos[
                    df_productos["Cambios Históricos"] > 0
                ].shape[0]
                st.metric("Productos Modificados", productos_con_cambios)

            # Section 3: Product selection and price modification
            st.markdown("### ✏️ Modificar Precio de Producto")

            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                # Create select box with product details
                opciones_productos = [
                    f"{p[0]} - {p[1]} (${p[2]:.2f})" for p in productos
                ]
                producto_seleccionado = st.selectbox(
                    "Selecciona un producto:",
                    options=opciones_productos,
                    key="producto_seleccionado_precios",
                    help="Selecciona un producto para modificar su precio",
                )

                # Extract product ID from selection
                producto_id = int(producto_seleccionado.split(" - ")[0])

                # Get selected product details
                producto_info = next(
                    (p for p in productos if p[0] == producto_id), None
                )

            with col2:
                if producto_info:
                    # Display current price
                    precio_actual = producto_info[2]
                    st.metric(
                        "Precio Actual",
                        f"${precio_actual:.2f}",
                        delta=None,
                        help="Precio actual del producto seleccionado",
                    )

            with col3:
                if producto_info:
                    # Display historical changes count
                    cambios_historicos = producto_info[3]
                    st.metric(
                        "Cambios Registrados",
                        cambios_historicos,
                        delta=None,
                        help="Número de cambios de precio registrados en el historial",
                    )

            # Price modification section
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                nuevo_precio = st.number_input(
                    "Nuevo Precio ($):",
                    min_value=0.01,
                    value=float(precio_actual) if producto_info else 0.01,
                    step=0.01,
                    format="%.2f",
                    key="nuevo_precio_input",
                    help="Ingresa el nuevo precio para el producto",
                )

            with col2:
                # Calculate percentage change
                if producto_info and precio_actual > 0:
                    cambio_porcentaje = (
                        (nuevo_precio - precio_actual) / precio_actual * 100
                    )
                    st.metric(
                        "Cambio %",
                        f"{cambio_porcentaje:.1f}%",
                        delta=f"{cambio_porcentaje:.1f}%",
                        delta_color="normal"
                        if abs(cambio_porcentaje) < 10
                        else "inverse",
                    )

            with col3:
                # Display absolute change
                if producto_info:
                    cambio_absoluto = nuevo_precio - precio_actual
                    st.metric(
                        "Cambio Absoluto",
                        f"${cambio_absoluto:.2f}",
                        delta=f"{cambio_absoluto:.2f}",
                        delta_color="normal" if cambio_absoluto >= 0 else "inverse",
                    )

            # Update price button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    "💾 Actualizar Precio",
                    key="actualizar_precio_btn",
                    use_container_width=True,
                ):
                    if nuevo_precio != precio_actual:
                        try:
                            cursor.execute(
                                "SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = DATABASE() AND trigger_name = 'auditoria_precios'"
                            )
                            trigger_exists = cursor.fetchall()
                            # Calculate percentage change
                            porcentaje_cambio = 0
                            if precio_actual > 0:
                                porcentaje_cambio = (
                                    (nuevo_precio - precio_actual) / precio_actual * 100
                                )

                            # Update product price
                            cursor.execute(
                                "UPDATE Producto SET Precio = %s WHERE IDProd = %s",
                                (nuevo_precio, producto_id),
                            )

                            # # Manually insert into audit table (fallback if trigger doesn't work)
                            # cursor.execute(
                            #     """
                            #     INSERT INTO Historial_Precios (IDProd, Precio_Anterior, Precio_Nuevo, Porcentaje_Cambio)
                            #     VALUES (%s, %s, %s, %s)
                            # """,
                            #     (
                            #         producto_id,
                            #         precio_actual,
                            #         nuevo_precio,
                            #         porcentaje_cambio,
                            #     ),
                            # )

                            conn.commit()

                            st.success("✅ Precio actualizado exitosamente!")
                            st.info(
                                f"**Producto:** {producto_info[1]}\n\n"
                                f"**Precio anterior:** ${precio_actual:.2f}\n\n"
                                f"**Nuevo precio:** ${nuevo_precio:.2f}\n\n"
                                f"**Cambio:** {cambio_porcentaje:.1f}%"
                            )

                            # Refresh the page to show updated data
                            st.rerun()

                        except Exception as e:
                            st.error(
                                f"❌ Error al actualizar el precio: {str(e)[:200]}"
                            )
                            conn.rollback()
                    else:
                        st.warning(
                            "⚠️ El nuevo precio es igual al precio actual. No se realizaron cambios."
                        )

            # Section 4: Audit history for selected product
            st.markdown("### 📜 Historial de Cambios de Precio")

            if producto_id:
                # Query audit history for selected product
                cursor.execute(
                    """
                    SELECT
                        hp.Fecha_Cambio,
                        hp.Precio_Anterior,
                        hp.Precio_Nuevo,
                        hp.Porcentaje_Cambio,
                        ROW_NUMBER() OVER (ORDER BY hp.Fecha_Cambio) AS Orden
                    FROM Historial_Precios hp
                    WHERE hp.IDProd = %s
                    ORDER BY hp.Fecha_Cambio DESC
                """,
                    (producto_id,),
                )

                historial = cursor.fetchall()

                if historial:
                    # Create DataFrame for audit history
                    df_historial = pd.DataFrame(
                        historial,
                        columns=[
                            "Fecha y Hora",
                            "Precio Anterior",
                            "Precio Nuevo",
                            "Porcentaje de Cambio",
                            "N°",
                        ],
                    )

                    # Format columns
                    df_historial["Fecha y Hora"] = pd.to_datetime(
                        df_historial["Fecha y Hora"]
                    )
                    df_historial["Precio Anterior"] = df_historial[
                        "Precio Anterior"
                    ].apply(lambda x: f"${x:.2f}")
                    df_historial["Precio Nuevo"] = df_historial["Precio Nuevo"].apply(
                        lambda x: f"${x:.2f}"
                    )
                    df_historial["Porcentaje de Cambio"] = df_historial[
                        "Porcentaje de Cambio"
                    ].apply(lambda x: f"{x:.1f}%")

                    # Display audit history
                    st.dataframe(
                        df_historial[
                            [
                                "N°",
                                "Fecha y Hora",
                                "Precio Anterior",
                                "Precio Nuevo",
                                "Porcentaje de Cambio",
                            ]
                        ],
                        use_container_width=True,
                    )

                    # Audit history statistics
                    st.markdown("#### 📊 Estadísticas del Historial")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de Cambios", len(historial))
                    with col2:
                        # Calculate average percentage change
                        cambios = [h[3] for h in historial]
                        promedio_cambio = sum(cambios) / len(cambios) if cambios else 0
                        st.metric("Cambio Promedio", f"{promedio_cambio:.1f}%")
                    with col3:
                        # Find largest change
                        max_cambio = max(abs(c) for c in cambios) if cambios else 0
                        st.metric("Cambio Máximo", f"{max_cambio:.1f}%")

                    # Price evolution chart
                    st.markdown("#### 📈 Evolución del Precio")

                    # Prepare data for chart
                    chart_data = df_historial.copy()
                    chart_data["Fecha y Hora"] = pd.to_datetime(
                        chart_data["Fecha y Hora"]
                    )
                    chart_data = chart_data.sort_values("Fecha y Hora")

                    # Extract numeric prices for chart
                    chart_data["Precio Nuevo Num"] = (
                        chart_data["Precio Nuevo"].str.replace("$", "").astype(float)
                    )

                    # Create line chart
                    st.line_chart(
                        chart_data.set_index("Fecha y Hora")["Precio Nuevo Num"],
                        use_container_width=True,
                    )

                    # Display price change timeline
                    st.markdown("#### ⏱️ Línea de Tiempo de Cambios")

                    # Create a timeline view
                    for idx, cambio in enumerate(
                        historial[:10]
                    ):  # Show last 10 changes
                        fecha = cambio[0]
                        precio_ant = cambio[1]
                        precio_nuevo = cambio[2]
                        porcentaje = cambio[3]

                        col1, col2, col3 = st.columns([2, 1, 1])

                        with col1:
                            st.markdown(
                                f"**Cambio #{idx + 1}** - {fecha.strftime('%d/%m/%Y %H:%M')}"
                            )

                        with col2:
                            st.markdown(f"${precio_ant:.2f} → ${precio_nuevo:.2f}")

                        with col3:
                            color = "🟢" if porcentaje >= 0 else "🔴"
                            st.markdown(f"{color} {porcentaje:.1f}%")

                    if len(historial) > 10:
                        st.info(
                            f"Mostrando los últimos 10 cambios de {len(historial)} totales."
                        )

                else:
                    st.info(
                        "📝 Este producto no tiene historial de cambios de precio registrado."
                    )

            # Section 5: Complete audit table view
            st.markdown("### 📊 Tabla Completa de Auditoría")

            if st.checkbox(
                "Mostrar tabla completa de auditoría", key="mostrar_auditoria_completa"
            ):
                try:
                    cursor.execute("""
                        SELECT
                            hp.IDProd,
                            p.Nombre AS Producto,
                            hp.Precio_Anterior,
                            hp.Precio_Nuevo,
                            hp.Fecha_Cambio,
                            hp.Porcentaje_Cambio,
                            u.IDU AS Usuario_Modificador,
                            u.Nombre AS Nombre_Usuario
                        FROM Historial_Precios hp
                        JOIN Producto p ON hp.IDProd = p.IDProd
                        LEFT JOIN Compra c ON hp.IDProd = c.IDProd
                        LEFT JOIN Usuario u ON c.IDUC = u.IDU
                        ORDER BY hp.Fecha_Cambio DESC
                        LIMIT 100
                    """)

                    auditoria_completa = cursor.fetchall()

                    if auditoria_completa:
                        df_auditoria = pd.DataFrame(
                            auditoria_completa,
                            columns=[
                                "ID Producto",
                                "Producto",
                                "Precio Anterior",
                                "Precio Nuevo",
                                "Fecha Cambio",
                                "Porcentaje Cambio",
                                "ID Usuario",
                                "Usuario",
                            ],
                        )

                        # Format columns
                        df_auditoria["Precio Anterior"] = df_auditoria[
                            "Precio Anterior"
                        ].apply(lambda x: f"${x:.2f}")
                        df_auditoria["Precio Nuevo"] = df_auditoria[
                            "Precio Nuevo"
                        ].apply(lambda x: f"${x:.2f}")
                        df_auditoria["Porcentaje Cambio"] = df_auditoria[
                            "Porcentaje Cambio"
                        ].apply(lambda x: f"{x:.1f}%")

                        # Display with filters
                        st.dataframe(
                            df_auditoria,
                            use_container_width=True,
                            column_config={
                                "Porcentaje Cambio": st.column_config.ProgressColumn(
                                    format="%f%%", min_value=-100, max_value=100
                                )
                            },
                        )

                        # Summary statistics for complete audit
                        st.markdown("##### 📈 Resumen de Auditoría Completa")

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            total_cambios = len(df_auditoria)
                            st.metric("Cambios Totales", total_cambios)
                        with col2:
                            productos_afectados = df_auditoria["ID Producto"].nunique()
                            st.metric("Productos Afectados", productos_afectados)

                        with col3:
                            cambios_positivos = df_auditoria[
                                df_auditoria["Porcentaje Cambio"].str.contains("-")
                                == False
                            ].shape[0]
                            st.metric("Aumentos de Precio", cambios_positivos)

                        with col4:
                            cambios_negativos = df_auditoria[
                                df_auditoria["Porcentaje Cambio"].str.contains("-")
                            ].shape[0]
                            st.metric("Reducciones de Precio", cambios_negativos)

                        # Export functionality
                        st.markdown("##### 💾 Exportar Datos")
                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button(
                                "📥 Exportar Historial a CSV", key="export_csv"
                            ):
                                csv = df_auditoria.to_csv(index=False)
                                st.download_button(
                                    label="Descargar CSV",
                                    data=csv,
                                    file_name="historial_precios.csv",
                                    mime="text/csv",
                                )

                        with col2:
                            if st.button("📊 Generar Reporte", key="generate_report"):
                                st.info(
                                    "Reporte generado: Resumen de cambios de precios"
                                )
                                # Simple report generation
                                report_text = f"""
                                ### 📋 Reporte de Cambios de Precios

                                **Período analizado:** Desde {df_auditoria["Fecha Cambio"].min()} hasta {df_auditoria["Fecha Cambio"].max()}
                                **Total de cambios:** {total_cambios}
                                **Productos afectados:** {productos_afectados}
                                **Aumentos de precio:** {cambios_positivos}
                                **Reducciones de precio:** {cambios_negativos}

                                **Productos con más cambios:**
                                """
                                st.markdown(report_text)

                                # Top products by number of changes
                                top_productos = (
                                    df_auditoria["Producto"].value_counts().head(5)
                                )
                                for producto, cambios in top_productos.items():
                                    st.write(f"- {producto}: {cambios} cambios")
                    else:
                        st.info("La tabla de auditoría está vacía.")

                except Exception as e:
                    st.error(f"Error al consultar auditoría completa: {str(e)[:200]}")

        else:
            st.warning("No se encontraron productos en la base de datos.")

    except Exception as e:
        st.error(f"Error al cargar productos: {str(e)[:200]}")

    finally:
        cursor.close()
        conn.close()
