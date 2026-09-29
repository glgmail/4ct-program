#!/usr/bin/env python3
"""D1 Phase 2, Implementation B (Mode T).  Entry point.

  python3 d1b.py all [--jobs N] [--out DIR] [--webs W1,...] [--git-commit C]
      controls (SPEC 9), then W1..W7 in B19 mode (SPEC 6.4, 7)
  python3 d1b.py controls [--out DIR]
  python3 d1b.py web W1 [--mode B19|STRICT-ALL|PARTIAL-ALL] [--jobs N] [--out DIR]
"""

import argparse
import hashlib
import json
import os
try:
    import resource
except ImportError:  # not on Windows
    resource = None
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import tait_colourings, hex_to_packed          # noqa: E402
from webs import get_web, TARGETS                         # noqa: E402
from sites import generate                                # noqa: E402
import ranks                                              # noqa: E402

A3_KEYS = ["degenerate_square_merge", "degenerate_triangle_merge", "extra_circle_theta",
           "extra_circle_other", "bridge_fail", "marker_loss_fail",
           "marker_component_vanished", "component_split", "unmarked_component_created",
           "no_eligible_face_fail", "boozer_degenerate_bigon", "boozer_degenerate_triangle",
           "boozer_degenerate_square"]
IMPL ="B (Mode T: transfer matrices), search/d1/implB"
N_E = {"W1": 6727, "W2": 5322, "W3": 4902, "W4": 6351, "W5": 7153, "W6": 6331,
       "W7": 5458}     # B19 Table 2
EXPECTED_N = {"W1": 11160, "W2": 27792, "W3": 45960, "W4": 47196, "W5": 40704,
              "W6": 53172, "W7": 101970}


def check_target(name, K):
    exp = TARGETS[name]
    assert K.V == exp["V"]
    sizes = {}
    for f in K.faces:
        sizes[len(f)] = sizes.get(len(f), 0) + 1
    assert sizes == exp["faces"], (name, sizes)
    f = K.faces[K.face_of[exp["outer"]]]
    assert f[0] == exp["outer"]
    assert [d // 3 for d in f] == exp["outer_vs"], (name, [d // 3 for d in f])


def maxrss_mb():
    if resource is None:
        return 0.0, 0.0
    a = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    b = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return a / 1024.0, b / 1024.0


def run_target(name, mode, outdir, jobs, git_commit, command, check=False,
               log=print, extra_remark42=False):
    t0 = time.time()
    K = get_web(name)
    outer = None
    if name in TARGETS:
        check_target(name, K)
        outer = TARGETS[name]["outer"]
    tait = tait_colourings(K)
    T = len(tait)
    if name in TARGETS:
        assert T == TARGETS[name]["tait"]

    def prog(done, tot):
        if done % 100 == 0 or done == tot:
            log("  [%s %s] sites %d/%d  %.1fs" % (name, mode, done, tot, time.time() - t0))
    sites, results, nodes, events = generate(K, mode, outer, jobs=jobs, check=check, progress=prog)
    t1 = time.time()
    d = os.path.join(outdir, name, mode)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "halffoams.jsonl")
    degs, vecs, kinds = [], [], []
    nby = {"zip": 0, "unzip": 0, "saddle": 0, "ih": 0}
    i = 0
    h = hashlib.sha256()
    with open(path, "w", newline="\n") as fh:
        for site, out in zip(sites, results):
            for chain, deg, row in out:
                i += 1
                assert len(row) == T
                line = json.dumps({"i": i, "site": list(site), "chain": chain,
                                   "deg": deg, "a": row}) + "\n"
                fh.write(line)
                h.update(line.encode("ascii"))
                degs.append(deg)
                vecs.append(hex_to_packed(row))
                kinds.append(site[0])
                nby[site[0]] += 1
    N = i
    sha = h.hexdigest()
    R = ranks.compute_all(degs, vecs, T)
    t2 = time.time()
    res = {
        "web": name, "mode": mode, "V": K.V, "Tait": T, "N": N,
        "N_by_move": nby,
        "ell": R["ell"], "ell_q": {str(k): v for k, v in sorted(R["ell_q"].items())},
        "r": R["r"], "r_q": {str(k): v for k, v in sorted(R["r_q"].items())},
        "beta_changes": R["beta_changes"], "N_ell_ours": R["N_ell"],
        "halffoams_sha256": sha, "command": command, "git_commit": git_commit,
        "implementation": IMPL,
    }
    with open(os.path.join(d, "result.json"), "w", newline="\n") as fh:
        fh.write(json.dumps(res, sort_keys=True, indent=1) + "\n")
    # sample-pair values for the later A/B comparison of SPEC 7.5 item 2
    if N:
        with open(os.path.join(d, "pairsample.tsv"), "w", newline="\n") as fh:
            for a, b, v in ranks.sample_pairs(degs, vecs):
                fh.write("%d\t%d\t%d\n" % (a, b, v))
    # Amendment 1, A3: degenerate events (whole generation, all sites)
    with open(os.path.join(d, "a3_events.json"), "w", newline="\n") as fh:
        allev = dict((k, 0) for k in A3_KEYS)
        allev.update(events)
        fh.write(json.dumps(allev, sort_keys=True, indent=1) + "\n")
    # Amendment 1, A2: ranks of (i) Unzip block alone, (ii) first N_e, (iii) full list
    a2 = None
    if mode == "B19" and name in N_E:
        nun = nby["unzip"]
        assert all(k == "unzip" for k in kinds[:nun]), "Unzip block is not a prefix"
        a2 = {}
        for label, n in (("i_unzip_block", nun), ("ii_first_N_e", N_E[name]), ("iii_full", N)):
            n = min(n, N)
            Rs = R if n == N else ranks.compute_all(degs[:n], vecs[:n], T)
            a2[label] = {"n": n, "ell": Rs["ell"],
                         "ell_q": {str(k): v for k, v in sorted(Rs["ell_q"].items())},
                         "r": Rs["r"],
                         "r_q": {str(k): v for k, v in sorted(Rs["r_q"].items())}}
        with open(os.path.join(d, "a2_subsets.json"), "w", newline="\n") as fh:
            fh.write(json.dumps(a2, sort_keys=True, indent=1) + "\n")
    extra = {}
    if extra_remark42:
        for kind in ("zip", "unzip", "saddle", "ih"):
            sel = [k for k in range(N) if kinds[k] == kind]
            extra[kind] = ranks.ell_only([degs[k] for k in sel], [vecs[k] for k in sel])
        with open(os.path.join(d, "remark42.json"), "w", newline="\n") as fh:
            fh.write(json.dumps({"ell_by_move_type_alone": extra}, sort_keys=True, indent=1) + "\n")
    t3 = time.time()
    rs, rc = maxrss_mb()
    timing = ("web %s mode %s: sites %d, GEN nodes %d, generation %.1fs, ranks %.1fs, "
              "total %.1fs, maxrss self %.0f MB, largest child %.0f MB, jobs %d\n"
              % (name, mode, len(sites), nodes, t1 - t0, t2 - t1, t3 - t0, rs, rc, jobs))
    with open(os.path.join(d, "timing.txt"), "w", newline="\n") as fh:
        fh.write(timing)
    log(timing.strip())
    return res, extra, events, a2


def fmt_q(q):
    parts = []
    for k in sorted(q, key=int):
        parts.append("%dq^%s" % (q[k], k))
    return " + ".join(parts) if parts else "0"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["all", "controls", "web"])
    ap.add_argument("web", nargs="?")
    ap.add_argument("--mode", default="B19", choices=["B19", "STRICT-ALL", "PARTIAL-ALL"])
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    ap.add_argument("--webs", default="W1,W2,W3,W4,W5,W6,W7")
    ap.add_argument("--git-commit", default="unrecorded")
    ap.add_argument("--no-check", action="store_true",
                    help="skip verifying that every derived colouring is a Tait colouring")
    a = ap.parse_args()
    command = "python3 d1b.py " + " ".join(sys.argv[1:])

    if a.cmd in ("all", "controls"):
        import controls
        ok = controls.run_all(os.path.join(a.out, "controls"))
        if not ok:
            print("CONTROLS FAILED; not running W1-W7")
            sys.exit(1)
    if a.cmd == "controls":
        return
    webs = [a.web] if a.cmd == "web" else a.webs.split(",")
    mode = a.mode if a.cmd == "web" else "B19"
    summary = []
    for w in webs:
        res, extra, events, a2 = run_target(w, mode, a.out, a.jobs, a.git_commit, command,
                                            check=not a.no_check,
                                            extra_remark42=(w == "W1" and mode == "B19"))
        line = "%s %s: N=%d (B19 Table 2: %s) Tait=%d ell=%d r=%d ell_q=%s r_q=%s" % (
            w, mode, res["N"], EXPECTED_N.get(w), res["Tait"], res["ell"], res["r"],
            fmt_q(res["ell_q"]), fmt_q(res["r_q"]))
        if extra:
            line += " remark4.2=%s" % json.dumps(extra, sort_keys=True)
        line += " A3=%s" % json.dumps(events, sort_keys=True)
        if a2:
            for k in sorted(a2):
                line += "\n    A2 %s: n=%d ell=%d r=%d ell_q=%s r_q=%s" % (
                    k, a2[k]["n"], a2[k]["ell"], a2[k]["r"], fmt_q(a2[k]["ell_q"]), fmt_q(a2[k]["r_q"]))
        print(line)
        summary.append(line)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
