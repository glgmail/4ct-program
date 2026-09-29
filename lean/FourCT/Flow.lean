/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT.Tait

/-!
# FourCT.Flow — nowhere-zero ℤ₂ × ℤ₂-flows

A **flow** on a graph gives each edge an element of an abelian group, so that
at every vertex the values on the edges there add up to zero. With values in
the Klein four-group `ℤ₂ × ℤ₂` (`FourColor.Color`) every element is its own
negative, so the edges need no direction. A flow is **nowhere-zero** when no
edge gets `0`.

Two classical correspondences, both proved here without the Four Colour
Theorem (checked by `checks/lean/fourct_independence.lean`):

* **Cubic maps, any surface:** the nowhere-zero ℤ₂ × ℤ₂-flows are exactly the
  proper 3-edge-colourings (`edgeColoring_iff_nowhereZeroFlow`). Three
  non-zero colours sum to zero exactly when they are different.
* **Any plain map on the sphere:** the face 4-colourings correspond to the
  nowhere-zero flows by Tait's rule `taitEdge`, which colours each edge with
  the sum of the colours on its two sides. This is Tutte's duality between
  colourings and flows (`fourColorable_iff_nowhereZeroFlow`).
  - Colouring to flow holds on every surface (`nowhereZeroFlow_taitEdge`).
  - Flow to colouring needs the sphere, through `FourCT.exists_facePotential`.
    It fails on the torus (`FourCT.Examples.theta_torus_flow`).

In Mathlib's vocabulary: a loopless plane graph is 4-colourable exactly when
its dual has a nowhere-zero ℤ₂ × ℤ₂-flow
(`FourCT.PlaneGraph.colorable_four_iff_nowhereZeroFlow_dual`).

## Main definitions

* `FourCT.NowhereZeroFlow G w`: `w` is a nowhere-zero ℤ₂ × ℤ₂-flow on `G`.

## Main results

* `FourCT.edgeColoring_iff_nowhereZeroFlow`
* `FourCT.nowhereZeroFlow_taitEdge`, `FourCT.exists_coloring_of_nowhereZeroFlow`,
  `FourCT.fourColorable_iff_nowhereZeroFlow`
* `FourCT.PlaneGraph.colorable_four_iff_nowhereZeroFlow_dual`
-/

namespace FourCT

open FourColor Equiv Equiv.Perm

variable {D : Type*} [Fintype D] [DecidableEq D]

/-- A **nowhere-zero ℤ₂ × ℤ₂-flow** on a hypermap: each edge gets a colour
(both of its darts carry it) that is never `0`, and the colours of the darts
around each vertex add up to `0`. Every element of ℤ₂ × ℤ₂ is its own
negative, so edges need no direction; a loop meets its vertex twice, so it
contributes `0`. -/
structure NowhereZeroFlow (G : Hypermap D) (w : D → Color) : Prop where
  /-- The value belongs to the edge: both of its darts carry it. -/
  edge : ∀ x, w (G.edge x) = w x
  /-- No edge gets `0`. -/
  ne_zero : ∀ x, w x ≠ 0
  /-- The values around each vertex add up to `0`. -/
  sum_node : ∀ x, ∑ y ∈ Finset.univ.filter (fun y => G.node.SameCycle x y), w y = 0

instance (G : Hypermap D) (w : D → Color) : Decidable (NowhereZeroFlow G w) :=
  decidable_of_iff ((∀ x, w (G.edge x) = w x) ∧ (∀ x, w x ≠ 0) ∧
      ∀ x, ∑ y ∈ Finset.univ.filter (fun y => G.node.SameCycle x y), w y = 0)
    ⟨fun ⟨a, b, c⟩ => ⟨a, b, c⟩, fun ⟨a, b, c⟩ => ⟨a, b, c⟩⟩

/-! ### Cubic maps: flows are edge colourings -/

/-- **On a cubic map, the nowhere-zero ℤ₂ × ℤ₂-flows are exactly the proper
3-edge-colourings**, on any surface. At a vertex, three non-zero colours add
up to zero exactly when they are pairwise different. -/
theorem edgeColoring_iff_nowhereZeroFlow {G : Hypermap D} (hc : G.Cubic) {e : D → Color} :
    EdgeColoring G e ↔ NowhereZeroFlow G e := by
  constructor
  · intro he
    exact ⟨he.edge, he.ne_zero, he.sum_node_eq_zero hc⟩
  · intro hw
    refine ⟨hw.edge, hw.ne_zero, fun x h => ?_⟩
    -- Two equal colours at a vertex cancel, leaving the third to be `0`.
    have hs := hw.sum_node x
    rw [sum_sameCycle_node_of_cubic hc, h, Color.add_self, zero_add] at hs
    exact hw.ne_zero _ hs

/-! ### Face colourings and flows -/

/-- Tait's rule applied to any face labelling gives values summing to zero at
every vertex, on any surface. Going round a vertex, each face there is met
from both of its sides. -/
theorem sum_node_taitEdge (G : Hypermap D) {k : D → Color} (hk : ∀ x, k (G.face x) = k x)
    (x : D) :
    ∑ y ∈ Finset.univ.filter (fun y => G.node.SameCycle x y), taitEdge G k y = 0 := by
  -- Across the edge of `y` lies the face of `node⁻¹ y`.
  have hke : ∀ y, k (G.edge y) = k (G.node⁻¹ y) := fun y => by
    rw [← hk (G.edge y), Perm.eq_inv_iff_eq.2 (G.edgeK y)]
  simp only [taitEdge, hke, Finset.sum_add_distrib]
  rw [sum_sameCycle_inv G.node x k]
  exact Color.add_self _

/-- **A face 4-colouring gives a nowhere-zero ℤ₂ × ℤ₂-flow** by Tait's rule,
on any surface. -/
theorem nowhereZeroFlow_taitEdge {G : Hypermap D} (hG : G.Plain) {k : D → Color}
    (hk : G.Coloring k) : NowhereZeroFlow G (taitEdge G k) where
  edge x := by simp only [taitEdge, hG.edge_edge, add_comm]
  ne_zero x := by
    simp only [taitEdge, ne_eq, Color.add_eq_zero_iff]
    exact (hk.edge x).symm
  sum_node := sum_node_taitEdge G hk.face

/-- **On the sphere, every nowhere-zero ℤ₂ × ℤ₂-flow comes from a face
4-colouring** by Tait's rule. `FourCT.exists_facePotential` gives face colours
whose sums across the edges are the flow's values. Adjacent faces then differ,
because no value is zero. -/
theorem exists_coloring_of_nowhereZeroFlow {G : Hypermap D} (hG : G.Plain) (hp : G.Planar)
    {w : D → Color} (hw : NowhereZeroFlow G w) : ∃ k, G.Coloring k ∧ taitEdge G k = w := by
  obtain ⟨k, hkf, hke⟩ := exists_facePotential G hG hp w hw.edge hw.sum_node
  refine ⟨k, ⟨fun x h => hw.ne_zero x ?_, hkf⟩, funext hke⟩
  rw [← hke x, h, Color.add_self]

/-- **Tutte's duality, on the sphere**: a plain genus-0 map has a face
4-colouring exactly when it has a nowhere-zero ℤ₂ × ℤ₂-flow. -/
theorem fourColorable_iff_nowhereZeroFlow {G : Hypermap D} (hG : G.Plain) (hp : G.Planar) :
    G.FourColorable ↔ ∃ w, NowhereZeroFlow G w := by
  constructor
  · rintro ⟨k, hk⟩
    exact ⟨_, nowhereZeroFlow_taitEdge hG hk⟩
  · rintro ⟨w, hw⟩
    obtain ⟨k, hk, -⟩ := exists_coloring_of_nowhereZeroFlow hG hp hw
    exact ⟨k, hk⟩

/-! ### In Mathlib's vocabulary -/

namespace PlaneGraph

variable {D : Type} [Fintype D] [DecidableEq D]

/-- **A loopless plane graph is 4-colourable (Mathlib's `Colorable 4`) exactly
when its dual has a nowhere-zero ℤ₂ × ℤ₂-flow.**

The dual's edges cross the edges of `P`, and its vertices are the faces of
`P`. So the right-hand side says: `P`'s edges can be given non-zero colours so
that the colours around every face of `P` add up to zero. -/
theorem colorable_four_iff_nowhereZeroFlow_dual (P : PlaneGraph D) (hl : P.map.Loopless) :
    P.graph.Colorable 4 ↔ ∃ w, NowhereZeroFlow P.map.dual w := by
  rw [← P.graphFourColorable_iff hl, ← Hypermap.fourColorable_dual_iff]
  exact fourColorable_iff_nowhereZeroFlow ((Hypermap.plain_dual _).2 P.plain)
    ((Hypermap.planar_dual _).2 P.planar)

end PlaneGraph

end FourCT
