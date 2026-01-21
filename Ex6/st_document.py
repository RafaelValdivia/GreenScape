import json
import os

import mysql.connector as mq
import streamlit as st
from doc_mongodb import MongoDBPlantDocumentSystem


def show_document_system():
    st.title("📚 Explorador de Documentos")

    try:
        doc_system = MongoDBPlantDocumentSystem()
    except:
        st.error(
            "❌ Error de conexión con MongoDB. Verifica que el servidor esté corriendo."
        )
        return

    # Create directories if they don't exist
    if not os.path.exists("./greenscape_documents"):
        os.makedirs("./greenscape_documents")

    # Header with buttons
    col1, col2 = st.columns([3, 1])

    with col1:
        if st.button("📋 Crear Datos de Prueba (5 plantas con documentos)"):
            with st.spinner("Creando datos de prueba para el ejercicio 5..."):
                doc_system.create_test_data()
                st.success("✅ Datos creados exitosamente!")
                st.rerun()

    with col2:
        if st.button("🔄 Actualizar"):
            st.rerun()

    # Get all plant IDs
    with open("connection.json", "r") as file:
        mysql_connection = json.load(file)["mysql"]
        conn = mq.connect(**mysql_connection)
    cursor = conn.cursor()
    cursor.execute("SELECT IDProd FROM Planta")
    plant_ids = cursor.fetchall()
    plant_ids = [id[0] for id in plant_ids]
    conn.close()

    # Plant selector
    selected_plant = st.selectbox(
        "🌱 **Selecciona una planta:**",
        options=plant_ids,
        format_func=lambda x: f"Planta #{x}",
    )

    if not selected_plant:
        return

    # Get documents for selected plant
    documents = doc_system.get_plant_documents(selected_plant)

    if not documents:
        st.info(f"ℹ️ La Planta #{selected_plant} no tiene documentos asociados.")

        # Upload section for empty plant
        st.divider()
        st.subheader("📤 Agregar primer documento a esta planta")

        uploaded_file = st.file_uploader(
            "Selecciona un archivo:",
            type=["txt", "pdf", "jpg", "png", "jpeg", "docx", "xlsx", "csv"],
            key="initial_upload",
        )

        if uploaded_file:
            st.write(f"📄 Archivo seleccionado: {uploaded_file.name}")

            if st.button("Subir como Documento Principal", type="primary"):
                content = uploaded_file.read()
                filename = uploaded_file.name

                with st.spinner("Subiendo documento..."):
                    doc_system.insert_main_document(
                        plant_id=selected_plant, content=content, filename=filename
                    )
                    st.success("✅ Documento principal agregado exitosamente!")
                    st.rerun()
        return

    # Display statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📊 Total Documentos", documents["total_documents"])

    with col2:
        st.metric("📘 Principal", "1")

    with col3:
        sec_count = documents["total_documents"] - 1
        st.metric("📄 Secundarios", sec_count)

    st.divider()

    # Display main document
    if documents["main_document"]:
        main = documents["main_document"]

        with st.expander(
            f"📘 **{main['filename']}** - Documento Principal", expanded=True
        ):
            # Document info
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Tipo:** {main['type']}")
                st.write(f"**MIME Type:** {main['mime_type']}")
            with col2:
                st.write(f"**Tamaño:** {main['size'] / 1024:.1f} KB")
                created_date = main["created"]
                if hasattr(created_date, "strftime"):
                    created_date = created_date.strftime("%Y-%m-%d %H:%M")
                st.write(f"**Creado:** {created_date}")

            # Handle different file types
            file_path = main["filepath"]

            if main["mime_type"].startswith("text/") or main["filename"].endswith(
                ".txt"
            ):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    st.text_area(
                        "📖 Contenido:",
                        value=content,
                        height=200,
                        key=f"main_text_{main['id']}",
                    )
                except Exception as e:
                    st.info(f"⚠️ No se pudo leer el archivo de texto: {e}")

            elif main["mime_type"].startswith("image/"):
                try:
                    st.image(file_path, caption=main["filename"], use_column_width=True)
                except Exception as e:
                    st.info(f"⚠️ No se pudo cargar la imagen: {e}")

                    # Provide download as fallback
                    try:
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()
                        st.download_button(
                            label="📥 Descargar Imagen",
                            data=file_bytes,
                            file_name=main["filename"],
                            mime=main["mime_type"],
                            key=f"download_main_{main['id']}",
                        )
                    except:
                        st.error("❌ No se puede acceder al archivo")

            elif main["mime_type"] == "application/pdf":
                try:
                    with open(file_path, "rb") as f:
                        pdf_bytes = f.read()

                    # Provide download button
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_bytes,
                        file_name=main["filename"],
                        mime="application/pdf",
                        key=f"download_main_pdf_{main['id']}",
                    )

                    # Try to show PDF preview (simplified)
                    st.info(
                        "💡 Vista previa de PDF no disponible directamente. Descarga el archivo para verlo."
                    )

                except Exception as e:
                    st.error(f"❌ Error con el archivo PDF: {e}")

            else:
                # For other file types, provide download
                try:
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()

                    st.download_button(
                        label=f"📥 Descargar {main['filename']}",
                        data=file_bytes,
                        file_name=main["filename"],
                        mime=main["mime_type"],
                        key=f"download_main_other_{main['id']}",
                    )
                    st.info(f"📄 Tipo de archivo: {main['mime_type']}")

                except Exception as e:
                    st.error(f"❌ Error al acceder al archivo: {e}")

    # Display secondary documents
    if documents["secondary_documents"]:
        st.subheader("📄 Documentos Secundarios")

        for i, doc in enumerate(documents["secondary_documents"]):
            with st.expander(f"**{doc['filename']}** - {doc['type']}", expanded=False):
                # Document info
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Tipo:** {doc['type']}")
                    st.write(f"**MIME:** {doc['mime_type']}")
                with col2:
                    st.write(f"**Tamaño:** {doc['size'] / 1024:.1f} KB")
                    created_date = doc["created"]
                    if hasattr(created_date, "strftime"):
                        created_date = created_date.strftime("%Y-%m-%d")
                    st.write(f"**Creado:** {created_date}")

                # Handle different file types
                file_path = doc["filepath"]

                if doc["mime_type"].startswith("text/") or doc["filename"].endswith(
                    ".txt"
                ):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        st.text_area(
                            "Contenido:",
                            value=content,
                            height=150,
                            key=f"sec_text_{doc['id']}",
                        )
                    except Exception as e:
                        st.info(f"No se pudo leer el archivo: {e}")

                elif doc["mime_type"].startswith("image/"):
                    try:
                        st.image(
                            file_path, caption=doc["filename"], use_column_width=True
                        )
                    except Exception as e:
                        st.info(f"No se puede mostrar la imagen: {e}")

                        # Provide download as fallback
                        try:
                            with open(file_path, "rb") as f:
                                file_bytes = f.read()
                            st.download_button(
                                label="📥 Descargar Imagen",
                                data=file_bytes,
                                file_name=doc["filename"],
                                mime=doc["mime_type"],
                                key=f"download_sec_{doc['id']}",
                            )
                        except:
                            st.error("No se puede acceder al archivo")

                else:
                    # For other file types, provide download
                    try:
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()

                        st.download_button(
                            label="📥 Descargar Archivo",
                            data=file_bytes,
                            file_name=doc["filename"],
                            mime=doc["mime_type"],
                            key=f"download_sec_{doc['id']}",
                        )

                        if doc["mime_type"] == "application/pdf":
                            st.info(
                                "Vista previa de PDF no disponible. Descarga para ver."
                            )
                        else:
                            st.info(f"Tipo de archivo: {doc['mime_type']}")

                    except Exception as e:
                        st.error(f"Error al acceder al archivo: {e}")

    # Upload new document section
    st.divider()
    st.subheader("📤 Agregar nuevo documento")

    upload_col1, upload_col2 = st.columns(2)

    with upload_col1:
        upload_type = st.radio(
            "Tipo de documento:",
            ["Secundario", "Principal"],
            help="Solo puede haber un documento principal por planta",
        )

    with upload_col2:
        uploaded_file = st.file_uploader(
            "Selecciona un archivo:",
            type=["txt", "pdf", "jpg", "png", "jpeg", "docx", "xlsx", "csv"],
            key="new_upload",
        )

    if uploaded_file:
        st.write(f"📄 **Archivo seleccionado:** {uploaded_file.name}")
        st.write(f"📏 **Tamaño:** {uploaded_file.size / 1024:.1f} KB")
        if upload_type == "Secundario":
            doc_type = st.text_input("Tipo de Documento")
        if st.button("Subir Documento", type="primary"):
            content = uploaded_file.read()
            filename = uploaded_file.name

            with st.spinner("Subiendo documento..."):
                try:
                    if upload_type == "Principal":
                        doc_system.insert_main_document(
                            plant_id=selected_plant,
                            content=content,
                            filename=filename,
                        )
                        st.success("✅ Documento principal agregado exitosamente!")
                    elif upload_type == "Secundario" and doc_type:
                        doc_system.insert_secondary_document(
                            plant_id=selected_plant,
                            tipo_documento=doc_type,
                            content=content,
                            filename=filename,
                        )
                        st.success("✅ Documento secundario agregado exitosamente!")

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al subir el documento: {str(e)}")


if __name__ == "__main__":
    show_document_system()
