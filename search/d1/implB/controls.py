"""SPEC section 9 controls for Implementation B."""

import os
import traceback

import closedfoam as cf
from core import (tait_colourings, gen, GenStats, gen_rows_hex, hex_to_packed,
                  rec_unzip, rec_saddle, rec_zip, rec_ih, OMEGA_POW)
from webs import get_web, CONTROLS_TAIT
import ranks

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print("%s  %s  %s" % ("PASS" if ok else "FAIL", name, detail))


def check(name, fn):
    try:
        ok, detail = fn()
    except Exception as e:  # noqa: BLE001
        ok, detail = False, "exception: %r\n%s" % (e, traceback.format_exc())
    record(name, ok, detail)
    return ok


# ------------------------------------------------------------------ 9.1
PTS = [(0x02, 0x03, 0x05), (0x53, 0xCA, 0x01)]


def c91_table():
    msgs = []
    bad = 0

    def expect(label, foam, phi_exp, jf_exp):
        nonlocal bad
        f, s, nv = foam
        v, d = cf.phi_eval(f, s, nv)
        j = cf.jflat(f, s, nv)
        if v != phi_exp or j != jf_exp:
            bad += 1
            msgs.append("%s: Phi=%d (exp %d) J=%d (exp %d)" % (label, v, phi_exp, j, jf_exp))
    expect("empty", ([], [], 0), 1, 1)
    for n in range(0, 9):
        expect("sphere%d" % n, cf.sphere(n), 1 if n % 3 == 2 else 0, 1 if n == 2 else 0)
    for n1 in range(4):
        for n2 in range(4):
            for n3 in range(4):
                ms = sorted([n1, n2, n3])
                phi = 1 if ms in ([0, 1, 2], [1, 2, 3]) else 0
                jf = 1 if ms == [0, 1, 2] else 0
                expect("theta%d%d%d" % (n1, n2, n3), cf.theta_foam(n1, n2, n3), phi, jf)
    for n in range(0, 9):
        expect("torus%d" % n, cf.torus(n), 1 if n % 3 == 0 else 0, 1 if n == 0 else 0)
    for n in range(0, 9):
        expect("genus2_%d" % n, cf.genus2(n), 1 if n % 3 == 1 else 0, 0)
    for w in ["circle", "twocircles", "theta", "K4", "prism3", "cube", "prism5", "prism6"]:
        W = get_web(w)
        tp = CONTROLS_TAIT[w] % 2
        expect("%sxS1" % w, cf.web_times_circle(W), tp, tp)
    expect("torus+2disks", cf.torus_two_disks(), 0, 0)
    # specific values quoted in SPEC 9.1
    v, d = cf.phi_eval(*cf.theta_foam(1, 2, 3))
    if (v, d) != (1, 6):
        bad += 1
        msgs.append("theta(1,2,3) Phi/deg %r" % ((v, d),))
    # dot migration relation tests (KR 2.32 at Phi)
    s = 0
    for k in range(3):
        n = [0, 0, 0]
        n[k] = 1
        s ^= cf.phi_eval(*cf.theta_foam(*n))[0]
    if s != 0:
        bad += 1
        msgs.append("dot migration")
    for base in [(0, 0, 0), (1, 0, 0), (2, 1, 0), (1, 1, 2), (3, 0, 1)]:
        s = 0
        for k in range(3):
            n = list(base)
            n[k] += 1
            s ^= cf.phi_eval(*cf.theta_foam(*n))[0]
        if s != 0:
            bad += 1
            msgs.append("dot sum %r" % (base,))
    return bad == 0, "; ".join(msgs) or "all Phi/J-flat values as in SPEC 9.1 table"


def c91_full():
    bad = []
    for X in PTS:
        e1 = X[0] ^ X[1] ^ X[2]
        for n in range(7):
            if cf.full_eval(*cf.sphere(n), X) != cf.h_poly(n - 2, X):
                bad.append(("sphere", n, X))
            p = cf.g_pow(X[0], n) ^ cf.g_pow(X[1], n) ^ cf.g_pow(X[2], n)
            if cf.full_eval(*cf.torus(n), X) != p:
                bad.append(("torus", n, X))
            g2 = 0
            for i in range(3):
                j, k = [x for x in range(3) if x != i]
                g2 ^= cf.g_mul(cf.g_pow(X[i], n), cf.g_mul(X[i] ^ X[j], X[i] ^ X[k]))
            if cf.full_eval(*cf.genus2(n), X) != g2:
                bad.append(("genus2", n, X))
        for n1 in range(5):
            for n2 in range(5):
                for n3 in range(5):
                    if cf.full_eval(*cf.theta_foam(n1, n2, n3), X) != cf.schur_theta((n1, n2, n3), X):
                        bad.append(("theta", (n1, n2, n3), X))
        # KR Cor 2.16 specific: sphere with 3 dots = E1
        if cf.full_eval(*cf.sphere(3), X) != e1:
            bad.append(("sphere3=E1", X))
    return not bad, ("%d mismatches: %r" % (len(bad), bad[:5])) if bad else \
        "rows 2-5 (n=0..6) and theta(n1,n2,n3), 0<=n_i<=4, at both GF(2^8) points"


# ------------------------------------------------------------------ helpers
def gen_full(name, strict=True):
    K = get_web(name)
    S = tait_colourings(K)
    st = GenStats()
    G = gen(K, S, strict, None, st, check=True)
    rows = gen_rows_hex(G)
    return K, S, G, rows


def ranks_of(G, rows, T):
    return ranks.compute_all(G.degs, [hex_to_packed(r) for r in rows], T)


def gram(G, rows):
    vecs = [hex_to_packed(r) for r in rows]
    n = len(rows)
    M = [[(ranks.beta(vecs[i], vecs[j]) if G.degs[i] + G.degs[j] == 0 else 0)
          for j in range(n)] for i in range(n)]
    return M


# ------------------------------------------------------------------ 9.3
def c93_circle():
    K, S, G, rows = gen_full("circle")
    ok = (S == [(1,), (2,), (3,)] and rows == ["132", "111", "123"]
          and G.degs == [-2, 0, 2])
    M = gram(G, rows)
    ok = ok and M == [[0, 0, 1], [0, 1, 0], [1, 0, 0]]
    R = ranks_of(G, rows, 3)
    ok = ok and R["ell"] == 3
    return ok, "a-vectors %s degs %s Gram %s ell %d" % (rows, G.degs, M, R["ell"])


def c93_theta():
    K, S, G, rows = gen_full("theta")
    exp_tait = [(1, 2, 3), (1, 3, 2), (2, 1, 3), (2, 3, 1), (3, 1, 2), (3, 2, 1)]
    exp_rows = ["111111", "231312", "321213", "112233", "232131", "322332"]
    exp_M = [[0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 1, 0], [0, 0, 0, 1, 0, 0],
             [0, 0, 1, 0, 1, 0], [0, 1, 0, 1, 0, 0], [1, 0, 0, 0, 0, 0]]
    M = gram(G, rows)
    R = ranks_of(G, rows, 6)
    chains = [list(c) for c in G.chains]
    ok = (S == exp_tait and rows == exp_rows and G.degs == [-3, -1, 1, -1, 1, 3]
          and M == exp_M and R["ell"] == 6 and R["ell_q"] == {-3: 1, -1: 2, 1: 2, 3: 1}
          and K.faces == [(0, 4), (1, 3), (2, 5)])
    return ok, "a-vectors %s chains %s Gram rank %d ell_q %s" % (rows, chains, R["ell"], R["ell_q"])


# ------------------------------------------------------------------ 9.4
EXP94 = {
    "circle": {-2: 1, 0: 1, 2: 1},
    "twocircles": {-4: 1, -2: 2, 0: 3, 2: 2, 4: 1},
    "theta": {-3: 1, -1: 2, 1: 2, 3: 1},
    "K4": {-3: 1, -1: 2, 1: 2, 3: 1},
    "prism3": {-3: 1, -1: 2, 1: 2, 3: 1},
    "cube": {-4: 2, -2: 6, 0: 8, 2: 6, 4: 2},
    "prism5": {-5: 1, -3: 5, -1: 9, 1: 9, 3: 5, 5: 1},
    "prism6": {-6: 1, -4: 7, -2: 17, 0: 22, 2: 17, 4: 7, 6: 1},
}


def divisible_by_3fact(q):
    """Is the Laurent polynomial q divisible by (q^2+1+q^-2)(q+q^-1)?"""
    if not q:
        return True
    lo = min(q)
    p = [0] * (max(q) - lo + 1)
    for k, v in q.items():
        p[k - lo] = v
    div = [1, 0, 2, 0, 2, 0, 1]      # q^5+2q^3+2q+q^-1... times q^3 shift: (1,0,2,0,2,0,1)
    p = p[:]
    while len(p) >= len(div):
        c = p[-1]
        for i in range(len(div)):
            p[len(p) - len(div) + i] -= c * div[i]
        assert p[-1] == 0
        p.pop()
    return all(x == 0 for x in p)


def c94(name):
    def fn():
        K, S, G, rows = gen_full(name)
        T = len(S)
        R = ranks_of(G, rows, T)
        ok = (T == CONTROLS_TAIT[name] and G.n == T and R["ell"] == T
              and R["ell_q"] == EXP94[name] and R["r"] == T and R["r_q"] == EXP94[name])
        div = divisible_by_3fact(R["ell_q"])
        if name not in ("circle", "twocircles"):
            ok = ok and div
        return ok, "Tait %d N %d ell %d ell_q %s r %d r_q %s [3]!|ell_q %s" % (
            T, G.n, R["ell"], R["ell_q"], R["r"], R["r_q"], div)
    return fn


def cup_rows(deltas):
    rows = []
    for dl in deltas:
        # cup: one facet chi 1, dots dl; e = (c-1)(dl - 1) mod 3 (SPEC 4.5)
        s = ""
        for c in (1, 2, 3):
            x12 = 1 if c in (1, 2) else 0
            x13 = 1 if c in (1, 3) else 0
            e = (dl * (c - 1) - x12 - 2 * x13) % 3
            s += str(OMEGA_POW[e])
        rows.append(s)
    return rows


def c94_rq():
    rows = cup_rows([0, 1, 5])
    degs = [-2, 0, 8]
    R = ranks.compute_all(degs, [hex_to_packed(r) for r in rows], 3)
    ok1 = rows == ["132", "111", "123"] and R["ell_q"] == {0: 1} and R["r"] == 3 \
        and R["r_q"] == {-2: 1, 0: 1, 8: 1}
    rows2 = cup_rows([0, 1, 2, 3])
    R2 = ranks.compute_all([-2, 0, 2, 4], [hex_to_packed(r) for r in rows2], 3)
    ok2 = R2["ell_q"] == {-2: 1, 0: 1, 2: 1} and R2["r_q"] == {-2: 1, 0: 1, 2: 1}
    return ok1 and ok2, "delta=0,1,5: ell_q %s r %d r_q %s; delta=0..3: ell_q %s r_q %s" % (
        R["ell_q"], R["r"], R["r_q"], R2["ell_q"], R2["r_q"])


# ------------------------------------------------------------------ 9.5
def c95_moves(name, expN, exp_by, exp_ell, outdir):
    def fn():
        import d1b
        res, _, _, _ = d1b.run_target(name, "STRICT-ALL", outdir, 1, "n/a (control)",
                                "controls", check=True, log=lambda s: None)
        by = res["N_by_move"]
        got_by = (by["zip"], by["unzip"], by["saddle"], by["ih"])
        eq = {int(k): v for k, v in res["ell_q"].items()}
        ok = res["N"] == expN and got_by == exp_by and res["ell"] == exp_ell and eq == EXP94[name]
        return ok, "N %d by move %s ell %d ell_q %s r %d" % (res["N"], got_by, res["ell"], eq, res["r"])
    return fn


def face_with_both(K, e1, e2):
    """Faces of K containing a dart of edge-item e1 and a dart of edge-item e2;
    returns list of (face, i, j) with i < j the positions of those darts."""
    out = []
    for f in K.faces:
        p1 = [k for k, d in enumerate(f) if K.eidx[d] == e1]
        p2 = [k for k, d in enumerate(f) if K.eidx[d] == e2]
        if p1 and p2:
            assert len(p1) == 1 and len(p2) == 1
            i, j = sorted([p1[0], p2[0]])
            out.append((f, i, j))
    return out


def chain_test(which):
    def fn():
        W = get_web("W1")
        T0 = tait_colourings(W)
        F0 = W.faces[W.face_of[0]]
        assert F0 == (0, 13, 40, 43, 16), F0
        info = ""
        if which == 1:
            K1, r1, _ = rec_unzip(W, F0, 0, 2)
            K2, r2, _, _ = rec_ih(K1, 60)
        elif which == 2:
            K1, r1, _ = rec_saddle(W, F0, 0, 2)
            fi, fj = F0[0], F0[2]
            n1 = K1.eidx[fi]
            n2 = K1.eidx[fj]
            cands = face_with_both(K1, n1, n2)
            info = " faces with both new edges: %d" % len(cands)
            f, i, j = cands[0]
            K2, r2, _ = rec_unzip(K1, f, i, j)
        elif which == 3:
            K1, r1, _, _, ji = rec_zip(W, 0)
            cands = face_with_both(K1, ji[0], ji[1])
            info = " faces with both joined edges: %d" % len(cands)
            f, i, j = cands[0]
            K2, r2, _ = rec_saddle(K1, f, i, j)
        elif which == 4:
            K1, r1, _, _ = rec_ih(W, 0)
            K2, r2, _, _, _ = rec_zip(K1, 54)
        else:
            K1, r1, _ = rec_unzip(W, F0, 0, 2)
            K2, r2, _, _, _ = rec_zip(K1, 60)
        T1 = tait_colourings(K1)
        s1 = r1.support(T0)
        s2 = r2.support(T1)
        mid = {}
        for (t1, t0) in s1:
            mid.setdefault(t1, set()).add(t0)
        prod = set()
        for (t2, t1) in s2:
            for t0 in mid.get(t1, ()):
                prod.add((t2, t0))
        exp = {1: (36, 36, 0), 2: (24, 48, 0), 3: (24, 12, 0), 4: (36, 36, 0), 5: (None, None, 36)}[which]
        got = (len(s1), len(s2), len(prod))
        if which == 5:
            ok = len(prod) == 36
        else:
            ok = got == exp and len(s1) > 0 and len(s2) > 0
        return ok, "supports %d, %d; product pairs %d (expected %s)%s" % (got + (exp, info))
    return fn


def run_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    del RESULTS[:]
    check("9.1 closed-foam table (Phi, J-flat, asserts)", c91_table)
    check("9.1 full-polynomial tests at GF(2^8) points", c91_full)
    check("9.3 circle vectors and Gram", c93_circle)
    check("9.3 theta vectors and Gram", c93_theta)
    for w in ["circle", "twocircles", "theta", "K4", "prism3", "cube", "prism5", "prism6"]:
        check("9.4 GEN STRICT on %s" % w, c94(w))
    check("9.4 r_q test (cups delta=0,1,5 and 0..3)", c94_rq)
    check("9.5 moves on prism5 (STRICT-ALL)",
          c95_moves("prism5", 3660, (360, 2190, 840, 270), 30, outdir))
    check("9.5 moves on cube (STRICT-ALL)",
          c95_moves("cube", 2160, (288, 1224, 576, 72), 24, outdir))
    for k in range(1, 6):
        check("9.5 Lemma 4.11 chain %d" % k, chain_test(k))
    ok = all(r[1] for r in RESULTS)
    with open(os.path.join(outdir, "controls.txt"), "w", newline="\n") as fh:
        for name, good, detail in RESULTS:
            fh.write("%s  %s  %s\n" % ("PASS" if good else "FAIL", name, detail))
        fh.write("ALL CONTROLS %s\n" % ("PASS" if ok else "FAIL"))
    print("ALL CONTROLS %s" % ("PASS" if ok else "FAIL"))
    return ok
