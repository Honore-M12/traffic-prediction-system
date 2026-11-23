from pathlib import Path
import sys

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Régulation des feux | Smart Traffic",
    page_icon="🚦",
    layout="wide"
)

RACINE = Path(__file__).resolve().parents[2]
DOSSIER_RESULTATS = RACINE / "results"

FICHIER_SIMULATION = DOSSIER_RESULTATS / "simulation.csv"
FICHIER_RESUME = DOSSIER_RESULTATS / "simulation_summary.csv"

sys.path.insert(0, str(RACINE / "dashboard"))

from style import (
    appliquer_style,
    afficher_menu,
    afficher_banniere,
    titre_section
)

appliquer_style()
afficher_menu("Régulation des feux")


# ============================================================
# STYLE LOCAL
# ============================================================

st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background: transparent;
        border: none;
        padding: 0;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 13px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 29px;
    }

    div[data-testid="stMetricDelta"] {
        font-size: 12px;
    }

    .info-simulation {
        background: #EAF2F8;
        border-left: 4px solid #259D9A;
        padding: 12px 16px;
        border-radius: 6px;
        color: #29445D;
        font-size: 13px;
        margin-bottom: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

@st.cache_data
def charger_donnees():

    simulation = pd.read_csv(FICHIER_SIMULATION)
    resume = pd.read_csv(FICHIER_RESUME)

    simulation["datetime"] = pd.to_datetime(
        simulation["datetime"],
        errors="coerce"
    )

    colonnes_numeriques = [
        "traffic_flow",
        "predicted_flow",
        "fixed_avg_wait_s",
        "fixed_avg_speed_kmh",
        "fixed_stops_per_veh",
        "fixed_co2_g_per_veh",
        "fixed_n_vehicles",
        "fixed_avg_queue_veh",
        "fixed_green_main_s",
        "fixed_green_secondary_s",
        "fixed_cycle_s",
        "ai_avg_wait_s",
        "ai_avg_speed_kmh",
        "ai_stops_per_veh",
        "ai_co2_g_per_veh",
        "ai_n_vehicles",
        "ai_avg_queue_veh",
        "ai_green_main_s",
        "ai_green_secondary_s",
        "ai_cycle_s"
    ]

    for colonne in colonnes_numeriques:
        if colonne in simulation.columns:
            simulation[colonne] = pd.to_numeric(
                simulation[colonne],
                errors="coerce"
            )

    for colonne in ["fixed", "ai", "gain_pct"]:
        if colonne in resume.columns:
            resume[colonne] = pd.to_numeric(
                resume[colonne],
                errors="coerce"
            )

    simulation = (
        simulation
        .dropna(subset=["datetime"])
        .sort_values("datetime")
        .reset_index(drop=True)
    )

    return simulation, resume


try:
    simulation, resume = charger_donnees()

except FileNotFoundError as erreur:
    st.error(
        f"Fichier introuvable : {erreur.filename}"
    )
    st.stop()

except Exception as erreur:
    st.error(
        f"Erreur lors du chargement des résultats : {erreur}"
    )
    st.stop()


# ============================================================
# VÉRIFICATION DES COLONNES
# ============================================================

colonnes_requises = [
    "datetime",
    "traffic_flow",
    "predicted_flow",
    "congestion_level",
    "fixed_avg_wait_s",
    "fixed_avg_queue_veh",
    "fixed_avg_speed_kmh",
    "fixed_stops_per_veh",
    "fixed_co2_g_per_veh",
    "fixed_green_main_s",
    "fixed_green_secondary_s",
    "fixed_cycle_s",
    "ai_avg_wait_s",
    "ai_avg_queue_veh",
    "ai_avg_speed_kmh",
    "ai_stops_per_veh",
    "ai_co2_g_per_veh",
    "ai_green_main_s",
    "ai_green_secondary_s",
    "ai_cycle_s"
]

colonnes_manquantes = [
    colonne
    for colonne in colonnes_requises
    if colonne not in simulation.columns
]

if colonnes_manquantes:
    st.error(
        "Colonnes manquantes dans simulation.csv : "
        + ", ".join(colonnes_manquantes)
    )
    st.stop()


colonnes_resume = {
    "scope",
    "indicator",
    "fixed",
    "ai",
    "gain_pct"
}

if not colonnes_resume.issubset(resume.columns):
    st.error(
        "La structure de simulation_summary.csv est incorrecte."
    )
    st.stop()


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def gain_pourcentage(fixe, ia):
    """Gain relatif de l'IA par rapport au cycle fixe."""

    if pd.isna(fixe) or pd.isna(ia) or fixe == 0:
        return 0.0

    return ((fixe - ia) / fixe) * 100


def format_nombre(valeur, decimales=2):

    if valeur is None or pd.isna(valeur):
        return "N/D"

    return f"{valeur:,.{decimales}f}".replace(",", " ")


def moyenne(colonne):
    """Calcule la moyenne sur la période actuellement sélectionnée."""

    if colonne not in simulation_filtre.columns:
        return float("nan")

    serie = pd.to_numeric(
        simulation_filtre[colonne],
        errors="coerce"
    ).dropna()

    if serie.empty:
        return float("nan")

    return float(serie.mean())


# ============================================================
# BANNIÈRE
# ============================================================

afficher_banniere(
    "Régulation intelligente des feux",
    "Comparaison entre un cycle fixe et une régulation adaptative basée sur le trafic prédit.",
    surtitre="GESTION INTELLIGENTE DU TRAFIC"
)


# ============================================================
# FILTRES
# ============================================================

st.markdown("")

dates_disponibles = sorted(
    simulation["datetime"].dt.date.unique()
)

col_filtre1, col_filtre2 = st.columns([1, 1])

with col_filtre1:

    date_selectionnee = st.selectbox(
        "Journée simulée",
        options=dates_disponibles,
        format_func=lambda d: d.strftime("%d/%m/%Y")
    )

with col_filtre2:

    st.markdown(
        "<div style='height: 28px'></div>",
        unsafe_allow_html=True
    )


simulation_jour = simulation[
    simulation["datetime"].dt.date == date_selectionnee
].copy()

if simulation_jour.empty:
    st.warning("Aucune donnée disponible pour cette journée.")
    st.stop()


simulation_jour["heure"] = (
    simulation_jour["datetime"].dt.hour
    + simulation_jour["datetime"].dt.minute / 60
)

heure_min = int(simulation_jour["datetime"].dt.hour.min())
heure_max = int(simulation_jour["datetime"].dt.hour.max())

plage_horaire = st.slider(
    "Plage horaire",
    min_value=heure_min,
    max_value=heure_max,
    value=(heure_min, heure_max),
    step=1
)

simulation_filtre = simulation_jour[
    (simulation_jour["heure"] >= plage_horaire[0])
    & (simulation_jour["heure"] <= plage_horaire[1])
].copy()

if simulation_filtre.empty:
    st.warning("Aucune donnée dans cette plage horaire.")
    st.stop()


# ============================================================
# INDICATEURS CALCULÉS SUR LA DATE ET L'HEURE SÉLECTIONNÉES
# ============================================================

attente_fixe = moyenne("fixed_avg_wait_s")
attente_ia = moyenne("ai_avg_wait_s")

file_fixe = moyenne("fixed_avg_queue_veh")
file_ia = moyenne("ai_avg_queue_veh")

vitesse_fixe = moyenne("fixed_avg_speed_kmh")
vitesse_ia = moyenne("ai_avg_speed_kmh")

co2_fixe = moyenne("fixed_co2_g_per_veh")
co2_ia = moyenne("ai_co2_g_per_veh")

arrets_fixe = moyenne("fixed_stops_per_veh")
arrets_ia = moyenne("ai_stops_per_veh")

gain_attente = gain_pourcentage(attente_fixe, attente_ia)
gain_file = gain_pourcentage(file_fixe, file_ia)
gain_co2 = gain_pourcentage(co2_fixe, co2_ia)

gain_vitesse = (
    ((vitesse_ia - vitesse_fixe) / vitesse_fixe) * 100
    if pd.notna(vitesse_fixe) and vitesse_fixe != 0
    else 0.0
)


# ============================================================
# KPI : PERFORMANCE
# ============================================================

titre_section(
    "Performance de la régulation sur la période sélectionnée"
)

st.caption(
    f"Résultats du {date_selectionnee.strftime('%d/%m/%Y')} "
    f"entre {plage_horaire[0]:02d}:00 et {plage_horaire[1]:02d}:00. "
    "Les indicateurs sont recalculés à partir des observations affichées."
)

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Temps d'attente moyen",
        f"{format_nombre(attente_ia)} s",
        delta=f"{-gain_attente:+.1f} %",
        delta_color="inverse"
    )

with col2:

    st.metric(
        "Longueur moyenne des files",
        format_nombre(file_ia),
        delta=f"{-gain_file:+.1f} %",
        delta_color="inverse"
    )

with col3:

    st.metric(
        "Vitesse moyenne",
        f"{format_nombre(vitesse_ia)} km/h",
        delta=f"{gain_vitesse:+.1f} %",
        delta_color="normal"
    )

with col4:

    st.metric(
        "Émissions de CO₂",
        f"{format_nombre(co2_ia)} g/véh",
        delta=f"{-gain_co2:+.1f} %",
        delta_color="inverse"
    )


# ============================================================
# COMPARAISON CYCLE FIXE / IA
# ============================================================

st.markdown("")

titre_section(
    f"Comparaison cycle fixe / régulation IA — {date_selectionnee.strftime('%d/%m/%Y')}"
)

indicateurs = pd.DataFrame({
    "Indicateur": [
        "Temps d'attente (s)",
        "File d'attente (véh.)",
        "Vitesse (km/h)",
        "Arrêts / véhicule",
        "CO₂ (g/véh)"
    ],
    "Cycle fixe": [
        attente_fixe,
        file_fixe,
        vitesse_fixe,
        arrets_fixe,
        co2_fixe
    ],
    "Régulation IA": [
        attente_ia,
        file_ia,
        vitesse_ia,
        arrets_ia,
        co2_ia
    ]
})

indicateurs_long = indicateurs.melt(
    id_vars="Indicateur",
    var_name="Stratégie",
    value_name="Valeur"
)

fig_comparaison = px.bar(
    indicateurs_long,
    x="Indicateur",
    y="Valeur",
    color="Stratégie",
    barmode="group",
    text_auto=".2f",
    color_discrete_map={
        "Cycle fixe": "#E5A23B",
        "Régulation IA": "#259D91"
    }
)

fig_comparaison.update_layout(
    height=390,
    margin=dict(l=20, r=20, t=20, b=20),
    xaxis_title="",
    yaxis_title="Valeur",
    legend_title="Stratégie",
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(
        family="Arial",
        size=11,
        color="#52647A"
    )
)

fig_comparaison.update_traces(
    textposition="outside",
    cliponaxis=False
)

st.plotly_chart(
    fig_comparaison,
    use_container_width=True
)


# ============================================================
# ÉVOLUTION TEMPORELLE
# ============================================================

st.markdown("")

titre_section(
    f"Évolution temporelle — {date_selectionnee.strftime('%d/%m/%Y')}"
)

col1, col2 = st.columns(2)


# ------------------------------------------------------------
# TEMPS D'ATTENTE
# ------------------------------------------------------------

with col1:

    fig_attente = go.Figure()

    fig_attente.add_trace(
        go.Scatter(
            x=simulation_filtre["datetime"],
            y=simulation_filtre["fixed_avg_wait_s"],
            mode="lines",
            name="Cycle fixe",
            line=dict(
                color="#1473D2",
                width=1.8
            )
        )
    )

    fig_attente.add_trace(
        go.Scatter(
            x=simulation_filtre["datetime"],
            y=simulation_filtre["ai_avg_wait_s"],
            mode="lines",
            name="Régulation IA",
            line=dict(
                color="#79B9FF",
                width=1.8
            )
        )
    )

    fig_attente.update_layout(
        title=f"Temps d'attente moyen — {date_selectionnee.strftime('%d/%m/%Y')}",
        height=390,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis_title="Heure",
        yaxis_title="Temps (secondes)",
        legend=dict(
            orientation="h",
            y=1.08,
            x=1,
            xanchor="right"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(
        fig_attente,
        use_container_width=True
    )


# ------------------------------------------------------------
# LONGUEUR DES FILES
# ------------------------------------------------------------

with col2:

    fig_files = go.Figure()

    fig_files.add_trace(
        go.Scatter(
            x=simulation_filtre["datetime"],
            y=simulation_filtre["fixed_avg_queue_veh"],
            mode="lines",
            name="Cycle fixe",
            line=dict(
                color="#1473D2",
                width=1.8
            )
        )
    )

    fig_files.add_trace(
        go.Scatter(
            x=simulation_filtre["datetime"],
            y=simulation_filtre["ai_avg_queue_veh"],
            mode="lines",
            name="Régulation IA",
            line=dict(
                color="#79B9FF",
                width=1.8
            )
        )
    )

    fig_files.update_layout(
        title=f"Longueur moyenne des files — {date_selectionnee.strftime('%d/%m/%Y')}",
        height=390,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis_title="Heure",
        yaxis_title="Véhicules à l'arrêt",
        legend=dict(
            orientation="h",
            y=1.08,
            x=1,
            xanchor="right"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(
        fig_files,
        use_container_width=True
    )


# ============================================================
# DÉBIT DU TRAFIC
# ============================================================

st.markdown("")

titre_section(
    "Débit du trafic"
)

fig_trafic = go.Figure()

fig_trafic.add_trace(
    go.Scatter(
        x=simulation_filtre["datetime"],
        y=simulation_filtre["traffic_flow"],
        mode="lines",
        name="Trafic réel",
        line=dict(
            color="#1473D2",
            width=1.8
        )
    )
)

fig_trafic.add_trace(
    go.Scatter(
        x=simulation_filtre["datetime"],
        y=simulation_filtre["predicted_flow"],
        mode="lines",
        name="Trafic prédit",
        line=dict(
            color="#79B9FF",
            width=1.8,
            dash="dash"
        )
    )
)

fig_trafic.update_layout(
    height=390,
    margin=dict(l=20, r=20, t=25, b=20),
    xaxis_title="Heure",
    yaxis_title="Véhicules / 5 minutes",
    legend=dict(
        orientation="h",
        y=1.08,
        x=1,
        xanchor="right"
    ),
    plot_bgcolor="white",
    paper_bgcolor="white"
)

st.plotly_chart(
    fig_trafic,
    use_container_width=True
)


# ============================================================
# DURÉE DES FEUX VERTS
# ============================================================

st.markdown("")

titre_section(
    "Adaptation des feux de circulation"
)

col1, col2 = st.columns(2)


# ------------------------------------------------------------
# DURÉE DU VERT PAR AXE
# ------------------------------------------------------------

with col1:

    fig_vert = go.Figure()

    fig_vert.add_trace(
        go.Scatter(
            x=simulation_filtre["datetime"],
            y=simulation_filtre["ai_green_main_s"],
            mode="lines",
            name="Axe principal N-S",
            line=dict(
                color="#1473D2",
                width=2
            )
        )
    )

    fig_vert.add_trace(
        go.Scatter(
            x=simulation_filtre["datetime"],
            y=simulation_filtre["ai_green_secondary_s"],
            mode="lines",
            name="Axe secondaire E-O",
            line=dict(
                color="#79B9FF",
                width=2
            )
        )
    )

    fig_vert.update_layout(
        title="Durée du feu vert par axe – Régulation IA",
        height=390,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis_title="Heure",
        yaxis_title="Durée (secondes)",
        legend=dict(
            orientation="h",
            y=1.08,
            x=1,
            xanchor="right"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(
        fig_vert,
        use_container_width=True
    )


# ------------------------------------------------------------
# DURÉE DU CYCLE
# ------------------------------------------------------------

with col2:

    fig_cycle = go.Figure()

    fig_cycle.add_trace(
        go.Scatter(
            x=simulation_filtre["datetime"],
            y=simulation_filtre["fixed_cycle_s"],
            mode="lines",
            name="Cycle fixe",
            line=dict(
                color="#1473D2",
                width=2
            )
        )
    )

    fig_cycle.add_trace(
        go.Scatter(
            x=simulation_filtre["datetime"],
            y=simulation_filtre["ai_cycle_s"],
            mode="lines",
            name="Cycle IA",
            line=dict(
                color="#79B9FF",
                width=2
            )
        )
    )

    fig_cycle.update_layout(
        title="Durée totale du cycle",
        height=390,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis_title="Heure",
        yaxis_title="Durée (secondes)",
        legend=dict(
            orientation="h",
            y=1.08,
            x=1,
            xanchor="right"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(
        fig_cycle,
        use_container_width=True
    )


# ============================================================
# TABLEAU DÉTAILLÉ
# ============================================================

st.markdown("")

titre_section(
    "Détails des résultats"
)

colonnes_tableau = {
    "datetime": "Heure",
    "traffic_flow": "Trafic réel",
    "predicted_flow": "Trafic prédit",
    "congestion_level": "Congestion",
    "fixed_avg_wait_s": "Attente fixe (s)",
    "ai_avg_wait_s": "Attente IA (s)",
    "fixed_avg_queue_veh": "File fixe",
    "ai_avg_queue_veh": "File IA",
    "ai_green_main_s": "Vert N-S (s)",
    "ai_green_secondary_s": "Vert E-O (s)",
    "ai_cycle_s": "Cycle IA (s)"
}

colonnes_disponibles = [
    colonne
    for colonne in colonnes_tableau
    if colonne in simulation_filtre.columns
]

tableau = simulation_filtre[
    colonnes_disponibles
].copy()

tableau = tableau.rename(
    columns=colonnes_tableau
)

tableau["Heure"] = tableau["Heure"].dt.strftime(
    "%d/%m/%Y %H:%M"
)

st.dataframe(
    tableau,
    use_container_width=True,
    hide_index=True,
    height=370
)


# ============================================================
# INFORMATIONS SUR LE SCÉNARIO
# ============================================================

with st.expander(
    "Informations sur le scénario de simulation"
):

    st.markdown(
        """
        ### Scénario étudié

        La simulation compare deux stratégies de gestion des feux
        de circulation dans un carrefour urbain fictif construit avec SUMO.

        - Cycle fixe : les durées des feux verts restent constantes.
        - Régulation IA : les durées des feux verts sont adaptées
          en fonction du débit de trafic prédit.

        ### Fonctionnement

        Le système utilise les prédictions du modèle de trafic pour
        estimer la demande et adapter la répartition du temps vert
        entre les deux axes du carrefour.

        Les deux scénarios sont évalués avec les mêmes véhicules,
        afin de rendre la comparaison plus cohérente.

        ### Limites

        - Le carrefour est fictif et ne représente pas une intersection réelle.
        - La répartition du trafic entre les deux axes repose sur des hypothèses.
        - Les résultats dépendent de la période de données simulée.
        - La simulation ne représente pas un déploiement réel sur le terrain.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="dashboard-footer">
        SMART TRAFFIC · INTELLIGENT TRAFFIC LIGHT REGULATION
    </div>
    """,
    unsafe_allow_html=True
)