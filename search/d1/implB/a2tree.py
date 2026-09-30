"""SPEC Amendment 2, A2.4: SITES, outcomes, paths and leaves, in Mode T.

A family is described by a list of level policies (level j = the j-th move):
  "expand:REDUCIBLE" / "expand:IRREDUCIBLE"  - sites with that outcome are
      expanded (their bottom web's SITES form level j+1); nothing is emitted;
  "emit"  - sites with outcome REDUCIBLE emit their leaves (GEN_STRICT of the
      bottom web); no site is expanded.
Optionally level 1 is restricted to a single site of the root web.
Every site of every expanded node is classified and counted.
"""

from core import (Web, rebuild, sigma, zip_precondition, rec_zip, rec_ih,
                  rec_unzip, rec_saddle, gen, Fail, DEG_TABLE)

OUTCOMES = ("precond", "bridge", "irreducible", "reducible")
KINDS = ("zip", "unzip", "saddle", "ih")


# ---------------------------------------------------------------- SITES (A2.4)
def site_list(K):
    """ALL-mode order of SPEC 6.2 (adjacent pairs included)."""
    out = [("zip", e) for e in K.edge_ids]
    for kind in ("unzip", "saddle"):
        for f in K.faces:
            L = len(f)
            for i in range(L):
                for j in range(i + 1, L):
                    out.append((kind, f[0], i, j))
    out += [("ih", e) for e in K.edge_ids]
    return out


def build_move(K, site):
    """Returns None for PRECOND, else (K2, record)."""
    kind = site[0]
    if kind in ("zip", "ih"):
        if not zip_precondition(K, site[1]):
            return None
        if kind == "zip":
            K2, rec, _, _, _ = rec_zip(K, site[1])
        else:
            K2, rec, _, _ = rec_ih(K, site[1])
        return K2, rec
    f = K.faces[K.face_of[site[1]]]
    assert f[0] == site[1]
    i, j = site[2], site[3]
    assert K.eidx[f[i]] != K.eidx[f[j]], "Unzip/Saddle pair on one edge"
    if kind == "unzip":
        K2, rec, _ = rec_unzip(K, f, i, j)
    else:
        K2, rec, _ = rec_saddle(K, f, i, j)
    return K2, rec


# ---------------------------------------------------------------- GEN_STRICT degrees
def _shift(c, s):
    return {k + s: v for k, v in c.items()}


def _merge(*cs):
    out = {}
    for c in cs:
        for k, v in c.items():
            out[k] = out.get(k, 0) + v
    return out


def gen_count(K):
    """Degree multiset of GEN_STRICT(K) (SPEC 6.1, STRICT, all faces, no
    marker), or None if it fails.  Same face choice and webs as core.gen."""
    if K.V == 0 and K.m == 0:
        return {0: 1}
    if K.m > 0:
        sub = gen_count(Web(K.alpha, K.m - 1, validate=False))
        if sub is None:
            return None
        return _merge(_shift(sub, -2), sub, _shift(sub, 2))
    if K.has_bridge():
        return None
    chosen = None
    for L in (2, 3, 4):
        for f in K.faces:
            if len(f) == L:
                chosen = f
                break
        if chosen is not None:
            break
    if chosen is None:
        return None
    f = chosen
    L = len(f)
    vs = [x // 3 for x in f]
    lg = [sigma(x) for x in f]
    if L == 2:
        K2, _, _ = rebuild(K, vs, [], [(lg[0], lg[1])])
        sub = gen_count(K2)
        if sub is None:
            return None
        return _merge(_shift(sub, DEG_TABLE["C2"]), _shift(sub, DEG_TABLE["C2d"]))
    if L == 3:
        K2, _, _ = rebuild(K, vs, [(lg[0], lg[2], lg[1])], [])
        return gen_count(K2)
    Ka, _, _ = rebuild(K, vs, [], [(lg[0], lg[1]), (lg[2], lg[3])])
    sa = gen_count(Ka)
    if sa is None:
        return None
    Kb, _, _ = rebuild(K, vs, [], [(lg[1], lg[2]), (lg[3], lg[0])])
    sb = gen_count(Kb)
    if sb is None:
        return None
    return _merge(sa, sb)


# ---------------------------------------------------------------- column helpers
def apply_tc(cols, tcols):
    out = []
    for entries in tcols:
        lo = hi = 0
        for k, code in entries:
            a, b = cols[k]
            if code == 1:
                lo ^= a
                hi ^= b
            elif code == 2:
                lo ^= b
                hi ^= a ^ b
            else:
                lo ^= a ^ b
                hi ^= a
        out.append((lo, hi))
    return out


def row_hex(cols, i):
    return "".join("0123"[((lo >> i) & 1) | (((hi >> i) & 1) << 1)] for lo, hi in cols)


def row_packed(cols, i):
    lo = hi = 0
    for t, (a, b) in enumerate(cols):
        lo |= ((a >> i) & 1) << t
        hi |= ((b >> i) & 1) << t
    return lo, hi


# ---------------------------------------------------------------- the walk
def new_counts():
    return {"sites": {}, "expanded": {}, "leaves": {}, "retained": {}}


def _bump_site(cnt, level, kind, outcome):
    lv = cnt["sites"].setdefault(level, {k: {o: 0 for o in OUTCOMES} for k in KINDS})
    lv[kind][outcome] += 1


def _bump(d, k, v=1):
    d[k] = d.get(k, 0) + v


def classify(K, site, need_leaves, S=None, wanted=None):
    """Outcome of a site.  Returns (outcome, K2, rec, extra).

    count mode (S None): extra is the GEN_STRICT degree multiset when REDUCIBLE.
    a-vector mode, need_leaves (an emitting level): the outcome is decided by the
    degree-only GEN; extra is (S2, tcols, G, degree multiset) when REDUCIBLE, where
    the transfer and the Gen object G are computed only if wanted(rec, multiset)
    (some leaf is retained), else (None, None, None, multiset): A2.4 lets the
    a-vectors of non-retained leaves be skipped; they are counted from the multiset.
    a-vector mode, not need_leaves: extra is (S2, tcols, None)."""
    bm = build_move(K, site)
    if bm is None:
        return "precond", None, None, None
    K2, rec = bm
    if K2.has_bridge():
        return "bridge", K2, rec, None
    if S is None:                       # count-only
        c = gen_count(K2)
        return ("reducible" if c is not None else "irreducible"), K2, rec, c
    if need_leaves:
        c = gen_count(K2)
        if c is None:
            return "irreducible", K2, rec, None
        if wanted is not None and not wanted(rec, c):
            return "reducible", K2, rec, (None, None, None, c)
        S2, tc = rec.transfer(S)
        G = gen(K2, S2, True, None)     # succeeds when gen_count does (same greedy)
        return "reducible", K2, rec, (S2, tc, G, c)
    S2, tc = rec.transfer(S)
    c = gen_count(K2)
    return ("reducible" if c is not None else "irreducible"), K2, rec, (S2, tc, None)


def walk(K, policies, level, cnt, retain, S=None, chain=None, restrict=None,
         out=None, prefix_moves=(), prefix_deg=0):
    """Expand node K at `level` (its sites are level+1).  In a-vector mode
    (S given) `chain` is the list of transfer tcols from the root down to K,
    and retained leaves are appended to `out` as (moves, chain_labels, deg,
    cols_at_root, row).  retain(deg) -> bool."""
    _bump(cnt["expanded"], level)
    pol = policies[level]
    sites = site_list(K)
    if restrict is not None and level == 0:
        assert restrict in sites
        sites = [restrict]
    lv = level + 1
    emit = pol == "emit"
    want = None if emit else pol.split(":")[1].lower()

    def wanted(rec, c):
        d0 = prefix_deg + rec.deg
        return any(retain(d0 + dg) for dg in c)
    for site in sites:
        outcome, K2, rec, extra = classify(K, site, emit, S, wanted)
        _bump_site(cnt, lv, site[0], outcome)
        moves = prefix_moves + (list(site),)
        if emit:
            if outcome != "reducible":
                continue
            d0 = prefix_deg + rec.deg
            if S is None:
                for dg, n in extra.items():
                    _bump(cnt["leaves"], d0 + dg, n)
                    if retain(d0 + dg):
                        _bump(cnt["retained"], d0 + dg, n)
                continue
            S2, tc, G, c = extra
            if G is None:                   # no retained leaf: count from the multiset
                for dg, n in c.items():
                    _bump(cnt["leaves"], d0 + dg, n)
                continue
            gc = {}
            for dg in G.degs:
                _bump(cnt["leaves"], d0 + dg)
                _bump(gc, dg)
            assert gc == c, "GEN degrees differ from the degree-only GEN"
            idx = [i for i in range(G.n) if retain(d0 + G.degs[i])]
            if not idx:
                continue
            cols = apply_tc(G.cols, tc)
            for tcs in reversed(chain):
                cols = apply_tc(cols, tcs)
            for i in idx:
                _bump(cnt["retained"], d0 + G.degs[i])
                out.append((list(moves), list(G.chains[i]), d0 + G.degs[i], row_hex(cols, i)))
        else:
            if outcome != want:
                continue
            if S is None:
                walk(K2, policies, lv, cnt, retain, None, None, None, None,
                     moves, prefix_deg + rec.deg)
            else:
                S2, tc, _ = extra
                walk(K2, policies, lv, cnt, retain, S2, chain + [tc], None, out,
                     moves, prefix_deg + rec.deg)


def descend(K, path, S=None):
    """Follow a path of sites from K; returns (K_k, S_k, [tcols...], deg sum,
    moves)."""
    chain = []
    deg = 0
    moves = []
    for site in path:
        bm = build_move(K, site)
        assert bm is not None
        K2, rec = bm
        if S is not None:
            S, tc = rec.transfer(S)
            chain.append(tc)
        deg += rec.deg
        moves.append(list(site))
        K = K2
    return K, S, chain, deg, tuple(moves)


def enumerate_units(K, policies, unit_level, restrict=None):
    """Paths (lists of sites) to the nodes expanded at unit_level, in DFS
    order, plus the site counts for levels <= unit_level (count mode)."""
    cnt = new_counts()
    units = []

    def rec(K, level, path):
        if level == unit_level:
            units.append(list(path))
            return
        _bump(cnt["expanded"], level)
        pol = policies[level]
        assert pol != "emit"
        want = pol.split(":")[1].lower()
        sites = site_list(K)
        if restrict is not None and level == 0:
            sites = [restrict]
        for site in sites:
            outcome, K2, r, extra = classify(K, site, False, None)
            _bump_site(cnt, level + 1, site[0], outcome)
            if outcome == want:
                rec(K2, level + 1, path + [site])
    rec(K, 0, [])
    return units, cnt


def merge_counts(a, b):
    for lv, kinds in b["sites"].items():
        tgt = a["sites"].setdefault(lv, {k: {o: 0 for o in OUTCOMES} for k in KINDS})
        for k in KINDS:
            for o in OUTCOMES:
                tgt[k][o] += kinds[k][o]
    for key in ("expanded", "leaves", "retained"):
        for k, v in b[key].items():
            _bump(a[key], k, v)
    return a
