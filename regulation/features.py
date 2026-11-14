"""Pont vers le code de Joel (src/features.py).

Le modèle final (models/best_model.pkl) est une pipeline qui prend des COLONNES
BRUTES. Son code (classe RegresseurBorne, variables cycliques, calcul des
retards) est dans ``src/features.py``, dossier de Joel : il doit être à la
racine du projet, à côté de ``regulation/``, et les commandes se lancent depuis
cette racine.

Ce fichier ne recalcule rien : il appelle les fonctions de Joel, pour que la
simulation et le modèle voient exactement les mêmes variables.
"""
import sys
from pathlib import Path


def joel_features():
    """Importe src/features.py de Joel (la racine du projet doit être le dossier courant)."""
    root = str(Path.cwd())
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        import src.features as sf
    except ImportError as e:
        raise ImportError(
            "Impossible d'importer src/features.py (dossier de Joel). Copier son dossier "
            "src/ à la racine du projet, à côté de regulation/, et lancer la commande depuis "
            f"cette racine ({root}).\nDétail : {e}") from e
    return sf


def model_input(df, feature_cols):
    """Colonnes du modèle, dans l'ordre ; erreur claire si certaines manquent."""
    cols = list(feature_cols)
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError("Colonnes absentes : " + ", ".join(missing))
    return df[cols]
