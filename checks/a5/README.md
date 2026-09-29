# checks/a5/ — Penrose's formula, computed twice

Task A5 (#39). Penrose's evaluation `P` of a cubic map sums, over every colouring
of the edges with `0, 1, 2`, the product over the vertices of the Levi-Civita
symbol of the three colours in rotation order. The Tait count `T` is the number
of proper 3-edge-colourings. Penrose's formula, proved in Lean as
`FourCT.penrose_eq`, says that on the sphere `P = (-1)^(V/2) T`.

These scripts compute `P` and `T` two independent ways and test the formula,
including the sign.

## The two implementations

| | Implementation A: `penrose.py` | Implementation B: `independent/run.py` |
| --- | --- | --- |
| P | enumerates proper colourings by backtracking and adds their signs | contracts the Levi-Civita tensor network over all colourings, vertex by vertex |
| T | the same backtracking | a separate backtracking, with a self-check by contracting the "three different colours" tensor |
| Written by | the main session | a separate agent that never read `penrose.py`, `search/b1/colour.py` or the prototype; see `independent/README.md` |

Both use the Python standard library only, with exact integers.

## One command each

In WSL, from the repository root, with plantri built by `search/b1/run.py`:

```bash
python3 checks/a5/penrose.py --plantri PLANTRI --max 12 --out DIR_A
python3 checks/a5/independent/run.py --plantri PLANTRI --max 12 --out DIR_B
python3 checks/a5/compare.py DIR_A DIR_B
```

Implementation A takes about 70 s and B about 30 s. Two runs of each gave
byte-identical files:

```
8a768e5ffcd3846ce64d84cb884a246b8b214eab5f58968ac5514da1141777bd  results-plane.txt       (A and B)
58ef7ca292b7beb55df7e4f438cf1f28be7e761e3bec3dc5620f61ee3bc09b74  results-named.txt       (A and B)
f892f46131647e61e7248d8da1ca3b376ed0e11cada31e0fe19ca9b36fdb81b8  results-embeddings.txt  (A only)
```

## What they show (`result.txt`, `results/`)

- **The two implementations agree** on all 9,150 plane cubic graphs: the duals
  of the 3-connected triangulations with 4 to 12 vertices, so up to 20
  vertices.
- **Penrose's formula holds with its sign on every one of them**, and every one
  has a Tait colouring.
- **Named graphs:**

  | Graph | V | P | T | Comment |
  | --- | ---: | ---: | ---: | --- |
  | theta, on the sphere | 2 | -6 | 6 | the formula |
  | theta, on the torus | 2 | +6 | 6 | the sign fails in genus one |
  | K4 | 4 | 6 | 6 | |
  | K3,3 | 6 | 0 | 12 | the terms cancel |
  | Petersen | 10 | 0 | 0 | no Tait colouring |
  | Wagner (Möbius ladder, 8 vertices) | 8 | -18 | 18 | non-planar, but \|P\| = T |

- **Every rotation system** of the plane graphs with at most 12 vertices, and
  of K3,3, Petersen and Wagner (`results-embeddings.txt`):
  - Reversing the rotation at one vertex negates every term at once, so it
    changes only the overall sign.
  - For a planar graph, every embedding has `|P| = T`, and only the genus-0
    ones are guaranteed the formula's sign. Of the other embeddings, about
    half have the other sign.
  - For K3,3, every embedding (genus 1 or 2) has `P = 0` against `T = 12`: its
    Tait colourings come in cancelling pairs. So off the sphere the formula can
    fail in magnitude too, not only in sign.
