/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT.PlaneGraph

/-!
# FourCT.Examples — worked examples of the definitions

A wrong definition of "planar" can make every theorem downstream vacuous, and
the kernel will not notice. This file checks the definitions of
`FourCT.PlaneGraph` against a small case that can be verified by hand: the
**tetrahedron**, whose underlying graph is the complete graph on four
vertices.

What it establishes:

* `tetrahedron` is a `PlaneGraph`. That it is plain, satisfies the hypermap
  identity and is loopless is checked by `decide`. That it is planar, genus
  zero, follows from counting by `decide`: 6 edges, 4 vertices, 4 faces, one
  component, 12 darts, so `2·1 + 12 = 6 + 4 + 4`.
* Its underlying graph contains `K₄` (`k4Embedding`), so `K₄` is planar in
  the sense of `SimpleGraph.IsPlanar` (`isPlanar_K4`).
* `K₄` is not 3-colourable (`not_colorable_three_K4`). So
  `SimpleGraph.IsPlanar.colorable_four` is tight: a planar graph can need
  all four colours, and the definition of planarity is not so narrow as to
  make the theorem trivial.

The other direction needs no example. The theorem is proved, so no graph
that needs five colours can be `IsPlanar`: the definition cannot be too broad
in that way.

## Counting tools

Genus is defined through `Nat.card` of orbit quotients, which is not
computable, so it cannot be evaluated directly. `cycleCount_eq_card` makes
an orbit count a `Fintype.card`, which `decide` evaluates. `connected_of_reach`
proves connectivity from a computable set of darts reachable from a fixed
dart.
-/

namespace FourCT.Examples

open FourColor Equiv Equiv.Perm

/-! ### Counting tools -/

section Counting

variable {D : Type} [Fintype D] [DecidableEq D]

/-- The orbit relation of a permutation of a finite type is decidable, via
Mathlib's `Equiv.Perm.instDecidableRelSameCycle` (at most `card D`
iterations). -/
instance instDecidableRelSetoidSameCycle (f : Perm D) :
    DecidableRel (SameCycle.setoid f).r :=
  fun x y => instDecidableRelSameCycle f x y

/-- The number of orbits of a permutation, as a `Fintype.card` that `decide`
can evaluate. -/
theorem cycleCount_eq_card (f : Perm D) :
    cycleCount f = Fintype.card (Quotient (SameCycle.setoid f)) :=
  Nat.card_eq_fintype_card

/-- The darts reachable from `z` in at most `n` steps of `edge`, `node` or
`face`. Computable, so membership can be decided. -/
def reach (G : Hypermap D) (z : D) : ℕ → Finset D
  | 0 => {z}
  | n + 1 =>
    let s := reach G z n
    s ∪ s.image G.edge ∪ s.image G.node ∪ s.image G.face

omit [Fintype D] in
theorem eqvGen_of_mem_reach (G : Hypermap D) (z : D) :
    ∀ (n : ℕ) (x : D), x ∈ reach G z n → Relation.EqvGen G.GLink z x
  | 0, x, h => by
    rw [reach, Finset.mem_singleton] at h
    subst h
    exact Relation.EqvGen.refl _
  | n + 1, x, h => by
    simp only [reach, Finset.mem_union, Finset.mem_image] at h
    rcases h with ((h | ⟨y, hy, rfl⟩) | ⟨y, hy, rfl⟩) | ⟨y, hy, rfl⟩
    · exact eqvGen_of_mem_reach G z n x h
    · exact .trans _ _ _ (eqvGen_of_mem_reach G z n y hy) (.rel _ _ (Or.inl rfl))
    · exact .trans _ _ _ (eqvGen_of_mem_reach G z n y hy) (.rel _ _ (Or.inr (Or.inl rfl)))
    · exact .trans _ _ _ (eqvGen_of_mem_reach G z n y hy) (.rel _ _ (Or.inr (Or.inr rfl)))

omit [Fintype D] in
/-- A hypermap in which every dart is reachable from one dart is connected. -/
theorem connected_of_reach (G : Hypermap D) (z : D) (n : ℕ) (h : ∀ x, x ∈ reach G z n) :
    G.Connected := by
  show Nat.card (Quotient G.gcompSetoid) = 1
  refine Nat.card_eq_one_iff_unique.mpr ⟨⟨?_⟩, ⟨Quotient.mk _ z⟩⟩
  refine Quotient.ind fun a => Quotient.ind fun b => ?_
  exact Quotient.sound (Relation.EqvGen.trans _ _ _
    (Relation.EqvGen.symm _ _ (eqvGen_of_mem_reach G z n a (h a)))
    (eqvGen_of_mem_reach G z n b (h b)))

omit [DecidableEq D] in
/-- Euler's formula, used forwards: a connected hypermap whose darts, edges,
vertices and faces satisfy `2 + darts = edges + vertices + faces` has genus
zero. -/
theorem planar_of_counts (G : Hypermap D) (hc : G.Connected)
    (h : 2 + Fintype.card D = cycleCount G.edge + cycleCount G.node + cycleCount G.face) :
    G.Planar := by
  have hc' : G.compCount = 1 := hc
  show (G.EulerLhs - G.EulerRhs) / 2 = 0
  simp only [Hypermap.EulerLhs, Hypermap.EulerRhs, hc', Nat.card_eq_fintype_card]
  omega

end Counting

/-! ### The tetrahedron

Twelve darts, three at each of the four vertices: dart `3a + i` is the
`i`-th dart around vertex `a`. The cyclic orders around the vertices are
`0: 1 2 3`, `1: 0 3 2`, `2: 0 1 3`, `3: 0 2 1`. These are the orders of a
drawing of `K₄` in the plane, and the one choice among the sixteen that gives
four triangular faces. -/

/-- `edge`: the dart at the other end of the same edge. -/
def tetraEdge : Perm (Fin 12) :=
  ⟨![3, 6, 9, 0, 11, 7, 1, 5, 10, 2, 8, 4], ![3, 6, 9, 0, 11, 7, 1, 5, 10, 2, 8, 4],
    by decide, by decide⟩

/-- `node`: the next dart around the same vertex. -/
def tetraNode : Perm (Fin 12) :=
  ⟨![1, 2, 0, 4, 5, 3, 7, 8, 6, 10, 11, 9], ![2, 0, 1, 5, 3, 4, 8, 6, 7, 11, 9, 10],
    by decide, by decide⟩

/-- `face`: the next dart around the same face, `node⁻¹ ∘ edge`. -/
def tetraFace : Perm (Fin 12) :=
  ⟨![5, 8, 11, 2, 10, 6, 0, 4, 9, 1, 7, 3], ![6, 9, 3, 11, 7, 0, 5, 10, 1, 8, 4, 2],
    by decide, by decide⟩

/-- The tetrahedron as a hypermap. -/
def tetraMap : Hypermap (Fin 12) where
  edge := tetraEdge
  node := tetraNode
  face := tetraFace
  node_face_edge := by decide

theorem tetraMap_plain : tetraMap.Plain := ⟨by decide, by decide⟩

theorem tetraMap_connected : tetraMap.Connected :=
  connected_of_reach tetraMap 0 12 (by decide)

/-- 6 edges, 4 vertices, 4 faces. -/
theorem tetraMap_counts :
    cycleCount tetraMap.edge = 6 ∧ cycleCount tetraMap.node = 4 ∧
      cycleCount tetraMap.face = 4 := by
  simp only [cycleCount_eq_card]
  decide

theorem tetraMap_planar : tetraMap.Planar := by
  refine planar_of_counts tetraMap tetraMap_connected ?_
  obtain ⟨he, hn, hf⟩ := tetraMap_counts
  rw [he, hn, hf]
  decide

theorem tetraMap_loopless : tetraMap.Loopless := by
  intro x
  show ¬ tetraNode.SameCycle x (tetraEdge x)
  revert x
  decide

/-- **The tetrahedron**, as a plane graph. -/
def tetrahedron : PlaneGraph (Fin 12) := ⟨tetraMap, tetraMap_plain, tetraMap_planar⟩

/-- Vertex `a` of the tetrahedron: the orbit of dart `3a`. -/
def tetraVertex (a : Fin 4) : tetrahedron.Vertex := tetrahedron.vertexOf ⟨3 * a.val, by omega⟩

instance : DecidableEq tetrahedron.Vertex :=
  @Quotient.decidableEq _ _ (instDecidableRelSetoidSameCycle tetraNode)

theorem tetraVertex_injective : Function.Injective tetraVertex := by
  intro a b h
  rw [tetraVertex, tetraVertex, PlaneGraph.vertexOf_eq_iff] at h
  revert a b
  decide

theorem tetra_adj_iff (a b : Fin 4) :
    tetrahedron.graph.Adj (tetraVertex a) (tetraVertex b) ↔ a ≠ b := by
  rw [PlaneGraph.graph_adj]
  constructor
  · rintro ⟨hne, -⟩ rfl
    exact hne rfl
  · intro hab
    refine ⟨fun h => hab (tetraVertex_injective h), ?_⟩
    simp only [tetraVertex, PlaneGraph.vertexOf_eq_iff]
    revert a b
    decide

/-- `K₄` sits inside the tetrahedron's underlying graph. -/
def k4Embedding : (⊤ : SimpleGraph (Fin 4)) ↪g tetrahedron.graph where
  toFun := tetraVertex
  inj' := tetraVertex_injective
  map_rel_iff' := fun {a b} => (tetra_adj_iff a b).trans (SimpleGraph.top_adj a b).symm

/-- **`K₄` is planar.** -/
theorem isPlanar_K4 : (⊤ : SimpleGraph (Fin 4)).IsPlanar :=
  ⟨Fin 12, inferInstance, tetrahedron, tetraMap_loopless, ⟨k4Embedding⟩⟩

/-- **`K₄` needs four colours.** -/
theorem not_colorable_three_K4 : ¬ (⊤ : SimpleGraph (Fin 4)).Colorable 3 := by
  intro h
  have := h.chromaticNumber_le
  rw [SimpleGraph.chromaticNumber_top, Fintype.card_fin] at this
  norm_num at this

/-- The Four Colour Theorem, applied: `K₄` is 4-colourable, and this is the
best possible bound for planar graphs. -/
example : (⊤ : SimpleGraph (Fin 4)).Colorable 4 ∧ ¬ (⊤ : SimpleGraph (Fin 4)).Colorable 3 :=
  ⟨isPlanar_K4.colorable_four, not_colorable_three_K4⟩

end FourCT.Examples
