"""Colourings, computed two independent ways.

The house rule is that every computation has two implementations that agree.
The candidates are all built on 4-colourings, so they are computed here two
ways, from opposite sides of Tait's correspondence:

A. **Vertex colourings** by backtracking over vertices (`vertex_colourings`).
B. **Tait colourings**, the 3-edge-colourings of the dual cubic graph, by
   backtracking over edges (`tait_colourings`).

With colours taken from Z2 x Z2, colouring an edge by the difference of its
ends' colours turns each proper vertex 4-colouring into a Tait colouring,
and exactly 4 vertex colourings (differing by adding a constant) map to each
Tait colouring. So the labelled counts satisfy vertex = 4 x Tait. Up to
permuting the colours (24 ways for vertices, 6 for edges) the two counts
are therefore equal. `run.py selfcheck` requires this for every sphere
triangulation up to its bound.

Colourings "up to permutation" are enumerated in normal form. For a sphere
triangulation, the face (0, rot[0][0], rot[0][1]) is coloured 0, 1, 2. For a
colouring of a boundary cycle, colours are numbered in order of first
appearance.
"""
from __future__ import annotations

from planar import Tri


# ---------------------------------------------------------------------------
# A. vertex colourings
# ---------------------------------------------------------------------------
def _order_from(t: Tri, start):
    """Vertices in breadth-first order from `start`, so each new vertex has
    as many coloured neighbours as possible (keeps backtracking shallow)."""
    seen = set(start)
    order = list(start)
    i = 0
    while i < len(order):
        for w in t.rot[order[i]]:
            if w not in seen:
                seen.add(w)
                order.append(w)
        i += 1
    return order


def vertex_colourings(t: Tri, fixed=None, limit=None):
    """Yield proper 4-colourings of t as tuples, each extending the partial
    colouring `fixed` ({vertex: colour}). With fixed=None on a sphere
    triangulation, the face (0, rot[0][0], rot[0][1]) is fixed to 0, 1, 2,
    which yields each colouring up to permutation exactly once."""
    n = t.n
    if fixed is None:
        a, b = t.rot[0][0], t.rot[0][1]
        fixed = {0: 0, a: 1, b: 2}
    col = [-1] * n
    for v, c in fixed.items():
        col[v] = c
    for v, c in fixed.items():
        if any(col[w] == c for w in t.rot[v]):
            return
    order = [v for v in _order_from(t, list(fixed)) if v not in fixed]
    rot = t.rot
    produced = 0

    def rec(i):
        nonlocal produced
        if i == len(order):
            produced += 1
            yield tuple(col)
            return
        v = order[i]
        used = {col[w] for w in rot[v]}
        for c in range(4):
            if c not in used:
                col[v] = c
                yield from rec(i + 1)
                if limit is not None and produced >= limit:
                    col[v] = -1
                    return
        col[v] = -1

    yield from rec(0)


def extends(t: Tri, fixed):
    """Whether the partial colouring `fixed` extends to a proper 4-colouring."""
    for _ in vertex_colourings(t, fixed=fixed, limit=1):
        return True
    return False


def count_vertex_colourings(t: Tri):
    return sum(1 for _ in vertex_colourings(t))


# ---------------------------------------------------------------------------
# B. Tait colourings of the dual
# ---------------------------------------------------------------------------
def dual(t: Tri):
    """The dual cubic graph of a sphere triangulation: faces as vertices.
    Returns (faces, dual_adjacency, edge_list), where edge_list[i] is the
    pair of faces on the two sides of the i-th edge of t."""
    faces = t.faces()
    where = {}
    for fi, f in enumerate(faces):
        for i in range(len(f)):
            where[(f[i], f[(i + 1) % len(f)])] = fi
    edges = []
    for v, w in t.edges():
        edges.append((where[(v, w)], where[(w, v)]))
    adj = [[] for _ in faces]
    for i, (f, g) in enumerate(edges):
        adj[f].append((g, i))
        adj[g].append((f, i))
    return faces, adj, edges


def tait_colourings(t: Tri):
    """Yield 3-edge-colourings of the dual cubic graph as tuples over t's
    edges, up to permuting the three colours. Normal form: the three edges of
    dual vertex 0 get colours 0, 1, 2 in their listed order."""
    faces, adj, edges = dual(t)
    m = len(edges)
    col = [-1] * m
    at = [[e for _, e in adj[f]] for f in range(len(faces))]
    for c, e in enumerate(at[0]):
        col[e] = c
    # order edges breadth-first over dual vertices from face 0
    order, seen, queue = [], set(at[0]), [0]
    visited = {0}
    while queue:
        f = queue.pop(0)
        for g, e in adj[f]:
            if e not in seen:
                seen.add(e)
                order.append(e)
            if g not in visited:
                visited.add(g)
                queue.append(g)
    ends = edges

    def ok(e, c):
        f, g = ends[e]
        return all(col[x] != c for x in at[f] if x != e) and \
            all(col[x] != c for x in at[g] if x != e)

    def rec(i):
        if i == len(order):
            yield tuple(col)
            return
        e = order[i]
        for c in range(3):
            if ok(e, c):
                col[e] = c
                yield from rec(i + 1)
        col[e] = -1

    yield from rec(0)


def count_tait_colourings(t: Tri):
    return sum(1 for _ in tait_colourings(t))


# ---------------------------------------------------------------------------
# helpers shared by candidates
# ---------------------------------------------------------------------------
def normalise(colouring, anchor):
    """Relabel colours so the vertices in `anchor` get 0, 1, 2, ... in order
    of first appearance, then the remaining colours in order of appearance."""
    m = {}
    for v in anchor:
        c = colouring[v]
        if c not in m:
            m[c] = len(m)
    for c in colouring:
        if c not in m:
            m[c] = len(m)
    return tuple(m[c] for c in colouring)


def cycle_colourings(k, colours=4):
    """Proper colourings of a k-cycle with at most `colours` colours, up to
    permutation (colours numbered by first appearance)."""
    out = []
    seq = [0]

    def rec():
        if len(seq) == k:
            if seq[-1] != seq[0]:
                out.append(tuple(seq))
            return
        top = max(seq) + 1
        for c in range(min(top + 1, colours)):
            if c != seq[-1]:
                seq.append(c)
                rec()
                seq.pop()

    rec()
    return out
