"""Enumerating bad cartwheels with tail ranges: appendix A.9.8-A.9.22.

PHASE 1 STATUS: implemented from the pseudocode, exercised only on samples
for timing (run.py sample-bad). It has not been run in full and its output
has not been compared with the published counts (9366 for centre degree 7,
728 for centre degree 8). Treat it as a draft.

Sets are sets: cartwheels are identified by their degree ranges (the
structure of a cartwheel is fixed by its C^d_0 wheel), so a cartwheel reached
along two branches counts once, as the set notation of A.9.14 and A.9.21
says.
"""
from __future__ import annotations

from collections import deque

from .cartwheel import (CARTWHEEL_DEGREES, always_apply, dominantly_apply,
                        prune, upper_bound_of_charge)
from .pseudo import G_INTERSECT, PC, homomorphism


def _with_ranges(cw, lo, hi):
    p = cw.pc
    return cw.with_pc(PC(p.nv, lo, hi, p.head, p.rev, p.succ, p.pred))


def concrete_degree_except_tail(cw):
    """Algorithm A.9.10."""
    out = [cw]
    for v in range(cw.pc.nv):
        lo, hi = cw.pc.lo[v], cw.pc.hi[v]
        if lo == hi or hi == 9:
            continue
        new = []
        for d in CARTWHEEL_DEGREES[:4]:
            if lo <= d <= hi:
                for c in out:
                    l2 = c.pc.lo[:]
                    h2 = c.pc.hi[:]
                    l2[v] = h2[v] = d
                    new.append(_with_ranges(c, l2, h2))
        out = new
    return out


def update_degree_by_rule(cw, e, rstar):
    """Algorithm A.9.9."""
    m = homomorphism(rstar.pc, rstar.dart, cw.pc, e, G_INTERSECT)
    if m is None:
        return []
    vmap, _ = m
    lo = cw.pc.lo[:]
    hi = cw.pc.hi[:]
    for vr in range(rstar.pc.nv):
        vc = vmap[vr]
        lo[vc] = max(lo[vc], rstar.pc.lo[vr])
        hi[vc] = min(hi[vc], rstar.pc.hi[vr])
    return concrete_degree_except_tail(_with_ranges(cw, lo, hi))


def fix_in_rules(cw0, tables, index, stats=None):
    """Algorithm A.9.8. Returns C_d as a list of (cartwheel, fixed rules)."""
    cur = [(cw0, [])]
    for i in range(1, cw0.d + 1):
        nxt = []
        for cw, fixed in cur:
            for rstar in tables.rstar_d:
                for cw1 in update_degree_by_rule(cw, cw.into[i], rstar):
                    f1 = fixed + [rstar]
                    if prune(cw1, f1, tables, index) is not None:
                        continue
                    nxt.append((cw1, f1))
        cur = nxt
        if stats is not None:
            stats.setdefault("C_i sizes", []).append(len(cur))
    return cur


def should_refine(cw, i, rule):
    """Algorithm A.9.16."""
    e = cw.out[i]
    return (not always_apply(cw.pc, e, rule)) and dominantly_apply(cw.pc, e, rule)


def refinement(cw, i, rule):
    """Algorithms A.9.17-A.9.19."""
    m = homomorphism(rule.pc, rule.dart, cw.pc, cw.out[i], G_INTERSECT)
    assert m is not None
    vmap, _ = m
    ur = [u for u in range(rule.pc.nv)
          if cw.pc.hi[vmap[u]] == 9 and cw.pc.lo[vmap[u]] < rule.pc.lo[u]]
    # refineAlways (A.9.18)
    lo = cw.pc.lo[:]
    for u in ur:
        lo[vmap[u]] = rule.pc.lo[u]
    out = [_with_ranges(cw, lo, cw.pc.hi[:])]
    # refineNever (A.9.19)
    for u in ur:
        hi = cw.pc.hi[:]
        hi[vmap[u]] = rule.pc.lo[u] - 1
        out.extend(concrete_degree_except_tail(_with_ranges(cw, cw.pc.lo[:], hi)))
    return out


def _ckey(cw):
    return (tuple(cw.pc.lo), tuple(cw.pc.hi))


def fix_out_rules(cd, tables, index, stats=None):
    """Algorithm A.9.14. Returns C as a list of (cartwheel, fixed rules)."""
    q = deque(cd)
    out = []
    seen = set()
    while q:
        cw, fixed = q.popleft()
        refined = False
        for i in range(1, cw.d + 1):
            for rule in tables.rules:
                if not should_refine(cw, i, rule):
                    continue
                refined = True
                for cw1 in refinement(cw, i, rule):
                    if prune(cw1, fixed, tables, index) is not None:
                        continue
                    q.append((cw1, fixed))
                break
            if refined:
                break
        if not refined:
            k = (_ckey(cw), tuple(id(r) for r in fixed))
            if k not in seen:
                seen.add(k)
                out.append((cw, fixed))
    return out


def centre_darts_by_degree(cw):
    """Algorithm A.9.22: centre darts (v_j -> v, j = 1..d in clockwise
    order) grouped by the degree of their tail."""
    out = {}
    for j in range(1, cw.d + 1):
        e = cw.into[j]
        t = cw.pc.head[cw.pc.rev[e]]
        assert cw.pc.lo[t] == cw.pc.hi[t]
        out.setdefault(cw.pc.lo[t], []).append(e)
    return out


def enum_bad_cartwheels(cw0, tables, index, stats=None):
    """Algorithm A.9.21 for one C^d_0 wheel. Returns (C', failures), where
    C' is the set of cartwheels (deduplicated) and failures lists the
    assertions of lines 7-9 that did not hold."""
    cd = fix_in_rules(cw0, tables, index, stats)
    c = fix_out_rules(cd, tables, index, stats)
    failures = []
    result = []
    keys = set()
    for cw, fixed in c:
        sigma = upper_bound_of_charge(cw, fixed, tables)
        d = cw.pc.lo[0]
        cdarts = centre_darts_by_degree(cw)
        if sigma != 0:
            failures.append(("sigma", sigma, _ckey(cw)))
        if d not in (7, 8):
            failures.append(("centre degree", d, _ckey(cw)))
        if not (len(cdarts.get(7, ())) + len(cdarts.get(8, ()))
                + len(cdarts.get(9, ())) > 0):
            failures.append(("no neighbour of degree 7-9", None, _ckey(cw)))
        k = _ckey(cw)
        if k not in keys:
            keys.add(k)
            result.append(cw)
    return result, failures
