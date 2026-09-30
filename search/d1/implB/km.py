"""Kronheimer-Mrowka half-foams F_S of W1 (SPEC Amendment 2, A2.5, families KM
and KMd).  This is B's small facet-based module (A2.11), separate from Mode T:
it builds the facet-seam half-foam and evaluates its a-vector directly by the
SPEC 4.5 formula (enumerating colourings of the facets)."""

from itertools import combinations, combinations_with_replacement, product

from core import OMEGA_POW

EXPECTED_MIN_DARTS = [0, 1, 2, 4, 7, 10, 15, 18, 25, 31, 37, 45]


def face_sets(K):
    """The 3-sets of pairwise non-adjacent faces, lexicographic in sorted index
    triples.  Faces are indexed by increasing minimum dart (K.faces order)."""
    nf = len(K.faces)
    adj = [set() for _ in range(nf)]
    for d in range(3 * K.V):
        f, g = K.face_of[d], K.face_of[K.alpha[d]]
        if f != g:
            adj[f].add(g)
    out = []
    for tri in combinations(range(nf), 3):
        if all(b not in adj[a] for a, b in combinations(tri, 2)):
            out.append(tri)
    return out


def build_foam(K, S):
    """Facet-seam data of the undotted F_S.  Returns dict with facets (chi list),
    owner (item -> facet), seams, nv, deg0 (degree without dots)."""
    Sset = set(S)
    nf = len(K.faces)
    T = [f for f in range(nf) if f not in Sset]
    fl = {f: i for i, f in enumerate(T)}
    wall_edges = []
    for j, e in enumerate(K.edge_ids):
        f, g = K.face_of[e], K.face_of[K.alpha[e]]
        if f not in Sset and g not in Sset:
            wall_edges.append(j)
    wl = {j: len(T) + k for k, j in enumerate(wall_edges)}
    nfac = len(T) + len(wall_edges)
    owner = {}
    for j, e in enumerate(K.edge_ids):
        f, g = K.face_of[e], K.face_of[K.alpha[e]]
        if j in wl:
            owner[j] = wl[j]
        else:
            assert (f in Sset) != (g in Sset), "edge between two S faces"
            owner[j] = fl[g] if f in Sset else fl[f]
    seams = []
    for j in wall_edges:
        e = K.edge_ids[j]
        f, g = K.face_of[e], K.face_of[K.alpha[e]]
        seams.append((fl[f], fl[g], wl[j]))
    nv = 0
    for v in range(K.V):
        es = [K.eidx[3 * v + k] for k in range(3)]
        seams.append(tuple(owner[j] for j in es))
        faces_v = {K.face_of[3 * v + k] for k in range(3)}
        if not (faces_v & Sset):
            nv += 1
    chi = [1] * nfac
    deg0 = -2 * sum(chi) + 3 * nv + 3 * K.V // 2
    return {"chi": chi, "owner": owner, "seams": seams, "nv": nv, "nfac": nfac,
            "deg0": deg0, "T": T, "walls": wall_edges}


def colouring_table(K, foam, tait):
    """For each Tait colouring t (index k): list of admissible facet colourings
    c (tuples) with c(owner(e)) = t(e), plus their (chi12, chi13)."""
    nfac = foam["nfac"]
    owner = foam["owner"]
    seams = foam["seams"]
    chi = foam["chi"]
    nv = foam["nv"]
    halfV = K.V // 2
    table = []
    for t in tait:
        fixed = [0] * nfac
        ok = True
        for j in range(K.E):
            g = owner[j]
            if fixed[g] == 0:
                fixed[g] = t[j]
            elif fixed[g] != t[j]:
                ok = False
                break
        rows = []
        if ok:
            free = [g for g in range(nfac) if fixed[g] == 0]
            for combo in product((1, 2, 3), repeat=len(free)):
                c = fixed[:]
                for g, col in zip(free, combo):
                    c[g] = col
                if all(c[a] != c[b] and c[a] != c[x] and c[b] != c[x] for (a, b, x) in seams):
                    x12 = sum(chi[g] for g in range(nfac) if c[g] in (1, 2)) - nv - halfV
                    x13 = sum(chi[g] for g in range(nfac) if c[g] in (1, 3)) - nv - halfV
                    rows.append((tuple(c), x12, x13))
        table.append(rows)
    return table


def avector(table, dots):
    """hex string of the a-vector for the given dot vector (list per facet)."""
    out = []
    for rows in table:
        acc = 0
        for c, x12, x13 in rows:
            e = -x12 - 2 * x13
            for g, dg in dots:
                e += dg * (c[g] - 1)
            acc ^= OMEGA_POW[e % 3]
        out.append("0123"[acc])
    return "".join(out)


def km_members(K, tait, kmax):
    """Yield (km_darts, dots_list, deg, hex) in family order: S in order, then
    k = 0..kmax, then multisets of k facets (non-decreasing tuples, lex)."""
    assert [f[0] for f in K.faces] == EXPECTED_MIN_DARTS
    sets = face_sets(K)
    assert len(sets) == 20
    for S in sets:
        foam = build_foam(K, S)
        assert foam["nfac"] == 24 and foam["nv"] == 5 and foam["deg0"] == -3
        table = colouring_table(K, foam, tait)
        darts = sorted(K.faces[f][0] for f in S)
        for k in range(kmax + 1):
            for ms in combinations_with_replacement(range(foam["nfac"]), k):
                cnt = {}
                for g in ms:
                    cnt[g] = cnt.get(g, 0) + 1
                yield darts, list(ms), foam["deg0"] + 2 * k, avector(table, sorted(cnt.items()))


def check_face_colourings(K, sets):
    """The 20 sets are exactly the colour classes of the proper face
    4-colourings of K (SPEC A2.5, spec-check); returns (#4-colourings, ok)."""
    nf = len(K.faces)
    adj = [set() for _ in range(nf)]
    for d in range(3 * K.V):
        f, g = K.face_of[d], K.face_of[K.alpha[d]]
        if f != g:
            adj[f].add(g)
    cols = []
    col = [0] * nf

    def rec(i):
        if i == nf:
            cols.append(col[:])
            return
        for c in range(4):
            if all(col[j] != c for j in adj[i] if j < i):
                col[i] = c
                rec(i + 1)
        col[i] = 0
    rec(0)
    classes = set()
    for c in cols:
        for x in range(4):
            cls = tuple(sorted(f for f in range(nf) if c[f] == x))
            classes.add(cls)
    return len(cols), classes == set(sets)
