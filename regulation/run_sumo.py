"""Simulation SUMO : cycle fixe contre régulation IA, sur les mêmes véhicules.

Exemples (depuis la racine du dépôt) :
    # rapide, sans modèle : prédiction = débit des 5 minutes précédentes
    python -m regulation.run_sumo --data data/processed/test.csv

    # avec les prédictions de Joel
    python -m regulation.run_sumo --data data/processed/test.csv --predictor csv \
        --predictions results/predictions_test.csv

    # validation finale avec le modèle sauvegardé
    python -m regulation.run_sumo --data data/processed/test.csv --predictor model \
        --model-info models/model_info.json

    # toutes les journées complètes du test (long) ou des journées choisies
    python -m regulation.run_sumo --data data/processed/test.csv --days all
    python -m regulation.run_sumo --data data/processed/test.csv --days 2020-05-19,2020-05-23
"""
import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import sumolib
import traci

from . import config as cfg
from .decision import congestion_level, decide_green
from .demand import write_routes
from .indicators import interval_metrics, overall_metrics, read_tripinfo
from .network import SCENARIO_DIR, TLS_ID, build, incoming_edges
from .predictors import (CsvPredictor, ModelPredictor, OraclePredictor,
                         PersistencePredictor, load_model_info)

INDICATORS = [
    ("avg_wait_s", "Temps d'attente moyen", "s/véh", "lower"),
    ("avg_queue_veh", "Longueur moyenne des files", "véh à l'arrêt", "lower"),
    ("avg_speed_kmh", "Vitesse moyenne", "km/h", "higher"),
    ("stops_per_veh", "Nombre moyen d'arrêts", "arrêts/véh", "lower"),
    ("co2_g_per_veh", "Émissions de CO2 (optionnel)", "g/véh", "lower"),
]
DEFAULT_DAYS = "2020-05-19,2020-05-23"     # un mardi et un samedi
SAMPLE_EVERY_S = 5                         # échantillonnage des files
FLUSH_MAX_S = 3600                         # vidage du réseau après la fenêtre


def run_window(net_file, routes_file, tripinfo_file, n_steps, plan, seed, gui=False,
               extra_cmd=(), on_step=None):
    """Une simulation SUMO complète. ``plan(i)`` donne (vert_N-S, vert_E-O) pour
    un cycle qui démarre pendant l'intervalle de 5 min numéro ``i``.

    ``on_step(t, cycle_started, current)`` (facultatif) est appelé à chaque seconde
    simulée ; utilisé par le mode visualisation (regulation/visualiser.py)."""
    binary = sumolib.checkBinary("sumo-gui" if gui else "sumo")
    cmd = [binary, "-n", str(net_file), "-r", str(routes_file),
           "--tripinfo-output", str(tripinfo_file),
           "--device.emissions.probability", "1",
           "--time-to-teleport", "-1", "--seed", str(seed),
           "--no-step-log", "true", "--no-warnings", "true"]
    if gui:
        cmd += ["--start", "true", "--quit-on-end", "true"]
    cmd += [str(a) for a in extra_cmd]
    traci.start(cmd)
    edges = incoming_edges()
    horizon = n_steps * cfg.STEP_S
    queue_samples, cycles = [], []
    last_phase, current, t = -1, (cfg.FIXED_GREEN_S, cfg.FIXED_GREEN_S), 0
    try:
        while True:
            traci.simulationStep()
            t = int(traci.simulation.getTime())
            if t > horizon and traci.simulation.getMinExpectedNumber() == 0:
                break
            if t > horizon + FLUSH_MAX_S:
                print(f"  Attention : réseau non vidé {FLUSH_MAX_S}s après la fenêtre.")
                break
            phase = traci.trafficlight.getPhase(TLS_ID)
            cycle_started = False
            if phase != last_phase:
                i = min(t // cfg.STEP_S, n_steps - 1)
                # setPhaseDuration fixe le temps restant ; la seconde déjà écoulée
                # quand on détecte le changement de phase compte, d'où le « - 1 »
                # (vérifié : la durée obtenue est exactement celle demandée).
                if phase == 0:                         # début de cycle : décision
                    current = plan(i)
                    cycle_started = True
                    cycles.append((t, *current))
                    traci.trafficlight.setPhaseDuration(TLS_ID, current[0] - 1)
                elif phase == 3:
                    traci.trafficlight.setPhaseDuration(TLS_ID, current[1] - 1)
                last_phase = phase
            if on_step is not None:
                on_step(t, cycle_started, current)
            if t % SAMPLE_EVERY_S == 0 and t <= horizon:
                queue_samples.append(
                    (t, sum(traci.edge.getLastStepHaltingNumber(e) for e in edges)))
    finally:
        try:
            traci.close()
        except Exception:        # fenêtre déjà fermée par l'utilisateur
            pass
    return read_tripinfo(tripinfo_file), queue_samples, cycles


def select_windows(df, days_arg):
    df = df.copy()
    df["day"] = df["datetime"].dt.strftime("%Y-%m-%d")
    full = [d for d, g in df.groupby("day") if len(g) == 288]
    wanted = full if days_arg == "all" else [d.strip() for d in days_arg.split(",")]
    missing = [d for d in wanted if d not in full]
    if missing:
        raise SystemExit(f"Journées absentes ou incomplètes dans le fichier : {missing}\n"
                         f"Journées complètes disponibles : {full[0]} -> {full[-1]}")
    return [(d, df[df["day"] == d].drop(columns="day").reset_index(drop=True))
            for d in wanted]


def build_predictor(args, df):
    if args.predictor == "persistence":
        return PersistencePredictor()
    if args.predictor == "oracle":
        return OraclePredictor()
    if args.predictor == "csv":
        if not args.predictions:
            raise SystemExit("--predictions est requis avec --predictor csv")
        return CsvPredictor(args.predictions, args.time_col, args.pred_col,
                            name=f"csv:{Path(args.predictions).name}")
    if args.predictor == "model":
        if args.model_info:
            info = load_model_info(args.model_info, args.model_key)
            model_path = Path(args.model_info).parent / info["fichier"]
            features = info["variables_entree"]
        elif args.model_path and args.features:
            model_path, features = args.model_path, args.features.split(",")
        else:
            raise SystemExit("--model-info ou --model-path + --features requis")
        p = ModelPredictor(model_path, features, data_dir=Path(args.data).parent)
        p.name = f"model:{Path(model_path).name}"
        return p
    raise SystemExit(f"prédicteur inconnu : {args.predictor}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="test.csv (pas de 5 min, colonne datetime)")
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--days", default=DEFAULT_DAYS,
                    help="journées à simuler (AAAA-MM-JJ séparées par des virgules) ou 'all'")
    ap.add_argument("--predictor", default="persistence",
                    choices=["persistence", "oracle", "csv", "model"])
    ap.add_argument("--predictions")
    ap.add_argument("--time-col")
    ap.add_argument("--pred-col")
    ap.add_argument("--model-info", help="models/model_info.json")
    ap.add_argument("--model-key", default=None, help="seulement pour l'ancien format A/B")
    ap.add_argument("--model-path")
    ap.add_argument("--features")
    ap.add_argument("--seed", type=int, default=cfg.SEED)
    ap.add_argument("--gui", action="store_true", help="ouvre sumo-gui (pour regarder)")
    ap.add_argument("--peak-vph", type=float,
                    help=f"demande totale au pic du dataset (défaut {cfg.PEAK_TOTAL_VPH:.0f} véh/h)")
    ap.add_argument("--fixed-green", type=int,
                    help=f"vert par axe du cycle fixe de référence (défaut {cfg.FIXED_GREEN_S} s)")
    ap.add_argument("--work-dir", default=str(SCENARIO_DIR / "runs"),
                    help="dossier des fichiers temporaires SUMO")
    ap.add_argument("--rebuild-net", action="store_true", help="reconstruit le réseau SUMO")
    args = ap.parse_args(argv)

    df = pd.read_csv(args.data, parse_dates=["datetime"]).sort_values("datetime").reset_index(drop=True)
    windows = select_windows(df, args.days)
    predictor = build_predictor(args, df)
    pred_all = pd.Series(predictor.predict(df), index=df["datetime"])

    if args.peak_vph:
        cfg.PEAK_TOTAL_VPH = args.peak_vph
    if args.fixed_green:
        cfg.FIXED_GREEN_S = args.fixed_green
    net_file = SCENARIO_DIR / "c.net.xml"
    if args.rebuild_net or not net_file.exists():
        build(SCENARIO_DIR)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    details, trips_all = [], {"fixed": [], "ai": []}
    queues_all = {"fixed": [], "ai": []}
    summary_rows = []

    def add_summary(scope, tf, qf, ta, qa):
        mf, ma = overall_metrics(tf, qf), overall_metrics(ta, qa)
        for key, label, unit, better in INDICATORS:
            f, a = mf[key], ma[key]
            gain = (f - a) / f * 100 if better == "lower" else (a - f) / f * 100
            summary_rows.append({"scope": scope, "indicator": key, "label": label,
                                 "unit": unit, "fixed": round(f, 3), "ai": round(a, 3),
                                 "gain_pct": round(gain, 1)})

    for w, (day, dw) in enumerate(windows):
        n = len(dw)
        run_dir = Path(args.work_dir) / day
        run_dir.mkdir(parents=True, exist_ok=True)
        routes = run_dir / "routes.rou.xml"
        demand = write_routes(dw, routes, seed=args.seed + w)
        pred = pred_all.reindex(dw["datetime"]).to_numpy()
        plans = [decide_green(f, h, m) for f, h, m in zip(pred, dw["hour"], dw["minute"])]
        fixed_plan = (cfg.FIXED_GREEN_S, cfg.FIXED_GREEN_S)
        print(f"[{day}] {demand['n_vehicles']} véhicules ; simulation cycle fixe...")
        res = {}
        res["fixed"] = run_window(net_file, routes, run_dir / "tripinfo_fixed.xml", n,
                                  lambda i: fixed_plan, args.seed, args.gui)
        print(f"[{day}] simulation régulation IA...")
        res["ai"] = run_window(net_file, routes, run_dir / "tripinfo_ai.xml", n,
                               plans.__getitem__, args.seed, args.gui)
        for k in res:
            trips_all[k].append(res[k][0])
            queues_all[k] += res[k][1]
        add_summary(day, res["fixed"][0], res["fixed"][1], res["ai"][0], res["ai"][1])

        base = pd.DataFrame({
            "datetime": dw["datetime"], "traffic_flow": dw["traffic_flow"],
            "predicted_flow": np.round(pred, 1),
            "demand_total_vph": np.round(demand["demand_total_vph"], 1),
            "share_main": np.round(demand["share_main"], 3),
            "congestion_level": [congestion_level(p)[0] for p in pred]})
        parts = [base]
        for k in ("fixed", "ai"):
            parts.append(interval_metrics(*[res[k][0], res[k][1], res[k][2], n]).add_prefix(f"{k}_"))
        details.append(pd.concat(parts, axis=1))

    detail = pd.concat(details, ignore_index=True)
    num = detail.select_dtypes("number").columns
    detail[num] = detail[num].round(3)
    cat = lambda k: pd.concat(trips_all[k], ignore_index=True)
    add_summary("global", cat("fixed"), queues_all["fixed"], cat("ai"), queues_all["ai"])
    summary = pd.DataFrame(summary_rows)
    summary = pd.concat([summary[summary.scope == "global"], summary[summary.scope != "global"]])

    detail.to_csv(out_dir / "simulation.csv", index=False)
    summary.to_csv(out_dir / "simulation_summary.csv", index=False)

    g = summary[summary.scope == "global"].drop(columns="scope")
    print(f"\nPrédicteur : {predictor.name} | graine : {args.seed} | journées : "
          f"{', '.join(d for d, _ in windows)}")
    print(g.to_string(index=False))
    wait_gain = g.loc[g.indicator == "avg_wait_s", "gain_pct"].iloc[0]
    status = "atteint" if wait_gain >= cfg.GAIN_TARGET_PCT else "NON atteint"
    print(f"Objectif {cfg.GAIN_TARGET_PCT:.0f} % sur le temps d'attente : {status}")
    print(f"Fichiers écrits dans {out_dir}/ : simulation.csv, simulation_summary.csv")


if __name__ == "__main__":
    main()
