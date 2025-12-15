import streamlit as st

from Ex6 import st_libs as stl

if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
if "query_results" not in st.session_state:
    st.session_state.query_results = None
if "selected_plant" not in st.session_state:
    st.session_state.selected_plant = None
if "price_history" not in st.session_state:
    st.session_state.price_history = None

stl.create_sidebar()


# with open("Ex6/style.css") as style:
#     st.markdown(f"<style>{style.read()}</style>", unsafe_allow_html=True)


if st.session_state.current_page == "Dashboard":
    stl.show_dashboard()
elif st.session_state.current_page == "Consultas SQL":
    stl.query_selector_section()
elif st.session_state.current_page == "Análisis de Usuario":
    stl.user_analysis_section()
elif st.session_state.current_page == "Conversaciones":
    stl.conversation_management_section()
elif st.session_state.current_page == "Documentos":
    stl.document_explorer_section()
elif st.session_state.current_page == "Gestor de Precios":
    stl.price_manager_section()
elif st.session_state.current_page == "Configuración":
    stl.show_configuration()
