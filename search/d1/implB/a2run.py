#!/usr/bin/env python3
"""SPEC Amendment 2 (Phase 2b), Implementation B.

  python3 a2run.py all --jobs 8            controls, then F0 KM KMd T2R T2 T3s, then union
  python3 a2run.py family T2 --jobs 8      one family (F0 is recomputed as the start state)
  python3 a2run.py family T3 --jobs 8 --prior DIR
                                           optional family T3 (SPEC A2.5), then the union
                                           with T3 after T3s (prior families read from DIR)
  python3 a2run.py control C4 --jobs 8     one control (C0 C3 C4 C5 C6 C8)

Outputs under results/<web>/A2/... (SPEC A2.8).  h.jsonl files are written to
--hdir (default: results tree) and are not meant to be committed.
"""

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import resource
except ImportError:
    resource = None

from core import tait_colourings, hex_to_packed, gen, scale_pair   # noqa: E402,F401
from webs import get_web, TARGETS                                    # noqa: E402
import a2tree as TR                                                  # noqa: E402
import ranks                                                         # noqa: E402
import km                                                            # noqa: E402

IMPL = "B (Mode T: transfer matrices), search/d1/implB"
S0_SITE = ("unzip", 0, 0, 1)

FAMILIES = {
    "F0": dict(web="W1", policies=["emit"], unit=0, restrict=None, retain="all"),
    "T2R": dict(web="W1", policies=["expand:REDUCIBLE", "emit"], unit=1, restrict=None, retain="RET"),
    "T2": dict(web="W1", policies=["expand:IRREDUCIBLE", "emit"], unit=1, restrict=None, retain="RET"),
    "T3s": dict(web="W1", policies=["expand:IRREDUCIBLE", "expand:IRREDUCIBLE", "emit"], unit=2,
                restrict=S0_SITE, retain="RET"),
    # optional (Gabriel's go, 2026-09-30): T3s without the symmetry reduction, all 60 bigon
    # moves as M1; no Aut closure.  Units are the level-2 nodes (5,220), in DFS order.
    "T3": dict(web="W1", policies=["expand:IRREDUCIBLE", "expand:IRREDUCIBLE", "emit"], unit=2,
               restrict=None, retain="RET"),
    # control C6 symmetry check: T2 restricted to M1 = s0
    "T2s0": dict(web="W1", policies=["expand:IRREDUCIBLE", "emit"], unit=1, restrict=S0_SITE, retain="RET"),
    # controls C4, C5
    "C4-prism5": dict(web="prism5", policies=["expand:REDUCIBLE", "emit"], unit=1, restrict=None, retain="all"),
    "C4-cube": dict(web="cube", policies=["expand:REDUCIBLE", "emit"], unit=1, restrict=None, retain="all"),
    "C5-W2": dict(web="W2", policies=["expand:IRREDUCIBLE", "emit"], unit=1, restrict=None, retain="m5m3"),
    "C5-W3": dict(web="W3", policies=["expand:IRREDUCIBLE", "emit"], unit=1, restrict=None, retain="m5m3"),
}

# SPEC A2.5 / A2.9 expected count-only numbers  (level -> (precond, bridge, irreducible, reducible))
EXPECTED = {
    "F0": dict(levels={1: (0, 60, 60, 180)}, leaves=11880,
               hist={-3: 810, -1: 2610, 1: 3780, 3: 3150, 5: 1350, 7: 180}),
    "T2R": dict(levels={2: (240, 12660, 720, 45120)}, expanded={1: 180}, leaves=4190400, retained=107430,
                per_kind={2: {"zip": (120, 660, 60, 4650), "unzip": (0, 120, 450, 23310),
                              "saddle": (0, 11880, 180, 11820), "ih": (120, 0, 30, 5340)}}),
    "T2": dict(levels={2: (240, 4260, 5220, 11400)}, expanded={1: 60}, leaves=1499040, retained=50220,
               per_kind={2: {"zip": (120, 0, 120, 1740), "unzip": (0, 120, 4620, 3840),
                             "saddle": (0, 4140, 360, 4080), "ih": (120, 0, 120, 1740)}}),
    "T3s": dict(levels={3: (548, 6974, 9508, 17362)}, expanded={1: 1, 2: 87}, leaves=4085832,
                retained=61927),
    # level 3 and totals from the A2.5 T3 row; levels 1-2 are the F0 / T2 site outcomes (same sites);
    # per_m1: every one of the 60 first moves gives the T3s numbers.
    "T3": dict(levels={1: (0, 60, 60, 180), 2: (240, 4260, 5220, 11400),
                       3: (32880, 418440, 570480, 1041720)},
               expanded={1: 60, 2: 5220}, leaves=245149920, retained=3715620,
               per_m1=dict(n=60, units=87, level=3, outcomes=(548, 6974, 9508, 17362),
                           leaves=4085832, retained=61927)),
    "T2s0": dict(levels={2: (4, 71, 87, 190)}, expanded={1: 1}, retained=837),
    "C4-prism5": dict(levels={2: (320, 4290, 0, 10950)}, expanded={1: 100}, leaves=566700),
    "C4-cube": dict(levels={2: (288, 2532, 0, 5748)}, expanded={1: 72}, leaves=250056),
    "C5-W2": dict(levels={2: (288, 5976, 7152, 17208)}, expanded={1: 72}, leaves=4603104,
                  retained_hist={-5: 14232, -3: 147216}),
    "C5-W3": dict(levels={2: (336, 8532, 10520, 25316)}, expanded={1: 90}, leaves=8835096,
                  retained_hist={-5: 8444, -3: 159612}),
}

NOT_IMPLEMENTED = {"T4s": "T4s is not implemented (optional; no go from Gabriel)"}
H_MAX = 2000000          # A2.8: above this many processed members h.jsonl is not written
M1_LIMIT = None          # test option: restrict a tree family to its first K level-1 expansions

P2_ELLQ = {-3: 9, -1: 20, 1: 20, 3: 9}
P2_RQ = {-3: 9, -1: 20, 1: 20, 3: 11}
B19_NE = None


def retain_fn(key):
    if key == "all":
        return lambda d: True
    if key == "RET":
        return lambda d: d <= -3 and (d - 3) % 6 == 0
    if key == "m5m3":
        return lambda d: d in (-5, -3)
    raise KeyError(key)


def is_ret(d):
    return d <= -3 and (d - 3) % 6 == 0


def dumps(obj):
    return json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=True) + "\n"


def smap(d):
    return {str(k): v for k, v in sorted(d.items()) if v}


def peak_rss_mb():
    if resource is None:
        return 0.0
    a = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    b = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return max(a, b) / 1024.0


def cpu_seconds():
    t = os.times()
    return t.user + t.system + t.children_user + t.children_system


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- GF(2) spaces
class F2Space:
    """F-span of int bit-vectors; basis keyed by highest bit."""

    def __init__(self):
        self.b = {}

    def reduce(self, x):
        b = self.b
        while x:
            h = x.bit_length() - 1
            y = b.get(h)
            if y is None:
                return x
            x ^= y
        return 0

    def contains(self, x):
        return self.reduce(x) == 0

    def add(self, x):
        x = self.reduce(x)
        if x == 0:
            return False
        self.b[x.bit_length() - 1] = x
        return True

    def __len__(self):
        return len(self.b)


def fview(v, T):
    return v[0] | (v[1] << T)


# ---------------------------------------------------------------- workers
_G = {}


def _init(webname):
    K = get_web(webname)
    _G["K"] = K
    _G["S"] = tait_colourings(K)


def _unit_job(args):
    fam, path, mode = args
    spec = FAMILIES[fam]
    K = _G["K"]
    u = spec["unit"]
    retain = retain_fn(spec["retain"])
    cnt = TR.new_counts()
    if mode == "count":
        Ku, _, _, deg, moves = TR.descend(K, path, None)
        TR.walk(Ku, spec["policies"], u, cnt, retain, None, None,
                spec["restrict"] if u == 0 else None, None, moves, deg)
        return cnt, None
    Ku, Su, chain, deg, moves = TR.descend(K, path, _G["S"])
    out = []
    TR.walk(Ku, spec["policies"], u, cnt, retain, Su, chain,
            spec["restrict"] if u == 0 else None, out, moves, deg)
    return cnt, out


class BudgetExceeded(Exception):
    pass


class Monitor:
    """Samples the summed RSS of this process and its pool workers, and enforces
    the A2.10 budget (CPU and wall of a pass) when given."""

    def __init__(self, cpu_budget=None, wall_budget=None):
        self.t0 = time.time()
        t = os.times()
        self.self_cpu0 = t.user + t.system
        self.cpu_budget = cpu_budget
        self.wall_budget = wall_budget
        self.peak_total_rss_mb = 0.0
        self.worker_cpu = 0.0
        try:
            self.tick = os.sysconf("SC_CLK_TCK")
        except (ValueError, AttributeError, OSError):
            self.tick = 100

    @staticmethod
    def _rss_kb(pid):
        try:
            with open("/proc/%d/status" % pid) as fh:
                for line in fh:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1])
        except OSError:
            pass
        return 0

    def _cpu(self, pid):
        try:
            with open("/proc/%d/stat" % pid) as fh:
                f = fh.read().rsplit(")", 1)[1].split()
            return (int(f[11]) + int(f[12])) / self.tick
        except (OSError, IndexError, ValueError):
            return 0.0

    def check(self, pids):
        if not os.path.exists("/proc/self/status"):
            return
        rss = self._rss_kb(os.getpid()) + sum(self._rss_kb(p) for p in pids)
        self.peak_total_rss_mb = max(self.peak_total_rss_mb, rss / 1024.0)
        self.worker_cpu = sum(self._cpu(p) for p in pids)
        t = os.times()
        cpu = t.user + t.system - self.self_cpu0 + self.worker_cpu
        wall = time.time() - self.t0
        if self.cpu_budget is not None and cpu > self.cpu_budget:
            raise BudgetExceeded("CPU %.0f s > budget %.0f s (wall %.0f s)" % (cpu, self.cpu_budget, wall))
        if self.wall_budget is not None and wall > self.wall_budget:
            raise BudgetExceeded("wall %.0f s > budget %.0f s (CPU %.0f s)" % (wall, self.wall_budget, cpu))


def run_units(fam, units, mode, jobs, monitor=None):
    """Yields unit results in order.  At most 4*jobs units are in flight, so
    finished-but-unconsumed results stay bounded."""
    spec = FAMILIES[fam]
    args = [(fam, p, mode) for p in units]
    if jobs <= 1:
        _init(spec["web"])
        for n, a in enumerate(args, 1):
            if monitor is not None and n % 10 == 0:
                monitor.check([])
            yield _unit_job(a)
        return
    import multiprocessing as mp
    from collections import deque
    ctx = mp.get_context("fork")
    pool = ctx.Pool(jobs, initializer=_init, initargs=(spec["web"],))
    try:
        it = iter(args)
        window = deque()
        for a in it:
            window.append(pool.apply_async(_unit_job, (a,)))
            if len(window) >= 4 * jobs:
                break
        n = 0
        while window:
            r = window.popleft().get()
            nxt = next(it, None)
            if nxt is not None:
                window.append(pool.apply_async(_unit_job, (nxt,)))
            n += 1
            if monitor is not None and n % 10 == 0:
                monitor.check([p.pid for p in pool._pool])
            yield r
        if monitor is not None:
            monitor.check([p.pid for p in pool._pool])
    finally:
        pool.terminate()
        pool.join()


LAST_UNIT_COUNTS = {}


def limit_units(units):
    """M1_LIMIT (test option, T3 only): keep the units below the first K level-1 expansions."""
    if M1_LIMIT is None:
        return units
    firsts = []
    for p in units:
        if p[0] not in firsts:
            firsts.append(p[0])
    keep = firsts[:M1_LIMIT]
    return [p for p in units if p[0] in keep]


def count_pass(fam, jobs, monitor=None):
    spec = FAMILIES[fam]
    K = get_web(spec["web"])
    units, cnt = TR.enumerate_units(K, spec["policies"], spec["unit"], spec["restrict"])
    if fam in BUDGETED:
        units = limit_units(units)
    per = []
    gen_ = run_units(fam, units, "count", jobs, monitor)
    try:
        for c, _ in gen_:
            per.append(c)
            TR.merge_counts(cnt, c)
    finally:
        gen_.close()
    LAST_UNIT_COUNTS[fam] = per
    return units, cnt


def check_expected(fam, cnt):
    exp = EXPECTED.get(fam)
    msgs = []
    if exp is None:
        return True, msgs
    ok = True
    for lv, tup in exp.get("levels", {}).items():
        got = cnt["sites"].get(lv, {})
        tot = tuple(sum(got[k][o] for k in TR.KINDS) for o in TR.OUTCOMES) if got else None
        if tot != tup:
            ok = False
            msgs.append("level %d outcomes %r != %r" % (lv, tot, tup))
    for lv, kinds in exp.get("per_kind", {}).items():
        for k, tup in kinds.items():
            got = tuple(cnt["sites"][lv][k][o] for o in TR.OUTCOMES)
            if got != tup:
                ok = False
                msgs.append("level %d %s %r != %r" % (lv, k, got, tup))
    for lv, n in exp.get("expanded", {}).items():
        if cnt["expanded"].get(lv) != n:
            ok = False
            msgs.append("expanded level %d %r != %r" % (lv, cnt["expanded"].get(lv), n))
    if "leaves" in exp and sum(cnt["leaves"].values()) != exp["leaves"]:
        ok = False
        msgs.append("leaves %d != %d" % (sum(cnt["leaves"].values()), exp["leaves"]))
    if "retained" in exp and sum(cnt["retained"].values()) != exp["retained"]:
        ok = False
        msgs.append("retained %d != %d" % (sum(cnt["retained"].values()), exp["retained"]))
    if "hist" in exp and cnt["leaves"] != exp["hist"]:
        ok = False
        msgs.append("hist %r" % cnt["leaves"])
    if "retained_hist" in exp and cnt["retained"] != exp["retained_hist"]:
        ok = False
        msgs.append("retained hist %r" % cnt["retained"])
    return ok, msgs


def per_m1_check(fam, units, per):
    """T3: every first move has the T3s subtree numbers (A2.5, A2.9 C3)."""
    exp = EXPECTED.get(fam, {}).get("per_m1")
    if exp is None:
        return True, [], None
    lv = exp["level"]
    groups = {}
    order = []
    for p, c in zip(units, per):
        key = tuple(p[0])
        if key not in groups:
            groups[key] = TR.new_counts()
            order.append(key)
        TR.merge_counts(groups[key], c)
    ok = True
    msgs = []
    sig = {}
    for key in order:
        g = groups[key]
        got = g["sites"].get(lv, {})
        tot = tuple(sum(got[k][o] for k in TR.KINDS) for o in TR.OUTCOMES) if got else None
        s_ = (tot, g["expanded"].get(lv - 1, 0), sum(g["leaves"].values()), sum(g["retained"].values()))
        sig.setdefault(s_, []).append(list(key))
    want = (tuple(exp["outcomes"]), exp["units"], exp["leaves"], exp["retained"])
    if len(order) != exp["n"]:
        ok = False
        msgs.append("first moves %d != %d" % (len(order), exp["n"]))
    for s_, keys in sig.items():
        if s_ != want:
            ok = False
            msgs.append("first moves %r: %r != %r" % (keys[:3], s_, want))
    summary = {"first_moves": len(order),
               "signatures": sorted([list(s_[0]) + [s_[1], s_[2], s_[3], len(k)] for s_, k in sig.items()])}
    return ok, msgs, summary


def sites_json(cnt):
    return {str(lv): {k: {o: kinds[k][o] for o in TR.OUTCOMES} for k in TR.KINDS}
            for lv, kinds in sorted(cnt["sites"].items())}


# ---------------------------------------------------------------- the F0 state (A2.7 step 1)
class State:
    """Spans of A2.7, built from F0."""

    def __init__(self, f0_degs, f0_vecs, T):
        self.T = T
        self.f0_m3 = [v for d, v in zip(f0_degs, f0_vecs) if d == -3]
        self.f0_3 = [v for d, v in zip(f0_degs, f0_vecs) if d == 3]
        self.f0_3_index = [i + 1 for i, d in enumerate(f0_degs) if d == 3]
        # C3: GF(4)-greedy independent F0_3 members, in F0 order
        ech = ranks.Echelon()
        self.C3 = []
        self.C3_index = []
        for idx, v in zip(self.f0_3_index, self.f0_3):
            if ech.add(v):
                self.C3.append(v)
                self.C3_index.append(idx)
        self.A3 = F2Space()
        for v in self.f0_m3 + self.f0_3:
            self.A3.add(fview(v, T))
        self.U = F2Space()
        self.U0_basis = []
        for v in self.f0_m3:
            if self.U.add(fview(v, T)):
                self.U0_basis.append(v)
        self.P = F2Space()
        for v in self.f0_m3:
            self.P.add(self.p(v))
        # dim R = dim A3 - rank(pairing of an F-basis of A3 with an F-basis of U0)
        a3b = []
        sp = F2Space()
        for v in self.f0_m3 + self.f0_3:
            if sp.add(fview(v, T)):
                a3b.append(v)
        rows = []
        for v in a3b:
            x = 0
            for k, w in enumerate(self.U0_basis):
                if ranks.beta_F(v, w):
                    x |= 1 << k
            rows.append(x)
        self.dimR = len(a3b) - ranks.gf2_rank(rows)
        self.novel_m3 = []          # novel degree -3 vectors (members and images)
        self.start = {"dimU": len(self.U), "dimA3": len(self.A3), "dimR": self.dimR,
                      "ell_m3": len(self.P)}

    def p(self, v):
        x = 0
        for j, c in enumerate(self.C3):
            if ranks.beta_F(v, c):
                x |= 1 << j
        return x

    def process(self, v, deg):
        """A2.7 step 2 items 1-3.  Returns (status, novel) with status in
        None / 'A3_VIOLATION' / 'ELL60' / 'DIMU11'."""
        fv = fview(v, self.T)
        if not self.A3.contains(fv):
            return "A3_VIOLATION", False
        if not self.U.add(fv):
            return None, False
        for h in self.f0_m3:
            assert ranks.beta(v, h) == 0, "novel member pairs nonzero with F0_-3"
        if deg == -3:
            self.P.add(self.p(v))
            self.novel_m3.append(v)
        if len(self.P) == 10:
            return "ELL60", True
        if len(self.U) == 11:
            return "DIMU11", True
        return None, True

    def final(self, ell_m1, ell_1):
        """A2.7 step 3: recompute ell_-3 and ell_3 from scratch."""
        allm3 = self.f0_m3 + self.novel_m3
        em3 = ranks.gf2_rank([self.p(v) for v in allm3])
        cols = ranks.independent_subset(allm3)
        e3 = ranks.pairing_rank(self.f0_3, cols)
        assert e3 == em3, "ell_3 != ell_-3"
        assert em3 == len(self.P)
        return {"dimU": len(self.U), "ell_m3": em3, "ell_3": e3, "ell": em3 + ell_m1 + ell_1 + e3}


def automorphisms(K):
    """SPEC A2.6: list of dart maps g (index 0 = identity)."""
    nd = 3 * K.V
    a = K.alpha

    def sig(d, eps):
        return 3 * (d // 3) + ((d % 3) + (1 if eps > 0 else 2)) % 3
    out = []
    for dstar in range(nd):
        for eps in (1, -1):
            g = [None] * nd
            g[0] = dstar
            stack = [0]
            ok = True
            while stack and ok:
                x = stack.pop()
                for y, gy in ((a[x], a[g[x]]), (3 * (x // 3) + ((x % 3) + 1) % 3, sig(g[x], eps))):
                    if g[y] is None:
                        g[y] = gy
                        stack.append(y)
                    elif g[y] != gy:
                        ok = False
                        break
            if ok and None not in g and len(set(g)) == nd:
                out.append(g)
    return out


def aut_perms(K, tait):
    """For each automorphism g, the permutation pi with (g.a)[s] = a[pi[s]]."""
    idx = {t: i for i, t in enumerate(tait)}
    perms = []
    for g in automorphisms(K):
        ghat = [K.eidx[g[K.edge_ids[j]]] for j in range(K.E)]
        pi = []
        for s in tait:
            pi.append(idx[tuple(s[ghat[e]] for e in range(K.E))])
        perms.append(pi)
    return perms


def act(pi, v):
    lo, hi = v
    nlo = nhi = 0
    for s, p in enumerate(pi):
        nlo |= ((lo >> p) & 1) << s
        nhi |= ((hi >> p) & 1) << s
    return nlo, nhi


# ---------------------------------------------------------------- F0
def run_F0(jobs, hdir, log):
    fam = "F0"
    t0, c0 = time.time(), cpu_seconds()
    units, ccnt = count_pass(fam, jobs)
    t1, c1 = time.time(), cpu_seconds()
    okc, msgs = check_expected(fam, ccnt)
    K = get_web("W1")
    tait = tait_colourings(K)
    T = len(tait)
    cnt = TR.new_counts()
    degs, vecs, lines = [], [], []
    for c, out in run_units(fam, [[]], "main", 1):
        TR.merge_counts(cnt, c)
        for i, (moves, chain, d, hx) in enumerate(out, 1):
            degs.append(d)
            vecs.append(hex_to_packed(hx))
            lines.append(json.dumps({"i": i, "site": moves[0], "chain": chain, "deg": d, "a": hx}) + "\n")
    t2, c2 = time.time(), cpu_seconds()
    return dict(fam=fam, units=units, ccnt=ccnt, cnt=cnt, okc=okc, msgs=msgs, T=T, tait=tait,
                degs=degs, vecs=vecs, lines=lines, times=(t0, t1, t2, c0, c1, c2))


def f0_state(F0res, log):
    degs, vecs, T = F0res["degs"], F0res["vecs"], F0res["T"]
    R = ranks.compute_all(degs, vecs, T)
    if R["ell"] == 60:
        raise SystemExit("ell(F0) = 60: the question is decided; stop (A2.7 step 1)")
    if R["ell_q"] != P2_ELLQ or R["r_q"] != P2_RQ:
        raise SystemExit("F0 ranks differ from [P2]: ell_q %r r_q %r; stop and ask" % (R["ell_q"], R["r_q"]))
    st = State(degs, vecs, T)
    assert st.start == {"dimU": 9, "dimA3": 20, "dimR": 11, "ell_m3": 9}, st.start
    return R, st


def write_h(path, lines_iter):
    h = hashlib.sha256()
    n = 0
    with open(path, "w", newline="\n") as fh:
        for line in lines_iter:
            fh.write(line)
            h.update(line.encode("ascii"))
            n += 1
    return h.hexdigest(), n


def pairsample_lines(nret, degs_vecs_get, st, novel_members):
    """A2.7 direct-evaluation sample; returns list of lines."""
    out = []
    n3 = len(st.f0_3)
    for k in range(1, min(1000, nret) + 1):
        i = 1 + (7919 * k) % nret
        jj = (104729 * k) % n3
        v = degs_vecs_get(i)
        val = ranks.beta(v, st.f0_3[jj])
        assert val in (0, 1)
        out.append("%d\t%d\t%d\n" % (i, st.f0_3_index[jj], val))
    for i, v in novel_members:
        for idx, c in zip(st.C3_index, st.C3):
            val = ranks.beta(v, c)
            assert val in (0, 1)
            out.append("%d\t%d\t%d\n" % (i, idx, val))
    return out


def write_run_json(d, info):
    with open(os.path.join(d, "run.json"), "w", newline="\n") as fh:
        fh.write(dumps(info))


def base_run_info(command, jobs, times, extra=None):
    t0, t1, t2, c0, c1, c2 = times[:6]
    info = {"implementation": IMPL, "command": command, "git_commit": "unknown",
            "machine": platform.node() + " " + platform.platform(),
            "python": platform.python_version(),
            "workers": jobs,
            "count_pass": {"wall_s": round(t1 - t0, 2), "cpu_s": round(c1 - c0, 2)},
            "main_pass": {"wall_s": round(t2 - t1, 2), "cpu_s": round(c2 - c1, 2)},
            "peak_rss_mb": round(peak_rss_mb(), 1)}
    if extra:
        info.update(extra)
    return info


# ---------------------------------------------------------------- family processing
BUDGETED = ("T3",)       # families whose main pass is stopped at 3x its estimate (A2.10)
MAX_RUN_WALL_S = 4 * 3600 - 600   # A2.13: no single run over 4 h (10 min margin)


class VecStore:
    """Compact store of packed a-vectors (2T bits each), 1-based."""

    def __init__(self, T):
        self.T = T
        self.nb = (2 * T + 7) // 8
        self.buf = bytearray()

    def append(self, v):
        self.buf += (v[0] | (v[1] << self.T)).to_bytes(self.nb, "little")

    def get(self, i):
        x = int.from_bytes(self.buf[(i - 1) * self.nb:i * self.nb], "little")
        return x & ((1 << self.T) - 1), x >> self.T


def process_family(fam, F0res, R0, st, jobs, root, hdir, command, log, st_factory,
                   count_only=False, hprefix=None):
    """Tree family on W1 (T2R, T2, T3s, T3, T2s0).

    count_only: stop after the count-only pass (returns None).
    hprefix: also write the first hprefix h lines to <hdir>/W1-A2-<fam>-h-prefix<N>.jsonl.
    h.jsonl itself is written only if the family has at most H_MAX retained members (A2.8);
    its SHA-256 is always computed on the fly, in order."""
    spec = FAMILIES[fam]
    started = utcnow()
    t0, c0 = time.time(), cpu_seconds()
    mon_c = Monitor()
    units, ccnt = count_pass(fam, jobs, mon_c)
    t1, c1 = time.time(), cpu_seconds()
    okc, msgs = check_expected(fam, ccnt)
    okm, msgs_m, m1sum = per_m1_check(fam, units, LAST_UNIT_COUNTS[fam])
    okc, msgs = okc and okm, msgs + msgs_m
    nleaves = sum(ccnt["leaves"].values())
    nret = sum(ccnt["retained"].values())
    est = nleaves * 45e-6
    est_wall = est / max(1, min(jobs, 4))
    log("  %s count-only: %.1fs wall %.1fs CPU; units %d; leaves %d retained %d; C3 %s %s; "
        "main-pass estimate %.0f CPU s (~%.0f s wall); peak total RSS %.0f MB"
        % (fam, t1 - t0, c1 - c0, len(units), nleaves, nret, "ok" if okc else "MISMATCH", msgs, est,
           est_wall, mon_c.peak_total_rss_mb))
    if m1sum is not None:
        log("  %s per-first-move signatures [precond, bridge, irreducible, reducible, L2 nodes, "
            "leaves, retained, #first moves]: %s" % (fam, m1sum["signatures"]))
    if count_only:
        return None
    if fam in BUDGETED and not okc and M1_LIMIT is None:
        raise SystemExit("%s: count-only numbers differ from A2.5 (%s); main pass not run" % (fam, msgs))
    S = st_factory()
    d = os.path.join(root, "W1", "A2", fam)
    os.makedirs(d, exist_ok=True)
    os.makedirs(hdir, exist_ok=True)
    hpath = os.path.join(hdir, "W1-A2-%s-h.jsonl" % fam) if nret <= H_MAX else None
    h = hashlib.sha256()
    fh = open(hpath, "w", newline="\n") if hpath else None
    ppath = os.path.join(hdir, "W1-A2-%s-h-prefix%d.jsonl" % (fam, hprefix)) if hprefix else None
    pfh = open(ppath, "w", newline="\n") if ppath else None
    cnt = TR.enumerate_units(get_web(spec["web"]), spec["policies"], spec["unit"], spec["restrict"])[1]
    i = 0
    stop = None
    a3v = 0
    novel = []
    novel_members = []
    allv = VecStore(F0res["T"])
    m1_dig = []              # per first move: [label, first i, lines, sha256]
    cur_m1, m1h, m1_first = None, None, 0
    cpu_budget = wall_budget = None
    if fam in BUDGETED:
        cpu_budget = 3 * est
        wall_budget = min(3 * est_wall, MAX_RUN_WALL_S - (t1 - t0))
        log("  %s main-pass stop thresholds: CPU %.0f s, wall %.0f s" % (fam, cpu_budget, wall_budget))
    mon = Monitor(cpu_budget, wall_budget)
    gen_ = run_units(fam, units, "main", jobs, mon)
    try:
        for c, out in gen_:
            TR.merge_counts(cnt, c)
            for moves, chain, dg, hx in out:
                i += 1
                line = json.dumps({"i": i, "moves": moves, "chain": chain, "deg": dg, "a": hx}) + "\n"
                if fh:
                    fh.write(line)
                if pfh and i <= hprefix:
                    pfh.write(line)
                lb = line.encode("ascii")
                h.update(lb)
                if moves[0] != cur_m1:
                    if cur_m1 is not None:
                        m1_dig.append([cur_m1, m1_first, i - m1_first, m1h.hexdigest()])
                    cur_m1, m1h, m1_first = moves[0], hashlib.sha256(), i
                m1h.update(lb)
                v = hex_to_packed(hx)
                allv.append(v)
                status, isnov = S.process(v, dg)
                if status == "A3_VIOLATION":
                    a3v += 1
                    stop = status
                    break
                if isnov:
                    novel.append([i, dg, len(S.U), len(S.P)])
                    novel_members.append((i, v))
                if status in ("ELL60", "DIMU11"):
                    stop = status
                    break
            if stop:
                break
    except BudgetExceeded as e:
        gen_.close()
        t2, c2 = time.time(), cpu_seconds()
        msg = "%s main pass stopped by the A2.10 budget after %d members: %s" % (fam, i, e)
        log("  !!! " + msg)
        info = base_run_info(command, jobs, (t0, t1, t2, c0, c1, c2),
                             {"family": fam, "start_utc": started, "end_utc": utcnow(),
                              "aborted": msg, "estimate_cpu_s": round(est, 1),
                              "peak_total_rss_mb_sampled": {"count": round(mon_c.peak_total_rss_mb, 1),
                                                            "main": round(mon.peak_total_rss_mb, 1)}})
        write_run_json(d, info)
        raise SystemExit(msg)
    gen_.close()
    if cur_m1 is not None:
        m1_dig.append([cur_m1, m1_first, i + 1 - m1_first, m1h.hexdigest()])
    if fh:
        fh.close()
    if pfh:
        pfh.close()
    processed = i
    aut_novel = []
    if stop is None and fam in ("T3s", "T2s0"):
        K = get_web("W1")
        perms = aut_perms(K, F0res["tait"])
        assert len(perms) == 120
        for (ii, v), rec in zip(list(novel_members), list(novel)):
            dg = rec[1]
            for g in range(1, 120):
                gv = act(perms[g], v)
                status, isnov = S.process(gv, dg)
                if status == "A3_VIOLATION":
                    a3v += 1
                    stop = status
                    break
                if isnov:
                    aut_novel.append([ii, g, dg, len(S.U), len(S.P)])
                if status in ("ELL60", "DIMU11"):
                    stop = status
                    break
            if stop:
                break
    if stop is None:
        stop = "EXHAUSTED"
        # main-pass counts must equal the count-only pass
        assert cnt == ccnt, "main pass counts differ from count-only pass"
    t2, c2 = time.time(), cpu_seconds()
    fin = S.final(R0["ell_q"].get(-1, 0), R0["ell_q"].get(1, 0))
    res = {"amendment": 2, "web": "W1", "family": fam,
           "sites": sites_json(ccnt),
           "expanded_nodes": {str(k): v for k, v in sorted(ccnt["expanded"].items())},
           "leaves_by_degree": smap(ccnt["leaves"]), "N_leaves": nleaves, "N_retained": nret,
           "processed": processed, "h_sha256": h.hexdigest(), "a3_violations": a3v,
           "novel": novel, "aut_novel": aut_novel, "start": S.start, "final": fin, "stop": stop}
    with open(os.path.join(d, "result.json"), "w", newline="\n") as f:
        f.write(dumps(res))
    # pair sample
    lines = pairsample_lines(processed, allv.get, S, novel_members) if processed else []
    with open(os.path.join(d, "pairsample.tsv"), "w", newline="\n") as f:
        f.writelines(lines)
    if stop in ("ELL60", "DIMU11"):
        log("  !!! %s stop fired in %s: certificate needed" % (stop, fam))
    extra = {"family": fam, "start_utc": started, "end_utc": utcnow(),
             "count_check_ok": okc, "count_check_msgs": msgs,
             "estimate_cpu_s": round(est, 1), "h_path": hpath}
    if fam in BUDGETED:
        extra.update({"h_written": hpath is not None, "h_prefix_path": ppath,
                      "m1_limit": M1_LIMIT, "units": len(units),
                      "estimate_wall_s": round(est_wall, 1),
                      "budget": {"cpu_s": round(cpu_budget, 1), "wall_s": round(wall_budget, 1)},
                      "peak_total_rss_mb_sampled": {"count": round(mon_c.peak_total_rss_mb, 1),
                                                    "main": round(mon.peak_total_rss_mb, 1)},
                      "per_first_move_counts": m1sum,
                      "h_sha256_by_first_move": m1_dig})
    info = base_run_info(command, jobs, (t0, t1, t2, c0, c1, c2), extra)
    write_run_json(d, info)
    log("  %s: processed %d, novel %d (+%d Aut), final %s, stop %s, wall %.1fs cpu %.1fs"
        % (fam, processed, len(novel), len(aut_novel), fin, stop, t2 - t0, c2 - c0))
    return res, okc, msgs, S, novel_members, aut_novel


# ---------------------------------------------------------------- KM, KMd
def run_km(fam, F0res, R0, st_factory, root, hdir, command, log):
    started = utcnow()
    t0, c0 = time.time(), cpu_seconds()
    K = get_web("W1")
    tait = F0res["tait"]
    kmax = 0 if fam == "KM" else 3
    sets = km.face_sets(K)
    n4, okcls = km.check_face_colourings(K, sets)
    assert n4 == 240 and okcls, (n4, okcls)
    t1, c1 = time.time(), cpu_seconds()
    S = st_factory()
    d = os.path.join(root, "W1", "A2", fam)
    os.makedirs(d, exist_ok=True)
    os.makedirs(hdir, exist_ok=True)
    hpath = os.path.join(hdir, "W1-A2-%s-h.jsonl" % fam)
    h = hashlib.sha256()
    i = 0
    degs, vecs = [], []
    leaves = {}
    novel, novel_members = [], []
    stop = None
    a3v = 0
    with open(hpath, "w", newline="\n") as fh:
        for darts, dots, dg, hx in km.km_members(K, tait, kmax):
            i += 1
            line = json.dumps({"i": i, "km": darts, "dots": dots, "deg": dg, "a": hx}) + "\n"
            fh.write(line)
            h.update(line.encode("ascii"))
            v = hex_to_packed(hx)
            degs.append(dg)
            vecs.append(v)
            leaves[dg] = leaves.get(dg, 0) + 1
            if stop is None and is_ret(dg):
                status, isnov = S.process(v, dg)
                if status == "A3_VIOLATION":
                    a3v += 1
                    stop = status
                elif isnov:
                    novel.append([i, dg, len(S.U), len(S.P)])
                    novel_members.append((i, v))
                    if status in ("ELL60", "DIMU11"):
                        stop = status
            if stop:
                break
    processed = i
    exp_n = 20 if fam == "KM" else 58500
    exhausted = stop is None
    if exhausted:
        stop = "EXHAUSTED"
        assert processed == exp_n
    fin = S.final(R0["ell_q"].get(-1, 0), R0["ell_q"].get(1, 0))
    res = {"amendment": 2, "web": "W1", "family": fam, "sites": {}, "expanded_nodes": {},
           "leaves_by_degree": smap(leaves), "N_leaves": processed, "N_retained": processed,
           "processed": processed, "h_sha256": h.hexdigest(), "a3_violations": a3v,
           "novel": novel, "aut_novel": [], "start": S.start, "final": fin, "stop": stop}
    extra_ctl = None
    if fam == "KMd":
        Rk = ranks.compute_all(degs, vecs, len(tait))
        res.update({"N": processed, "ell": Rk["ell"], "ell_q": smap(Rk["ell_q"]),
                    "r": Rk["r"], "r_q": smap(Rk["r_q"])})
        Ru = ranks.compute_all(F0res["degs"] + degs, F0res["vecs"] + vecs, len(tait))
        extra_ctl = {"KMd": {"N": processed, "ell": Rk["ell"], "ell_q": smap(Rk["ell_q"]),
                             "r": Rk["r"], "r_q": smap(Rk["r_q"])},
                     "F0_union_KMd": {"N": len(F0res["degs"]) + processed, "ell": Ru["ell"],
                                      "ell_q": smap(Ru["ell_q"]), "r": Ru["r"], "r_q": smap(Ru["r_q"])}}
    with open(os.path.join(d, "result.json"), "w", newline="\n") as f:
        f.write(dumps(res))
    lines = pairsample_lines(processed, lambda k: vecs[k - 1], S, novel_members)
    with open(os.path.join(d, "pairsample.tsv"), "w", newline="\n") as f:
        f.writelines(lines)
    t2, c2 = time.time(), cpu_seconds()
    write_run_json(d, base_run_info(command, 1, (t0, t1, t2, c0, c1, c2),
                                    {"family": fam, "start_utc": started, "end_utc": utcnow(),
                                     "h_path": hpath}))
    log("  %s: processed %d, novel %d, final %s, stop %s, wall %.1fs"
        % (fam, processed, len(novel), fin, stop, t2 - t0))
    return res, extra_ctl, S, novel_members


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["all", "family", "control"])
    ap.add_argument("name", nargs="?")
    ap.add_argument("--jobs", type=int, default=8)
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--out", default=os.path.join(here, "results"))
    ap.add_argument("--hdir", default=None)
    ap.add_argument("--prior", default=None,
                    help="results root holding the mandatory families' result.json (union after T3)")
    ap.add_argument("--count-only", action="store_true", help="family: count-only pass only")
    ap.add_argument("--m1-limit", type=int, default=None,
                    help="test only: restrict a tree family to its first K level-1 expansions")
    ap.add_argument("--hprefix", type=int, default=None,
                    help="also write the first N h lines to a separate file")
    a = ap.parse_args()
    if a.name in NOT_IMPLEMENTED:
        raise SystemExit(NOT_IMPLEMENTED[a.name])
    global M1_LIMIT
    M1_LIMIT = a.m1_limit
    hdir = a.hdir or os.path.join(a.out, "h")
    command = "python3 a2run.py " + " ".join(sys.argv[1:])
    import a2controls
    a2controls.main(a, hdir, command)


if __name__ == "__main__":
    # a2controls imports this file as module `a2run`; make both names one module so that
    # the options set above (M1_LIMIT) are seen there.
    sys.modules.setdefault("a2run", sys.modules[__name__])
    main()
