import streamlit as st
from doc_mongodb import MongoDBPlantDocumentSystem


def show_document_system():
    st.title("📚 Explorador de Documentos")

    # Authentication section at the top
    with st.expander("🔐 Configuración de MongoDB", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            mongodb_user = st.text_input("Usuario MongoDB", "admin")
        with col2:
            mongodb_pass = st.text_input("Contraseña MongoDB", type="password")

    # Initialize MongoDB with authentication
    try:
        doc_system = MongoDBPlantDocumentSystem(
            username=mongodb_user, password=mongodb_pass
        )
        st.success("✅ Conectado a MongoDB")
    except Exception as e:
        st.error(f"❌ Error de conexión: {str(e)[:100]}")
        st.info("💡 Prueba con usuario: 'admin' y contraseña: 'password'")
        return

    # Top controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        plant_ids = doc_system.get_all_plant_ids()

    with col2:
        if st.button("📋 Crear Datos", help="Crea 5 plantas con documentos"):
            with st.spinner("Creando..."):
                success = doc_system.create_test_data()
                if success:
                    st.success("✅ ¡Datos creados!")
                    st.rerun()

    with col3:
        if st.button("🔄 Actualizar"):
            st.rerun()

    if not plant_ids:
        st.info("""
        ℹ️ **No hay plantas en la base de datos.**

        Haz clic en **'Crear Datos'** para generar:
        - 5 plantas (ID: 1-5)
        - Cada una con: Ficha Técnica + 3 documentos secundarios
        """)
        return

    # Plant selector
    selected_plant = st.selectbox("🌱 **Selecciona una planta:**", plant_ids)

    if not selected_plant:
        return

    # Get documents
    docs = doc_system.get_plant_documents(selected_plant)

    if not docs:
        st.info(f"ℹ️ La Planta #{selected_plant} no tiene documentos.")
        return

    # Display stats
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 Total", docs["total_documents"])
    col2.metric("📘 Principal", "1")
    col3.metric("📄 Secundarios", docs["total_documents"] - 1)

    # Display main document
    st.divider()
    st.subheader("📘 Documento Principal")

    main = docs["main_document"]
    with st.container():
        st.write(f"**{main['filename']}**")
        st.caption(f"Tipo: {main['type']} | Tamaño: {main['size'] / 1024:.1f} KB")

        # View content
        if st.button("👁️ Ver Contenido", key="view_main"):
            try:
                with open(main["filepath"], "r") as f:
                    st.text_area("Contenido:", f.read(), height=200)
            except:
                st.error("Error al leer archivo")

    # Display secondary documents
    if docs["secondary_documents"]:
        st.divider()
        st.subheader("📄 Documentos Secundarios")

        for doc in docs["secondary_documents"]:
            with st.expander(f"{doc['filename']} - {doc['type']}"):
                st.caption(f"ID: {doc['id']} | Tamaño: {doc['size'] / 1024:.1f} KB")

                if st.button("👁️ Ver", key=f"view_{doc['id']}"):
                    try:
                        with open(doc["filepath"], "r") as f:
                            st.text(f.read())
                    except:
                        st.error("Error al leer archivo")

    # Upload new document
    st.divider()
    st.subheader("📤 Subir Nuevo Documento")

    col1, col2 = st.columns(2)
    with col1:
        upload_type = st.selectbox("Tipo:", ["Secundario", "Principal"])
    with col2:
        uploaded_file = st.file_uploader("Archivo:", type=["txt"])

    if uploaded_file and st.button("Subir"):
        content = uploaded_file.read()

        if upload_type == "Principal":
            doc_system.insert_main_document(
                plant_id=selected_plant, content=content, filename=uploaded_file.name
            )
            st.success("✅ Documento principal agregado")
        else:
            doc_system.insert_secondary_document(
                plant_id=selected_plant,
                tipo_documento="Documento Secundario",
                content=content,
                filename=uploaded_file.name,
            )
            st.success("✅ Documento secundario agregado")
        st.rerun()


if __name__ == "__main__":
    show_document_system()
