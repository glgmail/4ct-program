#!/usr/bin/env python3
# Copyright (c) 2026 the 4ct-program contributors. Apache 2.0, see LICENSE.
"""Task A5 (#39), implementation A: Penrose's evaluation and Tait counts.

For a cubic graph with a rotation (a cyclic order of the three edge-ends at
each vertex):

* T, the Tait count: proper 3-edge-colourings with the colours 0, 1, 2.
* P, Penrose's evaluation: the sum over all colourings c of the edges with
  0, 1, 2 of the product over vertices of eps(c1, c2, c3), with c1, c2, c3 the
  colours at the vertex in rotation order and eps the Levi-Civita symbol.

A term is non-zero only for a proper colouring. So this implementation
enumerates proper colourings by backtracking and adds up their signs. The
second implementation, in checks/a5/independent/, contracts the full tensor
network instead, and was written without reading this file.

Outputs, all deterministic:

* results-plane.txt: `N index V P T` for every cubic plane graph `plantri -d N`
  gives, the duals of the 3-connected triangulations with N vertices.
* results-named.txt: `name V P T` for named graphs.
* results-embeddings.txt: every rotation system of some small cubic graphs,
  with its genus, and whether P = (-1)^(V/2) T and |P| = T.

Standard library only. Run in WSL from the repository root:

    python3 checks/a5/penrose.py --plantri PATH/TO/plantri --max 12 --out DIR
"""

import argparse
import itertools
import subprocess
import sys
import time
from pathlib import Path


def eps(a, b, c):
    """Levi-Civita symbol on 0, 1, 2."""
    if a == b or b == c or c == a:
        return 0
    return 1 if (b - a) % 3 == 1 else -1


class Cubic:
    """A cubic graph with a rotation, given by darts.

    Dart 3v + i is the i-th edge-end at vertex v in rotation order.
    `mate[d]` is the other end of d's edge. Loops and parallel edges are
    allowed."""

    def __init__(self, mate):
        self.mate = list(mate)
        self.V = len(mate) // 3
        assert len(mate) == 3 * self.V
        assert all(self.mate[self.mate[d]] == d and self.mate[d] != d for d in range(len(mate)))

    @classmethod
    def from_ascii(cls, line):
        """plantri ascii for a simple graph: neighbours in clockwise order."""
        nv, lists = line.split()
        adj = [[ord(ch) - 97 for ch in w] for w in lists.split(",")]
        assert len(adj) == int(nv) and all(len(a) == 3 for a in adj)
        mate = [None] * (3 * len(adj))
        for v, a in enumerate(adj):
            for i, w in enumerate(a):
                mate[3 * v + i] = 3 * w + adj[w].index(v)
        return cls(mate)

    @classmethod
    def from_edges(cls, rot):
        """rot[v] = the edge names at v in rotation order."""
        where = {}
        for v, names in enumerate(rot):
            for i, name in enumerate(names):
                where.setdefault(name, []).append(3 * v + i)
        mate = [None] * (3 * len(rot))
        for a, b in where.values():
            mate[a], mate[b] = b, a
        return cls(mate)

    def rotated(self, flips):
        """The same graph with the rotation reversed at the vertices in `flips`."""
        perm = []
        for v in range(self.V):
            perm += [3 * v, 3 * v + 2, 3 * v + 1] if flips[v] else [3 * v, 3 * v + 1, 3 * v + 2]
        pos = {d: k for k, d in enumerate(perm)}
        return Cubic([pos[self.mate[d]] for d in perm])

    def genus(self):
        """From Euler's formula; faces traced with face = node^-1 . edge."""
        n = len(self.mate)

        def node_inv(d):
            return 3 * (d // 3) + (d % 3 + 2) % 3

        seen = [False] * n
        faces = 0
        for d in range(n):
            if not seen[d]:
                faces += 1
                x = d
                while not seen[x]:
                    seen[x] = True
                    x = node_inv(self.mate[x])
        # components
        comp = list(range(self.V))

        def find(a):
            while comp[a] != a:
                comp[a] = comp[comp[a]]
                a = comp[a]
            return a

        for d in range(n):
            comp[find(d // 3)] = find(self.mate[d] // 3)
        c = len({find(v) for v in range(self.V)})
        e = n // 2
        return (2 * c - (self.V - e + faces)) // 2

    def penrose_tait(self):
        """(P, T) by backtracking over proper colourings."""
        edges = sorted({min(d, self.mate[d]) for d in range(len(self.mate))})
        col = [None] * len(self.mate)
        P = 0
        T = 0

        def free(d, c):
            v = d // 3
            return all(col[3 * v + i] != c for i in range(3))

        def rec(i):
            nonlocal P, T
            if i == len(edges):
                s = 1
                for v in range(self.V):
                    s *= eps(col[3 * v], col[3 * v + 1], col[3 * v + 2])
                P += s
                T += 1
                return
            d = edges[i]
            m = self.mate[d]
            for c in range(3):
                if free(d, c) and free(m, c):
                    col[d] = col[m] = c
                    rec(i + 1)
                    col[d] = col[m] = None

        rec(0)
        return P, T


NAMED = [
    ("theta-sphere", Cubic.from_edges([["x", "y", "z"], ["x", "z", "y"]])),
    ("theta-torus", Cubic.from_edges([["x", "y", "z"], ["x", "y", "z"]])),
    ("K4", Cubic.from_ascii("4 bcd,adc,abd,acb")),
    ("K33-a", Cubic.from_ascii("6 def,def,def,abc,abc,abc")),
    ("petersen", Cubic.from_ascii("10 bef,acg,bdh,cei,adj,ahi,bij,cfj,dfg,egh")),
    ("wagner8", Cubic.from_ascii("8 bhe,acf,bdg,ceh,dfa,egb,fhc,gad")),
]


def plantri_duals(exe, n):
    out = subprocess.run([exe, "-d", "-a", str(n)], capture_output=True, text=True, check=True)
    return [line for line in out.stdout.splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plantri", required=True)
    ap.add_argument("--max", type=int, default=12)
    ap.add_argument("--survey-max", type=int, default=8,
                    help="largest N whose plane graphs get every rotation system")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with open(out / "results-named.txt", "w") as fh:
        for name, g in NAMED:
            P, T = g.penrose_tait()
            fh.write(f"{name} {g.V} {P} {T}\n")

    with open(out / "results-plane.txt", "w") as fh:
        for n in range(4, args.max + 1):
            t0 = time.time()
            lines = plantri_duals(args.plantri, n)
            for idx, line in enumerate(lines):
                g = Cubic.from_ascii(line)
                P, T = g.penrose_tait()
                fh.write(f"{n} {idx} {g.V} {P} {T}\n")
            print(f"N={n}: {len(lines)} graphs, {time.time() - t0:.1f}s", file=sys.stderr)

    # Every rotation system of small graphs: planar ones from plantri, and the
    # named non-planar ones.
    graphs = []
    for n in range(4, args.survey_max + 1):
        for idx, line in enumerate(plantri_duals(args.plantri, n)):
            graphs.append((f"plantri-d-{n}-{idx}", Cubic.from_ascii(line)))
    graphs += [(name, g) for name, g in NAMED if name in ("K33-a", "petersen", "wagner8")]
    with open(out / "results-embeddings.txt", "w") as fh:
        fh.write("# graph genus rotations P=(-1)^(V/2)T |P|=T  (counts over all 2^V rotation systems)\n")
        for name, g in graphs:
            tally = {}
            for flips in itertools.product([0, 1], repeat=g.V):
                h = g.rotated(flips)
                P, T = h.penrose_tait()
                key = (h.genus(), P == (-1) ** (g.V // 2) * T, abs(P) == T)
                tally[key] = tally.get(key, 0) + 1
            for (gen, signed, mag), cnt in sorted(tally.items()):
                fh.write(f"{name} {gen} {cnt} {int(signed)} {int(mag)}\n")


if __name__ == "__main__":
    main()
