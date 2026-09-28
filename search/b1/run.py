#!/usr/bin/env python3
"""B1: the strengthening-search harness.

    python3 search/b1/run.py selfcheck --out DIR      # validate the machinery
    python3 search/b1/run.py tier1 --jobs 17 --out DIR  # all candidates, n <= 13
    python3 search/b1/run.py tier2 --jobs 17 --out DIR  # tier-1 survivors, n <= 16
    python3 search/b1/run.py all --jobs 17 --out DIR    # the three in order

Enumerates every triangulation of the sphere, and every triangulation of a
disc with a chordless boundary, up to the bound with plantri
(third_party/plantri, built here from its unmodified source). It tests every
candidate in candidates.py against each one. The bound is Gabriel's
decision, recorded on issue #9: tier 1 goes to 13 vertices, tier 2 to 16 for
the candidates that survive tier 1. Both are parameters (--tier1-max,
--tier2-max), so raising a bound is a rerun.

Outputs in DIR:
- report.txt: per candidate, the verdict, the triangulations tested per size,
  and for a killed candidate its smallest counterexample, in plantri's ascii
  code with the witness.
- summary.json: the same, machine-readable.
- timings.json: wall and CPU time per step. Timings are never part of
  report.txt, which reruns byte-identically.
Every file starts with a header naming the repository commit, the plantri
version and digest, the compiler, Python, host, and the command.

The enumeration is exhaustive, so there is no seed. The one random step, the
relabelling in selfcheck, uses the fixed seed SEED, which is recorded in the
output.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import platform
import random
import socket
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from candidates import CANDIDATES, dual_hamiltonian_cycle, hamiltonian_pairs, rejected  # noqa: E402
from canon import canonical  # noqa: E402
from colour import (count_tait_colourings, count_vertex_colourings, cycle_colourings,  # noqa: E402
                    extends, normalise)
from planar import Tri, check_structure, read_planar_code  # noqa: E402

PLANTRI_SRC = ROOT / "third_party" / "plantri" / "plantri.c"
SEED = 20260928

# OEIS A000109: triangulations of the sphere with n vertices.
A000109 = {4: 1, 5: 1, 6: 2, 7: 5, 8: 14, 9: 50, 10: 233, 11: 1249, 12: 7595,
           13: 49566, 14: 339722, 15: 2406841, 16: 17490241, 17: 129664753,
           18: 977526957}
# OEIS A342056: unrooted 3-connected triangulations of a disc with n vertices
# (plantri -P: chordless boundary of any length).
A342056 = {4: 1, 5: 2, 6: 7, 7: 27, 8: 132, 9: 773, 10: 5017, 11: 34861,
           12: 253676, 13: 1903584, 14: 14616442, 15: 114254053, 16: 906266345}


# ---------------------------------------------------------------------------
# plantri
# ---------------------------------------------------------------------------
def build_plantri(out: Path) -> Path:
    exe = out / "bin" / "plantri"
    exe.parent.mkdir(parents=True, exist_ok=True)
    src_sha = hashlib.sha256(PLANTRI_SRC.read_bytes()).hexdigest()
    stamp = exe.with_suffix(".sha256")
    if not exe.exists() or not stamp.exists() or stamp.read_text().strip() != src_sha:
        subprocess.run(["cc", "-o", str(exe), "-O4", str(PLANTRI_SRC)], check=True)
        stamp.write_text(src_sha + "\n")
    return exe


def plantri_stream(exe, n, disc=False, part=None, extra=()):
    args = [str(exe)] + (["-P"] if disc else []) + list(extra) + [str(n)]
    if part is not None:
        args.append(f"{part[0]}/{part[1]}")
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        yield from read_planar_code(p.stdout, disc=disc)
    finally:
        p.stdout.close()
        if p.wait() != 0:
            raise RuntimeError(f"plantri failed: {' '.join(args)}")


# ---------------------------------------------------------------------------
# header
# ---------------------------------------------------------------------------
def header(command):
    def git(*a):
        try:
            return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                                  text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return "?"
    dirty = git("status", "--porcelain", "--", "search/b1", "third_party/plantri")
    cc = subprocess.run(["cc", "--version"], capture_output=True, text=True).stdout.splitlines()
    return [
        "B1 strengthening-search harness (search/b1/run.py)",
        f"repository commit: {git('rev-parse', 'HEAD')}"
        + (" (with local changes under search/b1 or third_party/plantri)" if dirty else ""),
        f"plantri: 5.8, plantri.c sha256 {hashlib.sha256(PLANTRI_SRC.read_bytes()).hexdigest()}",
        f"compiler: {cc[0] if cc else '?'} (cc -O4)",
        f"python: {platform.python_version()} ({platform.python_implementation()})",
        f"host: {socket.gethostname()}",
        f"platform: {platform.platform()}",
        f"seed: {SEED} (selfcheck relabelling only; the enumeration is exhaustive)",
        f"command: {' '.join(command)}",
    ]


# ---------------------------------------------------------------------------
# the search
# ---------------------------------------------------------------------------
def _search_part(task):
    exe, domain, n, part, ids = task
    by_id = {c.id: c for c in CANDIDATES}
    tested = 0
    kills = {i: {"count": 0, "best": None} for i in ids}
    t0 = time.process_time()
    for t in plantri_stream(exe, n, disc=(domain == "disc"), part=part):
        check_structure(t)
        tested += 1
        for i in ids:
            w = by_id[i].test(t)
            if w is None:
                continue
            k = kills[i]
            k["count"] += 1
            code = canonical(t)
            if k["best"] is None or code < k["best"][0]:
                k["best"] = (code, t.ascii(),
                             [v + 1 for v in t.boundary] if t.is_disc else None, w)
    return domain, n, tested, kills, time.process_time() - t0


def search(exe, candidates, sizes, jobs, pool, log):
    """Run `candidates` over every size in `sizes` (ascending), dropping a
    candidate after the size at which it is first killed. Returns
    {id: result} and per-step timings."""
    alive = {c.id: c for c in candidates}
    results = {c.id: {"tested": {}, "killed_at": None} for c in candidates}
    timings = []
    for n in sizes:
        for domain in ("sphere", "disc"):
            ids = sorted(i for i, c in alive.items() if c.domain == domain)
            if not ids:
                continue
            mod = jobs if n >= 10 else 1
            tasks = [(exe, domain, n, (r, mod) if mod > 1 else None, ids) for r in range(mod)]
            w0 = time.time()
            parts = pool.map(_search_part, tasks)
            wall = time.time() - w0
            tested = sum(p[2] for p in parts)
            expect = (A000109 if domain == "sphere" else A342056)[n]
            if tested != expect:
                raise RuntimeError(f"{domain} n={n}: plantri gave {tested} graphs, OEIS says {expect}")
            cpu = sum(p[4] for p in parts)
            timings.append({"domain": domain, "n": n, "graphs": tested, "candidates": ids,
                            "wall_s": round(wall, 2), "cpu_s": round(cpu, 2)})
            for i in ids:
                results[i]["tested"][n] = tested
                count = sum(p[3][i]["count"] for p in parts)
                bests = [p[3][i]["best"] for p in parts if p[3][i]["best"] is not None]
                if count:
                    code, ascii_, boundary, witness = min(bests, key=lambda b: b[0])
                    results[i]["killed_at"] = {
                        "n": n, "counterexamples_at_n": count, "ascii": ascii_,
                        "boundary": boundary, "witness": witness}
                    del alive[i]
            log(f"{domain:6s} n={n:2d}: {tested:>10,d} graphs, {len(ids)} candidates, "
                f"{wall:7.1f} s wall, {cpu:8.1f} s CPU")
    return results, timings


def write_outputs(out: Path, name, head, results, candidates, bounds, timings, extra=None):
    lines = [f"# {h}" for h in head] + [""]
    summary = {"header": head, "bounds": bounds, "candidates": {}}
    for c in candidates:
        reason = rejected(c)
        entry = {"family": c.family, "domain": c.domain, "palette": c.palette,
                 "statement": c.statement, "expectation": c.expectation}
        lines.append(f"## {c.id} ({c.family}, {c.domain})")
        lines.append(f"statement: {c.statement}")
        lines.append(f"expectation: {c.expectation}")
        if reason:
            entry["verdict"] = "rejected"
            entry["reason"] = reason
            lines.append(f"VERDICT: rejected before running - {reason}")
        else:
            r = results.get(c.id)
            if r is None:
                entry["verdict"] = "not run in this step"
                lines.append("VERDICT: not run in this step")
            else:
                entry["tested"] = r["tested"]
                tested = ", ".join(f"n={n}: {m:,}" for n, m in sorted(r["tested"].items()))
                lines.append(f"tested: {tested}")
                if r["killed_at"]:
                    k = r["killed_at"]
                    entry["verdict"] = "killed"
                    entry["killed_at"] = k
                    lines.append(f"VERDICT: killed. Smallest counterexample has {k['n']} vertices "
                                 f"({k['counterexamples_at_n']:,} counterexamples of that size).")
                    lines.append(f"  counterexample (plantri ascii, rotations clockwise): {k['ascii']}")
                    if k["boundary"]:
                        lines.append(f"  boundary cycle (1-based): {k['boundary']}")
                    lines.append(f"  witness: {json.dumps(k['witness'], sort_keys=True)}")
                else:
                    top = max(r["tested"]) if r["tested"] else None
                    entry["verdict"] = f"not killed up to n={top}"
                    lines.append(f"VERDICT: not killed up to {top} vertices. This is a "
                                 "survivor, not a theorem.")
        summary["candidates"][c.id] = entry
        lines.append("")
    if extra:
        summary.update(extra)
    (out / f"{name}-report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / f"{name}-summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n",
                                              encoding="utf-8")
    (out / f"{name}-timings.json").write_text(json.dumps(timings, indent=1) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# selfcheck
# ---------------------------------------------------------------------------
def relabel(t: Tri, perm, mirror):
    rot = [None] * t.n
    for v in range(t.n):
        r = [perm[w] for w in t.rot[v]]
        rot[perm[v]] = list(reversed(r)) if mirror else r
    out = Tri(rot)
    if t.is_disc:
        b = [perm[v] for v in t.boundary]
        out.boundary = list(reversed(b)) if mirror else b
    return out


def count_dual_hamiltonian_cycles(t: Tri):
    """Hamiltonian cycles of the dual cubic graph, by exhaustive search from
    face 0. Each cycle is found once in each direction."""
    from colour import dual
    faces, adj, _ = dual(t)
    m = len(faces)
    nbr = [[g for g, _ in a] for a in adj]
    on = [False] * m
    on[0] = True
    count = 0

    def rec(v, depth):
        nonlocal count
        if depth == m:
            count += 0 in nbr[v]
            return
        for g in nbr[v]:
            if not on[g]:
                on[g] = True
                rec(g, depth + 1)
                on[g] = False

    rec(0, 1)
    return count // 2


def _brute_boundary_extensions(t: Tri):
    """Boundary colourings (normal form) that extend, by trying every
    assignment of 4 colours to every vertex. Independent of colour.extends."""
    edges = t.edges()
    out = set()
    for col in itertools.product(range(4), repeat=t.n):
        if all(col[a] != col[b] for a, b in edges):
            out.add(normalise([col[v] for v in t.boundary], range(len(t.boundary))))
    return out


def selfcheck(exe, out, log, sphere_max=11, disc_max=10):
    checks = []
    rng = random.Random(SEED)

    def record(name, ok, detail=""):
        checks.append({"check": name, "ok": ok, "detail": detail})
        log(f"{'ok  ' if ok else 'FAIL'} {name} {detail}")

    # counts against OEIS, and structure, for both domains
    for domain, table, top in (("sphere", A000109, sphere_max + 1), ("disc", A342056, disc_max + 1)):
        for n in range(4, top + 1):
            cnt = 0
            for t in plantri_stream(exe, n, disc=(domain == "disc")):
                check_structure(t)
                cnt += 1
            record(f"{domain} count n={n} matches OEIS", cnt == table[n], f"{cnt} vs {table[n]}")

    # disc sizes: the traced outer face has exactly the size asked for
    for n in range(4, disc_max + 1):
        total, bad = 0, 0
        for k in range(3, n):
            for t in plantri_stream(exe, n, disc=True, extra=(f"-P{k}",)):
                total += 1
                try:
                    check_structure(t, disc_size=k)
                except ValueError:
                    bad += 1
        record(f"disc n={n}: traced boundary = requested size, summed over sizes = OEIS",
               bad == 0 and total == A342056[n], f"{total} discs, {bad} wrong")

    # colourings two ways: vertex colourings == Tait colourings (up to
    # permutation), and never zero (that would be a counterexample to the 4CT,
    # or a bug that both sides share)
    for n in range(4, sphere_max + 1):
        bad = 0
        m = 0
        lo = hi = None
        for t in plantri_stream(exe, n):
            m += 1
            a, b = count_vertex_colourings(t), count_tait_colourings(t)
            if a != b or a == 0:
                bad += 1
            lo = a if lo is None else min(lo, a)
            hi = a if hi is None else max(hi, a)
        record(f"sphere n={n}: vertex colourings = Tait colourings, all positive",
               bad == 0, f"{m} graphs, {bad} bad, colourings per graph {lo}..{hi}")

    # dual Hamiltonicity two ways. Each Hamiltonian cycle H of the cubic dual
    # gives exactly one Tait colouring up to permutation (alternate two
    # colours along H, the third on the rest) in which one pair of classes
    # forms H. So the number of Hamiltonian cycles, counted by direct search,
    # equals the total number of Hamiltonian class pairs over all colourings.
    for n in range(4, sphere_max + 1):
        bad = 0
        total = 0
        for t in plantri_stream(exe, n):
            direct = count_dual_hamiltonian_cycles(t)
            via_tait = sum(k for _, k in hamiltonian_pairs(t))
            bad += direct != via_tait
            total += direct
            if (dual_hamiltonian_cycle(t) is not None) != (direct > 0):
                bad += 1
        record(f"sphere n={n}: dual Hamiltonian cycles by search = by Tait colourings",
               bad == 0, f"{bad} disagree, {total} Hamiltonian cycles in all")

    # canonical form: separates plantri's non-isomorphic outputs, and is
    # invariant under relabelling and reflection
    for domain, top in (("sphere", sphere_max), ("disc", disc_max)):
        for n in range(4, top + 1):
            codes, bad = set(), 0
            graphs = list(plantri_stream(exe, n, disc=(domain == "disc")))
            for t in graphs:
                c = canonical(t)
                codes.add(c)
                perm = list(range(t.n))
                rng.shuffle(perm)
                if canonical(relabel(t, perm, mirror=bool(rng.getrandbits(1)))) != c:
                    bad += 1
            record(f"{domain} n={n}: canonical codes distinct and invariant",
                   len(codes) == len(graphs) and bad == 0,
                   f"{len(codes)} codes for {len(graphs)} graphs, {bad} not invariant")

    # precolouring extension against brute force
    for n in range(4, min(disc_max, 8) + 1):
        bad = 0
        for t in plantri_stream(exe, n, disc=True):
            k = len(t.boundary)
            fast = {bc for bc in cycle_colourings(k, 4) if extends(t, dict(zip(t.boundary, bc)))}
            if fast != _brute_boundary_extensions(t):
                bad += 1
        record(f"disc n={n}: boundary extensions = brute force", bad == 0, f"{bad} disagree")

    ok = all(c["ok"] for c in checks)
    return ok, checks


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=["selfcheck", "tier1", "tier2", "all"])
    ap.add_argument("--out", default=str(ROOT / "search" / "b1" / "out"))
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 3))
    ap.add_argument("--tier1-max", type=int, default=13)
    ap.add_argument("--tier2-max", type=int, default=16)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    head = header(sys.argv)
    exe = build_plantri(out)
    logf = open(out / "log.txt", "a", encoding="utf-8")

    def log(msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    log(f"step {args.step}, jobs {args.jobs}, out {out}")
    status = 0
    if args.step in ("selfcheck", "all"):
        w0 = time.time()
        ok, checks = selfcheck(exe, out, log)
        (out / "selfcheck.json").write_text(json.dumps(
            {"header": head, "ok": ok, "checks": checks,
             "wall_s": round(time.time() - w0, 1)}, indent=1) + "\n", encoding="utf-8")
        if not ok:
            log("selfcheck FAILED; not running the search")
            return 1
    runnable = [c for c in CANDIDATES if rejected(c) is None]
    with Pool(args.jobs) as pool:
        if args.step in ("tier1", "all"):
            sizes = range(4, args.tier1_max + 1)
            res, tim = search(exe, runnable, sizes, args.jobs, pool, log)
            write_outputs(out, "tier1", head, res, CANDIDATES,
                          {"tier": 1, "sphere": [4, args.tier1_max], "disc": [4, args.tier1_max]},
                          tim)
        if args.step in ("tier2", "all"):
            t1 = json.loads((out / "tier1-summary.json").read_text(encoding="utf-8"))
            survivors = [c for c in runnable
                         if t1["candidates"][c.id]["verdict"].startswith("not killed")]
            log("tier 2 candidates: " + (", ".join(c.id for c in survivors) or "none"))
            sizes = range(args.tier1_max + 1, args.tier2_max + 1)
            res, tim = search(exe, survivors, sizes, args.jobs, pool, log)
            write_outputs(out, "tier2", head, res, CANDIDATES,
                          {"tier": 2, "sizes": [args.tier1_max + 1, args.tier2_max],
                           "candidates": [c.id for c in survivors]}, tim)
    log("done")
    return status


if __name__ == "__main__":
    sys.exit(main())
