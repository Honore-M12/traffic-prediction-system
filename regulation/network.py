"""Construit le carrefour SUMO : 4 branches, 2 voies par sens, tout droit,
feux à 2 phases (axe principal N-S, axe secondaire E-O).

    python -m regulation.network
"""
import subprocess
from pathlib import Path

import sumolib

from . import config as cfg

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "sumo_scenario"
TLS_ID = "C"
MAIN_APPROACHES = ("N", "S")
SEC_APPROACHES = ("E", "W")
APPROACHES = MAIN_APPROACHES + SEC_APPROACHES
_COORD = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}
_OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


def incoming_edges():
    return [f"{a}_C" for a in APPROACHES]


def _run_netconvert(args):
    cmd = [sumolib.checkBinary("netconvert")] + [str(a) for a in args]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"netconvert a échoué :\n{res.stdout}\n{res.stderr}")


def _phase_states(links_axis):
    """links_axis : liste (index_lien, 'main' | 'sec'). Retourne les 6 états."""
    n = max(i for i, _ in links_axis) + 1

    def state(green_axis, char):
        s = ["r"] * n
        for i, ax in links_axis:
            if ax == green_axis:
                s[i] = char
        return "".join(s)

    return {
        "g_main": state("main", "G"), "y_main": state("main", "y"),
        "g_sec": state("sec", "G"), "y_sec": state("sec", "y"),
        "red": "r" * n,
    }


def build(scenario_dir=SCENARIO_DIR):
    scenario_dir = Path(scenario_dir)
    scenario_dir.mkdir(parents=True, exist_ok=True)
    L = cfg.APPROACH_LENGTH_M
    nod, edg, con = ["<nodes>", '  <node id="C" x="0" y="0" type="traffic_light"/>'], \
        ["<edges>"], ["<connections>"]
    for a, (dx, dy) in _COORD.items():
        nod.append(f'  <node id="{a}" x="{dx * L:.0f}" y="{dy * L:.0f}"/>')
        for src, dst in ((a, "C"), ("C", a)):
            edg.append(f'  <edge id="{src}_{dst}" from="{src}" to="{dst}" '
                       f'numLanes="{cfg.LANES_PER_APPROACH}" speed="{cfg.SPEED_LIMIT_MS:.3f}"/>')
        for lane in range(cfg.LANES_PER_APPROACH):
            con.append(f'  <connection from="{a}_C" to="C_{_OPPOSITE[a]}" '
                       f'fromLane="{lane}" toLane="{lane}"/>')
    for block in (nod, edg, con):
        block.append("</" + block[0][1:-1] + ">")
    (scenario_dir / "c.nod.xml").write_text("\n".join(nod), encoding="utf-8")
    (scenario_dir / "c.edg.xml").write_text("\n".join(edg), encoding="utf-8")
    (scenario_dir / "c.con.xml").write_text("\n".join(con), encoding="utf-8")

    base = ["-n", scenario_dir / "c.nod.xml", "-e", scenario_dir / "c.edg.xml",
            "-x", scenario_dir / "c.con.xml", "--no-turnarounds", "true"]
    tmp_net = scenario_dir / "tmp.net.xml"
    _run_netconvert(base + ["-o", tmp_net])

    # Association lien de feu <-> axe, lue dans le réseau généré
    net = sumolib.net.readNet(str(tmp_net), withPrograms=True)
    links = []
    for idx, conns in net.getTLS(TLS_ID).getLinks().items():
        from_edge = conns[0][0].getEdge().getID()
        links.append((idx, "main" if from_edge[0] in MAIN_APPROACHES else "sec"))
    st = _phase_states(links)

    g = cfg.FIXED_GREEN_S
    phases = [(g, st["g_main"]), (cfg.YELLOW_S, st["y_main"]), (cfg.ALL_RED_S, st["red"]),
              (g, st["g_sec"]), (cfg.YELLOW_S, st["y_sec"]), (cfg.ALL_RED_S, st["red"])]
    tll = ['<tlLogics>', f'  <tlLogic id="{TLS_ID}" type="static" programID="0" offset="0">']
    tll += [f'    <phase duration="{d}" state="{s}"/>' for d, s in phases]
    tll += ["  </tlLogic>", "</tlLogics>"]
    (scenario_dir / "c.tll.xml").write_text("\n".join(tll), encoding="utf-8")

    net_file = scenario_dir / "c.net.xml"
    _run_netconvert(base + ["--tllogic-files", scenario_dir / "c.tll.xml", "-o", net_file])
    tmp_net.unlink()
    return net_file


if __name__ == "__main__":
    print("Réseau créé :", build())
