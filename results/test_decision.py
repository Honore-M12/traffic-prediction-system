from regulation.decision import decide_green, predict_green_time
from regulation import config as cfg

# 1. Les bornes de sécurité ne sont jamais dépassées
for flow in range(0, 801, 10):
    for hour in range(24):
        gm, gs = decide_green(flow, hour)
        assert cfg.G_MIN_S <= gm <= cfg.G_MAX_S, (flow, hour, gm)
        assert cfg.G_MIN_S <= gs <= cfg.G_MAX_S, (flow, hour, gs)
print("bornes OK")

# 2. Plus de trafic = cycle plus long
for flow in (100, 300, 500, 700):
    r = predict_green_time({"hour": 8, "predicted_flow": flow})
    print(f"débit {flow:3d} | {r['congestion_level']:6s} ({r['congestion_color']:6s}) | "
          f"vert N-S {r['green_main_s']:2d} s | vert E-O {r['green_secondary_s']:2d} s | cycle {r['cycle_s']:3d} s")
