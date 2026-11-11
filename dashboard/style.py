import streamlit as st

# =========================================================
# STYLE CSS COMMUN À TOUTES LES PAGES (design de Mireille)
# =========================================================

CSS = """
<style>

/* GENERAL */

.stApp {
    background: #F3F6FA;
    color: #24364B;
}

.block-container {
    max-width: 1600px;
    padding: 0.6rem 2rem 2.5rem 2rem !important;
}

header[data-testid="stHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    background: transparent !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

[data-testid="stDecoration"] {
    display: none !important;
}

#MainMenu, footer {
    visibility: hidden;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: #102A43;
    border-right: 1px solid #29435D;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 0.3rem 0.55rem 1rem 0.55rem !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
}

[data-testid="stSidebarNav"] {
    display: none !important;
}

/* BRAND */

.brand-container {
    padding: 12px 8px 18px 8px;
    border-bottom: 1px solid rgba(255,255,255,0.15);
    margin-bottom: 16px;
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 9px;
}

.brand-logo {
    width: 35px;
    height: 35px;
    border-radius: 8px;
    background: linear-gradient(135deg, #42B9C3, #287A9E);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 18px;
    font-weight: 800;
}

.brand-name {
    color: white;
    font-size: 17px;
    font-weight: 700;
}

.brand-subtitle {
    color: #9CB2C7;
    font-size: 9px;
    letter-spacing: 0.6px;
    margin-left: 44px;
    margin-top: -3px;
}

.nav-heading {
    color: #829BB2;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.3px;
    margin: 15px 8px 9px 8px;
}

.sidebar-active {
    background: #254765;
    border-left: 3px solid #43BEC5;
    border-radius: 6px;
    padding: 10px 9px;
    margin: 3px 0;
    color: white;
    font-size: 12px;
    font-weight: 600;
}

[data-testid="stSidebar"] [data-testid="stPageLink"] {
    border-radius: 6px;
    margin: 3px 0;
    padding: 2px 8px;
}

[data-testid="stSidebar"] [data-testid="stPageLink"]:hover {
    background: rgba(255,255,255,0.10);
}

[data-testid="stSidebar"] [data-testid="stPageLink"] p {
    color: #D6E2ED !important;
    font-size: 12px;
}

.sidebar-footer {
    border-top: 1px solid rgba(255,255,255,0.14);
    padding: 13px 8px;
    margin-top: 25px;
    color: #8FA8BE;
    font-size: 10px;
    line-height: 1.8;
}

/* HERO HEADER */

.hero {
    position: relative;
    overflow: hidden;
    height: 145px;
    border-radius: 9px;
    margin: 0 0 17px 0;
    padding: 25px 30px;
    background: linear-gradient(105deg, #102A43 0%, #174A68 65%, #246B80 100%);
    box-shadow: 0 3px 12px rgba(16,42,67,0.12);
}

.hero:before {
    content: "";
    position: absolute;
    right: -30px;
    top: -90px;
    width: 480px;
    height: 300px;
    background: radial-gradient(ellipse, rgba(115,190,207,0.30), transparent 68%);
}

.hero:after {
    content: "";
    position: absolute;
    right: 0;
    bottom: 0;
    width: 52%;
    height: 75px;
    opacity: 0.35;
    background:
        linear-gradient(155deg, transparent 48%, #9CCAD5 49%, #9CCAD5 50%, transparent 51%),
        linear-gradient(165deg, transparent 58%, #9CCAD5 59%, #9CCAD5 60%, transparent 61%);
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-eyebrow {
    color: #83D2D8;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.6px;
    margin-bottom: 9px;
}

.hero-title {
    color: white;
    font-size: 27px;
    font-weight: 700;
    margin: 0 0 7px 0;
}

.hero-description {
    color: #D7E6EF;
    font-size: 12px;
    margin: 0;
}

/* DEMO NOTICE */

.demo-notice {
    background: #FFF8E9;
    border: 1px solid #F0E2C4;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 0 0 20px 0;
    color: #80683A;
    font-size: 11px;
}

.demo-badge {
    background: #F2E4C7;
    color: #8D6A2D;
    padding: 4px 7px;
    border-radius: 4px;
    font-size: 9px;
    font-weight: 700;
    margin-right: 9px;
}

/* SECTION TITLES */

.section-title {
    color: #20364D;
    font-size: 16px;
    font-weight: 700;
    margin-top: 18px;
    margin-bottom: 4px;
}

.section-subtitle {
    color: #8593A3;
    font-size: 11px;
    margin-bottom: 12px;
}

/* FILTERS */

.stMultiSelect label,
.stSelectbox label {
    color: #43566A;
    font-size: 11px;
    font-weight: 600;
}

/* KPI CARDS */

.kpi-card {
    background: white;
    border: 1px solid #E4EAF0;
    border-radius: 8px;
    padding: 13px 14px;
    min-height: 105px;
    box-shadow: 0 2px 8px rgba(29,55,80,0.04);
}

.kpi-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
}

.kpi-icon {
    width: 23px;
    height: 23px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
}

.teal {
    background: #DDF3F1;
    color: #168E88;
}

.blue {
    background: #E3EDFC;
    color: #3978C7;
}

.purple {
    background: #F0E8FA;
    color: #9465C2;
}

.kpi-label {
    color: #718398;
    font-size: 9px;
    font-weight: 600;
}

.kpi-value {
    color: #172D46;
    font-size: 23px;
    font-weight: 750;
}

.kpi-foot {
    color: #91A0AF;
    font-size: 9px;
    margin-top: 5px;
}

/* GRAPHIQUES */

[data-testid="stPlotlyChart"] {
    background: white;
    border: 1px solid #E5EAF0;
    border-radius: 8px;
    padding: 3px;
    box-shadow: 0 2px 8px rgba(29,55,80,0.035);
}

/* TABLE */

[data-testid="stDataFrame"] {
    background: white;
    border: 1px solid #E4EAF0;
    border-radius: 8px;
}

/* FOOTER */

.dashboard-footer {
    border-top: 1px solid #E0E7EE;
    padding-top: 12px;
    margin-top: 25px;
    text-align: center;
    color: #9AA7B4;
    font-size: 9px;
    letter-spacing: 0.7px;
}

</style>
"""


def appliquer_style():
    """Injecte le CSS commun dans la page."""
    st.markdown(CSS, unsafe_allow_html=True)


# =========================================================
# MENU LATÉRAL COMMUN
# =========================================================

# Les 6 pages du dashboard : (fichier, nom affiché, icône)
PAGES = [
    ("app.py", "Tableau de bord", ":material/dashboard:"),
    ("pages/2_Exploration.py", "Exploration", ":material/query_stats:"),
    ("pages/3_Comparaison_modeles.py", "Comparaison des modèles", ":material/leaderboard:"),
    ("pages/4_Meilleur_modele.py", "Meilleur modèle", ":material/analytics:"),
    ("pages/5_Regulation_feux.py", "Régulation des feux", ":material/traffic:"),
    ("pages/6_Prediction.py", "Prédiction", ":material/online_prediction:"),
]


def afficher_menu(page_active):
    """Affiche le menu latéral. page_active = nom de la page où l'on se trouve."""
    with st.sidebar:

        # Logo et nom de la plateforme
        st.markdown("""
<div class="brand-container">
    <div class="brand-row">
        <div class="brand-logo">S</div>
        <div class="brand-name">Smart Traffic</div>
    </div>
    <div class="brand-subtitle">Traffic Intelligence Platform</div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="nav-heading">NAVIGATION PRINCIPALE</div>', unsafe_allow_html=True)

        # Un lien par page, sauf la page active qui est surlignée
        for fichier, nom, icone in PAGES:
            if nom == page_active:
                st.markdown(f'<div class="sidebar-active">▦ &nbsp; {nom}</div>', unsafe_allow_html=True)
            else:
                st.page_link(fichier, label=nom, icon=icone)

        # Pied du menu
        st.markdown("""
<div class="sidebar-footer">
    <strong style="color:#DCE7F0;">SMART TRAFFIC</strong><br>
    Machine Learning & Traffic Analysis<br>
    PROJECT VERSION 1.0
</div>
""", unsafe_allow_html=True)
        

# =========================================================
# ÉLÉMENTS VISUELS RÉUTILISABLES
# =========================================================

def afficher_banniere(titre, description, surtitre="SMART TRAFFIC"):
    """Affiche le bandeau bleu en haut de la page."""
    st.markdown(f"""
<div class="hero">
<div class="hero-content">
<div class="hero-eyebrow">{surtitre}</div>
<div class="hero-title">{titre}</div>
<div class="hero-description">{description}</div>
</div>
</div>
""", unsafe_allow_html=True)


def titre_section(titre, sous_titre=None):
    """Affiche un titre de section, avec un sous-titre facultatif."""
    st.markdown(f'<div class="section-title">{titre}</div>', unsafe_allow_html=True)
    if sous_titre:
        st.markdown(f'<div class="section-subtitle">{sous_titre}</div>', unsafe_allow_html=True)


def carte_kpi(label, valeur, pied, icone="▦", couleur="teal"):
    """Affiche une carte KPI (couleurs possibles : teal, blue, purple)."""
    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-header"><div class="kpi-icon {couleur}">{icone}</div><div class="kpi-label">{label}</div></div>
<div class="kpi-value">{valeur}</div>
<div class="kpi-foot">{pied}</div>
</div>
""", unsafe_allow_html=True)
    

def styliser_graphique(fig, titre, titre_y, hauteur=320):
    """Applique le style commun (inspiré de Mireille) à un graphique plotly."""
    fig.update_layout(
        template="plotly_white",
        title=dict(text=titre, font=dict(size=12, color="#263A50"), x=0.02),
        height=hauteur,
        margin=dict(l=25, r=15, t=48, b=38),
        font=dict(family="Arial", size=10, color="#6F8193"),
        xaxis_title="",
        yaxis_title=titre_y,
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#EAF0F5", zeroline=False)
    return fig