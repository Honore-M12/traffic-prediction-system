from pathlib import Path

import pandas as pd
import streamlit as st

# Dossier des données : on remonte de dashboard/ à la racine du projet
DOSSIER_DONNEES = Path(__file__).resolve().parent.parent / "data" / "processed"

# Codage de week_day selon la doc d'Honoré : 1 = lundi ... 7 = dimanche
JOURS = {
    1: "Lundi", 2: "Mardi", 3: "Mercredi", 4: "Jeudi",
    5: "Vendredi", 6: "Samedi", 7: "Dimanche",
}


@st.cache_data
def charger_donnees():
    """Charge le dataset complet nettoyé (34 820 lignes) et ajoute le nom du jour."""
    df = pd.read_csv(DOSSIER_DONNEES / "dataset_A_cleaned.csv", parse_dates=["datetime"])
    df["jour_nom"] = df["week_day"].map(JOURS)
    return df


def filtrer_donnees(df):
    """Affiche les filtres communs (période, jours, heures, type de jour) et renvoie les données filtrées."""
    date_min = df["datetime"].dt.date.min()
    date_max = df["datetime"].dt.date.max()

    c1, c2, c3, c4 = st.columns([1.2, 2, 1.3, 1.2])

    with c1:
        periode = st.date_input(
            "Période",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
        )
    with c2:
        jours = st.multiselect("Jours", options=list(JOURS.values()), default=list(JOURS.values()))
    with c3:
        heures = st.slider("Heures", min_value=0, max_value=23, value=(0, 23))
    with c4:
        type_jour = st.radio("Type de jour", ["Tous", "Semaine", "Week-end"], horizontal=True)

    # Tant que l'utilisateur n'a choisi que la date de début, on attend la date de fin
    if len(periode) != 2:
        st.info("Choisissez une date de début et une date de fin.")
        st.stop()
    debut, fin = periode

    # Conditions à respecter pour garder une ligne
    masque = (
        (df["datetime"].dt.date >= debut)
        & (df["datetime"].dt.date <= fin)
        & df["jour_nom"].isin(jours)
        & df["hour"].between(heures[0], heures[1])
    )
    if type_jour == "Semaine":
        masque &= df["is_weekend"] == 0
    elif type_jour == "Week-end":
        masque &= df["is_weekend"] == 1

    df_filtre = df[masque]

    if df_filtre.empty:
        st.warning("Aucune donnée ne correspond à ces filtres.")
        st.stop()

    return df_filtre