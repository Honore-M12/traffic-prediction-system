import plotly.express as px
import streamlit as st

from style import (
    appliquer_style,
    afficher_menu,
    afficher_banniere,
    titre_section,
    styliser_graphique,
)

from donnees import (
    charger_donnees,
    filtrer_donnees,
    etat_trafic,
    JOURS,
)


# =========================================================
# 1. CONFIGURATION DE LA PAGE
# =========================================================

st.set_page_config(
    page_title="Smart Traffic | Exploration",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. STYLE ET NAVIGATION
# =========================================================

appliquer_style()
afficher_menu("Exploration")


# =========================================================
# 3. BANNIÈRE PRINCIPALE
# =========================================================

afficher_banniere(
    "Exploration des données",
    "Analyse des variations du trafic selon les heures, "
    "les jours, la vitesse et les conditions météorologiques.",
    surtitre="EXPLORATION DES DONNÉES",
)


# =========================================================
# 4. CHARGEMENT DES DONNÉES ET FILTRES
# =========================================================

df = charger_donnees()

titre_section("Période et paramètres")

df = filtrer_donnees(df)

if df.empty:
    st.warning(
        "Aucune donnée disponible pour les critères sélectionnés. "
        "Veuillez modifier les filtres."
    )
    st.stop()


# =========================================================
# 5. PROFIL HORAIRE : SEMAINE VS WEEK-END
# =========================================================

titre_section(
    "Profil horaire du trafic",
    "Débit moyen pour chaque heure de la journée, "
    "en semaine et le week-end.",
)

profil = (
    df.assign(
        type_jour=df["is_weekend"].map({
            0: "Semaine",
            1: "Week-end",
        })
    )
    .groupby(["hour", "type_jour"])["traffic_flow"]
    .mean()
    .reset_index()
)

fig_profil = px.line(
    profil,
    x="hour",
    y="traffic_flow",
    color="type_jour",
    markers=True,
    color_discrete_map={
        "Semaine": "#20A99F",
        "Week-end": "#956AC5",
    },
)

fig_profil = styliser_graphique(
    fig_profil,
    "Débit moyen selon l'heure",
    "Véhicules / 5 min",
)

fig_profil.update_layout(
    showlegend=True,
    legend_title_text="",
)

fig_profil.update_xaxes(
    title="Heure de la journée",
    dtick=2,
)

st.plotly_chart(
    fig_profil,
    width="stretch",
)


# =========================================================
# 6. CARTE DE CHALEUR HEURE × JOUR
# =========================================================

titre_section(
    "Carte de chaleur heure × jour",
    "Débit moyen pour chaque créneau de la semaine.",
)

heatmap = (
    df.pivot_table(
        index="jour_nom",
        columns="hour",
        values="traffic_flow",
        aggfunc="mean",
    )
    .reindex(list(JOURS.values()))
    .dropna(how="all")
)

fig_heat = px.imshow(
    heatmap,
    color_continuous_scale="Teal",
    aspect="auto",
    labels={
        "x": "Heure",
        "y": "",
        "color": "Véhicules / 5 min",
    },
)

fig_heat = styliser_graphique(
    fig_heat,
    "Débit moyen par jour et par heure",
    "",
    hauteur=380,
)

fig_heat.update_xaxes(
    title="Heure de la journée",
    dtick=2,
)

st.plotly_chart(
    fig_heat,
    width="stretch",
)


# =========================================================
# 7. DÉBIT PAR JOUR DE LA SEMAINE
# =========================================================

titre_section(
    "Débit par jour de la semaine",
    "Débit moyen pour chaque jour, sur la sélection.",
)

par_jour = (
    df.groupby("jour_nom")["traffic_flow"]
    .mean()
    .reindex(list(JOURS.values()))
    .dropna()
    .reset_index()
)

par_jour["type_jour"] = par_jour["jour_nom"].isin(
    ["Samedi", "Dimanche"]
).map({
    True: "Week-end",
    False: "Semaine",
})

fig_jours = px.bar(
    par_jour,
    x="jour_nom",
    y="traffic_flow",
    text="traffic_flow",
    color="type_jour",
    color_discrete_map={
        "Semaine": "#20A99F",
        "Week-end": "#956AC5",
    },
)

fig_jours.update_traces(
    texttemplate="%{text:.0f}",
    textposition="outside",
)

fig_jours = styliser_graphique(
    fig_jours,
    "Débit moyen par jour",
    "Véhicules / 5 min",
)

fig_jours.update_yaxes(
    range=[
        0,
        par_jour["traffic_flow"].max() * 1.15,
    ]
)

st.plotly_chart(
    fig_jours,
    width="stretch",
)


# =========================================================
# 8. RELATION DÉBIT / VITESSE
# =========================================================

titre_section(
    "Relation débit / vitesse",
    "Chaque point représente une mesure de 5 minutes, "
    "classée selon l'état du trafic.",
)

nuage = df[
    ["traffic_flow", "speed_kmh", "datetime"]
].copy()

nuage["etat"] = nuage["speed_kmh"].apply(etat_trafic)

fig_nuage = px.scatter(
    nuage,
    x="traffic_flow",
    y="speed_kmh",
    color="etat",
    color_discrete_map={
        "Fluide": "#2E9E6B",
        "Dense": "#E8A33D",
        "Congestion": "#D9534F",
    },
    category_orders={
        "etat": [
            "Fluide",
            "Dense",
            "Congestion",
        ]
    },
    opacity=0.4,
    hover_data={
        "datetime": True,
    },
    render_mode="webgl",
)

fig_nuage = styliser_graphique(
    fig_nuage,
    "Vitesse en fonction du débit",
    "Vitesse (km/h)",
    hauteur=420,
)

fig_nuage.update_layout(
    showlegend=True,
    legend_title_text="",
)

fig_nuage.update_xaxes(
    title="Débit (véhicules / 5 min)",
)

st.plotly_chart(
    fig_nuage,
    width="stretch",
)


# =========================================================
# 9. IMPACT DE LA MÉTÉO
# =========================================================

titre_section(
    "Impact de la météo",
    "Débit moyen selon les conditions météorologiques "
    "(conditions observées au moins 3 heures sur la sélection).",
)

meteo = (
    df.groupby("weather_condition")
    .agg(
        debit_moyen=("traffic_flow", "mean"),
        nb_mesures=("traffic_flow", "size"),
    )
    .reset_index()
)

meteo = (
    meteo[meteo["nb_mesures"] >= 36]
    .sort_values("debit_moyen")
)

fig_meteo = px.bar(
    meteo,
    x="debit_moyen",
    y="weather_condition",
    orientation="h",
    text="debit_moyen",
    hover_data={
        "nb_mesures": True,
    },
    color_discrete_sequence=["#438CC8"],
)

fig_meteo.update_traces(
    texttemplate="%{text:.0f}",
    textposition="outside",
)

fig_meteo = styliser_graphique(
    fig_meteo,
    "Débit moyen par condition météorologique",
    "",
    hauteur=420,
)

fig_meteo.update_xaxes(
    title="Véhicules / 5 min",
    range=[
        0,
        meteo["debit_moyen"].max() * 1.15,
    ],
)

st.plotly_chart(
    fig_meteo,
    width="stretch",
)


# =========================================================
# 10. PIED DE PAGE
# =========================================================

st.markdown(
    """
    <div class="dashboard-footer">
        SMART TRAFFIC · SUPERVISION ET ANALYSE DU TRAFIC ROUTIER
    </div>
    """,
    unsafe_allow_html=True,
)