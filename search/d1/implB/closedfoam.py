"""Closed foams in facet-seam form (SPEC 4.1), evaluated directly by the KR
formula: exactly at Phi (SPEC 2.4) and, for unit tests, at points of GF(2^8)
(SPEC 2.5)."""

from itertools import product


def foam_deg(facets, nv):
    return 2 * sum(d for _, d in facets) - 2 * sum(c for c, _ in facets) + 3 * nv


def admissible(facets, seams):
    n = len(facets)
    for c in product((1, 2, 3), repeat=n):
        if all(len({c[a], c[b], c[x]}) == 3 for (a, b, x) in seams):
            yield c


def chi_ij(facets, nv, c, i, j):
    return sum(facets[f][0] for f in range(len(facets)) if c[f] in (i, j)) - nv


def phi_eval(facets, seams, nv):
    """Returns (Phi value in F, deg).  Enforces the SPEC 2.4 asserts."""
    n = [0, 0, 0]
    for c in admissible(facets, seams):
        x12 = chi_ij(facets, nv, c, 1, 2)
        x13 = chi_ij(facets, nv, c, 1, 3)
        x23 = chi_ij(facets, nv, c, 2, 3)
        assert x12 % 2 == 0 and x13 % 2 == 0 and x23 % 2 == 0, "odd chi(F_ij)"
        e = sum(facets[f][1] * (c[f] - 1) for f in range(len(facets))) - x12 - 2 * x13
        n[e % 3] += 1
    assert (n[1] - n[2]) % 2 == 0, "Phi value not in F"
    val = (n[0] + n[2]) % 2
    deg = foam_deg(facets, nv)
    if deg < 0 or deg % 6 != 0:
        assert val == 0, "Phi nonzero in forbidden degree"
    return val, deg


def jflat(facets, seams, nv):
    v, d = phi_eval(facets, seams, nv)
    return v if d == 0 else 0


# ---------------------------------------------------------------- GF(2^8), 0x11B
def g_mul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a & 0x100:
            a ^= 0x11B
    return r


def g_pow(a, e):
    if e < 0:
        a = g_inv(a)
        e = -e
    r = 1
    while e:
        if e & 1:
            r = g_mul(r, a)
        a = g_mul(a, a)
        e >>= 1
    return r


def g_inv(a):
    assert a != 0
    return g_pow(a, 254)


def full_eval(facets, seams, nv, X):
    """sum_c P/Q evaluated at X = (x1, x2, x3) in GF(2^8)."""
    tot = 0
    pairs = {(1, 2): X[0] ^ X[1], (1, 3): X[0] ^ X[2], (2, 3): X[1] ^ X[2]}
    for c in admissible(facets, seams):
        P = 1
        for f, (chi, d) in enumerate(facets):
            P = g_mul(P, g_pow(X[c[f] - 1], d))
        Q = 1
        for (i, j), s in pairs.items():
            x = chi_ij(facets, nv, c, i, j)
            assert x % 2 == 0
            Q = g_mul(Q, g_pow(s, x // 2))
        tot ^= g_mul(P, g_inv(Q))
    return tot


def h_poly(m, X):
    """complete homogeneous h_m at X (char 2)."""
    e1 = X[0] ^ X[1] ^ X[2]
    e2 = g_mul(X[0], X[1]) ^ g_mul(X[0], X[2]) ^ g_mul(X[1], X[2])
    e3 = g_mul(g_mul(X[0], X[1]), X[2])
    if m < 0:
        return 0
    h = [1]
    for k in range(1, m + 1):
        v = g_mul(e1, h[k - 1])
        if k >= 2:
            v ^= g_mul(e2, h[k - 2])
        if k >= 3:
            v ^= g_mul(e3, h[k - 3])
        h.append(v)
    return h[m]


def schur_theta(ns, X):
    """det(h_{n_i - 3 + j})_{i,j=1..3} (Jacobi-Trudi; = KR eq (8) after sorting,
    char 2 so det = permanent and row order is irrelevant)."""
    M = [[h_poly(n - 3 + j, X) for j in (1, 2, 3)] for n in ns]
    tot = 0
    for p in ((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)):
        tot ^= g_mul(g_mul(M[0][p[0]], M[1][p[1]]), M[2][p[2]])
    return tot


# ---------------------------------------------------------------- the SPEC 9.1 foams
def sphere(n):
    return [(2, n)], [], 0


def theta_foam(n1, n2, n3):
    return [(1, n1), (1, n2), (1, n3)], [(0, 1, 2)], 0


def torus(n):
    return [(0, n)], [], 0


def genus2(n):
    return [(-2, n)], [], 0


def web_times_circle(web):
    facets = [(0, 0)] * (web.E + web.m)
    seams = [tuple(web.eidx[3 * v + k] for k in range(3)) for v in range(web.V)]
    return facets, seams, 0


def torus_two_disks():
    return [(1, 0), (1, 0), (1, 0)], [(0, 0, 1), (0, 0, 2)], 1
