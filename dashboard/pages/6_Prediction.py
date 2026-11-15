from pathlib import Path
import sys
import json
from datetime import date, time, datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import joblib

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Prédiction | Smart Traffic",
    page_icon="📈",
    layout="wide"
)

RACINE = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(RACINE))

from src.features import construire_entree, COLONNES_ENTREE

sys.path.insert(0, str(RACINE / "dashboard"))

from style import (
    appliquer_style,
    afficher_menu,
    afficher_banniere,
    titre_section
)

appliquer_style()
afficher_menu("Prédiction")


# ============================================================
# CHEMINS DES FICHIERS
# ============================================================

MODEL_PATH = RACINE / "models" / "best_model.pkl"

MODEL_INFO_PATH = RACINE / "models" / "model_info.json"

DATA_PATHS = [
    RACINE / "data" / "processed" / "dataset_A_cleaned.csv",
    RACINE / "data" / "processed" / "train.csv"
]


# ============================================================
# CHARGEMENT DU MODÈLE
# ============================================================

@st.cache_resource
def charger_modele():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modèle introuvable : {MODEL_PATH}"
        )

    return joblib.load(MODEL_PATH)


@st.cache_data
def charger_informations_modele():

    if MODEL_INFO_PATH.exists():
        with open(MODEL_INFO_PATH, "r", encoding="utf-8") as fichier:
            return json.load(fichier)

    return {}


# ============================================================
# CHARGEMENT DE L'HISTORIQUE
# ============================================================

@st.cache_data
def charger_historique():

    historique = None
    fichier_utilise = None

    for chemin in DATA_PATHS:

        if not chemin.exists():
            continue

        try:
            donnees = pd.read_csv(chemin)

            colonnes_requises = {
                "datetime",
                "traffic_flow",
                "speed_kmh"
            }

            if colonnes_requises.issubset(donnees.columns):
                historique = donnees.copy()
                fichier_utilise = chemin
                break

        except Exception:
            continue

    if historique is None:
        raise FileNotFoundError(
            "Aucun fichier historique valide contenant "
            "datetime, traffic_flow et speed_kmh."
        )

    historique["datetime"] = pd.to_datetime(
        historique["datetime"],
        errors="coerce"
    )

    historique["traffic_flow"] = pd.to_numeric(
        historique["traffic_flow"],
        errors="coerce"
    )

    historique["speed_kmh"] = pd.to_numeric(
        historique["speed_kmh"],
        errors="coerce"
    )

    historique = historique.dropna(
        subset=[
            "datetime",
            "traffic_flow",
            "speed_kmh"
        ]
    )

    historique = historique.sort_values(
        "datetime"
    ).drop_duplicates(
        subset=["datetime"],
        keep="last"
    ).reset_index(drop=True)

    if len(historique) < 36:
        raise ValueError(
            "L'historique contient moins de 36 observations valides."
        )

    return historique, str(fichier_utilise)


# ============================================================
# INITIALISATION
# ============================================================

try:
    model = charger_modele()
    model_info = charger_informations_modele()
    historique_complet, fichier_historique = charger_historique()

except Exception as erreur:
    st.error(f"Impossible de préparer la prédiction : {erreur}")
    st.stop()


# ============================================================
# PARAMÈTRES DU MODÈLE
# ============================================================

seuils = model_info.get(
    "seuils_niveaux_trafic",
    {}
)

SEUIL_FAIBLE = float(
    seuils.get("faible_jusqu_a", 303)
)

SEUIL_MOYEN = float(
    seuils.get("moyen_jusqu_a", 537)
)

HISTORIQUE_MINIMUM = int(
    model_info.get("conventions", {}).get(
        "historique_minimum",
        36
    )
)

# Catégories météorologiques présentes dans les données
if "weather_condition" in historique_complet.columns:

    meteo_options = sorted(
        historique_complet["weather_condition"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

else:
    meteo_options = []

if not meteo_options:
    st.error(
        "Aucune catégorie météorologique disponible dans les données."
    )
    st.stop()


# ============================================================
# EN-TÊTE
# ============================================================

afficher_banniere(
    "Prédiction du trafic routier",
    "Estimation du débit de circulation à partir des conditions "
    "météorologiques, temporelles et historiques.",
    "PRÉDICTION INTERACTIVE"
)


# ============================================================
# INFORMATIONS SUR LES DONNÉES
# ============================================================

date_debut = historique_complet["datetime"].min()
date_fin = historique_complet["datetime"].max()

col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.metric(
        "Observations disponibles",
        f"{len(historique_complet):,}".replace(",", " ")
    )

with col_info2:
    st.metric(
        "Historique nécessaire",
        f"{HISTORIQUE_MINIMUM} observations"
    )

with col_info3:
    st.metric(
        "Dernière observation",
        date_fin.strftime("%d/%m/%Y")
    )

st.caption(
    f"Période des données : {date_debut.strftime('%d/%m/%Y')} "
    f"au {date_fin.strftime('%d/%m/%Y')}."
)


# ============================================================
# FORMULAIRE DE PRÉDICTION
# ============================================================

titre_section(
    "Paramètres de prédiction"
)

with st.form("prediction_form"):

    # --------------------------------------------------------
    # CONDITIONS TEMPORELLES
    # --------------------------------------------------------

    st.markdown("#### Conditions temporelles")

    col_date, col_heure = st.columns(2)

    with col_date:
        selected_date = st.date_input(
            "Date de prédiction",
            value=date.today()
        )

    with col_heure:
        selected_time = st.time_input(
            "Heure de prédiction",
            value=time(8, 0),
            step=300
        )

    # --------------------------------------------------------
    # CONDITIONS MÉTÉOROLOGIQUES
    # --------------------------------------------------------

    st.markdown("---")
    st.markdown("#### Conditions météorologiques")

    col_meteo1, col_meteo2 = st.columns(2)

    with col_meteo1:

        temperature = st.number_input(
            "Température (°C)",
            min_value=-20.0,
            max_value=55.0,
            value=22.0,
            step=0.5
        )

        wind_speed = st.number_input(
            "Vitesse du vent (km/h)",
            min_value=0.0,
            max_value=150.0,
            value=10.0,
            step=1.0
        )

    with col_meteo2:

        precipitation = st.number_input(
            "Précipitations (mm)",
            min_value=0.0,
            max_value=200.0,
            value=0.0,
            step=0.5
        )

        weather_condition = st.selectbox(
            "Conditions météorologiques",
            options=meteo_options
        )

    # --------------------------------------------------------
    # INFORMATIONS COMPLÉMENTAIRES
    # --------------------------------------------------------

    st.markdown("---")

    holiday = st.checkbox(
        "Jour férié",
        value=False
    )

    submit = st.form_submit_button(
        "Lancer la prédiction",
        use_container_width=True
    )


# ============================================================
# TRAITEMENT DE LA PRÉDICTION
# ============================================================

if submit:

    prediction_datetime = datetime.combine(
        selected_date,
        selected_time
    )

    # Vérification de l'intervalle historique disponible
    historique_utilisable = historique_complet[
        historique_complet["datetime"] < prediction_datetime
    ].copy()

    if len(historique_utilisable) < HISTORIQUE_MINIMUM:

        st.error(
            f"Historique insuffisant pour cette date. "
            f"Le modèle nécessite au minimum "
            f"{HISTORIQUE_MINIMUM} observations antérieures."
        )

    else:

        try:

            # ------------------------------------------------
            # CONSTRUCTION DES VARIABLES DU MODÈLE
            # ------------------------------------------------

            entree = construire_entree(
                historique=historique_utilisable,
                instant=prediction_datetime,
                temp_celsius=temperature,
                wind_speed_kmh=wind_speed,
                precip_mm=precipitation,
                weather_condition=weather_condition,
                ferie=holiday
            )

            # Respect de l'ordre des variables attendu
            entree = entree[COLONNES_ENTREE]

            # ------------------------------------------------
            # PRÉDICTION
            # ------------------------------------------------

            prediction = float(
                model.predict(entree)[0]
            )

            prediction = max(0.0, prediction)

            # ------------------------------------------------
            # SAUVEGARDE DU RÉSULTAT
            # ------------------------------------------------

            st.session_state["prediction_result"] = {
                "valeur": prediction,
                "date": prediction_datetime,
                "meteo": weather_condition,
                "temperature": temperature,
                "vent": wind_speed,
                "precipitations": precipitation
            }

            if "prediction_history" not in st.session_state:
                st.session_state["prediction_history"] = []

            st.session_state["prediction_history"].append({
                "Date": prediction_datetime.strftime(
                    "%d/%m/%Y %H:%M"
                ),
                "Trafic prédit": round(prediction, 2),
                "Météo": weather_condition
            })

            st.session_state["prediction_history"] = (
                st.session_state["prediction_history"][-20:]
            )

        except Exception as erreur:

            st.error(
                f"Erreur lors de la prédiction : {erreur}"
            )


# ============================================================
# AFFICHAGE DU RÉSULTAT
# ============================================================

if "prediction_result" in st.session_state:

    resultat = st.session_state["prediction_result"]

    prediction = resultat["valeur"]

    titre_section(
        "Résultat de la prédiction"
    )

    # --------------------------------------------------------
    # NIVEAU DE CIRCULATION
    # --------------------------------------------------------

    if prediction <= SEUIL_FAIBLE:

        niveau = "Faible"
        message = "Circulation fluide"
        couleur = "#168E88"

    elif prediction <= SEUIL_MOYEN:

        niveau = "Moyen"
        message = "Circulation modérée"
        couleur = "#C18A35"

    else:

        niveau = "Élevé"
        message = "Circulation dense"
        couleur = "#C45A5A"

    # --------------------------------------------------------
    # CARTES DE RÉSULTAT
    # --------------------------------------------------------

    col_resultat, col_niveau = st.columns([2, 1])

    with col_resultat:

        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">
                    TRAFIC ESTIMÉ
                </div>
                <div class="result-value">
                    {prediction:.0f}
                </div>
                <div class="result-unit">
                    Véhicules / 5 minutes
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_niveau:

        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">
                    NIVEAU DE CIRCULATION
                </div>
                <div style="
                    color:{couleur};
                    font-size:25px;
                    font-weight:700;
                    margin:12px 0;
                ">
                    {niveau}
                </div>
                <div class="result-unit">
                    {message}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # JAUGE DE TRAFIC
    # --------------------------------------------------------

    maximum_jauge = max(
        794,
        prediction * 1.15
    )

    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=prediction,
            number={
                "suffix": " véhicules",
                "font": {
                    "size": 25,
                    "color": "#20364D"
                }
            },
            title={
                "text": "Volume de trafic estimé",
                "font": {
                    "size": 13,
                    "color": "#43566A"
                }
            },
            gauge={
                "axis": {
                    "range": [0, maximum_jauge],
                    "tickcolor": "#8593A3"
                },
                "bar": {
                    "color": "#20A99F"
                },
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {
                        "range": [0, SEUIL_FAIBLE],
                        "color": "#DDF3F1"
                    },
                    {
                        "range": [
                            SEUIL_FAIBLE,
                            SEUIL_MOYEN
                        ],
                        "color": "#FFF0D4"
                    },
                    {
                        "range": [
                            SEUIL_MOYEN,
                            maximum_jauge
                        ],
                        "color": "#F8DEDE"
                    }
                ]
            }
        )
    )

    fig_gauge.update_layout(
        height=270,
        margin=dict(
            l=25,
            r=25,
            t=50,
            b=15
        ),
        paper_bgcolor="white"
    )

    st.plotly_chart(
        fig_gauge,
        use_container_width=True
    )

    # --------------------------------------------------------
    # CONDITIONS UTILISÉES
    # --------------------------------------------------------

    with st.expander("Conditions de cette prédiction"):

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.write(
                f"**Date :** {resultat['date'].strftime('%d/%m/%Y')}"
            )
            st.write(
                f"**Heure :** {resultat['date'].strftime('%H:%M')}"
            )

        with col_b:
            st.write(
                f"**Température :** {resultat['temperature']} °C"
            )
            st.write(
                f"**Vent :** {resultat['vent']} km/h"
            )

        with col_c:
            st.write(
                f"**Précipitations :** {resultat['precipitations']} mm"
            )
            st.write(
                f"**Météo :** {resultat['meteo']}"
            )


# ============================================================
# HISTORIQUE DES PRÉDICTIONS
# ============================================================

if st.session_state.get("prediction_history"):

    titre_section(
        "Historique des prédictions"
    )

    historique_predictions = pd.DataFrame(
        st.session_state["prediction_history"]
    )

    st.dataframe(
        historique_predictions,
        use_container_width=True,
        hide_index=True
    )

    if st.button("Effacer l'historique"):

        st.session_state["prediction_history"] = []

        st.rerun()


# ============================================================
# INFORMATIONS TECHNIQUES
# ============================================================

with st.expander("Informations sur le fonctionnement"):

    st.markdown(
        f"""
        - Modèle utilisé : régression linéaire.
        - Historique minimal requis : {HISTORIQUE_MINIMUM} observations.
        - Intervalle des données : 5 minutes.
        - Variables historiques : débits précédents, moyennes et vitesses.
        - Variables calendaires : jour, heure, week-end et jours fériés.
        - Variables météorologiques : température, vent, précipitations et météo.
        """
    )

    st.caption(
        "Les variables historiques sont calculées automatiquement "
        "à partir des observations disponibles avant la date de prédiction."
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