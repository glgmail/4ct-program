#!/usr/bin/env python3
"""Build the queryable index over the near-linear proof's reducible configurations.

    python3 search/index/build.py            # write search/index/configurations.csv
    python3 search/index/build.py --check    # rebuild in memory, compare byte for byte
    python3 search/index/build.py --lookup F # shape of configuration file F, and its row

Reads the configuration files under data/near-linear-4ct/reducible-configurations/D
(imported unchanged from upstream; see data/README.md) and writes one row per
configuration of the set D in the paper, 8,202 in all: the 8,200 files, plus the
two configurations that consist of a single vertex of degree 3 or 4, which the
paper counts in D (section 3) but upstream does not ship as files.

Standard library only, no randomness, no timestamps: the output depends on the
input bytes alone, so it rebuilds byte-identically from a clean checkout.

The configuration file format
-----------------------------
Line 1 is empty. Line 2 is "N R": the free completion has N vertices, of which
1..R form the ring and R+1..N are the configuration's own vertices. Then one
line per configuration vertex: "v d n_1 ... n_d", its degree d and its d
neighbours in cyclic order. The build refuses any file that breaks the
conventions it relies on, and says which:

- every configuration vertex has a line, and d equals the number of neighbours;
- adjacency between configuration vertices is symmetric;
- consecutive neighbours of v are adjacent (every face at v is a triangle);
- the cyclic orders are consistently oriented: if b follows a around v, then b
  precedes v around a;
- the ring is the cycle 1, 2, ..., R, and wherever two ring vertices are
  consecutive around v, the second is the next ring vertex;
- the edge count is 3N - 3 - R, as it must be for a triangulated disc bounded
  by a ring of length R;
- the configuration's own vertices induce a connected graph.

Every file at the pinned upstream commit satisfies all of them.

The shape
---------
Two files describe the same configuration when some bijection of vertices,
sending configuration vertices to configuration vertices, carries every cyclic
neighbour order onto the other file's. `shape_oriented` identifies a
configuration up to such maps that keep the orientation; `shape` also allows
reflection, so a configuration and its mirror image share a `shape`.

Each is the first 16 hex digits of the sha256 of a canonical code: over every
starting dart (a configuration vertex and one of its neighbours) and, for
`shape`, both orientations, number the vertices in breadth-first order,
walking each configuration vertex's neighbours in cyclic order starting from
the dart it was reached along, and record every configuration vertex's
number and its neighbours' numbers. The lexicographically least record is the
canonical code. It does not depend on how a file happens to number its
vertices. search/index/crosscheck.py checks it against an independent graph
isomorphism test.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "data" / "near-linear-4ct" / "reducible-configurations" / "D"
INDEX = ROOT / "search" / "index" / "configurations.csv"

COLUMNS = [
    "config",          # D0000 .. D8199, or deg3 / deg4
    "path",            # the file under data/, or empty for deg3 / deg4
    "ring_size",       # R
    "vertices",        # the configuration's own vertices, N - R
    "edges",           # edges between configuration vertices
    "degree_sequence", # degrees of the configuration's vertices, non-increasing
    "shape",           # canonical id up to isomorphism and reflection
    "shape_oriented",  # canonical id up to orientation-preserving isomorphism
    "chiral",          # 1 if the mirror image is a different oriented shape
]

# The paper's D (section 3) "includes the D-reducible configurations
# consisting of a single vertex of degree 3 or 4"; upstream's README: the
# directory holds the configurations of D "except for a vertex of degree 3,4".
SINGLE_VERTEX = (3, 4)


class FormatError(ValueError):
    pass


class Config:
    """A configuration: ring size, vertex count, and each configuration
    vertex's neighbours in cyclic order."""

    def __init__(self, name: str, path: str, n: int, ring: int,
                 rot: dict[int, list[int]]):
        self.name, self.path, self.n, self.ring, self.rot = name, path, n, ring, rot


def parse(text: str, name: str, path: str) -> Config:
    lines = text.split("\n")
    if lines[0].strip():
        raise FormatError(f"{name}: line 1 should be empty")
    try:
        n, ring = map(int, lines[1].split())
    except ValueError:
        raise FormatError(f"{name}: line 2 should be 'N R'") from None
    rot: dict[int, list[int]] = {}
    for line in lines[2:]:
        if not line.strip():
            continue
        nums = [int(x) for x in line.split()]
        v, d, nbrs = nums[0], nums[1], nums[2:]
        if len(nbrs) != d:
            raise FormatError(f"{name}: vertex {v} has degree {d} but {len(nbrs)} neighbours")
        if v in rot:
            raise FormatError(f"{name}: vertex {v} listed twice")
        rot[v] = nbrs
    cfg = Config(name, path, n, ring, rot)
    validate(cfg)
    return cfg


def validate(cfg: Config) -> None:
    name, n, ring, rot = cfg.name, cfg.n, cfg.ring, cfg.rot
    if sorted(rot) != list(range(ring + 1, n + 1)):
        raise FormatError(f"{name}: configuration vertices are not {ring + 1}..{n}")
    for v, nbrs in rot.items():
        if len(set(nbrs)) != len(nbrs) or v in nbrs:
            raise FormatError(f"{name}: vertex {v} has a repeated or self neighbour")
        for w in nbrs:
            if not 1 <= w <= n:
                raise FormatError(f"{name}: vertex {v} has out-of-range neighbour {w}")
            if w > ring and v not in rot[w]:
                raise FormatError(f"{name}: {v}-{w} is listed at {v} but not at {w}")
        for i, a in enumerate(nbrs):
            b = nbrs[(i + 1) % len(nbrs)]
            if a > ring:
                around_a = rot[a]
                j = around_a.index(v)
                if around_a[j - 1] != b:
                    raise FormatError(f"{name}: face {v},{a},{b} is not consistently oriented")
            elif b > ring:
                if v not in rot[b] or a not in rot[b]:
                    raise FormatError(f"{name}: face {v},{a},{b} is not a triangle")
            elif b != a % ring + 1:
                raise FormatError(f"{name}: ring vertices {a},{b} are consecutive at {v} "
                                  f"but {b} is not the next ring vertex")
    edges = {frozenset((v, w)) for v, nbrs in rot.items() for w in nbrs}
    edges |= {frozenset((i, i % ring + 1)) for i in range(1, ring + 1)}
    if len(edges) != 3 * n - 3 - ring:
        raise FormatError(f"{name}: {len(edges)} edges, but a triangulated disc with "
                          f"{n} vertices and ring {ring} has {3 * n - 3 - ring}")
    start = min(rot)
    seen, stack = {start}, [start]
    while stack:
        v = stack.pop()
        for w in rot[v]:
            if w > ring and w not in seen:
                seen.add(w)
                stack.append(w)
    if len(seen) != len(rot):
        raise FormatError(f"{name}: the configuration's vertices are not connected")


def single_vertex(degree: int) -> Config:
    """The configuration consisting of one vertex of the given degree: its
    free completion is a wheel whose ring is its neighbours."""
    cfg = Config(f"deg{degree}", "", degree + 1, degree,
                 {degree + 1: list(range(1, degree + 1))})
    validate(cfg)
    return cfg


def code_from(cfg: Config, start: int, first: int, step: int,
              best: list[int] | None) -> list[int] | None:
    """The breadth-first code from the dart start->first, walking cyclic
    orders forwards (step 1) or backwards (step -1). Returns None as soon as
    the code is certain to exceed `best`."""
    ring, rot = cfg.ring, cfg.rot
    number = {start: 0}
    entry = {start: first}
    queue = [start]
    code: list[int] = []
    head = 0
    while head < len(queue):
        v = queue[head]
        head += 1
        nbrs = rot[v]
        i = nbrs.index(entry[v])
        k = len(nbrs)
        code.append(number[v])
        code.append(k)
        for t in range(k):
            w = nbrs[(i + step * t) % k]
            if w not in number:
                number[w] = len(number)
                if w > ring:
                    entry[w] = v
                    queue.append(w)
            code.append(number[w])
        if best is not None:
            prefix = best[:len(code)]
            if code > prefix:
                return None
            if code < prefix:
                best = None
    return code


def canonical(cfg: Config, steps: tuple[int, ...]) -> list[int]:
    best: list[int] | None = None
    for step in steps:
        for v in sorted(cfg.rot):
            for w in cfg.rot[v]:
                code = code_from(cfg, v, w, step, best)
                if code is not None and (best is None or code < best):
                    best = code
    assert best is not None
    return best


def digest(cfg: Config, code: list[int]) -> str:
    text = f"{cfg.n} {cfg.ring}:" + ",".join(map(str, code))
    return hashlib.sha256(text.encode("ascii")).hexdigest()[:16]


def row(cfg: Config) -> dict[str, str]:
    ring, rot = cfg.ring, cfg.rot
    oriented = digest(cfg, canonical(cfg, (1,)))
    mirrored = digest(cfg, canonical(cfg, (-1,)))
    either = digest(cfg, canonical(cfg, (1, -1)))
    inner_edges = {frozenset((v, w)) for v, nbrs in rot.items() for w in nbrs if w > ring}
    return {
        "config": cfg.name,
        "path": cfg.path,
        "ring_size": str(ring),
        "vertices": str(len(rot)),
        "edges": str(len(inner_edges)),
        "degree_sequence": " ".join(str(d) for d in sorted((len(n) for n in rot.values()),
                                                          reverse=True)),
        "shape": either,
        "shape_oriented": oriented,
        "chiral": "1" if oriented != mirrored else "0",
    }


def load_all() -> list[Config]:
    files = sorted(CONFIG_DIR.glob("*.conf"))
    if not files:
        sys.exit(f"no configuration files under {CONFIG_DIR.relative_to(ROOT).as_posix()}; "
                 "is git-lfs installed and the data pulled?")
    configs = []
    for f in files:
        raw = f.read_bytes()
        if raw.startswith(b"version https://git-lfs"):
            sys.exit(f"{f.relative_to(ROOT).as_posix()} is an LFS pointer; run `git lfs pull` first")
        configs.append(parse(raw.decode("ascii"), f.stem, f.relative_to(ROOT).as_posix()))
    configs += [single_vertex(d) for d in SINGLE_VERTEX]
    return configs


def render(configs: list[Config]) -> bytes:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    for cfg in configs:
        writer.writerow(row(cfg))
    return out.getvalue().encode("ascii")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="rebuild and compare with the committed index")
    ap.add_argument("--lookup", metavar="FILE",
                    help="print the shape of a configuration file and any index rows with it")
    args = ap.parse_args()

    if args.lookup:
        f = Path(args.lookup)
        r = row(parse(f.read_text(encoding="ascii"), f.stem, f.as_posix()))
        print(f"shape {r['shape']}  shape_oriented {r['shape_oriented']}  "
              f"ring {r['ring_size']}  vertices {r['vertices']}")
        with INDEX.open(newline="", encoding="ascii") as handle:
            hits = [x for x in csv.DictReader(handle) if x["shape"] == r["shape"]]
        for x in hits:
            same = "same orientation" if x["shape_oriented"] == r["shape_oriented"] else "mirror image"
            print(f"  {x['config']}  {x['path'] or '(not a file)'}  ({same})")
        if not hits:
            print("  not in the index")
        return 0

    data = render(load_all())
    if args.check:
        committed = INDEX.read_bytes() if INDEX.is_file() else b""
        if committed == data:
            print(f"{INDEX.relative_to(ROOT).as_posix()} rebuilds identically "
                  f"(sha256 {hashlib.sha256(data).hexdigest()})")
            return 0
        print(f"{INDEX.relative_to(ROOT).as_posix()} differs from a fresh build", file=sys.stderr)
        return 1
    INDEX.write_bytes(data)
    rows = data.count(b"\n") - 1
    print(f"wrote {INDEX.relative_to(ROOT).as_posix()}: {rows} rows, "
          f"sha256 {hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
