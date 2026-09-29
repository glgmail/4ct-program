#!/usr/bin/env python3
"""Implementation A (Mode G) of SPEC search/d1/SPEC.md -- one command:

    python3 run_all.py                 # controls, N table (all modes), W1..W7 in B19 mode
    python3 run_all.py --controls      # controls only
    python3 run_all.py --web W3        # one web (B19 mode); controls must pass first
    python3 run_all.py --jobs 4        # webs in parallel subprocesses

Outputs go to out/ next to this file (see README.md).
"""

import argparse
import gzip
import hashlib
import io
import json
import os
import resource
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from d1a import web as W                       # noqa: E402
from d1a import webdata                        # noqa: E402
from d1a.gen import generate, new_events       # noqa: E402
from d1a.analysis import TargetWeb, analyse, sample_pairs, check_pairs   # noqa: E402
from d1a.foam import STATS                     # noqa: E402
from d1a.records import STATS as RSTATS       # noqa: E402
from d1a.web import STATS as WSTATS           # noqa: E402

OUT = os.path.join(HERE, "out")
WEBS = ["W1", "W2", "W3", "W4", "W5", "W6", "W7"]
MODES = ["B19", "STRICT-ALL", "PARTIAL-ALL"]
IMPL = "A (Mode G, facet-seam foams, direct colouring enumeration)"


def git_commit():
    # No git commands are run (task rule); the caller may pass the commit in.
    return os.environ.get("D1_GIT_COMMIT", "unknown")


def peak_mb():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(r / 1024.0, 1)   # Linux: KiB


def write_json(path, obj):
    with open(path, "w", newline="\n") as fh:
        fh.write(json.dumps(obj, sort_keys=True, indent=2) + "\n")


def run_controls():
    from d1a.controls import run_controls as rc
    t0 = time.time()
    res = rc()
    allok = all(ok for _, ok, _ in res)
    os.makedirs(OUT, exist_ok=True)
    lines = []
    for name, ok, det in res:
        lines.append("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- " + det) if det else ""))
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(OUT, "controls.txt"), "w", newline="\n") as fh:
        fh.write(txt)
    sys.stdout.write(txt)
    sys.stdout.write("controls: %s in %.1f s\n" % ("ALL PASS" if allok else "FAILURES", time.time() - t0))
    return allok


N_E = {"W1": 6727, "W2": 5322, "W3": 4902, "W4": 6351, "W5": 7153, "W6": 6331, "W7": 5458}
# B19 Table 2 column N_e (the prefix B19 evaluated), used for Amendment 1 A2 (ii)

N_EXPECTED = {   # SPEC 6.4: (B19, STRICT-ALL, PARTIAL-ALL) and B19 by move (zip, unzip, saddle, ih)
    "W1": ((11160, 11880, 11880), (1080, 3960, 3960, 2160)),
    "W2": ((27792, 30600, 30600), (2808, 9864, 10224, 4896)),
    "W3": ((45960, 48864, 48864), (4188, 16872, 16800, 8100)),
    "W4": ((47196, 50040, 50040), (4248, 17496, 16956, 8496)),
    "W5": ((40704, 43992, 43992), (3744, 14784, 14832, 7344)),
    "W6": ((53172, 41664, 58044), (4704, 19404, 19068, 9996)),
    "W7": ((101970, 116730, 117486), (9036, 37296, 39564, 16074)),
}
STRICT_BY_MOVE = {
    "W1": (1080, 4320, 4320, 2160), "W2": (2808, 11088, 11808, 4896),
    "W3": (4188, 18336, 18240, 8100), "W4": (4248, 19008, 18288, 8496),
    "W5": (3744, 16416, 16488, 7344), "W6": (3696, 13776, 17304, 6888),
    "W7": (10188, 43488, 45828, 17226),
}


def n_table():
    """Count-only generation in all three modes (checks SPEC 6.4 tables)."""
    rows = {}
    for name in WEBS:
        K = W.load(name)
        outer = webdata.EXPECT[name][3]
        for mode in MODES:
            ev = new_events()
            cnt = generate(K, outer, mode, False, lambda *a: None, ev)
            rows["%s %s" % (name, mode)] = {"N": sum(cnt.values()), "N_by_move": cnt,
                                            "events": ev}
    write_json(os.path.join(OUT, "n_table.json"), rows)
    ok = True
    for name in WEBS:
        tot, byb = N_EXPECTED[name]
        for mode, e in zip(MODES, tot):
            ok = ok and rows["%s %s" % (name, mode)]["N"] == e
        mv = lambda r: tuple(r["N_by_move"][k] for k in ("zip", "unzip", "saddle", "ih"))
        ok = ok and mv(rows["%s B19" % name]) == byb
        ok = ok and mv(rows["%s STRICT-ALL" % name]) == STRICT_BY_MOVE[name]
    msg = "%s  SPEC 6.4 N table (count-only generation, all three modes, W1-W7)\n" % (
        "PASS" if ok else "FAIL")
    with open(os.path.join(OUT, "controls.txt"), "a", newline="\n") as fh:
        fh.write(msg)
    sys.stdout.write(msg)
    if not ok:
        sys.exit("N table mismatch")
    return rows


def run_web(name, mode="B19"):
    t0 = time.time()
    K = W.load(name)
    K.validate()
    outer = webdata.EXPECT[name][3]
    tw = TargetWeb(K)
    assert tw.T == webdata.EXPECT[name][2]
    # pass 1: count only, to fix N and the SPEC 7.5 sample indices
    ev0 = new_events()
    cnt0 = generate(K, outer, mode, False, lambda *a: None, ev0)
    N0 = sum(cnt0.values())
    pairs = sample_pairs(N0)
    needed = set()
    for i, j in pairs:
        needed.add(i)
        needed.add(j)
    # pass 2: build foams, a-vectors
    odir = os.path.join(OUT, name, mode)
    os.makedirs(odir, exist_ok=True)
    buf = io.BytesIO()
    sha = hashlib.sha256()
    foams, avs, degs, moves = {}, {}, {}, {}
    state = {"n": 0}

    def cb(site, H, d, chain):
        state["n"] += 1
        i = state["n"]
        tw.check_degree(H, d)
        a = tw.avec(H)
        avs[i] = a
        degs[i] = d
        moves[i] = site[0]
        if i in needed:
            foams[i] = H
        line = json.dumps({"i": i, "site": list(site), "chain": list(chain),
                           "deg": d, "a": tw.hexa(a)}) + "\n"
        b = line.encode("ascii")
        sha.update(b)
        buf.write(b)

    for d in (WSTATS, RSTATS, STATS):
        for k in d:
            d[k] = 0
    t1 = time.time()
    ev1 = new_events()
    counts = generate(K, outer, mode, True, cb, ev1)
    t_gen = time.time() - t1
    N = state["n"]
    assert N == N0 and counts == cnt0 and ev1 == ev0
    raw = buf.getvalue()
    with open(os.path.join(odir, "halffoams.jsonl.gz"), "wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh, mtime=0, compresslevel=9) as gz:
            gz.write(raw)
    if os.environ.get("D1_KEEP_JSONL"):
        with open(os.path.join(odir, "halffoams.jsonl"), "wb") as fh:
            fh.write(raw)
    del buf, raw
    t1 = time.time()
    res = analyse((avs[i], degs[i]) for i in range(1, N + 1))
    t_rank = time.time() - t1
    assert res["ell"] <= res["r"] <= tw.T
    t1 = time.time()
    checked = check_pairs(tw, foams, avs, degs, pairs)
    t_pairs = time.time() - t1
    # per-move-type l (B19 Remark 4.2 for W1; reported for every web)
    per_move = {}
    for mv in ("zip", "unzip", "saddle", "ih"):
        r2 = analyse((avs[i], degs[i]) for i in range(1, N + 1) if moves[i] == mv)
        per_move[mv] = {"ell": r2["ell"], "ell_q": {str(k): v for k, v in r2["ell_q"].items()}}
    # Amendment 1, A2: (i) the Unzip block alone, (ii) the first N_e
    # half-foams in A1 order, (iii) the full list (= the top-level keys).
    def summary(idx):
        r3 = analyse((avs[i], degs[i]) for i in idx)
        return {"N": len(idx), "ell": r3["ell"],
                "ell_q": {str(k): v for k, v in r3["ell_q"].items()},
                "r": r3["r"], "r_q": {str(k): v for k, v in r3["r_q"].items()}}
    unz = [i for i in range(1, N + 1) if moves[i] == "unzip"]
    if mode == "B19":
        assert unz == list(range(1, len(unz) + 1)), "A1 order: Unzip block first"
    Ne = N_E[name]
    a2 = {"unzip_block": summary(unz),
          "prefix_N_e": dict(summary(list(range(1, min(Ne, N) + 1))), N_e=Ne)}
    result = {
        "web": name, "mode": mode, "V": K.V, "Tait": tw.T, "N": N,
        "site_order": "Amendment 1 A1: Unzip, Zip, Saddle, IH" if mode == "B19"
                      else "SPEC 6.2: Zip, Unzip, Saddle, IH",
        "A2_unzip_block": a2["unzip_block"],
        "A2_prefix_N_e": a2["prefix_N_e"],
        "A3_events": ev1,
        "N_by_move": counts,
        "ell": res["ell"],
        "ell_q": {str(k): v for k, v in res["ell_q"].items()},
        "r": res["r"],
        "r_q": {str(k): v for k, v in res["r_q"].items()},
        "beta_changes": res["beta_changes"],
        "N_ell": res["N_ell"],
        "halffoams_sha256": sha.hexdigest(),
        "command": "python3 run_all.py --web %s --mode %s" % (name, mode),
        "git_commit": git_commit(),
        "implementation": "A",
    }
    write_json(os.path.join(odir, "result.json"), result)
    extra = {
        "web": name, "mode": mode,
        "ell_by_move_type": per_move,
        "direct_pairs_checked": checked,
        "avec_branching_events": STATS["branch"],
        "avec_max_replications": STATS["maxrep"],
        "records_built": RSTATS["records"],
        "degenerate_merged_nominal_facets": RSTATS["merged_nominal_facets"],
        "rebuilds": WSTATS["rebuilds"],
        "circles_created_by_joins": WSTATS["join_circles"],
        "rebuilds_creating_several_circles": WSTATS["multi_circle_rebuilds"],
        "halffoams_jsonl_gz_sha256": hashlib.sha256(
            open(os.path.join(odir, "halffoams.jsonl.gz"), "rb").read()).hexdigest(),
    }
    write_json(os.path.join(odir, "extra.json"), extra)
    timing = {"web": name, "mode": mode, "seconds_total": round(time.time() - t0, 1),
              "seconds_generate_and_avec": round(t_gen, 1), "seconds_ranks": round(t_rank, 1),
              "seconds_direct_pairs": round(t_pairs, 1), "peak_rss_mb": peak_mb()}
    write_json(os.path.join(odir, "timing.json"), timing)
    print(json.dumps({"web": name, "N": N, "ell": res["ell"], "r": res["r"],
                      "ell_q": result["ell_q"], "r_q": result["r_q"],
                      "A2": a2, "A3": {k: v for k, v in ev1.items() if v},
                      "timing": timing}), flush=True)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--web")
    ap.add_argument("--mode", default="B19")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--skip-controls", action="store_true",
                    help="internal: used by the parallel driver after controls passed")
    args = ap.parse_args()
    if args.mode != "B19":
        # Only B19 mode is run for W1-W7 at this stage (task scope).
        sys.exit("only --mode B19 is enabled for W1-W7 at this stage")
    if not args.skip_controls:
        if not run_controls():
            sys.exit("controls failed; not running W1-W7")
    if args.controls:
        return
    if args.web:
        run_web(args.web, args.mode)
        return
    n_table()
    procs = []
    pending = list(WEBS)
    running = []
    while pending or running:
        while pending and len(running) < args.jobs:
            w = pending.pop(0)
            p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--web", w,
                                  "--mode", args.mode, "--skip-controls"])
            running.append((w, p))
        w, p = running.pop(0)
        if p.wait() != 0:
            sys.exit("web %s failed" % w)


if __name__ == "__main__":
    main()
