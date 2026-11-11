import streamlit as st
from style import appliquer_style, afficher_menu

st.set_page_config(
    page_title="Smart Traffic | Régulation des feux",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

appliquer_style()
afficher_menu("Régulation des feux")

st.write("Page en construction : régulation des feux et simulation.")