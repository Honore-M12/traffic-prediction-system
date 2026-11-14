"""Module de décision : transforme le trafic prévu en durées de vert.

Logique (méthode de Webster simplifiée) :
  1. le débit prévu est mis à l'échelle du carrefour fictif ;
  2. il est réparti entre l'axe principal (N-S) et l'axe secondaire (E-O) ;
  3. la durée du cycle dépend de la charge (court si peu de trafic, long si
     saturé) ;
  4. le vert est réparti proportionnellement à la demande de chaque axe, borné
     entre un minimum et un maximum de sécurité ;
  5. un temps de dégagement fixe (jaune + tout-rouge) suit chaque vert.
"""
import math

from . import config as cfg


def scale_demand_vph(flow_5min):
    """Débit du dataset (véh / 5 min) -> demande du carrefour fictif (véh/h)."""
    return flow_5min / cfg.FLOW_REF * cfg.PEAK_TOTAL_VPH


def expected_share_main(hour, minute=0):
    """Part prévue de la demande sur l'axe principal selon l'heure (hypothèse)."""
    h = hour + minute / 60.0
    return cfg.SHARE_MEAN + cfg.SHARE_AMP * math.cos(
        2 * math.pi * (h - cfg.SHARE_PEAK_HOUR) / 24.0)


def congestion_level(flow_5min):
    """Niveau de congestion et couleur d'alerte (vert / orange / rouge).

    Seuils de Joel (model_info.json) : faible jusqu'à 303, moyen jusqu'à 537
    véhicules par 5 minutes, élevé au-delà.
    """
    if flow_5min <= cfg.CONGESTION_LOW_FLOW:
        return "faible", "vert"
    if flow_5min <= cfg.CONGESTION_HIGH_FLOW:
        return "moyen", "orange"
    return "élevé", "rouge"


def _flow_ratios(predicted_flow, hour, minute):
    q_total = scale_demand_vph(max(float(predicted_flow), 0.0))
    share = expected_share_main(hour, minute)
    y_main = q_total * share / cfg.SAT_FLOW_AXIS_VPH
    y_sec = q_total * (1.0 - share) / cfg.SAT_FLOW_AXIS_VPH
    return y_main, y_sec


def decide_green(predicted_flow, hour, minute=0):
    """Retourne (vert_principal, vert_secondaire) en secondes entières."""
    y_main, y_sec = _flow_ratios(predicted_flow, hour, minute)
    y_tot = y_main + y_sec
    lost = 2 * cfg.CLEARANCE_S
    cycle = (1.5 * lost + 5.0) / (1.0 - min(y_tot, cfg.Y_MAX))
    cycle = min(max(cycle, cfg.CYCLE_MIN_S), cfg.CYCLE_MAX_S)
    g_total = cycle - lost
    if y_tot > 0:
        g_main = g_total * y_main / y_tot
        g_sec = g_total * y_sec / y_tot
    else:
        g_main = g_sec = g_total / 2.0
    g_main = int(round(min(max(g_main, cfg.G_MIN_S), cfg.G_MAX_S)))
    g_sec = int(round(min(max(g_sec, cfg.G_MIN_S), cfg.G_MAX_S)))
    return g_main, g_sec


def predict_green_time(conditions, predictor=None):
    """Point d'entrée pour le dashboard (page 6 : prédiction interactive).

    Paramètres
    ----------
    conditions : dict
        Heure : ``hour`` (0-23, et ``minute``) ou ``instant`` (date et heure).
        Soit ``predicted_flow`` (véh / 5 min) est fourni, soit un ``predictor``
        (ModelPredictor) est passé et reçoit ``conditions`` : il faut alors aussi
        ``historique`` (au moins 36 observations passées), ``instant``,
        ``temp_celsius``, ``wind_speed_kmh``, ``precip_mm``, ``weather_condition``.
    predictor : objet avec une méthode ``predict_one(conditions)``, optionnel.

    Retour
    ------
    dict : predicted_flow, congestion_level, congestion_color, load_ratio,
           green_main_s, green_secondary_s, clearance_s, cycle_s
    """
    if "hour" in conditions:
        hour, minute = int(conditions["hour"]), int(conditions.get("minute", 0))
    else:                                   # heure déduite de l'instant (page 6)
        import pandas as pd
        ts = pd.Timestamp(conditions.get("instant", conditions.get("datetime")))
        hour, minute = ts.hour, ts.minute
    if conditions.get("predicted_flow") is not None:
        flow = float(conditions["predicted_flow"])
    elif predictor is not None:
        flow = float(predictor.predict_one(conditions))
    else:
        raise ValueError(
            "Fournir 'predicted_flow' dans conditions ou un predictor "
            "(avec une méthode predict_one).")

    g_main, g_sec = decide_green(flow, hour, minute)
    y_main, y_sec = _flow_ratios(flow, hour, minute)
    level, color = congestion_level(flow)
    return {
        "predicted_flow": flow,
        "congestion_level": level,
        "congestion_color": color,
        "load_ratio": round(y_main + y_sec, 3),
        "green_main_s": g_main,
        "green_secondary_s": g_sec,
        "clearance_s": cfg.CLEARANCE_S,
        "cycle_s": g_main + g_sec + 2 * cfg.CLEARANCE_S,
    }
