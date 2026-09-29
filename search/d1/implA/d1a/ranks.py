"""Rank computations (SPEC Sec. 7): l, l_q, prefix ranks beta_n, r, r_q."""

from .gf4 import Echelon, PairRank, pairing_rank


class GradedRanks:
    """Incremental l_d = rank(B_d B_{-d}^T) for all degrees, with prefix beta_n."""

    def __init__(self):
        self.E = {}          # degree -> Echelon (membership, basis of U_d)
        self.S = {}          # degree d -> PairRank(rows U_d, cols U_{-d})
        self.n = 0
        self.beta = 0
        self.changes = []

    def _S(self, d):
        s = self.S.get(d)
        if s is None:
            s = PairRank()
            self.S[d] = s
            # columns = existing basis of U_{-d}
            Em = self.E.get(-d)
            if Em is not None:
                for w in Em.rows:
                    s.add_col(w)
            # rows = existing basis of U_d (none when created before U_d grows)
            Ed = self.E.get(d)
            if Ed is not None and d != 0:
                for u in Ed.rows:
                    s.add_row(u)
        return s

    def add(self, a, d):
        self.n += 1
        Ed = self.E.get(d)
        if Ed is None:
            Ed = Echelon()
            self.E[d] = Ed
        if Ed.reduce(a)[1] < 0:
            return
        # make sure both pairing structures exist (built from the bases
        # *before* a is inserted), then insert a
        self._S(d)
        self._S(-d)
        Ed.add(a)
        if d == 0:
            s = self._S(0)
            s.add_col(a)
            s.add_row(a)
        else:
            s = self._S(d)
            s.add_row(a)
            t = self._S(-d)
            t.add_col(a)
            if s.rank != t.rank:
                raise AssertionError("l_d != l_-d")
        beta = sum(s.rank for s in self.S.values())
        if beta != self.beta:
            self.beta = beta
            self.changes.append([self.n, beta])

    def ell_q(self):
        out = {}
        for d, s in self.S.items():
            if s.rank:
                out[d] = s.rank
        for d in out:
            if out.get(-d) != out[d]:
                raise AssertionError("l_d != l_-d")
        return dict(sorted(out.items()))

    def recheck(self):
        """Recompute every l_d from scratch with the bases (not incremental)."""
        out = {}
        for d, Ed in self.E.items():
            Em = self.E.get(-d)
            if Em is None:
                continue
            r = pairing_rank(Ed.rows, Em.rows, assert_F=True)
            if r:
                out[d] = r
        return dict(sorted(out.items()))


def span_basis(E_by_deg, degs):
    E = Echelon()
    for d in degs:
        for v in E_by_deg[d].rows:
            E.add(v)
    return E.rows


def r_and_rq(E_by_deg):
    """SPEC 7.3: r = rank of the full pairing; r_q from h(k) = rank of the
    pairing between span{a_i : d_i <= k, d_i = k mod 6} and
    span{a_j : d_j >= -k, d_j = -k mod 6}; g(k) = h(k) - h(k-6)."""
    degs = sorted(E_by_deg)
    allrows = span_basis(E_by_deg, degs)
    r = pairing_rank(allrows, allrows, assert_F=True)
    if not degs:
        return 0, {}
    lo = min(degs)
    hi = max(max(degs), -lo)
    cache = {}

    def h(k):
        if k in cache:
            return cache[k]
        I = [d for d in degs if d <= k and (d - k) % 6 == 0]
        J = [d for d in degs if d >= -k and (d + k) % 6 == 0]
        if not I or not J:
            v = 0
        else:
            v = pairing_rank(span_basis(E_by_deg, I), span_basis(E_by_deg, J), assert_F=True)
        cache[k] = v
        return v

    rq = {}
    total = 0
    for k in range(lo, hi + 1):
        g = h(k) - h(k - 6)
        if g < 0:
            raise AssertionError("g(k) < 0")
        if g:
            rq[k] = g
            total += g
    # h is constant above hi: check that no generator is missed
    for k in range(hi + 1, hi + 7):
        if h(k) != h(k - 6):
            raise AssertionError("h not constant above the range")
    if total != r:
        raise AssertionError("sum g(k) = %d != r = %d" % (total, r))
    return r, rq
