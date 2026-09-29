"""Webs (SPEC Sec. 3): darts, rotation systems, faces, Tait colourings, REBUILD.

Edge keys used everywhere in Implementation A:
  interval edge with edge id e (= min dart)  ->  key e      (e >= 0)
  vertexless circle with id c                ->  key -1-c   (< 0)
"""

from . import webdata


def sigma(d):
    r = d % 3
    return d - r + (r + 1) % 3


def vert(d):
    return d // 3


def ckey(c):
    return -1 - c


class Web:
    __slots__ = ("V", "alpha", "m", "_faces", "_face_of")

    def __init__(self, V, alpha, m, check=True):
        self.V = V
        self.alpha = alpha
        self.m = m
        self._faces = None
        self._face_of = None
        if check:
            n = 3 * V
            if len(alpha) != n:
                raise ValueError("alpha length")
            for d in range(n):
                a = alpha[d]
                if a == d or alpha[a] != d:
                    raise ValueError("alpha is not a fixed-point-free involution")

    # --- faces -----------------------------------------------------------
    def _compute_faces(self):
        n = 3 * self.V
        alpha = self.alpha
        face_of = [-1] * n
        faces = []
        for d in range(n):
            if face_of[d] >= 0:
                continue
            fid = len(faces)
            orb = []
            x = d
            while face_of[x] < 0:
                face_of[x] = fid
                orb.append(x)
                x = sigma(alpha[x])
            if x != d:
                raise AssertionError("phi orbit not closed")
            faces.append(tuple(orb))
        self._faces = faces
        self._face_of = face_of

    def faces(self):
        """Faces in canonical form (orbit from its min dart), sorted by min dart."""
        if self._faces is None:
            self._compute_faces()
        return self._faces

    def face_of(self):
        if self._faces is None:
            self._compute_faces()
        return self._face_of

    def edge_ids(self):
        return [d for d in range(3 * self.V) if d < self.alpha[d]]

    def ekey(self, d):
        a = self.alpha[d]
        return d if d < a else a

    def has_bridge(self):
        fo = self.face_of()
        alpha = self.alpha
        for d in range(3 * self.V):
            if fo[d] == fo[alpha[d]]:
                return True
        return False

    def components_with_vertices(self):
        V = self.V
        par = list(range(V))

        def find(x):
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            return x

        for d in range(3 * V):
            a, b = find(d // 3), find(self.alpha[d] // 3)
            if a != b:
                par[a] = b
        return len({find(v) for v in range(V)})

    def vertex_components(self):
        """comp[v] = index of the connected component of vertex v (components
        numbered by their smallest vertex, in increasing order)."""
        V = self.V
        comp = [-1] * V
        nc = 0
        alpha = self.alpha
        for s in range(V):
            if comp[s] >= 0:
                continue
            comp[s] = nc
            stack = [s]
            while stack:
                v = stack.pop()
                for k in range(3):
                    w = alpha[3 * v + k] // 3
                    if comp[w] < 0:
                        comp[w] = nc
                        stack.append(w)
            nc += 1
        return comp, nc

    def validate(self):
        V = self.V
        E = 3 * V // 2
        F = len(self.faces())
        comps = self.components_with_vertices()
        if V - E + F != 2 * comps:
            raise AssertionError("Euler characteristic check failed: V-E+F=%d, comps=%d"
                                 % (V - E + F, comps))

    def all_keys(self):
        """Edge keys in canonical Tait order: edges by id, then circles."""
        return self.edge_ids() + [ckey(c) for c in range(self.m)]

    # --- Tait colourings (SPEC 3.3), canonical lexicographic order ----------
    def tait_colourings(self):
        edges = self.edge_ids()
        alpha = self.alpha
        pos = {e: i for i, e in enumerate(edges)}
        nE = len(edges)
        # for each edge index, the edge indices at its two end vertices that come earlier
        vedges = []
        for v in range(self.V):
            vedges.append([pos[self.ekey(3 * v + k)] for k in range(3)])
        constraints = [[] for _ in range(nE)]
        for v in range(self.V):
            es = vedges[v]
            if len(set(es)) < 3:
                return []  # a loop: no Tait colouring
            for a in es:
                for b in es:
                    if b < a:
                        constraints[a].append(b)
        out = []
        cur = [0] * nE

        def rec(i):
            if i == nE:
                out.append(tuple(cur))
                return
            cons = constraints[i]
            for c in (1, 2, 3):
                ok = True
                for b in cons:
                    if cur[b] == c:
                        ok = False
                        break
                if ok:
                    cur[i] = c
                    rec(i + 1)
            cur[i] = 0

        if nE:
            rec(0)
        else:
            out = [()]
        if self.m:
            res = []
            import itertools
            for t in out:
                for cs in itertools.product((1, 2, 3), repeat=self.m):
                    res.append(t + cs)
            out = res
        return out


def from_rotation(text):
    items = text.split()
    nbr = {}
    for it in items:
        v, rest = it.split(":")
        nbr[int(v)] = [int(x) for x in rest.split(",")]
    V = len(nbr)
    assert sorted(nbr) == list(range(V))
    alpha = [None] * (3 * V)
    for v in range(V):
        for k, w in enumerate(nbr[v]):
            lst = nbr[w]
            if lst.count(v) != 1:
                raise ValueError("not a simple graph entry %d-%d" % (v, w))
            alpha[3 * v + k] = 3 * w + lst.index(v)
    return Web(V, alpha, 0)


def load(name):
    if name == "circle":
        return Web(0, [], 1)
    if name == "two_circles":
        return Web(0, [], 2)
    if name == "theta":
        return Web(2, list(webdata.THETA_ALPHA), 0)
    return from_rotation(webdata.ROT[name])


def count_automorphisms(K):
    """Number of map automorphisms incl. reflections (= |Aut| of the graph for
    3-connected planar graphs).  Used only to validate the transcription."""
    n = 3 * K.V
    alpha = K.alpha

    def sig_inv(d):
        r = d % 3
        return d - r + (r + 2) % 3

    count = 0
    for orient in (0, 1):
        for img0 in range(n):
            mp = {0: img0}
            stack = [0]
            ok = True
            while stack and ok:
                d = stack.pop()
                e = mp[d]
                nxt = [(alpha[d], alpha[e]),
                       (sigma(d), sigma(e) if orient == 0 else sig_inv(e))]
                for a, b in nxt:
                    if a in mp:
                        if mp[a] != b:
                            ok = False
                            break
                    else:
                        mp[a] = b
                        stack.append(a)
            if ok and len(mp) == n and len(set(mp.values())) == n:
                count += 1
    return count


# --- REBUILD (SPEC 3.4) ---------------------------------------------------

STATS = {"rebuilds": 0, "join_circles": 0, "multi_circle_rebuilds": 0}


def rebuild(K, D, NV, J):
    """REBUILD(K; D; NV; J).

    NV: list of triples of slots; a slot is ('p', dart) or ('l', label).
    J : list of join pairs (p, q) of ports.
    Returns (K2, dmap, join_keys, s) where join_keys[i] is the K2 edge key of
    join i and s is the number of surviving vertices.
    """
    Dset = set(D)
    alpha = K.alpha
    surv = [v for v in range(K.V) if v not in Dset]
    newidx = {v: i for i, v in enumerate(surv)}
    s = len(surv)
    Vn = s + len(NV)
    dmap = {}
    for v in surv:
        b = 3 * newidx[v]
        for k in range(3):
            dmap[3 * v + k] = b + k
    portslot = {}
    labels = {}
    for i, tri in enumerate(NV):
        assert len(tri) == 3
        for k, slot in enumerate(tri):
            nd = 3 * (s + i) + k
            kind, val = slot
            if kind == 'p':
                assert vert(val) in Dset and val not in portslot
                portslot[val] = nd
            else:
                labels.setdefault(val, []).append(nd)
    joinpart = {}
    for idx, (p, q) in enumerate(J):
        assert vert(p) in Dset and vert(q) in Dset
        assert p not in joinpart and q not in joinpart and p != q
        joinpart[p] = (q, idx)
        joinpart[q] = (p, idx)
    alpha2 = [None] * (3 * Vn)
    join_dart = [None] * len(J)

    def resolve(x):
        vis = []
        while True:
            if vert(x) not in Dset:
                return dmap[x], vis
            if x in portslot:
                return portslot[x], vis
            if x in joinpart:
                y, idx = joinpart[x]
                vis.append(idx)
                x = alpha[y]
                continue
            raise AssertionError("REBUILD reached an unassigned dart of a deleted vertex")

    starts = [(dmap[d], alpha[d]) for d in sorted(dmap)] + \
             [(portslot[p], alpha[p]) for p in sorted(portslot)]
    for nd, x in starts:
        partner, vis = resolve(x)
        alpha2[nd] = partner
        for idx in vis:
            join_dart[idx] = nd
    for lab in sorted(labels, key=repr):
        ds = labels[lab]
        assert len(ds) == 2
        alpha2[ds[0]] = ds[1]
        alpha2[ds[1]] = ds[0]
    for d in range(3 * Vn):
        assert alpha2[d] is not None and alpha2[alpha2[d]] == d and alpha2[d] != d
    # circles from closed join chains
    m2 = K.m
    join_keys = [None] * len(J)
    for idx in range(len(J)):
        if join_dart[idx] is not None:
            nd = join_dart[idx]
            join_keys[idx] = min(nd, alpha2[nd])
    for idx in range(len(J)):
        if join_keys[idx] is not None:
            continue
        cid = m2
        m2 += 1
        p, q = J[idx]
        join_keys[idx] = ckey(cid)
        x = alpha[q]
        while x != p:
            y, idx2 = joinpart[x]
            assert join_keys[idx2] is None or join_keys[idx2] == ckey(cid)
            join_keys[idx2] = ckey(cid)
            x = alpha[y]
    STATS["rebuilds"] += 1
    STATS["join_circles"] += m2 - K.m
    if m2 - K.m > 1:
        STATS["multi_circle_rebuilds"] += 1
    K2 = Web(Vn, alpha2, m2, check=False)
    return K2, dmap, join_keys, s
