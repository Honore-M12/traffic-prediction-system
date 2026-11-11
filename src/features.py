"""
features.py : variables partagées entre l'entraînement (notebook), la simulation et le dashboard.

Ce module doit rester importable : le modèle sauvegardé (best_model.pkl) y fait référence,
et ne se rechargera que si le dossier racine du projet est dans le chemin d'import.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]

# ----------------------------------------------------------------------------
# Listes de variables (une seule définition pour tout le projet)
# ----------------------------------------------------------------------------
METEO = ["temp_celsius", "wind_speed_kmh", "precip_mm"]
CALENDRIER = ["holidays", "is_weekend", "hour_sin", "hour_cos", "minute_sin", "minute_cos",
              "weekday_sin", "weekday_cos"]
HISTORIQUE = ["traffic_flow_lag_1", "traffic_flow_lag_2", "traffic_flow_lag_3",
              "traffic_flow_lag_6", "traffic_flow_lag_12",
              "flow_mean_12", "flow_mean_36", "flow_diff",
              "speed_lag_1", "speed_lag_3"]
CATEGORIELLES = ["weather_condition"]
CIBLE = "traffic_flow"

HISTORIQUE_MIN = 36   # valeurs passées nécessaires (flow_mean_36)


def ajouter_variables_cycliques(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute l'encodage sinus/cosinus de l'heure, de la minute et du jour de la semaine.

    Colonnes d'entrée requises : hour (0-23), minute (0-55), week_day (1 = lundi ... 7 = dimanche).
    """
    df = df.copy()
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["minute_sin"] = np.sin(2 * np.pi * df["minute"] / 60)
    df["minute_cos"] = np.cos(2 * np.pi * df["minute"] / 60)
    df["weekday_sin"] = np.sin(2 * np.pi * (df["week_day"] - 1) / 7)
    df["weekday_cos"] = np.cos(2 * np.pi * (df["week_day"] - 1) / 7)
    return df


def ajouter_variables_historique(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule les variables d'historique à partir du PASSÉ uniquement.

    `df` doit être trié par date, au pas de 5 minutes, et contenir `traffic_flow` et `speed_kmh`.
    Les décalages sont calculés par ligne (comme dans le jeu de données d'origine).
    La vitesse du même instant n'est jamais utilisée (fuite de données) : seulement ses valeurs passées.
    """
    df = df.copy()
    y = df["traffic_flow"]
    for k in (1, 2, 3, 6, 12):
        df[f"traffic_flow_lag_{k}"] = y.shift(k)
    df["flow_mean_12"] = y.shift(1).rolling(12).mean()
    df["flow_mean_36"] = y.shift(1).rolling(36).mean()
    df["flow_diff"] = df["traffic_flow_lag_1"] - df["traffic_flow_lag_3"]
    df["speed_lag_1"] = df["speed_kmh"].shift(1)
    df["speed_lag_3"] = df["speed_kmh"].shift(3)
    return df


def charger_donnees_modele(dossier=None):
    """Charge train / val / test et ajoute toutes les variables du modèle.

    Les variables d'historique sont calculées sur la série COMPLÈTE (train, puis val, puis test) :
    le début de val utilise ainsi la fin de train, comme en situation réelle où le passé récent est connu.
    Les 36 premières lignes du train sont retirées (historique insuffisant).
    Retourne (train, val, test).
    """
    dossier = Path(dossier) if dossier else RACINE / "data" / "processed"
    noms = ("train", "val", "test")
    parts = [pd.read_csv(dossier / f"{n}.csv", parse_dates=["datetime"]).assign(jeu=n) for n in noms]
    full = pd.concat(parts, ignore_index=True)
    assert full["datetime"].is_monotonic_increasing, "Les données doivent être triées par date"
    full = ajouter_variables_historique(ajouter_variables_cycliques(full))
    full = full.dropna(subset=HISTORIQUE)
    return tuple(full[full["jeu"] == n].drop(columns="jeu").reset_index(drop=True) for n in noms)


# ----------------------------------------------------------------------------
# Colonnes brutes attendues par le modèle et pipeline
# ----------------------------------------------------------------------------
COLONNES_ENTREE = (["hour", "minute", "week_day", "holidays", "is_weekend"]
                   + METEO + CATEGORIELLES + HISTORIQUE)


def faire_pipeline(modele, normaliser: bool = True):
    """Pipeline complète : variables cycliques, normalisation / One-Hot, puis modèle.

    Elle accepte les COLONNES BRUTES (COLONNES_ENTREE) : hour, minute, week_day, etc.
    Le dashboard n'a donc pas à calculer les sinus/cosinus lui-même.
    normaliser=False pour les modèles à base d'arbres.
    """
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

    numeriques = METEO + CALENDRIER + HISTORIQUE
    prep = ColumnTransformer([
        ("num", StandardScaler() if normaliser else "passthrough", numeriques),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORIELLES),
    ])
    return Pipeline([
        ("cyc", FunctionTransformer(ajouter_variables_cycliques, validate=False)),
        ("prep", prep),
        ("modele", modele),
    ])


def construire_entree(historique: pd.DataFrame, instant, temp_celsius: float, wind_speed_kmh: float,
                      precip_mm: float, weather_condition: str, ferie: bool = False) -> pd.DataFrame:
    """Construit UNE ligne d'entrée du modèle pour l'instant demandé.

    historique : observations récentes AVANT `instant`, au pas de 5 minutes, triées par date,
                 avec les colonnes `traffic_flow` et `speed_kmh` (au moins HISTORIQUE_MIN lignes).
    instant    : date et heure de la prédiction.
    ferie      : True si c'est un jour férié. Comme dans le jeu de données d'origine,
                 `holidays` vaut 1 aussi pour tous les week-ends.
    """
    if len(historique) < HISTORIQUE_MIN:
        raise ValueError(f"Il faut au moins {HISTORIQUE_MIN} observations passées, "
                         f"{len(historique)} fournies.")
    instant = pd.Timestamp(instant)

    # On ajoute une ligne "inconnue" à la fin : ses variables d'historique ne dépendent que du passé
    h = historique[["traffic_flow", "speed_kmh"]].tail(HISTORIQUE_MIN).reset_index(drop=True)
    h.loc[len(h)] = [np.nan, np.nan]
    ligne = ajouter_variables_historique(h).iloc[[-1]][HISTORIQUE].reset_index(drop=True)

    jour = instant.isoweekday()          # 1 = lundi ... 7 = dimanche (même codage que le jeu de données)
    ligne["hour"] = instant.hour
    ligne["minute"] = instant.minute
    ligne["week_day"] = jour
    ligne["is_weekend"] = int(jour >= 6)
    ligne["holidays"] = int(bool(ferie) or jour >= 6)
    ligne["temp_celsius"] = temp_celsius
    ligne["wind_speed_kmh"] = wind_speed_kmh
    ligne["precip_mm"] = precip_mm
    ligne["weather_condition"] = weather_condition
    return ligne[COLONNES_ENTREE]
