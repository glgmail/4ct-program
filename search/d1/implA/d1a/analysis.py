"""Glue between generation, a-vectors and ranks; shared by controls and runs."""

from . import gf4
from .foam import avec, degree, glue, eval_closed, tait_columns
from .ranks import GradedRanks, r_and_rq


class TargetWeb:
    """A target web with its Tait colourings in canonical order."""

    def __init__(self, K):
        self.K = K
        self.keys = K.all_keys()
        self.taits = K.tait_colourings()
        self.T = len(self.taits)
        self.tcol = tait_columns(self.taits, self.keys)

    def avec(self, H):
        return avec(H, self.tcol, self.T)

    def hexa(self, a):
        return gf4.to_hex(a, self.T)

    def check_degree(self, H, deg):
        d2 = degree(H, self.K.V)
        if d2 != deg:
            raise AssertionError("degree from facet data %d != table sum %d" % (d2, deg))

    def direct_pair(self, H1, H2):
        chi, dots, seams, nv = glue(H1, H2, self.keys)
        val, cnt = eval_closed(chi, dots, seams, nv)
        return val


def analyse(items):
    """items: iterable of (a, deg).  Returns dict with ell, ell_q, r, r_q,
    beta changes and N_ell."""
    G = GradedRanks()
    for a, d in items:
        G.add(a, d)
    ellq = G.ell_q()
    if G.recheck() != ellq:
        raise AssertionError("incremental l_q differs from recomputation")
    ell = sum(ellq.values())
    assert ell == G.beta
    r, rq = r_and_rq(G.E)
    Nl = None
    for n, b in G.changes:
        if b == ell:
            Nl = n
            break
    if ell == 0:
        Nl = 0
    return {"ell": ell, "ell_q": ellq, "r": r, "r_q": rq,
            "beta_changes": G.changes, "N_ell": Nl}


def sample_pairs(N, count=10000):
    """SPEC 7.5 item 2 (1-based indices)."""
    return [(1 + (7919 * k) % N, 1 + (104729 * k) % N) for k in range(1, count + 1)]


def check_pairs(tw, foams, avecs, degs, pairs):
    """Direct closed-foam value vs a-vector pairing on the given pairs.
    foams/avecs/degs are indexable by 1-based index.  Returns number checked."""
    cache = {}
    n = 0
    for (i, j) in pairs:
        key = (i, j) if i <= j else (j, i)
        if key in cache:
            val = cache[key]
        else:
            val = tw.direct_pair(foams[i], foams[j])
            cache[key] = val
        b = gf4.dot(avecs[i], avecs[j])
        if b > 1:
            raise AssertionError("pairing value not in F at (%d,%d)" % (i, j))
        if b != val:
            raise AssertionError("direct value %d != a-vector pairing %d at (%d,%d)"
                                 % (val, b, i, j))
        s = degs[i] + degs[j]
        if (s < 0 or s % 6) and b:
            raise AssertionError("nonzero pairing in degree %d" % s)
        n += 1
    return n
