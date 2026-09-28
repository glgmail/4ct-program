#!/usr/bin/env python3
"""Compare the outputs of F1 (upstream C++) and F2 (our independent Python)
object by object, not just by count.

    python3 checks/f1_vs_f2/compare.py F1_DIR F2_DIR F2_REPO RULE_DIR

F1_DIR   the WORK directory of a checks/f1/reproduce.sh run, or a copy of
         its combined_rules/ and wheels/
F2_DIR   the F2 output directory (a1-rstar.jsonl, a2-rstar-d.jsonl,
         wheels-<d>.txt, call.jsonl)
F2_REPO  a checkout of F2, whose checks/f2/nl4ct rebuilds cartwheels from
         (d, wheel) exactly as F2 does (A.9.6 generateCartwheel)
RULE_DIR data/near-linear-4ct/discharging-rules/R, to name the rules that
         F1's combination flags refer to

Both sides are reduced to one common form: for every vertex its degree
range (infinity as None) and its neighbours in clockwise order, with the
outer gap marked. Each object then gets a canonical code by breadth-first
numbering from a root dart, walking every rotation clockwise from the dart
it was entered by:

- a combined rule is rooted at its dart s->t (its identity includes s and
  t), and its code also carries the charge and the set of original rules;
- a cartwheel is rooted at its centre, minimised over the d darts into
  the centre.

Equal codes mean an orientation-preserving isomorphism that respects the
root and the degree ranges. The two sides must give the same multiset of
codes. If they do not, the comparison is repeated with F2 mirrored, to
tell a convention mismatch from a real difference.

This script is neither implementation. It reads F1's intermediate files,
whose formats are the C++'s own (upstream FORMAT.md), and it rebuilds F2's
cartwheels with F2's generate_cartwheel. It was written after F2 was
complete, by the session that ran F1, and F2's author never saw it.
"""
from __future__ import annotations

import collections
import json
import os
import sys
from pathlib import Path

GAP = -1


# ---------------------------------------------------------------------------
# F1 files (formats of near-linear-4ct/computer-checks, FORMAT.md)
# ---------------------------------------------------------------------------
def read_f1_structure(lines, n):
    """n vertex lines 'i lo hi a1 ... ak' (1-based, 0 = infinity, -1 = gap)."""
    rot, lab = {}, {}
    for line in lines[:n]:
        nums = [int(x) for x in line.split()]
        v, lo, hi, nb = nums[0] - 1, nums[1], nums[2], nums[3:]
        lab[v] = (None if lo == 0 else lo, None if hi == 0 else hi)
        rot[v] = [GAP if w == -1 else w - 1 for w in nb]
    return rot, lab


def read_f1_combined_rule(path, rule_names):
    lines = [l for l in Path(path).read_text().splitlines()]
    head = lines[1].split()
    n, s, t, r = (int(x) for x in head)
    rot, lab = read_f1_structure(lines[2:], n)
    flags = lines[2 + n].strip()
    assert len(flags) == len(rule_names), (path, len(flags))
    rules = tuple(sorted(rule_names[i] for i, c in enumerate(flags) if c == "1"))
    return rot, lab, s - 1, t - 1, r, rules


def read_f1_cartwheel(path):
    lines = Path(path).read_text().splitlines()
    n, c = (int(x) for x in lines[1].split())
    rot, lab = read_f1_structure(lines[2:], n)
    return rot, lab, c - 1


# ---------------------------------------------------------------------------
# F2 structures (dart lists: head, rev, succ, pred; succ is clockwise)
# ---------------------------------------------------------------------------
def rotations_from_darts(nv, head, rev, succ, pred):
    tail = lambda e: head[rev[e]]
    by_v = collections.defaultdict(list)
    for e in range(len(head)):
        by_v[head[e]].append(e)
    rot = {}
    for v in range(nv):
        darts = by_v.get(v, [])
        starts = [e for e in darts if pred[e] == -1]
        if len(starts) > 1:
            raise ValueError(f"vertex {v} has {len(starts)} gaps")
        seq = []
        if starts:
            e = starts[0]
            while e != -1:
                seq.append(tail(e))
                e = succ[e]
            seq.append(GAP)
        elif darts:
            e0 = min(darts)
            e = e0
            while True:
                seq.append(tail(e))
                e = succ[e]
                if e == e0:
                    break
        if len(seq) - (1 if starts else 0) != len(darts):
            raise ValueError(f"vertex {v}: rotation does not cover its darts")
        rot[v] = seq
    return rot


def f2_label(lo, hi, inf):
    norm = lambda x: None if (x is None or x >= inf) else x
    return (norm(lo), norm(hi))


# ---------------------------------------------------------------------------
# canonical code
# ---------------------------------------------------------------------------
def code_from(rot, lab, root, entry_nb, best=None):
    num = {root: 0}
    entry = {root: entry_nb}
    queue = [root]
    out = []
    h = 0
    while h < len(queue):
        u = queue[h]
        h += 1
        r = rot[u]
        k = len(r)
        i = r.index(entry[u]) if entry[u] is not None else 0
        out.append(lab[u])
        out.append(k)
        for j in range(k):
            w = r[(i + j) % k]
            if w == GAP:
                out.append(GAP)
                continue
            if w not in num:
                num[w] = len(num)
                entry[w] = u
                queue.append(w)
            out.append(num[w])
    if len(num) != len(rot):
        raise ValueError("not connected")
    return tuple(out)


def rule_code(rot, lab, s, t, charge, rules):
    return (charge, rules, code_from(rot, lab, t, s))


def cartwheel_code(rot, lab, centre):
    return min(code_from(rot, lab, centre, w) for w in rot[centre] if w != GAP)


def mirror(rot):
    return {v: list(reversed(r)) for v, r in rot.items()}


def compare(name, f1_codes, f2_codes, f2_mirror_codes=None):
    a, b = collections.Counter(f1_codes), collections.Counter(f2_codes)
    same = a == b
    print(f"{name}: F1 {sum(a.values())} objects ({len(a)} distinct), "
          f"F2 {sum(b.values())} ({len(b)} distinct): "
          f"{'IDENTICAL as multisets' if same else 'DIFFER'}")
    if not same:
        print(f"    only in F1: {sum((a - b).values())}, only in F2: {sum((b - a).values())}")
        if f2_mirror_codes is not None:
            m = collections.Counter(f2_mirror_codes)
            print(f"    with F2 mirrored: {'identical' if m == a else 'still differ'}")
    return same


def main():
    f1, f2, f2repo, ruledir = (Path(x) for x in sys.argv[1:5])
    sys.path.insert(0, str(f2repo / "checks" / "f2"))
    from nl4ct import pseudo, cartwheel  # noqa: E402

    rule_names = sorted(p.stem for p in ruledir.glob("*.rule"))
    ok = True

    # -- R* and R*-D --------------------------------------------------------
    for label, f1sub, f2file in (("A.1 R*", "all", "a1-rstar.jsonl"),
                                 ("A.2 R*-D", "non_blocked", "a2-rstar-d.jsonl")):
        c1 = []
        for p in sorted((f1 / "combined_rules" / f1sub).iterdir()):
            rot, lab, s, t, r, rules = read_f1_combined_rule(p, rule_names)
            c1.append(rule_code(rot, lab, s, t, r, rules))
        c2, c2m = [], []
        for line in (f2 / f2file).read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            o = json.loads(line)
            nv = len(o["lo"])
            rot = rotations_from_darts(nv, o["head"], o["rev"], o["succ"], o["pred"])
            lab = {v: f2_label(o["lo"][v], o["hi"][v], pseudo.INF) for v in range(nv)}
            # dart 0 is s->t: head t, tail s
            t = o["head"][0]
            s = o["head"][o["rev"][0]]
            rules = tuple(sorted(o["rules"]))
            c2.append(rule_code(rot, lab, s, t, o["charge"], rules))
            c2m.append(rule_code(mirror(rot), lab, s, t, o["charge"], rules))
        ok &= compare(label, c1, c2, c2m)

    # -- C0: surviving wheels per degree --------------------------------------
    for d in (7, 8, 9, 10, 11):
        c1 = []
        for p in sorted((f1 / "wheels" / f"d{d}").iterdir()):
            rot, lab, c = read_f1_cartwheel(p)
            c1.append(cartwheel_code(rot, lab, c))
        c2, c2m = [], []
        for line in (f2 / f"wheels-{d}.txt").read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if parts[-1] != "survives":
                continue
            degs = [int(x) for x in parts[1:-1]]
            cw = cartwheel.generate_cartwheel(d, degs)
            pc = cw.pc
            rot = rotations_from_darts(pc.nv, pc.head, pc.rev, pc.succ, pc.pred)
            lab = {v: f2_label(pc.lo[v], pc.hi[v], pseudo.INF) for v in range(pc.nv)}
            c2.append(cartwheel_code(rot, lab, 0))
            c2m.append(cartwheel_code(mirror(rot), lab, 0))
        ok &= compare(f"A.3 C0, centre degree {d}", c1, c2, c2m)

    # -- C_all: the bad cartwheels ----------------------------------------------
    c1 = []
    for p in sorted((f1 / "wheels" / "zero").iterdir()):
        rot, lab, c = read_f1_cartwheel(p)
        c1.append(cartwheel_code(rot, lab, c))
    c2, c2m = [], []
    for line in (f2 / "call.jsonl").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        o = json.loads(line)
        cw = cartwheel.generate_cartwheel(o["d"], o["wheel"])
        pc = cw.pc
        rot = rotations_from_darts(pc.nv, pc.head, pc.rev, pc.succ, pc.pred)
        assert len(o["lo"]) == pc.nv
        lab = {v: f2_label(o["lo"][v], o["hi"][v], pseudo.INF) for v in range(pc.nv)}
        c2.append(cartwheel_code(rot, lab, 0))
        c2m.append(cartwheel_code(mirror(rot), lab, 0))
    ok &= compare("A.3 C_all, bad cartwheels", c1, c2, c2m)

    print("VERDICT:", "every object set identical" if ok else "DIFFERENCES FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
