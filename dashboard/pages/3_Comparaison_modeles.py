import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Smart Traffic | Comparaison des modèles",
    page_icon=None ,
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# DONNEES DE DEMONSTRATION
# A remplacer par les resultats reels de Joel
# =========================================================

data = {
    "Modèle": [
        "Linear Regression",
        "Decision Tree",
        "Random Forest",
        "XGBoost",
        "LightGBM"
    ],
    "MAE": [42.5, 35.8, 27.4, 23.6, 22.1],
    "RMSE": [56.2, 48.3, 37.5, 32.8, 30.9],
    "R²": [0.72, 0.81, 0.89, 0.92, 0.93]
}

df = pd.DataFrame(data)

# =========================================================
# STYLE CSS
# =========================================================

st.markdown("""
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
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("""
<div class="brand-container">
    <div class="brand-row">
        <div class="brand-logo">S</div>
        <div class="brand-name">Smart Traffic</div>
    </div>
    <div class="brand-subtitle">Traffic Intelligence Platform</div>
</div>
""", unsafe_allow_html=True)

    st.markdown(
        '<div class="nav-heading">NAVIGATION PRINCIPALE</div>',
        unsafe_allow_html=True
    )

    st.page_link(
        "app.py",
        label="Tableau de bord",
        icon=":material/dashboard:"
    )

    st.markdown(
        '<div class="sidebar-active">▦ &nbsp; Comparaison des modèles</div>',
        unsafe_allow_html=True
    )

    st.page_link(
        "pages/4_Meilleur_modele.py",
        label="Meilleur modèle",
        icon=":material/analytics:"
    )

    st.page_link(
        "pages/6_Prediction.py",
        label="Prédiction",
        icon=":material/online_prediction:"
    )

    st.markdown("""
<div class="sidebar-footer">
    <strong style="color:#DCE7F0;">SMART TRAFFIC</strong><br>
    Machine Learning & Traffic Analysis<br>
    PROJECT VERSION 1.0
</div>
""", unsafe_allow_html=True)


# =========================================================
# HEADER PRINCIPAL
# =========================================================

st.markdown("""
<div class="hero">
<div class="hero-content">
<div class="hero-eyebrow">SMART TRAFFIC / ANALYTICS</div>
<div class="hero-title">Comparaison des modèles</div>
<div class="hero-description">Évaluation des performances des algorithmes de prédiction du trafic routier.</div>
</div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# AVERTISSEMENT
# =========================================================

st.markdown("""
<div class="demo-notice">
<span class="demo-badge">DEMO DATA</span>
Les performances affichées sont provisoires et seront remplacées par les résultats réels des modèles entraînés.
</div>
""", unsafe_allow_html=True)


# =========================================================
# PARAMETRES DE COMPARAISON
# =========================================================

st.markdown(
    '<div class="section-title">Paramètres de comparaison</div>',
    unsafe_allow_html=True
)

filter_col, metric_col = st.columns([2, 1])

with filter_col:
    selected_models = st.multiselect(
        "Modèles à comparer",
        options=df["Modèle"].tolist(),
        default=df["Modèle"].tolist()
    )

with metric_col:
    ranking_metric = st.selectbox(
        "Critère de classement",
        ["RMSE", "MAE", "R²"]
    )

filtered_df = df[df["Modèle"].isin(selected_models)].copy()

if filtered_df.empty:
    st.warning("Sélectionnez au moins un modèle.")
    st.stop()


# =========================================================
# CALCUL DES INDICATEURS
# =========================================================

if ranking_metric == "R²":
    best_model = filtered_df.loc[filtered_df["R²"].idxmax()]
else:
    best_model = filtered_df.loc[filtered_df[ranking_metric].idxmin()]

best_mae = filtered_df["MAE"].min()
best_r2 = filtered_df["R²"].max()


# =========================================================
# KPI
# =========================================================

st.markdown(
    '<div class="section-title">Synthèse des performances</div>',
    unsafe_allow_html=True
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-header"><div class="kpi-icon teal">▦</div><div class="kpi-label">Modèles évalués</div></div>
<div class="kpi-value">{len(filtered_df)}</div>
<div class="kpi-foot">Algorithmes comparés</div>
</div>
""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-header"><div class="kpi-icon blue">♛</div><div class="kpi-label">Meilleur modèle</div></div>
<div class="kpi-value" style="font-size:19px">{best_model["Modèle"]}</div>
<div class="kpi-foot">Selon {ranking_metric}</div>
</div>
""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-header"><div class="kpi-icon blue">↘</div><div class="kpi-label">Meilleur MAE</div></div>
<div class="kpi-value">{best_mae:.2f}</div>
<div class="kpi-foot">Véhicules / 5 min</div>
</div>
""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-header"><div class="kpi-icon purple">R²</div><div class="kpi-label">Meilleur R²</div></div>
<div class="kpi-value">{best_r2:.3f}</div>
<div class="kpi-foot">Coefficient de détermination</div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# STYLE DES GRAPHIQUES
# =========================================================

def configure_chart(fig, title, y_title):

    fig.update_traces(
        textposition="outside",
        marker_line_width=0
    )

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=title,
            font=dict(size=12, color="#263A50"),
            x=0.04
        ),
        height=275,
        margin=dict(l=25, r=15, t=48, b=38),
        font=dict(family="Arial", size=9, color="#6F8193"),
        xaxis_title="",
        yaxis_title=y_title,
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig.update_xaxes(
        tickangle=0,
        showgrid=False,
        automargin=True
    )

    fig.update_yaxes(
        gridcolor="#EAF0F5",
        zeroline=False
    )

    return fig


# =========================================================
# GRAPHIQUES MAE ET RMSE
# =========================================================

st.markdown(
    '<div class="section-title">Analyse des performances</div>',
    unsafe_allow_html=True
)

chart1, chart2 = st.columns(2)

with chart1:

    fig_mae = px.bar(
        filtered_df,
        x="Modèle",
        y="MAE",
        text="MAE",
        color_discrete_sequence=["#20A99F"]
    )

    fig_mae.update_traces(texttemplate="%{text:.1f}")

    fig_mae = configure_chart(
        fig_mae,
        "MAE — Erreur absolue moyenne",
        "Véhicules / 5 min"
    )

    st.plotly_chart(fig_mae, use_container_width=True)


with chart2:

    fig_rmse = px.bar(
        filtered_df,
        x="Modèle",
        y="RMSE",
        text="RMSE",
        color_discrete_sequence=["#438CC8"]
    )

    fig_rmse.update_traces(texttemplate="%{text:.1f}")

    fig_rmse = configure_chart(
        fig_rmse,
        "RMSE — Erreur quadratique",
        "Véhicules / 5 min"
    )

    st.plotly_chart(fig_rmse, use_container_width=True)


# =========================================================
# GRAPHIQUE R²
# =========================================================

fig_r2 = px.bar(
    filtered_df,
    x="Modèle",
    y="R²",
    text="R²",
    color_discrete_sequence=["#956AC5"]
)

fig_r2.update_traces(texttemplate="%{text:.2f}")

fig_r2 = configure_chart(
    fig_r2,
    "R² — Coefficient de détermination",
    "Score R²"
)

fig_r2.update_yaxes(range=[0, 1.08])

st.plotly_chart(fig_r2, use_container_width=True)


# =========================================================
# CLASSEMENT
# =========================================================

st.markdown(
    '<div class="section-title">Classement des modèles</div>',
    unsafe_allow_html=True
)

ascending = ranking_metric != "R²"

ranking_df = filtered_df.sort_values(
    by=ranking_metric,
    ascending=ascending
).reset_index(drop=True)

ranking_df.insert(0, "Rang", range(1, len(ranking_df) + 1))

ranking_df = ranking_df.rename(
    columns={"Modèle": "Algorithme"}
)

st.dataframe(
    ranking_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Rang": st.column_config.NumberColumn("Rang", format="%d"),
        "MAE": st.column_config.NumberColumn("MAE", format="%.2f"),
        "RMSE": st.column_config.NumberColumn("RMSE", format="%.2f"),
        "R²": st.column_config.NumberColumn("R²", format="%.3f")
    }
)


# =========================================================
# CONCLUSION
# =========================================================

st.success(
    f"Meilleur modèle selon {ranking_metric} : {best_model['Modèle']}"
)

st.markdown("""
<div class="dashboard-footer">
SMART TRAFFIC — TRAFFIC INTELLIGENCE PLATFORM
</div>
""", unsafe_allow_html=True)