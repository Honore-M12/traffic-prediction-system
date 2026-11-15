import streamlit as st
import base64
from pathlib import Path


# =========================================================
# CONFIGURATION DU LOGO
# =========================================================

DOSSIER_STYLE = Path(__file__).resolve().parent
LOGO_PATH = DOSSIER_STYLE / "assets" / "feu-de-circulation.png"


def charger_logo():
    if LOGO_PATH.exists():
        with open(LOGO_PATH, "rb") as fichier:
            image_base64 = base64.b64encode(
                fichier.read()
            ).decode("utf-8")

        return f"data:image/png;base64,{image_base64}"

    return None


LOGO_BASE64 = charger_logo()


# =========================================================
# STYLE CSS COMMUN
# =========================================================

CSS = """
<style>

/* =====================================================
   GENERAL
===================================================== */

.stApp {
    background: #F4F7FA;
    color: #24364B;
    font-family: Arial, sans-serif;
}

.block-container {
    max-width: 1600px;
    padding: 1.1rem 2rem 2.5rem 2rem !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    display: none !important;
}

#MainMenu,
footer {
    visibility: hidden;
}


/* =====================================================
   SIDEBAR
===================================================== */

[data-testid="stSidebar"] {
    background: #102A43;
    border-right: 1px solid #25435D;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 0.6rem 0.65rem 1rem 0.65rem !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
}

[data-testid="stSidebarNav"] {
    display: none !important;
}


/* =====================================================
   IDENTITE VISUELLE
===================================================== */

.brand-container {
    padding: 15px 8px 20px 8px;
    border-bottom: 1px solid rgba(255,255,255,0.14);
    margin-bottom: 20px;
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 11px;
}

.brand-logo-img {
    width: 38px;
    height: 38px;
    object-fit: contain;
    display: block;
    flex-shrink: 0;
}

.brand-fallback {
    width: 38px;
    height: 38px;
    border-radius: 9px;
    background: linear-gradient(135deg, #35B9B0, #287A9E);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 19px;
    font-weight: 800;
    flex-shrink: 0;
}

.brand-name {
    color: white;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.1px;
}

.brand-subtitle {
    color: #A9BED0;
    font-size: 10px;
    margin-left: 49px;
    margin-top: -3px;
}


/* =====================================================
   NAVIGATION
===================================================== */

.nav-heading {
    color: #91A9BE;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.2px;
    margin: 18px 8px 12px 8px;
}

.sidebar-active {
    background: #254765;
    border-left: 3px solid #36B9B0;
    border-radius: 7px;
    padding: 11px 10px;
    margin: 4px 0;
    color: white;
    font-size: 12px;
    font-weight: 650;
}

[data-testid="stSidebar"] [data-testid="stPageLink"] {
    border-radius: 7px;
    margin: 4px 0;
    padding: 3px 9px;
    transition: background 0.2s ease;
}

[data-testid="stSidebar"] [data-testid="stPageLink"]:hover {
    background: rgba(255,255,255,0.10);
}

[data-testid="stSidebar"] [data-testid="stPageLink"] p {
    color: #D6E2ED !important;
    font-size: 12px;
}

[data-testid="stSidebar"] [data-testid="stPageLink"] svg {
    color: #80BFC8 !important;
}


/* =====================================================
   PIED DE SIDEBAR
===================================================== */

.sidebar-footer {
    border-top: 1px solid rgba(255,255,255,0.14);
    padding: 15px 8px;
    margin-top: 28px;
    color: #A9BED0;
    font-size: 10px;
    line-height: 1.8;
}


/* =====================================================
   BANNIERE PRINCIPALE
===================================================== */

.hero {
    position: relative;
    overflow: hidden;
    min-height: 135px;
    border-radius: 11px;
    margin: 0 0 24px 0;
    padding: 25px 30px;
    background: linear-gradient(
        110deg,
        #102A43 0%,
        #174A68 65%,
        #246B80 100%
    );
    box-shadow: 0 4px 14px rgba(16,42,67,0.10);
}

.hero:before {
    content: "";
    position: absolute;
    right: -30px;
    top: -90px;
    width: 450px;
    height: 300px;
    background: radial-gradient(
        ellipse,
        rgba(115,190,207,0.22),
        transparent 70%
    );
}

.hero:after {
    content: "";
    position: absolute;
    right: 0;
    bottom: 0;
    width: 45%;
    height: 65px;
    opacity: 0.22;
    background:
        linear-gradient(
            155deg,
            transparent 48%,
            #9CCAD5 49%,
            #9CCAD5 50%,
            transparent 51%
        ),
        linear-gradient(
            165deg,
            transparent 58%,
            #9CCAD5 59%,
            #9CCAD5 60%,
            transparent 61%
        );
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-eyebrow {
    color: #80D3D1;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
}

.hero-title {
    color: white;
    font-size: 27px;
    font-weight: 700;
    margin: 0 0 8px 0;
}

.hero-description {
    color: #D7E6EF;
    font-size: 12px;
    margin: 0;
}


/* =====================================================
   TITRES DE SECTION
===================================================== */

.section-title {
    color: #20364D;
    font-size: 16px;
    font-weight: 700;
    margin-top: 23px;
    margin-bottom: 5px;
}

.section-subtitle {
    color: #8192A5;
    font-size: 11px;
    margin-bottom: 14px;
}


/* =====================================================
   FILTRES
===================================================== */

.stMultiSelect label,
.stSelectbox label,
.stDateInput label,
.stSlider label,
.stRadio label {
    color: #43566A;
    font-size: 11px;
    font-weight: 600;
}

[data-testid="stMultiSelect"] [data-baseweb="tag"] {
    background-color: #DCEDEA !important;
    color: #176F6B !important;
}

[data-baseweb="input"],
[data-baseweb="select"] > div {
    border-radius: 7px !important;
}


/* =====================================================
   CARTES KPI
===================================================== */

.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E3EAF0;
    border-radius: 10px;
    padding: 15px 16px;
    min-height: 110px;
    box-shadow: 0 3px 10px rgba(29,55,80,0.035);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(29,55,80,0.08);
}

.kpi-header {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-bottom: 11px;
}

.kpi-icon {
    width: 25px;
    height: 25px;
    border-radius: 7px;
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
    font-size: 10px;
    font-weight: 600;
}

.kpi-value {
    color: #172D46;
    font-size: 24px;
    font-weight: 750;
    line-height: 1.3;
}

.kpi-foot {
    color: #91A0AF;
    font-size: 9px;
    margin-top: 6px;
}


/* =====================================================
   GRAPHIQUES
===================================================== */

[data-testid="stPlotlyChart"] {
    background: white;
    border: 1px solid #E5EAF0;
    border-radius: 10px;
    padding: 5px;
    box-shadow: 0 3px 10px rgba(29,55,80,0.035);
}


/* =====================================================
   TABLEAUX
===================================================== */

[data-testid="stDataFrame"] {
    background: white;
    border: 1px solid #E4EAF0;
    border-radius: 9px;
    overflow: hidden;
}


/* =====================================================
   MESSAGES ET INDICATEURS
===================================================== */

[data-testid="stAlert"] {
    border-radius: 9px;
}


/* =====================================================
   FOOTER
===================================================== */

.dashboard-footer {
    border-top: 1px solid #E0E7EE;
    padding-top: 14px;
    margin-top: 30px;
    text-align: center;
    color: #91A0AF;
    font-size: 9px;
    letter-spacing: 0.4px;
}

</style>
"""


# =========================================================
# APPLICATION DU STYLE
# =========================================================

def appliquer_style():
    """Injecte le CSS commun dans la page."""
    st.markdown(CSS, unsafe_allow_html=True)


# =========================================================
# MENU LATÉRAL COMMUN
# =========================================================

PAGES = [
    ("app.py", "Tableau de bord", ":material/dashboard:"),
    ("pages/2_Exploration.py", "Exploration", ":material/query_stats:"),
    ("pages/3_Comparaison_modeles.py", "Comparaison des modèles", ":material/leaderboard:"),
    ("pages/4_Meilleur_modele.py", "Meilleur modèle", ":material/analytics:"),
    ("pages/5_Regulation_feux.py", "Régulation des feux", ":material/traffic:"),
    ("pages/6_Prediction.py", "Prédiction", ":material/online_prediction:"),
]


def afficher_menu(page_active):
    """Affiche le menu latéral commun."""

    with st.sidebar:

        if LOGO_BASE64:
            logo_html = (
                '<img class="brand-logo-img" '
                f'src="{LOGO_BASE64}" '
                'alt="Smart Traffic">'
            )
        else:
            logo_html = '<div class="brand-fallback">S</div>'

        brand_html = (
            '<div class="brand-container">'
            '<div class="brand-row">'
            f'{logo_html}'
            '<div class="brand-name">Smart Traffic</div>'
            '</div>'
            '<div class="brand-subtitle">'
            'Supervision du trafic routier'
            '</div>'
            '</div>'
        )

        st.markdown(
            brand_html,
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="nav-heading">NAVIGATION</div>',
            unsafe_allow_html=True
        )

        for fichier, nom, icone in PAGES:

            if nom == page_active:
                st.markdown(
                    f'<div class="sidebar-active">▦ &nbsp; {nom}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.page_link(
                    fichier,
                    label=nom,
                    icon=icone
                )



# =========================================================
# BANNIERE
# =========================================================

def afficher_banniere(
    titre,
    description,
    surtitre="SUPERVISION ROUTIÈRE"
):
    """Affiche la bannière principale."""

    html = (
        '<div class="hero">'
        '<div class="hero-content">'
        f'<div class="hero-eyebrow">{surtitre}</div>'
        f'<div class="hero-title">{titre}</div>'
        f'<div class="hero-description">{description}</div>'
        '</div>'
        '</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True
    )


# =========================================================
# TITRES DE SECTION
# =========================================================

def titre_section(titre, sous_titre=None):
    """Affiche un titre de section."""

    st.markdown(
        f'<div class="section-title">{titre}</div>',
        unsafe_allow_html=True
    )

    if sous_titre:
        st.markdown(
            f'<div class="section-subtitle">{sous_titre}</div>',
            unsafe_allow_html=True
        )


# =========================================================
# CARTES KPI
# =========================================================

def carte_kpi(
    label,
    valeur,
    pied,
    icone="▦",
    couleur="teal"
):
    """Affiche une carte KPI."""

    html = (
        '<div class="kpi-card">'
        '<div class="kpi-header">'
        f'<div class="kpi-icon {couleur}">{icone}</div>'
        f'<div class="kpi-label">{label}</div>'
        '</div>'
        f'<div class="kpi-value">{valeur}</div>'
        f'<div class="kpi-foot">{pied}</div>'
        '</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True
    )


# =========================================================
# STYLISATION DES GRAPHIQUES PLOTLY
# =========================================================

def styliser_graphique(
    fig,
    titre,
    titre_y,
    hauteur=320
):
    """
    Applique le style commun aux graphiques Plotly.
    """

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=titre,
            font=dict(
                size=13,
                color="#263A50"
            ),
            x=0.02
        ),
        height=hauteur,
        margin=dict(
            l=30,
            r=20,
            t=50,
            b=40
        ),
        font=dict(
            family="Arial",
            size=11,
            color="#6F8193"
        ),
        xaxis_title="",
        yaxis_title=titre_y,
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        )
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#E5EAF0"
    )

    fig.update_yaxes(
        gridcolor="#EAF0F5",
        zeroline=False
    )

    return fig