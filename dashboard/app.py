import streamlit as st
from style import appliquer_style, afficher_menu

st.set_page_config(
    page_title="Smart Traffic | Tableau de bord",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

appliquer_style()
afficher_menu("Tableau de bord")

st.write("Page en construction : Vue d'ensemble (KPI).")