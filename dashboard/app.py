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
    page_title="Smart Traffic | Tableau de bord",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. STYLE ET NAVIGATION
# =========================================================

appliquer_style()
afficher_menu("Tableau de bord")

afficher_banniere(
    "Vue d'ensemble du trafic",
    "Indicateurs clés du trafic sur la Ventura Highway (Los Angeles), février à mai 2020.",
    surtitre="SMART TRAFFIC / OVERVIEW",
)


# =========================================================
# 3. CHARGEMENT DES DONNÉES
# =========================================================

df = charger_donnees()

titre_section("Filtres")

df = filtrer_donnees(df)

# Vérification des données après filtrage
if df.empty:
    st.warning(
        "Aucune donnée disponible pour les filtres sélectionnés. "
        "Veuillez modifier vos critères."
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
        "Colonnes manquantes dans les données : "
        + ", ".join(colonnes_manquantes)
    )
    st.stop()


# =========================================================
# 4. CALCUL DES INDICATEURS
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
# 5. AFFICHAGE DES KPI
# =========================================================

titre_section(
    "Indicateurs clés",
    f"Calculés sur {len(df):,} mesures de 5 minutes.".replace(",", " ")
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    carte_kpi(
        "Débit moyen",
        f"{debit_moyen:.0f}",
        "Véhicules / 5 min"
    )

with k2:
    carte_kpi(
        "Vitesse moyenne",
        f"{vitesse_moyenne:.1f} km/h",
        "Sur la période",
        icone="↗",
        couleur="blue"
    )

with k3:
    carte_kpi(
        "Heure de pointe",
        f"{heure_pointe} h",
        "Débit moyen le plus élevé",
        icone="◷",
        couleur="purple"
    )

with k4:
    carte_kpi(
        "Débit maximal",
        f"{debit_max:.0f}",
        "Véhicules / 5 min",
        icone="▲"
    )


# =========================================================
# 6. ÉTAT GLOBAL DU TRAFIC
# =========================================================

titre_section(
    "État du trafic",
    (
        f"Fluide ≥ {SEUIL_FLUIDE} km/h · "
        f"Dense entre {SEUIL_CONGESTION} et {SEUIL_FLUIDE} km/h · "
        f"Congestion < {SEUIL_CONGESTION} km/h"
    )
)

etat = etat_trafic(vitesse_moyenne)

message = (
    f"État global de la sélection : **{etat}** "
    f"(vitesse moyenne {vitesse_moyenne:.1f} km/h)"
)

if etat == "Fluide":
    st.success(message, icon="🟢")

elif etat == "Dense":
    st.warning(message, icon="🟠")

else:
    st.error(message, icon="🔴")


# =========================================================
# 7. RÉPARTITION DES ÉTATS DU TRAFIC
# =========================================================

part_fluide = (
    df["speed_kmh"] >= SEUIL_FLUIDE
).mean() * 100

part_congestion = (
    df["speed_kmh"] < SEUIL_CONGESTION
).mean() * 100

part_dense = 100 - part_fluide - part_congestion

a1, a2, a3 = st.columns(3)

with a1:
    st.success(
        f"**{part_fluide:.1f} %** du temps en trafic fluide",
        icon="🟢"
    )

with a2:
    st.warning(
        f"**{part_dense:.1f} %** du temps en trafic dense",
        icon="🟠"
    )

with a3:
    st.error(
        f"**{part_congestion:.1f} %** du temps en congestion",
        icon="🔴"
    )


# =========================================================
# 8. ÉVOLUTION TEMPORELLE DU DÉBIT
# =========================================================

# Calcul de la durée de la période sélectionnée
nb_jours = (
    df["datetime"].max() - df["datetime"].min()
).days

# Adaptation de la fréquence selon la période
if nb_jours > 14:
    frequence = "D"
    libelle = "moyenne par jour"

elif nb_jours > 2:
    frequence = "h"
    libelle = "moyenne par heure"

else:
    frequence = "5min"
    libelle = "mesures toutes les 5 minutes"


# Agrégation des données
evolution = (
    df.set_index("datetime")["traffic_flow"]
    .resample(frequence)
    .mean()
    .dropna()
    .reset_index()
)

titre_section(
    "Évolution du débit",
    f"Débit sur la sélection ({libelle})."
)


# =========================================================
# 9. CRÉATION DU GRAPHIQUE
# =========================================================

fig = px.line(
    evolution,
    x="datetime",
    y="traffic_flow",
    color_discrete_sequence=["#20A99F"],
)

# Ligne horizontale représentant le débit moyen
fig.add_hline(
    y=debit_moyen,
    line_dash="dot",
    line_color="#9465C2",
    annotation_text=f"Moyenne : {debit_moyen:.0f}",
    annotation_position="top left",
)

# Application du style commun
fig = styliser_graphique(
    fig,
    "Débit de véhicules",
    "Véhicules / 5 min",
    hauteur=380,
)

fig.update_layout(
    showlegend=False,
)

fig.update_xaxes(
    title="Date et heure",
)

# Affichage du graphique
st.plotly_chart(
    fig,
    width="stretch",
)


# =========================================================
# 10. FOOTER
# =========================================================

st.markdown(
    """
    <div class="dashboard-footer">
        SMART TRAFFIC · TRAFFIC ANALYSIS & INTELLIGENCE
    </div>
    """,
    unsafe_allow_html=True,
)