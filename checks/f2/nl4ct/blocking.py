"""Reducible configurations in pseudo-configurations, and blocking.

Algorithms A.6.6-A.6.8 (containConf, dartsByDegree, rootedContainConf) and
A.7.1-A.7.2 (blockedByReducibleConfiguration, representativeDegree).

Speed-up (ours; it does not change any answer)
----------------------------------------------
A.6.6 tries every configuration K of the set against every dart f* of the
target whose endpoint degrees equal those of K's special dart f = x->y. We
decide exactly the same pairs, but skip pairs for which Algorithm A.2.1 is
bound to return null, for the following reason.

Walk around y in K from f: f, succ(f), succ^2(f), ... until the successor
is nil or we are back at f (ls darts), and pred(f), pred^2(f), ... until
nil or back at f (lp darts). A.2.1 maps succ^k(f) to succ^k(f*) and
pred^k(f) to pred^k(f*), and returns null if the target pointer is nil where
the source pointer is not (lines 23-24, 28-29). It maps the tail of each of
these darts to the tail of its image, and with ginclude a source vertex with
a single degree must go to a target vertex of exactly that degree. So the
target must show the same sequence of degrees along the same walk from f*,
except at positions whose source tail has a degree range (only the
auxiliary vertex of a cut-vertex extension has one); those positions are
wildcards in the index. We group the configurations by (deg y, deg x, ls,
lp, wildcard positions) and index each group by the sequence; from f* we
compute the sequence for each group and look it up. Every candidate found
this way is then decided by A.2.1 itself, so nothing is decided by the index.
"""
from __future__ import annotations

import itertools

from .pseudo import G_INCLUDE, INF, NIL, homomorphism

CONF_DEG_MAX = 12


WILD = -1  # placeholder at wildcard positions


def _walks(pc, f):
    """(ls, lp, wildcard positions, sequence) for the walk described in the
    module docstring."""
    head, rev, succ, pred, lo, hi = (pc.head, pc.rev, pc.succ, pc.pred,
                                     pc.lo, pc.hi)
    seq = []
    wild = []

    def add(t):
        if lo[t] == hi[t]:
            seq.append(lo[t])
        else:
            wild.append(len(seq))
            seq.append(WILD)

    e = f
    ls = 0
    while True:
        add(head[rev[e]])
        ls += 1
        e = succ[e]
        if e == NIL or e == f:
            break
    lp = 0
    if e != f:  # not cyclic: walk backwards too
        e = pred[f]
        while e != NIL and e != f:
            add(head[rev[e]])
            lp += 1
            e = pred[e]
    return ls, lp, tuple(wild), tuple(seq)


def _target_seq(pc, deg, fs, ls, lp, wild):
    head, rev, succ, pred = pc.head, pc.rev, pc.succ, pc.pred
    seq = []
    e = fs
    for k in range(ls):
        if k:
            e = succ[e]
            if e == NIL:
                return None
        seq.append(deg[head[rev[e]]])
    e = fs
    for _ in range(lp):
        e = pred[e]
        if e == NIL:
            return None
        seq.append(deg[head[rev[e]]])
    for i in wild:
        seq[i] = WILD
    return tuple(seq)


class ConfIndex:
    """The set K of configurations, prepared for containConf."""

    def __init__(self, confs):
        self.confs = confs
        # (dy, dx) -> {(ls, lp, wild): {sequence: [conf]}}
        self.groups = {}
        for c in confs:
            pc, f = c.pc, c.dart
            y = pc.head[f]
            x = pc.head[pc.rev[f]]
            assert pc.lo[y] == pc.hi[y] and pc.lo[x] == pc.hi[x]
            key = (pc.lo[y], pc.lo[x])
            ls, lp, wild, seq = _walks(pc, f)
            g = self.groups.setdefault(key, {}).setdefault((ls, lp, wild), {})
            g.setdefault(seq, []).append(c)

    def n_groups(self):
        return sum(len(g) for g in self.groups.values())

    def contain(self, pc, deg, centre):
        return contain_conf(pc, deg, centre, self)


class LiteralConfs:
    """The set K for a literal transcription of A.6.6 (no index): every
    configuration against every dart with the right endpoint degrees. Used
    to cross-check ConfIndex (run.py --literal)."""

    def __init__(self, confs):
        self.confs = confs

    def contain(self, pc, deg, centre):
        target = _SingleDegreeView(pc, deg)
        dbd = darts_by_degree(pc, deg)  # A.6.6 line 1
        for c in self.confs:  # line 2
            cpc, f = c.pc, c.dart
            y = cpc.head[f]
            x = cpc.head[cpc.rev[f]]
            dy, dx = cpc.lo[y], cpc.lo[x]
            for fs in dbd.get((dy, dx), ()):  # line 7
                if dy > 8 and pc.head[fs] != centre:  # lines 8-10
                    continue
                if homomorphism(cpc, f, target, fs, G_INCLUDE) is not None:
                    return c, fs  # lines 11-13
        return None


def darts_by_degree(pc, deg):
    """Algorithm A.6.7 (deg is the single degree of each vertex)."""
    out = {}
    head, rev = pc.head, pc.rev
    for e in range(len(head)):
        dy = deg[head[e]]
        dx = deg[head[rev[e]]]
        if dy > CONF_DEG_MAX or dx > CONF_DEG_MAX:
            continue
        out.setdefault((dy, dx), []).append(e)
    return out


def contain_conf(pc, deg, centre, index):
    """Algorithm A.6.6 on the single-degree pseudo-configuration (pc, deg).

    Returns the first (conf, f*) found, or None.
    """
    target = _SingleDegreeView(pc, deg)
    dbd = darts_by_degree(pc, deg)
    head = pc.head
    for key in sorted(dbd):
        dy = key[0]
        groups = index.groups.get(key)
        if not groups:
            continue
        for fs in dbd[key]:
            if dy > 8 and head[fs] != centre:
                continue
            for (ls, lp, wild), table in groups.items():
                seq = _target_seq(pc, deg, fs, ls, lp, wild)
                if seq is None:
                    continue
                for c in table.get(seq, ()):
                    if homomorphism(c.pc, c.dart, target, fs,
                                    G_INCLUDE) is not None:
                        return c, fs
    return None


class _SingleDegreeView:
    """A pseudo-configuration whose ranges are the given single degrees."""

    __slots__ = ("nv", "lo", "hi", "head", "rev", "succ", "pred")

    def __init__(self, pc, deg):
        self.nv = pc.nv
        self.lo = deg
        self.hi = deg
        self.head = pc.head
        self.rev = pc.rev
        self.succ = pc.succ
        self.pred = pc.pred


def representative_degrees(pc, centre):
    """Algorithm A.7.2: the list of single-degree functions to check."""
    choices = []
    for v in range(pc.nv):
        lo, hi = pc.lo[v], pc.hi[v]
        if v == centre and hi > CONF_DEG_MAX:
            choices.append((hi,))
        elif v != centre and hi > 8:
            choices.append((hi,))
        else:
            choices.append(tuple(range(lo, hi + 1)))
    return choices


def blocked(pc, centre, index):
    """Algorithm A.7.1 blockedByReducibleConfiguration."""
    choices = representative_degrees(pc, centre)
    for deg in itertools.product(*choices):
        if index.contain(pc, list(deg), centre) is None:
            return False
    return True


def is_blocked_witness(pc, centre, index):
    """Like `blocked`, but return the witnesses (for reports)."""
    choices = representative_degrees(pc, centre)
    wits = []
    for deg in itertools.product(*choices):
        w = index.contain(pc, list(deg), centre)
        if w is None:
            return None
        wits.append(w)
    return wits


assert INF > CONF_DEG_MAX
