import streamlit as st


def sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding: 19px 0;">
                <h1 style="color: #0a5c36; margin-bottom: 0;">🌿</h1>
                <h1 style="color: #0a5c36; margin-top: 0;">GreenScape</h2>
                <p style="color: #1e7d32; font-size: 14px;">Plataforma de Análisis de Datos</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        page_options = {
            "🏠 Home": "Home",
            "📊 Consultas SQL": "Consultas SQL",
            "💬 Conversaciones": "Conversaciones",
            "📚 Documentos": "Documentos",
            "👤 Análisis de Usuario": "Análisis de Usuario",
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

        st.markdown(f"**Página actual:** {st.session_state.current_page}")

        if st.button("🔄 Recargar Página", use_container_width=True):
            st.rerun()


def show_home():
    pass
