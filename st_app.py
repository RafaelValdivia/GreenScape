import sys

import streamlit as st
from typing_extensions import Any

sys.path.append("Ex3")
sys.path.append("Ex4")
sys.path.append("Ex5")
sys.path.append("Ex6")

from Ex6.st_document import *
from Ex6.st_sidebar import *

from Ex6.st_comments import *
from Ex6.st_products import *
from Ex6.st_queries import *

st.set_page_config(
    layout="wide",
    page_title="GreenScape DB",
    page_icon="🌿",
    initial_sidebar_state="expanded",
)


def init_session_state():
    if "query_results" not in st.session_state:
        st.session_state.query_results = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"


page_functions = {
    "Home": show_home,
    "Consultas SQL": show_query_selector,
    "Conversaciones": show_conversation_manager,
    "Documentos": show_document_system,
    "Gestor de Precios": show_product_manager,
    "Configuración": None,
}
if __name__ == "__main__":
    init_session_state()
    sidebar()
    page_functions[st.session_state.current_page]()
