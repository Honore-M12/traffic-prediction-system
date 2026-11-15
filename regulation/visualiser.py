"""Visualisation dans sumo-gui : un créneau court, cycle fixe puis régulation IA.

La simulation reprend exactement le même trafic et le même contrôleur que
run_sumo.py, mais sur un créneau (par exemple la pointe du matin) et avec une
fenêtre SUMO centrée sur le carrefour, ralentie pour être regardée.

    - véhicules JAUNES : cycle fixe (40 s / 40 s)
    - véhicules BLEUS  : régulation IA
    - un trait vert ou rouge à chaque ligne d'arrêt = le feu de la voie

Exemples (depuis la racine du dépôt) :
    python -m regulation.visualiser --data data/processed/test.csv --predictor model \
        --model-info models/model_info.json
    python -m regulation.visualiser --data data/processed/test.csv --window 17:00-18:30 \
        --predictor csv --predictions results/predictions_test.csv --scenario ai

Les chiffres affichés à la fin ne concernent que ce créneau : ils illustrent la
simulation, la mesure officielle reste celle de run_sumo.py (journées complètes).
"""
import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
import traci

from . import config as cfg
from .decision import decide_green
from .demand import write_routes
from .network import SCENARIO_DIR, TLS_ID, build
from .run_sumo import INDICATORS, build_predictor, run_window
from .indicators import overall_metrics

FIXED_COLOR = None                 # jaune : couleur par défaut de SUMO
AI_COLOR = "0,150,255"             # bleu
HALF_WIDTH_M, HALF_HEIGHT_M = 110, 80      # zone visible autour du carrefour


def parse_window(text):
    """'07:30-09:00' -> (450, 540) en minutes depuis minuit."""
    try:
        a, b = text.split("-")
        h1, m1 = map(int, a.split(":"))
        h2, m2 = map(int, b.split(":"))
    except ValueError:
        raise SystemExit(f"--window doit avoir la forme HH:MM-HH:MM (reçu : {text!r})")
    start, end = h1 * 60 + m1, h2 * 60 + m2
    if not (0 <= start < end <= 24 * 60) or start % 5 or end % 5:
        raise SystemExit("--window : heures croissantes dans la même journée, par pas de 5 minutes")
    return start, end


def clock(seconds_of_day):
    s = int(seconds_of_day)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def colored_copy(src, dest, rgb):
    """Copie le fichier de véhicules en colorant le type 'car' (même trafic, autre couleur)."""
    text = Path(src).read_text(encoding="utf-8")
    assert '<vType id="car"' in text
    Path(dest).write_text(text.replace('<vType id="car"', f'<vType id="car" color="{rgb}"', 1),
                          encoding="utf-8")
    return dest


def make_hook(label, gui, t0_s, warm_s, horizon_s, delay_s, shots_dir, shot_every_s, tag):
    """Fonction appelée à chaque seconde simulée : caméra, ralenti, affichage, captures."""
    state = {"view": None}

    def hook(t, cycle_started, current):
        if gui and state["view"] is None:
            try:
                view = traci.gui.getIDList()[0]
                cx, cy = traci.junction.getPosition(TLS_ID)
                traci.gui.setSchema(view, "real world")
                traci.gui.setBoundary(view, cx - HALF_WIDTH_M, cy - HALF_HEIGHT_M,
                                      cx + HALF_WIDTH_M, cy + HALF_HEIGHT_M)
                state["view"] = view
            except Exception as e:                  # la caméra est un confort, pas une nécessité
                state["view"] = False
                print(f"  (caméra non réglée : {e})")
        if not (warm_s <= t <= horizon_s):
            return
        if cycle_started:
            g_main, g_sec = current
            print(f"  {clock(t0_s + t)} | {label:<15} | vert N-S {g_main:2d} s | "
                  f"vert E-O {g_sec:2d} s | cycle {g_main + g_sec + 2 * cfg.CLEARANCE_S:3d} s")
        if shots_dir and gui and state["view"] and (t - warm_s) % shot_every_s == 0:
            traci.gui.screenshot(state["view"],
                                 str(Path(shots_dir) / f"{tag}_{clock(t0_s + t).replace(':', 'h', 1)[:5]}.png"))
        if delay_s:
            time.sleep(delay_s)

    return hook


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="test.csv")
    ap.add_argument("--day", default="2020-05-19", help="journée (AAAA-MM-JJ)")
    ap.add_argument("--window", default="07:30-09:00", help="créneau à regarder (HH:MM-HH:MM)")
    ap.add_argument("--warmup", type=int, default=30,
                    help="minutes simulées avant le créneau, sans ralenti, pour que le carrefour "
                         "soit déjà chargé (défaut 30)")
    ap.add_argument("--scenario", default="both", choices=["both", "fixed", "ai"])
    ap.add_argument("--delay", type=int, default=40,
                    help="ralenti : millisecondes d'attente par seconde simulée (défaut 40, "
                         "0 = pleine vitesse)")
    ap.add_argument("--screenshots", type=int, default=0,
                    help="enregistre une capture d'écran toutes les N minutes simulées (0 = non)")
    ap.add_argument("--headless", action="store_true", help="sans fenêtre (test du programme)")
    ap.add_argument("--out-dir", default="results_view")
    ap.add_argument("--predictor", default="persistence",
                    choices=["persistence", "oracle", "csv", "model"])
    ap.add_argument("--predictions")
    ap.add_argument("--time-col")
    ap.add_argument("--pred-col")
    ap.add_argument("--model-info")
    ap.add_argument("--model-key", default=None)
    ap.add_argument("--model-path")
    ap.add_argument("--features")
    ap.add_argument("--seed", type=int, default=cfg.SEED)
    args = ap.parse_args(argv)

    start_min, end_min = parse_window(args.window)
    begin_min = max(0, start_min - args.warmup)
    df = pd.read_csv(args.data, parse_dates=["datetime"]).sort_values("datetime").reset_index(drop=True)
    day = df[df["datetime"].dt.strftime("%Y-%m-%d") == args.day]
    mod = day["datetime"].dt.hour * 60 + day["datetime"].dt.minute
    dw = day[(mod >= begin_min) & (mod < end_min)].reset_index(drop=True)
    if len(dw) != (end_min - begin_min) // 5:
        raise SystemExit(f"Données incomplètes pour {args.day} {begin_min // 60:02d}:{begin_min % 60:02d}"
                         f"-{end_min // 60:02d}:{end_min % 60:02d} dans {args.data}")

    predictor = build_predictor(args, df)
    pred = pd.Series(predictor.predict(df), index=df["datetime"]).reindex(dw["datetime"]).to_numpy()
    plans = [decide_green(f, h, m) for f, h, m in zip(pred, dw["hour"], dw["minute"])]
    fixed_plan = (cfg.FIXED_GREEN_S, cfg.FIXED_GREEN_S)

    net_file = SCENARIO_DIR / "c.net.xml"
    if not net_file.exists():
        build(SCENARIO_DIR)
    out_dir = Path(args.out_dir)
    shots_dir = out_dir / "captures" if args.screenshots else None
    for d in (out_dir, shots_dir):
        if d:
            Path(d).mkdir(parents=True, exist_ok=True)
    work = SCENARIO_DIR / "runs" / f"vue_{args.day}"
    work.mkdir(parents=True, exist_ok=True)
    routes = work / "routes_fixed.rou.xml"
    demand = write_routes(dw, routes, seed=args.seed)
    routes_ai = colored_copy(routes, work / "routes_ai.rou.xml", AI_COLOR)

    n, gui = len(dw), not args.headless
    t0_s = begin_min * 60
    warm_s = (start_min - begin_min) * 60
    horizon_s = n * cfg.STEP_S
    shot_every_s = max(args.screenshots, 1) * 60
    print(f"Créneau {args.window} du {args.day} (+{start_min - begin_min} min de mise en route) ; "
          f"{demand['n_vehicles']} véhicules ; prédicteur : {predictor.name}")
    if gui:
        print("Une fenêtre sumo-gui va s'ouvrir. Ne la ferme qu'à la fin de la simulation.")

    scenarios = [("fixed", "Cycle fixe", routes, lambda i: fixed_plan, "véhicules jaunes"),
                 ("ai", "Régulation IA", routes_ai, plans.__getitem__, "véhicules bleus")]
    results = {}
    try:
        for key, label, rfile, plan, colour in scenarios:
            if args.scenario not in ("both", key):
                continue
            print(f"\n=== {label} ({colour}) ===")
            hook = make_hook(label, gui, t0_s, warm_s, horizon_s,
                             args.delay / 1000 if gui else 0, shots_dir, shot_every_s, key)
            results[key] = run_window(
                net_file, rfile, work / f"tripinfo_{key}.xml", n, plan, args.seed, gui,
                extra_cmd=["--window-size", "1100,700"] if gui else (), on_step=hook)
    except traci.exceptions.FatalTraCIError:
        print("\nFenêtre fermée avant la fin : simulation interrompue.")
        return

    if set(results) == {"fixed", "ai"}:
        rows = []
        for key in ("fixed", "ai"):
            trips, queues, _ = results[key]
            trips = trips[trips["sched_s"] >= warm_s]            # créneau regardé seulement
            queues = [(t, q) for t, q in queues if t >= warm_s]
            rows.append(overall_metrics(trips, queues))
        print(f"\nIndicateurs sur le créneau {args.window} (mise en route exclue) :")
        table = []
        for k, lab, unit, better in INDICATORS:
            f, a = rows[0][k], rows[1][k]
            gain = (f - a) / f * 100 if better == "lower" else (a - f) / f * 100
            table.append({"indicateur": lab, "unité": unit, "cycle fixe": round(f, 3),
                          "IA": round(a, 3), "gain %": round(gain, 1)})
        table = pd.DataFrame(table)
        print(table.to_string(index=False))
        table.to_csv(out_dir / "indicateurs_creneau.csv", index=False)
        print(f"Tableau écrit dans {out_dir}/indicateurs_creneau.csv")
    if shots_dir:
        print(f"Captures d'écran dans {shots_dir}/")


if __name__ == "__main__":
    main()
