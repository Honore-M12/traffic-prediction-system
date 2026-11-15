"""Sources de prédiction du débit (véh / 5 min).

Tous les prédicteurs exposent ``predict(df)`` (un débit prévu par ligne de df).
La simulation ne dépend que de cette interface : pour utiliser les prédictions
ou le modèle de Joel, il suffit de changer de prédicteur.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .features import joel_features, model_input


def load_model_info(path, key=None):
    """Lit model_info.json (format actuel : un seul modèle ; ancien format : clés A/B).

    Retourne un dict : modele, fichier, variables_entree, MAE_test.
    """
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    if "fichier" not in d:
        if key is None or key not in d:
            raise KeyError(f"Clé {key!r} absente de {path} ; clés disponibles : {list(d)}")
        d = d[key]
    perf = d.get("performances_test")
    mae = d.get("MAE_test", perf.get("MAE") if isinstance(perf, dict) else None)
    return {"modele": d.get("modele", "?"), "fichier": d["fichier"],
            "variables_entree": d["variables_entree"], "MAE_test": mae}


class PersistencePredictor:
    """Prédiction naïve : le débit prévu est celui des 5 minutes précédentes."""
    name = "persistence"

    def predict(self, df):
        return df["traffic_flow_lag_1"].to_numpy(dtype=float)


class OraclePredictor:
    """Prédiction parfaite (borne haute, pour comparaison uniquement)."""
    name = "oracle"

    def predict(self, df):
        return df["traffic_flow"].to_numpy(dtype=float)


class CsvPredictor:
    """Lit un fichier de prédictions (ex : results/predictions_test.csv).

    Le fichier doit contenir une colonne ``datetime`` et une colonne de
    prédiction (``predicted_flow`` ou, à défaut, la première colonne dont le
    nom contient « pred »). On peut aussi imposer les noms avec ``time_col`` et
    ``pred_col``.
    """

    def __init__(self, path, time_col=None, pred_col=None, name="csv"):
        p = pd.read_csv(path)
        tcol = time_col or next((c for c in p.columns
                                 if c.lower() in ("datetime", "date", "timestamp", "time")), None)
        pcol = pred_col or ("predicted_flow" if "predicted_flow" in p.columns else
                            next((c for c in p.columns
                                  if "pred" in c.lower() and c != tcol), None))
        if tcol is None or pcol is None:
            raise ValueError(f"Colonnes introuvables dans {path} : {list(p.columns)}. "
                             "Utiliser --time-col et --pred-col.")
        p[tcol] = pd.to_datetime(p[tcol])
        self.series = p.set_index(tcol)[pcol].astype(float)
        self.pred_col = pcol
        self.name = f"{name} (colonne {pcol})"

    def predict(self, df):
        out = self.series.reindex(df["datetime"]).to_numpy()
        missing = int(np.isnan(out).sum())
        if missing:
            raise ValueError(f"{missing} horodatages de test.csv absents du fichier de prédictions.")
        return out


class ModelPredictor:
    """Charge le modèle sauvegardé de Joel (models/best_model.pkl).

    Prérequis : le dossier ``src/`` de Joel est à la racine du projet (le .pkl y
    fait référence) et les commandes sont lancées depuis cette racine.

    ``feature_cols`` : colonnes d'entrée (champ ``variables_entree`` de
    model_info.json). ``data_dir`` : dossier contenant train.csv, val.csv et
    test.csv. Les variables d'historique (retards, moyennes glissantes) sont alors
    calculées par la fonction de Joel ``charger_donnees_modele`` sur la série
    complète, comme à l'entraînement ; le début du test utilise la fin de la
    validation.
    """
    name = "model"

    def __init__(self, model_path, feature_cols, data_dir=None):
        import joblib
        joel_features()                      # à importer AVANT de charger le .pkl
        self.model = joblib.load(model_path)
        self.feature_cols = list(feature_cols)
        self.data_dir = data_dir
        self._frame = None

    def _full_frame(self):
        if self._frame is None:
            sf = joel_features()
            parts = sf.charger_donnees_modele(self.data_dir)
            self._frame = pd.concat(parts, ignore_index=True).set_index("datetime")
        return self._frame

    def predict(self, df):
        if all(c in df.columns for c in self.feature_cols):
            X = model_input(df, self.feature_cols)
        else:
            if self.data_dir is None:
                raise ValueError("Colonnes d'historique absentes du fichier et data_dir non "
                                 "fourni (dossier avec train.csv, val.csv, test.csv).")
            X = self._full_frame().reindex(df["datetime"])[self.feature_cols]
            if X.isna().any().any():
                raise ValueError("Variables d'historique indisponibles pour certains instants "
                                 "(les dates de ce fichier doivent figurer dans train/val/test).")
        return np.asarray(self.model.predict(X), dtype=float)

    def predict_one(self, conditions):
        """Débit prévu pour un instant, via ``construire_entree`` de Joel.

        conditions : dict avec ``historique`` (DataFrame des observations passées,
        au pas de 5 min, colonnes traffic_flow et speed_kmh, au moins 36 lignes),
        ``instant``, ``temp_celsius``, ``wind_speed_kmh``, ``precip_mm``,
        ``weather_condition`` et, en option, ``ferie`` (jour férié).
        """
        sf = joel_features()
        X = sf.construire_entree(
            conditions["historique"], conditions["instant"], conditions["temp_celsius"],
            conditions["wind_speed_kmh"], conditions["precip_mm"],
            conditions["weather_condition"], conditions.get("ferie", False))
        return float(self.model.predict(X)[0])
