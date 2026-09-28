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

    def write_stream(self, name, lines):
        """Like write, for an iterator of lines too large to hold: the
        payload goes to a temporary file first, then the header with its
        digest is written in front of it."""
        h = hashlib.sha256()
        tmp = os.path.join(self.dir, name + ".partial")
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            for ln in lines:
                b = ln + "\n"
                h.update(b.encode("utf-8"))
                fh.write(b)
        digest = h.hexdigest()
        with open(os.path.join(self.dir, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write("\n".join(self.head) + "\n")
            fh.write(f"# payload sha256: {digest}\n")
            with open(tmp, "r", encoding="utf-8") as src:
                while True:
                    block = src.read(1 << 20)
                    if not block:
                        break
                    fh.write(block)
        os.remove(tmp)
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


def _mp_context():
    """forkserver where available (Linux), else the platform default. Workers
    rebuild their state in _init_worker, so nothing depends on fork."""
    import multiprocessing as mp
    try:
        return mp.get_context("forkserver")
    except ValueError:
        return mp.get_context()


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
    n_checked = len(arrays)
    t_setup = None
    counts = {"reasons": {}, "survivors": 0}
    pool = None

    def results():
        nonlocal pool
        if args.jobs > 1:
            import multiprocessing as mp
            chunks = ((d, arrays[i:i + 200]) for i in range(0, len(arrays), 200))
            pool = _mp_context().Pool(
                args.jobs, initializer=_init_worker,
                initargs=(args.literal, args.order))
            for part in pool.imap(_work, chunks, chunksize=1):  # ordered
                yield from part
            pool.close()
            pool.join()
        else:
            yield from cartwheel.enum_possible_bad_wheels(
                d, _W["tables"], _W["index"], arrays)

    def lines():
        for degs, why in results():
            k = why or "survives"
            counts["reasons"][k] = counts["reasons"].get(k, 0) + 1
            if why is None:
                counts["survivors"] += 1
            yield f"{d} " + " ".join(map(str, degs)) + f" {k}"

    if args.jobs <= 1:
        _init_worker(args.literal, args.order)
        t_setup = t()
    tag = f"wheels-{d}" + ("-sample" if args.sample else "") + variant(args)
    try:
        digest = out.write_stream(tag + ".txt", lines())
    finally:
        if pool is not None:
            pool.terminate()
    del arrays
    elapsed = t()
    reasons = counts["reasons"]
    nsurv = counts["survivors"]
    result = {
        "centre_degree": d,
        "wheels_up_to_rotation": total_arrays,
        "wheels_checked": n_checked,
        "survivors": nsurv,
        "pruned": {k: v for k, v in sorted(reasons.items())},
        "file": tag + ".txt",
        "payload_sha256": digest,
        "literal": args.literal,
        "sample": args.sample,
    }
    if not args.sample:
        result["target"] = TARGETS[f"wheels_{d}"]
        result["matches_target"] = nsurv == TARGETS[f"wheels_{d}"]
    work = elapsed - (t_setup or 0)
    timing = {"total_s": elapsed, "jobs": args.jobs, "wheels": n_checked,
              "setup_s": t_setup,
              "per_wheel_ms_wall": round(1000 * work / max(1, n_checked), 3),
              "peak_rss_mb_main_process": peak_rss_mb()}
    out.record(tag, result, timing)
    print(f"{tag}: {n_checked} of {total_arrays} wheels checked, {nsurv} survive"
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
    """Time enumBadCartwheels (A.9.21, a draft) on a deterministic sample of
    C^d_0: the survivors of A.9.7 among a strided pool of --pool wheels
    (all wheels if --pool 0), then a strided --count of those. For the
    projection only; not a result."""
    from nl4ct import badcartwheels
    d = args.degree
    t = Timer()
    _init_worker(args.literal, args.order)
    tables, index = _W["tables"], _W["index"]
    arrays = cartwheel.enum_wheel_degrees(d)
    n_all = len(arrays)
    if args.pool:
        arrays = arrays[::max(1, len(arrays) // args.pool)][:args.pool]
    res = cartwheel.enum_possible_bad_wheels(d, tables, index, arrays)
    c0 = [degs for degs, why in res if why is None]
    t_c0 = t()
    print(f"pool {len(arrays)} of {n_all} wheels, {len(c0)} in C0", flush=True)
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
    out.record(f"sample-bad-{d}", {"wheels": n_all, "pool": len(arrays),
                                   "C0_in_pool": len(c0), "sampled": len(rows),
                                   "rows": rows},
               {"c0_s": t_c0, "sample_s": round(tot, 3),
                "mean_s_per_wheel": round(tot / max(1, len(rows)), 3),
                "peak_rss_mb": peak_rss_mb()})


# ---------------------------------------------------------------------------
# the full bad-cartwheel enumeration (A.9.20 / A.9.21)
# ---------------------------------------------------------------------------
BAD_TARGETS = {7: 9366, 8: 728}


def read_c0(out_dir, d):
    """C^d_0: the survivors listed in wheels-<d>.txt, in file order."""
    path = os.path.join(out_dir, f"wheels-{d}.txt")
    c0 = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            if ln.startswith("#"):
                continue
            parts = ln.split()
            if parts[-1] == "survives":
                c0.append(tuple(int(x) for x in parts[1:-1]))
    return c0


def _bad_work(task):
    import traceback
    from nl4ct import badcartwheels
    tid, d, degs = task
    t1 = time.perf_counter()
    stats = {}
    rec = {"tid": tid, "d": d, "wheel": list(degs)}
    try:
        cw0 = cartwheel.generate_cartwheel(d, degs)
        bad, failures = badcartwheels.enum_bad_cartwheels(
            cw0, _W["tables"], _W["index"], stats)
        rec["bad"] = [[cw.pc.lo, cw.pc.hi] for cw in bad]
        rec["failures"] = [[str(a), b, [list(c[0]), list(c[1])]] for a, b, c in failures]
    except Exception:
        rec["bad"] = []
        rec["failures"] = [["exception", traceback.format_exc(), None]]
    rec["pairs"] = stats.get("pairs")
    rec["C_i"] = stats.get("C_i sizes")
    rec["seconds"] = round(time.perf_counter() - t1, 3)
    rec["rss_mb"] = peak_rss_mb()
    return rec


def run_bad(out, args):
    """enumAllBadCartwheels over every C^d_0 wheel, d = 7..11, in parallel.

    Progress goes to bad-progress.jsonl (one line per finished wheel, with
    its time), so an interrupted run resumes where it stopped. When every
    wheel is done, the payloads call.jsonl and bad-wheels.jsonl are written
    in a fixed order."""
    t = Timer()
    degrees = [int(x) for x in args.degrees.split(",")]
    tasks = []
    for d in degrees:
        for degs in read_c0(out.dir, d):
            tasks.append((len(tasks), d, degs))
    prog = os.path.join(out.dir, "bad-progress.jsonl")
    done = {}
    if os.path.exists(prog):
        with open(prog, encoding="utf-8") as fh:
            for ln in fh:
                if ln.strip():
                    r = json.loads(ln)
                    done[r["tid"]] = r
    for tid, d, degs in tasks:  # the task list must not have changed
        if tid in done:
            assert done[tid]["d"] == d and tuple(done[tid]["wheel"]) == degs
    todo = [x for x in tasks if x[0] not in done]
    print(f"bad: {len(tasks)} wheels, {len(done)} done before, {len(todo)} to do",
          flush=True)
    if todo:
        with open(prog, "a", encoding="utf-8", newline="\n") as fh:
            if args.jobs > 1:
                with _mp_context().Pool(args.jobs, initializer=_init_worker,
                                        initargs=(args.literal, args.order)) as pool:
                    for n, rec in enumerate(pool.imap_unordered(_bad_work, todo, chunksize=1)):
                        fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
                        fh.flush()
                        done[rec["tid"]] = rec
                        if n % 200 == 0:
                            print(f"  {len(done)}/{len(tasks)} at {t():.0f} s", flush=True)
            else:
                _init_worker(args.literal, args.order)
                for rec in map(_bad_work, todo):
                    fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
                    fh.flush()
                    done[rec["tid"]] = rec
    recs = [done[tid] for tid, _, _ in tasks]
    call_lines = []
    wheel_lines = []
    per_d = {}
    for r in recs:
        for lo, hi in r["bad"]:
            call_lines.append(json.dumps({"d": r["d"], "wheel": r["wheel"], "lo": lo,
                                          "hi": hi}, separators=(",", ":")))
        wheel_lines.append(json.dumps({"d": r["d"], "wheel": r["wheel"],
                                       "bad": len(r["bad"]), "pairs": r["pairs"],
                                       "C_i": r["C_i"], "failures": r["failures"]},
                                      separators=(",", ":")))
        s = per_d.setdefault(str(r["d"]), {"C0": 0, "bad_cartwheels": 0,
                                           "pairs_before_dedup": 0,
                                           "wheels_with_failures": 0,
                                           "failures": 0, "cpu_s": 0.0,
                                           "max_wheel_s": 0.0})
        s["C0"] += 1
        s["bad_cartwheels"] += len(r["bad"])
        s["pairs_before_dedup"] += r["pairs"] or 0
        s["wheels_with_failures"] += 1 if r["failures"] else 0
        s["failures"] += len(r["failures"])
        s["cpu_s"] += r["seconds"]
        s["max_wheel_s"] = max(s["max_wheel_s"], r["seconds"])
    d_call = out.write("call.jsonl", call_lines)
    d_wheels = out.write("bad-wheels.jsonl", wheel_lines)
    result = {"degrees": degrees, "file_call": "call.jsonl", "payload_sha256_call": d_call,
              "file_per_wheel": "bad-wheels.jsonl",
              "payload_sha256_per_wheel": d_wheels, "per_degree": {},
              "all_failures": [dict(d=r["d"], wheel=r["wheel"], failures=r["failures"])
                               for r in recs if r["failures"]][:200]}
    timing = {"wall_s": t(), "jobs": args.jobs, "per_degree": {}}
    for k, s in per_d.items():
        res = {x: s[x] for x in ("C0", "bad_cartwheels", "pairs_before_dedup",
                                 "wheels_with_failures", "failures")}
        if int(k) in BAD_TARGETS:
            res["target"] = BAD_TARGETS[int(k)]
            res["matches_target"] = s["bad_cartwheels"] == BAD_TARGETS[int(k)]
        result["per_degree"][k] = res
        timing["per_degree"][k] = {"cpu_s": round(s["cpu_s"], 1),
                                   "max_wheel_s": s["max_wheel_s"]}
    timing["max_worker_rss_mb"] = max((r.get("rss_mb") or 0) for r in recs) if recs else None
    out.record("bad", result, timing)
    for k, v in result["per_degree"].items():
        print(f"bad d={k}: {v}", flush=True)
    print(f"call.jsonl payload {d_call[:16]}; bad-wheels.jsonl payload {d_wheels[:16]}; "
          f"{t():.0f} s", flush=True)


# ---------------------------------------------------------------------------
# A.10 (Lemmas A.4-A.6) on samples of roots
# ---------------------------------------------------------------------------
def load_call(out_dir):
    from nl4ct.pseudo import PC as _PC
    cws = []
    with open(os.path.join(out_dir, "call.jsonl"), encoding="utf-8") as fh:
        for ln in fh:
            if ln.startswith("#"):
                continue
            r = json.loads(ln)
            cw = cartwheel.generate_cartwheel(r["d"], tuple(r["wheel"]))
            p = cw.pc
            assert len(r["lo"]) == p.nv
            cws.append(cw.with_pc(_PC(p.nv, r["lo"], r["hi"], p.head, p.rev,
                                      p.succ, p.pred)))
    return cws


def _init_a10(out_dir):
    from nl4ct import cartcombine
    ds, ds_index = load_index(False)
    specs = inputs.read_special(SPECIAL)
    tpc = specs["T73"][0]
    t73 = inputs.Conf(tpc, inputs.maximum_degree_dart(tpc), "T73", -1, False)
    xpc, _, xc = specs["X"]
    _W["ctx"] = cartcombine.Context(load_call(out_dir), ds_index,
                                    blocking.ConfIndex(ds + [t73]),
                                    blocking.ConfIndex([t73]), xpc, xc)


class _RootTimeout(Exception):
    pass


def _a10_work(task):
    import signal
    import traceback
    from nl4ct import cartcombine
    check, n, compare, cap = task  # compare: True/"both", False/"with", "without"
    out = {"check": check, "root": n}

    def one(prefilter):
        stats = {}

        def alarm(*_):
            raise _RootTimeout()
        old = signal.signal(signal.SIGALRM, alarm) if hasattr(signal, "SIGALRM") else None
        if old is not None:
            signal.alarm(cap)
        t1 = time.perf_counter()
        try:
            asserts, sig = cartcombine.run_root(_W["ctx"], check, n, prefilter, stats)
            r = {"seconds": round(time.perf_counter() - t1, 3), "stats": stats,
                 "assertions": len(asserts), "results": [list(a) for a in asserts],
                 "failed": [a for a in asserts if not a[1]], "signature": sig}
        except _RootTimeout:
            r = {"seconds": None, "timeout_s": cap, "stats": stats}
        except Exception:
            r = {"seconds": None, "exception": traceback.format_exc(), "stats": stats}
        finally:
            if old is not None:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)
        return r

    if compare != "without":
        out["prefilter"] = one(True)
    if compare in (True, "both", "without"):
        out["no_prefilter"] = one(False)
    out["rss_mb"] = peak_rss_mb()
    return out


def run_a10_sample(out, args):
    from nl4ct import cartcombine
    t = Timer()
    _init_a10(out.dir)
    ctx = _W["ctx"]
    t_init = t()
    sets = {"A.4": len(ctx.c9), "A.5": len(ctx.c8), "A.6": len(ctx.c7)}
    tasks = []
    nroots = {}
    for check in args.checks.split(","):
        rs = cartcombine.roots(ctx, check)
        nroots[check] = len(rs)
        step = max(1, len(rs) // args.count) if rs else 1
        for n in rs[::step][:args.count]:
            tasks.append((check, n, args.compare, args.cap))
    print(f"a10-sample: sets {sets}, roots {nroots}, {len(tasks)} sampled, "
          f"init {t_init:.0f} s", flush=True)
    rows = []
    if args.jobs > 1:
        with _mp_context().Pool(args.jobs, initializer=_init_a10,
                                initargs=(out.dir,)) as pool:
            for r in pool.imap_unordered(_a10_work, tasks, chunksize=1):
                rows.append(r)
                print(json.dumps(r)[:300], flush=True)
    else:
        for task in tasks:
            rows.append(_a10_work(task))
            print(json.dumps(rows[-1])[:300], flush=True)
    rows.sort(key=lambda r: (r["check"], r["root"]))
    summary = {"sets_after_deleteDegreeFromKto9": sets, "roots": nroots,
               "sampled": len(rows), "compare": args.compare, "cap_s": args.cap,
               "per_check": {}}
    for check in nroots:
        rr = [r for r in rows if r["check"] == check]
        done = [r["prefilter"]["seconds"] for r in rr if r["prefilter"]["seconds"] is not None]
        timeouts = sum(1 for r in rr if r["prefilter"].get("timeout_s"))
        excs = sum(1 for r in rr if r["prefilter"].get("exception"))
        failed = sum(len(r["prefilter"].get("failed", [])) for r in rr)
        s = {"sampled": len(rr), "finished": len(done), "timeouts": timeouts,
             "exceptions": excs, "failed_assertions": failed}
        if done:
            mean = sum(done) / len(done)
            s.update({"mean_s": round(mean, 3), "max_s": max(done),
                      "median_s": sorted(done)[len(done) // 2],
                      "projected_cpu_h": round(mean * nroots[check] / 3600, 2)})
        if args.compare:
            both = [r for r in rr if r["prefilter"].get("signature")
                    and r["no_prefilter"].get("signature")]
            s["compared"] = len(both)
            s["identical"] = sum(
                1 for r in both
                if r["prefilter"]["signature"] == r["no_prefilter"]["signature"]
                and r["prefilter"]["assertions"] == r["no_prefilter"]["assertions"]
                and r["prefilter"]["failed"] == r["no_prefilter"]["failed"])
            nd = [r["no_prefilter"]["seconds"] for r in both]
            pd = [r["prefilter"]["seconds"] for r in both]
            if nd:
                s["mean_s_without_prefilter"] = round(sum(nd) / len(nd), 3)
                s["mean_s_with_prefilter_same_roots"] = round(sum(pd) / len(pd), 3)
        summary["per_check"][check] = s
    tag = "a10-sample" + ("-compare" if args.compare else "")
    summary["rows"] = rows
    out.record(tag, summary, {"wall_s": t(), "init_s": t_init, "jobs": args.jobs})
    for check, s in summary["per_check"].items():
        print(check, s, flush=True)


A10_CHECKS = ("A.4", "A.5", "A.6")


def _read_jsonl(path):
    out = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                if ln.strip() and not ln.startswith("#"):
                    out.append(json.loads(ln))
    return out


def run_a10(out, args):
    """Lemmas A.4-A.6 in full: every root of A.10.4, A.10.9 and A.10.10,
    with the prefilter. Progress goes to a10-progress.jsonl (resumable);
    the payload a10-roots.jsonl has one line per root, in (check, root)
    order, without timings."""
    from nl4ct import cartcombine
    t = Timer()
    _init_a10(out.dir)
    ctx = _W["ctx"]
    tasks = []
    nroots = {}
    for check in A10_CHECKS:
        rs = cartcombine.roots(ctx, check)
        nroots[check] = len(rs)
        tasks.extend((check, n, "with", 0) for n in rs)
    prog = os.path.join(out.dir, "a10-progress.jsonl")
    done = {(r["check"], r["root"]): r for r in _read_jsonl(prog)}
    todo = [x for x in tasks if (x[0], x[1]) not in done]
    print(f"a10: roots {nroots}, {len(done)} done before, {len(todo)} to do",
          flush=True)
    if todo:
        with open(prog, "a", encoding="utf-8", newline="\n") as fh:
            def record(rec):
                fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
                fh.flush()
                done[(rec["check"], rec["root"])] = rec
            if args.jobs > 1:
                with _mp_context().Pool(args.jobs, initializer=_init_a10,
                                        initargs=(out.dir,)) as pool:
                    for k, rec in enumerate(pool.imap_unordered(_a10_work, todo,
                                                                chunksize=1)):
                        record(rec)
                        if k % 100 == 0:
                            print(f"  {len(done)}/{len(tasks)} at {t():.0f} s", flush=True)
            else:
                for task in todo:
                    record(_a10_work(task))
    lines = []
    per = {c: {"roots": nroots[c], "assertions": 0, "roots_passed": 0,
               "roots_failed": [], "exceptions": [], "timeouts": [],
               "cpu_s": 0.0, "max_root_s": 0.0} for c in A10_CHECKS}
    for check, n, _, _ in tasks:
        r = done[(check, n)]
        p = r["prefilter"]
        s = per[check]
        entry = {"check": check, "root": n,
                 "call_index": ctx.call_index[check][n],
                 "results": p.get("results"), "failed": p.get("failed"),
                 "exception": p.get("exception"), "signature": p.get("signature")}
        lines.append(json.dumps(entry, separators=(",", ":")))
        if p.get("exception"):
            s["exceptions"].append(n)
        elif p.get("timeout_s"):
            s["timeouts"].append(n)
        else:
            s["assertions"] += p["assertions"]
            if p["failed"]:
                s["roots_failed"].append({"root": n, "failed": p["failed"]})
            else:
                s["roots_passed"] += 1
            s["cpu_s"] += p["seconds"]
            s["max_root_s"] = max(s["max_root_s"], p["seconds"])
    digest = out.write("a10-roots.jsonl", lines)
    result = {"file": "a10-roots.jsonl", "payload_sha256": digest, "per_check": {}}
    timing = {"wall_s": t(), "jobs": args.jobs, "per_check": {}}
    for c, s in per.items():
        verdict = ("no roots" if s["roots"] == 0 else
                   "pass" if s["roots_passed"] == s["roots"] else "FAIL")
        result["per_check"][c] = {
            "lemma": {"A.4": "Lemma 8.3", "A.5": "Lemma 8.5", "A.6": "Lemma 8.6"}[c],
            "roots": s["roots"], "roots_passed": s["roots_passed"],
            "assertions_checked": s["assertions"],
            "roots_failed": s["roots_failed"], "exceptions": s["exceptions"],
            "timeouts": s["timeouts"], "verdict": verdict}
        timing["per_check"][c] = {"cpu_s": round(s["cpu_s"], 1),
                                  "max_root_s": s["max_root_s"]}
    timing["max_worker_rss_mb"] = max((r.get("rss_mb") or 0) for r in done.values())
    out.record("a10", result, timing)
    for c, v in result["per_check"].items():
        print(f"{c} ({v['lemma']}): {v['verdict']}: {v['roots_passed']}/{v['roots']} "
              f"roots pass, {v['assertions_checked']} assertions, "
              f"{len(v['roots_failed'])} failed, {len(v['exceptions'])} exceptions, "
              f"{len(v['timeouts'])} timeouts", flush=True)
    print(f"a10-roots.jsonl payload {digest[:16]}; {t():.0f} s", flush=True)


def run_a10_verify(out, args):
    """Rerun roots of the full A.10 run without the prefilter and require
    identical results. Roots: the --heaviest slowest A.4 roots of the full
    run, plus --count strided roots per check, skipping roots already
    compared by a10-sample --compare."""
    t = Timer()
    full = {(r["check"], r["root"]): r
            for r in _read_jsonl(os.path.join(out.dir, "a10-progress.jsonl"))}
    before = set()
    for key in ("a10-sample-compare",):
        for r in out.summary.get(key, {}).get("rows", []):
            before.add((r["check"], r["root"]))
    pick = []
    a4 = sorted((k for k in full if k[0] == "A.4" and k not in before),
                key=lambda k: -(full[k]["prefilter"].get("seconds") or 0))
    pick.extend(a4[:args.heaviest])
    for check in A10_CHECKS:
        rs = sorted(k for k in full if k[0] == check and k not in before
                    and k not in pick)
        step = max(1, len(rs) // max(1, args.count))
        pick.extend(rs[::step][:args.count])
    tasks = [(c, n, "without", 0) for c, n in pick]
    print(f"a10-verify: {len(tasks)} roots ({args.heaviest} heaviest A.4)", flush=True)
    rows = []
    with _mp_context().Pool(args.jobs, initializer=_init_a10,
                            initargs=(out.dir,)) as pool:
        for rec in pool.imap_unordered(_a10_work, tasks, chunksize=1):
            f = full[(rec["check"], rec["root"])]["prefilter"]
            g = rec["no_prefilter"]
            same = (f.get("signature") == g.get("signature")
                    and f.get("results") == g.get("results")
                    and f.get("failed") == g.get("failed"))
            rows.append({"check": rec["check"], "root": rec["root"],
                         "identical": same,
                         "seconds_with": f.get("seconds"),
                         "seconds_without": g.get("seconds"),
                         "exception": g.get("exception")})
            print(json.dumps(rows[-1]), flush=True)
    rows.sort(key=lambda r: (r["check"], r["root"]))
    res = {"roots": len(rows), "identical": sum(r["identical"] for r in rows),
           "heaviest_a4": args.heaviest, "rows": rows,
           "per_check": {c: {"roots": sum(1 for r in rows if r["check"] == c),
                             "identical": sum(1 for r in rows
                                              if r["check"] == c and r["identical"])}
                         for c in A10_CHECKS}}
    out.record("a10-verify", res, {"wall_s": t(), "jobs": args.jobs,
                                   "cpu_s_without": round(sum(r["seconds_without"] or 0
                                                              for r in rows), 1)})
    print(f"a10-verify: {res['identical']}/{res['roots']} identical; {res['per_check']}",
          flush=True)


def run_all(out, args):
    """The whole pipeline, one step after another, into one --out directory."""
    t = Timer()
    run_combination(out, args, False)
    run_combination(out, args, True)
    run_special(out, args)
    for d in (7, 8, 9, 10, 11):
        args.degree = d
        run_wheels(out, args)
    run_bad(out, args)
    run_a10(out, args)
    print(f"all: {t():.0f} s", flush=True)


def main(argv=None):
    argv = sys.argv if argv is None else argv
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["a1", "a2", "wheels", "special", "phase1",
                                     "sample-wheels", "sample-bad", "bad",
                                     "a10-sample", "a10", "a10-verify", "all"])
    ap.add_argument("--degree", type=int, default=7)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--pool", type=int, default=0)
    ap.add_argument("--degrees", default="7,8,9,10,11")
    ap.add_argument("--checks", default="A.4,A.5,A.6")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--cap", type=int, default=1800)
    ap.add_argument("--heaviest", type=int, default=20)
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
    if args.what == "bad":
        run_bad(out, args)
    if args.what == "a10-sample":
        run_a10_sample(out, args)
    if args.what == "a10":
        run_a10(out, args)
    if args.what == "a10-verify":
        run_a10_verify(out, args)
    if args.what == "all":
        run_all(out, args)


if __name__ == "__main__":
    main()
