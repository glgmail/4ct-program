/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT.PlaneGraph
import Mathlib.Data.ZMod.Basic

/-!
# The flow reformulation of the Four Colour Theorem

**Every bridgeless plane graph has a nowhere-zero `ℤ₂ × ℤ₂`-flow.**

This file holds the statement and the one definition it needs, and nothing
else. Its equivalence with the Four Colour Theorem, and its proof from the base
port, are in `FourCT/Equivalences.lean`. Needs Gabriel's written sign-off (see
`Statements/README.md`).

## Reading the statement

* `D`, `P : FourCT.PlaneGraph D`: a plane graph on the darts `D`, as in
  `Statements/Tait.lean`. Parallel edges and loops are allowed.
* `P.map.Bridgeless`: no edge has the same face on both of its sides. For a
  plane graph that means no edge whose removal would disconnect it. Without
  this the statement is false: across a bridge the flow would have to be `0`
  (`FourCT.Examples.dumbbell`).
* `IsNowhereZeroFlow P w`: `w` is a nowhere-zero flow with values in Mathlib's
  `ZMod 2 × ZMod 2`.

**The flow is on the graph `P` itself**, not on its dual. By duality it
corresponds to 4-colourings of `P`'s faces, which are the vertices of the dual.

**The orientation convention** is the standard one for flows on maps. Values
sit on darts, a dart and its reverse carry opposite values
(`w (edge x) = - w x`), and the values leaving each vertex sum to zero. In
`ZMod 2 × ZMod 2` every element is its own negative, so the statement does not
depend on how the edges are directed. `FourCT.Equivalences` proves the
unoriented form equivalent.
-/

namespace Statements

open FourCT

/-- A **nowhere-zero `ZMod 2 × ZMod 2`-flow** on the plane graph `P`: values on
the darts such that the two darts of an edge carry opposite values, no dart
carries `0`, and the values of the darts at each vertex sum to `0`. -/
def IsNowhereZeroFlow {D : Type} [Fintype D] [DecidableEq D] (P : PlaneGraph D)
    (w : D → ZMod 2 × ZMod 2) : Prop :=
  (∀ x, w (P.map.edge x) = -w x) ∧ (∀ x, w x ≠ 0) ∧
    ∀ x, ∑ y ∈ Finset.univ.filter (fun y => P.map.node.SameCycle x y), w y = 0

/-- **The flow reformulation of the Four Colour Theorem**: every bridgeless
plane graph has a nowhere-zero `ZMod 2 × ZMod 2`-flow. -/
def Flows : Prop :=
  ∀ (D : Type) [Fintype D] [DecidableEq D] (P : PlaneGraph D),
    P.map.Bridgeless → ∃ w, IsNowhereZeroFlow P w

end Statements
