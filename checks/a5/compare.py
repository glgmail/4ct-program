#!/usr/bin/env python3
# Copyright (c) 2026 the 4ct-program contributors. Apache 2.0, see LICENSE.
"""Task A5 (#39): compare the two implementations, and test Penrose's formula.

Reads the results of implementation A (checks/a5/penrose.py) and of the
independent implementation B (checks/a5/independent/). Checks that:

* A and B agree on every graph: same lines, in the same order;
* on every plane graph, P = (-1)^(V/2) T (Penrose's formula) and T > 0.

Prints a summary. Exit status 0 only if everything holds.

    python3 checks/a5/compare.py DIR_A DIR_B
"""

import sys
from pathlib import Path


def main():
    a, b = Path(sys.argv[1]), Path(sys.argv[2])
    ok = True
    for name in ("results-plane.txt", "results-named.txt"):
        la = (a / name).read_text().splitlines()
        lb = (b / name).read_text().splitlines()
        same = la == lb
        ok &= same
        print(f"{name}: A has {len(la)} lines, B has {len(lb)}; identical: {same}")
    rows = [list(map(int, line.split())) for line in (a / "results-plane.txt").read_text().splitlines()]
    formula = sum(1 for n, i, v, p, t in rows if p == (-1) ** (v // 2) * t)
    positive = sum(1 for n, i, v, p, t in rows if t > 0)
    print(f"plane graphs: {len(rows)}, N = {min(r[0] for r in rows)}..{max(r[0] for r in rows)}, "
          f"up to {max(r[2] for r in rows)} vertices")
    print(f"P = (-1)^(V/2) T on {formula} of {len(rows)}; T > 0 on {positive} of {len(rows)}")
    ok &= formula == len(rows) and positive == len(rows)
    for line in (a / "results-named.txt").read_text().splitlines():
        name, v, p, t = line.split()
        v, p, t = int(v), int(p), int(t)
        print(f"  {name}: V={v} P={p} T={t}  P=(-1)^(V/2)T: {p == (-1) ** (v // 2) * t}  |P|=T: {abs(p) == t}")
    print("ALL CHECKS PASS" if ok else "CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
