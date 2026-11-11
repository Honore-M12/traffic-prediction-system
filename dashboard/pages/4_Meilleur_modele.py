import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Smart Traffic | Meilleur modèle",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# DONNEES DE DEMONSTRATION
# A remplacer par les resultats reels de Joel
# =========================================================

np.random.seed(42)

n = 120

dates = pd.date_range(
    start="2020-05-01 00:00",
    periods=n,
    freq="5min"
)

actual = np.random.randint(180, 650, n)

noise = np.random.normal(0, 25, n)
predicted = np.clip(actual + noise, 87, 794)

results = pd.DataFrame({
    "Date": dates,
    "Valeurs réelles": actual,
    "Valeurs prédites": predicted
})

results["Erreur"] = (
    results["Valeurs réelles"] - results["Valeurs prédites"]
)

results["Erreur absolue"] = results["Erreur"].abs()

results["Erreur (%)"] = (
    results["Erreur absolue"] /
    results["Valeurs réelles"] * 100
)

# Métriques de démonstration
mae = results["Erreur absolue"].mean()
rmse = np.sqrt((results["Erreur"] ** 2).mean())

ss_res = ((results["Valeurs réelles"] - results["Valeurs prédites"]) ** 2).sum()
ss_tot = ((results["Valeurs réelles"] - results["Valeurs réelles"].mean()) ** 2).sum()

r2 = 1 - (ss_res / ss_tot)

# Importance illustrative des variables
feature_importance = pd.DataFrame({
    "Variable": [
        "traffic_flow_lag_1",
        "traffic_flow_lag_3",
        "hour",
        "speed_kmh",
        "is_weekend",
        "temp_celsius",
        "wind_speed_kmh",
        "precip_mm"
    ],
    "Importance": [0.29, 0.23, 0.17, 0.12, 0.08, 0.05, 0.035, 0.025]
})

# =========================================================
# STYLE GLOBAL - STYLE A
# =========================================================

st.markdown("""
<style>

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

/* HERO */

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

/* NOTICE */

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
    margin-top: 20px;
    margin-bottom: 4px;
}

.section-subtitle {
    color: #8593A3;
    font-size: 11px;
    margin-bottom: 13px;
}

/* KPI */

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

/* CHARTS */

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

/* INFO BOXES */

.info-box {
    background: white;
    border: 1px solid #E4EAF0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 10px;
}

.info-title {
    color: #263D53;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 7px;
}

.info-text {
    color: #74869A;
    font-size: 11px;
    line-height: 1.7;
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

    st.page_link(
        "pages/3_Comparaison_modeles.py",
        label="Comparaison des modèles",
        icon=":material/analytics:"
    )

    st.markdown(
        '<div class="sidebar-active">▦ &nbsp; Meilleur modèle</div>',
        unsafe_allow_html=True
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
# HEADER
# =========================================================

st.markdown("""
<div class="hero">
    <div class="hero-content">
        <div class="hero-eyebrow">SMART TRAFFIC / MODEL ANALYSIS</div>
        <div class="hero-title">Analyse du meilleur modèle</div>
        <div class="hero-description">
            Analyse détaillée des prédictions, des erreurs et de la fiabilité du modèle sélectionné.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# AVERTISSEMENT
# =========================================================

st.markdown("""
<div class="demo-notice">
    <span class="demo-badge">DEMO DATA</span>
    Les données et les résultats présentés sont illustratifs.
    Ils seront remplacés par les prédictions et métriques réelles de Joel.
</div>
""", unsafe_allow_html=True)


# =========================================================
# MODELE SELECTIONNE
# =========================================================

st.markdown(
    '<div class="section-title">Modèle sélectionné</div>',
    unsafe_allow_html=True
)

col_model, col_status = st.columns([3, 1])

with col_model:
    st.markdown("""
    <div class="info-box">
        <div class="info-title">LightGBM</div>
        <div class="info-text">
            Modèle de démonstration sélectionné selon les résultats fictifs
            de la page de comparaison. Le modèle réel sera déterminé
            à partir des résultats de validation et de test.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_status:
    st.markdown("""
    <div class="info-box">
        <div class="info-title">Statut</div>
        <div style="color:#B17C2D;font-size:12px;font-weight:700;">
            Démonstration
        </div>
        <div class="info-text">Résultats temporaires</div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# INDICATEURS
# =========================================================

st.markdown(
    '<div class="section-title">Indicateurs de performance</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">Résultats calculés sur les données de démonstration.</div>',
    unsafe_allow_html=True
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <div class="kpi-icon teal">MAE</div>
            <div class="kpi-label">Erreur absolue moyenne</div>
        </div>
        <div class="kpi-value">{mae:.2f}</div>
        <div class="kpi-foot">Véhicules / 5 min</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <div class="kpi-icon blue">RMSE</div>
            <div class="kpi-label">Erreur quadratique</div>
        </div>
        <div class="kpi-value">{rmse:.2f}</div>
        <div class="kpi-foot">Véhicules / 5 min</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <div class="kpi-icon purple">R²</div>
            <div class="kpi-label">Coefficient R²</div>
        </div>
        <div class="kpi-value">{r2:.3f}</div>
        <div class="kpi-foot">Qualité d'ajustement</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <div class="kpi-icon teal">N</div>
            <div class="kpi-label">Observations testées</div>
        </div>
        <div class="kpi-value">{len(results)}</div>
        <div class="kpi-foot">Exemples affichés</div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# ACTUAL VS PREDICTED
# =========================================================

st.markdown(
    '<div class="section-title">Valeurs réelles vs valeurs prédites</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">Comparaison entre le trafic observé et les estimations du modèle.</div>',
    unsafe_allow_html=True
)

fig_comparison = go.Figure()

fig_comparison.add_trace(go.Scatter(
    x=results["Date"],
    y=results["Valeurs réelles"],
    mode="lines",
    name="Valeurs réelles",
    line=dict(color="#263F5B", width=2)
))

fig_comparison.add_trace(go.Scatter(
    x=results["Date"],
    y=results["Valeurs prédites"],
    mode="lines",
    name="Valeurs prédites",
    line=dict(color="#20A99F", width=2, dash="dot")
))

fig_comparison.update_layout(
    template="plotly_white",
    height=360,
    margin=dict(l=30, r=20, t=35, b=35),
    font=dict(family="Arial", size=10, color="#6F8193"),
    xaxis_title="Date et heure",
    yaxis_title="Véhicules / 5 min",
    legend=dict(
        orientation="h",
        y=1.12,
        x=0
    ),
    plot_bgcolor="white",
    paper_bgcolor="white"
)

fig_comparison.update_xaxes(
    gridcolor="#EAF0F5"
)

fig_comparison.update_yaxes(
    gridcolor="#EAF0F5"
)

st.plotly_chart(
    fig_comparison,
    use_container_width=True
)


# =========================================================
# SCATTER PLOT ACTUAL VS PREDICTED
# =========================================================

st.markdown(
    '<div class="section-title">Précision des prédictions</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">Plus les points sont proches de la diagonale, plus les prédictions sont précises.</div>',
    unsafe_allow_html=True
)

fig_scatter = px.scatter(
    results,
    x="Valeurs réelles",
    y="Valeurs prédites",
    color_discrete_sequence=["#20A99F"],
    opacity=0.65
)

min_value = min(
    results["Valeurs réelles"].min(),
    results["Valeurs prédites"].min()
)

max_value = max(
    results["Valeurs réelles"].max(),
    results["Valeurs prédites"].max()
)

fig_scatter.add_trace(go.Scatter(
    x=[min_value, max_value],
    y=[min_value, max_value],
    mode="lines",
    name="Prédiction parfaite",
    line=dict(color="#D66B6B", dash="dash", width=2)
))

fig_scatter.update_layout(
    template="plotly_white",
    height=350,
    margin=dict(l=30, r=20, t=35, b=35),
    font=dict(family="Arial", size=10, color="#6F8193"),
    xaxis_title="Trafic réel (véhicules / 5 min)",
    yaxis_title="Trafic prédit (véhicules / 5 min)",
    plot_bgcolor="white",
    paper_bgcolor="white"
)

fig_scatter.update_xaxes(gridcolor="#EAF0F5")
fig_scatter.update_yaxes(gridcolor="#EAF0F5")

st.plotly_chart(
    fig_scatter,
    use_container_width=True
)


# =========================================================
# ANALYSE DES ERREURS
# =========================================================

st.markdown(
    '<div class="section-title">Analyse des erreurs de prédiction</div>',
    unsafe_allow_html=True
)

error_col1, error_col2 = st.columns(2)

with error_col1:

    fig_residuals = px.histogram(
        results,
        x="Erreur",
        nbins=25,
        color_discrete_sequence=["#438CC8"]
    )

    fig_residuals.update_layout(
        template="plotly_white",
        title="Distribution des résidus",
        height=320,
        margin=dict(l=25, r=15, t=50, b=35),
        font=dict(family="Arial", size=10, color="#6F8193"),
        xaxis_title="Erreur (réel - prédit)",
        yaxis_title="Nombre d'observations",
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(
        fig_residuals,
        use_container_width=True
    )

with error_col2:

    fig_error_time = px.line(
        results,
        x="Date",
        y="Erreur absolue",
        color_discrete_sequence=["#20A99F"]
    )

    fig_error_time.update_layout(
        template="plotly_white",
        title="Évolution de l'erreur absolue",
        height=320,
        margin=dict(l=25, r=15, t=50, b=35),
        font=dict(family="Arial", size=10, color="#6F8193"),
        xaxis_title="Date",
        yaxis_title="Erreur absolue",
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig_error_time.update_yaxes(
        gridcolor="#EAF0F5"
    )

    st.plotly_chart(
        fig_error_time,
        use_container_width=True
    )


# =========================================================
# IMPORTANCE DES VARIABLES
# =========================================================

st.markdown(
    '<div class="section-title">Importance des variables</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">Illustration des variables susceptibles de contribuer aux prédictions. À remplacer par les importances réelles du modèle.</div>',
    unsafe_allow_html=True
)

importance_sorted = feature_importance.sort_values(
    by="Importance",
    ascending=True
)

fig_importance = px.bar(
    importance_sorted,
    x="Importance",
    y="Variable",
    orientation="h",
    text="Importance",
    color_discrete_sequence=["#438CC8"]
)

fig_importance.update_traces(
    texttemplate="%{text:.1%}",
    textposition="outside"
)

fig_importance.update_layout(
    template="plotly_white",
    height=370,
    margin=dict(l=25, r=45, t=25, b=35),
    font=dict(family="Arial", size=10, color="#6F8193"),
    xaxis_title="Importance relative",
    yaxis_title="",
    showlegend=False,
    plot_bgcolor="white",
    paper_bgcolor="white"
)

fig_importance.update_xaxes(
    gridcolor="#EAF0F5",
    tickformat=".0%"
)

st.plotly_chart(
    fig_importance,
    use_container_width=True
)


# =========================================================
# TABLEAU DES PREDICTIONS
# =========================================================

st.markdown(
    '<div class="section-title">Détail des prédictions</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">Extrait des observations utilisées pour évaluer le modèle.</div>',
    unsafe_allow_html=True
)

display_df = results.copy()

display_df["Date"] = display_df["Date"].dt.strftime(
    "%d/%m/%Y %H:%M"
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Valeurs réelles": st.column_config.NumberColumn(
            "Trafic réel",
            format="%.0f"
        ),
        "Valeurs prédites": st.column_config.NumberColumn(
            "Trafic prédit",
            format="%.1f"
        ),
        "Erreur": st.column_config.NumberColumn(
            "Résidu",
            format="%.1f"
        ),
        "Erreur absolue": st.column_config.NumberColumn(
            "Erreur absolue",
            format="%.1f"
        ),
        "Erreur (%)": st.column_config.NumberColumn(
            "Erreur (%)",
            format="%.2f%%"
        )
    }
)


# =========================================================
# LIMITES ET OBSERVATIONS
# =========================================================

st.markdown(
    '<div class="section-title">Limites et observations</div>',
    unsafe_allow_html=True
)

limit1, limit2 = st.columns(2)

with limit1:
    st.markdown("""
    <div class="info-box">
        <div class="info-title">Limites des données</div>
        <div class="info-text">
            Le jeu de données représente une série agrégée de trafic
            routier. Il ne décrit pas directement le trafic par voie
            ou par intersection.<br><br>
            La période étudiée couvre février à mai 2020.
            Les changements de circulation liés à la période COVID-19
            peuvent limiter la généralisation à une année normale.
        </div>
    </div>
    """, unsafe_allow_html=True)

with limit2:
    st.markdown("""
    <div class="info-box">
        <div class="info-title">Points à surveiller</div>
        <div class="info-text">
            Les performances doivent être interprétées sur un jeu
            de test chronologique indépendant.<br><br>
            Les erreurs peuvent varier selon l'heure, les conditions
            météorologiques et les changements de trafic.
            Une validation sur d'autres périodes serait utile
            pour évaluer la généralisation du modèle.
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# CONCLUSION
# =========================================================

st.markdown("""
<div class="info-box">
    <div class="info-title">Conclusion de l'analyse</div>
    <div class="info-text">
        Cette page permet d'évaluer le comportement du modèle
        sélectionné en comparant ses prédictions aux valeurs réelles,
        en étudiant la distribution de ses erreurs et en visualisant
        les variables utilisées. Les conclusions définitives seront
        établies après intégration des résultats réels de l'équipe ML.
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="dashboard-footer">
    SMART TRAFFIC — TRAFFIC INTELLIGENCE PLATFORM
</div>
""", unsafe_allow_html=True)