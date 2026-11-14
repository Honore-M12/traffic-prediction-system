"""Calcul des indicateurs à partir des sorties de SUMO (tripinfo + files)."""
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from . import config as cfg


def read_tripinfo(path):
    """Lit tripinfo.xml : une ligne par véhicule arrivé à destination.

    wait_s   = waitingTime (arrêté, < 0,1 m/s) + departDelay (attente avant
               d'entrer sur le réseau si l'approche est pleine).
    time_s   = durée du trajet + departDelay (pour la vitesse moyenne).
    stops    = waitingCount (nombre d'arrêts).
    sched_s  = instant de départ prévu (dans la fenêtre simulée).
    """
    rows = []
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag != "tripinfo":
            continue
        a = el.attrib
        delay = float(a.get("departDelay", 0))
        em = el.find("emissions")
        rows.append({
            "sched_s": float(a["depart"]) - delay,
            "wait_s": float(a["waitingTime"]) + delay,
            "time_s": float(a["duration"]) + delay,
            "route_m": float(a["routeLength"]),
            "stops": float(a["waitingCount"]),
            "co2_mg": float(em.attrib["CO2_abs"]) if em is not None else np.nan,
        })
        el.clear()
    return pd.DataFrame(rows)


def interval_metrics(trips, queue_samples, cycles, n_steps):
    """Indicateurs par intervalle de 5 min.

    trips          : DataFrame de read_tripinfo (véhicules rattachés à leur
                     intervalle de départ prévu)
    queue_samples  : liste (instant, véhicules à l'arrêt sur les 4 approches)
    cycles         : liste (instant, vert_principal, vert_secondaire)
    """
    idx = np.arange(n_steps)
    t = trips.copy()
    t["i"] = np.minimum((t["sched_s"] // cfg.STEP_S).astype(int), n_steps - 1)
    g = t.groupby("i")
    n = g.size().reindex(idx, fill_value=0)
    speed = (g["route_m"].sum() / g["time_s"].sum() * 3.6).reindex(idx)
    out = pd.DataFrame({
        "avg_wait_s": g["wait_s"].mean().reindex(idx),
        "avg_speed_kmh": speed,
        "stops_per_veh": g["stops"].mean().reindex(idx),
        "co2_g_per_veh": (g["co2_mg"].mean() / 1000.0).reindex(idx),
        "n_vehicles": n,
    })
    q = pd.DataFrame(queue_samples, columns=["t", "q"])
    q["i"] = np.minimum((q["t"] // cfg.STEP_S).astype(int), n_steps - 1)
    out["avg_queue_veh"] = q.groupby("i")["q"].mean().reindex(idx)
    c = pd.DataFrame(cycles, columns=["t", "g_main", "g_sec"])
    c["i"] = np.minimum((c["t"] // cfg.STEP_S).astype(int), n_steps - 1)
    gc = c.groupby("i")[["g_main", "g_sec"]].mean().reindex(idx)
    out["green_main_s"], out["green_secondary_s"] = gc["g_main"], gc["g_sec"]
    out["cycle_s"] = out["green_main_s"] + out["green_secondary_s"] + 2 * cfg.CLEARANCE_S
    return out


def overall_metrics(trips, queue_samples):
    """Indicateurs globaux (pondérés par le nombre de véhicules)."""
    return {
        "avg_wait_s": trips["wait_s"].mean(),
        "avg_queue_veh": float(np.mean([q for _, q in queue_samples])),
        "avg_speed_kmh": trips["route_m"].sum() / trips["time_s"].sum() * 3.6,
        "stops_per_veh": trips["stops"].mean(),
        "co2_g_per_veh": trips["co2_mg"].mean() / 1000.0,
        "n_vehicles": len(trips),
    }
