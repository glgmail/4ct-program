/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT.Tait

/-!
# Tait's reformulation of the Four Colour Theorem

**Every bridgeless plane cubic map has a proper 3-edge-colouring.**

This file holds the statement and nothing else. Its equivalence with the
Four Colour Theorem, and its proof from the base port, are in
`FourCT/Equivalences.lean`. Needs Gabriel's written sign-off (see
`Statements/README.md`).

## Reading the statement

* `D` is a finite type of **darts**, the half-edges: one dart for each end of
  each edge.
* `P : FourCT.PlaneGraph D` is a **plane graph**: a graph drawn on the
  sphere, given by three permutations of the darts (`edge` swaps the two
  darts of an edge, `node` goes round a vertex, `face` goes round a face).
  Every edge has two darts, and the genus is zero. Parallel edges and loops
  are allowed.
* `P.map.Bridgeless`: no edge has the same face on both of its sides. For a
  plane graph that means no edge whose removal would disconnect it. Without
  this the statement is false: a cubic graph with a bridge has no proper
  3-edge-colouring (`FourCT.Examples.dumbbell`).
* `P.map.Cubic`: every vertex has exactly three darts, so three edge-ends.
* `FourCT.EdgeColoring P.map e`: `e` colours each edge with one of the three
  non-zero colours of the Klein four-group, and the edge-ends at every vertex
  get different colours. At a vertex of degree three, that means three
  different colours.

This is the edge-colouring side of Tait's correspondence, stated for cubic
maps. The textbook route to the vertex form goes through the dual of a
triangulation. `FourCT/Equivalences.lean` uses the base port's reduction to
cubic maps instead.
-/

namespace Statements

open FourCT

/-- **Tait's reformulation of the Four Colour Theorem**: every bridgeless plane
cubic map has a proper 3-edge-colouring. -/
def Tait : Prop :=
  ∀ (D : Type) [Fintype D] (P : PlaneGraph D),
    P.map.Bridgeless → P.map.Cubic → ∃ e, EdgeColoring P.map e

end Statements
