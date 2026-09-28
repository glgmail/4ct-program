"""Free cartwheels with limited degrees and tail ranges (section 11.2,
appendix A.9.1-A.9.7 and A.9.11-A.9.13).

Phase 1 needs enumPossibleBadWheels (A.9.7) for centre degree 7. The later
steps of enumBadCartwheels (fixInRules, fixOutRules, A.9.8-A.9.21) are in
`badcartwheels.py`.

Speed-ups (ours; they do not change any answer)
-----------------------------------------------
* amountOfPossibleChargeSend (A.9.4) returns the largest charge among the
  combined rules that do not "never apply". We try the combined rules in
  order of decreasing charge and stop at the first that sometimes applies;
  the maximum is the same.
* Before calling A.2.1 for a rule and a dart e, we test the two degree
  conditions A.2.1 itself tests first (at the head of e and at its tail,
  lines 19 and then 19 again after line 22), using precomputed tables. A
  rule failing them would make A.2.1 return null anyway.
"""
from __future__ import annotations

from .blocking import blocked
from .pseudo import (G_DOMINANT, G_INCLUDE, G_INTERSECT, NIL, PC,
                     from_rotations, homomorphism)

CARTWHEEL_DEGREES = (5, 6, 7, 8, 9)


# ---------------------------------------------------------------------------
# A.9.5 enumWheels, A.9.6 generateCartwheel
# ---------------------------------------------------------------------------
def enum_wheel_degrees(d):
    """Algorithm A.9.5 without the cartwheel construction: the degree
    arrays of length d over CARTWHEEL_DEGREES that are lexicographically
    smallest among their rotations, in the order A.9.5 generates them."""
    out = []
    degrees = [0] * d

    def rec(i, ilowest):
        if i == d:
            for k in range(1, d):
                if degrees[k:] + degrees[:k] < degrees:
                    return
            out.append(tuple(degrees))
            return
        for j in range(ilowest, 5):
            degrees[i] = CARTWHEEL_DEGREES[j]
            rec(i + 1, ilowest)

    for j in range(5):
        degrees[0] = CARTWHEEL_DEGREES[j]
        rec(1, j)
    return out


class Cartwheel:
    """A free cartwheel with limited degrees and tail ranges.

    pc: the pseudo-configuration (vertex 0 is the centre v, 1..d its
    neighbours v_1..v_d in clockwise order, the rest second neighbours).
    into[j]: the dart v_j -> v; out[j]: the dart v -> v_j (j = 1..d; index
    0 unused).
    """

    __slots__ = ("pc", "d", "into", "out")

    def __init__(self, pc, d, into, out):
        self.pc = pc
        self.d = d
        self.into = into
        self.out = out

    def with_pc(self, pc):
        return Cartwheel(pc, self.d, self.into, self.out)


def generate_cartwheel(d, degrees):
    """Algorithm A.9.6 generateCartwheel(d, degrees)."""
    rotations = [list(range(1, d + 1))]
    for i in range(1, d + 1):
        i1 = i + 1 if i < d else 1
        i2 = i - 1 if i > 1 else d
        rotations.append([i1, 0, i2])
    k = d + 1
    for i in range(1, d + 1):
        if degrees[i - 1] == 9:
            continue
        a = degrees[i - 1] - len(rotations[i])
        for _ in range(a):
            ilast = rotations[i][-1]
            rotations.append([i, ilast])
            rotations[i].append(k)
            rotations[ilast] = [k] + rotations[ilast]
            k += 1
        ifirst = rotations[i][0]
        ilast = rotations[i][-1]
        rotations[ifirst].append(ilast)
        rotations[ilast] = [ifirst] + rotations[ilast]
    for i in range(1, k):
        if i > d or degrees[i - 1] == 9:
            rotations[i].append(-1)
    nv, head, rev, succ, pred, darts = from_rotations(rotations)
    lo = [0] * nv
    hi = [0] * nv
    lo[0] = hi[0] = d
    for i in range(1, nv):
        if i <= d:
            lo[i] = hi[i] = degrees[i - 1]
        else:
            lo[i], hi[i] = 5, 9
    pc = PC(nv, lo, hi, head, rev, succ, pred)
    into = [NIL] + [darts[0][j] for j in range(1, d + 1)]
    out = [NIL] + [darts[j][0] for j in range(1, d + 1)]
    return Cartwheel(pc, d, into, out)


# ---------------------------------------------------------------------------
# A.9.1-A.9.4: rules on a dart
# ---------------------------------------------------------------------------
def always_apply(pc, e, rule):
    """Algorithm A.9.1."""
    return homomorphism(rule.pc, rule.dart, pc, e, G_INCLUDE) is not None


def never_apply(pc, e, rule):
    """Algorithm A.9.2."""
    return homomorphism(rule.pc, rule.dart, pc, e, G_INTERSECT) is None


def dominantly_apply(pc, e, rule):
    """Algorithm A.9.15."""
    return homomorphism(rule.pc, rule.dart, pc, e, G_DOMINANT) is not None


class RuleTables:
    """R (the 84 rules) and R*-D, prepared for A.9.3 and A.9.4."""

    def __init__(self, rules, rstar_d, literal=False):
        self.rules = rules
        self.rstar_d = rstar_d
        self.literal = literal
        # combined rules by decreasing charge (stable: ties keep list order)
        self.by_charge = sorted(rstar_d, key=lambda r: -r.charge)

    @staticmethod
    def _ends(rule):
        pc = rule.pc
        t = pc.head[rule.dart]
        s = pc.head[pc.rev[rule.dart]]
        return pc.lo[t], pc.hi[t], pc.lo[s], pc.hi[s]


def amount_of_charge_send_literal(pc, e, rules):
    """Algorithm A.9.3, literally."""
    a = 0
    for rule in rules:
        if always_apply(pc, e, rule):
            a += rule.charge
    return a


def amount_of_possible_charge_send_literal(pc, e, rstar_d):
    """Algorithm A.9.4, literally."""
    a = 0
    for rule in rstar_d:
        if never_apply(pc, e, rule):
            continue
        a = max(a, rule.charge)
    return a


def amount_of_charge_send(pc, e, rules):
    """Algorithm A.9.3: the sum of r(R) over rules R that always apply to e."""
    a = 0
    t = pc.head[e]
    s = pc.head[pc.rev[e]]
    tlo, thi, slo, shi = pc.lo[t], pc.hi[t], pc.lo[s], pc.hi[s]
    for rule in rules:
        rp = rule.pc
        rt = rp.head[rule.dart]
        rs = rp.head[rp.rev[rule.dart]]
        # A.2.1 with ginclude checks these two ranges first
        if not (rp.lo[rt] <= tlo and thi <= rp.hi[rt]):
            continue
        if not (rp.lo[rs] <= slo and shi <= rp.hi[rs]):
            continue
        if always_apply(pc, e, rule):
            a += rule.charge
    return a


def amount_of_possible_charge_send(pc, e, by_charge):
    """Algorithm A.9.4: the largest r* over combined rules in R*-D that do
    not never apply to e (0 if none)."""
    t = pc.head[e]
    s = pc.head[pc.rev[e]]
    tlo, thi, slo, shi = pc.lo[t], pc.hi[t], pc.lo[s], pc.hi[s]
    for rule in by_charge:
        if rule.charge <= 0:
            return 0
        rp = rule.pc
        rt = rp.head[rule.dart]
        rs = rp.head[rp.rev[rule.dart]]
        # A.2.1 with gintersection checks these two ranges first
        if rp.lo[rt] > thi or tlo > rp.hi[rt]:
            continue
        if rp.lo[rs] > shi or slo > rp.hi[rs]:
            continue
        if not never_apply(pc, e, rule):
            return rule.charge
    return 0


# ---------------------------------------------------------------------------
# A.9.11-A.9.13: pruning
# ---------------------------------------------------------------------------
def prune_by_non_associated_rule(cw, fixed, rules):
    """Algorithm A.9.12. fixed[j-1] is the combined rule R*_j for j <= i."""
    for j, rj in enumerate(fixed, start=1):
        e = cw.into[j]
        for idx, rule in enumerate(rules):
            if not (rj.mask >> idx) & 1 and always_apply(cw.pc, e, rule):
                return True
    return False


def upper_bound_of_charge(cw, fixed, tables):
    """Algorithm A.9.13."""
    d = cw.d
    i = len(fixed)
    total = 10 * (6 - d)
    for rj in fixed:
        total += rj.charge
    if tables.literal:
        for j in range(i + 1, d + 1):
            total += amount_of_possible_charge_send_literal(
                cw.pc, cw.into[j], tables.rstar_d)
        for j in range(1, d + 1):
            total -= amount_of_charge_send_literal(cw.pc, cw.out[j],
                                                   tables.rules)
        return total
    for j in range(i + 1, d + 1):
        total += amount_of_possible_charge_send(cw.pc, cw.into[j],
                                                tables.by_charge)
    for j in range(1, d + 1):
        total -= amount_of_charge_send(cw.pc, cw.out[j], tables.rules)
    return total


def prune(cw, fixed, tables, index, stats=None):
    """Algorithm A.9.11. Returns the reason ("rule", "charge", "blocked")
    or None if the cartwheel survives."""
    if prune_by_non_associated_rule(cw, fixed, tables.rules):
        return "rule"
    if upper_bound_of_charge(cw, fixed, tables) < 0:
        return "charge"
    if blocked(cw.pc, 0, index):
        return "blocked"
    return None


# ---------------------------------------------------------------------------
# A.9.7 enumPossibleBadWheels
# ---------------------------------------------------------------------------
def enum_possible_bad_wheels(d, tables, index, degree_arrays=None):
    """Algorithm A.9.7. Returns [(degrees, reason or None)] for every wheel
    of A.9.5; the survivors (reason None) form C^d_0."""
    if degree_arrays is None:
        degree_arrays = enum_wheel_degrees(d)
    out = []
    for degs in degree_arrays:
        cw = generate_cartwheel(d, degs)
        out.append((degs, prune(cw, [], tables, index)))
    return out
