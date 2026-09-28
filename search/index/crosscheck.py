#!/usr/bin/env python3
"""Check search/index/configurations.csv against an independent implementation.

    python3 search/index/crosscheck.py

Needs networkx (tested with 3.6.1). build.py does not use it.

What it checks, and why it is enough
------------------------------------
1. The plain columns. ring_size, vertices, edges and degree_sequence are
   recomputed here from the data files with a separate parser.

2. `shape`: same value exactly when isomorphic. Take a configuration's free
   completion as an abstract graph, ring cycle included, with each vertex
   marked "ring" or "configuration". Capping the ring with one extra vertex
   gives a triangulation of the sphere, which is 3-connected, so by Whitney's
   theorem its embedding is unique up to reflection. Hence two configurations
   have the same `shape` if and only if their marked graphs are isomorphic,
   and networkx can decide that without knowing about embeddings. The check
   is exhaustive: it groups the graphs by Weisfeiler-Lehman hash (isomorphic
   graphs always share one), runs a full isomorphism test on every pair
   inside a group, and requires that pairs are isomorphic exactly when they
   share a `shape`.

3. `chiral`. A configuration is achiral exactly when an orientation-preserving
   isomorphism carries it onto its mirror image. Orientation is encoded as a
   labelled directed graph of darts: each dart points to the next dart around
   its tail and to its head vertex. The test is an isomorphism check between
   that graph and the one built from reversed cyclic orders, run for every
   configuration.

4. Invariance of build.py's canonical code. It relabels every configuration's
   vertices with a fixed permutation, and separately mirrors it. It then
   requires build.py to return the same `shape`, the same `shape_oriented`
   after relabelling, and the two oriented shapes swapped after mirroring.
   This one imports build.py, so it is a test of that code rather than an
   independent implementation.

Written by the same author as build.py, so "independent" means a different
method and library, not a different person. Checks 2 and 3 do not share code
or method with it.
"""
from __future__ import annotations

import csv
import itertools
import sys
from collections import defaultdict
from pathlib import Path

import networkx as nx
from networkx.algorithms import isomorphism as iso

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "search" / "index" / "configurations.csv"


def read(path: Path) -> tuple[int, int, dict[int, list[int]]]:
    tokens = path.read_text(encoding="ascii").split("\n", 2)
    n, r = (int(x) for x in tokens[1].split())
    adj = {}
    for line in tokens[2].splitlines():
        parts = [int(x) for x in line.split()]
        if parts:
            adj[parts[0]] = parts[2:]
    return n, r, adj


def wheel(d: int) -> tuple[int, int, dict[int, list[int]]]:
    return d + 1, d, {d + 1: list(range(1, d + 1))}


def marked_graph(n: int, r: int, adj: dict[int, list[int]]) -> nx.Graph:
    g = nx.Graph()
    for v in range(1, n + 1):
        g.add_node(v, kind="ring" if v <= r else "conf")
    g.add_edges_from((v, w) for v, ws in adj.items() for w in ws)
    g.add_edges_from((i, i % r + 1) for i in range(1, r + 1))
    return g


def dart_graph(r: int, adj: dict[int, list[int]], reverse: bool) -> nx.DiGraph:
    g = nx.DiGraph()
    for v in set(adj) | {w for ws in adj.values() for w in ws}:
        g.add_node(("v", v), kind="ring" if v <= r else "conf")
    for v, ws in adj.items():
        order = ws[::-1] if reverse else ws
        k = len(order)
        for i, w in enumerate(order):
            g.add_node(("d", v, w), kind="dart")
            g.add_edge(("d", v, w), ("d", v, order[(i + 1) % k]), label="next")
            g.add_edge(("d", v, w), ("v", w), label="head")
            g.add_edge(("v", v), ("d", v, w), label="tail")
    return g


def fail(msg: str) -> None:
    print("FAIL", msg)
    global failures
    failures += 1


failures = 0


def main() -> int:
    with INDEX.open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    print(f"index: {len(rows)} rows")

    confs = {}
    for row in rows:
        if row["path"]:
            confs[row["config"]] = read(ROOT / row["path"])
        else:
            confs[row["config"]] = wheel(int(row["config"].removeprefix("deg")))

    # 1. plain columns
    for row in rows:
        n, r, adj = confs[row["config"]]
        inner = {frozenset((v, w)) for v, ws in adj.items() for w in ws if w > r}
        want = {
            "ring_size": str(r),
            "vertices": str(len(adj)),
            "edges": str(len(inner)),
            "degree_sequence": " ".join(map(str, sorted(map(len, adj.values()), reverse=True))),
        }
        for col, val in want.items():
            if row[col] != val:
                fail(f"{row['config']}: {col} is {row[col]!r}, recomputed {val!r}")
    print("1. plain columns recomputed")

    # 2. shape <=> isomorphism of marked graphs, every candidate pair
    graphs = {name: marked_graph(*c) for name, c in confs.items()}
    buckets = defaultdict(list)
    for name, g in graphs.items():
        buckets[nx.weisfeiler_lehman_graph_hash(g, node_attr="kind")].append(name)
    shape = {row["config"]: row["shape"] for row in rows}
    pairs = isomorphic = 0
    match = iso.categorical_node_match("kind", None)
    for names in buckets.values():
        for a, b in itertools.combinations(names, 2):
            pairs += 1
            same = nx.is_isomorphic(graphs[a], graphs[b], node_match=match)
            isomorphic += same
            if same != (shape[a] == shape[b]):
                fail(f"{a} vs {b}: isomorphic={same} but shapes {shape[a]} / {shape[b]}")
    # A shared shape split across hash groups would be a non-isomorphic pair
    # with equal shapes that the pairwise loop above never sees.
    bucket_of = {name: h for h, names in buckets.items() for name in names}
    by_shape = defaultdict(list)
    for name, s in shape.items():
        by_shape[s].append(name)
    for s, names in by_shape.items():
        if len({bucket_of[x] for x in names}) > 1:
            fail(f"shape {s} is shared by non-isomorphic configurations {names}")
    print(f"2. {len(buckets)} hash groups, {pairs} candidate pairs tested, "
          f"{isomorphic} isomorphic; shapes shared by several configurations: "
          f"{sum(len(v) > 1 for v in by_shape.values())}")

    # 3. chirality via oriented dart graphs
    chiral = 0
    dmatch = iso.categorical_node_match("kind", None)
    ematch = iso.categorical_edge_match("label", None)
    for row in rows:
        n, r, adj = confs[row["config"]]
        achiral = nx.is_isomorphic(dart_graph(r, adj, False), dart_graph(r, adj, True),
                                   node_match=dmatch, edge_match=ematch)
        chiral += not achiral
        if (row["chiral"] == "1") != (not achiral):
            fail(f"{row['config']}: chiral={row['chiral']} but mirror-isomorphic={achiral}")
    print(f"3. chirality recomputed: {chiral} chiral, {len(rows) - chiral} achiral")

    # 4. build.py's canonical code is invariant under relabelling and mirroring
    sys.path.insert(0, str(Path(__file__).parent))
    import build  # noqa: E402

    for row in rows:
        n, r, adj = confs[row["config"]]
        # relabel configuration vertices by reversing their order, and rotate
        # the ring; the ring must stay the cycle 1..R in the same direction
        ring_map = {i: (i % r) + 1 for i in range(1, r + 1)}
        conf_map = {v: n + r + 1 - v for v in adj}
        m = {**ring_map, **conf_map}
        relabelled = {m[v]: [m[w] for w in ws] for v, ws in adj.items()}
        # the mirror image: reverse every cyclic order and the ring direction
        ring_rev = {i: r + 1 - i for i in range(1, r + 1)}
        mirrored = {v: [ring_rev.get(w, w) for w in ws[::-1]] for v, ws in adj.items()}
        for label, rot, expect in (("relabelled", relabelled, "same"),
                                   ("mirrored", mirrored, "swapped")):
            cfg = build.Config(row["config"], row["path"], n, r, rot)
            build.validate(cfg)
            got = build.row(cfg)
            if got["shape"] != row["shape"]:
                fail(f"{row['config']} {label}: shape changed")
            if expect == "same" and got["shape_oriented"] != row["shape_oriented"]:
                fail(f"{row['config']} {label}: shape_oriented changed")
            if expect == "swapped" and row["chiral"] == "1" \
                    and got["shape_oriented"] == row["shape_oriented"]:
                fail(f"{row['config']} {label}: chiral but mirror has the same oriented shape")
    print("4. build.py invariant under relabelling and mirroring")

    print("OK" if failures == 0 else f"{failures} FAILURE(S)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
