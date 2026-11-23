"""Visualisation dans sumo-gui : on voit l'impact de l'IA pendant la simulation.

Par défaut, DEUX fenêtres sumo-gui s'ouvrent côte à côte et avancent en même
temps, sur exactement le même trafic :

    - fenêtre de GAUCHE : cycle fixe (90 s : 56 s axe / 24 s rues latérales)
    - fenêtre de DROITE : régulation IA (verts recalculés d'après la prévision)

Les véhicules sont colorés selon leur temps d'attente (même code de couleurs
dans les deux fenêtres) : VERT = ils roulent, JAUNE = ils attendent environ
15 s, ROUGE = ils attendent 30 s ou plus. Moins de rouge à droite = l'IA agit.
Un compteur est affiché dans le terminal chaque minute simulée : file d'attente
et attente maximale des deux scénarios, côte à côte.

    python -m regulation.visualiser --data data/processed/test.csv --predictor model \
        --model-info models/model_info.json

Options : --successif (les deux scénarios l'un après l'autre, dans une seule
fenêtre, véhicules jaunes puis bleus), --colors scenario (couleur par scénario),
--window 17:00-18:30, --delay 100 (plus lent), --screenshots 5, --focus J1.

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
from .network import SCENARIO_DIR, TLS_IDS, build, incoming_edges
from .run_sumo import INDICATORS, build_predictor, iter_window, run_window
from .indicators import overall_metrics

FIXED_COLOR = None                 # jaune : couleur par défaut de SUMO
AI_COLOR = "0,150,255"             # bleu
HALF_WIDTH_M, HALF_HEIGHT_M = 480, 170    # zone visible : les 3 carrefours (--focus J1/J2/J3 : zoom)
ZOOM_WIDTH_M, ZOOM_HEIGHT_M = 110, 80


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


def wait_color(w):
    """Couleur d'un véhicule selon son temps d'attente (s) : vert -> jaune -> rouge."""
    f = min(max(w, 0.0) / 30.0, 1.0)
    if f < 0.5:
        return (int(510 * f), 200, 0, 255)
    return (255, int(200 * (1 - (f - 0.5) * 2)), 0, 255)


def make_hook(label, gui, t0_s, warm_s, horizon_s, delay_s, shots_dir, shot_every_s, tag,
              focus="all", quiet=False, color_wait=False, stats=None):
    """Fonction appelée à chaque seconde simulée : caméra, couleurs, ralenti,
    affichage, captures. ``stats`` (dict) reçoit la file et l'attente en direct."""
    state = {"view": None}
    edges = incoming_edges()

    def hook(t, cycle_started, current):
        if gui and state["view"] is None:
            try:
                view = traci.gui.getIDList()[0]
                if focus == "all" and len(TLS_IDS) > 1:   # centré sur le carrefour du milieu
                    cx, cy = traci.junction.getPosition(TLS_IDS[len(TLS_IDS) // 2])
                    hw, hh = HALF_WIDTH_M, HALF_HEIGHT_M
                elif focus == "all":                    # un seul carrefour : on le voit de près
                    cx, cy = traci.junction.getPosition(TLS_IDS[0])
                    hw, hh = ZOOM_WIDTH_M, ZOOM_HEIGHT_M
                else:
                    cx, cy = traci.junction.getPosition(focus)
                    hw, hh = ZOOM_WIDTH_M, ZOOM_HEIGHT_M
                traci.gui.setSchema(view, "real world")
                traci.gui.setBoundary(view, cx - hw, cy - hh, cx + hw, cy + hh)
                state["view"] = view
            except Exception as e:                  # la caméra est un confort, pas une nécessité
                state["view"] = False
                print(f"  (caméra non réglée : {e})")
        if t % 2 == 0 and (color_wait or (stats is not None and t % 5 == 0)):
            vehs = traci.vehicle.getIDList()
            waits = [traci.vehicle.getWaitingTime(v) for v in vehs]
            if color_wait and gui:
                for v, w in zip(vehs, waits):
                    traci.vehicle.setColor(v, wait_color(w))
            if stats is not None and t % 5 == 0:
                q = sum(traci.edge.getLastStepHaltingNumber(e) for e in edges)
                stats.update(queue=q, max_wait=max(waits, default=0.0),
                             n_stopped=sum(1 for w in waits if w > 0))
                if warm_s <= t <= horizon_s:
                    stats["q_sum"] = stats.get("q_sum", 0) + q
                    stats["q_n"] = stats.get("q_n", 0) + 1
        if not (warm_s <= t <= horizon_s):
            return
        if cycle_started and not quiet:
            g_main, g_sec = current
            print(f"  {clock(t0_s + t)} | {label:<15} | vert axe {g_main:2d} s | "
                  f"vert rues latérales {g_sec:2d} s | cycle {g_main + g_sec + 2 * cfg.CLEARANCE_S:3d} s")
        if shots_dir and gui and state["view"] and (t - warm_s) % shot_every_s == 0:
            traci.gui.screenshot(state["view"],
                                 str(Path(shots_dir) / f"{tag}_{clock(t0_s + t).replace(':', 'h', 1)[:5]}.png"))
        if delay_s:
            time.sleep(delay_s)

    return hook


def live_line(t0_s, t, st_fixed, st_ai, cycle_ai):
    """Ligne de comparaison en direct (cycle fixe | IA)."""
    def mean(st):
        return st.get("q_sum", 0) / st["q_n"] if st.get("q_n") else 0.0

    def fmt(st):
        return (f"file {st.get('queue', 0):2d} véh (moy. {mean(st):4.1f}), "
                f"attente max {st.get('max_wait', 0):3.0f} s")
    mf, ma = mean(st_fixed), mean(st_ai)
    delta = f"{(ma - mf) / mf * 100:+.0f} %" if mf > 0 else "  -"
    return (f"  {clock(t0_s + t)} | FIXE : {fmt(st_fixed)} | "
            f"IA : {fmt(st_ai)}, cycle {cycle_ai:2d} s | file moyenne IA {delta}")


def run_side_by_side(net_file, routes, work, n, fixed_plan, plans, seed, gui, args,
                     t0_s, warm_s, horizon_s, shots_dir, shot_every_s):
    """Deux simulations avancées ensemble, seconde par seconde (deux fenêtres)."""
    color_wait = args.colors == "attente"
    specs = [("fixed", "Cycle fixe", lambda i: fixed_plan),
             ("ai", "Régulation IA", plans.__getitem__)]
    stats = {k: {} for k, _, _ in specs}
    current_cycle = {"ai": plans[0][0] + plans[0][1] + 2 * cfg.CLEARANCE_S}
    gens = {}
    for idx, (key, label, plan) in enumerate(specs):
        base_hook = make_hook(label, gui, t0_s, warm_s, horizon_s, 0, shots_dir, shot_every_s,
                              key, args.focus, quiet=True, color_wait=color_wait, stats=stats[key])

        def hook(t, started, cur, _k=key, _h=base_hook):
            if _k == "ai":
                current_cycle["ai"] = cur[0] + cur[1] + 2 * cfg.CLEARANCE_S
            _h(t, started, cur)

        extra = (["--window-size", f"{args.win_width},{args.win_height}",
                  "--window-pos", f"{idx * (args.win_width + 12)},40"] if gui else ())
        gens[key] = iter_window(net_file, routes, work / f"tripinfo_{key}.xml", n, plan, seed, gui,
                                extra_cmd=extra, on_step=hook, label=key)
    alive = {k: True for k in gens}
    results = {}
    try:
        while any(alive.values()):
            t = 0
            for key, gen in gens.items():
                if alive[key]:
                    try:
                        t = next(gen)
                    except StopIteration as stop:
                        results[key] = stop.value
                        alive[key] = False
            if all(alive.values()) and warm_s <= t <= horizon_s:
                if (t - warm_s) % args.report_every == 0:
                    print(live_line(t0_s, t, stats["fixed"], stats["ai"], current_cycle["ai"]))
                if gui and args.delay:
                    time.sleep(args.delay / 1000)
    finally:
        for gen in gens.values():
            gen.close()
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="test.csv")
    ap.add_argument("--day", default="2020-05-19", help="journée (AAAA-MM-JJ)")
    ap.add_argument("--window", default="07:30-09:00", help="créneau à regarder (HH:MM-HH:MM)")
    ap.add_argument("--warmup", type=int, default=30,
                    help="minutes simulées avant le créneau, sans ralenti, pour que l'axe "
                         "soit déjà chargé (défaut 30)")
    ap.add_argument("--scenario", default="both", choices=["both", "fixed", "ai"])
    ap.add_argument("--successif", action="store_true",
                    help="les deux scénarios l'un après l'autre dans une seule fenêtre "
                         "(par défaut : deux fenêtres côte à côte)")
    ap.add_argument("--colors", choices=["attente", "scenario"],
                    help="attente : vert -> rouge selon l'attente (défaut en côte à côte) ; "
                         "scenario : jaune = cycle fixe, bleu = IA (défaut en successif)")
    ap.add_argument("--win-width", type=int, default=660, help="largeur de chaque fenêtre (défaut 660)")
    ap.add_argument("--win-height", type=int, default=620, help="hauteur de chaque fenêtre (défaut 620)")
    ap.add_argument("--report-every", type=int, default=60,
                    help="secondes simulées entre deux lignes du compteur en direct (défaut 60)")
    ap.add_argument("--focus", default="all", choices=["all"] + TLS_IDS,
                    help="all = tous les carrefours dans la fenêtre (zoom si un seul) ; J1... = zoom sur un carrefour")
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
    fixed_plan = (cfg.FIXED_MAIN_GREEN_S, cfg.FIXED_SIDE_GREEN_S)

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
    side_by_side = args.scenario == "both" and not args.successif
    if args.colors is None:
        args.colors = "attente" if side_by_side else "scenario"
    routes_ai = colored_copy(routes, work / "routes_ai.rou.xml", AI_COLOR)

    n, gui = len(dw), not args.headless
    t0_s = begin_min * 60
    warm_s = (start_min - begin_min) * 60
    horizon_s = n * cfg.STEP_S
    shot_every_s = max(args.screenshots, 1) * 60
    print(f"Créneau {args.window} du {args.day} (+{start_min - begin_min} min de mise en route) ; "
          f"{demand['n_vehicles']} véhicules ; prédicteur : {predictor.name}")
    results = {}
    try:
        if side_by_side:
            if gui:
                print("Deux fenêtres sumo-gui vont s'ouvrir : GAUCHE = cycle fixe, DROITE = régulation IA. "
                      "Ne les ferme qu'à la fin.")
            if args.colors == "attente":
                print("Couleur des véhicules : VERT = roule, JAUNE = attend ~15 s, ROUGE = attend 30 s ou plus.")
            print("\n  Compteur en direct (une ligne par minute simulée) :")
            results = run_side_by_side(net_file, routes, work, n, fixed_plan, plans, args.seed, gui,
                                       args, t0_s, warm_s, horizon_s, shots_dir, shot_every_s)
        else:
            if gui:
                print("Une fenêtre sumo-gui va s'ouvrir. Ne la ferme qu'à la fin de la simulation.")
            scenarios = [("fixed", "Cycle fixe", routes, lambda i: fixed_plan, "véhicules jaunes"),
                         ("ai", "Régulation IA", routes_ai, plans.__getitem__, "véhicules bleus")]
            for key, label, rfile, plan, colour in scenarios:
                if args.scenario not in ("both", key):
                    continue
                print(f"\n=== {label} ({colour}) ===")
                hook = make_hook(label, gui, t0_s, warm_s, horizon_s,
                                 args.delay / 1000 if gui else 0, shots_dir, shot_every_s, key,
                                 args.focus, color_wait=args.colors == "attente")
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
