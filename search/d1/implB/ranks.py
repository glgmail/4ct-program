"""Rank computations of SPEC section 7 over packed GF(4) vectors.

A vector in GF(4)^T is a pair (lo, hi) of ints; bit t of lo (hi) is the
coefficient of 1 (omega) of coordinate t.  Pairings beta(u, v) = sum_t u_t v_t.
Gram/pairing matrices are always formed between ORIGINAL a-vectors (an
independent subset of the generated list), so every entry is a pairing value
of two half-foams and must lie in F (asserted); their GF(2) rank equals the
GF(4) rank of the Gram matrix (section 7).
"""

from core import scale_pair, GF4_INV


def _pc(x):
    return bin(x).count("1")


try:
    (1).bit_count()

    def _pc(x):  # noqa: F811
        return x.bit_count()
except AttributeError:
    pass


def beta(u, v):
    """GF(4) code of sum_t u_t v_t."""
    a1, b1 = u
    a2, b2 = v
    bb = b1 & b2
    lo = _pc((a1 & a2) ^ bb) & 1
    hi = _pc((a1 & b2) ^ (b1 & a2) ^ bb) & 1
    return lo | (hi << 1)


def beta_F(u, v):
    c = beta(u, v)
    assert c in (0, 1), "pairing value not in F"
    return c


class Echelon:
    """Row echelon form over GF(4); pivot = lowest set position (leftmost
    column).  Only used to test membership / independence."""

    def __init__(self):
        self.piv = {}

    def add(self, v):
        lo, hi = v
        piv = self.piv
        while True:
            m = lo | hi
            if m == 0:
                return False
            p = (m & -m).bit_length() - 1
            code = ((lo >> p) & 1) | (((hi >> p) & 1) << 1)
            b = piv.get(p)
            if b is None:
                piv[p] = scale_pair(GF4_INV[code], lo, hi)
                return True
            sl, sh = scale_pair(code, b[0], b[1])
            lo ^= sl
            hi ^= sh

    def __len__(self):
        return len(self.piv)


def gf2_rank(rows):
    basis = {}
    r = 0
    for x in rows:
        while x:
            h = x.bit_length() - 1
            b = basis.get(h)
            if b is None:
                basis[h] = x
                r += 1
                break
            x ^= b
    return r


def pairing_rank(A, B):
    """rank over F of the matrix [beta(a, b)]_{a in A, b in B}."""
    rows = []
    for a in A:
        x = 0
        for k, b in enumerate(B):
            if beta_F(a, b):
                x |= 1 << k
        rows.append(x)
    return gf2_rank(rows)


def independent_subset(vecs):
    ech = Echelon()
    return [v for v in vecs if ech.add(v)]


def compute_all(degs, vecs, T):
    """degs[i], vecs[i] (packed) for i = 0..N-1.  Returns dict with
    ell, ell_q, r, r_q, beta_changes, N_ell."""
    N = len(degs)
    S = {}           # d -> independent originals spanning U_d
    ech = {}
    P = {}           # key = |d| -> row bitmasks: rows S[key], columns S[-key]
    ell = {}         # key -> rank of P[key]
    total = 0
    changes = []
    for n in range(N):
        d = degs[n]
        v = vecs[n]
        key = abs(d)
        for dd in (key, -key):
            if dd not in ech:
                ech[dd] = Echelon()
                S[dd] = []
        if key not in P:
            P[key] = []
            ell[key] = 0
        if not ech[d].add(v):
            continue
        S[d].append(v)
        rows = P[key]
        if d == 0:
            c = len(S[0]) - 1
            for k in range(c):
                if beta_F(S[0][k], v):
                    rows[k] |= 1 << c
            x = 0
            for k, w in enumerate(S[0]):
                if beta_F(v, w):
                    x |= 1 << k
            rows.append(x)
        elif d > 0:
            x = 0
            for k, w in enumerate(S[-d]):
                if beta_F(v, w):
                    x |= 1 << k
            rows.append(x)
        else:
            c = len(S[d]) - 1
            for k, w in enumerate(S[-d]):
                if beta_F(w, v):
                    rows[k] |= 1 << c
        newr = gf2_rank(rows)
        old = ell[key]
        if newr != old:
            ell[key] = newr
            total += (newr - old) * (1 if key == 0 else 2)
            changes.append([n + 1, total])
    ell_final = total
    N_ell = 0
    for n, b in changes:
        if b == ell_final:
            N_ell = n
            break
    # ell_q, with an independent check ell_d == ell_{-d} (transposed matrices)
    ell_q = {}
    for key in sorted(P):
        if key == 0:
            r0 = pairing_rank(S[0], S[0])
            assert r0 == ell[0]
            if r0:
                ell_q[0] = r0
        else:
            rp = pairing_rank(S[key], S[-key])
            rm = pairing_rank(S[-key], S[key])
            assert rp == rm == ell[key], "ell_d != ell_-d"
            if rp:
                ell_q[key] = rp
                ell_q[-key] = rp
    assert sum(ell_q.values()) == ell_final
    # r and r_q (section 7.3)
    alld = sorted(d for d in S if S[d])
    allv = []
    for d in alld:
        allv.extend(S[d])
    Ball = independent_subset(allv)
    r = pairing_rank(Ball, Ball)
    r_q = {}
    if N:
        dmin, dmax = min(degs), max(degs)
        kmax = max(dmax, -dmin)

        def h(k):
            I = []
            J = []
            for d in alld:
                if d <= k and (d - k) % 6 == 0:
                    I.extend(S[d])
                if d >= -k and (d + k) % 6 == 0:
                    J.extend(S[d])
            I = independent_subset(I)
            J = independent_subset(J)
            if not I or not J:
                return 0
            return pairing_rank(I, J)
        hv = {}
        for k in range(dmin - 6, kmax + 7):
            hv[k] = h(k) if k >= dmin else 0
        gsum = 0
        for k in range(dmin, kmax + 1):
            g = hv[k] - hv[k - 6]
            assert g >= 0, "negative generator count"
            if g:
                r_q[k] = g
            gsum += g
        for k in range(kmax + 1, kmax + 7):
            assert hv[k] == hv[k - 6], "h not constant above kmax"
        assert gsum == r, "sum g(k) != r"
    assert ell_final <= r <= T
    return {"ell": ell_final, "ell_q": ell_q, "r": r, "r_q": r_q,
            "beta_changes": changes, "N_ell": N_ell}


def ell_only(degs, vecs):
    """ell of a sub-list (used for B19 Remark 4.2)."""
    S = {}
    for d, v in zip(degs, vecs):
        S.setdefault(d, []).append(v)
    for d in S:
        S[d] = independent_subset(S[d])
    tot = 0
    for d in S:
        if -d in S:
            tot += pairing_rank(S[d], S[-d])
    return tot


def sample_pairs(degs, vecs):
    """SPEC 7.5 item 2 sample: k = 1..10000.  Returns list of (i, j, value)
    with 1-based i, j; asserts value in F and the vanishing rule."""
    N = len(degs)
    out = []
    for k in range(1, 10001):
        i = 1 + (7919 * k) % N
        j = 1 + (104729 * k) % N
        val = beta(vecs[i - 1], vecs[j - 1])
        assert val in (0, 1), "sample pairing not in F"
        s = degs[i - 1] + degs[j - 1]
        if s < 0 or s % 6 != 0:
            assert val == 0, "pairing nonzero in forbidden degree"
        out.append((i, j, val))
    return out
