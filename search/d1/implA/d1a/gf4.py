"""GF(4) vectors as bit-plane pairs and exact linear algebra (SPEC 7.4).

A vector v in GF(4)^n is a pair (A, B) of n-bit ints: v_t = A_t + B_t*omega.
Scalar codes: 0, 1, 2 = omega, 3 = omega^2 = 1 + omega.
"""

INV = {1: 1, 2: 3, 3: 2}


def mul(x, y):
    """Product of GF(4) codes."""
    if not x or not y:
        return 0
    lg = {1: 0, 2: 1, 3: 2}
    return (1, 2, 3)[(lg[x] + lg[y]) % 3]


def add(u, v):
    return (u[0] ^ v[0], u[1] ^ v[1])


def scale(v, c):
    A, B = v
    if c == 1:
        return v
    if c == 2:        # omega*(a + b w) = b + (a+b) w
        return (B, A ^ B)
    if c == 3:        # omega^2*(a + b w) = (a+b) + a w
        return (A ^ B, A)
    return (0, 0)


def coef(v, p):
    return ((v[0] >> p) & 1) | (((v[1] >> p) & 1) << 1)


def dot(u, v):
    """beta(u, v) = sum_t u_t v_t, as a GF(4) code."""
    A1, B1 = u
    A2, B2 = v
    bb = (B1 & B2).bit_count()
    lo = ((A1 & A2).bit_count() + bb) & 1
    hi = ((A1 & B2).bit_count() + (B1 & A2).bit_count() + bb) & 1
    return lo | (hi << 1)


def from_codes(codes):
    A = B = 0
    for t, c in enumerate(codes):
        if c & 1:
            A |= 1 << t
        if c & 2:
            B |= 1 << t
    return (A, B)


def to_codes(v, n):
    return [coef(v, t) for t in range(n)]


def to_hex(v, n):
    A, B = v
    sa = format(A, "0%db" % n)[::-1] if n else ""
    sb = format(B, "0%db" % n)[::-1] if n else ""
    return "".join("0123"[(a == "1") + 2 * (b == "1")] for a, b in zip(sa, sb))


class Echelon:
    """Row echelon basis; pivot = lowest set coordinate (leftmost column)."""
    __slots__ = ("piv", "rows")

    def __init__(self):
        self.piv = {}
        self.rows = []     # the vectors as inserted (a basis of the span)

    def reduce(self, v):
        A, B = v
        piv = self.piv
        while True:
            x = A | B
            if not x:
                return (0, 0), -1
            p = (x & -x).bit_length() - 1
            r = piv.get(p)
            if r is None:
                return (A, B), p
            c = ((A >> p) & 1) | (((B >> p) & 1) << 1)
            rA, rB = scale(r, c)
            A ^= rA
            B ^= rB

    def add(self, v):
        w, p = self.reduce(v)
        if p < 0:
            return False
        c = coef(w, p)
        self.piv[p] = scale(w, INV[c])
        self.rows.append(v)
        return True

    def __len__(self):
        return len(self.piv)


def rank_of(vectors):
    E = Echelon()
    for v in vectors:
        E.add(v)
    return len(E)


def pairing_rank(rows, cols, assert_F=False):
    """rank of the matrix [dot(r, c)].  With assert_F, every entry must lie
    in F = {0, 1} (true for pairings of half-foam a-vectors, SPEC 4.5)."""
    E = Echelon()
    for r in rows:
        A = B = 0
        for k, c in enumerate(cols):
            x = dot(r, c)
            if assert_F and x > 1:
                raise AssertionError("pairing value not in F")
            if x & 1:
                A |= 1 << k
            if x & 2:
                B |= 1 << k
        E.add((A, B))
    return len(E)


class PairRank:
    """Incremental rank of the pairing matrix between a growing row space R and
    a growing column space C (both given by independent vectors).

    Invariant: R = span(pivot rows) + span(kernel); every kernel vector pairs
    to zero with all columns; pivot c-vectors are in echelon form.
    rank = number of pivot rows.
    """
    __slots__ = ("cols", "piv", "kernel")

    def __init__(self):
        self.cols = []
        self.piv = {}       # column index -> [T-vector, c-vector]
        self.kernel = []

    @property
    def rank(self):
        return len(self.piv)

    def add_col(self, w):
        k = len(self.cols)
        self.cols.append(w)
        bit = 1 << k
        for p, pr in self.piv.items():
            c = dot(pr[0], w)
            if c:
                cv = pr[1]
                pr[1] = (cv[0] | (bit if c & 1 else 0), cv[1] | (bit if c & 2 else 0))
        vals = [dot(z, w) for z in self.kernel]
        i0 = -1
        for i, v in enumerate(vals):
            if v:
                i0 = i
                break
        if i0 < 0:
            return
        z0 = scale(self.kernel[i0], INV[vals[i0]])
        newk = []
        for i, z in enumerate(self.kernel):
            if i == i0:
                continue
            if vals[i]:
                z = add(z, scale(z0, vals[i]))
            newk.append(z)
        self.kernel = newk
        self.piv[k] = [z0, (bit, 0)]

    def add_row(self, u):
        A = B = 0
        for k, w in enumerate(self.cols):
            c = dot(u, w)
            if c & 1:
                A |= 1 << k
            if c & 2:
                B |= 1 << k
        tv = u
        piv = self.piv
        while True:
            x = A | B
            if not x:
                self.kernel.append(tv)
                return
            p = (x & -x).bit_length() - 1
            pr = piv.get(p)
            if pr is None:
                cinv = INV[((A >> p) & 1) | (((B >> p) & 1) << 1)]
                piv[p] = [scale(tv, cinv), scale((A, B), cinv)]
                return
            c = ((A >> p) & 1) | (((B >> p) & 1) << 1)
            sA, sB = scale(pr[1], c)
            A ^= sA
            B ^= sB
            tv = add(tv, scale(pr[0], c))
