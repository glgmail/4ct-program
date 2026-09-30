#!/usr/bin/env python3
"""Implementation A, Phase 2b (SPEC Amendment 2): the dodecahedron families.

    python3 a2run.py --all --jobs 4      # mandatory families + controls + union
    python3 a2run.py --family T2         # one family (F0 KM KMd T2R T2 T3s)
    python3 a2run.py --control C4-cube   # one control (C0 C4-prism5 C4-cube C5-W2 C5-W3 C6 C8)
    python3 a2run.py --union             # union.json from finished families
    python3 a2run.py --family T3 --jobs 8   # optional T3 (Gabriel's go, 2026-09-30)

The mandatory families (A2.13 item 2) and the optional T3 are enabled; T4s
refuses to run.  T3 runs its 60 first-move subtrees in worker processes
(A2.10); novelty is still processed in family order in the parent.
Outputs: out/<web>/A2/... (A2.8).  h.jsonl files are written next to the other
outputs but are not meant to be committed (A2.13 item 4); T3's is not written
at all (more than 2,000,000 lines, A2.8).
"""

import argparse
import datetime
import hashlib
import itertools
import json
import math
import multiprocessing
import os
import platform
import resource
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from d1a import web as W                                    # noqa: E402
from d1a import webdata, gf4, tree                          # noqa: E402
from d1a import records as R                                # noqa: E402
from d1a.a2lib import (automorphisms, tait_perms, apply_perm, foam_image,   # noqa: E402
                       km_sets, face_4colourings, km_foam, FSpan, fview, f_rank)
from d1a.analysis import TargetWeb, analyse                 # noqa: E402
from d1a.foam import degree                                 # noqa: E402
from d1a.gen import generate                                # noqa: E402

OUT = os.environ.get("D1_A2_OUT", os.path.join(HERE, "out"))
S0 = ("unzip", 0, 0, 1)
P2_ELLQ = {-3: 9, -1: 20, 1: 20, 3: 9}
P2_RQ = {-3: 9, -1: 20, 1: 20, 3: 11}
MANDATORY = ["F0", "KM", "KMd", "T2R", "T2", "T3s"]
CONTROLS = ["C0", "C4-prism5", "C4-cube", "C5-W2", "C5-W3", "C6", "C8"]


def RET(d):
    return d <= -3 and (d - 3) % 6 == 0


def ALL(d):
    return True


def C5KEEP(d):
    return d in (-5, -3)


TREE = {   # family: (web, rules, first, keep)
    "F0": ("W1", ["emit"], None, ALL),
    "T2R": ("W1", ["reducible", "emit"], None, RET),
    "T2": ("W1", ["irreducible", "emit"], None, RET),
    "T3s": ("W1", ["irreducible", "irreducible", "emit"], S0, RET),
    "C4-prism5": ("prism5", ["reducible", "emit"], None, ALL),
    "C4-cube": ("cube", ["reducible", "emit"], None, ALL),
    "C5-W2": ("W2", ["irreducible", "emit"], None, C5KEEP),
    "C5-W3": ("W3", ["irreducible", "emit"], None, C5KEEP),
}

# A2.10: A (CPU) upper estimates in seconds for the main pass; 3x is the hard stop.
ESTIMATE = {"F0": 120, "KM": 120, "KMd": 120, "T2R": 1800, "T2": 720, "T3s": 1800,
            "C0": 120, "C6": 720, "C8": 120,
            "C4-prism5": 1200, "C4-cube": 600, "C5-W2": 2700, "C5-W3": 2700,
            "T3": 60 * 69.4}   # T3: 60 x the measured T3s main pass (out/W1/A2/T3s/run.json)

# ------------------------------------------------------------------ C3 expected
def _s(z, u, s, i):
    return {"zip": z, "unzip": u, "saddle": s, "ih": i}


EXPECT = {
    "F0": {"levels": {"1": (0, 60, 60, 180)}, "N_leaves": 11880, "N_retained": 11880,
           "leaves_by_degree": {"-3": 810, "-1": 2610, "1": 3780, "3": 3150, "5": 1350, "7": 180}},
    "T2R": {"levels": {"2": (240, 12660, 720, 45120)}, "expanded": {"1": 180},
            "N_leaves": 4190400, "N_retained": 107430,
            "per_move": {"2": _s((120, 660, 60, 4650), (0, 120, 450, 23310),
                                 (0, 11880, 180, 11820), (120, 0, 30, 5340))}},
    "T2": {"levels": {"2": (240, 4260, 5220, 11400)}, "expanded": {"1": 60},
           "N_leaves": 1499040, "N_retained": 50220,
           "per_move": {"2": _s((120, 0, 120, 1740), (0, 120, 4620, 3840),
                                (0, 4140, 360, 4080), (120, 0, 120, 1740))}},
    "T3s": {"levels": {"3": (548, 6974, 9508, 17362)}, "expanded": {"1": 1, "2": 87},
            "N_leaves": 4085832, "N_retained": 61927},
    "C4-prism5": {"levels": {"2": (320, 4290, 0, 10950)}, "expanded": {"1": 100},
                  "N_leaves": 566700},
    "C4-cube": {"levels": {"2": (288, 2532, 0, 5748)}, "expanded": {"1": 72},
                "N_leaves": 250056},
    "C5-W2": {"levels": {"2": (288, 5976, 7152, 17208)}, "expanded": {"1": 72},
              "N_leaves": 4603104, "N_retained": 14232 + 147216,
              "retained_by_degree": {"-5": 14232, "-3": 147216}},
    "C5-W3": {"levels": {"2": (336, 8532, 10520, 25316)}, "expanded": {"1": 90},
              "N_leaves": 8835096, "N_retained": 8444 + 159612,
              "retained_by_degree": {"-5": 8444, "-3": 159612},
              "level1_irreducible_by_move": {"unzip": 88, "ih": 2}},
}


def check_counts(name, d, extra=None):
    """Control C3: compare a count-only Stats dict with A2.5 / A2.9."""
    e = EXPECT.get(name)
    if e is None:
        return []
    bad = []
    for lvl, tot in e.get("levels", {}).items():
        got = tuple(sum(d["sites"][lvl][m][o] for m in tree.MOVES) for o in tree.OUTCOMES)
        if got != tot:
            bad.append("level %s outcomes %s != %s" % (lvl, got, tot))
    for lvl, n in e.get("expanded", {}).items():
        if d["expanded_nodes"].get(lvl) != n:
            bad.append("expanded %s = %s != %s" % (lvl, d["expanded_nodes"].get(lvl), n))
    for lvl, pm in e.get("per_move", {}).items():
        for mv, tup in pm.items():
            got = tuple(d["sites"][lvl][mv][o] for o in tree.OUTCOMES)
            if got != tup:
                bad.append("level %s %s %s != %s" % (lvl, mv, got, tup))
    for k in ("N_leaves", "N_retained", "leaves_by_degree"):
        if k in e and d[k] != e[k]:
            bad.append("%s %s != %s" % (k, d[k], e[k]))
    if "retained_by_degree" in e:
        got = {k: d["leaves_by_degree"].get(k, 0) for k in e["retained_by_degree"]}
        if got != e["retained_by_degree"]:
            bad.append("retained by degree %s" % got)
    if "level1_irreducible_by_move" in e:
        got = {m: d["sites"]["1"][m]["irreducible"] for m in tree.MOVES
               if d["sites"]["1"][m]["irreducible"]}
        if got != e["level1_irreducible_by_move"]:
            bad.append("level-1 irreducible by move %s" % got)
    if extra:
        bad += extra
    return bad


# ------------------------------------------------------------------ utilities
def peak_mb():
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_result(path, obj):
    """A2.8: json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=True) + newline."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\n") as fh:
        fh.write(json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=True) + "\n")


def qmap(d):
    return {str(k): v for k, v in sorted(d.items()) if v}


class Budget(Exception):
    pass


class Clock:
    def __init__(self, name):
        self.name = name
        self.t0 = time.time()
        self.c0 = time.process_time()
        self.start = utc()
        self.phases = {}
        self.limit = 3 * ESTIMATE.get(name, 3600)
        self.main_t0 = None

    def mark(self, phase):
        self.phases[phase] = {"wall_s": round(time.time() - self.t0, 1),
                              "cpu_s": round(time.process_time() - self.c0, 1)}
        self.t0 = time.time()
        self.c0 = time.process_time()

    def begin_main(self):
        self.main_t0 = time.process_time()

    def check(self):
        if self.main_t0 is not None and time.process_time() - self.main_t0 > self.limit:
            raise Budget("%s: main pass exceeded 3x its estimate (%d s)" % (self.name, self.limit))

    def runjson(self, path, extra=None):
        d = {"implementation": "A", "command": "python3 a2run.py " + " ".join(sys.argv[1:]),
             "git_commit": os.environ.get("D1_GIT_COMMIT", "unknown"),
             "machine": platform.node() + " " + platform.platform() + " python " + platform.python_version(),
             "phases": self.phases, "peak_rss_mb": peak_mb(), "workers": 1,
             "start_utc": self.start, "end_utc": utc(),
             "estimate_main_cpu_s": ESTIMATE.get(self.name)}
        if extra:
            d.update(extra)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="\n") as fh:
            fh.write(json.dumps(d, sort_keys=True, indent=1) + "\n")


def famdir(web, name):
    return os.path.join(OUT, web, "A2", name)


class HWriter:
    """h.jsonl lines + running SHA-256 (A2.8)."""

    def __init__(self, path):
        self.sha = hashlib.sha256()
        self.n = 0
        self.fh = open(path, "w", newline="\n") if path else None

    def line(self, obj):
        s = json.dumps(obj) + "\n"
        b = s.encode("ascii")
        self.sha.update(b)
        self.n += 1
        if self.fh:
            self.fh.write(s)

    def close(self):
        if self.fh:
            self.fh.close()
        return self.sha.hexdigest()


# ------------------------------------------------------------------ F0 state
class F0State:
    """F0 (A2.5) and the derived spaces of A2.7 step 1."""

    def __init__(self, check_phase2=False):
        self.K = W.load("W1")
        self.tw = TargetWeb(self.K)
        self.T = self.tw.T
        tw = self.tw
        items = []

        def emit(moves, chain, deg, H):
            tw.check_degree(H, deg)
            items.append((moves[0], chain, deg, H, tw.avec(H)))
        st = tree.Stats(1)
        tree.walk(self.K, ["emit"], None, ALL, st, emit)
        self.stats = st.as_dict()
        self.items = items
        if check_phase2:
            # the tree machinery reproduces SPEC 6.1/6.2 GEN in STRICT-ALL mode
            ref = []
            generate(self.K, None, "STRICT-ALL", True,
                     lambda site, H, d, ch: ref.append((list(site), ch, d, tw.avec(H))))
            assert len(ref) == len(items)
            for (s1, c1, d1, _, a1), (s2, c2, d2, a2) in zip(items, ref):
                assert s1 == s2 and tuple(c1) == tuple(c2) and d1 == d2 and a1 == a2
        self.idx = {d: [k for k, it in enumerate(items) if it[2] == d] for d in (-3, -1, 1, 3)}
        T = self.T
        self.A3 = FSpan()
        for k in self.idx[-3] + self.idx[3]:
            self.A3.add(fview(items[k][4], T))
        self.U0 = FSpan()
        self.U0_members = [k for k in self.idx[-3] if self.U0.add(fview(items[k][4], T))]
        E = gf4.Echelon()
        self.C3 = [k for k in self.idx[3] if E.add(items[k][4])]
        self.C3vec = [items[k][4] for k in self.C3]
        self.P = FSpan()
        self.P_members = [k for k in self.idx[-3] if self.P.add(self.pvec(items[k][4]))]
        self.m3vecs = [items[k][4] for k in self.idx[-3]]
        # dim R = 20 - rank of the constraints beta(b, u) over F-bases of A3 and U0
        cons = []
        for x in self.A3.rows:
            b = gf4_from_fview(x, T)
            c = 0
            for m, y in enumerate(self.U0.rows):
                v = gf4.dot(b, gf4_from_fview(y, T))
                c |= (v & 1) << (2 * m)
                c |= (v >> 1) << (2 * m + 1)
            cons.append(c)
        self.dimR = len(self.A3) - f_rank(cons)
        # U0 inside R
        for y in self.U0.rows:
            u = gf4_from_fview(y, T)
            assert all(gf4.dot(u, v) == 0 for v in self.m3vecs)

    def pvec(self, a):
        x = 0
        for k, c in enumerate(self.C3vec):
            v = gf4.dot(a, c)
            if v > 1:
                raise AssertionError("p-vector entry not in F")
            x |= v << k
        return x

    def start(self):
        return {"dimU": len(self.U0), "dimA3": len(self.A3), "dimR": self.dimR,
                "ell_m3": len(self.P)}


def gf4_from_fview(x, T):
    m = (1 << T) - 1
    return (x & m, x >> T)


# ------------------------------------------------------------------ step 2
class Search:
    def __init__(self, st):
        self.st = st
        self.U = st.U0.copy()
        self.P = st.P.copy()
        self.novel = []          # [i, deg, dimU, ell]
        self.aut_novel = []
        self.novel_items = []    # (i, g, deg, a) for every novel vector
        self.m3_added = []       # degree -3 novel vectors (for step 3)
        self.P_witness = []      # (i, g) whose p-vector entered P
        self.stop = None
        self.a3v = 0

    def process(self, a, deg, i, g=None):
        st = self.st
        T = st.T
        x = fview(a, T)
        if not st.A3.contains(x):
            self.a3v += 1
            self.stop = "A3_VIOLATION"
            return self.stop
        if self.U.contains(x):
            return None
        self.U.add(x)
        for v in st.m3vecs:
            if gf4.dot(a, v) != 0:
                raise AssertionError("novel member pairs nontrivially with F0_-3")
        if deg == -3:
            self.m3_added.append(a)
            if self.P.add(st.pvec(a)):
                self.P_witness.append((i, g))
        rec = [i, deg, len(self.U), len(self.P)]
        if g is None:
            self.novel.append(rec)
        else:
            self.aut_novel.append([i, g, deg, len(self.U), len(self.P)])
        self.novel_items.append((i, g, deg, a))
        if len(self.P) == 10:
            self.stop = "ELL60"
        elif len(self.U) == 11:
            self.stop = "DIMU11"
        return self.stop

    def final(self, ellq_f0):
        st = self.st
        m3 = st.m3vecs + self.m3_added
        ell_m3 = f_rank([st.pvec(v) for v in m3])
        assert ell_m3 == len(self.P), "step 3: l_-3 recomputation differs"
        rows = []
        for k in st.idx[3]:
            r = st.items[k][4]
            x = 0
            for j, c in enumerate(m3):
                v = gf4.dot(r, c)
                if v > 1:
                    raise AssertionError("pairing not in F")
                x |= v << j
            rows.append(x)
        ell_3 = f_rank(rows)
        assert ell_3 == ell_m3, "step 3: l_3 != l_-3"
        ell = ell_m3 + ellq_f0.get(-1, 0) + ellq_f0.get(1, 0) + ell_3
        return {"dimU": len(self.U), "ell_m3": ell_m3, "ell_3": ell_3, "ell": ell}


# ------------------------------------------------------------------ sample
def sample_lines(st, N_ret, avec_of, foam_of, novel_foams):
    """A2.7 direct-evaluation sample: returns (lines, n_direct)."""
    tw = st.tw
    p3 = st.idx[3]
    n3 = len(p3)
    lines = []
    nd = 0

    def one(i, j0, a, H):
        nonlocal nd
        b = st.items[j0][4]
        v = gf4.dot(a, b)
        if v > 1:
            raise AssertionError("sample value not in F")
        if H is None:
            raise AssertionError("no foam kept for sample index %d" % i)
        dv = tw.direct_pair(H, st.items[j0][3])
        if dv != v:
            raise AssertionError("direct closed-foam value %d != beta %d at (%d,%d)"
                                 % (dv, v, i, j0 + 1))
        nd += 1
        lines.append("%d\t%d\t%d\n" % (i, j0 + 1, v))

    for k in range(1, min(1000, N_ret) + 1):
        i = 1 + (7919 * k) % N_ret
        j0 = p3[(104729 * k) % n3]
        one(i, j0, avec_of(i), foam_of(i))
    for (i, a, H) in novel_foams:
        for j0 in st.C3:
            one(i, j0, a, H)
    return lines, nd


def sample_indices(N_ret):
    return sorted({1 + (7919 * k) % N_ret for k in range(1, min(1000, N_ret) + 1)})


# ------------------------------------------------------------------ families
def run_tree_family(name, clock):
    web, rules, first, keep = TREE[name]
    K = W.load(web)
    # count-only pass
    cst = tree.Stats(len(rules))
    pf = {} if name == "T2" else None
    tree.walk(K, rules, first, keep, cst, None, pf)
    cd = cst.as_dict()
    extra = []
    if pf is not None:
        vals = set((tuple(v[0][o] for o in tree.OUTCOMES), v[1]) for v in pf.values())
        if len(pf) != 60 or vals != {((4, 71, 87, 190), 837)}:
            extra.append("T2 per-first-move uniformity fails: %s" % vals)
    if name == "T3s":
        alt = tree.Stats(len(rules))
        tree.walk(K, rules, ("unzip", 18, 1, 2), keep, alt)
        if alt.as_dict()["sites"]["3"] != cd["sites"]["3"]:
            extra.append("T3s level-3 counts differ for ['unzip', 18, 1, 2]")
    bad = check_counts(name, cd, extra)
    clock.mark("count")
    if bad:
        raise AssertionError("C3 count mismatch for %s: %s" % (name, bad))
    return K, cd


def family_main(name, st, ellq_f0):
    clock = Clock(name)
    d = famdir("W1", name)
    os.makedirs(d, exist_ok=True)
    tw = st.tw
    T = st.T
    res = {"amendment": 2, "web": "W1", "family": name}
    S = Search(st)
    avecs = {}
    foams = {}
    novel_foams = []
    hw = HWriter(os.path.join(d, "h.jsonl"))
    if name in ("KM", "KMd"):
        K = st.K
        sets, _ = km_sets(K)
        cols = face_4colourings(K)
        classes = set()
        for c in cols:
            for colour in (1, 2, 3, 4):
                cl = tuple(f for f in range(len(c)) if c[f] == colour)
                if len(cl) == 3:
                    classes.add(cl)
        assert len(sets) == 20 and len(cols) == 240 and classes == set(sets)
        mins = [f[0] for f in K.faces()]
        assert mins == [0, 1, 2, 4, 7, 10, 15, 18, 25, 31, 37, 45]
        members = []
        for S_ in sets:
            H0, nfac = km_foam(K, S_)
            assert nfac == 24 and H0.nv == 5 and degree(H0, K.V) == -3
            ks = range(0, 4) if name == "KMd" else range(0, 1)
            for k in ks:
                for combo in itertools.combinations_with_replacement(range(nfac), k):
                    members.append((S_, combo))
        lbd = {}
        for S_, combo in members:
            dd = -3 + 2 * len(combo)
            lbd[dd] = lbd.get(dd, 0) + 1
        cd = {"sites": {}, "expanded_nodes": {},
              "leaves_by_degree": {str(k): v for k, v in sorted(lbd.items())},
              "N_leaves": len(members), "N_retained": len(members)}
        expN = 20 if name == "KM" else 58500
        if len(members) != expN:
            raise AssertionError("C3: %s has %d members" % (name, len(members)))
        clock.mark("count")
        clock.begin_main()
        items = []

        def km_member(idx):
            S_, combo = members[idx - 1]
            dots = [0] * 24
            for f in combo:
                dots[f] += 1
            H, _ = km_foam(K, S_, dots)
            return H
        for i, (S_, combo) in enumerate(members, 1):
            H = km_member(i)
            deg = degree(H, K.V)
            assert deg == -3 + 2 * len(combo)
            a = tw.avec(H)
            avecs[i] = a
            items.append((a, deg))
            hw.line({"i": i, "km": sorted(mins[f] for f in S_), "dots": list(combo),
                     "deg": deg, "a": tw.hexa(a)})
            if RET(deg) and S.stop is None:
                nb = len(S.novel)
                S.process(a, deg, i)
                if len(S.novel) > nb:
                    novel_foams.append((i, a, H))
            if S.stop is not None:
                break
        processed = hw.n
        foam_of = km_member
    else:
        K, cd = run_tree_family(name, clock)
        web, rules, first, keep = TREE[name]
        idxs = set(sample_indices(cd["N_retained"]))
        clock.begin_main()
        state = {"i": 0}

        def emit(moves, chain, deg, H):
            state["i"] += 1
            i = state["i"]
            if i % 2000 == 0:
                clock.check()
            tw.check_degree(H, deg)
            a = tw.avec(H)
            avecs[i] = a
            if i in idxs:
                foams[i] = H
            hw.line({"i": i, "moves": moves, "chain": list(chain), "deg": deg,
                     "a": tw.hexa(a)})
            nb = len(S.novel)
            S.process(a, deg, i)
            if len(S.novel) > nb:
                novel_foams.append((i, a, H))
            if S.stop is not None:
                raise tree.StopWalk()
        mst = tree.Stats(len(rules))
        try:
            tree.walk(K, rules, first, keep, mst, emit)
            assert mst.as_dict() == cd, "main pass counts differ from the count-only pass"
        except tree.StopWalk:
            pass
        processed = state["i"]
        if S.stop is not None and processed != cd["N_retained"]:
            idxs2 = set(sample_indices(processed)) - set(foams)
            st2 = {"i": 0}

            def emit2(moves, chain, deg, H):
                st2["i"] += 1
                if st2["i"] in idxs2:
                    foams[st2["i"]] = H
                if st2["i"] >= processed:
                    raise tree.StopWalk()
            try:
                tree.walk(K, rules, first, keep, tree.Stats(len(rules)), emit2)
            except tree.StopWalk:
                pass
        foam_of = foams.get
    # A2.7 step 2.4: Aut closure (T3s only)
    aut_direct = 0
    if name == "T3s" and S.stop is None:
        auts = automorphisms(st.K)
        perms = tait_perms(st.K, st.tw.taits, auts)
        base = list(S.novel_items)
        for (i, g0, deg, a) in base:
            Hn = [H for (ii, aa, H) in novel_foams if ii == i][0]
            for g in range(1, 120):
                b = apply_perm(a, perms[g])
                nb = len(S.aut_novel)
                S.process(b, deg, i, g)
                if len(S.aut_novel) > nb:
                    # extra internal check: the image foam has a-vector g.a and
                    # direct values with C3 equal to beta
                    Hg = foam_image(Hn, st.K, auts[g][2])
                    assert tw.avec(Hg) == b
                    for j0 in st.C3:
                        assert tw.direct_pair(Hg, st.items[j0][3]) == gf4.dot(b, st.items[j0][4])
                        aut_direct += 1
                if S.stop is not None:
                    break
            if S.stop is not None:
                break
    clock.mark("main")
    hsha = hw.close()
    lines, nd = sample_lines(st, processed, lambda i: avecs[i], foam_of, novel_foams)
    with open(os.path.join(d, "pairsample.tsv"), "w", newline="\n") as fh:
        fh.writelines(lines)
    fin = S.final(ellq_f0)
    res.update(cd)
    res.update({"processed": processed, "h_sha256": hsha, "a3_violations": S.a3v,
                "novel": S.novel, "aut_novel": S.aut_novel, "start": st.start(),
                "final": fin, "stop": S.stop or "EXHAUSTED"})
    if name == "KMd":
        r = analyse((avecs[i], degree_of_km(i, items)) for i in range(1, processed + 1))
        res.update({"N": processed, "ell": r["ell"], "ell_q": qmap(r["ell_q"]), "r": r["r"],
                    "r_q": qmap(r["r_q"])})
        # C8: F0 u KMd
        r2 = analyse([(it[4], it[2]) for it in st.items] +
                     [(avecs[i], items[i - 1][1]) for i in range(1, processed + 1)])
        write_result(os.path.join(famdir("W1", "ctl-C8"), "result.json"), {
            "amendment": 2, "web": "W1", "family": "ctl-C8",
            "KMd": {"N": processed, "ell": r["ell"], "ell_q": qmap(r["ell_q"]), "r": r["r"],
                    "r_q": qmap(r["r_q"])},
            "F0_union_KMd": {"N": len(st.items) + processed, "ell": r2["ell"],
                             "ell_q": qmap(r2["ell_q"]), "r": r2["r"], "r_q": qmap(r2["r_q"])}})
    write_result(os.path.join(d, "result.json"), res)
    with open(os.path.join(d, "novel.jsonl"), "w", newline="\n") as fh:
        for (i, g, deg, a) in S.novel_items:
            fh.write(json.dumps({"i": i, "g": g, "deg": deg, "a": tw.hexa(a)}) + "\n")
    if S.stop in ("ELL60", "DIMU11"):
        write_certificate(d, st, S, name, avecs, foams, novel_foams)
    clock.runjson(os.path.join(d, "run.json"), {"direct_evaluations": nd + aut_direct,
                                               "h_lines": hw.n})
    summary = {k: res[k] for k in ("N_leaves", "N_retained", "processed", "a3_violations",
                                   "final", "stop")}
    summary["novel"] = len(S.novel)
    summary["aut_novel"] = len(S.aut_novel)
    print(json.dumps({"family": name, "summary": summary, "phases": clock.phases}), flush=True)
    return res


def degree_of_km(i, items):
    return items[i - 1][1]


def run_f0(st, ellq_f0, r):
    clock = Clock("F0")
    d = famdir("W1", "F0")
    os.makedirs(d, exist_ok=True)
    # step 0: count-only pass (the a-vectors of F0 were already built by F0State)
    K, cd0 = run_tree_family("F0", clock)
    cd = dict(st.stats)
    assert cd == cd0
    bad = check_counts("F0", cd)
    if bad:
        raise AssertionError("C3 count mismatch for F0: %s" % bad)
    hw = HWriter(os.path.join(d, "h.jsonl"))
    for i, (site, chain, deg, H, a) in enumerate(st.items, 1):
        hw.line({"i": i, "site": site, "chain": list(chain), "deg": deg, "a": st.tw.hexa(a)})
    hsha = hw.close()
    N = len(st.items)
    nbm = {"zip": 0, "unzip": 0, "saddle": 0, "ih": 0}
    for it in st.items:
        nbm[it[0][0]] += 1
    lines, nd = sample_lines(st, N, lambda i: st.items[i - 1][4], lambda i: st.items[i - 1][3], [])
    with open(os.path.join(d, "pairsample.tsv"), "w", newline="\n") as fh:
        fh.writelines(lines)
    S = Search(st)
    res = {"amendment": 2, "web": "W1", "family": "F0"}
    res.update(cd)
    res.update({"processed": N, "h_sha256": hsha, "a3_violations": 0, "novel": [],
                "aut_novel": [], "start": st.start(), "final": S.final(ellq_f0),
                "stop": "EXHAUSTED", "N": N, "ell": r["ell"], "ell_q": qmap(r["ell_q"]),
                "r": r["r"], "r_q": qmap(r["r_q"]), "N_by_move": nbm, "C3_size": len(st.C3)})
    write_result(os.path.join(d, "result.json"), res)
    clock.mark("main")
    clock.runjson(os.path.join(d, "run.json"), {"direct_evaluations": nd})
    print(json.dumps({"family": "F0", "ell": r["ell"], "ell_q": res["ell_q"],
                      "r_q": res["r_q"], "C3_size": len(st.C3), "start": st.start()}), flush=True)


# ------------------------------------------------------------------ T3 (optional)
# A2.5 T3 = T3s without the symmetry reduction: M1 ranges over the 60
# IRREDUCIBLE level-1 sites of W1 in SITES order, M2 IRREDUCIBLE, M3 REDUCIBLE
# (emitted), retained degrees RET, no Aut closure.  The 60 subtrees run in
# worker processes (A2.10).  Each worker returns its subtree's h.jsonl lines
# (global i), its counts, the sample values it was asked for, and the
# "candidates": the members whose a-vector is outside A3, or outside
# U0 + the span of the subtree's earlier candidates.  Every other member is
# in the family's current U whatever happened before it (U contains U0 and
# every earlier processed vector), so A2.7 step 2 returns "not novel" for it
# with no side effect.  The parent runs step 2 on the candidates in family
# order, which is exactly the sequential computation.
T3_RULES = ["irreducible", "irreducible", "emit"]
T3S_MAIN_CPU = 69.4
T3_EXPECT = {"L1": (0, 60, 60, 180), "L2": (240, 4260, 5220, 11400),
             "L3": (32880, 418440, 570480, 1041720), "sub_L3": (548, 6974, 9508, 17362),
             "expanded": {"0": 1, "1": 60, "2": 5220},
             "N_leaves": 245149920, "N_retained": 3715620}
H_FILE_MAX = 2000000
MEM_ABORT_MB = 3400
_W = {}


def _w_K():
    if "K" not in _W:
        _W["K"] = W.load("W1")
    return _W["K"]


def _w_st():
    if "st" not in _W:
        c0 = time.process_time()
        _W["st"] = F0State()
        _W["setup_cpu"] = time.process_time() - c0
    return _W["st"]


def _outc(stats, lvl):
    return tuple(sum(stats["sites"][lvl][m][o] for m in tree.MOVES) for o in tree.OUTCOMES)


def t3_count_task(site):
    c0 = time.process_time()
    d = tree.walk(_w_K(), T3_RULES, tuple(site), RET, tree.Stats(3)).as_dict()
    return {"stats": d, "cpu": time.process_time() - c0, "rss": peak_mb()}


def _direct_check(st, a, H, j0):
    v = gf4.dot(a, st.items[j0][4])
    if v > 1:
        raise AssertionError("sample value not in F")
    dv = st.tw.direct_pair(H, st.items[j0][3])
    if dv != v:
        raise AssertionError("direct closed-foam value %d != beta %d (F0 member %d)"
                             % (dv, v, j0 + 1))
    return v


def t3_main_task(args):
    """One first-move subtree.  args = (m, site, offset, want, lines_wanted)."""
    m, site, offset, want, lines_wanted = args
    c0 = time.process_time()
    st = _w_st()
    setup = _W.pop("setup_cpu", 0.0)
    tw, T = st.tw, st.T
    Ul = st.U0.copy()
    lines = []
    samp = []
    cands = []
    nd = [0]
    n = [0]
    a3 = [False]

    def emit(moves, chain, deg, H):
        n[0] += 1
        il = n[0]
        tw.check_degree(H, deg)
        a = tw.avec(H)
        if lines_wanted:
            lines.append(json.dumps({"i": offset + il, "moves": moves, "chain": list(chain),
                                     "deg": deg, "a": tw.hexa(a)}))
        for j0 in want.get(il, ()):
            samp.append((offset + il, j0, _direct_check(st, a, H, j0)))
            nd[0] += 1
        x = fview(a, T)
        if not st.A3.contains(x):
            if not a3[0]:          # the first violation stops the family
                a3[0] = True
                cands.append((il, deg, a, H, None))
        elif not Ul.contains(x):
            Ul.add(x)
            c3 = [_direct_check(st, a, H, j0) for j0 in st.C3]
            nd[0] += len(c3)
            cands.append((il, deg, a, H, c3))
    stats = tree.walk(_w_K(), T3_RULES, tuple(site), RET, tree.Stats(3), emit).as_dict()
    data = ("\n".join(lines) + "\n").encode("ascii") if lines else b""
    return {"m": m, "stats": stats, "n": n[0], "data": data, "samp": samp, "cands": cands,
            "direct": nd[0], "cpu": time.process_time() - c0, "setup_cpu": setup,
            "rss": peak_mb()}


def _tree_rss_mb(root):
    """Resident set size of root and all its descendants (Linux /proc), in MB."""
    kids, rss = {}, {}
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        try:
            with open("/proc/%s/stat" % p) as fh:
                s = fh.read()
            ppid = int(s[s.rfind(")") + 2:].split()[1])
            with open("/proc/%s/statm" % p) as fh:
                r = int(fh.read().split()[1])
        except (OSError, ValueError, IndexError):
            continue
        kids.setdefault(ppid, []).append(int(p))
        rss[int(p)] = r
    tot, stack = 0, [root]
    while stack:
        q = stack.pop()
        tot += rss.get(q, 0)
        stack += kids.get(q, [])
    return tot * os.sysconf("SC_PAGE_SIZE") / 2.0 ** 20


class RssMonitor(threading.Thread):
    """Samples the total RSS of this process tree (parent + workers)."""

    def __init__(self):
        super().__init__(daemon=True)
        self.peak = 0.0
        self.halt = threading.Event()
        self.over = False

    def run(self):
        me = os.getpid()
        while not self.halt.is_set():
            v = _tree_rss_mb(me)
            self.peak = max(self.peak, v)
            if v > MEM_ABORT_MB:
                self.over = True
            self.halt.wait(0.5)


def _pool_results(it, count, deadline, mon, what, on_result):
    """Consume count ordered results, enforcing the wall limit and memory ceiling."""
    for _ in range(count):
        while True:
            try:
                r = it.next(timeout=2)
                break
            except multiprocessing.TimeoutError:
                if time.time() > deadline:
                    raise Budget("T3 %s pass exceeded its wall limit" % what)
                if mon.over:
                    raise Budget("T3 %s pass: total RSS above %d MB" % (what, MEM_ABORT_MB))
        if on_result(r) is False:
            return


def t3_level1(K):
    st = tree.Stats(3)
    fbm = {f[0]: f for f in K.faces()}
    firsts = []
    for site in tree.sites(K):
        oc, op, node = tree.outcome(K, site, fbm)
        st.sites["1"][site[0]][oc] += 1
        if oc == "irreducible":
            firsts.append(site)
    return st.sites["1"], firsts


def run_t3(st, ellq_f0, jobs, first_limit=None):
    name = "T3"
    t_start, start_utc = time.time(), utc()
    cpu_parent0 = time.process_time()
    K = st.K
    d = famdir("W1", name)
    os.makedirs(d, exist_ok=True)
    four_h = 4 * 3600.0
    mon = RssMonitor()
    mon.start()
    ctx = multiprocessing.get_context("forkserver")
    phases = {}
    worker_rss = [0.0]
    wcpu = {"count": 0.0, "main": 0.0, "setup": 0.0}
    with ctx.Pool(jobs) as pool:
        # ---------------- step 0: count-only pass
        t0, c0 = time.time(), time.process_time()
        l1, firsts = t3_level1(K)
        bad = []
        if _outc({"sites": {"1": l1}}, "1") != T3_EXPECT["L1"] or len(firsts) != 60:
            bad.append("level 1 outcomes %s" % (_outc({"sites": {"1": l1}}, "1"),))
        if first_limit:
            firsts = firsts[:first_limit]
        subs = []

        def got_count(r):
            subs.append(r["stats"])
            wcpu["count"] += r["cpu"]
            worker_rss[0] = max(worker_rss[0], r["rss"])
        _pool_results(pool.imap(t3_count_task, firsts, chunksize=1), len(firsts),
                      t_start + four_h, mon, "count", got_count)
        cd = {"sites": {"1": l1}, "expanded_nodes": {"0": 1, "1": len(firsts), "2": 0},
              "leaves_by_degree": {}, "N_leaves": 0, "N_retained": 0}
        for lvl in ("2", "3"):
            cd["sites"][lvl] = {mv: {oc: 0 for oc in tree.OUTCOMES} for mv in tree.MOVES}
        lbd = {}
        per_sub = []
        for site, s in zip(firsts, subs):
            if s["expanded_nodes"] != {"0": 1, "1": 1, "2": 87}:
                bad.append("subtree %s expanded %s" % (list(site), s["expanded_nodes"]))
            if _outc(s, "3") != T3_EXPECT["sub_L3"]:
                bad.append("subtree %s level-3 outcomes %s" % (list(site), _outc(s, "3")))
            for lvl in ("2", "3"):
                for mv in tree.MOVES:
                    for oc in tree.OUTCOMES:
                        cd["sites"][lvl][mv][oc] += s["sites"][lvl][mv][oc]
            cd["expanded_nodes"]["2"] += s["expanded_nodes"]["2"]
            for k, v in s["leaves_by_degree"].items():
                lbd[int(k)] = lbd.get(int(k), 0) + v
            cd["N_leaves"] += s["N_leaves"]
            cd["N_retained"] += s["N_retained"]
            per_sub.append((s["N_leaves"], s["N_retained"], json.dumps(s["sites"]["3"], sort_keys=True)))
        cd["leaves_by_degree"] = {str(k): v for k, v in sorted(lbd.items()) if v}
        uniform = {"leaves_retained": sorted(set((a, b) for a, b, _ in per_sub)),
                   "level3_per_move_patterns": len(set(c for _, _, c in per_sub))}
        if not first_limit:
            for key, lvl in (("L2", "2"), ("L3", "3")):
                if _outc(cd, lvl) != T3_EXPECT[key]:
                    bad.append("level %s outcomes %s" % (lvl, _outc(cd, lvl)))
            for k in ("expanded", "N_leaves", "N_retained"):
                got = cd["expanded_nodes"] if k == "expanded" else cd[k]
                if got != T3_EXPECT[k]:
                    bad.append("%s %s" % (k, got))
            # level 2 of T3 is level 2 of T2 (same 60 first moves, all sites)
            for mv, tup in EXPECT["T2"]["per_move"]["2"].items():
                if tuple(cd["sites"]["2"][mv][o] for o in tree.OUTCOMES) != tup:
                    bad.append("level 2 %s differs from T2" % mv)
        phases["count"] = {"wall_s": round(time.time() - t0, 1),
                           "cpu_s": round(time.process_time() - c0 + wcpu["count"], 1)}
        if bad:
            raise AssertionError("C3 count mismatch for T3: %s" % bad)
        nsub = len(firsts)
        est_cpu = nsub * T3S_MAIN_CPU
        est_wall = math.ceil(nsub / float(jobs)) * T3S_MAIN_CPU
        print(json.dumps({"family": name, "count": {k: cd[k] for k in
                          ("expanded_nodes", "N_leaves", "N_retained")},
                          "level3": _outc(cd, "3"), "uniform": uniform,
                          "count_phase": phases["count"],
                          "estimate_main_cpu_s": round(est_cpu, 1),
                          "estimate_main_wall_s": round(est_wall, 1), "jobs": jobs}), flush=True)

        # ---------------- step 2: main pass
        t0, c0 = time.time(), time.process_time()
        deadline = min(t0 + 3 * est_wall, t_start + four_h)
        N_ret = cd["N_retained"]
        offsets = []
        o = 0
        for s in subs:
            offsets.append(o)
            o += s["N_retained"]
        p3 = st.idx[3]
        n3 = len(p3)

        def kpairs(N):
            return [(1 + (7919 * k) % N, p3[(104729 * k) % n3])
                    for k in range(1, min(1000, N) + 1)]

        def wants(pairs):
            w = [dict() for _ in firsts]
            for i, j0 in pairs:
                m = max(q for q in range(nsub) if offsets[q] < i)
                w[m].setdefault(i - offsets[m], []).append(j0)
            return w
        want = wants(kpairs(N_ret))
        write_h = N_ret <= H_FILE_MAX
        hpath = os.path.join(d, "h.jsonl")
        if os.path.exists(hpath):
            os.remove(hpath)
        hfh = open(hpath, "wb") if write_h else None
        sha = hashlib.sha256()
        S = Search(st)
        novel_foams = []
        novel_c3 = {}
        sval = {}
        state = {"processed": 0, "direct": 0, "lines": 0}

        def got_main(r):
            m = r["m"]
            wcpu["main"] += r["cpu"]            # includes the worker's F0 set-up
            wcpu["setup"] += r["setup_cpu"]
            worker_rss[0] = max(worker_rss[0], r["rss"])
            state["direct"] += r["direct"]
            if r["stats"] != subs[m]:
                raise AssertionError("main pass counts differ from the count-only pass "
                                     "(subtree %d)" % m)
            if r["n"] != subs[m]["N_retained"]:
                raise AssertionError("subtree %d: %d members != %d" % (m, r["n"],
                                                                       subs[m]["N_retained"]))
            for (i, j0, v) in r["samp"]:
                sval[(i, j0)] = v
            upto = r["n"]
            for (il, deg, a, H, c3) in r["cands"]:
                i = offsets[m] + il
                nb = len(S.novel)
                S.process(a, deg, i)
                if len(S.novel) > nb:
                    novel_foams.append((i, a, H))
                    novel_c3[i] = c3
                if S.stop is not None:
                    upto = il
                    break
            data = r["data"]
            if upto != r["n"]:
                data = b"".join(ln + b"\n" for ln in data.split(b"\n")[:upto])
            sha.update(data)
            if hfh:
                hfh.write(data)
            state["processed"] = offsets[m] + upto
            state["lines"] += data.count(b"\n")
            if wcpu["main"] > 3 * est_cpu:
                raise Budget("T3 main pass exceeded 3x its CPU estimate (%d s)" % (3 * est_cpu))
            if S.stop is not None:
                return False
        tasks = [(m, firsts[m], offsets[m], want[m], True) for m in range(nsub)]
        _pool_results(pool.imap(t3_main_task, tasks, chunksize=1), nsub, deadline, mon,
                      "main", got_main)
        if hfh:
            hfh.close()
        processed = state["processed"]
        if state["lines"] != processed:
            raise AssertionError("h lines %d != processed %d" % (state["lines"], processed))
        if S.stop is None and processed != N_ret:
            raise AssertionError("processed %d != N_retained %d" % (processed, N_ret))
        if not write_h and processed <= H_FILE_MAX:
            print("note: a stop left %d processed members; h.jsonl was not written "
                  "(N_retained > %d)" % (processed, H_FILE_MAX), flush=True)
        pairs = kpairs(processed)
        if S.stop is not None:
            # the sample indices depend on `processed`: evaluate the missing ones
            pool.terminate()
        missing = [pq for pq in pairs if pq not in sval]
    if missing:
        with ctx.Pool(jobs) as pool:
            want2 = wants(missing)
            tasks = [(m, firsts[m], offsets[m], want2[m], False)
                     for m in range(nsub) if want2[m]]

            def got_extra(r):
                for (i, j0, v) in r["samp"]:
                    sval[(i, j0)] = v
                state["direct"] += len(r["samp"])
                wcpu["main"] += r["cpu"]
            _pool_results(pool.imap(t3_main_task, tasks, chunksize=1), len(tasks),
                          t_start + four_h, mon, "sample", got_extra)
    lines = ["%d\t%d\t%d\n" % (i, j0 + 1, sval[(i, j0)]) for (i, j0) in pairs]
    for (i, a, H) in novel_foams:
        for j0, v in zip(st.C3, novel_c3[i]):
            lines.append("%d\t%d\t%d\n" % (i, j0 + 1, v))
    with open(os.path.join(d, "pairsample.tsv"), "w", newline="\n") as fh:
        fh.writelines(lines)
    phases["main"] = {"wall_s": round(time.time() - t0, 1),
                      "cpu_s": round(time.process_time() - c0 + wcpu["main"], 1)}
    fin = S.final(ellq_f0)
    res = {"amendment": 2, "web": "W1", "family": name}
    res.update(cd)
    res.update({"processed": processed, "h_sha256": sha.hexdigest(), "a3_violations": S.a3v,
                "novel": S.novel, "aut_novel": [], "start": st.start(), "final": fin,
                "stop": S.stop or "EXHAUSTED"})
    write_result(os.path.join(d, "result.json"), res)
    with open(os.path.join(d, "novel.jsonl"), "w", newline="\n") as fh:
        for (i, g, deg, a) in S.novel_items:
            fh.write(json.dumps({"i": i, "g": g, "deg": deg, "a": st.tw.hexa(a)}) + "\n")
    if S.stop in ("ELL60", "DIMU11"):
        write_certificate(d, st, S, name, None, None, novel_foams)
    mon.halt.set()
    mon.join()
    run = {"implementation": "A", "command": "python3 a2run.py " + " ".join(sys.argv[1:]),
           "git_commit": os.environ.get("D1_GIT_COMMIT", "unknown"),
           "machine": platform.node() + " " + platform.platform() + " python " +
           platform.python_version(),
           "phases": phases, "workers": jobs, "subtrees": nsub,
           "peak_rss_mb": round(mon.peak, 1),
           "peak_rss_note": "sampled every 0.5 s: parent + forkserver + workers, summed",
           "parent_peak_rss_mb": peak_mb(), "worker_peak_rss_mb_max": worker_rss[0],
           "worker_setup_cpu_s": round(wcpu["setup"], 1),
           "parent_cpu_s_total": round(time.process_time() - cpu_parent0, 1),
           "start_utc": start_utc, "end_utc": utc(),
           "estimate_main_cpu_s": round(est_cpu, 1), "estimate_main_wall_s": round(est_wall, 1),
           "direct_evaluations": state["direct"], "h_lines": processed,
           "h_jsonl_written": write_h, "first_limit": first_limit}
    with open(os.path.join(d, "run.json"), "w", newline="\n") as fh:
        fh.write(json.dumps(run, sort_keys=True, indent=1) + "\n")
    summary = {k: res[k] for k in ("N_leaves", "N_retained", "processed", "a3_violations",
                                   "h_sha256", "final", "stop")}
    summary["novel"] = len(S.novel)
    print(json.dumps({"family": name, "summary": summary, "phases": phases,
                      "peak_rss_mb": run["peak_rss_mb"]}), flush=True)
    return res


# ------------------------------------------------------------------ certificates
def write_certificate(d, st, S, name, avecs, foams, novel_foams):
    tw = st.tw
    it = st.items
    if S.stop == "DIMU11":
        vecs = [{"family": "F0", "i": k + 1, "a": tw.hexa(it[k][4])} for k in st.U0_members]
        for (i, g, deg, a) in S.novel_items:
            vecs.append({"family": name, "i": i, "g": g, "deg": deg, "a": tw.hexa(a)})
        write_result(os.path.join(d, "certificate.json"), {"stop": "DIMU11", "vectors": vecs})
        return

    def block(rows, colidx):
        """columns = first members of colidx (F0 order) raising the column rank."""
        cols = []
        E = FSpan()
        for j in colidx:
            x = 0
            for r, a in enumerate(rows):
                x |= gf4.dot(a, it[j][4]) << r
            if E.add(x):
                cols.append(j)
            if len(cols) == len(rows):
                break
        M = [[gf4.dot(a, it[j][4]) for j in cols] for a in rows]
        return cols, M

    def det(M):
        return 1 if f_rank([sum(b << j for j, b in enumerate(r)) for r in M]) == len(M) else 0
    wit_i, wit_g = S.P_witness[0]
    wit_a = [a for (i, g, deg, a) in S.novel_items if i == wit_i and g == wit_g][0]
    rows3 = [it[k][4] for k in st.P_members] + [wit_a]
    cols3, M3 = block(rows3, st.idx[3])
    # the +-1 blocks: rows = F0_-1 members raising the rank of their pairing with F0_1
    E1 = gf4.Echelon()
    C1 = [k for k in st.idx[1] if E1.add(it[k][4])]
    P1 = FSpan()
    rows1 = []
    for k in st.idx[-1]:
        x = 0
        for j, c in enumerate(C1):
            x |= gf4.dot(it[k][4], it[c][4]) << j
        if P1.add(x):
            rows1.append(k)
    cols1, M1 = block([it[k][4] for k in rows1], st.idx[1])
    # direct re-evaluation of every entry
    witH = [H for (i, a, H) in novel_foams if i == wit_i][0] if wit_g is None else \
        foam_image([H for (i, a, H) in novel_foams if i == wit_i][0], st.K,
                   automorphisms(st.K)[wit_g][2])
    rowsH3 = [it[k][3] for k in st.P_members] + [witH]
    for r, H in enumerate(rowsH3):
        for c, j in enumerate(cols3):
            assert tw.direct_pair(H, it[j][3]) == M3[r][c]
    for r, k in enumerate(rows1):
        for c, j in enumerate(cols1):
            assert tw.direct_pair(it[k][3], it[j][3]) == M1[r][c]
    cert = {"stop": "ELL60",
            "rows_m3": [{"family": "F0", "i": k + 1} for k in st.P_members] +
                       [{"family": name, "i": wit_i, "g": wit_g}],
            "cols_3": [{"family": "F0", "i": j + 1} for j in cols3],
            "M3": M3, "det_M3": det(M3),
            "rows_m1": [{"family": "F0", "i": k + 1} for k in rows1],
            "cols_1": [{"family": "F0", "i": j + 1} for j in cols1],
            "M1": M1, "det_M1": det(M1)}
    assert cert["det_M3"] == 1 and cert["det_M1"] == 1
    write_result(os.path.join(d, "certificate.json"), cert)


# ------------------------------------------------------------------ controls
def span_by_residue(vecs_degs, T):
    """F-spans of baseline vectors per degree."""
    sp = {}
    for a, d in vecs_degs:
        sp.setdefault(d, []).append(fview(a, T))
    return sp


def in_predicted_span(sp, a, d, T, cache):
    key = d
    S = cache.get(key)
    if S is None:
        S = FSpan()
        for dd, xs in sp.items():
            if dd <= d and (d - dd) % 6 == 0:
                for x in xs:
                    S.add(x)
        cache[key] = S
    return S.contains(fview(a, T))


def run_c45(name):
    clock = Clock(name)
    web, rules, first, keep = TREE[name]
    K, cd = run_tree_family(name, clock)
    tw = TargetWeb(K)
    T = tw.T
    d = famdir(web, "ctl-" + name.split("-")[0])
    os.makedirs(d, exist_ok=True)
    # baseline
    base = []
    if name.startswith("C4"):
        node = tree.gentree(K)
        for k, dg in enumerate(node.degs):
            chain, H = tree.leaf(node, k)
            base.append((tw.avec(H), dg, H))
        qexp = {"prism5": {-5: 1, -3: 5, -1: 9, 1: 9, 3: 5, 5: 1},
                "cube": {-4: 2, -2: 6, 0: 8, 2: 6, 4: 2}}[web]
    else:
        outer = webdata.EXPECT[web][3]
        generate(K, outer, "B19", True, lambda s, H, dg, ch: base.append((tw.avec(H), dg, H)))
        qexp = None
    sp = span_by_residue([(a, dg) for a, dg, H in base], T)
    cache = {}
    nb = len(base)
    idxs = set()
    for k in range(1, min(1000, cd["N_retained"]) + 1):
        idxs.add(1 + (7919 * k) % cd["N_retained"])
    avecs, degs, foams = {}, {}, {}
    hw = HWriter(os.path.join(d, "h.jsonl"))
    viol = [0]
    state = {"i": 0}
    clock.begin_main()

    def emit(moves, chain, deg, H):
        state["i"] += 1
        i = state["i"]
        if i % 5000 == 0:
            clock.check()
        tw.check_degree(H, deg)
        a = tw.avec(H)
        avecs[i] = a
        degs[i] = deg
        if i in idxs:
            foams[i] = H
        hw.line({"i": i, "moves": moves, "chain": list(chain), "deg": deg, "a": tw.hexa(a)})
        if not in_predicted_span(sp, a, deg, T, cache):
            viol[0] += 1
    mst = tree.Stats(len(rules))
    tree.walk(K, rules, first, keep, mst, emit)
    assert mst.as_dict() == cd
    N = state["i"]
    hsha = hw.close()
    rb = analyse((a, dg) for a, dg, H in base)
    rc = analyse([(a, dg) for a, dg, H in base] + [(avecs[i], degs[i]) for i in range(1, N + 1)])
    # sample: i over family members, j over baseline members
    lines = []
    ndir = 0
    for k in range(1, min(1000, N) + 1):
        i = 1 + (7919 * k) % N
        j = 1 + (104729 * k) % nb
        v = gf4.dot(avecs[i], base[j - 1][0])
        assert v <= 1
        dv = tw.direct_pair(foams[i], base[j - 1][2])
        assert dv == v, "direct value differs in %s" % name
        ndir += 1
        lines.append("%d\t%d\t%d\n" % (i, j, v))
    with open(os.path.join(d, "pairsample.tsv"), "w", newline="\n") as fh:
        fh.writelines(lines)
    clock.mark("main")
    ok = viol[0] == 0 and rc["ell"] == tw.T and (
        rc["ell"] == rc["r"] == tw.T and rc["ell_q"] == qexp and rc["r_q"] == qexp
        if qexp is not None else rc["ell"] <= tw.T)
    res = {"amendment": 2, "web": web, "family": "ctl-" + name.split("-")[0]}
    res.update(cd)
    res.update({"processed": N, "h_sha256": hsha, "span_violations": viol[0],
                "baseline": {"N": nb, "ell": rb["ell"], "ell_q": qmap(rb["ell_q"]),
                             "r": rb["r"], "r_q": qmap(rb["r_q"])},
                "combined": {"N": nb + N, "ell": rc["ell"], "ell_q": qmap(rc["ell_q"]),
                             "r": rc["r"], "r_q": qmap(rc["r_q"])},
                "pass": ok})
    write_result(os.path.join(d, "result.json"), res)
    clock.runjson(os.path.join(d, "run.json"), {"direct_evaluations": ndir})
    print(json.dumps({"control": name, "pass": ok, "N": N, "span_violations": viol[0],
                      "combined_ell": rc["ell"], "phases": clock.phases}), flush=True)
    if not ok:
        raise AssertionError("control %s failed" % name)


def run_c0(st, r):
    clock = Clock("C0")
    tw = st.tw
    vecs = []
    generate(st.K, webdata.EXPECT["W1"][3], "B19", True,
             lambda s, H, dg, ch: vecs.append((tw.avec(H), dg)))
    T = st.T
    m3_ok = all(st.U0.contains(fview(a, T)) for a, dg in vecs if dg == -3)
    p3_ok = all(st.A3.contains(fview(a, T)) for a, dg in vecs if dg == 3)
    ok = m3_ok and p3_ok and r["ell"] >= 58 and len(vecs) == 11160
    d = famdir("W1", "ctl-C0")
    write_result(os.path.join(d, "result.json"), {
        "amendment": 2, "web": "W1", "family": "ctl-C0", "B19_N": len(vecs),
        "B19_m3_in_U0": m3_ok, "B19_3_in_A3": p3_ok, "ell_F0": r["ell"], "pass": ok})
    clock.mark("main")
    clock.runjson(os.path.join(d, "run.json"))
    print(json.dumps({"control": "C0", "pass": ok}), flush=True)
    if not ok:
        raise AssertionError("C0 failed")


def run_c6(st, ellq_f0):
    clock = Clock("C6")
    tw = st.tw
    T = st.T
    auts = automorphisms(st.K)
    ok_all = all(g is not None for _, _, g in auts) and len(auts) == 120
    assert auts[0][2] == list(range(60))
    perms = tait_perms(st.K, tw.taits, auts)
    m3_ok = p3_ok = True
    for g in range(120):
        for k in st.idx[-3]:
            if not st.U0.contains(fview(apply_perm(st.items[k][4], perms[g]), T)):
                m3_ok = False
        for k in st.idx[3]:
            if not st.A3.contains(fview(apply_perm(st.items[k][4], perms[g]), T)):
                p3_ok = False
    # beta invariance on the F0 direct-evaluation sample, and image foams
    N = len(st.items)
    p3 = st.idx[3]
    inv_ok = True
    img_ok = True
    for k in range(1, min(1000, N) + 1):
        i = 1 + (7919 * k) % N
        j0 = p3[(104729 * k) % len(p3)]
        u, v = st.items[i - 1][4], st.items[j0][4]
        b = gf4.dot(u, v)
        for g in range(120):
            if gf4.dot(apply_perm(u, perms[g]), apply_perm(v, perms[g])) != b:
                inv_ok = False
        if k <= 20:
            for g in (1, 2, 61, 119):
                Hg = foam_image(st.items[i - 1][3], st.K, auts[g][2])
                if tw.avec(Hg) != apply_perm(u, perms[g]):
                    img_ok = False
    # symmetry check: T2 restricted to s0, then Aut closure
    K = st.K
    S = Search(st)
    state = {"i": 0}

    def emit(moves, chain, deg, H):
        state["i"] += 1
        a = tw.avec(H)
        S.process(a, deg, state["i"])
    tree.walk(K, ["irreducible", "emit"], S0, RET, tree.Stats(2), emit)
    n837 = state["i"]
    for (i, g0, deg, a) in list(S.novel_items):
        for g in range(1, 120):
            S.process(apply_perm(a, perms[g]), deg, i, g)
    fin = S.final(ellq_f0)
    t2 = json.load(open(os.path.join(famdir("W1", "T2"), "result.json")))
    sym_ok = (n837 == 837 and fin["dimU"] == t2["final"]["dimU"]
              and fin["ell_m3"] == t2["final"]["ell_m3"])
    ok = ok_all and m3_ok and p3_ok and inv_ok and img_ok and sym_ok and S.a3v == 0
    d = famdir("W1", "ctl-C6")
    write_result(os.path.join(d, "result.json"), {
        "amendment": 2, "web": "W1", "family": "ctl-C6", "n_aut": sum(1 for a in auts if a[2]),
        "F0_m3_images_in_U0": m3_ok, "F0_3_images_in_A3": p3_ok, "beta_invariant": inv_ok,
        "image_foams_match": img_ok,
        "sym_check": {"s0_members": n837, "novel": len(S.novel), "aut_novel": len(S.aut_novel),
                      "final": fin, "T2_final": t2["final"]},
        "pass": ok})
    clock.mark("main")
    clock.runjson(os.path.join(d, "run.json"))
    print(json.dumps({"control": "C6", "pass": ok, "sym": fin, "T2": t2["final"]}), flush=True)
    if not ok:
        raise AssertionError("C6 failed")


def run_union(st, ellq_f0):
    """A2.7 step 4: order KM, T2R, T2, T3s, then the optional families that ran (T3)."""
    S = Search(st)
    rows = []
    order = ["KM", "T2R", "T2", "T3s"] + [f for f in ("T3",) if os.path.exists(
        os.path.join(famdir("W1", f), "result.json"))]
    for fam in order:
        p = os.path.join(famdir("W1", fam), "novel.jsonl")
        for line in open(p):
            o = json.loads(line)
            a = gf4.from_codes([int(c) for c in o["a"]])
            before = len(S.novel_items)
            S.process(a, o["deg"], o["i"], o["g"])
            if len(S.novel_items) > before:
                rows.append([fam, o["i"], o["g"], o["deg"], len(S.U), len(S.P)])
            if S.stop:
                break
        if S.stop:
            break
    write_result(os.path.join(OUT, "W1", "A2", "union.json"), {
        "amendment": 2, "web": "W1", "family": "union", "order": order,
        "novel": rows, "a3_violations": S.a3v, "start": st.start(), "final": S.final(ellq_f0),
        "stop": S.stop or "EXHAUSTED"})
    print(json.dumps({"union": S.final(ellq_f0), "stop": S.stop or "EXHAUSTED"}), flush=True)


def run_summary():
    """Controls C1-C3 summary, ledger of CPU/wall seconds, SHA-256 of every
    Phase 2b output file.  Not a compared file."""
    res = {}
    for fam in MANDATORY:
        res[fam] = json.load(open(os.path.join(famdir("W1", fam), "result.json")))
    c1 = all(r["a3_violations"] == 0 for r in res.values())
    c2 = res["T2R"]["novel"] == [] and res["T2R"]["aut_novel"] == []
    ctl = {}
    for web, name in [("W1", "ctl-C0"), ("prism5", "ctl-C4"), ("cube", "ctl-C4"),
                      ("W2", "ctl-C5"), ("W3", "ctl-C5"), ("W1", "ctl-C6")]:
        ctl["%s/%s" % (web, name)] = json.load(open(os.path.join(famdir(web, name),
                                                                  "result.json")))["pass"]
    ledger = {}
    sums = []
    for root, dirs, files in sorted(os.walk(OUT)):
        dirs.sort()
        if os.sep + "A2" not in root + os.sep and not root.endswith("A2"):
            continue
        for f in sorted(files):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, OUT).replace(os.sep, "/")
            if "/A2/" not in "/" + rel:
                continue
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            sums.append("%s  %s\n" % (h, rel))
            if f == "run.json":
                ledger[os.path.dirname(rel)] = json.load(open(p))["phases"]
    summary = {
        "C1_zero_A3_violations": c1, "C2_T2R_no_novel": c2,
        "C3_counts": "asserted in every run (a mismatch aborts the run)",
        "controls": ctl,
        "stops": {f: r["stop"] for f, r in res.items()},
        "final": {f: r["final"] for f, r in res.items()},
        "novel": {f: [len(r["novel"]), len(r["aut_novel"])] for f, r in res.items()},
        "ledger_seconds": ledger}
    with open(os.path.join(OUT, "A2-summary.json"), "w", newline="\n") as fh:
        fh.write(json.dumps(summary, sort_keys=True, indent=1) + "\n")
    with open(os.path.join(OUT, "A2-SHA256SUMS.txt"), "w", newline="\n") as fh:
        fh.writelines(sums)
    ok = c1 and c2 and all(ctl.values())
    print(json.dumps({"summary_ok": ok, "C1": c1, "C2": c2, "controls": ctl}), flush=True)
    return ok


# ------------------------------------------------------------------ driver
def f0_setup(check_phase2=False):
    st = F0State(check_phase2)
    r = analyse((it[4], it[2]) for it in st.items)
    if r["ell"] == 60:
        raise SystemExit("l(F0) = 60: the question is decided (A2.7 step 1); stopping")
    if r["ell_q"] != P2_ELLQ or r["r_q"] != P2_RQ:
        raise SystemExit("F0 l_q or r_q differs from [P2]: stop and ask (A2.7 step 1)")
    s = st.start()
    assert s == {"dimU": 9, "dimA3": 20, "dimR": 11, "ell_m3": 9}, s
    assert s["dimU"] == r["r_q"][-3] and s["dimA3"] == r["r_q"][-3] + r["r_q"][3]
    assert s["ell_m3"] == r["ell_q"][3]
    return st, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family")
    ap.add_argument("--control")
    ap.add_argument("--union", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--first-limit", type=int, default=None,
                    help="T3 test runs only: the first N first moves")
    args = ap.parse_args()
    if args.family == "T4s":
        sys.exit("T4s is not run (A2.13 item 2; only T3 has Gabriel's go)")
    if args.family == "T3":
        if not 1 <= args.jobs <= 8:
            sys.exit("T3: --jobs must be 1..8 (at most 8 worker processes)")
        st, r = f0_setup()
        run_t3(st, r["ell_q"], args.jobs, args.first_limit)
        return
    if args.summary:
        sys.exit(0 if run_summary() else 1)
    if args.control and args.control.startswith(("C4", "C5")):
        run_c45(args.control)
        return
    if args.family or args.control or args.union:
        st, r = f0_setup(check_phase2=(args.family == "F0"))
        if args.family == "F0":
            run_f0(st, r["ell_q"], r)
        elif args.family:
            family_main(args.family, st, r["ell_q"])
        elif args.control == "C0":
            run_c0(st, r)
        elif args.control == "C6":
            run_c6(st, r["ell_q"])
        elif args.union:
            run_union(st, r["ell_q"])
        return
    if args.all:
        t0 = time.time()
        jobs = [["--family", f] for f in MANDATORY] + \
               [["--control", c] for c in CONTROLS if c not in ("C6", "C8")]
        running = []
        failed = []
        while jobs or running:
            while jobs and len(running) < args.jobs:
                j = jobs.pop(0)
                running.append((j, subprocess.Popen([sys.executable, os.path.abspath(__file__)] + j)))
            time.sleep(1)
            for jr in list(running):
                if jr[1].poll() is not None:
                    running.remove(jr)
                    if jr[1].returncode != 0:
                        failed.append(jr[0])
        for extra in (["--control", "C6"], ["--union"], ["--summary"]):
            if subprocess.call([sys.executable, os.path.abspath(__file__)] + extra) != 0:
                failed.append(extra)
        print(json.dumps({"all_wall_s": round(time.time() - t0, 1), "failed": failed}), flush=True)
        if failed:
            sys.exit(1)


if __name__ == "__main__":
    main()
