from pathlib import Path
import sys

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Analyse du modèle final | Smart Traffic",
    page_icon="📊",
    layout="wide"
)

RACINE = Path(__file__).resolve().parents[2]
DOSSIER_RESULTATS = RACINE / "results"

sys.path.insert(0, str(RACINE / "dashboard"))

from style import (
    appliquer_style,
    afficher_menu,
    afficher_banniere,
    titre_section
)

appliquer_style()
afficher_menu("Analyse du meilleur modèle")


# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

FICHIER_METRICS = DOSSIER_RESULTATS / "metrics_test.csv"
FICHIER_PREDICTIONS = DOSSIER_RESULTATS / "predictions_test.csv"
FICHIER_IMPORTANCE = DOSSIER_RESULTATS / "feature_importance.csv"


@st.cache_data
def charger_donnees():

    metrics = pd.read_csv(FICHIER_METRICS)
    predictions = pd.read_csv(FICHIER_PREDICTIONS)
    importance = pd.read_csv(FICHIER_IMPORTANCE)

    predictions["datetime"] = pd.to_datetime(
        predictions["datetime"],
        errors="coerce"
    )

    for colonne in ["y_true", "y_pred", "y_persistance"]:
        predictions[colonne] = pd.to_numeric(
            predictions[colonne],
            errors="coerce"
        )

    importance["hausse_MAE"] = pd.to_numeric(
        importance["hausse_MAE"],
        errors="coerce"
    )

    predictions = predictions.dropna(
        subset=["datetime", "y_true", "y_pred"]
    ).sort_values("datetime")

    importance = importance.dropna(
        subset=["variable", "hausse_MAE"]
    )

    return metrics, predictions, importance


try:
    metrics, predictions, importance = charger_donnees()

except FileNotFoundError as erreur:
    st.error(
        f"Fichier introuvable : {erreur.filename}"
    )
    st.stop()

except Exception as erreur:
    st.error(f"Erreur de chargement : {erreur}")
    st.stop()


# ============================================================
# VÉRIFICATION DES COLONNES
# ============================================================

colonnes_metrics = {
    "modèle", "MAE", "RMSE", "R2",
    "WAPE_pct", "biais", "gain_vs_persistance_pct"
}

colonnes_predictions = {
    "datetime", "y_true", "y_pred", "y_persistance"
}

colonnes_importance = {
    "variable", "hausse_MAE"
}

if not colonnes_metrics.issubset(metrics.columns):
    st.error("Colonnes manquantes dans metrics_test.csv.")
    st.stop()

if not colonnes_predictions.issubset(predictions.columns):
    st.error("Colonnes manquantes dans predictions_test.csv.")
    st.stop()

if not colonnes_importance.issubset(importance.columns):
    st.error("Colonnes manquantes dans feature_importance.csv.")
    st.stop()


# ============================================================
# IDENTIFICATION DU MODÈLE FINAL
# ============================================================

modele_final = metrics[
    metrics["modèle"].astype(str).str.contains(
        "regression_lineaire",
        case=False,
        na=False
    )
]

if modele_final.empty:
    st.error("Résultats de la régression linéaire introuvables.")
    st.stop()

modele_final = modele_final.iloc[0]

mae = float(modele_final["MAE"])
rmse = float(modele_final["RMSE"])
r2 = float(modele_final["R2"])
wape = float(modele_final["WAPE_pct"])
biais = float(modele_final["biais"])
gain = float(modele_final["gain_vs_persistance_pct"])


# ============================================================
# EN-TÊTE
# ============================================================

afficher_banniere(
    "Analyse du modèle final",
    "Performances et comportement de la régression linéaire.",
    "ANALYSE ET PERFORMANCE"
)


# ============================================================
# 1. INDICATEURS DE PERFORMANCE
# ============================================================

titre_section(
    "Performance sur le jeu de test"
)

# Première ligne
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "MAE",
        f"{mae:.2f}",
        help="Erreur absolue moyenne en véhicules par intervalle de 5 minutes."
    )

with col2:
    st.metric(
        "RMSE",
        f"{rmse:.2f}",
        help="Racine de l'erreur quadratique moyenne."
    )

with col3:
    st.metric(
        "R²",
        f"{r2:.4f}",
        help="Coefficient de détermination."
    )

# Deuxième ligne
col4, col5, col6 = st.columns(3)

with col4:
    st.metric(
        "WAPE",
        f"{wape:.2f} %"
    )

with col5:
    st.metric(
        "Biais",
        f"{biais:.2f}"
    )

with col6:
    st.metric(
        "Gain vs persistance",
        f"{gain:.2f} %"
    )


# ============================================================
# 2. VALEURS RÉELLES ET PRÉDITES
# ============================================================

titre_section(
    "Valeurs réelles vs prédictions"
)

fig_comparaison = go.Figure()

fig_comparaison.add_trace(
    go.Scatter(
        x=predictions["datetime"],
        y=predictions["y_true"],
        mode="lines",
        name="Trafic réel",
        line=dict(width=1.7)
    )
)

fig_comparaison.add_trace(
    go.Scatter(
        x=predictions["datetime"],
        y=predictions["y_pred"],
        mode="lines",
        name="Trafic prédit",
        line=dict(width=1.7)
    )
)

fig_comparaison.update_layout(
    xaxis_title="Date et heure",
    yaxis_title="Débit (véhicules / 5 min)",
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(l=10, r=10, t=30, b=10)
)

st.plotly_chart(
    fig_comparaison,
    use_container_width=True
)


# ============================================================
# 3. ANALYSE DES ERREURS
# ============================================================

titre_section(
    "Analyse des erreurs"
)

predictions = predictions.copy()

predictions["residu"] = (
    predictions["y_true"] - predictions["y_pred"]
)

predictions["erreur_absolue"] = (
    predictions["residu"].abs()
)

col_erreur1, col_erreur2 = st.columns(2)

# Distribution des erreurs
with col_erreur1:

    fig_distribution = px.histogram(
        predictions,
        x="residu",
        nbins=40,
        title="Distribution des erreurs",
        labels={
            "residu": "Erreur (réel - prédit)",
            "count": "Nombre de prédictions"
        }
    )

    fig_distribution.add_vline(
        x=0,
        line_dash="dash",
        annotation_text="0"
    )

    fig_distribution.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10)
    )

    st.plotly_chart(
        fig_distribution,
        use_container_width=True
    )


# Évolution temporelle des erreurs
with col_erreur2:

    fig_erreurs_temps = px.scatter(
        predictions,
        x="datetime",
        y="residu",
        title="Erreurs dans le temps",
        labels={
            "datetime": "Date et heure",
            "residu": "Erreur (réel - prédit)"
        },
        opacity=0.55
    )

    fig_erreurs_temps.add_hline(
        y=0,
        line_dash="dash"
    )

    fig_erreurs_temps.update_layout(
        margin=dict(l=10, r=10, t=50, b=10)
    )

    st.plotly_chart(
        fig_erreurs_temps,
        use_container_width=True
    )


# Indicateurs d'erreur
col_stat1, col_stat2, col_stat3 = st.columns(3)

with col_stat1:
    st.metric(
        "Erreur absolue moyenne",
        f"{predictions['erreur_absolue'].mean():.2f}"
    )

with col_stat2:
    st.metric(
        "Erreur absolue maximale",
        f"{predictions['erreur_absolue'].max():.2f}"
    )

with col_stat3:
    st.metric(
        "Prédictions évaluées",
        f"{len(predictions):,}".replace(",", " ")
    )


# ============================================================
# 4. IMPORTANCE DES VARIABLES
# ============================================================

titre_section(
    "Importance des variables"
)

importance_triee = importance.sort_values(
    by="hausse_MAE",
    ascending=True
)

fig_importance = px.bar(
    importance_triee,
    x="hausse_MAE",
    y="variable",
    orientation="h",
    labels={
        "hausse_MAE": "Augmentation du MAE après permutation",
        "variable": "Variable"
    },
    title="Importance par permutation"
)

fig_importance.add_vline(
    x=0,
    line_dash="dash"
)

fig_importance.update_layout(
    yaxis_title="",
    xaxis_title="Augmentation du MAE",
    margin=dict(l=10, r=10, t=50, b=10)
)

st.plotly_chart(
    fig_importance,
    use_container_width=True
)


# Tableau détaillé repliable
with st.expander("Détails de l'importance des variables"):

    tableau_importance = importance.sort_values(
        by="hausse_MAE",
        ascending=False
    ).rename(
        columns={
            "variable": "Variable",
            "hausse_MAE": "Hausse du MAE",
            "ecart_type": "Écart-type"
        }
    )

    st.dataframe(
        tableau_importance,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 5. COMPARAISON AVEC LES MODÈLES DE RÉFÉRENCE
# ============================================================

titre_section(
    "Comparaison avec les modèles de référence"
)

colonnes_affichage = [
    "modèle",
    "MAE",
    "RMSE",
    "R2",
    "WAPE_pct",
    "gain_vs_persistance_pct"
]

tableau_reference = metrics[
    colonnes_affichage
].copy()

tableau_reference = tableau_reference.rename(
    columns={
        "modèle": "Modèle",
        "MAE": "MAE",
        "RMSE": "RMSE",
        "R2": "R²",
        "WAPE_pct": "WAPE (%)",
        "gain_vs_persistance_pct": "Gain vs persistance (%)"
    }
)

st.dataframe(
    tableau_reference.style.format({
        "MAE": "{:.2f}",
        "RMSE": "{:.2f}",
        "R²": "{:.4f}",
        "WAPE (%)": "{:.2f}",
        "Gain vs persistance (%)": "{:.2f}"
    }),
    use_container_width=True,
    hide_index=True
)