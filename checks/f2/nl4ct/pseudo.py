"""Dart representations, pseudo-configurations and (free) homomorphisms.

Written from arXiv:2603.24880v2, section 9 and appendix A.2-A.5. Every
function names the algorithm it transcribes. Nothing here is taken from any
other implementation.

Representation (our choice; the paper leaves it open)
-----------------------------------------------------
A pseudo-configuration with degree ranges (Z, lo, hi) is a `PC`:

- vertices are 0 .. nv-1, with degree range [lo[v], hi[v]]; the upper bound
  "infinity" is the integer INF (larger than any degree that occurs);
- darts are 0 .. nd-1, with the four pointers of section 9.2 held in the
  parallel lists head, rev, succ, pred; NIL (-1) is the nil pointer.

`succ` is the clockwise successor around the head (section 9.2, "succ
corresponds to the clockwise orientation of the darts around the vertices").

Maps between pseudo-configurations (homomorphisms) are pairs of lists
(vmap, dmap), indexed by the source's vertices and darts.

Operations never modify their arguments; they return new objects.
"""
from __future__ import annotations

from collections import deque

NIL = -1
INF = 1 << 20  # "infinity" in degree ranges; the files write it as 0


class PC:
    """A pseudo-configuration with degree ranges (section 9.4)."""

    __slots__ = ("nv", "lo", "hi", "head", "rev", "succ", "pred")

    def __init__(self, nv, lo, hi, head, rev, succ, pred):
        self.nv = nv
        self.lo = lo
        self.hi = hi
        self.head = head
        self.rev = rev
        self.succ = succ
        self.pred = pred

    @property
    def nd(self):
        return len(self.head)

    def copy(self):
        return PC(self.nv, self.lo[:], self.hi[:], self.head[:], self.rev[:],
                  self.succ[:], self.pred[:])

    def tail(self, e):
        return self.head[self.rev[e]]

    # -- incidence lists ---------------------------------------------------
    def incidence(self):
        """Per vertex: (degree d_Z(v), is_boundary, first dart).

        A vertex is a boundary vertex if some dart with that head has no
        successor (appendix A.4, remark before Algorithm A.4.4). The first
        dart of a boundary vertex is the one with pred = nil; for an inner
        vertex we return the lowest-numbered dart with that head.
        """
        nv = self.nv
        deg = [0] * nv
        bnd = [False] * nv
        first = [NIL] * nv
        head, succ, pred = self.head, self.succ, self.pred
        for e in range(len(head)):
            v = head[e]
            deg[v] += 1
            if succ[e] == NIL:
                bnd[v] = True
            if pred[e] == NIL:
                first[v] = e
        for e in range(len(head)):
            v = head[e]
            if first[v] == NIL:
                first[v] = e
        return deg, bnd, first

    def key(self):
        """Exact structural fingerprint (not isomorphism-invariant)."""
        return (self.nv, tuple(self.lo), tuple(self.hi), tuple(self.head),
                tuple(self.rev), tuple(self.succ), tuple(self.pred))


# ---------------------------------------------------------------------------
# Algorithm A.5.1 fromVRotations
# ---------------------------------------------------------------------------
def from_rotations(rotations):
    """Build the dart structure from clockwise rotations (Algorithm A.5.1).

    rotations[a] lists the neighbours of vertex a in clockwise order, with -1
    marking the boundary. The dart darts[a][b] has head a and tail b. Darts
    are numbered in the order they are created (vertex a ascending, then the
    position in rotations[a]). Returns (nv, head, rev, succ, pred, darts),
    where darts[a][b] is the dart with head a and tail b.
    """
    n = len(rotations)
    darts = [dict() for _ in range(n)]
    nd = 0
    for a in range(n):
        for b in rotations[a]:
            if b == -1:
                continue
            if b in darts[a]:
                raise ValueError(f"multiple darts between {a} and {b}")
            darts[a][b] = nd
            nd += 1
    head = [NIL] * nd
    rev = [NIL] * nd
    succ = [NIL] * nd
    pred = [NIL] * nd
    for a in range(n):
        rot = rotations[a]
        size = len(rot)
        for i, b in enumerate(rot):
            if b == -1:
                continue
            e = darts[a][b]
            head[e] = a
            if a not in darts[b]:
                raise ValueError(f"rotations of {a} and {b} disagree")
            rev[e] = darts[b][a]
            s = rot[i + 1] if i < size - 1 else rot[0]
            succ[e] = darts[a][s] if s != -1 else NIL
            p = rot[i - 1] if i > 0 else rot[size - 1]
            pred[e] = darts[a][p] if p != -1 else NIL
    return n, head, rev, succ, pred, darts


def mirror(pc):
    """Algorithm A.6.5: swap pred and succ of every dart."""
    return PC(pc.nv, pc.lo[:], pc.hi[:], pc.head[:], pc.rev[:], pc.pred[:],
              pc.succ[:])


def disjoint_union(a, b):
    """(a \\sqcup b); b's vertices and darts are shifted by a.nv and a.nd."""
    ov, od = a.nv, len(a.head)

    def sh(x):
        return x + od if x != NIL else NIL

    return PC(a.nv + b.nv, a.lo + b.lo, a.hi + b.hi,
              a.head + [h + ov for h in b.head],
              a.rev + [r + od for r in b.rev],
              a.succ + [sh(s) for s in b.succ],
              a.pred + [sh(p) for p in b.pred])


# ---------------------------------------------------------------------------
# Algorithm A.2.1 homomorphism
# ---------------------------------------------------------------------------
G_INCLUDE = 0      # source range includes target range   ("ginclude")
G_INTERSECT = 1    # the two ranges intersect             ("gintersection")
G_DOMINANT = 2     # intersect, and (hi_src = INF or hi_tgt < 9)  (A.9.15)
G_NONE = 3         # no degree constraint


def homomorphism(src, e, tgt, et, mode):
    """Algorithm A.2.1: the homomorphism src -> tgt with e -> et, or None.

    The degree predicate g(lo(v), hi(v), lo*(v*), hi*(v*)) is chosen by
    `mode`. For G_INCLUDE the source range must contain the target range
    (this is how A.6.8 and A.9.1 use it: lo(v) <= deg <= hi(v) for every
    concrete degree of the image). Returns (vmap, dmap) or None.
    """
    s_head, s_rev, s_succ, s_pred = src.head, src.rev, src.succ, src.pred
    s_lo, s_hi = src.lo, src.hi
    t_head, t_rev, t_succ, t_pred = tgt.head, tgt.rev, tgt.succ, tgt.pred
    t_lo, t_hi = tgt.lo, tgt.hi
    dmap = [NIL] * len(s_head)
    vmap = [NIL] * src.nv
    q = deque()
    q.append((e, et))
    pop = q.popleft
    push = q.append
    while q:
        f, fs = pop()
        m = dmap[f]
        if m != NIL:
            if m != fs:
                return None
            continue
        dmap[f] = fs
        h = s_head[f]
        hs = t_head[fs]
        mh = vmap[h]
        if mh != NIL and mh != hs:
            return None
        vmap[h] = hs
        if mode == G_INCLUDE:
            if not (s_lo[h] <= t_lo[hs] and t_hi[hs] <= s_hi[h]):
                return None
        elif mode == G_INTERSECT:
            if s_lo[h] > t_hi[hs] or t_lo[hs] > s_hi[h]:
                return None
        elif mode == G_DOMINANT:
            if s_lo[h] > t_hi[hs] or t_lo[hs] > s_hi[h]:
                return None
            if not (s_hi[h] == INF or t_hi[hs] < 9):
                return None
        push((s_rev[f], t_rev[fs]))
        x = s_succ[f]
        if x != NIL:
            y = t_succ[fs]
            if y == NIL:
                return None
            push((x, y))
        x = s_pred[f]
        if x != NIL:
            y = t_pred[fs]
            if y == NIL:
                return None
            push((x, y))
    return vmap, dmap


# ---------------------------------------------------------------------------
# Algorithm A.3.1 freeHomomorphismTriangulation
# ---------------------------------------------------------------------------
def _find(parent, x):
    root = x
    while parent[root] != root:
        root = parent[root]
    while parent[x] != root:  # path compression; roots are unchanged
        parent[x], x = root, parent[x]
    return root


def free_hom_triangulation(pc, pairs):
    """Algorithm A.3.1 on the underlying pseudo-triangulation of pc.

    Returns (nv', head', rev', succ', pred', vmap, dmap): the image
    Z* (compactly renumbered, roots in increasing order of their original
    index) and the map phi* as (vmap, dmap).
    """
    head, rev = pc.head, pc.rev
    succ = pc.succ[:]  # succ*, pred*: modified on roots (lines 25-30)
    pred = pc.pred[:]
    nd = len(head)
    ufv = list(range(pc.nv))
    ufd = list(range(nd))
    q = deque(pairs)
    while q:
        e, f = q.popleft()
        re = _find(ufd, e)
        rf = _find(ufd, f)
        if re == rf:  # line 9: same(e, f)
            continue
        hv = _find(ufv, head[e])  # lines 12-13
        hw = _find(ufv, head[f])
        if hv != hw:
            ufv[hv] = hw
        ufd[re] = rf  # line 17: f* becomes the root representative
        q.append((rev[re], rev[rf]))  # line 18
        se, sf = succ[re], succ[rf]
        pe, pf = pred[re], pred[rf]
        if se != NIL and sf != NIL:  # lines 19-21
            q.append((se, sf))
        if pe != NIL and pf != NIL:  # lines 22-24
            q.append((pe, pf))
        if se != NIL and sf == NIL:  # lines 25-27
            succ[rf] = se
        if pe != NIL and pf == NIL:  # lines 28-30
            pred[rf] = pe
    # lines 32-41: roots become the vertices and darts of Z*
    vnew = [NIL] * pc.nv
    vroots = []
    for v in range(pc.nv):
        if _find(ufv, v) == v:
            vnew[v] = len(vroots)
            vroots.append(v)
    dnew = [NIL] * nd
    droots = []
    for d in range(nd):
        if _find(ufd, d) == d:
            dnew[d] = len(droots)
            droots.append(d)
    vmap = [vnew[_find(ufv, v)] for v in range(pc.nv)]
    dmap = [dnew[_find(ufd, d)] for d in range(nd)]
    nhead = [vmap[head[d]] for d in droots]
    nrev = [dmap[rev[d]] for d in droots]
    nsucc = [dmap[succ[d]] if succ[d] != NIL else NIL for d in droots]
    npred = [dmap[pred[d]] if pred[d] != NIL else NIL for d in droots]
    return len(vroots), nhead, nrev, nsucc, npred, vmap, dmap


# ---------------------------------------------------------------------------
# Algorithm A.4.1 dartIdentification
# ---------------------------------------------------------------------------
def dart_identification(pc, pairs):
    """Algorithm A.4.1. Returns (PC*, (vmap, dmap)) or None.

    None means a loop error or a degree-mismatch error.
    """
    nv, head, rev, succ, pred, vmap, dmap = free_hom_triangulation(pc, pairs)
    for d in range(len(head)):  # lines 2-4: loop error
        if head[d] == head[rev[d]]:
            return None
    lo = [1] * nv  # line 5
    hi = [INF] * nv
    plo, phi_ = pc.lo, pc.hi
    for v in range(pc.nv):  # lines 6-12
        w = vmap[v]
        a = lo[w] if lo[w] > plo[v] else plo[v]
        b = hi[w] if hi[w] < phi_[v] else phi_[v]
        if a > b:
            return None  # degree mismatch
        lo[w] = a
        hi[w] = b
    return PC(nv, lo, hi, head, rev, succ, pred), (vmap, dmap)


def compose(first, second):
    """second o first, for maps given as (vmap, dmap)."""
    v1, d1 = first
    v2, d2 = second
    return [v2[x] for x in v1], [d2[x] for x in d1]


# ---------------------------------------------------------------------------
# Algorithms A.4.3 - A.4.9: free homomorphism of a pseudo-configuration
# ---------------------------------------------------------------------------
def inner_subdegree_error(pc, inc):
    """Algorithm A.4.5: an inner vertex with d_Z(v) < lo(v)."""
    deg, bnd, _ = inc
    lo = pc.lo
    for v in range(pc.nv):
        if not bnd[v] and deg[v] < lo[v]:
            return True
    return False


def vertex_single_degree_issue(pc, inc):
    """Algorithm A.4.6: first vertex with lo = hi and a degree issue."""
    deg, bnd, _ = inc
    lo, hi = pc.lo, pc.hi
    for v in range(pc.nv):
        if lo[v] != hi[v]:
            continue
        if lo[v] < deg[v]:
            return v
        if bnd[v] and deg[v] == lo[v]:
            return v
    return None


def add_boundary_darts(pc, v, inc):
    """Algorithm A.4.8. Returns the new PC or None (boundary error)."""
    head, rev, succ, pred = pc.head, pc.rev, pc.succ, pc.pred
    efirst = elast = NIL
    for e in range(len(head)):
        if head[e] == v:
            if pred[e] == NIL:
                efirst = e
            if succ[e] == NIL:
                elast = e
    assert efirst != NIL and elast != NIL
    u = head[rev[efirst]]
    w = head[rev[elast]]
    if u == w:
        return None  # boundary error
    z = pc.copy()
    duw = len(z.head)
    dwu = duw + 1
    # the pseudo-code overwrites these two pointers; in a pseudo-configuration
    # they are nil (M5). We check rather than assume.
    assert z.succ[rev[efirst]] == NIL, "succ(rev(e_first)) not nil"
    assert z.pred[rev[elast]] == NIL, "pred(rev(e_last)) not nil"
    z.head += [u, w]
    z.rev += [dwu, duw]
    z.succ += [NIL, rev[elast]]
    z.pred += [rev[efirst], NIL]
    z.pred[efirst] = elast
    z.succ[elast] = efirst
    z.succ[rev[efirst]] = duw
    z.pred[rev[elast]] = dwu
    return z


def fix_single_degree_issue(pc, v, inc):
    """Algorithm A.4.7. Returns (PC*, map) or None."""
    deg, bnd, first = inc
    d = pc.lo[v]
    if d < deg[v]:
        e = first[v]  # for a boundary vertex: the dart with pred = nil
        f = e
        for _ in range(d):
            f = pc.succ[f]
            assert f != NIL
        return dart_identification(pc, [(e, f)])
    if bnd[v] and d == deg[v]:
        z = add_boundary_darts(pc, v, inc)
        if z is None:
            return None
        return z, (list(range(pc.nv)), list(range(len(pc.head))))
    raise AssertionError("fix_single_degree_issue without an issue")


def single_out_lower_degree(pc, inc):
    """Algorithm A.4.9: split [lo, hi] into {lo} and [lo+1, hi]."""
    deg, _, _ = inc
    lo, hi = pc.lo, pc.hi
    for v in range(pc.nv):
        if lo[v] < hi[v] and lo[v] <= deg[v]:
            z1 = PC(pc.nv, lo[:], hi[:], pc.head, pc.rev, pc.succ, pc.pred)
            z1.hi[v] = lo[v]
            z2 = PC(pc.nv, lo[:], hi[:], pc.head, pc.rev, pc.succ, pc.pred)
            z2.lo[v] = lo[v] + 1
            return z1, z2
    return None


def resolve_degree_issues(pc):
    """Algorithm A.4.4. Returns a list of (PC, map from pc)."""
    out = []
    ident = (list(range(pc.nv)), list(range(len(pc.head))))
    q = deque([(pc, ident)])
    while q:
        z, phi = q.popleft()
        inc = z.incidence()
        if inner_subdegree_error(z, inc):
            continue
        v = vertex_single_degree_issue(z, inc)
        if v is not None:
            a = fix_single_degree_issue(z, v, inc)
            if a is not None:
                z2, psi = a
                q.append((z2, compose(phi, psi)))
            continue
        b = single_out_lower_degree(z, inc)
        if b is not None:
            q.append((b[0], phi))
            q.append((b[1], phi))
            continue
        out.append((z, phi))
    return out


def free_hom_configuration(pc, pairs):
    """Algorithm A.4.3 freeHomomorphismConfiguration.

    Returns a list of (PC*, (vmap, dmap)) with the map from pc.
    """
    a = dart_identification(pc, pairs)
    if a is None:
        return []
    z, phi = a
    return [(z2, compose(phi, psi)) for z2, psi in resolve_degree_issues(z)]
