"""Construit le réseau SUMO : une route principale à sens unique (2 voies) qui
traverse un carrefour à feux (N_JUNCTIONS dans config.py, 1 par défaut), avec
une rue latérale à double sens à chaque carrefour. Feux à 2 phases (axe
principal, rues latérales), tout droit.

                   N1
                    |
    M0 -----------> J1 -----------> M2        (sens unique, 2 voies)
                    |
                   S1

    python -m regulation.network
"""
import subprocess
from pathlib import Path

import sumolib

from . import config as cfg

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "sumo_scenario"
TLS_IDS = [f"J{k}" for k in range(1, cfg.N_JUNCTIONS + 1)]
MAIN_EDGES = [f"A{k}" for k in range(cfg.N_JUNCTIONS + 1)]      # A0 : M0 -> J1 ... A3 : J3 -> M4


def side_in(j):
    """Rues latérales du carrefour j (1..N) : (entrée nord, entrée sud)."""
    return f"N{j}_J{j}", f"S{j}_J{j}"


def incoming_edges():
    """Tronçons qui arrivent à un feu (pour mesurer les files d'attente)."""
    edges = MAIN_EDGES[:-1]
    for j in range(1, cfg.N_JUNCTIONS + 1):
        edges += list(side_in(j))
    return edges


def routes():
    """Itinéraires : l'axe principal, et la traversée de chaque rue latérale."""
    r = {"main": MAIN_EDGES}
    for j in range(1, cfg.N_JUNCTIONS + 1):
        r[f"N{j}"] = [f"N{j}_J{j}", f"J{j}_S{j}"]
        r[f"S{j}"] = [f"S{j}_J{j}", f"J{j}_N{j}"]
    return r


def _run_netconvert(args):
    cmd = [sumolib.checkBinary("netconvert")] + [str(a) for a in args]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"netconvert a échoué :\n{res.stdout}\n{res.stderr}")


def _phase_states(links_axis):
    """links_axis : liste (index_lien, 'main' | 'side'). Retourne les états des phases."""
    n = max(i for i, _ in links_axis) + 1

    def state(green_axis, char):
        s = ["r"] * n
        for i, ax in links_axis:
            if ax == green_axis:
                s[i] = char
        return "".join(s)

    return {
        "g_main": state("main", "G"), "y_main": state("main", "y"),
        "g_side": state("side", "G"), "y_side": state("side", "y"),
        "red": "r" * n,
    }


def build(scenario_dir=SCENARIO_DIR):
    scenario_dir = Path(scenario_dir)
    scenario_dir.mkdir(parents=True, exist_ok=True)
    L, S, nj = cfg.SPACING_M, cfg.SIDE_LENGTH_M, cfg.N_JUNCTIONS
    speed = f"{cfg.SPEED_LIMIT_MS:.3f}"
    nod, edg, con = ["<nodes>"], ["<edges>"], ["<connections>"]

    # axe principal : M0 -> J1 -> ... -> Jn -> M(n+1), sens unique
    nod.append('  <node id="M0" x="0" y="0"/>')
    for k in range(1, nj + 1):
        nod.append(f'  <node id="J{k}" x="{k * L:.0f}" y="0" type="traffic_light"/>')
    nod.append(f'  <node id="M{nj + 1}" x="{(nj + 1) * L:.0f}" y="0"/>')
    chain = ["M0"] + [f"J{k}" for k in range(1, nj + 1)] + [f"M{nj + 1}"]
    for k in range(nj + 1):
        edg.append(f'  <edge id="A{k}" from="{chain[k]}" to="{chain[k + 1]}" '
                   f'numLanes="{cfg.LANES_MAIN}" speed="{speed}"/>')
    for k in range(1, nj + 1):
        for lane in range(cfg.LANES_MAIN):
            con.append(f'  <connection from="A{k - 1}" to="A{k}" fromLane="{lane}" toLane="{lane}"/>')

    # rues latérales (double sens, 1 voie par sens), traversée tout droit
    for j in range(1, nj + 1):
        for tag, sign in (("N", 1), ("S", -1)):
            nod.append(f'  <node id="{tag}{j}" x="{j * L:.0f}" y="{sign * S:.0f}"/>')
            edg.append(f'  <edge id="{tag}{j}_J{j}" from="{tag}{j}" to="J{j}" '
                       f'numLanes="{cfg.LANES_SIDE}" speed="{speed}"/>')
            edg.append(f'  <edge id="J{j}_{tag}{j}" from="J{j}" to="{tag}{j}" '
                       f'numLanes="{cfg.LANES_SIDE}" speed="{speed}"/>')
        con.append(f'  <connection from="N{j}_J{j}" to="J{j}_S{j}"/>')
        con.append(f'  <connection from="S{j}_J{j}" to="J{j}_N{j}"/>')
    for block in (nod, edg, con):
        block.append("</" + block[0][1:-1] + ">")
    (scenario_dir / "c.nod.xml").write_text("\n".join(nod), encoding="utf-8")
    (scenario_dir / "c.edg.xml").write_text("\n".join(edg), encoding="utf-8")
    (scenario_dir / "c.con.xml").write_text("\n".join(con), encoding="utf-8")

    base = ["-n", scenario_dir / "c.nod.xml", "-e", scenario_dir / "c.edg.xml",
            "-x", scenario_dir / "c.con.xml", "--no-turnarounds", "true"]
    tmp_net = scenario_dir / "tmp.net.xml"
    _run_netconvert(base + ["-o", tmp_net])

    # Association lien de feu <-> axe, lue dans le réseau généré ; programme
    # statique par défaut = cycle fixe (le contrôleur Python le remplace ensuite).
    net = sumolib.net.readNet(str(tmp_net), withPrograms=True)
    tll = ["<tlLogics>"]
    for tls in TLS_IDS:
        links = []
        for idx, conns in net.getTLS(tls).getLinks().items():
            from_edge = conns[0][0].getEdge().getID()
            links.append((idx, "main" if from_edge.startswith("A") else "side"))
        st = _phase_states(links)
        gm, gs = cfg.FIXED_MAIN_GREEN_S, cfg.FIXED_SIDE_GREEN_S
        phases = [(gm, st["g_main"]), (cfg.YELLOW_S, st["y_main"]), (cfg.ALL_RED_S, st["red"]),
                  (gs, st["g_side"]), (cfg.YELLOW_S, st["y_side"]), (cfg.ALL_RED_S, st["red"])]
        tll.append(f'  <tlLogic id="{tls}" type="static" programID="0" offset="0">')
        tll += [f'    <phase duration="{d}" state="{s}"/>' for d, s in phases]
        tll.append("  </tlLogic>")
    tll.append("</tlLogics>")
    (scenario_dir / "c.tll.xml").write_text("\n".join(tll), encoding="utf-8")

    net_file = scenario_dir / "c.net.xml"
    _run_netconvert(base + ["--tllogic-files", scenario_dir / "c.tll.xml", "-o", net_file])
    tmp_net.unlink()
    return net_file


if __name__ == "__main__":
    print("Réseau créé :", build())
