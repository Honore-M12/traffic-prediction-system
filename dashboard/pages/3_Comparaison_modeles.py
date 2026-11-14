import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from style import (
    appliquer_style,
    afficher_menu,
    afficher_banniere,
    titre_section,
    carte_kpi
)


# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Smart Traffic | Comparaison des modèles",
    layout="wide",
    initial_sidebar_state="expanded"
)

appliquer_style()
afficher_menu("Comparaison des modèles")

RACINE = Path(__file__).resolve().parents[2]
FICHIER_METRICS = RACINE / "results" / "metrics.csv"


# =========================================================
# CHARGEMENT DES DONNEES
# =========================================================

@st.cache_data
def charger_metriques():

    if not FICHIER_METRICS.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {FICHIER_METRICS}"
        )

    df = pd.read_csv(FICHIER_METRICS)

    colonnes_requises = [
        "model", "type", "retenu", "MAE", "RMSE", "R2"
    ]

    colonnes_absentes = [
        col for col in colonnes_requises if col not in df.columns
    ]

    if colonnes_absentes:
        raise ValueError(
            f"Colonnes absentes dans metrics.csv : {colonnes_absentes}"
        )

    for col in ["MAE", "RMSE", "R2"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["retenu"] = (
        df["retenu"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"true": True, "false": False})
    )

    if "score_pondere" in df.columns:
        df["score_pondere"] = pd.to_numeric(
            df["score_pondere"], errors="coerce"
        )

    return df.dropna(subset=["MAE", "RMSE", "R2"])


try:
    df_complet = charger_metriques()

except Exception as erreur:
    st.error(f"Impossible de charger les résultats : {erreur}")
    st.stop()


# =========================================================
# PREPARATION DES DONNEES
# =========================================================

noms_modeles = {
    "regression_lineaire": "Régression linéaire",
    "decision_tree": "Decision Tree",
    "random_forest": "Random Forest",
    "knn": "KNN",
    "svm": "SVM",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "mlp": "MLP",
    "persistance": "Persistance",
    "moyenne_par_heure": "Moyenne par heure",
    "moyenne_globale": "Moyenne globale"
}

df_complet["Modèle"] = (
    df_complet["model"]
    .map(noms_modeles)
    .fillna(df_complet["model"])
)

df_modeles = df_complet[
    df_complet["type"] == "modèle"
].copy()

df_baselines = df_complet[
    df_complet["type"] == "baseline"
].copy()

if df_modeles.empty:
    st.error("Aucun modèle d'apprentissage n'a été trouvé.")
    st.stop()


# =========================================================
# BANNIERE
# =========================================================

afficher_banniere(
    "Comparaison des modèles",
    "Évaluation comparative des algorithmes de prédiction du trafic routier.",
    "SMART TRAFFIC / MACHINE LEARNING"
)


# =========================================================
# PARAMETRES DE COMPARAISON
# =========================================================

titre_section(
    "Paramètres de comparaison",
    "Sélectionnez les algorithmes et le critère de classement."
)

selected_models = st.multiselect(
    "Modèles à comparer",
    options=df_modeles["Modèle"].tolist(),
    default=df_modeles["Modèle"].tolist(),
    key="selection_modeles"
)

col1, col2 = st.columns([1, 1])

with col1:
    ranking_metric = st.selectbox(
        "Critère de classement",
        options=["MAE", "RMSE", "R²"],
        key="critere_classement"
    )

with col2:
    afficher_baselines = st.toggle(
        "Afficher les modèles de référence",
        value=True,
        key="afficher_baselines"
    )


# =========================================================
# CORRESPONDANCE DES METRIQUES
# =========================================================

correspondance = {
    "MAE": "MAE",
    "RMSE": "RMSE",
    "R²": "R2"
}

colonne_classement = correspondance[ranking_metric]
ascending = ranking_metric != "R²"


# =========================================================
# FILTRAGE
# =========================================================

filtered_df = df_modeles[
    df_modeles["Modèle"].isin(selected_models)
].copy()

if filtered_df.empty:
    st.warning("Sélectionnez au moins un modèle pour afficher les résultats.")
    st.stop()


# =========================================================
# KPI
# =========================================================

meilleur_mae = filtered_df.loc[filtered_df["MAE"].idxmin()]
meilleur_rmse = filtered_df.loc[filtered_df["RMSE"].idxmin()]
meilleur_r2 = filtered_df.loc[filtered_df["R2"].idxmax()]

titre_section(
    "Synthèse des performances",
    "Meilleurs résultats individuels obtenus lors de la validation."
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    carte_kpi(
        "Modèles évalués",
        str(len(filtered_df)),
        "Algorithmes sélectionnés",
        "▦",
        "teal"
    )

with k2:
    carte_kpi(
        "Meilleur MAE",
        f"{meilleur_mae['MAE']:.2f}",
        meilleur_mae["Modèle"],
        "↘",
        "teal"
    )

with k3:
    carte_kpi(
        "Meilleur RMSE",
        f"{meilleur_rmse['RMSE']:.2f}",
        meilleur_rmse["Modèle"],
        "⌁",
        "blue"
    )

with k4:
    carte_kpi(
        "Meilleur R²",
        f"{meilleur_r2['R2']:.4f}",
        meilleur_r2["Modèle"],
        "R²",
        "purple"
    )


# =========================================================
# FONCTION DE STYLE DES GRAPHIQUES
# =========================================================

def styliser_graphique(fig, titre, titre_x, hauteur=350):

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=titre,
            font=dict(size=14, color="#263A50"),
            x=0.03
        ),
        height=hauteur,
        margin=dict(l=15, r=45, t=55, b=25),
        font=dict(
            family="Arial",
            size=11,
            color="#6F8193"
        ),
        xaxis_title=titre_x,
        yaxis_title="",
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        bargap=0.35
    )

    fig.update_xaxes(
        gridcolor="#EAF0F5",
        showgrid=True,
        zeroline=False,
        automargin=True
    )

    fig.update_yaxes(
        showgrid=False,
        automargin=True,
        autorange="reversed"
    )

    return fig


# =========================================================
# CLASSEMENT
# =========================================================

ranking_df = filtered_df.sort_values(
    by=colonne_classement,
    ascending=ascending
).reset_index(drop=True)


# =========================================================
# GRAPHIQUE MAE
# =========================================================

titre_section(
    "Analyse comparative",
    "Comparaison des erreurs de prédiction et de la qualité des modèles."
)

donnees_mae = filtered_df.sort_values("MAE", ascending=True)

fig_mae = px.bar(
    donnees_mae,
    x="MAE",
    y="Modèle",
    orientation="h",
    text="MAE",
    color="retenu",
    color_discrete_map={
        True: "#20A99F",
        False: "#438CC8"
    }
)

fig_mae.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside",
    cliponaxis=False
)

fig_mae = styliser_graphique(
    fig_mae,
    "MAE — Erreur absolue moyenne",
    "Véhicules / 5 min"
)

st.plotly_chart(fig_mae, use_container_width=True)


# =========================================================
# GRAPHIQUE RMSE
# =========================================================

donnees_rmse = filtered_df.sort_values("RMSE", ascending=True)

fig_rmse = px.bar(
    donnees_rmse,
    x="RMSE",
    y="Modèle",
    orientation="h",
    text="RMSE",
    color="retenu",
    color_discrete_map={
        True: "#20A99F",
        False: "#438CC8"
    }
)

fig_rmse.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside",
    cliponaxis=False
)

fig_rmse = styliser_graphique(
    fig_rmse,
    "RMSE — Erreur quadratique moyenne",
    "Véhicules / 5 min"
)

st.plotly_chart(fig_rmse, use_container_width=True)


# =========================================================
# GRAPHIQUE R2
# =========================================================

donnees_r2 = filtered_df.sort_values("R2", ascending=True)

fig_r2 = px.bar(
    donnees_r2,
    x="R2",
    y="Modèle",
    orientation="h",
    text="R2",
    color="retenu",
    color_discrete_map={
        True: "#20A99F",
        False: "#956AC5"
    }
)

fig_r2.update_traces(
    texttemplate="%{text:.4f}",
    textposition="outside",
    cliponaxis=False
)

fig_r2 = styliser_graphique(
    fig_r2,
    "R² — Coefficient de détermination",
    "Score R²"
)

fig_r2.update_xaxes(range=[0.94, 0.98])

st.plotly_chart(fig_r2, use_container_width=True)

st.caption(
    "L'axe du graphique R² est resserré entre 0,94 et 0,98 "
    "afin de rendre les différences plus visibles."
)


# =========================================================
# TABLEAU COMPARATIF
# =========================================================

titre_section(
    "Classement des modèles",
    f"Classement selon le critère sélectionné : {ranking_metric}."
)

tableau = ranking_df.copy()

tableau.insert(0, "Rang", range(1, len(tableau) + 1))

tableau["Statut"] = tableau["retenu"].map({
    True: "Sélection multicritère",
    False: "Autre modèle"
})

tableau = tableau.rename(
    columns={
        "Modèle": "Algorithme",
        "R2": "R²"
    }
)

colonnes = [
    "Rang",
    "Algorithme",
    "MAE",
    "RMSE",
    "R²",
    "Statut"
]

if "score_pondere" in tableau.columns:
    tableau = tableau.rename(
        columns={"score_pondere": "Score pondéré"}
    )
    colonnes.append("Score pondéré")

st.dataframe(
    tableau[colonnes],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Rang": st.column_config.NumberColumn(
            "Rang",
            format="%d"
        ),
        "MAE": st.column_config.NumberColumn(
            "MAE",
            format="%.2f"
        ),
        "RMSE": st.column_config.NumberColumn(
            "RMSE",
            format="%.2f"
        ),
        "R²": st.column_config.NumberColumn(
            "R²",
            format="%.4f"
        ),
        "Score pondéré": st.column_config.NumberColumn(
            "Score pondéré",
            format="%.2f"
        )
    }
)


# =========================================================
# MODELES DE REFERENCE
# =========================================================

if afficher_baselines and not df_baselines.empty:

    titre_section(
        "Modèles de référence",
        "Comparaison avec les méthodes de prédiction de base."
    )

    baselines = df_baselines[
        ["Modèle", "MAE", "RMSE", "R2"]
    ].rename(
        columns={"R2": "R²"}
    )

    st.dataframe(
        baselines,
        use_container_width=True,
        hide_index=True,
        column_config={
            "MAE": st.column_config.NumberColumn(
                "MAE",
                format="%.2f"
            ),
            "RMSE": st.column_config.NumberColumn(
                "RMSE",
                format="%.2f"
            ),
            "R²": st.column_config.NumberColumn(
                "R²",
                format="%.4f"
            )
        }
    )


# =========================================================
# BILAN COMPARATIF
# =========================================================

titre_section(
    "Bilan comparatif",
    "Principales observations issues de l'évaluation."
)

tous_modeles = df_modeles.copy()

mae_global = tous_modeles.loc[tous_modeles["MAE"].idxmin()]
r2_global = tous_modeles.loc[tous_modeles["R2"].idxmax()]

col_a, col_b = st.columns(2)

with col_a:
    st.metric(
        "Meilleure erreur absolue",
        f"{mae_global['MAE']:.2f}",
        mae_global["Modèle"]
    )

with col_b:
    st.metric(
        "Meilleur coefficient R²",
        f"{r2_global['R2']:.4f}",
        r2_global["Modèle"]
    )

modele_multicritere = df_modeles[
    df_modeles["retenu"] == True
]

if not modele_multicritere.empty:

    modele_choisi = modele_multicritere.iloc[0]

    if (
        "score_pondere" in modele_multicritere.columns
        and pd.notna(modele_choisi["score_pondere"])
    ):
        st.info(
            "La sélection multicritère repose sur plusieurs indicateurs "
            f"de performance. Le score obtenu est de "
            f"{modele_choisi['score_pondere']:.2f}/100."
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#9AA7B4;
        font-size:9px;
        padding-top:15px;
        margin-top:25px;
        border-top:1px solid #E0E7EE;
        letter-spacing:0.7px;">
        SMART TRAFFIC — TRAFFIC INTELLIGENCE PLATFORM
    </div>
    """,
    unsafe_allow_html=True
)