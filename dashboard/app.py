import plotly.express as px
import streamlit as st
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

st.set_page_config(
    page_title="Smart Traffic | Tableau de bord",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

appliquer_style()
afficher_menu("Tableau de bord")

afficher_banniere(
    "Vue d'ensemble du trafic",
    "Indicateurs clés du trafic sur la Ventura Highway (Los Angeles), février à mai 2020.",
    surtitre="SMART TRAFFIC / OVERVIEW",
)

# Chargement des données et filtres
df = charger_donnees()

titre_section("Filtres")
df = filtrer_donnees(df)

# Calcul des indicateurs sur les données filtrées
debit_moyen = df["traffic_flow"].mean()
vitesse_moyenne = df["speed_kmh"].mean()
heure_pointe = df.groupby("hour")["traffic_flow"].mean().idxmax()
debit_max = df["traffic_flow"].max()

# Affichage des KPI
titre_section("Indicateurs clés", f"Calculés sur {len(df):,} mesures de 5 minutes.".replace(",", " "))

k1, k2, k3, k4 = st.columns(4)

with k1:
    carte_kpi("Débit moyen", f"{debit_moyen:.0f}", "Véhicules / 5 min")
with k2:
    carte_kpi("Vitesse moyenne", f"{vitesse_moyenne:.1f} km/h", "Sur la période", icone="↗", couleur="blue")
with k3:
    carte_kpi("Heure de pointe", f"{heure_pointe} h", "Débit moyen le plus élevé", icone="◷", couleur="purple")
with k4:
    carte_kpi("Débit maximal", f"{debit_max}", "Véhicules / 5 min", icone="▲")

# État du trafic : alertes vert / orange / rouge
titre_section(
    "État du trafic",
    f"Fluide ≥ {SEUIL_FLUIDE} km/h · Dense entre {SEUIL_CONGESTION} et {SEUIL_FLUIDE} km/h · Congestion < {SEUIL_CONGESTION} km/h",
)

etat = etat_trafic(vitesse_moyenne)
message = f"État global de la sélection : **{etat}** (vitesse moyenne {vitesse_moyenne:.1f} km/h)"

if etat == "Fluide":
    st.success(message, icon="🟢")
elif etat == "Dense":
    st.warning(message, icon="🟠")
else:
    st.error(message, icon="🔴")

part_fluide = (df["speed_kmh"] >= SEUIL_FLUIDE).mean() * 100
part_congestion = (df["speed_kmh"] < SEUIL_CONGESTION).mean() * 100
part_dense = 100 - part_fluide - part_congestion

a1, a2, a3 = st.columns(3)

with a1:
    st.success(f"**{part_fluide:.1f} %** du temps en trafic fluide", icon="🟢")
with a2:
    st.warning(f"**{part_dense:.1f} %** du temps en trafic dense", icon="🟠")
with a3:
    st.error(f"**{part_congestion:.1f} %** du temps en congestion", icon="🔴")

# Évolution du débit : niveau de détail adapté à la durée sélectionnée
nb_jours = (df["datetime"].max() - df["datetime"].min()).days

if nb_jours > 14:
    frequence, libelle = "D", "moyenne par jour"
elif nb_jours > 2:
    frequence, libelle = "h", "moyenne par heure"
else:
    frequence, libelle = "5min", "mesures toutes les 5 minutes"

evolution = (
    df.set_index("datetime")["traffic_flow"]
    .resample(frequence)
    .mean()
    .dropna()
    .reset_index()
)

titre_section("Évolution du débit", f"Débit sur la sélection ({libelle}).")

fig = px.line(evolution, x="datetime", y="traffic_flow", color_discrete_sequence=["#20A99F"])
fig.add_hline(
    y=debit_moyen,
    line_dash="dot",
    line_color="#9465C2",
    annotation_text=f"Moyenne : {debit_moyen:.0f}",
)
fig = styliser_graphique(fig, "Débit de véhicules", "Véhicules / 5 min")

st.plotly_chart(fig, width="stretch")