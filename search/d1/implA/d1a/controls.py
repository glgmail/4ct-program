"""SPEC Sec. 9 controls for Implementation A (Mode G).

run_controls() returns a list of (name, passed, detail) and raises nothing;
the caller refuses to run W1-W7 unless every control passed.
"""

import itertools

from . import web as W
from . import records as R
from . import gf4
from . import webdata
from .foam import HalfFoam, eval_closed, closed_degree, glue, avec_slow, compose, EMPTY
from .gen import GEN, generate, new_events
from .analysis import TargetWeb, analyse, sample_pairs, check_pairs


# ---------------------------------------------------------------- GF(2^8)
def gmul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a & 0x100:
            a ^= 0x11B
    return r


def gpow(a, n):
    if n < 0:
        a = ginv(a)
        n = -n
    r = 1
    while n:
        if n & 1:
            r = gmul(r, a)
        a = gmul(a, a)
        n >>= 1
    return r


def ginv(a):
    assert a
    return gpow(a, 254)


def h_poly(m, x):
    """complete homogeneous h_m(x1,x2,x3) by the recurrence
    h_m(x1..xk) = h_m(x1..x_{k-1}) + x_k h_{m-1}(x1..xk)."""
    if m < 0:
        return 0
    # table over number of variables
    prev = [1] + [0] * m                        # zero variables: h_0 = 1
    for k in range(3):
        cur = [0] * (m + 1)
        for j in range(m + 1):
            cur[j] = prev[j] ^ (gmul(x[k], cur[j - 1]) if j else 0)
        prev = cur
    return prev[m]


def schur3(lam, x):
    """Jacobi-Trudi: s_lam = det(h_{lam_i - i + j}) (char 2: permanent)."""
    M = [[h_poly(lam[i] - i + j, x) for j in range(3)] for i in range(3)]
    tot = 0
    for p in itertools.permutations(range(3)):
        tot ^= gmul(gmul(M[0][p[0]], M[1][p[1]]), M[2][p[2]])
    return tot


def poly_eval(chi, dots, seams, nv, x):
    """sum_c P/Q at X = x in GF(2^8), brute force over colourings."""
    n = len(chi)
    tot = 0
    for c in itertools.product((1, 2, 3), repeat=n):
        if any(len({c[a], c[b], c[d]}) != 3 for (a, b, d) in seams):
            continue
        P = 1
        for f in range(n):
            P = gmul(P, gpow(x[c[f] - 1], dots[f]))
        Q = 1
        for (i, j) in ((1, 2), (1, 3), (2, 3)):
            ch = sum(chi[f] for f in range(n) if c[f] in (i, j)) - nv
            assert ch % 2 == 0
            Q = gmul(Q, gpow(x[i - 1] ^ x[j - 1], ch // 2))
        tot ^= gmul(P, ginv(Q))
    return tot


POINTS = [(0x02, 0x03, 0x05), (0x53, 0xCA, 0x01)]


def phi_jb(chi, dots, seams, nv):
    val, _ = eval_closed(chi, dots, seams, nv)
    deg = closed_degree(chi, dots, nv)
    return val, (val if deg == 0 else 0), deg


def sphere(n):
    return [2], [n], [], 0


def theta_foam(n1, n2, n3):
    return [1, 1, 1], [n1, n2, n3], [(0, 1, 2)], 0


def torus(n):
    return [0], [n], [], 0


def genus2(n):
    return [-2], [n], [], 0


def web_times_circle(K):
    keys = K.all_keys()
    idx = {k: i for i, k in enumerate(keys)}
    chi = [0] * len(keys)
    dots = [0] * len(keys)
    seams = []
    for v in range(K.V):
        seams.append(tuple(idx[K.ekey(3 * v + k)] for k in range(3)))
    return chi, dots, seams, 0


def expected_theta_poly(n, x):
    s = sorted(n, reverse=True)
    if len(set(s)) < 3:
        return 0
    return schur3((s[0] - 2, s[1] - 1, s[2]), x)


# ---------------------------------------------------------------- 9.1
def control_91(out):
    ok = True
    rows = []
    # row 1: empty foam
    v, jb, deg = phi_jb([], [], [], 0)
    rows.append(("empty", v == 1 and jb == 1))
    for n in range(0, 7):
        v, jb, deg = phi_jb(*sphere(n))
        rows.append(("sphere%d" % n, v == (1 if n % 3 == 2 else 0) and jb == (1 if n == 2 else 0)))
        v, jb, deg = phi_jb(*torus(n))
        rows.append(("torus%d" % n, v == (1 if n % 3 == 0 else 0) and jb == (1 if n == 0 else 0)))
        v, jb, deg = phi_jb(*genus2(n))
        rows.append(("genus2_%d" % n, v == (1 if n % 3 == 1 else 0) and jb == 0))
    for n in itertools.product(range(4), repeat=3):
        v, jb, deg = phi_jb(*theta_foam(*n))
        ms = sorted(n)
        ev = 1 if ms in ([0, 1, 2], [1, 2, 3]) else 0
        ej = 1 if ms == [0, 1, 2] else 0
        rows.append(("theta%s" % (n,), v == ev and jb == ej))
    # specific values
    rows.append(("theta(2,1,0)=1", phi_jb(*theta_foam(2, 1, 0))[1] == 1))
    rows.append(("theta(1,1,0)=0", phi_jb(*theta_foam(1, 1, 0))[0] == 0))
    v, jb, deg = phi_jb(*theta_foam(1, 2, 3))
    rows.append(("theta(1,2,3): Phi=1, deg 6", v == 1 and deg == 6))
    # row 6: web x S^1
    for name in ("circle", "two_circles", "theta", "K4", "prism3", "cube", "prism5", "W1"):
        K = W.load(name)
        T = len(K.tait_colourings())
        v, jb, deg = phi_jb(*web_times_circle(K))
        rows.append(("%s x S1 = Tait %d mod 2" % (name, T), v == T % 2 and deg == 0))
    # row 7
    v, jb, deg = phi_jb([1, 1, 1], [0, 0, 0], [(0, 0, 1), (0, 0, 2)], 1)
    rows.append(("torus+meridian+longitude disks", v == 0))
    # full polynomial tests at GF(2^8) points
    for x in POINTS:
        e1 = x[0] ^ x[1] ^ x[2]
        for n in range(0, 7):
            rows.append(("poly sphere%d %s" % (n, x),
                         poly_eval(*sphere(n), x) == h_poly(n - 2, x)))
            p = 0
            for xi in x:
                p ^= gpow(xi, n)
            rows.append(("poly torus%d %s" % (n, x), poly_eval(*torus(n), x) == p))
            g = 0
            for i in range(3):
                j, k = [a for a in range(3) if a != i]
                g ^= gmul(gpow(x[i], n), gmul(x[i] ^ x[j], x[i] ^ x[k]))
            rows.append(("poly genus2_%d %s" % (n, x), poly_eval(*genus2(n), x) == g))
        for n in itertools.product(range(5), repeat=3):
            rows.append(("poly theta%s %s" % (n, x),
                         poly_eval(*theta_foam(*n), x) == expected_theta_poly(n, x)))
        # relation: sum_k theta(n + e_k) = E1 * theta(n)   (KR Prop 2.32)
        for n in itertools.product(range(4), repeat=3):
            lhs = 0
            for k in range(3):
                m = list(n)
                m[k] += 1
                lhs ^= poly_eval(*theta_foam(*m), x)
            rhs = gmul(e1, poly_eval(*theta_foam(*n), x))
            rows.append(("relation dot migration %s %s" % (n, x), lhs == rhs))
    # relation at Phi: sum of the three = 0
    for n in itertools.product(range(4), repeat=3):
        s = 0
        for k in range(3):
            m = list(n)
            m[k] += 1
            s ^= phi_jb(*theta_foam(*m))[0]
        rows.append(("Phi dot migration %s" % (n,), s == 0))
    bad = [r for r in rows if not r[1]]
    out.append(("9.1 closed-foam evaluation (%d checks)" % len(rows), not bad,
                "failures: %s" % bad[:5] if bad else "all pass"))


# ---------------------------------------------------------------- helpers
def gen_list(K, strict=True):
    lst = GEN(K, None, strict, True, new_events())
    return lst


def gram_direct(tw, foams):
    n = len(foams)
    return [[tw.direct_pair(foams[i], foams[j]) for j in range(n)] for i in range(n)]


def gram_avec(avecs, degs, jflat=True):
    n = len(avecs)
    G = []
    for i in range(n):
        row = []
        for j in range(n):
            b = gf4.dot(avecs[i], avecs[j])
            assert b <= 1
            row.append(b if (not jflat or degs[i] + degs[j] == 0) else 0)
        G.append(row)
    return G


def gf2_rank(M):
    rows = [int("".join(str(x) for x in r)[::-1] or "0", 2) for r in M]
    E = gf4.Echelon()
    for r in rows:
        E.add((r, 0))
    return len(E)


# ---------------------------------------------------------------- 9.3
def control_93(out):
    # circle
    K = W.load("circle")
    tw = TargetWeb(K)
    lst = gen_list(K)
    foams = [h for h, d, c in lst]
    degs = [d for h, d, c in lst]
    avs = [tw.avec(h) for h in foams]
    hexes = [tw.hexa(a) for a in avs]
    G = gram_avec(avs, degs)
    Gd = [[v if degs[i] + degs[j] == 0 else 0 for j, v in enumerate(row)]
          for i, row in enumerate(gram_direct(tw, foams))]
    ok = (degs == [-2, 0, 2] and hexes == ["132", "111", "123"]
          and G == [[0, 0, 1], [0, 1, 0], [1, 0, 0]] and Gd == G
          and [c for _, _, c in lst] == [("C1",), ("C1d",), ("C1dd",)])
    res = analyse(zip(avs, degs))
    ok = ok and res["ell"] == 3
    out.append(("9.3 circle: GEN, a-vectors 132/111/123, Gram, l=3", ok,
                "degs %s a %s l %d" % (degs, hexes, res["ell"])))
    # theta
    K = W.load("theta")
    tw = TargetWeb(K)
    lst = gen_list(K)
    foams = [h for h, d, c in lst]
    degs = [d for h, d, c in lst]
    avs = [tw.avec(h) for h in foams]
    hexes = [tw.hexa(a) for a in avs]
    G = gram_avec(avs, degs)
    Gd = [[v if degs[i] + degs[j] == 0 else 0 for j, v in enumerate(row)]
          for i, row in enumerate(gram_direct(tw, foams))]
    expG = [[0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 1, 0], [0, 0, 0, 1, 0, 0],
            [0, 0, 1, 0, 1, 0], [0, 1, 0, 1, 0, 0], [1, 0, 0, 0, 0, 0]]
    tait_ok = tw.taits == [(1, 2, 3), (1, 3, 2), (2, 1, 3), (2, 3, 1), (3, 1, 2), (3, 2, 1)]
    res = analyse(zip(avs, degs))
    ok = (tait_ok and degs == [-3, -1, 1, -1, 1, 3]
          and hexes == ["111111", "231312", "321213", "112233", "232131", "322332"]
          and G == expG and Gd == G and gf2_rank(G) == 6 and res["ell"] == 6
          and res["ell_q"] == {-3: 1, -1: 2, 1: 2, 3: 1})
    out.append(("9.3 theta: GEN, a-vectors, Gram (direct = a-vector), rank 6, l_q", ok,
                "degs %s a %s l_q %s" % (degs, hexes, res["ell_q"])))


# ---------------------------------------------------------------- 9.4
QDIM = {
    "circle": {-2: 1, 0: 1, 2: 1},
    "two_circles": {-4: 1, -2: 2, 0: 3, 2: 2, 4: 1},
    "theta": {-3: 1, -1: 2, 1: 2, 3: 1},
    "K4": {-3: 1, -1: 2, 1: 2, 3: 1},
    "prism3": {-3: 1, -1: 2, 1: 2, 3: 1},
    "cube": {-4: 2, -2: 6, 0: 8, 2: 6, 4: 2},
    "prism5": {-5: 1, -3: 5, -1: 9, 1: 9, 3: 5, 5: 1},
    "prism6": {-6: 1, -4: 7, -2: 17, 0: 22, 2: 17, 4: 7, 6: 1},
}


def divisible_by_3fact(pq):
    """pq: dict degree -> coefficient (Laurent polynomial in q).  Divide by
    (q^2+1+q^-2)(q+q^-1) = q^-3 + 2q^-1 + 2q + q^3 over Z."""
    if not pq:
        return True
    lo = min(pq)
    hi = max(pq)
    poly = [pq.get(d, 0) for d in range(lo, hi + 1)]
    div = [1, 0, 2, 0, 2, 0, 1]
    poly = list(poly)
    if len(poly) < len(div):
        return False
    for i in range(len(poly) - len(div) + 1):
        c = poly[i]
        if c:
            for k in range(len(div)):
                poly[i + k] -= c * div[k]
    return all(v == 0 for v in poly)


def control_94(out):
    allok = True
    det = []
    for name in ("circle", "two_circles", "theta", "K4", "prism3", "cube", "prism5", "prism6"):
        K = W.load(name)
        K.validate() if K.V else None
        tw = TargetWeb(K)
        lst = gen_list(K)
        if lst is None:
            allok = False
            det.append("%s: GEN failed" % name)
            continue
        avs = []
        for h, d, c in lst:
            tw.check_degree(h, d)
            avs.append(tw.avec(h))
        degs = [d for _, d, _ in lst]
        res = analyse(zip(avs, degs))
        exp = QDIM[name]
        ok = (len(lst) == tw.T and res["ell"] == tw.T and res["ell_q"] == exp
              and res["r"] == tw.T and res["r_q"] == exp)
        if name not in ("circle", "two_circles"):
            ok = ok and divisible_by_3fact(res["ell_q"])
        det.append("%s: N=%d T=%d l=%d r=%d l_q=%s" % (name, len(lst), tw.T, res["ell"],
                                                       res["r"], res["ell_q"]))
        allok = allok and ok
        # Mode G self-check: bit-parallel a-vectors vs per-t backtracking
        for (h, d, c), a in zip(lst, avs):
            slow = avec_slow(h, tw.taits, tw.keys)
            if gf4.from_codes(slow) != a:
                allok = False
                det.append("%s: avec mismatch" % name)
                break
    out.append(("9.4 reducible webs: N = l = r = Tait, l_q = r_q = qdim", allok, "; ".join(det)))
    # r_q != l_q test with cups
    K = W.load("circle")
    tw = TargetWeb(K)
    ok = True
    for deltas, eq, erq in (((0, 1, 5), {0: 1}, {-2: 1, 0: 1, 8: 1}),
                            ((0, 1, 2, 3), {-2: 1, 0: 1, 2: 1}, {-2: 1, 0: 1, 2: 1})):
        items = []
        for dl in deltas:
            H = HalfFoam([1], [dl], {W.ckey(0): 0}, [], 0)
            items.append((tw.avec(H), 2 * dl - 2))
        res = analyse(items)
        ok = ok and res["ell_q"] == eq and res["r_q"] == erq and res["r"] == 3
        if deltas == (0, 1, 5):
            ok = ok and [tw.hexa(a) for a, _ in items] == ["132", "111", "123"]
    out.append(("9.4 cups delta=0,1,5: l_q=1, r=3, r_q=q^-2+1+q^8; delta=0..3: l_q=r_q", ok, ""))


# ---------------------------------------------------------------- 9.5
def run_moves_control(name, mode="STRICT-ALL"):
    K = W.load(name)
    tw = TargetWeb(K)
    foams, avs, degs = {}, {}, {}
    n = [0]

    def cb(site, H, d, chain):
        n[0] += 1
        tw.check_degree(H, d)
        foams[n[0]] = H
        avs[n[0]] = tw.avec(H)
        degs[n[0]] = d
    counts = generate(K, None, mode, True, cb)
    res = analyse((avs[i], degs[i]) for i in range(1, n[0] + 1))
    checked = check_pairs(tw, foams, avs, degs, sample_pairs(n[0]))
    return n[0], counts, res, checked


def local_support(rec, K, Kp):
    """Pairs (t', t) admitting at least one local colouring (SPEC 4.6 conditions)."""
    tK = K.tait_colourings()
    tKp = Kp.tait_colourings()
    kK = {k: i for i, k in enumerate(K.all_keys())}
    kKp = {k: i for i, k in enumerate(Kp.all_keys())}
    nf = len(rec.facets)
    S = set()
    for a, tp in enumerate(tKp):
        for b, t in enumerate(tK):
            if any(t[kK[e]] != tp[kKp[e2]] for e, e2 in rec.ident):
                continue
            col = [0] * nf
            ok = True
            for g, (chi, dots, bot, top) in enumerate(rec.facets):
                for x in bot:
                    c = tp[kKp[x]]
                    if col[g] and col[g] != c:
                        ok = False
                    col[g] = c
                for x in top:
                    c = t[kK[x]]
                    if col[g] and col[g] != c:
                        ok = False
                    col[g] = c
            if not ok:
                continue
            free = [g for g in range(nf) if not col[g]]
            found = False
            for cs in itertools.product((1, 2, 3), repeat=len(free)):
                for g, c in zip(free, cs):
                    col[g] = c
                if all(len({col[x], col[y], col[z]}) == 3 for (x, y, z) in rec.seams):
                    found = True
                    break
            if found:
                S.add((a, b))
    return S


def bool_product(S2, S1):
    """S2 subset Tait(K2) x Tait(K1), S1 subset Tait(K1) x Tait(K0)."""
    by = {}
    for (m, b) in S1:
        by.setdefault(m, set()).add(b)
    P = set()
    for (a, m) in S2:
        for b in by.get(m, ()):
            P.add((a, b))
    return P


def face_with(K, set1, set2):
    """Faces of K containing a dart of set1 and a dart of set2: [(face, i, j)]."""
    res = []
    for f in K.faces():
        i1 = [k for k, d in enumerate(f) if d in set1]
        i2 = [k for k, d in enumerate(f) if d in set2]
        if i1 and i2:
            res.append((f, i1, i2))
    return res


def control_lemma411(out):
    K0 = W.load("W1")
    F0 = K0.faces()[K0.face_of()[0]]
    det = []
    ok = F0 == (0, 13, 40, 43, 16)
    e0 = 0
    ok = ok and K0.alpha[0] == 12

    def chain(op1, op2_builder, lab1, lab2):
        K1 = op1.Kp
        rec1 = op1.make(lab1)
        op2 = op2_builder(K1, op1)
        rec2 = op2.make(lab2)
        S1 = local_support(rec1, K0, K1)
        S2 = local_support(rec2, K1, op2.Kp)
        return len(S1), len(S2), len(bool_product(S2, S1))

    results = []
    # 1. Unzip then IH at tS (dart 60)
    op1 = R.op_unzip(K0, F0, 0, 2)
    results.append(("Unzip o IH", chain(op1, lambda K1, o: R.op_ih(K1, 60), "unzip", "ih"),
                    (36, 36, 0)))

    # 2. Saddle then Unzip at the face containing both new edges
    op1 = R.op_saddle(K0, F0, 0, 2)
    fi, fj = F0[0], F0[2]
    afi, afj = K0.alpha[fi], K0.alpha[fj]

    def b2(K1, o):
        cands = face_with(K1, {fi, afj}, {fj, afi})
        assert len(cands) == 1, cands
        f, i1, i2 = cands[0]
        assert len(i1) == 1 and len(i2) == 1
        i, j = sorted((i1[0], i2[0]))
        return R.op_unzip(K1, f, i, j)
    results.append(("Saddle o Unzip", chain(op1, b2, "saddle", "unzip"), (24, 48, 0)))

    # 3. Zip then Saddle at the face containing both joined edges
    op1 = R.op_zip(K0, e0)
    K1 = op1.Kp

    def b3(K1, o):
        # joined edges: the K'-edges of the two joins = bottom edges of L and R
        rec = o.make("zip")
        j0 = rec.facets[0][2][0]
        j1 = rec.facets[1][2][0]
        s1 = {j0, K1.alpha[j0]}
        s2 = {j1, K1.alpha[j1]}
        cands = face_with(K1, s1, s2)
        assert len(cands) == 1, cands
        f, i1, i2 = cands[0]
        assert len(i1) == 1 and len(i2) == 1
        i, j = sorted((i1[0], i2[0]))
        return R.op_saddle(K1, f, i, j)
    results.append(("Zip o Saddle", chain(op1, b3, "zip", "saddle"), (24, 12, 0)))

    # 4. IH then Zip at e' (dart 54)
    op1 = R.op_ih(K0, e0)
    results.append(("IH o Zip", chain(op1, lambda K1, o: R.op_zip(K1, 54), "ih", "zip"),
                    (36, 36, 0)))
    # 5. contrast
    op1 = R.op_unzip(K0, F0, 0, 2)
    results.append(("Unzip then Zip (contrast)",
                    chain(op1, lambda K1, o: R.op_zip(K1, 60), "unzip", "zip"),
                    (None, None, 36)))
    for name, got, exp in results:
        good = all(e is None or g == e for g, e in zip(got, exp))
        if name != "Unzip then Zip (contrast)":
            good = good and got[0] > 0 and got[1] > 0 and got[2] == 0
        ok = ok and good
        det.append("%s: supports %d, %d; product %d" % ((name,) + got))
    out.append(("9.5 KR Lemma 4.11 chains on W1", ok, "; ".join(det)))


def control_95(out):
    exp = {"prism5": (3660, (360, 2190, 840, 270), 30),
           "cube": (2160, (288, 1224, 576, 72), 24)}
    for name, (eN, ecnt, el) in exp.items():
        N, counts, res, checked = run_moves_control(name)
        got = (counts["zip"], counts["unzip"], counts["saddle"], counts["ih"])
        ok = N == eN and got == ecnt and res["ell"] == el and res["ell_q"] == QDIM[name]
        out.append(("9.5 moves on %s (STRICT-ALL)" % name, ok,
                    "N=%d by move %s l=%d l_q=%s r=%d r_q=%s; %d direct pairs checked"
                    % (N, got, res["ell"], res["ell_q"], res["r"], res["r_q"], checked)))
    control_lemma411(out)


def control_webs(out):
    """Appendix A transcription: Euler, face sizes, |Aut|, Tait, outer faces."""
    ok = True
    det = []
    for name, (fs, aut, tait, outer) in webdata.EXPECT.items():
        K = W.load(name)
        K.validate()
        sizes = {}
        for f in K.faces():
            sizes[len(f)] = sizes.get(len(f), 0) + 1
        T = len(K.tait_colourings())
        good = sizes == fs and T == tait
        if aut is not None:
            good = good and W.count_automorphisms(K) == aut
        if outer is not None:
            f = [f for f in K.faces() if f[0] == outer][0]
            good = good and [W.vert(d) for d in f] == webdata.OUTER_VERTICES[name]
        if not good:
            det.append(name)
        ok = ok and good
    out.append(("Appendix A webs: Euler, face sizes, |Aut|, Tait, outer faces", ok,
                "bad: %s" % det if det else "all match"))


def control_records(out):
    """Degree of every record type equals B19 Table 1 (asserted in build_record)
    -- exercised here on W1 sites and the reducible controls."""
    ok = True
    try:
        K = W.load("W1")
        f = K.faces()[0]
        for op, lab in ((R.op_zip(K, 0), "zip"), (R.op_ih(K, 0), "ih"),
                        (R.op_unzip(K, f, 0, 2), "unzip"), (R.op_saddle(K, f, 0, 2), "saddle")):
            op.make(lab)
        K = W.load("prism3")
        tri = [f for f in K.faces() if len(f) == 3][0]
        sq = [f for f in K.faces() if len(f) == 4][0]
        R.op_triangle(K, tri).make("C3")
        R.op_square(K, sq, "a").make("C4a")
        R.op_square(K, sq, "b").make("C4b")
        K = W.load("theta")
        op = R.op_bigon(K, K.faces()[0])
        op.make("C2")
        op.make("C2d")
        K = W.load("circle")
        op = R.op_disk(K)
        for lab in ("C1", "C1d", "C1dd"):
            op.make(lab)
    except AssertionError as e:
        ok = False
        out.append(("record degrees = B19 Table 1", False, str(e)))
        return
    out.append(("record degrees = B19 Table 1 (all 12 types)", ok, ""))


def control_avec_selfcheck(out, name="W1", mode="B19", step=37):
    """Bit-parallel a-vector (all t at once) vs row-wise per-t backtracking on
    every step-th half-foam of a W-web generating set."""
    K = W.load(name)
    tw = TargetWeb(K)
    n = [0, 0, 0]

    def cb(site, H, d, chain):
        n[0] += 1
        if n[0] % step == 1:
            n[1] += 1
            a = tw.avec(H)
            if gf4.from_codes(avec_slow(H, tw.taits, tw.keys)) != a:
                n[2] += 1
    generate(K, webdata.EXPECT[name][3], mode, True, cb)
    out.append(("Mode G self-check: bit-parallel vs per-t backtracking a-vectors, %s %s"
                % (name, mode), n[2] == 0, "%d half-foams compared, %d mismatches"
                % (n[1], n[2])))


def run_controls():
    out = []
    control_avec_selfcheck(out)
    control_webs(out)
    control_records(out)
    control_91(out)
    control_93(out)
    control_94(out)
    control_95(out)
    return out
