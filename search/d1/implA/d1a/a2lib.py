"""Phase 2b helpers: automorphisms (A2.6), KM half-foams (A2.5), F-spans (A2.7)."""

import itertools

from .web import sigma, vert
from .foam import HalfFoam, degree


# ---------------------------------------------------------------- A2.6
def sigma_inv(d):
    r = d % 3
    return d - r + (r + 2) % 3


def automorphisms(K):
    """List of dart maps, in the order (0,+1), (0,-1), (1,+1), ... (A2.6).
    Only consistent bijective propagations are returned; the caller asserts
    that every pair gives one."""
    n = 3 * K.V
    alpha = K.alpha
    out = []
    for ds in range(n):
        for eps in (1, -1):
            g = [None] * n
            g[0] = ds
            stack = [0]
            ok = True
            while stack and ok:
                x = stack.pop()
                gx = g[x]
                for y, gy in ((alpha[x], alpha[gx]),
                              (sigma(x), sigma(gx) if eps == 1 else sigma_inv(gx))):
                    if g[y] is None:
                        g[y] = gy
                        stack.append(y)
                    elif g[y] != gy:
                        ok = False
                        break
            if ok and None not in g and len(set(g)) == n:
                out.append((ds, eps, g))
            else:
                out.append((ds, eps, None))
    return out


def tait_perms(K, taits, auts):
    """For each automorphism g: perm[s] = index of the colouring s o g-hat."""
    edges = K.edge_ids()
    assert K.m == 0
    pos = {e: i for i, e in enumerate(edges)}
    index = {t: i for i, t in enumerate(taits)}
    perms = []
    for ds, eps, g in auts:
        ghat = [pos[K.ekey(g[e])] for e in edges]
        perm = [index[tuple(t[ghat[k]] for k in range(len(edges)))] for t in taits]
        perms.append(perm)
    return perms


def apply_perm(a, perm):
    """(g.a)(s) = a(perm[s]) on a bit-plane pair."""
    A, B = a
    nA = nB = 0
    for s, p in enumerate(perm):
        if (A >> p) & 1:
            nA |= 1 << s
        if (B >> p) & 1:
            nB |= 1 << s
    return (nA, nB)


def foam_image(H, K, g):
    """g(H) as a half-foam: the same facets and seams, owner(g-hat(e)) = owner(e)."""
    own = {}
    for e, f in H.owner.items():
        own[K.ekey(g[e])] = f
    return HalfFoam(H.chi, H.dots, own, H.seams, H.nv)


# ---------------------------------------------------------------- A2.5 KM
def km_sets(K):
    faces = K.faces()
    fo = K.face_of()
    nF = len(faces)
    adj = set()
    for d in range(3 * K.V):
        a, b = fo[d], fo[K.alpha[d]]
        adj.add((min(a, b), max(a, b)))
    out = []
    for S in itertools.combinations(range(nF), 3):
        if all((min(x, y), max(x, y)) not in adj for x, y in itertools.combinations(S, 2)):
            out.append(S)
    return out, adj


def face_4colourings(K):
    """All proper 4-colourings of the faces (adjacent faces differ)."""
    faces = K.faces()
    nF = len(faces)
    _, adj = km_sets(K)
    nb = [[] for _ in range(nF)]
    for a, b in adj:
        if a != b:
            nb[a].append(b)
            nb[b].append(a)
    col = [0] * nF
    out = []

    def rec(i):
        if i == nF:
            out.append(tuple(col))
            return
        for c in (1, 2, 3, 4):
            if all(col[j] != c for j in nb[i] if j < i):
                col[i] = c
                rec(i + 1)
        col[i] = 0
    rec(0)
    return out


def km_foam(K, S, dots=None):
    """F_S in facet-seam form (A2.5).  Returns (HalfFoam, number of facets)."""
    fo = K.face_of()
    nF = len(K.faces())
    T = [f for f in range(nF) if f not in S]
    FL = {f: i for i, f in enumerate(T)}
    edges = K.edge_ids()
    sides = {e: (fo[e], fo[K.alpha[e]]) for e in edges}
    WL = {}
    n = len(T)
    for e in edges:
        f, g = sides[e]
        if f not in S and g not in S:
            WL[e] = n
            n += 1
    owner = {}
    for e in edges:
        f, g = sides[e]
        if e in WL:
            owner[e] = WL[e]
        else:
            assert (f in S) != (g in S)
            owner[e] = FL[g] if f in S else FL[f]
    seams = []
    for e in edges:
        if e in WL:
            f, g = sides[e]
            seams.append((FL[f], FL[g], WL[e]))
    for v in range(K.V):
        seams.append(tuple(owner[K.ekey(3 * v + k)] for k in range(3)))
    nv = sum(1 for v in range(K.V) if all(fo[3 * v + k] not in S for k in range(3)))
    H = HalfFoam([1] * n, list(dots) if dots is not None else [0] * n, owner, seams, nv)
    return H, n


# ---------------------------------------------------------------- F-spans
class FSpan:
    """F_2 span of ints (bit vectors); pivot = lowest set bit."""
    __slots__ = ("piv", "rows")

    def __init__(self):
        self.piv = {}
        self.rows = []

    def reduce(self, x):
        piv = self.piv
        while x:
            p = x & -x
            r = piv.get(p)
            if r is None:
                return x
            x ^= r
        return 0

    def add(self, x):
        y = self.reduce(x)
        if not y:
            return False
        self.piv[y & -y] = y
        self.rows.append(x)
        return True

    def contains(self, x):
        return self.reduce(x) == 0

    def __len__(self):
        return len(self.piv)

    def copy(self):
        c = FSpan()
        c.piv = dict(self.piv)
        c.rows = list(self.rows)
        return c


def fview(a, T):
    """A2.7 F-view: bits v(t)&1 for t in order, then v(t)>>1."""
    return a[0] | (a[1] << T)


def from_fview(x, T):
    m = (1 << T) - 1
    return (x & m, x >> T)


def f_rank(rows):
    S = FSpan()
    for r in rows:
        S.add(r)
    return len(S)


def det_f2(M):
    """Determinant over F of a square 0/1 matrix (list of lists)."""
    n = len(M)
    rows = [sum(b << j for j, b in enumerate(r)) for r in M]
    return 1 if f_rank(rows) == n else 0
