"""Free combination of discharging rules: Algorithms A.8.1 and A.8.2.

Lemma A.1 is combine_rules(R, no configurations); Lemma A.2 is
combine_rules(R, Ds).
"""
from __future__ import annotations

from .blocking import blocked
from .inputs import Rule
from .pseudo import INF, NIL, PC, disjoint_union, free_hom_configuration


def neutral_rule():
    """R0 of section 9.4.1 / A.8.2 line 2: s0 -> t0, ranges [1, INF]."""
    pc = PC(2, [1, 1], [INF, INF], [1, 0], [1, 0], [NIL, NIL], [NIL, NIL])
    return Rule(pc, 0, 0, 0, "R0")


def add_rule_to_combination(comb, rule, bit, index, stats=None):
    """Algorithm A.8.1. `index` is a ConfIndex, or None for K = empty."""
    u = disjoint_union(comb.pc, rule.pc)
    pairs = [(comb.dart, rule.dart + len(comb.pc.head))]
    results = free_hom_configuration(u, pairs)
    out = []
    for z, (vmap, dmap) in results:
        e = dmap[comb.dart]
        if index is not None:
            if stats is not None:
                stats["blocking_checks"] += 1
            if blocked(z, z.head[e], index):
                continue
        out.append(Rule(z, e, comb.charge + rule.charge, comb.mask | bit))
    return out


def combine_rules(rules, index, order=None, progress=None):
    """Algorithm A.8.2 combineRules(R, K). Returns (list of rules, stats).

    Rules are added in `order` (indices into `rules`; default: as given).
    The flag of rule i is bit i, whatever the order.
    """
    stats = {"calls": 0, "blocking_checks": 0}
    if order is None:
        order = range(len(rules))
    combos = [neutral_rule()]
    for step, i in enumerate(order):
        rule = rules[i]
        new = list(combos)
        for c in combos:
            stats["calls"] += 1
            new.extend(add_rule_to_combination(c, rule, 1 << i, index, stats))
        combos = new
        if progress:
            progress(step, rule, len(combos))
    return combos, stats
