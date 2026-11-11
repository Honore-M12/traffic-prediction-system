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