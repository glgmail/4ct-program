"""Phase 2b (SPEC Amendment 2, A2.4): SITES, outcomes, the path tree.

GEN_STRICT is represented as a tree of reductions (Node) so that the degree
of every leaf is known without building foams, and foams are composed only
for the leaves that are retained (with memoisation inside one tree).
The leaf order is exactly SPEC 6.1's GEN order (checked against gen.GEN in
the controls).
"""

from . import records as R
from .foam import EMPTY, compose

OUTCOMES = ("precond", "bridge", "irreducible", "reducible")
MOVES = ("zip", "unzip", "saddle", "ih")


class Node:
    __slots__ = ("branches", "degs", "memo", "recs")

    def __init__(self, branches, degs):
        self.branches = branches      # None for the empty web, else [(op, labels, child)]
        self.degs = degs              # degrees of the leaves, in GEN order
        self.memo = None
        self.recs = None


def gentree(K):
    """GEN_STRICT(K) as a tree, or None if it fails (SPEC 6.1, STRICT, all
    faces eligible, no marker)."""
    if K.V == 0 and K.m == 0:
        return Node(None, [0])
    if K.m > 0:
        op = R.op_disk(K)
        ch = gentree(op.Kp)
        if ch is None:
            return None
        branches = [(op, ("C1", "C1d", "C1dd"), ch)]
    else:
        if K.has_bridge():
            return None
        face = None
        faces = K.faces()
        for L in (2, 3, 4):
            for f in faces:
                if len(f) == L:
                    face = f
                    break
            if face is not None:
                break
        if face is None:
            return None
        L = len(face)
        if L == 2:
            cand = [(R.op_bigon(K, face), ("C2", "C2d"))]
        elif L == 3:
            cand = [(R.op_triangle(K, face), ("C3",))]
        else:
            cand = [(R.op_square(K, face, "a"), ("C4a",)),
                    (R.op_square(K, face, "b"), ("C4b",))]
        branches = []
        for op, labs in cand:
            ch = gentree(op.Kp)
            if ch is None:
                return None
            branches.append((op, labs, ch))
    degs = []
    for op, labs, ch in branches:
        for lab in labs:
            dg = R.DEG[lab]
            cd = ch.degs
            degs.extend([d + dg for d in cd])
    return Node(branches, degs)


def leaf(node, k):
    """(chain tuple, foam) of leaf k of node (0-based), memoised."""
    if node.branches is None:
        return (), EMPTY
    m = node.memo
    if m is None:
        m = node.memo = {}
        node.recs = {}
    r = m.get(k)
    if r is not None:
        return r
    kk = k
    for bi, (op, labs, ch) in enumerate(node.branches):
        n = len(ch.degs)
        blk = n * len(labs)
        if kk < blk:
            lab = labs[kk // n]
            sub = kk % n
            break
        kk -= blk
    else:
        raise IndexError("leaf index out of range")
    key = (bi, lab)
    rec = node.recs.get(key)
    if rec is None:
        rec = node.recs[key] = op.make(lab)
    cch, cf = leaf(ch, sub)
    r = ((lab,) + cch, compose(rec, cf))
    m[k] = r
    return r


def leaf_chain(node, k):
    out = []
    while node.branches is not None:
        kk = k
        for op, labs, ch in node.branches:
            n = len(ch.degs)
            blk = n * len(labs)
            if kk < blk:
                out.append(labs[kk // n])
                k = kk % n
                node = ch
                break
            kk -= blk
    return tuple(out)


def precond_fails(K, e):
    du = e
    dw = K.alpha[e]
    s = R.sigma
    E = K.ekey
    legs = [E(s(du)), E(s(s(du))), E(s(dw)), E(s(s(dw)))]
    return len(set(legs)) != 4 or E(du) in legs


def sites(K):
    """SITES(K) (A2.4): Zip, Unzip (all pairs, adjacent included), Saddle, IH."""
    edges = K.edge_ids()
    faces = K.faces()
    pairs = [(f[0], i, j) for f in faces for i in range(len(f)) for j in range(i + 1, len(f))]
    out = [("zip", e) for e in edges]
    out += [("unzip", a, i, j) for (a, i, j) in pairs]
    out += [("saddle", a, i, j) for (a, i, j) in pairs]
    out += [("ih", e) for e in edges]
    return out


def make_op(K, site, fbm):
    kind = site[0]
    if kind == "zip":
        return R.op_zip(K, site[1])
    if kind == "ih":
        return R.op_ih(K, site[1])
    f = fbm[site[1]]
    fi, fj = f[site[2]], f[site[3]]
    if K.ekey(fi) == K.ekey(fj):
        raise AssertionError("Unzip/Saddle pair on one edge in a bridgeless web")
    if kind == "unzip":
        return R.op_unzip(K, f, site[2], site[3])
    return R.op_saddle(K, f, site[2], site[3])


def outcome(K, site, fbm):
    """(outcome, op, node) with node = gentree(K') when REDUCIBLE."""
    if site[0] in ("zip", "ih") and precond_fails(K, site[1]):
        return "precond", None, None
    op = make_op(K, site, fbm)
    Kp = op.Kp
    if Kp.has_bridge():
        return "bridge", op, None
    node = gentree(Kp)
    if node is None:
        return "irreducible", op, None
    return "reducible", op, node


class StopWalk(Exception):
    pass


class Stats:
    def __init__(self, nlevels):
        self.sites = {str(l): {mv: {oc: 0 for oc in OUTCOMES} for mv in MOVES}
                      for l in range(1, nlevels + 1)}
        self.expanded = {}
        self.leaves = {}
        self.retained = 0

    def as_dict(self):
        return {"sites": self.sites, "expanded_nodes": dict(self.expanded),
                "leaves_by_degree": {str(k): v for k, v in sorted(self.leaves.items()) if v},
                "N_leaves": sum(self.leaves.values()), "N_retained": self.retained}


def walk(K0, rules, first, keep, stats, emit=None, per_first=None):
    """Depth-first path enumeration (A2.4).

    rules: list over levels 1..L; rules[l-1] is "reducible" or "irreducible"
           (the outcome that is expanded) for l < L and "emit" for l = L.
    first: None, or a single level-1 site (T3s).
    keep:  predicate on degree (retained leaves).
    emit:  None (count only) or callback(moves, chain, deg, foam); it may raise
           StopWalk.
    per_first: optional dict site -> [sites-by-outcome dict, retained count]
    """
    L = len(rules)

    def rec(K, lvl, moves, ops, dsum):
        key = str(lvl - 1)
        stats.expanded[key] = stats.expanded.get(key, 0) + 1
        fbm = {f[0]: f for f in K.faces()}
        slist = [first] if (lvl == 1 and first is not None) else sites(K)
        rule = rules[lvl - 1]
        for site in slist:
            oc, op, node = outcome(K, site, fbm)
            stats.sites[str(lvl)][site[0]][oc] += 1
            if per_first is not None and lvl == 2:
                per_first[tuple(moves[0])][0][oc] += 1
            lab = list(site)
            if rule == "emit":
                if oc != "reducible":
                    continue
                base = dsum + R.DEG[site[0]]
                lv = stats.leaves
                mv = moves + [lab]
                allops = ops + [(op, site[0])]
                recs = None
                for k, d in enumerate(node.degs):
                    dd = base + d
                    lv[dd] = lv.get(dd, 0) + 1
                    if keep(dd):
                        stats.retained += 1
                        if per_first is not None and moves:
                            per_first[tuple(moves[0])][1] += 1
                        if emit is not None:
                            chain, H = leaf(node, k)
                            if recs is None:
                                recs = [o.make(kind) for (o, kind) in allops]
                            for r in reversed(recs):
                                H = compose(r, H)
                            emit(mv, chain, dd, H)
            elif oc == rule:
                if per_first is not None and lvl == 1:
                    per_first.setdefault(tuple(lab), [{o: 0 for o in OUTCOMES}, 0])
                rec(op.Kp, lvl + 1, moves + [lab], ops + [(op, site[0])],
                    dsum + R.DEG[site[0]])

    rec(K0, 1, [], [], 0)
    return stats
