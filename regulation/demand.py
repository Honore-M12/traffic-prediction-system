"""Convertit le dataset en trafic SUMO (fichier .rou.xml).

Pour chaque intervalle de 5 min, le débit du dataset est mis à l'échelle de
l'axe principal (véh/h). La demande de la rue latérale de chaque carrefour en
découle (part de l'axe principal = ``share_main``), puis tout est converti en
véhicules (arrivées de Poisson, graine fixe). Les deux scénarios (cycle fixe
et IA) reçoivent exactement le même fichier de trafic.
"""
import numpy as np

from . import config as cfg
from .decision import expected_share_main, scale_demand_vph
from .network import routes as network_routes

def make_share(df, rng):
    """Part réelle de l'axe principal dans la demande d'un carrefour : tendance horaire + bruit AR(1)."""
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

    Retourne la demande réelle : demand_total_vph (axe + 3 rues latérales),
    share_main (part de l'axe dans un carrefour), n_vehicles.
    """
    rng = np.random.default_rng(seed)
    share = make_share(df, rng)
    q_main = scale_demand_vph(df["traffic_flow"].to_numpy(float))          # véh/h
    q_side = q_main * (1.0 - share) / share                                # véh/h, par carrefour
    nj = cfg.N_JUNCTIONS

    departs = []     # (instant, itinéraire)
    for i in range(len(df)):
        t0 = i * cfg.STEP_S
        flows = [("main", q_main[i])]
        for j in range(1, nj + 1):
            flows += [(f"N{j}", q_side[i] / 2), (f"S{j}", q_side[i] / 2)]
        for route, q in flows:
            counts = rng.poisson(q / 3600.0, cfg.STEP_S)                   # par seconde
            for sec in np.nonzero(counts)[0]:
                for _ in range(counts[sec]):
                    departs.append((t0 + sec + rng.random(), route))
    departs.sort()

    lines = ['<routes>',
             '  <vType id="car" vClass="passenger" length="5" minGap="2.5" '
             f'maxSpeed="{cfg.SPEED_LIMIT_MS:.3f}" accel="2.6" decel="4.5" tau="1.0"/>']
    for name, edges in network_routes().items():
        lines.append(f'  <route id="r{name}" edges="{" ".join(edges)}"/>')
    for k, (t, r) in enumerate(departs):
        lines.append(f'  <vehicle id="v{k}" type="car" route="r{r}" depart="{t:.2f}" '
                     'departLane="best" departSpeed="max"/>')
    lines.append("</routes>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return {"demand_total_vph": q_main + nj * q_side, "share_main": share,
            "n_vehicles": len(departs)}
