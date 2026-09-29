#!/usr/bin/env python3
"""Independent computation of the Tait count T and the Penrose evaluation P
for cubic graphs with a rotation system.

Pure Python 3 standard library, exact integer arithmetic only.

Graph representation (general, allows multigraphs and loops):
    nv     number of vertices 0..nv-1
    edges  list of (a, b) endpoint pairs, edge id = list index
    rot    rot[v] = list of the 3 edge ids at v in the given cyclic order
           (a loop at v appears twice in rot[v]).

P = sum over all 3^E colourings c of prod_v eps(c(rot[v][0]), c(rot[v][1]), c(rot[v][2]))
    computed by a vertex-by-vertex tensor-network contraction (frontier
    dictionary from colours of open edges to integer partial sums).

T = number of proper 3-edge-colourings with labelled colours {0,1,2},
    computed by an explicit backtracking search over edges (a different
    method).  As an internal self-check, the contraction engine is also run
    with the "three distinct colours" indicator tensor and must agree with
    the backtracking count.

Usage:
    python3 run.py --plantri /home/claude/b1-out/bin/plantri --max 12 --out DIR
"""

import argparse
import subprocess
import sys
import time
from itertools import product


# ---------------------------------------------------------------- graphs

class Graph:
    def __init__(self, nv, edges, rot):
        self.nv = nv
        self.edges = [tuple(e) for e in edges]
        self.rot = [list(r) for r in rot]
        self._validate()

    def _validate(self):
        assert len(self.rot) == self.nv
        slots = [[] for _ in self.edges]
        for v, r in enumerate(self.rot):
            assert len(r) == 3, "vertex %d is not of degree 3" % v
            for e in r:
                slots[e].append(v)
        for e, (a, b) in enumerate(self.edges):
            assert sorted(slots[e]) == sorted([a, b]), "edge %d inconsistent" % e


def parse_ascii(line):
    """Parse plantri ascii format '<nv> <list>,<list>,...' (simple graphs)."""
    head, body = line.split(None, 1)
    nv = int(head)
    lists = body.strip().split(',')
    assert len(lists) == nv, "vertex count mismatch"
    nbrs = [[ord(ch) - 97 for ch in s] for s in lists]
    for i in range(nv):
        assert len(nbrs[i]) == 3, "not cubic"
        assert len(set(nbrs[i])) == 3, "multiple edge in ascii input"
        for j in nbrs[i]:
            assert 0 <= j < nv and j != i, "bad neighbour"
            assert i in nbrs[j], "adjacency not symmetric"
    edge_id = {}
    edges = []
    rot = []
    for i in range(nv):
        r = []
        for j in nbrs[i]:
            key = (min(i, j), max(i, j))
            if key not in edge_id:
                edge_id[key] = len(edges)
                edges.append(key)
            r.append(edge_id[key])
        rot.append(r)
    return Graph(nv, edges, rot)


# ---------------------------------------------------------------- tensors

def levi_civita(a, b, c):
    if a == b or b == c or a == c:
        return 0
    if (a, b, c) in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        return 1
    return -1


EPS = {t: levi_civita(*t) for t in product(range(3), repeat=3)}
DISTINCT = {t: (1 if len(set(t)) == 3 else 0) for t in product(range(3), repeat=3)}


# ---------------------------------------------------------------- contraction

def elimination_order(g):
    """Greedy deterministic vertex order: at each step take the unprocessed
    vertex giving the smallest open-edge frontier afterwards; ties broken by
    most already-open incident slots, then smallest vertex index."""
    remaining = [2] * len(g.edges)
    done = [False] * g.nv
    frontier = 0
    order = []
    maxf = 0
    for _ in range(g.nv):
        best = None
        for v in range(g.nv):
            if done[v]:
                continue
            ev = set(g.rot[v])
            opened = closed = already = 0
            for e in ev:
                k = g.rot[v].count(e)
                was_open = remaining[e] == 1
                if was_open:
                    already += 1
                after = remaining[e] - k
                if was_open and after == 0:
                    closed += 1
                elif (not was_open) and after == 1:
                    opened += 1
            size = frontier - closed + opened
            key = (size, -already, v)
            if best is None or key < best:
                best = key
        size, _, v = best
        done[v] = True
        for e in g.rot[v]:
            remaining[e] -= 1
        frontier = size
        maxf = max(maxf, frontier)
        order.append(v)
    return order, maxf


def contract(g, tensor):
    """Contract the network with `tensor` (dict 3-tuple -> int) at every
    vertex, argument order = rotation order.  Returns an integer."""
    order, _ = elimination_order(g)
    remaining = [2] * len(g.edges)
    open_edges = []          # ordered list of open edge ids (key layout)
    state = {(): 1}
    for v in order:
        slots = g.rot[v]
        pos = {e: i for i, e in enumerate(open_edges)}
        uniq = []
        for e in slots:
            if e not in uniq:
                uniq.append(e)
        new_edges = [e for e in uniq if e not in pos]
        for e in slots:
            remaining[e] -= 1
        next_open = [e for e in open_edges if remaining[e] > 0] + \
                    [e for e in new_edges if remaining[e] > 0]
        # recipes: where each slot / each next_open edge reads its colour from
        # source ('k', i) = old key position i ; ('n', j) = new assignment j
        nidx = {e: j for j, e in enumerate(new_edges)}

        def src(e):
            return (0, pos[e]) if e in pos else (1, nidx[e])
        slot_src = [src(e) for e in slots]
        out_src = [src(e) for e in next_open]
        new_assignments = list(product(range(3), repeat=len(new_edges)))
        newstate = {}
        for key, val in state.items():
            for na in new_assignments:
                srcs = (key, na)
                t = (srcs[slot_src[0][0]][slot_src[0][1]],
                     srcs[slot_src[1][0]][slot_src[1][1]],
                     srcs[slot_src[2][0]][slot_src[2][1]])
                w = tensor[t]
                if w == 0:
                    continue
                nk = tuple(srcs[s][i] for s, i in out_src)
                newstate[nk] = newstate.get(nk, 0) + val * w
        state = {k: x for k, x in newstate.items() if x != 0}
        open_edges = next_open
    assert open_edges == []
    return state.get((), 0)


def penrose(g):
    return contract(g, EPS)


# ---------------------------------------------------------------- backtracking

def tait_backtrack(g):
    """Count proper 3-edge-colourings by backtracking over edges."""
    E = len(g.edges)
    for v, r in enumerate(g.rot):
        if len(set(r)) < 3:      # loop: two slots share a colour
            return 0
    # edge order: BFS over vertices, edges in rotation order at each vertex
    seen_v = [False] * g.nv
    seen_e = [False] * E
    eorder = []
    for root in range(g.nv):
        if seen_v[root]:
            continue
        seen_v[root] = True
        queue = [root]
        qi = 0
        while qi < len(queue):
            v = queue[qi]
            qi += 1
            for e in g.rot[v]:
                if not seen_e[e]:
                    seen_e[e] = True
                    eorder.append(e)
                a, b = g.edges[e]
                w = b if a == v else a
                if not seen_v[w]:
                    seen_v[w] = True
                    queue.append(w)
    ends = [g.edges[e] for e in eorder]
    mask = [0] * g.nv
    count = 0
    # iterative DFS
    choice = [-1] * E
    i = 0
    while i >= 0:
        if i == E:
            count += 1
            i -= 1
            if i >= 0:
                a, b = ends[i]
                bit = 1 << choice[i]
                mask[a] ^= bit
                mask[b] ^= bit
            continue
        a, b = ends[i]
        c = choice[i] + 1
        while c < 3 and ((mask[a] >> c) & 1 or (mask[b] >> c) & 1):
            c += 1
        if c < 3:
            choice[i] = c
            bit = 1 << c
            mask[a] |= bit
            mask[b] |= bit
            i += 1
            if i < E:
                choice[i] = -1
        else:
            choice[i] = -1
            i -= 1
            if i >= 0:
                a2, b2 = ends[i]
                bit = 1 << choice[i]
                mask[a2] ^= bit
                mask[b2] ^= bit
    return count


def evaluate(g, selfcheck=True):
    P = penrose(g)
    T = tait_backtrack(g)
    if selfcheck:
        T2 = contract(g, DISTINCT)
        if T2 != T:
            raise RuntimeError("self-check failed: backtrack T=%d, contraction T=%d" % (T, T2))
    return P, T


# ---------------------------------------------------------------- named

def named_graphs():
    out = []
    # theta: vertices u=0, v=1; edges x=0, y=1, z=2
    theta_edges = [(0, 1), (0, 1), (0, 1)]
    out.append(("theta-sphere", Graph(2, theta_edges, [[0, 1, 2], [0, 2, 1]])))
    out.append(("theta-torus", Graph(2, theta_edges, [[0, 1, 2], [0, 1, 2]])))
    for name, s in [
        ("K4", "4 bcd,adc,abd,acb"),
        ("K33-a", "6 def,def,def,abc,abc,abc"),
        ("petersen", "10 bef,acg,bdh,cei,adj,ahi,bij,cfj,dfg,egh"),
        ("wagner8", "8 bhe,acf,bdg,ceh,dfa,egb,fhc,gad"),
    ]:
        out.append((name, parse_ascii(s)))
    return out


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plantri", required=True)
    ap.add_argument("--min", type=int, default=4)
    ap.add_argument("--max", type=int, default=12)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-selfcheck", action="store_true")
    args = ap.parse_args()
    selfcheck = not args.no_selfcheck

    import os
    os.makedirs(args.out, exist_ok=True)

    with open(os.path.join(args.out, "results-named.txt"), "w", newline="\n") as f:
        for name, g in named_graphs():
            P, T = evaluate(g, selfcheck)
            f.write("%s %d %d %d\n" % (name, g.nv, P, T))

    timings = []
    with open(os.path.join(args.out, "results-plane.txt"), "w", newline="\n") as f:
        for N in range(args.min, args.max + 1):
            t0 = time.time()
            proc = subprocess.run([args.plantri, "-d", "-a", str(N)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  check=True, text=True)
            idx = 0
            maxf = 0
            for line in proc.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                g = parse_ascii(line)
                assert g.nv == 2 * N - 4
                maxf = max(maxf, elimination_order(g)[1])
                P, T = evaluate(g, selfcheck)
                f.write("%d %d %d %d %d\n" % (N, idx, g.nv, P, T))
                idx += 1
            f.flush()
            dt = time.time() - t0
            msg = "N=%d graphs=%d max_frontier=%d seconds=%.1f" % (N, idx, maxf, dt)
            timings.append(msg)
            print(msg, file=sys.stderr, flush=True)
    with open(os.path.join(args.out, "timings.txt"), "w", newline="\n") as f:
        f.write("selfcheck=%s\n" % selfcheck)
        for m in timings:
            f.write(m + "\n")


if __name__ == "__main__":
    main()
