import streamlit as st
from style import appliquer_style, afficher_menu

st.set_page_config(
    page_title="Smart Traffic | Exploration",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

appliquer_style()
afficher_menu("Exploration")

st.write("Page en construction : exploration des données.")