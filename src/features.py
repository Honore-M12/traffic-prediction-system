"""
features.py : variables dérivées partagées entre l'entraînement (notebook),
la simulation et le dashboard.

Ce module doit rester importable : le modèle sauvegardé (best_model.pkl)
y fait référence, et ne se rechargera que si `src` est dans le chemin d'import.
"""
import numpy as np
import pandas as pd


def ajouter_variables_cycliques(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute l'encodage sinus/cosinus de l'heure, de la minute et du jour de la semaine.

    Colonnes d'entrée requises : hour (0-23), minute (0-55), week_day (1 = lundi ... 7 = dimanche).
    Ce codage garantit que 23 h et 0 h sont proches, ce qui aide les modèles sensibles aux distances.
    """
    df = df.copy()
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["minute_sin"] = np.sin(2 * np.pi * df["minute"] / 60)
    df["minute_cos"] = np.cos(2 * np.pi * df["minute"] / 60)
    df["weekday_sin"] = np.sin(2 * np.pi * (df["week_day"] - 1) / 7)
    df["weekday_cos"] = np.cos(2 * np.pi * (df["week_day"] - 1) / 7)
    return df
