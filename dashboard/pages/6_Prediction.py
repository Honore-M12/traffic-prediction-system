import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib
from pathlib import Path
from datetime import date, time, datetime

# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Smart Traffic | Prédiction",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CHEMINS DU PROJET
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATHS = [
    BASE_DIR / "models" / "best_model.pkl",
    BASE_DIR / "models" / "best_model.joblib",
    BASE_DIR / "models" / "best_model.joblib"
]

DATA_PATHS = [
    BASE_DIR / "data" / "processed" / "train.csv",
    BASE_DIR / "data" / "processed" / "dataset_A_cleaned.csv"
]

# =========================================================
# CHARGEMENT DU MODELE
# =========================================================

model = None
model_path_found = None

for path in MODEL_PATHS:
    if path.exists():
        try:
            model = joblib.load(path)
            model_path_found = path
            break
        except Exception:
            pass

# =========================================================
# CHARGEMENT DES DONNEES HISTORIQUES
# =========================================================

history_df = None

for path in DATA_PATHS:
    if path.exists():
        try:
            history_df = pd.read_csv(path)
            if "traffic_flow" in history_df.columns:
                break
        except Exception:
            history_df = None

lag_1 = 300
lag_3 = 300

if history_df is not None and "traffic_flow" in history_df.columns:

    traffic_history = (
        pd.to_numeric(history_df["traffic_flow"], errors="coerce")
        .dropna()
        .tolist()
    )

    if len(traffic_history) >= 3:
        lag_1 = float(traffic_history[-1])
        lag_3 = float(traffic_history[-3])

# =========================================================
# STYLE GLOBAL - STYLE A
# =========================================================

st.markdown("""
<style>

/* GENERAL */

.stApp {
    background: #F3F6FA;
    color: #24364B;
}

.block-container {
    max-width: 1600px;
    padding: 0.6rem 2rem 2.5rem 2rem !important;
}

header[data-testid="stHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    background: transparent !important;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    display: none !important;
}

#MainMenu, footer {
    visibility: hidden;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: #102A43;
    border-right: 1px solid #29435D;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 0.3rem 0.55rem 1rem 0.55rem !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
}

[data-testid="stSidebarNav"] {
    display: none !important;
}

/* BRAND */

.brand-container {
    padding: 12px 8px 18px 8px;
    border-bottom: 1px solid rgba(255,255,255,0.15);
    margin-bottom: 16px;
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 9px;
}

.brand-logo {
    width: 35px;
    height: 35px;
    border-radius: 8px;
    background: linear-gradient(135deg, #42B9C3, #287A9E);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 18px;
    font-weight: 800;
}

.brand-name {
    color: white;
    font-size: 17px;
    font-weight: 700;
}

.brand-subtitle {
    color: #9CB2C7;
    font-size: 9px;
    letter-spacing: 0.6px;
    margin-left: 44px;
    margin-top: -3px;
}

.nav-heading {
    color: #829BB2;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.3px;
    margin: 15px 8px 9px 8px;
}

.sidebar-active {
    background: #254765;
    border-left: 3px solid #43BEC5;
    border-radius: 6px;
    padding: 10px 9px;
    margin: 3px 0;
    color: white;
    font-size: 12px;
    font-weight: 600;
}

[data-testid="stSidebar"] [data-testid="stPageLink"] {
    border-radius: 6px;
    margin: 3px 0;
    padding: 2px 8px;
}

[data-testid="stSidebar"] [data-testid="stPageLink"]:hover {
    background: rgba(255,255,255,0.10);
}

[data-testid="stSidebar"] [data-testid="stPageLink"] p {
    color: #D6E2ED !important;
    font-size: 12px;
}

.sidebar-footer {
    border-top: 1px solid rgba(255,255,255,0.14);
    padding: 13px 8px;
    margin-top: 25px;
    color: #8FA8BE;
    font-size: 10px;
    line-height: 1.8;
}

/* HERO */

.hero {
    position: relative;
    overflow: hidden;
    height: 145px;
    border-radius: 9px;
    margin: 0 0 17px 0;
    padding: 25px 30px;
    background: linear-gradient(
        105deg,
        #102A43 0%,
        #174A68 65%,
        #246B80 100%
    );
    box-shadow: 0 3px 12px rgba(16,42,67,0.12);
}

.hero:before {
    content: "";
    position: absolute;
    right: -30px;
    top: -90px;
    width: 480px;
    height: 300px;
    background: radial-gradient(
        ellipse,
        rgba(115,190,207,0.30),
        transparent 68%
    );
}

.hero:after {
    content: "";
    position: absolute;
    right: 0;
    bottom: 0;
    width: 52%;
    height: 75px;
    opacity: 0.35;
    background:
        linear-gradient(
            155deg,
            transparent 48%,
            #9CCAD5 49%,
            #9CCAD5 50%,
            transparent 51%
        ),
        linear-gradient(
            165deg,
            transparent 58%,
            #9CCAD5 59%,
            #9CCAD5 60%,
            transparent 61%
        );
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-eyebrow {
    color: #83D2D8;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.6px;
    margin-bottom: 9px;
}

.hero-title {
    color: white;
    font-size: 27px;
    font-weight: 700;
    margin: 0 0 7px 0;
}

.hero-description {
    color: #D7E6EF;
    font-size: 12px;
    margin: 0;
}

/* SECTION TITLES */

.section-title {
    color: #20364D;
    font-size: 16px;
    font-weight: 700;
    margin-top: 22px;
    margin-bottom: 4px;
}

.section-subtitle {
    color: #8593A3;
    font-size: 11px;
    margin-bottom: 15px;
}

/* CARDS */

.info-card {
    background: white;
    border: 1px solid #E4EAF0;
    border-radius: 9px;
    padding: 17px;
    box-shadow: 0 2px 8px rgba(29,55,80,0.04);
}

.result-card {
    background: white;
    border: 1px solid #E4EAF0;
    border-radius: 10px;
    padding: 22px;
    box-shadow: 0 3px 12px rgba(29,55,80,0.05);
}

.result-label {
    color: #8291A1;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}

.result-value {
    color: #18334C;
    font-size: 36px;
    font-weight: 750;
    margin: 10px 0;
}

.result-unit {
    color: #8795A4;
    font-size: 11px;
}

.status-badge {
    display: inline-block;
    background: #DDF3F1;
    color: #168E88;
    padding: 6px 10px;
    border-radius: 5px;
    font-size: 11px;
    font-weight: 700;
}

/* FORM */

[data-testid="stForm"] {
    background: white;
    border: 1px solid #E4EAF0;
    border-radius: 9px;
    padding: 20px;
}

.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stDateInput label,
.stTimeInput label,
.stCheckbox label {
    color: #43566A;
    font-size: 11px;
    font-weight: 600;
}

/* BUTTON */

.stButton > button,
.stFormSubmitButton > button {
    background: #168F91;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 12px;
    font-weight: 700;
    transition: 0.2s;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #117779;
    color: white;
    border: none;
}

/* CHARTS */

[data-testid="stPlotlyChart"] {
    background: white;
    border: 1px solid #E5EAF0;
    border-radius: 8px;
    padding: 3px;
    box-shadow: 0 2px 8px rgba(29,55,80,0.035);
}

/* NOTICE */

.demo-notice {
    background: #FFF8E9;
    border: 1px solid #F0E2C4;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 20px;
    color: #80683A;
    font-size: 11px;
}

.demo-badge {
    background: #F2E4C7;
    color: #8D6A2D;
    padding: 4px 7px;
    border-radius: 4px;
    font-size: 9px;
    font-weight: 700;
    margin-right: 9px;
}

/* FOOTER */

.dashboard-footer {
    border-top: 1px solid #E0E7EE;
    padding-top: 12px;
    margin-top: 25px;
    text-align: center;
    color: #9AA7B4;
    font-size: 9px;
    letter-spacing: 0.7px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("""
    <div class="brand-container">
        <div class="brand-row">
            <div class="brand-logo">S</div>
            <div class="brand-name">Smart Traffic</div>
        </div>
        <div class="brand-subtitle">
            Traffic Intelligence Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="nav-heading">NAVIGATION PRINCIPALE</div>',
        unsafe_allow_html=True
    )

    st.page_link(
        "app.py",
        label="Tableau de bord",
        icon=":material/dashboard:"
    )

    st.page_link(
        "pages/3_Comparaison_modeles.py",
        label="Comparaison des modèles",
        icon=":material/analytics:"
    )

    st.page_link(
        "pages/4_Meilleur_modele.py",
        label="Meilleur modèle",
        icon=":material/leaderboard:"
    )

    st.markdown(
        '<div class="sidebar-active">▦ &nbsp; Prédiction</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="sidebar-footer">
        <strong style="color:#DCE7F0;">SMART TRAFFIC</strong><br>
        Machine Learning & Traffic Analysis<br>
        PROJECT VERSION 1.0
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="hero">
    <div class="hero-content">
        <div class="hero-eyebrow">SMART TRAFFIC / PREDICTION</div>
        <div class="hero-title">Prédiction du trafic routier</div>
        <div class="hero-description">
            Estimez le volume de circulation à partir des conditions
            météorologiques et temporelles.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# ETAT DU MODELE
# =========================================================

if model is None:
    st.markdown("""
    <div class="demo-notice">
        <span class="demo-badge">MODEL PENDING</span>
        Le formulaire est prêt. Le modèle entraîné sera connecté
        dès que les fichiers de Joel seront disponibles.
    </div>
    """, unsafe_allow_html=True)
else:
    st.success("Modèle de Machine Learning chargé.")

# =========================================================
# FORMULAIRE
# =========================================================

st.markdown(
    '<div class="section-title">Paramètres de prédiction</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">Définissez les conditions pour obtenir une estimation du trafic.</div>',
    unsafe_allow_html=True
)

with st.form("prediction_form"):

    st.markdown("#### Conditions temporelles")

    date_col, time_col = st.columns(2)

    with date_col:
        selected_date = st.date_input(
            "Date de prédiction",
            value=date.today()
        )

    with time_col:
        selected_time = st.time_input(
            "Heure de prédiction",
            value=time(8, 0)
        )

    st.markdown("---")
    st.markdown("#### Conditions météorologiques")

    weather_col1, weather_col2 = st.columns(2)

    with weather_col1:
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

    with weather_col2:
        precipitation = st.number_input(
            "Précipitations (mm)",
            min_value=0.0,
            max_value=200.0,
            value=0.0,
            step=0.5
        )

        weather_condition = st.selectbox(
            "Conditions météorologiques",
            [
                "Clear",
                "Clouds",
                "Rain",
                "Drizzle",
                "Mist",
                "Fog",
                "Snow",
                "Thunderstorm"
            ]
        )

    st.markdown("---")
    st.markdown("#### Informations complémentaires")

    holiday = st.checkbox(
        "Jour férié",
        value=False
    )

    submit = st.form_submit_button(
        "Lancer la prédiction",
        use_container_width=True
    )

# =========================================================
# TRAITEMENT DE LA PREDICTION
# =========================================================

if submit:

    prediction_datetime = datetime.combine(
        selected_date,
        selected_time
    )

    hour = prediction_datetime.hour
    minute = prediction_datetime.minute

    week_day = prediction_datetime.weekday()

    is_weekend = int(week_day >= 5)

    input_data = {
        "datetime": [prediction_datetime],
        "speed_kmh": [0.0],
        "week_day": [week_day],
        "holidays": [int(holiday)],
        "temp_celsius": [temperature],
        "wind_speed_kmh": [wind_speed],
        "precip_mm": [precipitation],
        "weather_condition": [weather_condition],
        "hour": [hour],
        "minute": [minute],
        "is_weekend": [is_weekend],
        "traffic_flow_lag_1": [lag_1],
        "traffic_flow_lag_3": [lag_3]
    }

    input_df = pd.DataFrame(input_data)

    st.session_state["last_input"] = input_df

    # -----------------------------------------------------
    # SI LE MODELE EST DISPONIBLE
    # -----------------------------------------------------

    if model is not None:

        try:

            if hasattr(model, "feature_names_in_"):
                expected_columns = list(model.feature_names_in_)

                missing_columns = [
                    col for col in expected_columns
                    if col not in input_df.columns
                ]

                if missing_columns:
                    st.error(
                        "Variables manquantes dans le formulaire : "
                        + ", ".join(missing_columns)
                    )
                    st.stop()

                model_input = input_df[expected_columns]

            else:
                model_input = input_df

            prediction = float(model.predict(model_input)[0])

            prediction = max(0, prediction)

            st.session_state["prediction_result"] = prediction

            st.session_state["prediction_history"] = (
                st.session_state.get("prediction_history", [])
            )

            st.session_state["prediction_history"].append({
                "Date": prediction_datetime.strftime("%d/%m/%Y %H:%M"),
                "Trafic prédit": round(prediction, 2),
                "Météo": weather_condition
            })

            st.session_state["prediction_history"] = (
                st.session_state["prediction_history"][-20:]
            )

        except Exception as error:
            st.error(
                f"Impossible d'effectuer la prédiction : {error}"
            )

    else:

        st.warning(
            "Le modèle n'est pas encore disponible. "
            "Le formulaire fonctionne, mais aucune prédiction réelle "
            "ne peut être calculée pour le moment."
        )

# =========================================================
# AFFICHAGE DU RESULTAT
# =========================================================

if "prediction_result" in st.session_state:

    prediction = st.session_state["prediction_result"]

    st.markdown(
        '<div class="section-title">Résultat de la prédiction</div>',
        unsafe_allow_html=True
    )

    result_col, status_col = st.columns([2, 1])

    with result_col:

        st.markdown(f"""
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
        """, unsafe_allow_html=True)

    with status_col:

        if prediction < 250:
            level = "Faible"
            color = "#168E88"
            message = "Circulation fluide"

        elif prediction < 450:
            level = "Modéré"
            color = "#C18A35"
            message = "Circulation moyenne"

        else:
            level = "Élevé"
            color = "#C45A5A"
            message = "Circulation dense"

        st.markdown(f"""
        <div class="result-card">
            <div class="result-label">
                NIVEAU DE CIRCULATION
            </div>
            <div style="
                color:{color};
                font-size:25px;
                font-weight:700;
                margin:12px 0;
            ">
                {level}
            </div>
            <div class="result-unit">
                {message}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Jauge de trafic

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prediction,
        number={
            "suffix": " véhicules",
            "font": {"size": 25, "color": "#20364D"}
        },
        title={
            "text": "Volume de trafic estimé",
            "font": {"size": 13, "color": "#43566A"}
        },
        gauge={
            "axis": {
                "range": [0, 794],
                "tickcolor": "#8593A3"
            },
            "bar": {"color": "#20A99F"},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 250], "color": "#DDF3F1"},
                {"range": [250, 450], "color": "#FFF0D4"},
                {"range": [450, 794], "color": "#F8DEDE"}
            ]
        }
    ))

    fig_gauge.update_layout(
        height=270,
        margin=dict(l=25, r=25, t=50, b=15),
        paper_bgcolor="white",
        font={"family": "Arial"}
    )

    st.plotly_chart(
        fig_gauge,
        use_container_width=True
    )

# =========================================================
# HISTORIQUE DES PREDICTIONS
# =========================================================

if st.session_state.get("prediction_history"):

    st.markdown(
        '<div class="section-title">Historique des prédictions</div>',
        unsafe_allow_html=True
    )

    history_predictions = pd.DataFrame(
        st.session_state["prediction_history"]
    )

    st.dataframe(
        history_predictions,
        use_container_width=True,
        hide_index=True
    )

    if st.button("Effacer l'historique"):
        st.session_state["prediction_history"] = []
        st.rerun()

# =========================================================
# INFORMATIONS SUR LES VARIABLES
# =========================================================

with st.expander("Comprendre les variables utilisées"):

    st.markdown("""
    - **Température** : température enregistrée au moment de la prédiction.
    - **Vent** : vitesse du vent en km/h.
    - **Précipitations** : quantité de pluie en mm.
    - **Météo** : état météorologique.
    - **Jour férié** : indique si la date correspond à un jour férié.
    - **Jour de la semaine** : calculé automatiquement à partir de la date.
    - **Week-end** : déterminé automatiquement.
    - **Lag 1** : trafic observé lors de l'intervalle précédent.
    - **Lag 3** : trafic observé trois intervalles auparavant.
    """)

# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="dashboard-footer">
    SMART TRAFFIC — TRAFFIC INTELLIGENCE PLATFORM
</div>
""", unsafe_allow_html=True)