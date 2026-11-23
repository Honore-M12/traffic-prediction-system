from regulation.decision import decide_green, predict_green_time
from regulation import config as cfg

# 1. Les bornes de sécurité ne sont jamais dépassées
for flow in range(0, 801, 10):
    for hour in range(24):
        gm, gs = decide_green(flow, hour)
        assert cfg.G_MIN_S <= gm <= cfg.G_MAX_S, (flow, hour, gm)
        assert cfg.G_MIN_S <= gs <= cfg.G_MAX_S, (flow, hour, gs)
        cycle = gm + gs + 2 * cfg.CLEARANCE_S
        assert cfg.CYCLE_MIN_S <= cycle <= cfg.CYCLE_MAX_S, (flow, hour, cycle)
print("bornes OK (verts 10-60 s, cycle 40-120 s)")

# 2. Plus de trafic = plus de vert pour l'axe principal
for flow in (100, 300, 500, 700):
    r = predict_green_time({"hour": 8, "predicted_flow": flow})
    print(f"débit {flow:3d} | {r['congestion_level']:6s} ({r['congestion_color']:6s}) | "
          f"vert axe {r['green_main_s']:2d} s | vert rues latérales {r['green_secondary_s']:2d} s | "
          f"cycle {r['cycle_s']:3d} s | décalages {r['offsets_s']}")
