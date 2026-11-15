"""Convertit le dataset en trafic SUMO (fichier .rou.xml).

Pour chaque intervalle de 5 min, le débit est mis à l'échelle du carrefour,
réparti entre l'axe principal (N-S) et l'axe secondaire (E-O), puis converti
en véhicules (arrivées de Poisson, graine fixe). Les deux scénarios (cycle fixe
et IA) reçoivent exactement le même fichier de trafic.
"""
import numpy as np

from . import config as cfg
from .decision import expected_share_main, scale_demand_vph

ROUTES = {"N": ("N_C", "C_S"), "S": ("S_C", "C_N"),
          "E": ("E_C", "C_W"), "W": ("W_C", "C_E")}


def make_share(df, rng):
    """Part réelle de la demande sur l'axe principal : tendance horaire + bruit AR(1)."""
    n = len(df)
    expected = np.array([expected_share_main(h, m)
                         for h, m in zip(df["hour"], df["minute"])])
    rho = cfg.SHARE_NOISE_RHO
    eps = rng.normal(0.0, cfg.SHARE_NOISE_STD * np.sqrt(1 - rho ** 2), n)
    noise = np.zeros(n)
    noise[0] = rng.normal(0.0, cfg.SHARE_NOISE_STD)
    for i in range(1, n):
        noise[i] = rho * noise[i - 1] + eps[i]
    return np.clip(expected + noise, cfg.SHARE_MIN, cfg.SHARE_MAX)


def write_routes(df, path, seed=cfg.SEED):
    """Écrit le .rou.xml pour les lignes de ``df`` (pas de 5 min consécutifs).

    Retourne un DataFrame avec la demande réelle (demand_total_vph, share_main).
    """
    rng = np.random.default_rng(seed)
    share = make_share(df, rng)
    q_total = scale_demand_vph(df["traffic_flow"].to_numpy(float))        # véh/h

    departs = []     # (instant, approche)
    for i, (q, s) in enumerate(zip(q_total, share)):
        t0 = i * cfg.STEP_S
        lam = {"main": q * s / 3600.0, "sec": q * (1 - s) / 3600.0}
        for axis, approaches in (("main", "NS"), ("sec", "EW")):
            counts = rng.poisson(lam[axis], cfg.STEP_S)            # par seconde
            for sec in np.nonzero(counts)[0]:
                for _ in range(counts[sec]):
                    departs.append((t0 + sec + rng.random(), approaches[rng.integers(2)]))
    departs.sort()

    lines = ['<routes>',
             '  <vType id="car" vClass="passenger" length="5" minGap="2.5" '
             f'maxSpeed="{cfg.SPEED_LIMIT_MS:.3f}" accel="2.6" decel="4.5" tau="1.0"/>']
    for a, (e1, e2) in ROUTES.items():
        lines.append(f'  <route id="r{a}" edges="{e1} {e2}"/>')
    for k, (t, a) in enumerate(departs):
        lines.append(f'  <vehicle id="v{k}" type="car" route="r{a}" depart="{t:.2f}" '
                     'departLane="best" departSpeed="max"/>')
    lines.append("</routes>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return {"demand_total_vph": q_total, "share_main": share, "n_vehicles": len(departs)}
