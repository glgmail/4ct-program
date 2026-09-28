#!/usr/bin/env python3
"""Task F2: an independent implementation of the computer checks of
arXiv:2603.24880v2, written from the paper's appendix A.

    python3 checks/f2/run.py a1                 # Lemma A.1: R*
    python3 checks/f2/run.py a2                 # Lemma A.2: R*-D
    python3 checks/f2/run.py wheels --degree 7  # A.9.7 enumPossibleBadWheels
    python3 checks/f2/run.py special            # checks of our X and T73
    python3 checks/f2/run.py phase1             # all of the above
    python3 checks/f2/run.py sample-wheels --degree 11 --count 2000
    python3 checks/f2/run.py sample-bad --degree 7 --count 20

Options: --out DIR (default checks/f2/out), --jobs N (wheels), --literal
(no speed-ups: a literal transcription, for cross-checking), --order
reversed (add the rules in reverse order in A.8.2).

Every output file starts with lines beginning "# " that record the paper,
the repository commit, Python, host and platform. The rest of the file (the
payload) depends only on the input data and the options; its sha256 is
printed and recorded in summary.json. Timings go to timings.json, never
into the payloads. Standard library only; no randomness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time

try:
    import resource
except ImportError:  # Windows
    resource = None

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

from nl4ct import blocking, cartwheel, combine, inputs, special  # noqa: E402
from nl4ct.pseudo import INF, NIL  # noqa: E402

PAPER = "arXiv:2603.24880v2 (7 May 2026)"
RULES_DIR = os.path.join(REPO, "data", "near-linear-4ct", "discharging-rules", "R")
CONF_DIR = os.path.join(REPO, "data", "near-linear-4ct", "reducible-configurations", "D")
SPECIAL = os.path.join(HERE, "data", "special-configurations.json")
TARGETS = {
    "a1_size": 1832, "a1_max_charge": 8,
    "a2_size": 671, "a2_max_charge": 5,
    "wheels_7": 5439, "wheels_8": 6790, "wheels_9": 3285, "wheels_10": 626,
    "wheels_11": 8,
}


# ---------------------------------------------------------------------------
# provenance and output
# ---------------------------------------------------------------------------
def git(*args):
    try:
        return subprocess.run(["git", "-C", REPO, *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def header(argv):
    dirty = git("status", "--porcelain", "--untracked-files=no", "--", "checks/f2")
    return [
        "# F2 independent checks (checks/f2/run.py)",
        f"# paper: {PAPER}",
        f"# repository commit: {git('rev-parse', 'HEAD')}"
        + (" (checks/f2 modified)" if dirty else ""),
        f"# python: {sys.version.split()[0]} ({platform.python_implementation()})",
        f"# host: {platform.node()}",
        f"# platform: {platform.platform()}",
        f"# command: {' '.join(argv)}",
    ]


class Output:
    def __init__(self, directory, argv):
        self.dir = directory
        os.makedirs(directory, exist_ok=True)
        self.head = header(argv)
        self.summary_path = os.path.join(directory, "summary.json")
        self.timings_path = os.path.join(directory, "timings.json")
        self.summary = self._load(self.summary_path)
        self.timings = self._load(self.timings_path)

    @staticmethod
    def _load(p):
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        return {}

    def write(self, name, lines):
        payload = "".join(ln + "\n" for ln in lines)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        with open(os.path.join(self.dir, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write("\n".join(self.head) + "\n")
            fh.write(f"# payload sha256: {digest}\n")
            fh.write(payload)
        return digest

    def _dump(self, path, data):
        body = {k: v for k, v in data.items() if k != "header"}
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"header": self.head, **body}, fh, indent=1, sort_keys=True)
            fh.write("\n")

    def record(self, key, value, timing=None):
        self.summary[key] = value
        self._dump(self.summary_path, self.summary)
        if timing is not None:
            self.timings[key] = timing
            self._dump(self.timings_path, self.timings)


def peak_rss_mb():
    if resource is None:
        return None
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(r / 1024.0, 1)


class Timer:
    def __init__(self):
        self.t0 = time.perf_counter()

    def __call__(self):
        return round(time.perf_counter() - self.t0, 3)


# ---------------------------------------------------------------------------
# canonical form of a (combined) rule, for order-independence checks
# ---------------------------------------------------------------------------
def canonical(rule, names):
    """Relabel darts and vertices in breadth-first order from the rule's dart
    (following rev, succ, pred), so that two combined rules get the same
    form exactly when an orientation-preserving isomorphism maps one onto
    the other, dart onto dart, keeping degree ranges and the set of rules."""
    pc = rule.pc
    dnew = {rule.dart: 0}
    order = [rule.dart]
    vnew = {}
    vorder = []
    k = 0
    while k < len(order):
        e = order[k]
        k += 1
        h = pc.head[e]
        if h not in vnew:
            vnew[h] = len(vorder)
            vorder.append(h)
        for f in (pc.rev[e], pc.succ[e], pc.pred[e]):
            if f != NIL and f not in dnew:
                dnew[f] = len(order)
                order.append(f)
    assert len(order) == len(pc.head) and len(vorder) == pc.nv

    def m(x):
        return dnew[x] if x != NIL else -1

    rules = [names[i] for i in range(len(names)) if (rule.mask >> i) & 1]
    return {
        "charge": rule.charge,
        "rules": rules,
        "lo": [pc.lo[v] for v in vorder],
        "hi": [pc.hi[v] if pc.hi[v] != INF else None for v in vorder],
        "head": [vnew[pc.head[e]] for e in order],
        "rev": [m(pc.rev[e]) for e in order],
        "succ": [m(pc.succ[e]) for e in order],
        "pred": [m(pc.pred[e]) for e in order],
    }


def rule_lines(combos, names):
    forms = [canonical(c, names) for c in combos]
    return sorted(json.dumps(f, separators=(",", ":"), sort_keys=True) for f in forms)


# ---------------------------------------------------------------------------
# the checks
# ---------------------------------------------------------------------------
def load_rules():
    return inputs.read_rules(RULES_DIR)


def load_index(literal):
    ds = inputs.read_ds(CONF_DIR)
    return ds, (blocking.LiteralConfs(ds) if literal else blocking.ConfIndex(ds))


def rule_order(rules, how):
    idx = list(range(len(rules)))
    return idx[::-1] if how == "reversed" else idx


def variant(args):
    return (("-" + args.order) if args.order != "given" else "") + \
        ("-literal" if args.literal else "")


def run_combination(out, args, with_d):
    tag = "a2" if with_d else "a1"
    t = Timer()
    rules = load_rules()
    names = [r.name for r in rules]
    info = {"rules": len(rules)}
    index = None
    if with_d:
        ds, index = load_index(args.literal)
        info["Ds"] = len(ds)
        info["Ds_entries_from_cut_vertex_extensions"] = sum(1 for c in ds if c.cut >= 0)
    t_load = t()
    alone = [r.name for i, r in enumerate(rules)
             if len(combine.add_rule_to_combination(combine.neutral_rule(), r,
                                                    1 << i, None)) != 1]
    combos, stats = combine.combine_rules(rules, index, rule_order(rules, args.order))
    t_comb = round(t() - t_load, 3)
    charges = [c.charge for c in combos]
    mx = max(charges)
    hist = {}
    for c in charges:
        hist[c] = hist.get(c, 0) + 1
    lines = rule_lines(combos, names)
    key = tag + variant(args)
    fname = f"{key}-{'rstar-d' if with_d else 'rstar'}.jsonl"
    digest = out.write(fname, lines)
    at_max = [json.loads(ln) for ln in lines if json.loads(ln)["charge"] == mx]
    tsize, tmax = TARGETS[f"{tag}_size"], TARGETS[f"{tag}_max_charge"]
    res = {
        "size_including_R0": len(combos),
        "max_charge": mx,
        "combinations_at_max_charge": len(at_max),
        "rules_in_combinations_at_max": [r["rules"] for r in at_max],
        "charge_histogram": {str(k): hist[k] for k in sorted(hist)},
        "rules_not_giving_one_combination_alone": alone,
        "file": fname,
        "payload_sha256": digest,
        "order": args.order,
        "literal": args.literal,
        "target_size": tsize,
        "target_max_charge": tmax,
        "matches_target": len(combos) == tsize and mx == tmax,
        **info,
        **stats,
    }
    out.record(key, res, {"load_s": t_load, "combine_s": t_comb,
                          "total_s": t(), "peak_rss_mb": peak_rss_mb()})
    print(f"{key}: size {len(combos)} (target {tsize}), max charge {mx} "
          f"(target {tmax}), {len(at_max)} at max; {t():.1f} s; "
          f"payload {digest[:16]}", flush=True)
    return combos, rules, index


# worker state (also used in the main process when --jobs 1)
_W = {}


def _init_worker(literal, order):
    rules = load_rules()
    ds, index = load_index(literal)
    combos, _ = combine.combine_rules(rules, index, rule_order(rules, order))
    _W["tables"] = cartwheel.RuleTables(rules, combos, literal)
    _W["index"] = index


def _work(chunk):
    d, arrays = chunk
    return cartwheel.enum_possible_bad_wheels(d, _W["tables"], _W["index"], arrays)


def run_wheels(out, args):
    d = args.degree
    t = Timer()
    arrays = cartwheel.enum_wheel_degrees(d)
    total_arrays = len(arrays)
    if args.sample:
        step = max(1, len(arrays) // args.sample)
        arrays = arrays[::step][:args.sample]
    t_setup = None
    if args.jobs > 1:
        import concurrent.futures as cf
        chunks = [(d, arrays[i:i + 100]) for i in range(0, len(arrays), 100)]
        with cf.ProcessPoolExecutor(args.jobs, initializer=_init_worker,
                                    initargs=(args.literal, args.order)) as ex:
            res = [r for part in ex.map(_work, chunks) for r in part]
    else:
        _init_worker(args.literal, args.order)
        t_setup = t()
        res = cartwheel.enum_possible_bad_wheels(d, _W["tables"], _W["index"], arrays)
    elapsed = t()
    survivors = [degs for degs, why in res if why is None]
    reasons = {}
    for _, why in res:
        k = why or "survives"
        reasons[k] = reasons.get(k, 0) + 1
    tag = f"wheels-{d}" + ("-sample" if args.sample else "") + variant(args)
    lines = [f"{d} " + " ".join(map(str, degs)) + f" {why or 'survives'}"
             for degs, why in res]
    digest = out.write(tag + ".txt", lines)
    result = {
        "centre_degree": d,
        "wheels_up_to_rotation": total_arrays,
        "wheels_checked": len(res),
        "survivors": len(survivors),
        "pruned": {k: v for k, v in sorted(reasons.items())},
        "file": tag + ".txt",
        "payload_sha256": digest,
        "literal": args.literal,
        "sample": args.sample,
    }
    if not args.sample:
        result["target"] = TARGETS[f"wheels_{d}"]
        result["matches_target"] = len(survivors) == TARGETS[f"wheels_{d}"]
    work = elapsed - (t_setup or 0)
    timing = {"total_s": elapsed, "jobs": args.jobs, "wheels": len(res),
              "setup_s": t_setup,
              "per_wheel_ms": round(1000 * work / max(1, len(res)), 3),
              "peak_rss_mb_main_process": peak_rss_mb()}
    out.record(tag, result, timing)
    print(f"{tag}: {len(res)} of {total_arrays} wheels checked, {len(survivors)} survive"
          + (f" (target {TARGETS[f'wheels_{d}']})" if not args.sample else "")
          + f"; {reasons}; {elapsed:.1f} s; payload {digest[:16]}", flush=True)


def run_special(out, args):
    t = Timer()
    specs = inputs.read_special(SPECIAL)
    ds, index = load_index(args.literal)
    lines = []
    allok = True
    for name, (pc, names, centre) in specs.items():
        checks = special.check_special(name, pc, names, centre,
                                       index if name in ("X", "Xw") else None)
        for desc, ok, detail in checks:
            allok = allok and bool(ok)
            lines.append(f"{name}\t{'ok' if ok else 'FAIL'}\t{desc}\t"
                         f"{json.dumps(detail)}")
    digest = out.write("special.txt", lines)
    out.record("special", {"all_ok": allok, "file": "special.txt",
                           "payload_sha256": digest}, {"total_s": t()})
    for ln in lines:
        print(ln)


def run_sample_bad(out, args):
    """Time enumBadCartwheels (A.9.21) on a deterministic sample of C^d_0.
    For the projection only; not a result."""
    from nl4ct import badcartwheels
    d = args.degree
    t = Timer()
    _init_worker(args.literal, args.order)
    tables, index = _W["tables"], _W["index"]
    arrays = cartwheel.enum_wheel_degrees(d)
    res = cartwheel.enum_possible_bad_wheels(d, tables, index, arrays)
    c0 = [degs for degs, why in res if why is None]
    t_c0 = t()
    step = max(1, len(c0) // args.count)
    sample = c0[::step][:args.count]
    rows = []
    for degs in sample:
        t1 = time.perf_counter()
        stats = {}
        cw0 = cartwheel.generate_cartwheel(d, degs)
        bad, failures = badcartwheels.enum_bad_cartwheels(cw0, tables, index, stats)
        dt = time.perf_counter() - t1
        rows.append({"degrees": list(degs), "seconds": round(dt, 3), "bad": len(bad),
                     "C_i": stats.get("C_i sizes"), "failures": len(failures)})
        print(rows[-1], flush=True)
    tot = sum(r["seconds"] for r in rows)
    out.record(f"sample-bad-{d}", {"C0": len(c0), "sampled": len(rows), "rows": rows},
               {"c0_s": t_c0, "sample_s": round(tot, 3),
                "mean_s_per_wheel": round(tot / max(1, len(rows)), 3),
                "peak_rss_mb": peak_rss_mb()})


def main(argv=None):
    argv = sys.argv if argv is None else argv
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["a1", "a2", "wheels", "special", "phase1",
                                     "sample-wheels", "sample-bad"])
    ap.add_argument("--degree", type=int, default=7)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--literal", action="store_true")
    ap.add_argument("--order", choices=["given", "reversed"], default="given")
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    args = ap.parse_args(argv[1:])
    args.sample = None
    out = Output(args.out, ["checks/f2/run.py", *argv[1:]])
    if args.what in ("a1", "phase1"):
        run_combination(out, args, False)
    if args.what in ("a2", "phase1"):
        run_combination(out, args, True)
    if args.what in ("special", "phase1"):
        run_special(out, args)
    if args.what in ("wheels", "phase1"):
        run_wheels(out, args)
    if args.what == "sample-wheels":
        args.sample = args.count
        run_wheels(out, args)
    if args.what == "sample-bad":
        run_sample_bad(out, args)


if __name__ == "__main__":
    main()
