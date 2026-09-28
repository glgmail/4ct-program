"""Self-consistency checks of our transcriptions of X and T_{7^3}.

These check that the transcription is a valid configuration (a triangulated
disc with consistent clockwise rotations and the right degrees). They cannot
check that it is the configuration the authors meant; that needs a reader
comparing checks/f2/data/special-configurations.json with Figure 12.
"""
from __future__ import annotations

from collections import Counter

from .blocking import blocked, is_blocked_witness
from .pseudo import NIL, resolve_degree_issues


def check_special(name, pc, names, centre, index=None):
    """Return a list of (description, ok, detail)."""
    res = []
    inc = pc.incidence()
    deg, bnd, _ = inc
    nd = len(pc.head)

    # degrees: an inner vertex has exactly its degree, a boundary vertex fewer
    bad = [names[v] for v in range(pc.nv)
           if (not bnd[v] and deg[v] != pc.lo[v]) or (bnd[v] and deg[v] >= pc.lo[v])]
    res.append(("inner vertices have exactly their degree, boundary vertices "
                "fewer neighbours than their degree", not bad, bad))

    # each vertex has one incidence list (M6): at most one dart with pred nil
    firsts = Counter(pc.head[e] for e in range(nd) if pc.pred[e] == NIL)
    lasts = Counter(pc.head[e] for e in range(nd) if pc.succ[e] == NIL)
    bad = [names[v] for v in range(pc.nv)
           if firsts[v] != (1 if bnd[v] else 0) or lasts[v] != (1 if bnd[v] else 0)]
    res.append(("one incidence list per vertex (M6)", not bad, bad))

    # (M5): around every dart with a successor there is a facial triangle
    tri = set()
    bad = []
    for e in range(nd):
        if pc.succ[e] == NIL:
            continue
        f = pc.rev[pc.succ[e]]
        g = pc.rev[pc.succ[f]] if pc.succ[f] != NIL else NIL
        if g == NIL or pc.succ[g] == NIL or pc.rev[pc.succ[g]] != e:
            bad.append((names[pc.head[pc.rev[e]]], names[pc.head[e]]))
            continue
        tri.add(frozenset((e, f, g)))
    res.append(("rotations are consistently oriented: every inner angle "
                "closes a triangle (M5)", not bad, bad))
    heads_ok = all(len({pc.head[x] for x in t}) == 3 for t in tri)
    res.append(("inner faces are triangles on three distinct vertices",
                heads_ok, len(tri)))

    # Euler characteristic of a disc: V - E + F = 1
    ne = nd // 2
    chi = pc.nv - ne + len(tri)
    res.append(("V - E + F = 1 (a disc)", chi == 1,
                f"V={pc.nv} E={ne} F={len(tri)}"))

    # the boundary is one closed walk through distinct vertices (no cut vertex)
    # from a boundary vertex v, the next one is the tail of v's first dart
    bverts = [v for v in range(pc.nv) if bnd[v]]
    walk = []
    if bverts:
        v = bverts[0]
        for _ in range(pc.nv + 1):
            walk.append(v)
            v = pc.head[pc.rev[_first_dart_at(pc, v)]]
            if v == bverts[0]:
                break
    ok = (not bverts) or (len(walk) == len(set(walk)) == len(bverts))
    res.append(("the boundary is a single cycle through every boundary vertex",
                ok, [names[v] for v in walk]))

    # a valid pseudo-configuration: no degree issues to resolve
    out = resolve_degree_issues(pc)
    ok = len(out) == 1 and out[0][0].key() == pc.key()
    res.append(("no degree issues (resolveDegreeIssues returns it unchanged)",
                ok, len(out)))

    res.append(("degree multiset", True,
                dict(sorted(Counter(pc.lo[v] for v in range(pc.nv)).items()))))
    if centre is not None:
        ok = not bnd[centre] and deg[centre] == pc.lo[centre]
        res.append((f"centre {names[centre]} is inner, degree {pc.lo[centre]}",
                    ok, deg[centre]))
    if index is not None and centre is not None and name == "X":
        b = blocked(pc, centre, index)
        res.append(("not blocked by Ds with this centre (X must not contain a "
                    "reducible configuration, or Lemma 8.3(iii) would not need it)",
                    not b, b))
    if index is not None and centre is not None and name == "Xw":
        w = is_blocked_witness(pc, centre, index)
        detail = None
        if w:
            c, _ = w[0]
            detail = {"configuration": c.name, "mirror": c.mirrored,
                      "cut_vertex_extension": c.cut,
                      "degrees": sorted(c.pc.lo[v] for v in range(c.pc.nv))}
        res.append(("blocked by Ds (Figure 13: contains a reducible "
                    "configuration of D)", w is not None, detail))
    return res


def _first_dart_at(pc, v):
    for e in range(len(pc.head)):
        if pc.head[e] == v and pc.pred[e] == NIL:
            return e
    raise AssertionError("no first dart")
