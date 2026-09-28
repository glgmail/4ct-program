"""Reading the input data: discharging rules, reducible configurations, and
our own transcription of X (Figure 12) and T_{7^3} (section 8).

File formats: `input-formats.md` (the excerpt of the upstream format notes
given to this task); see checks/f2/README.md. Conversions: appendix A.5
(fromVRotations) and A.6.1-A.6.5 (cut vertices, ring removal, special dart,
mirror images).
"""
from __future__ import annotations

import json
import os

from .pseudo import INF, NIL, PC, from_rotations, mirror


class Rule:
    """A (possibly combined) discharging rule ((Z, lo, hi), e, r, flags).

    `dart` is the dart s->t (head t, tail s). `mask` is the set of original
    rules combined into it, as a bit mask over the rule list (the flag f of
    appendix A.8). `name` is the file stem for original rules.
    """

    __slots__ = ("pc", "dart", "charge", "mask", "name")

    def __init__(self, pc, dart, charge, mask=0, name=""):
        self.pc = pc
        self.dart = dart
        self.charge = charge
        self.mask = mask
        self.name = name


class Conf:
    """A configuration of Ds with its special dart f = x->y (A.6.4)."""

    __slots__ = ("pc", "dart", "name", "cut", "mirrored")

    def __init__(self, pc, dart, name, cut, mirrored):
        self.pc = pc
        self.dart = dart
        self.name = name
        self.cut = cut        # which extension (0/1) if a cut vertex, else -1
        self.mirrored = mirrored


def _numbers(path):
    with open(path, "r", encoding="ascii") as fh:
        lines = [ln.split() for ln in fh.read().splitlines()]
    return [[int(t) for t in ln] for ln in lines if ln]


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def read_rule(path):
    rows = _numbers(path)
    n, s, t, r = rows[0]
    if len(rows) != n + 1:
        raise ValueError(f"{path}: expected {n} vertex lines")
    rotations = [None] * n
    lo = [0] * n
    hi = [0] * n
    for row in rows[1:]:
        i, dmin, dmax = row[0], row[1], row[2]
        rot = [a - 1 if a != -1 else -1 for a in row[3:]]
        v = i - 1
        if rotations[v] is not None:
            raise ValueError(f"{path}: vertex {i} twice")
        rotations[v] = rot
        lo[v] = dmin
        hi[v] = INF if dmax == 0 else dmax
        if dmin < 5:
            raise ValueError(f"{path}: lower degree {dmin} < 5 (Def. 4.1)")
        if lo[v] > hi[v]:
            raise ValueError(f"{path}: empty range at {i}")
        nb = [a for a in rot if a != -1]
        if -1 not in rot:  # inner vertex: the range is its degree
            if not (lo[v] == hi[v] == len(nb)):
                raise ValueError(f"{path}: inner vertex {i} range/degree")
        elif rot.count(-1) != 1:
            raise ValueError(f"{path}: vertex {i} has two boundary marks")
        elif not len(nb) < lo[v]:
            raise ValueError(f"{path}: boundary vertex {i} not below range")
    nv, head, rev, succ, pred, darts = from_rotations(rotations)
    pc = PC(nv, lo, hi, head, rev, succ, pred)
    e = darts[t - 1].get(s - 1)
    if e is None:
        raise ValueError(f"{path}: s, t not adjacent")
    return Rule(pc, e, r, 0, os.path.splitext(os.path.basename(path))[0])


def read_rules(directory):
    names = sorted(f for f in os.listdir(directory) if f.endswith(".rule"))
    return [read_rule(os.path.join(directory, f)) for f in names]


# ---------------------------------------------------------------------------
# Configurations
# ---------------------------------------------------------------------------
def read_conf_rotations(path):
    """Return (N, R, degrees, rotations) with 0-based vertices.

    Ring vertices are 0..R-1 (clockwise), configuration vertices R..N-1.
    rotations[i] is None for ring vertices (the file does not give them).
    """
    rows = _numbers(path)
    n, r = rows[0]
    if len(rows) != n - r + 1:
        raise ValueError(f"{path}: expected {n - r} vertex lines")
    deg = [0] * n
    rotations = [None] * n
    for row in rows[1:]:
        i, d = row[0], row[1]
        nb = [a - 1 for a in row[2:]]
        v = i - 1
        if not (r <= v < n) or rotations[v] is not None or len(nb) != d:
            raise ValueError(f"{path}: bad line for vertex {i}")
        deg[v] = d
        rotations[v] = nb
    return n, r, deg, rotations


def ring_fan(n, r, rotations, u):
    """Clockwise list of configuration neighbours of ring vertex u.

    Derived from the configuration vertices' rotations with the face rule
    (if q follows p around a, then around q, p follows a): around u, the
    configuration neighbour a is followed by pred_a(u). The fan starts at the
    neighbour a whose successor succ_a(u) is a ring vertex.
    """
    inner = [a for a in range(r, n) if u in rotations[a]]

    def around(a):
        rot = rotations[a]
        k = rot.index(u)
        return rot[k - 1], rot[(k + 1) % len(rot)]  # (pred, succ)

    starts = [a for a in inner if around(a)[1] < r]
    if len(starts) != 1:
        raise ValueError(f"ring vertex {u}: {len(starts)} fan starts")
    fan = [starts[0]]
    while True:
        p = around(fan[-1])[0]
        if p < r:
            break
        fan.append(p)
    if sorted(fan) != sorted(inner):
        raise ValueError(f"ring vertex {u}: fan does not cover neighbours")
    return fan


def find_cut_pairs(n, r, rotations):
    """Algorithm A.6.2."""
    pairs = []
    for i in range(r, n):
        rot = rotations[i]
        ur = set()
        t = 0
        d = len(rot)
        for j in range(d):
            k1 = rot[j]
            if k1 < r:
                ur.add(k1)
            k2 = rot[(j + 1) % d]
            if k1 < r and k2 >= r:  # a ring stretch ends
                t += 1
        if t >= 2 and len(ur) > 2:
            raise ValueError("invalid configuration (Z3)")
        if t == 2 and len(ur) == 2:
            a, b = sorted(ur)
            pairs.append((a, b))
    return pairs


def remove_ring(n, r, deg, rotations, keep):
    """Algorithm A.6.3; keep = the ring vertices not removed.

    Kept ring vertices get the rotation (fan, -1) and the range [d+1, INF].
    """
    old2new = [-1] * n
    k = 0
    for i in range(n):
        if i < r and i not in keep:
            continue
        old2new[i] = k
        k += 1
    rot = []
    lo = []
    hi = []
    for i in range(n):
        if i < r and i not in keep:
            continue
        if i < r:
            src = ring_fan(n, r, rotations, i) + [-1]
        else:
            src = rotations[i]
        new = [old2new[j] if j != -1 else -1 for j in src]
        rot.append(new)
        if i < r:
            d = sum(1 for j in new if j != -1)
            lo.append(d + 1)
            hi.append(INF)
        else:
            lo.append(deg[i])
            hi.append(deg[i])
    nv, head, rev, succ, pred, _ = from_rotations(rot)
    return PC(nv, lo, hi, head, rev, succ, pred)


def maximum_degree_dart(pc):
    """Algorithm A.6.4: the dart x->y with fixed degrees maximizing
    (deg y, deg x) lexicographically; first one in dart order on ties."""
    f = NIL
    best = (0, 0)
    for e in range(len(pc.head)):
        y = pc.head[e]
        x = pc.head[pc.rev[e]]
        if pc.lo[y] != pc.hi[y] or pc.lo[x] != pc.hi[x]:
            continue
        de = (pc.lo[y], pc.lo[x])
        if de > best:
            f = e
            best = de
    return f


def extend_from_cut_vertices(n, r, deg, rotations):
    """Algorithm A.6.1. Returns a list of (PC, special dart, extension)."""
    pairs = find_cut_pairs(n, r, rotations)
    if len(pairs) > 1:
        raise ValueError("more than one cut vertex")
    out = []
    for s in range(1 << len(pairs)):
        keep = set()
        for i, (a, b) in enumerate(pairs):
            keep.add(a if (s >> i) & 1 else b)
        pc = remove_ring(n, r, deg, rotations, keep)
        out.append((pc, maximum_degree_dart(pc), s if pairs else -1))
    return out


def read_ds(directory, with_mirrors=True):
    """The set Ds of appendix A.6: every configuration of D (as files),
    extended at its cut vertex if any, plus all mirror images.

    The single vertices of degree 3 and 4 are not included; see README.
    """
    names = sorted(f for f in os.listdir(directory) if f.endswith(".conf"))
    out = []
    for f in names:
        n, r, deg, rotations = read_conf_rotations(os.path.join(directory, f))
        stem = os.path.splitext(f)[0]
        for pc, dart, cut in extend_from_cut_vertices(n, r, deg, rotations):
            out.append(Conf(pc, dart, stem, cut, False))
            if with_mirrors:
                out.append(Conf(mirror(pc), dart, stem, cut, True))
    return out


# ---------------------------------------------------------------------------
# Our transcriptions: X (Figure 12) and T_{7^3} (section 8)
# ---------------------------------------------------------------------------
def read_special(path):
    """Read checks/f2/data/special-configurations.json.

    Returns {name: (PC, names, centre index or None)}. Rotations are
    clockwise lists of vertex names, "|" marking the boundary gap.
    """
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    out = {}
    for name, spec in doc["configurations"].items():
        names = [v["name"] for v in spec["vertices"]]
        idx = {nm: i for i, nm in enumerate(names)}
        rot = []
        lo = []
        for v in spec["vertices"]:
            rot.append([idx[a] if a != "|" else -1 for a in v["rotation"]])
            lo.append(v["degree"])
        nv, head, rev, succ, pred, _ = from_rotations(rot)
        pc = PC(nv, lo, lo[:], head, rev, succ, pred)
        centre = spec.get("centre")
        out[name] = (pc, names, idx[centre] if centre is not None else None)
    return out
