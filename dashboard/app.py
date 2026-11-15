import streamlit as st
import plotly.express as px

from style import (
    appliquer_style,
    afficher_menu,
    afficher_banniere,
    titre_section,
    carte_kpi,
    styliser_graphique,
)

from donnees import (
    charger_donnees,
    filtrer_donnees,
    etat_trafic,
    SEUIL_FLUIDE,
    SEUIL_CONGESTION,
)


# =========================================================
# 1. CONFIGURATION DE LA PAGE
# =========================================================

st.set_page_config(
    page_title="Smart Traffic | Supervision",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. STYLE ET NAVIGATION
# =========================================================

appliquer_style()
afficher_menu("Tableau de bord")


# =========================================================
# 3. RÉSERVATION DE LA BANNIÈRE
# =========================================================

# On réserve son emplacement avant les filtres.
# Elle sera remplie après le filtrage pour afficher
# automatiquement les dates réellement sélectionnées.

zone_banniere = st.empty()


# =========================================================
# 4. CHARGEMENT DES DONNÉES ET FILTRES
# =========================================================

df = charger_donnees()

titre_section("Période et paramètres")

df = filtrer_donnees(df)


# Vérification des données après filtrage

if df.empty:
    st.warning(
        "Aucune donnée disponible pour les critères sélectionnés. "
        "Veuillez modifier les filtres."
    )
    st.stop()


# Vérification des colonnes nécessaires

colonnes_requises = [
    "datetime",
    "traffic_flow",
    "speed_kmh",
    "hour",
]

colonnes_manquantes = [
    colonne
    for colonne in colonnes_requises
    if colonne not in df.columns
]

if colonnes_manquantes:
    st.error(
        "Certaines informations sont absentes des données : "
        + ", ".join(colonnes_manquantes)
    )
    st.stop()


# =========================================================
# 5. AFFICHAGE DE LA BANNIÈRE
# =========================================================

date_debut = df["datetime"].min()
date_fin = df["datetime"].max()

periode = (
    f"Du {date_debut.strftime('%d/%m/%Y')} "
    f"au {date_fin.strftime('%d/%m/%Y')}"
)

with zone_banniere.container():

    afficher_banniere(
        "Vue d'ensemble du trafic",
        f"Analyse des conditions de circulation sur la période sélectionnée : {periode}.",
        surtitre="SUPERVISION ROUTIÈRE",
    )


# =========================================================
# 6. CALCUL DES INDICATEURS
# =========================================================

debit_moyen = df["traffic_flow"].mean()

vitesse_moyenne = df["speed_kmh"].mean()

heure_pointe = (
    df.groupby("hour")["traffic_flow"]
    .mean()
    .idxmax()
)

debit_max = df["traffic_flow"].max()


# =========================================================
# 7. INDICATEURS PRINCIPAUX
# =========================================================

titre_section(
    "Indicateurs principaux",
    f"{len(df):,} mesures de circulation analysées".replace(",", " ")
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    carte_kpi(
        "Débit moyen",
        f"{debit_moyen:.0f}",
        "Véhicules / 5 min",
        icone="▦",
        couleur="teal",
    )

with k2:
    carte_kpi(
        "Vitesse moyenne",
        f"{vitesse_moyenne:.1f} km/h",
        "Sur la période sélectionnée",
        icone="↗",
        couleur="blue",
    )

with k3:
    carte_kpi(
        "Heure de pointe",
        f"{heure_pointe} h",
        "Heure de débit moyen maximal",
        icone="◷",
        couleur="purple",
    )

with k4:
    carte_kpi(
        "Débit maximal",
        f"{debit_max:.0f}",
        "Véhicules / 5 min",
        icone="▲",
        couleur="teal",
    )


# =========================================================
# 8. CONDITIONS DE CIRCULATION
# =========================================================

titre_section(
    "Conditions de circulation",
    (
        f"Fluide : ≥ {SEUIL_FLUIDE} km/h · "
        f"Dense : {SEUIL_CONGESTION} à {SEUIL_FLUIDE} km/h · "
        f"Congestion : < {SEUIL_CONGESTION} km/h"
    )
)

etat = etat_trafic(vitesse_moyenne)

col_etat, col_vitesse = st.columns([2, 1])

with col_etat:

    if etat == "Fluide":
        st.success(
            "Conditions de circulation fluides",
            icon="🟢",
        )

    elif etat == "Dense":
        st.warning(
            "Conditions de circulation denses",
            icon="🟠",
        )

    else:
        st.error(
            "Congestion détectée",
            icon="🔴",
        )

with col_vitesse:

    st.metric(
        "Vitesse moyenne constatée",
        f"{vitesse_moyenne:.1f} km/h",
    )


# =========================================================
# 9. RÉPARTITION DES CONDITIONS DE CIRCULATION
# =========================================================

part_fluide = (
    df["speed_kmh"] >= SEUIL_FLUIDE
).mean() * 100

part_congestion = (
    df["speed_kmh"] < SEUIL_CONGESTION
).mean() * 100

part_dense = 100 - part_fluide - part_congestion


titre_section(
    "Répartition du trafic",
    "Proportion des observations selon les conditions de circulation.",
)

a1, a2, a3 = st.columns(3)

with a1:
    carte_kpi(
        "Trafic fluide",
        f"{part_fluide:.1f} %",
        "Part des observations",
        icone="●",
        couleur="teal",
    )

with a2:
    carte_kpi(
        "Trafic dense",
        f"{part_dense:.1f} %",
        "Part des observations",
        icone="●",
        couleur="blue",
    )

with a3:
    carte_kpi(
        "Congestion",
        f"{part_congestion:.1f} %",
        "Part des observations",
        icone="●",
        couleur="purple",
    )


# =========================================================
# 10. ÉVOLUTION TEMPORELLE DU DÉBIT
# =========================================================

nb_jours = (
    date_fin - date_debut
).days

if nb_jours > 14:
    frequence = "D"
    libelle = "Moyenne journalière"

elif nb_jours > 2:
    frequence = "h"
    libelle = "Moyenne horaire"

else:
    frequence = "5min"
    libelle = "Mesures toutes les 5 minutes"


evolution = (
    df.set_index("datetime")["traffic_flow"]
    .resample(frequence)
    .mean()
    .dropna()
    .reset_index()
)


# =========================================================
# 11. GRAPHIQUE D'ÉVOLUTION
# =========================================================

titre_section(
    "Évolution du débit de circulation",
    f"{libelle} sur la période sélectionnée.",
)

fig = px.line(
    evolution,
    x="datetime",
    y="traffic_flow",
    color_discrete_sequence=["#20A99F"],
)

# Ligne représentant le débit moyen

fig.add_hline(
    y=debit_moyen,
    line_dash="dot",
    line_color="#9465C2",
    annotation_text=f"Débit moyen : {debit_moyen:.0f}",
    annotation_position="top left",
)

# Application du style commun

fig = styliser_graphique(
    fig,
    "Évolution du nombre de véhicules",
    "Véhicules / 5 min",
    hauteur=400,
)

fig.update_layout(
    showlegend=False,
    hovermode="x unified",
)

fig.update_xaxes(
    title="Date et heure",
)

st.plotly_chart(
    fig,
    width="stretch",
)


# =========================================================
# 12. PIED DE PAGE
# =========================================================

st.markdown(
    """
    <div class="dashboard-footer">
        SMART TRAFFIC · SUPERVISION ET ANALYSE DU TRAFIC ROUTIER
    </div>
    """,
    unsafe_allow_html=True,
)