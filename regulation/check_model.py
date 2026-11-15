"""Vérifie que le modèle sauvegardé de Joel est bien rechargé et reproduit.

Contrôles :
  1. le MAE recalculé sur test.csv correspond au MAE_test de model_info.json ;
  2. (optionnel) les prédictions correspondent à celles du fichier de Joel.

    python -m regulation.check_model --data data/processed/test.csv \
        --model-info models/model_info.json \
        --predictions results/predictions_test.csv
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .predictors import CsvPredictor, ModelPredictor, load_model_info


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--model-info", required=True)
    ap.add_argument("--model-key", default=None, help="seulement pour l'ancien format A/B")
    ap.add_argument("--predictions", help="results/predictions_test.csv (optionnel)")
    ap.add_argument("--time-col")
    ap.add_argument("--pred-col")
    args = ap.parse_args(argv)

    info = load_model_info(args.model_info, args.model_key)
    model_path = Path(args.model_info).parent / info["fichier"]
    df = pd.read_csv(args.data, parse_dates=["datetime"])
    model = ModelPredictor(model_path, info["variables_entree"], data_dir=Path(args.data).parent)
    pred = model.predict(df)
    y = df["traffic_flow"].to_numpy(float)

    mae = float(np.mean(np.abs(pred - y)))
    ok = info["MAE_test"] is not None and abs(mae - info["MAE_test"]) < 0.5
    print(f"Modèle {info['modele']} : {model_path.name}")
    print(f"  MAE recalculé sur {Path(args.data).name} : {mae:.3f}   "
          f"(model_info.json : {info['MAE_test']})  ->  {'OK' if ok else 'ÉCART'}")
    if not ok:
        print("  Le MAE ne correspond pas. Vérifier que le fichier de données est bien le "
              "jeu de test de Joel (mêmes lignes, mêmes colonnes d'historique).")

    if args.predictions:
        ref = CsvPredictor(args.predictions, args.time_col, args.pred_col).predict(df)
        diff = np.abs(pred - ref)
        print(f"  Écart avec {Path(args.predictions).name} : moyen {diff.mean():.4f}, "
              f"max {diff.max():.4f}  ->  {'OK' if diff.max() < 0.5 else 'ÉCART'}")


if __name__ == "__main__":
    main()
