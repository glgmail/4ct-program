"""Facet-seam foams (SPEC Sec. 4), Mode G.

HalfFoam: chi, dots (lists over facets), owner (dict edge key -> facet),
seams (list of facet triples), nv.

* compose(rec, H)          SPEC 4.3
* glue(H1, H2)             SPEC 4.4 (closed foam H1 u_K mirror(H2))
* eval_closed(...)         SPEC 2.4 / 4.4: direct enumeration of admissible
                           colourings of a closed foam, value at Phi.
* avec(H, tcol, T)         SPEC 4.5: direct enumeration of Col(H, t) for all
                           Tait colourings t at once (bit-parallel over t).

Exponent of one colouring (SPEC 2.4 / 4.5):
  e = sum_f dots(f)(c(f)-1) - chi(F_12) - 2 chi(F_13)  (mod 3).
With chi(F_ij) = sum_{c(f) in {i,j}} chi(f) - const, the constant contributes
3*const = 0 mod 3, and per facet the contribution is
  c=1: 0,   c=2: dots-chi,   c=3: 2(dots-chi)     i.e. (c-1)(dots-chi) mod 3.
GF(4) element codes: a + 2b for a + b*omega; omega^0 -> 1, omega^1 -> 2,
omega^2 = 1+omega -> 3.
"""

import sys


class HalfFoam:
    __slots__ = ("chi", "dots", "owner", "seams", "nv")

    def __init__(self, chi, dots, owner, seams, nv):
        self.chi = chi
        self.dots = dots
        self.owner = owner
        self.seams = seams
        self.nv = nv


EMPTY = HalfFoam([], [], {}, [], 0)


def compose(rec, H):
    """H' = C o H, SPEC 4.3.  H has boundary K' (bottom of rec)."""
    nH = len(H.chi)
    facets = rec.facets
    n = nH + len(facets)
    par = list(range(n))

    def find(x):
        r = x
        while par[r] != r:
            r = par[r]
        while par[x] != r:
            par[x], x = r, par[x]
        return r

    owner = H.owner
    for g, f in enumerate(facets):
        gi = nH + g
        for eps in f[2]:
            a = find(gi)
            b = find(owner[eps])
            if a != b:
                if a < b:
                    par[b] = a
                else:
                    par[a] = b
    cls = [0] * n
    newid = {}
    chi = []
    dots = []
    for i in range(n):
        r = find(i)
        c = newid.get(r)
        if c is None:
            c = len(chi)
            newid[r] = c
            chi.append(0)
            dots.append(0)
        cls[i] = c
    Hchi, Hdots = H.chi, H.dots
    for i in range(nH):
        c = cls[i]
        chi[c] += Hchi[i]
        dots[c] += Hdots[i]
    for g, f in enumerate(facets):
        c = cls[nH + g]
        b = 0
        for eps in f[2]:
            if eps >= 0:
                b += 1
        chi[c] += f[0] - b
        dots[c] += f[1]
    own2 = {}
    for e, e2 in rec.ident:
        own2[e] = cls[owner[e2]]
    for g, f in enumerate(facets):
        c = cls[nH + g]
        for t in f[3]:
            own2[t] = c
    seams = [(cls[a], cls[b], cls[c]) for (a, b, c) in H.seams]
    for (a, b, c) in rec.seams:
        seams.append((cls[nH + a], cls[nH + b], cls[nH + c]))
    return HalfFoam(chi, dots, own2, seams, H.nv + rec.nv)


def degree(H, V):
    """SPEC 4.2: deg H = 2 sum dots - 2 sum chi + 3 nv + (3/2) V."""
    assert V % 2 == 0
    return 2 * sum(H.dots) - 2 * sum(H.chi) + 3 * H.nv + 3 * V // 2


def glue(H1, H2, keys):
    """Closed foam H1 u_K mirror(H2), SPEC 4.4.  Returns (chi, dots, seams, nv)."""
    n1 = len(H1.chi)
    n = n1 + len(H2.chi)
    par = list(range(n))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for e in keys:
        a, b = find(H1.owner[e]), find(n1 + H2.owner[e])
        if a != b:
            par[max(a, b)] = min(a, b)
    cls = {}
    for i in range(n):
        r = find(i)
        if r not in cls:
            cls[r] = len(cls)
    m = [cls[find(i)] for i in range(n)]
    chi = [0] * len(cls)
    dots = [0] * len(cls)
    for i in range(n1):
        chi[m[i]] += H1.chi[i]
        dots[m[i]] += H1.dots[i]
    for i in range(len(H2.chi)):
        chi[m[n1 + i]] += H2.chi[i]
        dots[m[n1 + i]] += H2.dots[i]
    for e in keys:
        if e >= 0:
            chi[m[H1.owner[e]]] -= 1
    seams = [(m[a], m[b], m[c]) for (a, b, c) in H1.seams]
    seams += [(m[n1 + a], m[n1 + b], m[n1 + c]) for (a, b, c) in H2.seams]
    return chi, dots, seams, H1.nv + H2.nv


def closed_degree(chi, dots, nv):
    """KR Def 2.7: deg F = 2 sum d - 2 sum chi + 3 nv."""
    return 2 * sum(dots) - 2 * sum(chi) + 3 * nv


def eval_closed(chi, dots, seams, nv, check_asserts=True, want_colourings=False):
    """Direct evaluation of a closed foam at Phi (SPEC 2.4).

    Enumerates all admissible colourings by backtracking over facets with
    seam propagation.  Returns (value in {0,1}, (n0, n1, n2)).
    Asserts: n1 = n2 mod 2; chi(F_ij(c)) even for all admissible c;
    value 0 when deg < 0 or 6 does not divide deg.
    """
    n = len(chi)
    for s in seams:
        if s[0] == s[1] or s[0] == s[2] or s[1] == s[2]:
            cnt = (0, 0, 0)
            return 0, cnt
    adj = [[] for _ in range(n)]
    for s in seams:
        for x in s:
            adj[x].append(s)
    # static branching order: BFS over seam adjacency
    order = []
    seen = [False] * n
    for st in range(n):
        if seen[st]:
            continue
        seen[st] = True
        q = [st]
        k = 0
        while k < len(q):
            x = q[k]
            k += 1
            order.append(x)
            for s in adj[x]:
                for y in s:
                    if not seen[y]:
                        seen[y] = True
                        q.append(y)
    col = [0] * n
    kap = [(dots[f] - chi[f]) % 3 for f in range(n)]
    counts = [0, 0, 0]
    total_chi = sum(chi)

    def propagate(f, trail):
        stack = [f]
        while stack:
            g = stack.pop()
            for (a, b, c) in adj[g]:
                ca, cb, cc = col[a], col[b], col[c]
                if ca and cb:
                    if ca == cb:
                        return False
                    if cc:
                        if cc != ca ^ cb:
                            return False
                    else:
                        col[c] = ca ^ cb
                        trail.append(c)
                        stack.append(c)
                elif ca and cc:
                    if ca == cc:
                        return False
                    col[b] = ca ^ cc
                    trail.append(b)
                    stack.append(b)
                elif cb and cc:
                    if cb == cc:
                        return False
                    col[a] = cb ^ cc
                    trail.append(a)
                    stack.append(a)
        return True

    def leaf():
        e = 0
        s1 = s2 = s3 = 0
        for f in range(n):
            c = col[f]
            if c == 2:
                e += kap[f]
                s2 += chi[f]
            elif c == 3:
                e += 2 * kap[f]
                s3 += chi[f]
            else:
                s1 += chi[f]
        counts[e % 3] += 1
        if check_asserts:
            # chi(F_ij) = sum over facets coloured i or j - nv
            for x in (s1 + s2 - nv, s1 + s3 - nv, s2 + s3 - nv):
                if x % 2:
                    raise AssertionError("odd chi(F_ij) in a closed foam")

    def rec(pos):
        while pos < n and col[order[pos]]:
            pos += 1
        if pos == n:
            leaf()
            return
        f = order[pos]
        for c in (1, 2, 3):
            trail = [f]
            col[f] = c
            if propagate(f, trail):
                rec(pos + 1)
            for x in trail:
                col[x] = 0

    old = sys.getrecursionlimit()
    if old < 10000:
        sys.setrecursionlimit(10000)
    rec(0)
    n0, n1, n2 = counts
    if check_asserts and (n1 - n2) % 2:
        raise AssertionError("closed foam value not in F")
    val = (n0 + n2) % 2
    if check_asserts:
        deg = closed_degree(chi, dots, nv)
        if (deg < 0 or deg % 6) and val:
            raise AssertionError("nonzero Phi for a closed foam of degree %d" % deg)
    return val, (n0, n1, n2)


def tait_columns(taits, keys):
    """Bit-planes over Tait colourings: key -> (p0, p1) with colour = p0 + 2 p1."""
    T = len(taits)
    cols = {}
    for pos, k in enumerate(keys):
        p0 = p1 = 0
        for t in range(T):
            c = taits[t][pos]
            if c & 1:
                p0 |= 1 << t
            if c & 2:
                p1 |= 1 << t
        cols[k] = (p0, p1)
    return cols


STATS = {"avec": 0, "branch": 0, "maxrep": 0}


def avec(H, tcol, T):
    """a-vector of H (SPEC 4.5) as a pair of T-bit ints (A, B): a(t) = A_t + B_t*omega.

    Direct enumeration of Col(H, t) for all t simultaneously: row t of every
    bit-plane belongs to Tait colouring t.  Facets owning boundary edges are
    fixed by t; the others are determined through seams (third colour = XOR of
    the other two codes), or branched (rows replicated 3x) if not determined.
    A row is alive iff every seam is rainbow and all owned edges agree.
    """
    STATS["avec"] += 1
    n = len(H.chi)
    P = T
    FULL = (1 << P) - 1
    c0 = [None] * n
    c1 = [None] * n
    alive = FULL
    for e, f in H.owner.items():
        q0, q1 = tcol[e]
        if c0[f] is None:
            c0[f] = q0
            c1[f] = q1
        else:
            alive &= ~((c0[f] ^ q0) | (c1[f] ^ q1))
    seams = H.seams
    adj = [[] for _ in range(n)]
    for si, s in enumerate(seams):
        for x in set(s):
            adj[x].append(si)
    done = [False] * len(seams)
    work = [f for f in range(n) if c0[f] is not None]
    reps = 0

    def process(work, alive):
        while work:
            g = work.pop()
            for si in adj[g]:
                if done[si]:
                    continue
                a, b, c = seams[si]
                ka, kb, kc = c0[a] is not None, c0[b] is not None, c0[c] is not None
                nk = ka + kb + kc
                if nk == 3:
                    alive &= ~((c0[a] ^ c0[b] ^ c0[c]) | (c1[a] ^ c1[b] ^ c1[c]))
                    done[si] = True
                elif nk == 2:
                    if not ka:
                        x, y, z = b, c, a
                    elif not kb:
                        x, y, z = a, c, b
                    else:
                        x, y, z = a, b, c
                    if z == x or z == y:
                        # repeated facet with an unknown partner: handled later
                        continue
                    p0 = c0[x] ^ c0[y]
                    p1 = c1[x] ^ c1[y]
                    c0[z] = p0
                    c1[z] = p1
                    alive &= (p0 | p1)
                    done[si] = True
                    work.append(z)
        return alive

    alive = process(work, alive)
    while True:
        unknown = [f for f in range(n) if c0[f] is None]
        if not unknown:
            break
        # branch: prefer an unknown facet sharing a seam with a known one
        pick = None
        for f in unknown:
            for si in adj[f]:
                if any(c0[x] is not None for x in seams[si]):
                    pick = f
                    break
            if pick is not None:
                break
        if pick is None:
            pick = unknown[0]
        STATS["branch"] += 1
        reps += 1
        REP = 1 | (1 << P) | (1 << (2 * P))
        for f in range(n):
            if c0[f] is not None:
                c0[f] *= REP
                c1[f] *= REP
        alive *= REP
        FULLP = FULL
        c0[pick] = FULLP | (FULLP << (2 * P))
        c1[pick] = (FULLP << P) | (FULLP << (2 * P))
        P *= 3
        FULL = (1 << P) - 1
        if P > T * 3 ** 8:
            raise AssertionError("too much branching in avec")
        alive = process([pick], alive)
    for si in range(len(seams)):
        if not done[si]:
            a, b, c = seams[si]
            alive &= ~((c0[a] ^ c0[b] ^ c0[c]) | (c1[a] ^ c1[b] ^ c1[c]))
            # a seam with a repeated facet is never rainbow
            if a == b or a == c or b == c:
                alive = 0
            done[si] = True
    alive &= FULL
    STATS["maxrep"] = max(STATS["maxrep"], reps)
    # exponent mod 3, bit-sliced counter (lo, hi): value = lo + 2 hi in {0,1,2}
    lo = 0
    hi = 0
    for f in range(n):
        k = (H.dots[f] - H.chi[f]) % 3
        if not k:
            continue
        p0, p1 = c0[f], c1[f]
        m2 = p1 & ~p0          # colour 2
        m3 = p0 & p1           # colour 3
        if k == 1:
            add1, add2 = m2, m3
        else:
            add1, add2 = m3, m2
        # +1 under add1
        z = ~(lo | hi)
        nlo = (lo & ~add1) | (add1 & z)
        nhi = (hi & ~add1) | (add1 & lo)
        lo, hi = nlo, nhi
        # +2 under add2
        z = ~(lo | hi)
        nlo = (lo & ~add2) | (add2 & hi)
        nhi = (hi & ~add2) | (add2 & z)
        lo, hi = nlo, nhi
    A = alive & ~lo & FULL
    B = alive & (lo | hi) & FULL
    while P > T:
        P //= 3
        mk = (1 << P) - 1
        A = (A & mk) ^ ((A >> P) & mk) ^ (A >> (2 * P))
        B = (B & mk) ^ ((B >> P) & mk) ^ (B >> (2 * P))
    return A, B


def avec_slow(H, taits, keys):
    """Reference: per-t, row-wise backtracking enumeration of Col(H,t)
    (plain colour lists, seams checked only on complete assignments of the
    facets they touch).  Used in self-tests only."""
    n = len(H.chi)
    kap = [(H.dots[f] - H.chi[f]) % 3 for f in range(n)]
    pos = {k: i for i, k in enumerate(keys)}
    adj = [[] for _ in range(n)]
    for s in H.seams:
        for x in set(s):
            adj[x].append(s)
    out = []
    for t in taits:
        col = [0] * n
        ok = True
        for e, f in H.owner.items():
            c = t[pos[e]]
            if col[f] and col[f] != c:
                ok = False
            col[f] = c
        cnt = [0, 0, 0]
        if ok:
            for (a, b, c) in H.seams:
                if col[a] and col[b] and col[c] and len({col[a], col[b], col[c]}) != 3:
                    ok = False
        if ok:
            # order free facets so each is adjacent to earlier ones when possible
            free = []
            known = set(f for f in range(n) if col[f])
            rest = [f for f in range(n) if not col[f]]
            while rest:
                best = None
                for f in rest:
                    if any(x in known for s in adj[f] for x in s):
                        best = f
                        break
                if best is None:
                    best = rest[0]
                rest.remove(best)
                free.append(best)
                known.add(best)

            def consistent(f):
                for (a, b, c) in adj[f]:
                    ca, cb, cc = col[a], col[b], col[c]
                    if ca and cb and ca == cb:
                        return False
                    if ca and cc and ca == cc:
                        return False
                    if cb and cc and cb == cc:
                        return False
                return True

            def rec(i):
                if i == len(free):
                    e = 0
                    for f in range(n):
                        e += (col[f] - 1) * kap[f]
                    cnt[e % 3] += 1
                    return
                f = free[i]
                for c in (1, 2, 3):
                    col[f] = c
                    if consistent(f):
                        rec(i + 1)
                col[f] = 0
            rec(0)
        # value n0 + n1 w + n2 w^2 = (n0+n2) + (n1+n2) w
        out.append(((cnt[0] + cnt[2]) % 2) | (((cnt[1] + cnt[2]) % 2) << 1))
    return out
