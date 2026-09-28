"""Canonical form of a triangulation, to report one well-defined smallest
counterexample however the enumeration was split between processes.

The code is the least breadth-first numbering over every starting dart and
both orientations, walking each rotation from the dart a vertex was entered
by. Two triangulations get the same code exactly when they are isomorphic,
reflections included. A disc is capped first (planar.with_apex), with the
cap marked, so its outer face is part of the structure.

`run.py selfcheck` confirms that the code separates every pair of distinct
plantri outputs at each size it checks, and that relabelled and mirrored
copies get the same code.
"""
from __future__ import annotations

from planar import Tri, with_apex


def _code(rot, marked, v0, w0, step, best):
    num = {v0: 0}
    entry = {v0: w0}
    queue = [v0]
    out = []
    h = 0
    while h < len(queue):
        u = queue[h]
        h += 1
        r = rot[u]
        k = len(r)
        i = r.index(entry[u])
        out.append(1 if u in marked else 0)
        out.append(k)
        for j in range(k):
            w = r[(i + step * j) % k]
            if w not in num:
                num[w] = len(num)
                entry[w] = u
                queue.append(w)
            out.append(num[w])
        if best is not None and out > best[:len(out)]:
            return None
    return out


def canonical(t: Tri):
    if t.is_disc:
        c = with_apex(t)
        rot, marked, starts = c.rot, {t.n}, [t.n]
    else:
        rot, marked, starts = t.rot, set(), range(t.n)
    best = None
    for step in (1, -1):
        for v in starts:
            for w in rot[v]:
                code = _code(rot, marked, v, w, step, best)
                if code is not None and (best is None or code < best):
                    best = code
    return tuple(best)
