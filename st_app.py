import sys

import streamlit as st
from typing_extensions import Any

sys.path.append("Ex3")
sys.path.append("Ex4")
sys.path.append("Ex5")
sys.path.append("Ex6")

# from Ex6.st_products import *

from Ex6.st_comments import *
from Ex6.st_document import *
from Ex6.st_queries import *
from Ex6.st_sidebar import *

st.set_page_config(
    layout="centered",
    page_title="GreenScape DB",
    page_icon="🌿",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
    <style>
    /* ========== MINIMAL FRUTIGER AERO CSS ========== */
    /* Targeting native Streamlit classes only */

    /* Main app background - Frutiger Aero gradient */
    .stApp {
        background: linear-gradient(135deg, #d4f1ff 0%, #b8e8d8 50%, #c5f0e1 100%) !important;
    }

    /* Fix font colors - ensure readability */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown, .stText, p, label,
    .stAlert, .stException, .stExpander,
    div[data-testid="stCaptionContainer"] {
        color: #0a5c36 !important;
    }

    /* Sidebar with Frutiger Aero styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #e6f7fb, #c5e8ca) !important;
        border-right: 3px solid #4caf50 !important;
    }

    /* Buttons - glossy Frutiger style */
    .stButton > button {
        background: linear-gradient(to bottom, #4fc3f7, #0288d1) !important;
        color: white !important;
        border-radius: 12px !important;
        border: 1px solid #81d4fa !important;
        box-shadow: 0 4px 8px rgba(3, 169, 244, 0.3) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        background: linear-gradient(to bottom, #29b6f6, #0277bd) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(3, 169, 244, 0.4) !important;
    }

    /* Input fields with rounded corners */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 2px solid #4caf50 !important;
        background-color: rgba(255, 255, 255, 0.9) !important;
    }

    /* Slider styling */
    .stSlider > div > div > div > div {
        background-color: #4caf50 !important;
    }

    /* Metrics/Value cards */
    div[data-testid="stMetricValue"] {
        color: #0a5c36 !important;
        font-weight: 600 !important;
    }

    /* Dataframe styling */
    .stDataFrame {
        border: 1px solid #4caf50 !important;
        border-radius: 10px !important;
    }

    /* Tabs - Frutiger styling */
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(to bottom, #e8f5e9, #c8e6c9) !important;
        border-radius: 8px 8px 0 0 !important;
        border: 1px solid #81c784 !important;
        color: #0a5c36 !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(to bottom, #4caf50, #2e7d32) !important;
        color: white !important;
    }

    /* Progress bars */
    .stProgress > div > div > div > div {
        background-color: #4caf50 !important;
    }

    /* Expander */
    .stExpander {
        border: 1px solid #4caf50 !important;
        border-radius: 8px !important;
    }

    /* Alert boxes */
    .stAlert {
        border-left: 5px solid #4caf50 !important;
        border-radius: 8px !important;
    }

    /* Radio buttons background */
    .stRadio > div {
        background-color: rgba(255, 255, 255, 0.7) !important;
        border-radius: 8px !important;
        border: 1px solid #4caf50 !important;
    }

    /* Checkbox labels */
    .stCheckbox > label {
        color: #0a5c36 !important;
    }

    /* Divider */
    .stDivider {
        border-bottom: 2px solid #4caf50 !important;
    }

    /* Main content area */
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 20px rgba(0, 100, 0, 0.1) !important;
        border: 1px solid rgba(76, 175, 80, 0.2) !important;
    }

    /* Fix sidebar button colors */
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(to bottom, #4caf50, #2e7d32) !important;
        border: 1px solid #81c784 !important;
    }

    /* Fix for any white text on white background */
    p, span, div, label {
        color: #0a5c36 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    if "query_results" not in st.session_state:
        st.session_state.query_results = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"


def show_user_analisis():
    show_query_selector("o")


def show_product_manager():
    show_query_selector("ñ")


page_functions = {
    "Home": show_home,
    "Consultas SQL": show_query_selector,
    "Conversaciones": show_conversation_manager,
    "Documentos": show_document_system,
    "Análisis de Usuario": show_user_analisis,
    "Gestor de Precios": show_product_manager,
}
if __name__ == "__main__":
    init_session_state()
    sidebar()
    page_functions[st.session_state.current_page]()
