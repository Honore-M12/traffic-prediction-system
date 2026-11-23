"""Module de décision : transforme le trafic prévu en durées de vert.

Logique (minimisation du retard estimé, bornée), pour le carrefour fictif sur un axe :
  1. le débit prévu est mis à l'échelle de l'axe principal (véh/h) ;
  2. on en déduit la demande de la rue latérale (selon l'heure), majorée d'une
     marge de prudence SIDE_SAFETY (le contrôleur ne la mesure pas) ;
  3. on cherche le cycle et le partage du vert qui minimisent le retard total
     estimé (formule du retard uniforme du HCM), avec un facteur de progression
     sur l'axe principal (onde verte) ;
  4. les verts restent toujours entre un minimum et un maximum de sécurité ;
  5. un temps de dégagement fixe (jaune + tout-rouge) suit chaque vert ;
  6. (si N_JUNCTIONS > 1) les carrefours appliquent le même plan, décalé de
     OFFSET_S secondes de l'un à l'autre (onde verte sur l'axe principal).
"""
import math

from . import config as cfg


def scale_demand_vph(flow_5min):
    """Débit du dataset (véh / 5 min) -> demande de l'axe principal (véh/h)."""
    return flow_5min / cfg.FLOW_REF * cfg.PEAK_MAIN_VPH


def expected_share_main(hour, minute=0):
    """Part de l'axe principal dans la demande d'un carrefour (axe + rue latérale), selon l'heure (hypothèse)."""
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
    q_main = scale_demand_vph(max(float(predicted_flow), 0.0))
    share = expected_share_main(hour, minute)
    q_side = q_main * (1.0 - share) / share          # rue latérale d'un carrefour
    return q_main / cfg.SAT_MAIN_VPH, q_side / cfg.SAT_SIDE_VPH


def _delay_s(q, g, cycle, sat, pf=1.0):
    """Retard moyen par véhicule (s) pour un mouvement : retard uniforme
    (formule du Highway Capacity Manual) + retard de saturation."""
    lam = g / cycle
    cap = sat * lam                                    # capacité (véh/h)
    x = q / cap if cap > 0 else 9.9                    # degré de saturation
    d1 = 0.5 * cycle * (1 - lam) ** 2 / (1 - min(x, 1.0) * lam)
    t = 0.25                                           # période d'analyse (h)
    d2 = 900 * t * ((x - 1) + math.sqrt((x - 1) ** 2 + 4 * x / (cap * t))) if cap > 0 else 0.0
    return pf * d1 + d2


def decide_green(predicted_flow, hour, minute=0):
    """Retourne (vert axe principal, vert rues latérales) en secondes entières.

    On teste tous les cycles (par pas de 5 s) et tous les partages du vert
    admis par les bornes de sécurité, et on garde celui qui minimise le retard
    total estimé : somme, sur l'axe et sur la rue latérale, du débit multiplié
    par le retard moyen. Sur l'axe, le retard uniforme est réduit par un facteur
    de progression (onde verte) PROGRESSION_FACTOR.
    """
    q_main = scale_demand_vph(max(float(predicted_flow), 0.0))
    share = expected_share_main(hour, minute)
    q_side = q_main * (1.0 - share) / share * cfg.SIDE_SAFETY
    lost = 2 * cfg.CLEARANCE_S
    best, best_cost = None, float("inf")
    for cycle in range(cfg.CYCLE_MIN_S, cfg.CYCLE_MAX_S + 1, 5):
        g_total = cycle - lost
        lo = max(cfg.G_MIN_S, g_total - cfg.G_MAX_S)
        hi = min(cfg.G_MAX_S, g_total - cfg.G_MIN_S)
        for g_main in range(lo, hi + 1):
            g_side = g_total - g_main
            cost = (q_main * _delay_s(q_main, g_main, cycle, cfg.SAT_MAIN_VPH,
                                      cfg.PROGRESSION_FACTOR)
                    + q_side * _delay_s(q_side, g_side, cycle, cfg.SAT_SIDE_VPH))
            if cost < best_cost - 1e-9:
                best, best_cost = (g_main, g_side), cost
    return best


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
           green_main_s (axe principal), green_secondary_s (rues latérales),
           clearance_s, cycle_s, offsets_s (décalage de chaque carrefour, en s)
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
        "offsets_s": [k * cfg.OFFSET_S for k in range(cfg.N_JUNCTIONS)],
    }
