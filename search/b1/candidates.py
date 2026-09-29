"""The candidate language, and the candidates.

A candidate is a statement stronger than the Four Colour Theorem, written as
a `Candidate`:

- `id`, `family`, and `statement`: the claim in words, exactly as it is
  tested;
- `domain`: "sphere" (every triangulation of the sphere) or "disc" (every
  triangulation of a disc with a chordless boundary, plantri -P);
- `palette`: "shared" (all vertices choose from the same four colours) or
  "lists" (each vertex has its own list);
- `expectation`: what is known in advance, and why the candidate is here;
- `test(t)`: returns None if the statement holds for t, otherwise a witness
  (a JSON-serialisable dict saying why it fails on t).

**List-style candidates are rejected before they run.** Planar graphs are
not 4-choosable (Voigt 1993), so a candidate with palette "lists" is already
dead, and the harness reports it as rejected without spending compute.

A candidate that holds on every triangulation up to the bound has **not been
proved**. The report calls it "not killed up to n vertices", never true.

To add a candidate, append a Candidate to CANDIDATES. Its test sees one
triangulation at a time and must be deterministic.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Optional

from colour import (cycle_colourings, dual, extends, normalise, tait_colourings,
                    vertex_colourings)
from planar import Tri


@dataclass(frozen=True)
class Candidate:
    id: str
    family: str
    domain: str          # "sphere" or "disc"
    palette: str         # "shared" or "lists"
    statement: str
    expectation: str
    test: Optional[Callable[[Tri], Optional[dict]]]


# ---------------------------------------------------------------------------
# precolouring extension (discs)
# ---------------------------------------------------------------------------
def _boundary_extension(t: Tri, colours):
    k = len(t.boundary)
    for bc in cycle_colourings(k, colours):
        if not extends(t, dict(zip(t.boundary, bc))):
            return {"boundary": [v + 1 for v in t.boundary],
                    "boundary_colouring": list(bc)}
    return None


# ---------------------------------------------------------------------------
# Kempe changes
# ---------------------------------------------------------------------------
def kempe_classes(t: Tri):
    """Partition the 4-colourings of t (up to permutation) into Kempe
    equivalence classes. Returns a list of classes, each a sorted list of
    colourings in normal form."""
    anchor = (0, t.rot[0][0], t.rot[0][1])
    cols = list(vertex_colourings(t))
    index = {c: i for i, c in enumerate(cols)}
    parent = list(range(len(cols)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, c in enumerate(cols):
        for a, b in itertools.combinations(range(4), 2):
            seen = set()
            for s in range(t.n):
                if c[s] not in (a, b) or s in seen:
                    continue
                comp, stack = [], [s]
                seen.add(s)
                while stack:
                    v = stack.pop()
                    comp.append(v)
                    for w in t.rot[v]:
                        if w not in seen and c[w] in (a, b):
                            seen.add(w)
                            stack.append(w)
                new = list(c)
                for v in comp:
                    new[v] = b if c[v] == a else a
                j = index[normalise(new, anchor)]
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[max(ri, rj)] = min(ri, rj)
    classes = {}
    for i, c in enumerate(cols):
        classes.setdefault(find(i), []).append(c)
    return sorted((sorted(v) for v in classes.values()), key=lambda cl: (len(cl), cl))


def _kempe_connected(t: Tri):
    classes = kempe_classes(t)
    if len(classes) == 1:
        return None
    return {"kempe_classes": len(classes),
            "class_sizes": [len(c) for c in classes],
            "colouring_in_smallest_class": list(classes[0][0])}


# ---------------------------------------------------------------------------
# balanced colourings
# ---------------------------------------------------------------------------
def _class_sizes(c):
    return sorted((c.count(x) for x in range(4)), reverse=True)


def _balanced(t: Tri, ok):
    best = None
    for c in vertex_colourings(t):
        s = _class_sizes(c)
        if ok(s, t.n):
            return None
        if best is None or s < best:
            best = s
    return {"most_balanced_class_sizes": best}


# ---------------------------------------------------------------------------
# flows: the dual's Tait colourings
# ---------------------------------------------------------------------------
def dual_hamiltonian_cycle(t: Tri):
    """A Hamiltonian cycle of the dual cubic graph, as a list of faces, or
    None. Direct backtracking; independent of the Tait colourings."""
    faces, adj, _ = dual(t)
    m = len(faces)
    nbr = [[g for g, _ in a] for a in adj]
    path, on = [0], [False] * m
    on[0] = True

    def rec():
        if len(path) == m:
            return 0 in nbr[path[-1]]
        for g in nbr[path[-1]]:
            if not on[g]:
                on[g] = True
                path.append(g)
                if rec():
                    return True
                path.pop()
                on[g] = False
        return False

    return list(path) if rec() else None


def _two_classes_connected(edges, col, a, b, m):
    parent = list(range(m))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    comps = m
    for e, (f, g) in enumerate(edges):
        if col[e] in (a, b):
            rf, rg = find(f), find(g)
            if rf != rg:
                parent[rf] = rg
                comps -= 1
    return comps == 1


def hamiltonian_pairs(t: Tri):
    """For each Tait colouring, how many of its three colour-class pairs
    form a Hamiltonian cycle. Yields (colouring, count)."""
    faces, _, edges = dual(t)
    m = len(faces)
    for col in tait_colourings(t):
        k = sum(_two_classes_connected(edges, col, a, b, m)
                for a, b in ((0, 1), (0, 2), (1, 2)))
        yield col, k


def _tait_hamiltonian(t: Tri):
    return None if dual_hamiltonian_cycle(t) is not None else {"dual_hamiltonian": False}


def _perfect_tait(t: Tri):
    best = 0
    for _, k in hamiltonian_pairs(t):
        if k == 3:
            return None
        best = max(best, k)
    return {"best_hamiltonian_pairs": best}


# ---------------------------------------------------------------------------
# the candidates
# ---------------------------------------------------------------------------
CANDIDATES = [
    Candidate(
        id="PE1", family="precolouring extension", domain="disc", palette="shared",
        statement="In every triangulation of a disc with a chordless boundary, every "
                  "proper 4-colouring of the boundary cycle extends to the whole disc.",
        expectation="Control, known false: the wheel with four spokes, a 4-cycle "
                    "around one vertex, cannot extend a boundary colouring that uses "
                    "all four colours. The harness must kill it at 5 vertices.",
        test=lambda t: _boundary_extension(t, 4)),
    Candidate(
        id="PE2", family="precolouring extension", domain="disc", palette="shared",
        statement="In every triangulation of a disc with a chordless boundary, every "
                  "proper colouring of the boundary cycle that uses at most three "
                  "colours extends to a proper 4-colouring of the whole disc.",
        expectation="Open to us. Restricting the boundary to three colours is the "
                    "natural way to rescue PE1, since a 3-coloured boundary leaves a "
                    "fourth colour free for the inside.",
        test=lambda t: _boundary_extension(t, 3)),
    Candidate(
        id="K1", family="Kempe connectivity", domain="sphere", palette="shared",
        statement="For every triangulation of the sphere, any two proper 4-colourings "
                  "are connected by a sequence of Kempe changes.",
        expectation="Open to us. A yes would let an argument move between colourings "
                    "freely, which is what Kempe's own proof needed. Meyniel proved the "
                    "analogue for 5-colourings of planar graphs.",
        test=_kempe_connected),
    Candidate(
        id="BAL1", family="balanced colourings", domain="sphere", palette="shared",
        statement="Every triangulation of the sphere has an equitable proper "
                  "4-colouring: the four colour classes differ in size by at most one.",
        expectation="Expected false. In a bipyramid (two poles joined to every vertex "
                    "of a long cycle) the poles' colours are barred from the whole "
                    "cycle, so some class must stay small.",
        test=lambda t: _balanced(t, lambda s, n: s[0] - s[-1] <= 1)),
    Candidate(
        id="BAL2", family="balanced colourings", domain="sphere", palette="shared",
        statement="Every triangulation of the sphere on n vertices has a proper "
                  "4-colouring in which every colour is used on fewer than n/2 "
                  "vertices.",
        expectation="Positive control: a theorem for all planar graphs with n >= 3 "
                    "(Kawarabayashi, Yoneda and Yoneda, arXiv:2607.13025, July 2026). "
                    "If the harness kills it, the harness or the paper is wrong.",
        test=lambda t: _balanced(t, lambda s, n: 2 * s[0] < n)),
    Candidate(
        id="FL1", family="flows", domain="sphere", palette="shared",
        statement="The dual cubic graph of every triangulation of the sphere has a "
                  "Tait colouring in which two of the colour classes together form a "
                  "Hamiltonian cycle (equivalently, the dual is Hamiltonian).",
        expectation="Known false, but not within reach: this is Tait's conjecture, "
                    "refuted by Tutte (1946). The smallest counterexamples have 38 dual "
                    "vertices (Holton and McKay 1988), i.e. triangulations with 21 "
                    "vertices, beyond the bound. It must survive both tiers, which "
                    "shows that surviving is not being true.",
        test=_tait_hamiltonian),
    Candidate(
        id="FL2", family="flows", domain="sphere", palette="shared",
        statement="The dual cubic graph of every triangulation of the sphere has a "
                  "Tait colouring in which every two of the three colour classes "
                  "together form a Hamiltonian cycle.",
        expectation="Open to us; a strengthening of FL1 and so false eventually, "
                    "but the question is how early.",
        test=_perfect_tait),
    Candidate(
        id="L1", family="precolouring extension", domain="sphere", palette="lists",
        statement="Every triangulation of the sphere is 4-choosable: whatever list of "
                  "four colours each vertex is given, it can be coloured from its lists.",
        expectation="Rejected up front, never run: planar graphs are not 4-choosable "
                    "(Voigt 1993). It is here to show the rejection working.",
        test=None),
]


def rejected(c: Candidate):
    """The reason a candidate is not run, or None."""
    if c.palette != "shared":
        return ("list-style candidate: planar graphs are not 4-choosable "
                "(M. Voigt, Discrete Math. 120 (1993) 215-219), so candidates must "
                "use the shared four colours")
    if c.test is None:
        return "no test given"
    return None
