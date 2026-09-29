# A5 independent check: Tait count T and Penrose evaluation P

Independent second implementation, written without reading any other code in
`checks/a5/`, `search/b1/colour.py`, `search/b1/candidates.py` or `~/a5-proto/`.
Python 3 standard library only, exact integers throughout.

## Methods

Graphs are held as an edge list plus a rotation (`rot[v]` = the three edge ids
at v in cyclic order), which allows multigraphs and loops (used for the theta
graphs). Plantri ascii lines are parsed into this form; the listed neighbour
order is the rotation.

- **P (Penrose evaluation)**: tensor-network contraction of the Levi-Civita
  tensor `eps(c(e1), c(e2), c(e3))` at each vertex, arguments in rotation order,
  summed over all colours of every edge. Vertices are contracted one at a time
  in a greedy deterministic order (smallest resulting frontier, ties: more
  already-open edges, then lower index). The state is a dict from colour tuples
  of the open edges to integer partial sums. No enumeration of proper
  colourings.
- **T (Tait count)**: explicit iterative backtracking over edges (BFS edge
  order, per-vertex used-colour bitmasks), counting labelled proper
  3-edge-colourings.
- **Self-check** (on by default): the same contraction engine run with the
  "three distinct colours" indicator tensor must equal the backtracking T,
  otherwise the run aborts. It never failed.
- `test_bruteforce.py` compares P and T against a literal sum over all 3^E
  colourings for the small cases (named graphs with E <= 12, plantri N <= 6).
  All agree.

## Reproduce

Run this in WSL, with both .py files in the same directory:

    python3 run.py --plantri /home/claude/b1-out/bin/plantri --max 12 --out DIR
    python3 test_bruteforce.py --plantri /home/claude/b1-out/bin/plantri   # optional

Outputs `DIR/results-plane.txt` (`N index V P T`, where index counts from 0 in
plantri `-d -a N` output order), `DIR/results-named.txt` (`name V P T`) and
`DIR/timings.txt`.

## Bound reached and run times

All N = 4..12 were done (N = 12: 7595 graphs with 20 vertices). The run
covered 9150 graphs.

| N | graphs | V | max frontier | seconds (run A / run B) |
|---|---:|---:|---:|---:|
| 4 | 1 | 4 | 4 | 0.0 / 0.0 |
| 5 | 1 | 6 | 5 | 0.0 / 0.0 |
| 6 | 2 | 8 | 5 | 0.0 / 0.0 |
| 7 | 5 | 10 | 6 | 0.0 / 0.0 |
| 8 | 14 | 12 | 8 | 0.0 / 0.0 |
| 9 | 50 | 14 | 9 | 0.1 / 0.1 |
| 10 | 233 | 16 | 10 | 0.4 / 0.4 |
| 11 | 1249 | 18 | 10 | 2.7 / 3.0 |
| 12 | 7595 | 20 | 11 | 22.8 / 28.1 |

The times include the self-check. Total wall time was about 26 s for run A and
32 s for run B, on WSL Ubuntu with Python 3.14.4.

Two full runs gave byte-identical results files:

    sha256 results-plane.txt  8a768e5ffcd3846ce64d84cb884a246b8b214eab5f58968ac5514da1141777bd
    sha256 results-named.txt  58ef7ca292b7beb55df7e4f438cf1f28be7e761e3bec3dc5620f61ee3bc09b74
