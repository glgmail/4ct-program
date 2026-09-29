"""The twelve elementary cobordisms (SPEC Sec. 5) as web changes plus records.

Every op function takes the TOP web K and returns an Op with the bottom web
K' (= Kp), the deleted vertex set, dmap, and a function building the record
C : K' -> K for a given variant (dots / smoothing already fixed by the op).
"""

from .web import Web, sigma, vert, ckey, rebuild

STATS = {"records": 0, "merged_nominal_facets": 0}

DEG = {"C1": -2, "C1d": 0, "C1dd": 2, "C2": -1, "C2d": 1, "C3": 0,
       "C4a": 0, "C4b": 0, "zip": 1, "unzip": 1, "saddle": 2, "ih": 1}


class Record:
    __slots__ = ("label", "facets", "seams", "nv", "Vt", "Vb", "ident", "deg")

    def __init__(self, label, facets, seams, nv, Vt, Vb, ident):
        self.label = label
        self.facets = facets      # list of (chi, dots, bot tuple, top tuple)
        self.seams = seams        # list of triples of local facet indices
        self.nv = nv
        self.Vt = Vt
        self.Vb = Vb
        self.ident = ident        # list of (K key, K' key)
        self.deg = DEG[label]


def sheet(key):
    return 1 if key >= 0 else 0


def _identity(K, Kp, dmap, tops):
    """Identity edges/circles (SPEC 3.5): list of (K key, K' key)."""
    ident = []
    alpha = K.alpha
    for e in K.edge_ids():
        if e in tops:
            continue
        a = alpha[e]
        if e not in dmap or a not in dmap:
            raise AssertionError("edge %d touches a deleted vertex but is not a top edge" % e)
        d1, d2 = dmap[e], dmap[a]
        if Kp.alpha[d1] != d2:
            raise AssertionError("identity edge not preserved")
        ident.append((e, min(d1, d2)))
    for c in range(K.m):
        k = ckey(c)
        if k in tops:
            continue
        if c >= Kp.m:
            raise AssertionError("identity circle missing in K'")
        ident.append((k, k))
    return ident


def build_record(K, Kp, dmap, label, nominal, seams, nv, Vt, Vb):
    """nominal: list of [chi, dots, bot list, top list].  Nominal facets that
    share a bottom K'-edge are one facet (SPEC 4.3)."""
    n = len(nominal)
    par = list(range(n))

    def find(x):
        while par[x] != x:
            x = par[x]
        return x

    seen = {}
    for i, (_, _, bot, _) in enumerate(nominal):
        for b in bot:
            if b in seen:
                j = seen[b]
                if set(nominal[j][2]) != set(bot):
                    raise AssertionError("two nominal facets share part of their bottom")
                if nominal[j][0] != nominal[i][0]:
                    raise AssertionError("merged sheets with different chi")
                ri, rj = find(i), find(j)
                if ri != rj:
                    STATS["merged_nominal_facets"] += 1
                    par[max(ri, rj)] = min(ri, rj)
            else:
                seen[b] = i
    idx = {}
    facets = []
    for i in range(n):
        r = find(i)
        if r not in idx:
            idx[r] = len(facets)
            chi, dots, bot, top = nominal[i]
            facets.append([chi, dots, list(dict.fromkeys(bot)), list(dict.fromkeys(top))])
        else:
            f = facets[idx[r]]
            f[1] += nominal[i][1]
            for t in nominal[i][3]:
                if t not in f[3]:
                    f[3].append(t)
    remap = [idx[find(i)] for i in range(n)]
    seams2 = [tuple(remap[x] for x in s) for s in seams]
    facets = [(f[0], f[1], tuple(f[2]), tuple(f[3])) for f in facets]
    # partition checks
    tops = {}
    for g, f in enumerate(facets):
        for t in f[3]:
            if t in tops:
                raise AssertionError("K-edge in two local facets")
            tops[t] = g
    ident = _identity(K, Kp, dmap, tops)
    kkeys = set(K.all_keys())
    covered = set(tops) | {a for a, _ in ident}
    if covered != kkeys or len(tops) + len(ident) != len(kkeys):
        raise AssertionError("K-edges not partitioned by identity/top")
    bots = {}
    for g, f in enumerate(facets):
        for b in f[2]:
            if b in bots:
                raise AssertionError("K'-edge in two distinct local facets after merging")
            bots[b] = g
    kpkeys = set(Kp.all_keys())
    idimg = [b for _, b in ident]
    if len(set(idimg)) != len(idimg) or set(idimg) & set(bots) or \
            set(idimg) | set(bots) != kpkeys:
        raise AssertionError("K'-edges not partitioned by identity/bottom")
    rec = Record(label, facets, seams2, nv, Vt, Vb, ident)
    STATS["records"] += 1
    # degree (SPEC 4.3 item 5) against B19 Table 1
    sd = sum(f[1] for f in facets)
    sc = sum(f[0] for f in facets)
    b = sum(1 for f in facets for x in f[2] if x >= 0)
    twice = 2 * (2 * sd - 2 * (sc - b) + 3 * nv) + 3 * (Vt - Vb)
    if twice != 2 * DEG[label]:
        raise AssertionError("record degree %s != table for %s" % (twice / 2, label))
    return rec


class Op:
    __slots__ = ("K", "Kp", "D", "dmap", "make", "keep_marker", "kind", "info")

    def __init__(self, K, Kp, D, dmap, make, keep_marker, kind="", info=None):
        self.K = K
        self.Kp = Kp
        self.D = D
        self.dmap = dmap
        self.make = make          # label -> Record
        self.keep_marker = keep_marker
        self.kind = kind
        self.info = info or {}


def _idmap(K):
    return {d: d for d in range(3 * K.V)}


# 5.1 disk
def op_disk(K):
    assert K.m >= 1
    Kp = Web(K.V, K.alpha, K.m - 1, check=False)
    dmap = _idmap(K)
    top = ckey(K.m - 1)

    def make(label):
        dots = {"C1": 0, "C1d": 1, "C1dd": 2}[label]
        return build_record(K, Kp, dmap, label, [[1, dots, [], [top]]], [], 0, 0, 0)
    return Op(K, Kp, set(), dmap, make, True, "disk")


# 5.2 bigon
def op_bigon(K, face):
    f0, f1 = face
    v0, v1 = vert(f0), vert(f1)
    assert v0 != v1
    l0, l1 = sigma(f0), sigma(f1)
    D = {v0, v1}
    Kp, dmap, jk, s = rebuild(K, D, [], [(l0, l1)])
    a = jk[0]
    E = K.ekey

    def make(label):
        dots = {"C2": 0, "C2d": 1}[label]
        nominal = [[sheet(a), 0, [a], [E(l0), E(l1)]],
                   [1, dots, [], [E(f0)]],
                   [1, 0, [], [E(f1)]]]
        return build_record(K, Kp, dmap, label, nominal, [(0, 1, 2)], 0, 2, 0)
    theta = K.alpha[l0] == l1
    info = {"theta": theta, "circles": Kp.m - K.m,
            "boozer_ok": theta or (len({v0, v1, vert(K.alpha[l0]), vert(K.alpha[l1])}) == 4
                                   and len({E(f0), E(f1), E(l0), E(l1)}) == 4)}
    return Op(K, Kp, D, dmap, make, False, "bigon", info)


# 5.3 triangle
def op_triangle(K, face):
    f = face
    vs = [vert(x) for x in f]
    assert len(set(vs)) == 3
    l = [sigma(x) for x in f]
    D = set(vs)
    Kp, dmap, jk, s = rebuild(K, D, [(('p', l[0]), ('p', l[2]), ('p', l[1]))], [])
    y = 3 * s
    slot = {0: y, 2: y + 1, 1: y + 2}
    E = K.ekey
    Ep = Kp.ekey

    def make(label):
        nominal = []
        for k in range(3):
            nominal.append([1, 0, [Ep(slot[k])], [E(l[k])]])
        for k in range(3):
            nominal.append([1, 0, [], [E(f[k])]])
        seams = [(0, 1, 2)] + [(k, 3 + k, 3 + (k - 1) % 3) for k in range(3)]
        for x in nominal[:3]:
            assert x[2][0] >= 0
        return build_record(K, Kp, dmap, label, nominal, seams, 1, 3, 1)
    info = {"circles": Kp.m - K.m,
            "boozer_ok": len({E(x) for x in f} | {E(x) for x in l}) == 6}
    return Op(K, Kp, D, dmap, make, False, "triangle", info)


# 5.4 square
def op_square(K, face, which):
    f = face
    vs = [vert(x) for x in f]
    assert len(set(vs)) == 4
    l = [sigma(x) for x in f]
    D = set(vs)
    sh = 0 if which == "a" else 1
    i0, i1, i2, i3 = [(sh + k) % 4 for k in range(4)]
    J = [(l[i0], l[i1]), (l[i2], l[i3])]
    Kp, dmap, jk, s = rebuild(K, D, [], J)
    E = K.ekey
    label = "C4a" if which == "a" else "C4b"

    def make(lab):
        assert lab == label
        a01, a23 = jk
        nominal = [[sheet(a01), 0, [a01], [E(l[i0]), E(l[i1])]],
                   [sheet(a23), 0, [a23], [E(l[i2]), E(l[i3])]],
                   [1, 0, [], [E(f[i0])]],
                   [1, 0, [], [E(f[i2])]],
                   [1, 0, [], [E(f[i1]), E(f[i3])]]]
        seams = [(0, 2, 4), (1, 3, 4)]
        return build_record(K, Kp, dmap, label, nominal, seams, 0, 4, 0)
    info = {"circles": Kp.m - K.m, "degenerate_merge": jk[0] == jk[1],
            "boozer_ok": (len({E(x) for x in f} | {E(x) for x in l}) == 8
                          and len(set(vs) | {vert(K.alpha[x]) for x in l}) == 8)}
    return Op(K, Kp, D, dmap, make, False, "square", info)


def _edge_site(K, e):
    du = e
    dw = K.alpha[e]
    assert du < dw
    xu, yu = sigma(du), sigma(sigma(du))
    xw, yw = sigma(dw), sigma(sigma(dw))
    E = K.ekey
    legs = [E(xu), E(yu), E(xw), E(yw)]
    if len(set(legs)) != 4 or E(du) in legs:
        raise AssertionError("Zip/IH precondition fails at edge %d" % e)
    return du, dw, xu, yu, xw, yw


# 5.5 Zip
def op_zip(K, e):
    du, dw, xu, yu, xw, yw = _edge_site(K, e)
    D = {vert(du), vert(dw)}
    Kp, dmap, jk, s = rebuild(K, D, [], [(xu, yw), (yu, xw)])
    E = K.ekey

    def make(label):
        nominal = [[sheet(jk[0]), 0, [jk[0]], [E(xu), E(yw)]],
                   [sheet(jk[1]), 0, [jk[1]], [E(yu), E(xw)]],
                   [1, 0, [], [E(du)]]]
        return build_record(K, Kp, dmap, "zip", nominal, [(0, 1, 2)], 0, 2, 0)
    return Op(K, Kp, D, dmap, make, False, "zip", {"circles": Kp.m - K.m})


# 5.6 Unzip
def op_unzip(K, face, i, j):
    assert 0 <= i < j < len(face)
    fi, fj = face[i], face[j]
    V = K.V
    alpha = K.alpha
    afi, afj = alpha[fi], alpha[fj]
    assert len({fi, fj, afi, afj}) == 4
    tS, tR, tL = 3 * V, 3 * V + 1, 3 * V + 2
    bN, bL, bR = 3 * V + 3, 3 * V + 4, 3 * V + 5
    a2 = list(alpha) + [None] * 6

    def pair(p, q):
        a2[p] = q
        a2[q] = p
    pair(tS, bN)
    pair(tL, afi)
    pair(tR, fj)
    pair(bL, fi)
    pair(bR, afj)
    Kp = Web(V + 2, a2, K.m)
    dmap = _idmap(K)
    E = K.ekey
    x, y = E(fi), E(fj)

    def make(label):
        Ep = Kp.ekey
        nominal = [[1, 0, [Ep(bL), Ep(tL)], [x]],
                   [1, 0, [Ep(tR), Ep(bR)], [y]],
                   [1, 0, [Ep(tS)], []]]
        return build_record(K, Kp, dmap, "unzip", nominal, [(0, 1, 2)], 0, 0, 2)
    return Op(K, Kp, set(), dmap, make, True, "unzip")


# 5.7 Saddle
def op_saddle(K, face, i, j):
    assert 0 <= i < j < len(face)
    fi, fj = face[i], face[j]
    alpha = K.alpha
    afi, afj = alpha[fi], alpha[fj]
    assert len({fi, fj, afi, afj}) == 4
    a2 = list(alpha)
    a2[fi] = afj
    a2[afj] = fi
    a2[fj] = afi
    a2[afi] = fj
    Kp = Web(K.V, a2, K.m)
    dmap = _idmap(K)
    E = K.ekey
    x, y = E(fi), E(fj)
    n1, n2 = min(fi, afj), min(fj, afi)

    def make(label):
        nominal = [[1, 0, [n1, n2], [x, y]]]
        return build_record(K, Kp, dmap, "saddle", nominal, [], 0, 0, 0)
    return Op(K, Kp, set(), dmap, make, True, "saddle")


# 5.8 IH
def op_ih(K, e):
    du, dw, xu, yu, xw, yw = _edge_site(K, e)
    D = {vert(du), vert(dw)}
    NV = [(('l', 0), ('p', yw), ('p', xu)), (('l', 0), ('p', yu), ('p', xw))]
    Kp, dmap, jk, s = rebuild(K, D, NV, [])
    t, b = s, s + 1
    E = K.ekey

    def make(label):
        Ep = Kp.ekey
        nominal = [[1, 0, [Ep(3 * t + 1)], [E(yw)]],   # P1
                   [1, 0, [Ep(3 * t + 2)], [E(xu)]],   # P2
                   [1, 0, [Ep(3 * b + 1)], [E(yu)]],   # P3
                   [1, 0, [Ep(3 * b + 2)], [E(xw)]],   # P4
                   [1, 0, [Ep(3 * t)], []],            # B
                   [1, 0, [], [E(du)]]]                # Tf
        seams = [(4, 0, 1), (4, 2, 3), (5, 1, 2), (5, 3, 0)]
        return build_record(K, Kp, dmap, "ih", nominal, seams, 1, 2, 2)
    return Op(K, Kp, D, dmap, make, False, "ih")
