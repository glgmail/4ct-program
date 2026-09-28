"""Free combinations of free cartwheels: appendix A.10 (Lemmas A.4-A.6).

STATUS (phase 2): run on samples of the real C_all only, to time it and to
check that the prefilter changes nothing. Lemmas A.4-A.6 have not been
run in full.

The work is organised by *roots*: a root is one cartwheel of C (after
deleteDegreeFromKto9) to which A.10.4, A.10.9 or A.10.10 applies. The full
checks are the loops over all roots; `run_root` does one.

Interpretation (see README): A.10.2 line 6 takes "an arbitrary vertex" of
the combination as the centre c* for the blocking test. We take the image of
the centre of the root cartwheel. With every degree at most 8 or a tail
range, the centre only matters if it is a tail vertex (A.7.2 would then try
all its degrees 5..9 instead of treating it as unusable), and the image of a
centre never is one.

Prefilter for A.10.2 (ours; exact)
----------------------------------
A.10.2 calls freeHomomorphismConfiguration on (Z, delta) \\sqcup (Z', delta')
with the request (e, e'). The resulting map phi is a homomorphism of the
underlying pseudo-triangulations (Lemma 9.4) with phi(e) = phi(e'), so
phi(succ^k(e)) = phi(succ^k(e')) and phi(pred^k(e)) = phi(pred^k(e')) for
every k for which both sides are defined, and then the heads and the tails
of these darts are identified too. dartIdentification (A.4.1) intersects the
degree ranges of identified vertices and gives up if an intersection is
empty. So if head(e), head(e') have disjoint ranges, or if for some such k
the tails of succ^k(e) and succ^k(e') (or of pred^k) have disjoint ranges,
the free combination is empty and we skip it without building it.
`prefilter=False` turns this off; run.py a10-sample --compare runs the same
roots both ways and requires identical results.
"""
from __future__ import annotations

import hashlib

from .badcartwheels import centre_darts_by_degree
from .blocking import blocked
from .pseudo import (G_INCLUDE, NIL, PC, disjoint_union, free_hom_configuration,
                     homomorphism)


def delete_degree_from_k_to_9(cws, k, keep_index=None):
    """Algorithm A.10.1. If keep_index is a list, the positions (in cws) of
    the cartwheels kept are appended to it."""
    out = []
    for pos, cw in enumerate(cws):
        lo = cw.pc.lo[:]
        hi = cw.pc.hi[:]
        remove = False
        for v in range(cw.pc.nv):
            if lo[v] == hi[v] == k:
                remove = True
                break
            if lo[v] == k - 1 and hi[v] == 9:
                hi[v] = k - 1
        if not remove:
            p = cw.pc
            out.append(cw.with_pc(PC(p.nv, lo, hi, p.head, p.rev, p.succ, p.pred)))
            if keep_index is not None:
                keep_index.append(pos)
    return out


class Combined:
    """A pseudo-configuration with the map from the root's pseudo-config."""

    __slots__ = ("pc", "vmap", "dmap")

    def __init__(self, pc, vmap, dmap):
        self.pc = pc
        self.vmap = vmap
        self.dmap = dmap


def _meet(p, v, q, w):
    return not (p.lo[v] > q.hi[w] or q.lo[w] > p.hi[v])


def prefilter_ok(p, e, q, f):
    """False only if the free combination identifying e with f is empty for
    the reason given in the module docstring."""
    if not _meet(p, p.head[e], q, q.head[f]):
        return False
    for step in (p.succ, p.pred):
        qstep = q.succ if step is p.succ else q.pred
        a, b = e, f
        for _ in range(len(p.head) + len(q.head)):
            if not _meet(p, p.head[p.rev[a]], q, q.head[q.rev[b]]):
                return False
            a, b = step[a], qstep[b]
            if a == NIL or b == NIL or (a == e and b == f):
                break
    return True


def combine_each_cartwheel(pc, e, centre, cws, index, prefilter=True, stats=None):
    """Algorithm A.10.2. `centre` is the vertex of pc whose image is c*."""
    out = []
    nv0, nd0 = pc.nv, len(pc.head)
    for cw in cws:
        for j in range(1, cw.d + 1):
            e1 = cw.into[j]  # a dart whose head is the centre of cw
            if stats is not None:
                stats["pairs"] = stats.get("pairs", 0) + 1
            if prefilter and not prefilter_ok(pc, e, cw.pc, e1):
                if stats is not None:
                    stats["prefiltered"] = stats.get("prefiltered", 0) + 1
                continue
            u = disjoint_union(pc, cw.pc)
            for z, (vmap, dmap) in free_hom_configuration(u, [(e, e1 + nd0)]):
                if stats is not None:
                    stats["images"] = stats.get("images", 0) + 1
                if blocked(z, vmap[centre], index):
                    continue
                out.append(Combined(z, vmap[:nv0], dmap[:nd0]))
    return out


def combine_each_cartwheel_twice(pc, e1, e2, centre, cws, ds_index, index,
                                 prefilter=True, stats=None):
    """Algorithm A.10.3 (the first step uses Ds, as line 1 says)."""
    out = []
    for a in combine_each_cartwheel(pc, e1, centre, cws, ds_index, prefilter, stats):
        if stats is not None:
            stats["first_step_survivors"] = stats.get("first_step_survivors", 0) + 1
        for b in combine_each_cartwheel(a.pc, a.dmap[e2], a.vmap[centre], cws, index,
                                        prefilter, stats):
            out.append(Combined(b.pc, [b.vmap[x] for x in a.vmap],
                                [b.dmap[x] for x in a.dmap]))
    return out


def contain_x(pc, v, x_pc, x_centre):
    """Algorithm A.10.8."""
    ez = next(e for e in range(len(pc.head)) if pc.head[e] == v)
    ex = next(e for e in range(len(x_pc.head)) if x_pc.head[e] == x_centre)
    for _ in range(8):
        if homomorphism(x_pc, ex, pc, ez, G_INCLUDE) is not None:
            return True
        ex = x_pc.succ[ex]
    return False


# ---------------------------------------------------------------------------
# the three checks, root by root
# ---------------------------------------------------------------------------
class Context:
    """Everything the checks need: the converted cartwheel sets and the
    configuration indexes."""

    def __init__(self, call, ds_index, k_index, t73_index, x_pc, x_centre):
        i9, i8 = [], []
        self.c9 = delete_degree_from_k_to_9(call, 9, i9)          # A.10.4 line 1
        c8 = delete_degree_from_k_to_9(self.c9, 8, i8)            # A.10.9/10 line 2
        self.c8 = c8
        keep7 = [n for n, cw in enumerate(c8) if not blocked(cw.pc, 0, t73_index)]
        self.c7 = [c8[n] for n in keep7]                          # A.10.10 line 3
        # position in C_all (call.jsonl, 0-based) of each cartwheel of each set
        self.call_index = {"A.4": i9, "A.5": [i9[n] for n in i8],
                           "A.6": [i9[i8[n]] for n in keep7]}
        self.ds = ds_index
        self.k = k_index
        self.x_pc = x_pc
        self.x_centre = x_centre


def roots(ctx, check):
    """Indices (into the check's set) of the cartwheels the check acts on."""
    if check == "A.4":
        out = []
        for n, cw in enumerate(ctx.c9):
            if cw.pc.lo[0] != 8:
                continue
            cd = centre_darts_by_degree(cw)
            if cd.get(8) or cd.get(7):
                out.append(n)
        return out
    if check == "A.5":
        out = []
        for n, cw in enumerate(ctx.c8):
            p = cw.pc
            for j in range(1, cw.d + 1):
                e = cw.into[j]
                f = p.succ[e]
                ve, vf = p.head[p.rev[e]], p.head[p.rev[f]]
                if p.lo[ve] == p.hi[ve] == 7 and p.lo[vf] == p.hi[vf] == 7:
                    out.append(n)
                    break
        return out
    if check == "A.6":
        return [n for n, cw in enumerate(ctx.c7)
                if centre_darts_by_degree(cw).get(7)]
    raise ValueError(check)


def run_root(ctx, check, n, prefilter=True, stats=None):
    """Run one root. Returns (assertions, signature): a list of
    (kind, ok, detail), and a digest of every surviving combination (exact
    structure, in order), used to compare runs with and without the
    prefilter."""
    sig = hashlib.sha256()
    res_all = []

    def note(res):
        for r in res:
            sig.update(repr(r.pc.key()).encode())
        sig.update(b"|")

    if check == "A.4":  # A.10.4-A.10.7
        cw = ctx.c9[n]
        cs = ctx.c9
        cd = centre_darts_by_degree(cw)
        d8, d7 = cd.get(8, []), cd.get(7, [])
        rev = cw.pc.rev
        if d8:
            for e in d8:
                res = combine_each_cartwheel(cw.pc, rev[e], 0, cs, ctx.ds, prefilter, stats)
                note(res)
                res_all.append(("88", not res, len(res)))
        elif len(d7) == 1:
            res = combine_each_cartwheel(cw.pc, rev[d7[0]], 0, cs, ctx.ds, prefilter, stats)
            note(res)
            res_all.append(("87", not res, len(res)))
        elif len(d7) > 1:
            dist = []
            for i, e1 in enumerate(d7):
                e2 = d7[(i + 1) % len(d7)]
                k, f = 0, e1
                while True:
                    f = cw.pc.succ[f]
                    k += 1
                    if f == e2:
                        break
                dist.append(k)
            m = min(dist)
            for i, e1 in enumerate(d7):
                if dist[i] != m:
                    continue
                e2 = d7[(i + 1) % len(d7)]
                res = combine_each_cartwheel_twice(cw.pc, rev[e1], rev[e2], 0, cs,
                                                   ctx.ds, ctx.ds, prefilter, stats)
                note(res)
                for r in res:
                    ok = contain_x(r.pc, r.vmap[0], ctx.x_pc, ctx.x_centre)
                    sig.update(b"X1" if ok else b"X0")
                    res_all.append(("787", ok, None))
                if not res:
                    res_all.append(("787 (no combination)", True, 0))
    elif check == "A.5":  # A.10.9
        cw = ctx.c8[n]
        cs = ctx.c8
        p = cw.pc
        for j in range(1, cw.d + 1):
            e = cw.into[j]
            f = p.succ[e]
            ve, vf = p.head[p.rev[e]], p.head[p.rev[f]]
            if p.lo[ve] == p.hi[ve] == 7 and p.lo[vf] == p.hi[vf] == 7:
                res = combine_each_cartwheel_twice(p, p.rev[e], p.rev[f], 0, cs,
                                                   ctx.ds, ctx.ds, prefilter, stats)
                note(res)
                res_all.append(("7triangle", not res, len(res)))
    elif check == "A.6":  # A.10.10-A.10.12
        cw = ctx.c7[n]
        cs = ctx.c7
        d7 = centre_darts_by_degree(cw).get(7, [])
        rev = cw.pc.rev
        if len(d7) == 1:
            res = combine_each_cartwheel(cw.pc, rev[d7[0]], 0, cs, ctx.k, prefilter, stats)
            note(res)
            res_all.append(("77", not res, len(res)))
        elif len(d7) > 1:
            for i in range(len(d7)):
                for j in range(i):
                    res = combine_each_cartwheel_twice(cw.pc, rev[d7[i]], rev[d7[j]], 0,
                                                       cs, ctx.ds, ctx.k, prefilter, stats)
                    note(res)
                    res_all.append(("777", not res, len(res)))
    else:
        raise ValueError(check)
    return res_all, sig.hexdigest()
