/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT.PlaneGraph

/-!
# Penrose's reformulation of the Four Colour Theorem

**The Penrose evaluation of every bridgeless plane cubic map is non-zero.**

This file holds the statement and the definitions it needs, and nothing else.
Penrose's formula, which makes it equivalent to the Four Colour Theorem, is in
`FourCT/Penrose.lean`, and the equivalence itself in `FourCT/Equivalences.lean`.
Needs Gabriel's sign-off (see `Statements/README.md`).

## Reading the statement

* `levi a b c` is the Levi-Civita symbol on three colours `0, 1, 2`: `0` if two
  arguments are equal, `+1` if `(a, b, c)` is a cyclic rotation of `(0, 1, 2)`,
  and `-1` if it is a cyclic rotation of `(0, 2, 1)`.
* `penrose G` is Penrose's contraction of the Levi-Civita tensor over the map
  `G`.
  - It sums over every colouring `c` of the edges with the colours `0, 1, 2`.
    These are written as colourings of the darts that agree on the two darts
    of each edge, and they need not be proper.
  - Each term is a product of `levi` of the three colours met going round a
    vertex, in the order `node` gives. That order is the drawing's cyclic
    order, so the evaluation depends on the drawing, not only on the graph.
  - The product runs over darts, so each vertex contributes its factor once
    for each of its three darts. In a cubic map the three factors are equal,
    and since `levi` is `0` or `±1`, their product is that factor again.
* `P : FourCT.PlaneGraph D`, `P.map.Bridgeless` and `P.map.Cubic` are as in
  `Statements/Tait.lean`: a plane graph (finite, drawn on the sphere, parallel
  edges and loops allowed), with no bridge, and with three darts at every
  vertex. Without "bridgeless" the statement is false: a cubic map with a
  bridge has no Tait colouring, so its evaluation is `0`.

Penrose's formula (`FourCT.penrose_eq`) says that for a plane cubic map the
evaluation is `(-1) ^ (V / 2)` times the number of Tait colourings, where `V` is
the number of vertices. So the statement says every bridgeless plane cubic map
has a Tait colouring. The sign is needed only for the formula, not for this
statement.
-/

namespace Statements

open FourCT

/-- The **Levi-Civita symbol** on three colours: `0` if two of `a, b, c` are
equal, `+1` if `(a, b, c)` is a cyclic rotation of `(0, 1, 2)`, `-1` otherwise. -/
def levi (a b c : Fin 3) : ℤ :=
  if a = b ∨ b = c ∨ c = a then 0 else if b = a + 1 then 1 else -1

/-- **Penrose's evaluation** of a hypermap: over all colourings of the edges
with three colours, the sum of the products of `levi` of the colours round
each vertex. -/
def penrose {D : Type*} [Fintype D] [DecidableEq D] (G : FourColor.Hypermap D) : ℤ :=
  ∑ c ∈ Finset.univ.filter (fun c : D → Fin 3 => ∀ x, c (G.edge x) = c x),
    ∏ x, levi (c x) (c (G.node x)) (c (G.node (G.node x)))

/-- **Penrose's reformulation of the Four Colour Theorem**: every bridgeless
plane cubic map has a non-zero Penrose evaluation. -/
def Penrose : Prop :=
  ∀ (D : Type) [Fintype D] [DecidableEq D] (P : PlaneGraph D),
    P.map.Bridgeless → P.map.Cubic → penrose P.map ≠ 0

end Statements
