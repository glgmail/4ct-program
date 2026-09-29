"""D1 Phase 2, Implementation B (Mode T): webs, REBUILD, cobordism records,
transfer matrices and half-foam generation.  Python 3 standard library only.

Everything follows search/d1/SPEC.md; section numbers in comments refer to it.

GF(4) elements are encoded as in SPEC section 0: a + b*omega -> a + 2b.
Mode T never builds a half-foam: a generated list of half-foams with boundary
K is carried as its a-vectors (section 4.5), and a_{C o H} = a_H . T_C
(section 4.6).  The list is stored COLUMN-wise: for each Tait colouring t of
K a pair (lo, hi) of Python ints whose bit i is the F-coordinate (1, omega)
of a_{h_i}(t).  Multiplying all rows by a sparse transfer matrix is then a few
big-integer XORs per nonzero entry.

Only the columns of Tait colourings that can reach the target web are
carried (a subset S of Tait(K), closed under the transfer-matrix support);
columns outside S do not influence any a-vector entry at the target, because
T_C(t', t) = 0 unless t' is produced from t by a local colouring.
"""

from itertools import product

# ---------------------------------------------------------------- GF(4)
GF4_MUL = [[0, 0, 0, 0],
           [0, 1, 2, 3],
           [0, 2, 3, 1],
           [0, 3, 1, 2]]
GF4_INV = [None, 1, 3, 2]
OMEGA_POW = [1, 2, 3]          # omega^0, omega^1, omega^2 as codes


def scale_pair(code, lo, hi):
    """Multiply a packed GF(4) vector (lo, hi) by the scalar with this code."""
    if code == 1:
        return lo, hi
    if code == 2:              # omega*(a + b w) = b + (a+b) w
        return hi, lo ^ hi
    if code == 3:              # omega^2*(a + b w) = (a+b) + a w
        return lo ^ hi, lo
    return 0, 0


def sigma(d):
    return 3 * (d // 3) + ((d % 3) + 1) % 3


# ---------------------------------------------------------------- webs (section 3)
class Web:
    """A web: V trivalent vertices (darts 3v..3v+2, CCW), involution alpha,
    and m vertexless circles.  Items (Tait coordinates) are the edges in
    increasing edge id, followed by the circles in id order."""

    __slots__ = ("alpha", "V", "m", "edge_ids", "eidx", "E", "nitems",
                 "faces", "face_of")

    def __init__(self, alpha, m, validate=True):
        self.alpha = list(alpha)
        nd = len(self.alpha)
        assert nd % 3 == 0
        self.V = nd // 3
        self.m = m
        a = self.alpha
        for d in range(nd):
            assert a[d] is not None and 0 <= a[d] < nd, "alpha undefined"
            assert a[d] != d, "alpha has a fixed point"
            assert a[a[d]] == d, "alpha not an involution"
        self.edge_ids = [d for d in range(nd) if d < a[d]]
        self.E = len(self.edge_ids)
        eidx = [0] * nd
        for i, e in enumerate(self.edge_ids):
            eidx[e] = i
            eidx[a[e]] = i
        self.eidx = eidx
        self.nitems = self.E + m
        # faces: phi(d) = sigma(alpha(d)); canonical form starts at min dart
        face_of = [-1] * nd
        faces = []
        for d in range(nd):
            if face_of[d] >= 0:
                continue
            fi = len(faces)
            orb = []
            x = d
            while face_of[x] < 0:
                face_of[x] = fi
                orb.append(x)
                x = sigma(a[x])
            assert x == d
            faces.append(tuple(orb))
        self.faces = faces
        self.face_of = face_of
        if validate:
            self._validate_euler()

    def _validate_euler(self):
        V = self.V
        if V == 0:
            return
        parent = list(range(V))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for d in range(3 * V):
            ra, rb = find(d // 3), find(self.alpha[d] // 3)
            if ra != rb:
                parent[ra] = rb
        comps = len({find(v) for v in range(V)})
        assert V - self.E + len(self.faces) == 2 * comps, "Euler check failed"

    def has_bridge(self):
        fo = self.face_of
        a = self.alpha
        return any(fo[d] == fo[a[d]] for d in range(3 * self.V))

    def edge_item(self, d):
        return self.eidx[d]

    def circle_item(self, c):
        return self.E + c

    def is_interval_item(self, j):
        return j < self.E


def web_from_neighbours(lines):
    """Appendix A format: 'v: w0,w1,w2' (CCW).  Returns alpha."""
    nb = {}
    for tok in lines:
        v, rest = tok.split(":")
        nb[int(v)] = [int(x) for x in rest.split(",")]
    V = len(nb)
    alpha = [None] * (3 * V)
    for v in range(V):
        for k, w in enumerate(nb[v]):
            pos = nb[w].index(v)
            assert nb[w].count(v) == 1
            alpha[3 * v + k] = 3 * w + pos
    return alpha


# ---------------------------------------------------------------- Tait colourings
def tait_colourings(web):
    """All Tait colourings of web, as tuples over its items, in the canonical
    (lexicographic) order of section 3.3.  Exhaustive search with forced-move
    propagation; used only for target and control webs."""
    V, E = web.V, web.E
    vedges = [[web.eidx[3 * v + k] for k in range(3)] for v in range(V)]
    for v in range(V):
        if len(set(vedges[v])) < 3:
            return []                           # loop
    ends = [[] for _ in range(E)]
    for v in range(V):
        for e in vedges[v]:
            ends[e].append(v)
    col = [0] * E
    used = [0] * V                              # bitmask of colours at v
    out = []

    def options(e):
        u, w = ends[e]
        m = used[u] | used[w]
        return [c for c in (1, 2, 3) if not (m >> c) & 1]

    def rec(ncol):
        if ncol == E:
            out.append(tuple(col))
            return
        best, bopt = -1, None
        for e in range(E):
            if col[e] == 0:
                o = options(e)
                if best < 0 or len(o) < len(bopt):
                    best, bopt = e, o
                    if len(o) <= 1:
                        break
        if not bopt:
            return
        u, w = ends[best]
        for c in bopt:
            col[best] = c
            used[u] |= 1 << c
            used[w] |= 1 << c
            rec(ncol + 1)
            used[u] &= ~(1 << c)
            used[w] &= ~(1 << c)
        col[best] = 0

    if E > 0:
        rec(0)
    else:
        out = [()]
    res = []
    for t in out:
        for circ in product((1, 2, 3), repeat=web.m):
            res.append(t + circ)
    res.sort()
    return res


def is_tait(web, t):
    for v in range(web.V):
        s = {t[web.eidx[3 * v + k]] for k in range(3)}
        if s != {1, 2, 3}:
            return False
    return all(c in (1, 2, 3) for c in t)


# ---------------------------------------------------------------- REBUILD (section 3.4)
def rebuild(K, D, NV, J):
    """Returns (K', dmap, join_items) where join_items[i] is the K'-item of
    the edge (or circle) through join pair i."""
    Dset = set(D)
    surv = [v for v in range(K.V) if v not in Dset]
    s = len(surv)
    newv = {v: i for i, v in enumerate(surv)}
    dmap = {}
    for v in surv:
        for k in range(3):
            dmap[3 * v + k] = 3 * newv[v] + k
    port_slot = {}
    labels = {}
    for i, triple in enumerate(NV):
        for k, slot in enumerate(triple):
            nd = 3 * (s + i) + k
            if isinstance(slot, int):
                assert slot // 3 in Dset and slot not in port_slot
                port_slot[slot] = nd
            else:
                labels.setdefault(slot, []).append(nd)
    jp = {}
    for ji, (p, q) in enumerate(J):
        assert p // 3 in Dset and q // 3 in Dset
        assert p not in jp and q not in jp and p not in port_slot and q not in port_slot
        jp[p] = (q, ji)
        jp[q] = (p, ji)
    nV = s + len(NV)
    alpha2 = [None] * (3 * nV)
    join_dart = [None] * len(J)
    Ka = K.alpha

    def trace(x):
        vis = []
        while True:
            if x // 3 not in Dset:
                return dmap[x], vis
            if x in port_slot:
                return port_slot[x], vis
            if x in jp:
                y, ji = jp[x]
                vis.append(ji)
                x = Ka[y]
                continue
            raise AssertionError("REBUILD reached an unassigned dart %d" % x)

    for v in surv:
        for k in range(3):
            d = 3 * v + k
            partner, vis = trace(Ka[d])
            alpha2[dmap[d]] = partner
            for ji in vis:
                join_dart[ji] = dmap[d]
    for p in sorted(port_slot):
        nd = port_slot[p]
        partner, vis = trace(Ka[p])
        alpha2[nd] = partner
        for ji in vis:
            join_dart[ji] = nd
    for lab in sorted(labels, key=str):
        pair = labels[lab]
        assert len(pair) == 2
        alpha2[pair[0]] = pair[1]
        alpha2[pair[1]] = pair[0]
    # closed chains of joins -> new circles, in the order of their first join in J
    m2 = K.m
    join_circle = [None] * len(J)
    for ji in range(len(J)):
        if join_dart[ji] is not None or join_circle[ji] is not None:
            continue
        cid = m2
        m2 += 1
        join_circle[ji] = cid
        p0, q0 = J[ji]
        x = Ka[q0]
        while x != p0:
            assert x in jp, "open join chain not reached by trace"
            y, jk = jp[x]
            assert join_dart[jk] is None
            join_circle[jk] = cid
            x = Ka[y]
    K2 = Web(alpha2, m2)
    join_items = []
    for ji in range(len(J)):
        if join_dart[ji] is not None:
            join_items.append(K2.eidx[join_dart[ji]])
        else:
            join_items.append(K2.E + join_circle[ji])
    return K2, dmap, join_items


def update_marker(K, mk, D, dmap):
    """Original single-marker rule of SPEC 3.7 (superseded by Amendment 1 A4;
    kept for reference, not used)."""
    if mk is None:
        return None
    Dset = set(D)
    if mk // 3 not in Dset:
        return dmap[mk]
    orb = K.faces[K.face_of[mk]]
    for d in orb:
        if d // 3 not in Dset:
            return dmap[d]
    return None


def components(K):
    """Component label (smallest vertex) of every vertex of K."""
    V = K.V
    parent = list(range(V))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for d in range(3 * V):
        ra, rb = find(d // 3), find(K.alpha[d] // 3)
        if ra != rb:
            if ra < rb:
                parent[rb] = ra
            else:
                parent[ra] = rb
    return [find(v) for v in range(V)]


def count_event(ev, key, n=1):
    if ev is not None:
        ev[key] = ev.get(key, 0) + n


class MarkerLost(Exception):
    pass


def update_markers(K, K2, markers, D, dmap, ev=None):
    """Amendment 1, A4: a tuple of outer-face darts, at most one per component
    of K2.  For every old marker m (face orbit O in K), the candidates are
    dmap(m) if m's vertex survives, then the surviving darts of O in orbit
    order from O's minimum dart (the SPEC 3.7 rule), each mapped by dmap; the
    first candidate in each K2 component becomes that component's marker.
    If no dart of O survives: if every vertex of m's component was deleted
    (the component became circles or vanished) the marker is dropped;
    otherwise the outer face disappeared -> MarkerLost (a FAIL, counted).
    Components of K2 that get no marker are counted (all their faces are
    eligible).  Returns the new tuple (possibly empty)."""
    if markers is None:
        return None
    Dset = set(D)
    compK = components(K)
    comp2 = components(K2)
    new = []
    seen = set()
    for mk in markers:
        orb = K.faces[K.face_of[mk]]
        cand = []
        if mk // 3 not in Dset:
            cand.append(dmap[mk])
        for d in orb:
            if d // 3 not in Dset and d != mk:
                cand.append(dmap[d])
        if not cand:
            c = compK[mk // 3]
            if all(v in Dset for v in range(K.V) if compK[v] == c):
                count_event(ev, "marker_component_vanished")
                continue
            count_event(ev, "marker_loss_fail")
            raise MarkerLost()
        for d2 in cand:
            c2 = comp2[d2 // 3]
            if c2 not in seen:
                seen.add(c2)
                new.append(d2)
    unmarked_before = len(set(compK)) - len(markers)
    unmarked_after = len(set(comp2)) - len(seen)
    if unmarked_after > unmarked_before:
        count_event(ev, "unmarked_component_created", unmarked_after - unmarked_before)
    return tuple(new)


def n_components(K):
    return len(set(components(K)))


# ---------------------------------------------------------------- records (sections 4.3, 4.6, 5)
DEG_TABLE = {"C1": -2, "C1d": 0, "C1dd": 2, "C2": -1, "C2d": 1, "C3": 0,
             "C4a": 0, "C4b": 0, "zip": 1, "unzip": 1, "saddle": 2, "ih": 1}


class Record:
    """Elementary cobordism C : Kb -> Kt (bottom Kb = K', top Kt = K).

    facets: list of (chi, dots, bot_items (Kb items), top_items (Kt items)).
    """

    def __init__(self, label, Kt, Kb, dmap, facets, seams, nv, Vt, Vb,
                 circle_map=None):
        self.label = label
        self.Kt, self.Kb = Kt, Kb
        # merge nominal facets that share a bottom (or top) item (section 4.3)
        n = len(facets)
        par = list(range(n))

        def find(x):
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            return x
        owner_b, owner_t = {}, {}
        for g, (chi, dots, bot, top) in enumerate(facets):
            for j in bot:
                if j in owner_b:
                    par[find(g)] = find(owner_b[j])
                else:
                    owner_b[j] = g
            for j in top:
                if j in owner_t:
                    par[find(g)] = find(owner_t[j])
                else:
                    owner_t[j] = g
        classes = {}
        for g in range(n):
            classes.setdefault(find(g), []).append(g)
        reps = sorted(classes)
        cls_index = {r: i for i, r in enumerate(reps)}
        self.merged = any(len(v) > 1 for v in classes.values())
        F = []
        for r in reps:
            mem = classes[r]
            chis = {facets[g][0] for g in mem}
            if len(mem) > 1:
                # only the shared-sheet case of section 4.3 is expected
                bots = {frozenset(facets[g][2]) for g in mem}
                assert len(chis) == 1 and len(bots) == 1, \
                    "unexpected facet merge in %s" % label
            chi = facets[mem[0]][0]
            dots = sum(facets[g][1] for g in mem)
            bot = set()
            top = set()
            for g in mem:
                bot |= set(facets[g][2])
                top |= set(facets[g][3])
            F.append((chi, dots, tuple(sorted(bot)), tuple(sorted(top))))
        self.facets = F
        self.seams = [tuple(cls_index[find(g)] for g in tr) for tr in seams]
        self.nv, self.Vt, self.Vb = nv, Vt, Vb
        # bottom/top ownership
        bot_owner = {}
        top_owner = {}
        for g, (chi, dots, bot, top) in enumerate(F):
            for j in bot:
                assert j not in bot_owner
                bot_owner[j] = g
            for j in top:
                assert j not in top_owner
                top_owner[j] = g
        self.bot_owner, self.top_owner = bot_owner, top_owner
        # identity map (section 3.5): Kb item -> Kt item
        inv = {v: k for k, v in dmap.items()}
        src = [None] * Kb.nitems
        seen_t = set()
        for j in range(Kb.E):
            if j in bot_owner:
                continue
            d2 = Kb.edge_ids[j]
            e2 = Kb.alpha[d2]
            assert d2 in inv and e2 in inv, "new dart on a non-involved edge"
            d = inv[d2]
            assert Kt.alpha[d] == inv[e2], "identity edge not preserved"
            it = Kt.eidx[d]
            assert it not in top_owner
            src[j] = it
            seen_t.add(it)
        for c in range(Kb.m):
            j = Kb.E + c
            if j in bot_owner:
                continue
            ct = c if circle_map is None else circle_map[c]
            assert ct < Kt.m
            it = Kt.E + ct
            assert it not in top_owner
            src[j] = it
            seen_t.add(it)
        for it in range(Kt.nitems):
            assert (it in seen_t) != (it in top_owner), "Kt item coverage"
        assert len(seen_t) == sum(1 for x in src if x is not None)
        self.src = src
        # interval bottom items per facet
        self.nbint = [sum(1 for j in bot if j < Kb.E) for (_, _, bot, _) in F]
        # degree (section 4.3) against B19 Table 1
        b = sum(self.nbint)
        twice = 4 * sum(f[1] for f in F) - 4 * (sum(f[0] for f in F) - b) \
            + 6 * nv + 3 * (Vt - Vb)
        assert twice % 2 == 0
        self.deg = twice // 2
        base = label
        assert self.deg == DEG_TABLE[base], (label, self.deg)
        assert (Vb - Vt) % 2 == 0

    def local_colourings(self, t):
        """Yield (t', e) for every local colouring compatible with the top
        colouring t (a Tait colouring of Kt), e = e(C,c) mod 3."""
        F = self.facets
        fixed = []
        free = []
        for g, (chi, dots, bot, top) in enumerate(F):
            if top:
                cs = {t[j] for j in top}
                if len(cs) != 1:
                    return
                fixed.append(cs.pop())
            else:
                fixed.append(0)
                free.append(g)
        base = [t[s] if s is not None else 0 for s in self.src]
        Kb = self.Kb
        cst2 = self.Vb - self.Vt
        for combo in product((1, 2, 3), repeat=len(free)):
            c = fixed[:]
            for g, col in zip(free, combo):
                c[g] = col
            ok = True
            for (x, y, z) in self.seams:
                if c[x] == c[y] or c[x] == c[z] or c[y] == c[z]:
                    ok = False
                    break
            if not ok:
                continue
            tp = base[:]
            for g, (chi, dots, bot, top) in enumerate(F):
                for j in bot:
                    tp[j] = c[g]
            # e(C,c) = sum dots (c-1) - chi12 - 2 chi13      (section 4.6)
            s12 = s13 = 0
            b12 = b13 = 0
            dsum = 0
            for g, (chi, dots, bot, top) in enumerate(F):
                cg = c[g]
                dsum += dots * (cg - 1)
                if cg in (1, 2):
                    s12 += chi
                if cg in (1, 3):
                    s13 += chi
            for j in self.bot_owner:
                if j < Kb.E:
                    col = tp[j]
                    if col in (1, 2):
                        b12 += 1
                    if col in (1, 3):
                        b13 += 1
            # chi_ij = S_ij - b_ij - nv + (Vb - Vt)/2 ; keep doubled to stay integral
            chi12x2 = 2 * (s12 - b12 - self.nv) + cst2
            chi13x2 = 2 * (s13 - b13 - self.nv) + cst2
            assert chi12x2 % 2 == 0 and chi13x2 % 2 == 0
            e = (dsum - chi12x2 // 2 - chi13x2) % 3
            yield tuple(tp), e

    def transfer(self, S):
        """S: list of Tait colourings of Kt.  Returns (S', cols) where S' is the
        sorted list of Kb colourings reached, and cols[k] is the list of
        (index into S', GF(4) code) of the nonzero entries T_C(t', S[k])."""
        acc = []
        reached = set()
        for t in S:
            dct = {}
            for tp, e in self.local_colourings(t):
                dct[tp] = dct.get(tp, 0) ^ OMEGA_POW[e]
                reached.add(tp)
            acc.append(dct)
        Sp = sorted(reached)
        idx = {tp: i for i, tp in enumerate(Sp)}
        cols = []
        for dct in acc:
            cols.append([(idx[tp], v) for tp, v in sorted(dct.items()) if v])
        return Sp, cols

    def support(self, S):
        """Set of (t', t) pairs with at least one local colouring."""
        out = set()
        for t in S:
            for tp, e in self.local_colourings(t):
                out.add((tp, t))
        return out


# ---------------------------------------------------------------- the twelve cobordisms (section 5)
def sheet(K2, j):
    return 1 if j < K2.E else 0


def rec_disk(K, delta):
    """Section 5.1: returns (K', record, dmap)."""
    assert K.m >= 1
    K2 = Web(K.alpha, K.m - 1, validate=False)
    dmap = {d: d for d in range(3 * K.V)}
    lab = ["C1", "C1d", "C1dd"][delta]
    facets = [(1, delta, (), (K.E + K.m - 1,))]
    r = Record(lab, K, K2, dmap, facets, [], 0, 0, 0)
    return K2, r, dmap


def rec_bigon(K, f, dotted):
    f0, f1 = f
    v0, v1 = f0 // 3, f1 // 3
    assert v0 != v1
    l0, l1 = sigma(f0), sigma(f1)
    K2, dmap, ji = rebuild(K, [v0, v1], [], [(l0, l1)])
    a = ji[0]
    E = K.eidx
    facets = [(sheet(K2, a), 0, (a,), tuple({E[l0], E[l1]})),
              (1, 1 if dotted else 0, (), (E[f0],)),
              (1, 0, (), (E[f1],))]
    r = Record("C2d" if dotted else "C2", K, K2, dmap, facets, [(0, 1, 2)], 0, 2, 0)
    return K2, r, dmap, [v0, v1]


def rec_triangle(K, f):
    f0, f1, f2 = f
    vs = [f0 // 3, f1 // 3, f2 // 3]
    assert len(set(vs)) == 3
    l = [sigma(x) for x in f]
    K2, dmap, _ = rebuild(K, vs, [(l[0], l[2], l[1])], [])
    s = K.V - 3
    y = 3 * s
    slot = {0: y + 0, 2: y + 1, 1: y + 2}
    E = K.eidx
    facets = []
    for k in range(3):                                   # A_k
        facets.append((1, 0, (K2.eidx[slot[k]],), (E[l[k]],)))
    for k in range(3):                                   # T_k
        facets.append((1, 0, (), (E[f[k]],)))
    seams = [(0, 1, 2)] + [(k, 3 + k, 3 + (k - 1) % 3) for k in range(3)]
    r = Record("C3", K, K2, dmap, facets, seams, 1, 3, 1)
    return K2, r, dmap, vs


def rec_square(K, f, which):
    vs = [x // 3 for x in f]
    assert len(set(vs)) == 4
    l = [sigma(x) for x in f]
    E = K.eidx
    if which == "a":
        J = [(l[0], l[1]), (l[2], l[3])]
        pairs = [(0, 1), (2, 3)]
        halves = [0, 2]           # I01 under f0, I23 under f2
        strip = [1, 3]
    else:
        J = [(l[1], l[2]), (l[3], l[0])]
        pairs = [(1, 2), (3, 0)]
        halves = [1, 3]
        strip = [2, 0]
    K2, dmap, ji = rebuild(K, vs, [], J)
    facets = []
    for k, (p, q) in enumerate(pairs):                   # S sheets
        facets.append((sheet(K2, ji[k]), 0, (ji[k],), tuple(sorted({E[l[p]], E[l[q]]}))))
    for h in halves:                                     # I half-disks
        facets.append((1, 0, (), (E[f[h]],)))
    facets.append((1, 0, (), tuple(sorted({E[f[strip[0]]], E[f[strip[1]]]}))))
    seams = [(0, 2, 4), (1, 3, 4)]
    r = Record("C4" + which, K, K2, dmap, facets, seams, 0, 4, 0)
    return K2, r, dmap, vs


def edge_site(K, du):
    assert K.alpha[du] > du
    dw = K.alpha[du]
    xu, yu = sigma(du), sigma(sigma(du))
    xw, yw = sigma(dw), sigma(sigma(dw))
    return du, dw, xu, yu, xw, yw


def zip_precondition(K, du):
    du, dw, xu, yu, xw, yw = edge_site(K, du)
    legs = {K.eidx[x] for x in (xu, yu, xw, yw)}
    return len(legs) == 4 and K.eidx[du] not in legs


def rec_zip(K, du):
    du, dw, xu, yu, xw, yw = edge_site(K, du)
    assert zip_precondition(K, du)
    u, w = du // 3, dw // 3
    K2, dmap, ji = rebuild(K, [u, w], [], [(xu, yw), (yu, xw)])
    E = K.eidx
    facets = [(1, 0, (ji[0],), (E[xu], E[yw])),
              (1, 0, (ji[1],), (E[yu], E[xw])),
              (1, 0, (), (E[du],))]
    r = Record("zip", K, K2, dmap, facets, [(0, 1, 2)], 0, 2, 0)
    return K2, r, dmap, [u, w], ji


def rec_ih(K, du):
    du, dw, xu, yu, xw, yw = edge_site(K, du)
    assert zip_precondition(K, du)
    u, w = du // 3, dw // 3
    K2, dmap, _ = rebuild(K, [u, w], [("iota", yw, xu), ("iota", yu, xw)], [])
    s = K.V - 2
    t, b = s, s + 1
    E, E2 = K.eidx, K2.eidx
    facets = [(1, 0, (E2[3 * t + 1],), (E[yw],)),       # P1
              (1, 0, (E2[3 * t + 2],), (E[xu],)),       # P2
              (1, 0, (E2[3 * b + 1],), (E[yu],)),       # P3
              (1, 0, (E2[3 * b + 2],), (E[xw],)),       # P4
              (1, 0, (E2[3 * t],), ()),                 # B
              (1, 0, (), (E[du],))]                     # Tf
    seams = [(4, 0, 1), (4, 2, 3), (5, 1, 2), (5, 3, 0)]
    r = Record("ih", K, K2, dmap, facets, seams, 1, 2, 2)
    return K2, r, dmap, [u, w]


def rec_unzip(K, f, i, j):
    assert 0 <= i < j < len(f)
    fi, fj = f[i], f[j]
    a = K.alpha
    afi, afj = a[fi], a[fj]
    V = K.V
    t, b = V, V + 1
    tS, tR, tL = 3 * t, 3 * t + 1, 3 * t + 2
    bN, bL, bR = 3 * b, 3 * b + 1, 3 * b + 2
    a2 = list(a) + [None] * 6
    for p, q in ((tS, bN), (tL, afi), (tR, fj), (bL, fi), (bR, afj)):
        a2[p] = q
        a2[q] = p
    K2 = Web(a2, K.m)
    dmap = {d: d for d in range(3 * V)}
    E, E2 = K.eidx, K2.eidx
    facets = [(1, 0, tuple(sorted({E2[bL], E2[tL]})), (E[fi],)),
              (1, 0, tuple(sorted({E2[tR], E2[bR]})), (E[fj],)),
              (1, 0, (E2[tS],), ())]
    r = Record("unzip", K, K2, dmap, facets, [(0, 1, 2)], 0, 0, 2)
    return K2, r, dmap


def rec_saddle(K, f, i, j):
    assert 0 <= i < j < len(f)
    fi, fj = f[i], f[j]
    a = K.alpha
    afi, afj = a[fi], a[fj]
    a2 = list(a)
    a2[fi], a2[afj] = afj, fi
    a2[fj], a2[afi] = afi, fj
    K2 = Web(a2, K.m)
    dmap = {d: d for d in range(3 * K.V)}
    E, E2 = K.eidx, K2.eidx
    facets = [(1, 0, tuple(sorted({E2[fi], E2[fj]})), tuple(sorted({E[fi], E[fj]})))]
    r = Record("saddle", K, K2, dmap, facets, [], 0, 0, 0)
    return K2, r, dmap


# ---------------------------------------------------------------- generated lists
class Gen:
    """A list of half-foams with boundary K, stored column-wise over a
    subset S of Tait(K): cols[k] = (lo, hi) for S[k]."""
    __slots__ = ("n", "degs", "chains", "cols")

    def __init__(self, n, degs, chains, cols):
        self.n, self.degs, self.chains, self.cols = n, degs, chains, cols


def gen_empty(nS):
    return Gen(0, [], [], [(0, 0)] * nS)


def compose(rec, G, tcols):
    """C o G.  tcols from rec.transfer."""
    cols = []
    gc = G.cols
    for entries in tcols:
        lo = hi = 0
        for k, code in entries:
            a, b = gc[k]
            if code == 1:
                lo ^= a
                hi ^= b
            elif code == 2:
                lo ^= b
                hi ^= a ^ b
            else:
                lo ^= a ^ b
                hi ^= a
        cols.append((lo, hi))
    d = rec.deg
    return Gen(G.n, [x + d for x in G.degs],
               [(rec.label,) + ch for ch in G.chains], cols)


def concat(gs, nS):
    n = 0
    degs, chains = [], []
    cols = [(0, 0)] * nS
    for G in gs:
        if G.n == 0:
            continue
        sh = n
        cols = [(lo | (a << sh), hi | (b << sh)) for (lo, hi), (a, b) in zip(cols, G.cols)]
        n += G.n
        degs.extend(G.degs)
        chains.extend(G.chains)
    return Gen(n, degs, chains, cols)


class Fail(Exception):
    pass


class GenStats:
    def __init__(self):
        self.nodes = 0
        self.checked = 0
        self.ev = {}


def boozer_degenerate(K, f):
    """Amendment 1, A3: would Boozer's program abort on this face?"""
    a = K.alpha
    L = len(f)
    legs = [sigma(x) for x in f]
    vs = [x // 3 for x in f] + [a[l] // 3 for l in legs]
    es = [K.eidx[x] for x in f] + [K.eidx[l] for l in legs]
    if L == 2:
        comp = components(K)
        c = comp[f[0] // 3]
        if sum(1 for v in range(K.V) if comp[v] == c) == 2:
            return False                        # a theta component
        return len(set(vs)) != 4 or len(set(es)) != 4
    if L == 3:
        return len(set(es)) != 6
    return len(set(es)) != 8 or len(set(vs)) != 8


def _sub(K, K2, Sp, strict, markers, D, dmap, stats, check):
    """Recursive GEN call on K2 after a web change K -> K2 with deleted
    vertices D; counts A3 events; a lost marker is a FAIL of this branch."""
    ev = stats.ev if stats is not None else None
    if K2.m > K.m:
        # a bigon removed from a theta component (Boozer-legal, A5) or other
        comp = components(K)
        cs = {comp[v] for v in D}
        theta = len(D) == 2 and len(cs) == 1 and \
            sum(1 for v in range(K.V) if comp[v] in cs) == 2
        count_event(ev, "extra_circle_theta" if theta else "extra_circle_other", K2.m - K.m)
    if K2.V and n_components(K2) > (n_components(K) if K.V else 0):
        count_event(ev, "component_split")
    try:
        mk2 = update_markers(K, K2, markers, D, dmap, ev)
    except MarkerLost:
        if strict:
            raise Fail()
        return gen_empty(len(Sp))
    return gen_or_empty(K2, Sp, strict, mk2, stats, check)


def gen(K, S, strict, markers, stats=None, check=False):
    """GEN of section 6.1 in Mode T.  S: list of Tait colourings of K whose
    columns are wanted.  strict: STRICT (True) or PARTIAL semantics.
    markers: tuple of outer-face darts (Amendment 1, A4) or None.  Raises
    Fail (STRICT) or returns an empty Gen (PARTIAL) on failure."""
    ev = None
    if stats is not None:
        stats.nodes += 1
        ev = stats.ev
    if check:
        for t in S:
            assert is_tait(K, t), "derived colouring is not a Tait colouring"
        if stats is not None:
            stats.checked += len(S)
    nS = len(S)
    # 1. empty web
    if K.V == 0 and K.m == 0:
        return Gen(1, [0], [()], [(1, 0)] * nS)
    # 2. circle
    if K.m > 0:
        parts = []
        sub = None
        for delta in range(3):
            K2, r, dmap = rec_disk(K, delta)
            Sp, tc = r.transfer(S)
            if sub is None:
                sub = (Sp, _sub(K, K2, Sp, strict, markers, [], dmap, stats, check))
            assert sub[0] == Sp
            parts.append(compose(r, sub[1], tc))
        return concat(parts, nS)
    # 3. bridge
    if K.has_bridge():
        count_event(ev, "bridge_fail")
        raise Fail()
    # 4. choose a face
    excl = set(K.face_of[mk] for mk in markers) if markers else set()
    if markers:
        comp = components(K)
        assert len({comp[mk // 3] for mk in markers}) == len(markers)
    chosen = None
    for L in (2, 3, 4):
        for fi, f in enumerate(K.faces):
            if fi not in excl and len(f) == L:
                chosen = f
                break
        if chosen is not None:
            break
    if chosen is None:
        count_event(ev, "no_eligible_face_fail")
        raise Fail()
    f = chosen
    L = len(f)
    if boozer_degenerate(K, f):
        count_event(ev, "boozer_degenerate_%s" % {2: "bigon", 3: "triangle", 4: "square"}[L])
    if L == 2:
        parts = []
        sub = None
        for dotted in (False, True):
            K2, r, dmap, D = rec_bigon(K, f, dotted)
            Sp, tc = r.transfer(S)
            if sub is None:
                sub = (Sp, _sub(K, K2, Sp, strict, markers, D, dmap, stats, check))
            assert sub[0] == Sp
            parts.append(compose(r, sub[1], tc))
        return concat(parts, nS)
    if L == 3:
        K2, r, dmap, D = rec_triangle(K, f)
        if r.merged:
            count_event(ev, "degenerate_triangle_merge")
        Sp, tc = r.transfer(S)
        G = _sub(K, K2, Sp, strict, markers, D, dmap, stats, check)
        return compose(r, G, tc)
    parts = []
    for which in ("a", "b"):
        K2, r, dmap, D = rec_square(K, f, which)
        if r.merged:
            count_event(ev, "degenerate_square_merge")
        Sp, tc = r.transfer(S)
        G = _sub(K, K2, Sp, strict, markers, D, dmap, stats, check)
        parts.append(compose(r, G, tc))
    return concat(parts, nS)


def gen_or_empty(K, S, strict, markers, stats, check):
    """Recursive call: STRICT propagates Fail, PARTIAL turns it into []."""
    if strict:
        return gen(K, S, strict, markers, stats, check)
    try:
        return gen(K, S, strict, markers, stats, check)
    except Fail:
        return gen_empty(len(S))


def gen_top(K, S, strict, markers, stats=None, check=False):
    """GEN at a site: failure (either semantics) contributes nothing."""
    try:
        return gen(K, S, strict, markers, stats, check)
    except Fail:
        return gen_empty(len(S))


# ---------------------------------------------------------------- output helpers
_PAIRCODE = {("0", "0"): "0", ("1", "0"): "1", ("0", "1"): "2", ("1", "1"): "3"}


def gen_rows_hex(G):
    """a-vectors of G as strings of codes (one char per column), rows 0..n-1."""
    n = G.n
    if n == 0:
        return []
    colstrs = []
    fmt = "0%db" % n
    for lo, hi in G.cols:
        ls = format(lo, fmt)[::-1]
        hs = format(hi, fmt)[::-1]
        colstrs.append("".join([_PAIRCODE[p] for p in zip(ls, hs)]))
    if not colstrs:
        return [""] * n
    return ["".join(chars) for chars in zip(*colstrs)]


_LO = str.maketrans("0123", "0101")
_HI = str.maketrans("0123", "0011")


def hex_to_packed(s):
    """code string (position t = Tait index t) -> (lo, hi) with bit t."""
    if not s:
        return 0, 0
    return int(s.translate(_LO)[::-1], 2), int(s.translate(_HI)[::-1], 2)
