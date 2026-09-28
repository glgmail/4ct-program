"""Free combinations of free cartwheels: appendix A.10 (Lemmas A.4-A.6).

PHASE 1 STATUS: transcribed from the pseudocode, not run. It needs C_all from
badcartwheels.py. Treat it as a draft.

Interpretation (see README): A.10.2 line 6 takes "an arbitrary vertex" of
the combination as the centre c* for the blocking test. We take the image of
the centre of the first cartwheel. With every degree at most 8 or a tail
range, the centre only matters if it is a tail vertex (A.7.2 would then try
all its degrees 5..9 instead of treating it as unusable), and the image of a
centre never is one.
"""
from __future__ import annotations

from .badcartwheels import centre_darts_by_degree
from .blocking import blocked
from .pseudo import G_INCLUDE, PC, disjoint_union, free_hom_configuration, homomorphism


def delete_degree_from_k_to_9(cws, k):
    """Algorithm A.10.1."""
    out = []
    for cw in cws:
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
    return out


class Combined:
    """A pseudo-configuration with the map from the first cartwheel."""

    __slots__ = ("pc", "vmap", "dmap")

    def __init__(self, pc, vmap, dmap):
        self.pc = pc
        self.vmap = vmap
        self.dmap = dmap


def combine_each_cartwheel(pc, e, centre, cws, index):
    """Algorithm A.10.2. `centre` is the vertex of pc used as c* (mapped)."""
    out = []
    nv0, nd0 = pc.nv, len(pc.head)
    for cw in cws:
        for j in range(1, cw.d + 1):
            e1 = cw.into[j]  # a dart whose head is the centre of cw
            u = disjoint_union(pc, cw.pc)
            for z, (vmap, dmap) in free_hom_configuration(u, [(e, e1 + nd0)]):
                c = vmap[centre]
                if blocked(z, c, index):
                    continue
                out.append(Combined(z, vmap[:nv0], dmap[:nd0]))
    return out


def combine_each_cartwheel_twice(pc, e1, e2, centre, cws, ds_index, index):
    """Algorithm A.10.3 (the first step uses Ds, as line 1 says)."""
    out = []
    for a in combine_each_cartwheel(pc, e1, centre, cws, ds_index):
        for b in combine_each_cartwheel(a.pc, a.dmap[e2], a.vmap[centre], cws, index):
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


def check_deg8(call, ds_index, x_pc, x_centre, report):
    """Algorithms A.10.4-A.10.7 (Lemma A.4). `report(kind, ok, info)`."""
    cs = delete_degree_from_k_to_9(call, 9)
    for n, cw in enumerate(cs):
        if cw.pc.lo[0] != 8:
            continue
        cd = centre_darts_by_degree(cw)
        d8, d7 = cd.get(8, []), cd.get(7, [])
        rev = cw.pc.rev
        if d8:  # A.10.5
            for e in d8:
                res = combine_each_cartwheel(cw.pc, rev[e], 0, cs, ds_index)
                report("88", not res, (n, len(res)))
        elif len(d7) == 1:  # A.10.6
            res = combine_each_cartwheel(cw.pc, rev[d7[0]], 0, cs, ds_index)
            report("87", not res, (n, len(res)))
        elif len(d7) > 1:  # A.10.7
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
                                                   ds_index, ds_index)
                for r in res:
                    report("787", contain_x(r.pc, r.vmap[0], x_pc, x_centre), n)


def check_7_triangle(call, ds_index, report):
    """Algorithm A.10.9 (Lemma A.5)."""
    cs = delete_degree_from_k_to_9(delete_degree_from_k_to_9(call, 9), 8)
    for n, cw in enumerate(cs):
        p = cw.pc
        for j in range(1, cw.d + 1):
            e = cw.into[j]
            f = p.succ[e]
            ve = p.head[p.rev[e]]
            vf = p.head[p.rev[f]]
            if p.lo[ve] == p.hi[ve] == 7 and p.lo[vf] == p.hi[vf] == 7:
                res = combine_each_cartwheel_twice(p, p.rev[e], p.rev[f], 0, cs,
                                                   ds_index, ds_index)
                report("7triangle", not res, (n, len(res)))


def check_deg7(call, ds_index, k_index, t73_index, report):
    """Algorithms A.10.10-A.10.12 (Lemma A.6). k_index is Ds u {T73}."""
    cs = delete_degree_from_k_to_9(delete_degree_from_k_to_9(call, 9), 8)
    cs = [cw for cw in cs if not blocked(cw.pc, 0, t73_index)]
    for n, cw in enumerate(cs):
        d7 = centre_darts_by_degree(cw).get(7, [])
        rev = cw.pc.rev
        if len(d7) == 1:  # A.10.11
            res = combine_each_cartwheel(cw.pc, rev[d7[0]], 0, cs, k_index)
            report("77", not res, (n, len(res)))
        elif len(d7) > 1:  # A.10.12
            for i in range(len(d7)):
                for j in range(i):
                    res = combine_each_cartwheel_twice(cw.pc, rev[d7[i]], rev[d7[j]],
                                                       0, cs, ds_index, k_index)
                    report("777", not res, (n, len(res)))
