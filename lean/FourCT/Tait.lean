/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT.Potential
import FourCT.PlaneGraph

/-!
# FourCT.Tait — Tait's correspondence

Tait (1880): the vertices of a plane triangulation can be 4-coloured exactly
when the edges of its dual, a cubic map, can be 3-coloured so that the three
edges at each vertex get different colours.

Take the four colours to be the Klein four-group `ℤ₂ × ℤ₂` (`FourColor.Color`),
and colour each edge by the *sum* of the colours at its two ends. The two ends
differ, so the sum is one of the three non-zero colours. Around a triangle
with colours `a`, `b`, `c` the edges get `a + b`, `b + c` and `c + a`, which
are pairwise different. So a vertex colouring gives an edge colouring
(`edgeColoring_taitEdge`), on any surface. The converse needs the sphere:
given the edge colours, recover the vertex colours by adding up edge colours
along a path. On the sphere the result does not depend on the path
(`FourCT.exists_facePotential`); on a torus it can
(`FourCT.Examples.theta_torus`).

The port states colourings for the faces of a hypermap, so the cubic map is
the primary object here, and its faces are the triangulation's vertices.

Nothing here uses the Four Colour Theorem. For planar maps both sides of the
correspondence are true, since the theorem is proved, so an "equivalence"
proved from it would be empty. The CI check `checks/lean/fourct_independence.lean`
confirms that no theorem in this file depends on the theorem or on the
reducibility and unavoidability results that prove it.

## Main definitions

* `FourCT.EdgeColoring G e`: `e` is a proper 3-edge-colouring of `G`.
* `FourCT.taitEdge G k`: the edge colouring of a face colouring `k`.
* `FourCT.PlaneGraph.IsTriangulation`: every face of a plane graph has three
  darts.

## Main results

* `FourCT.edgeColoring_taitEdge`: a face 4-colouring of a cubic map gives a
  proper 3-edge-colouring. No planarity needed.
* `FourCT.exists_coloring_of_edgeColoring`: on the sphere, every proper
  3-edge-colouring of a cubic map comes from a face 4-colouring.
* `FourCT.taitEdge_eq_taitEdge_iff_of_connected`: on a connected map, two face
  colourings give the same edge colouring exactly when they differ by adding a
  constant colour. So the correspondence is four-to-one.
* `FourCT.PlaneGraph.tait`: **Tait's theorem.** A loopless plane
  triangulation has a proper vertex 4-colouring (in Mathlib's sense) exactly
  when its cubic dual has a proper 3-edge-colouring.
-/

namespace FourCT

open FourColor Equiv Equiv.Perm

variable {D : Type*}

/-! ### Edge colourings -/

/-- A **proper 3-edge-colouring** of a hypermap: each edge gets one of the three
non-zero colours (`e` is constant on the edge, and never `0`), and consecutive
darts around a vertex get different colours. At a vertex of degree three that
says the three edges there get three different colours. -/
structure EdgeColoring (G : Hypermap D) (e : D → Color) : Prop where
  /-- The colour belongs to the edge: both of its darts carry it. -/
  edge : ∀ x, e (G.edge x) = e x
  /-- Only the three non-zero colours are used. -/
  ne_zero : ∀ x, e x ≠ 0
  /-- Consecutive darts around a vertex have different colours. -/
  node : ∀ x, e (G.node x) ≠ e x

instance [Fintype D] [DecidableEq D] (G : Hypermap D) (e : D → Color) :
    Decidable (EdgeColoring G e) :=
  decidable_of_iff ((∀ x, e (G.edge x) = e x) ∧ (∀ x, e x ≠ 0) ∧ ∀ x, e (G.node x) ≠ e x)
    ⟨fun ⟨a, b, c⟩ => ⟨a, b, c⟩, fun ⟨a, b, c⟩ => ⟨a, b, c⟩⟩

/-- **Tait's edge colouring** of a face colouring `k`: the dart `x` gets the sum
of the colours of the faces on the two sides of its edge. -/
def taitEdge (G : Hypermap D) (k : D → Color) (x : D) : Color := k x + k (G.edge x)

/-- In a cubic hypermap a vertex has exactly the three darts `x`, `node x`,
`node (node x)`. -/
theorem sameCycle_node_iff {G : Hypermap D} (hc : G.Cubic) {x y : D} :
    G.node.SameCycle x y ↔ y = x ∨ y = G.node x ∨ y = G.node (G.node x) := by
  have hn3 : ∀ z, G.node (G.node (G.node z)) = z := fun z =>
    hc.node_node_node z
  have hinv : ∀ z, G.node⁻¹ z = G.node (G.node z) := fun z =>
    Perm.inv_eq_iff_eq.2 (hn3 z).symm
  refine ⟨mem_of_sameCycle (S := {y | y = x ∨ y = G.node x ∨ y = G.node (G.node x)})
    (Or.inl rfl) ?_ ?_, ?_⟩
  · rintro z (rfl | rfl | rfl) <;> simp [hn3]
  · rintro z (rfl | rfl | rfl) <;> simp [hinv, hn3]
  · rintro (rfl | rfl | rfl)
    · exact SameCycle.refl _ _
    · exact G.cnode_node x
    · exact (G.cnode_node x).trans (G.cnode_node _)

/-! ### From face colourings to edge colourings -/

/-- **A face 4-colouring of a cubic map gives a proper 3-edge-colouring**
(`taitEdge`). This direction holds on every surface. -/
theorem edgeColoring_taitEdge {G : Hypermap D} (hG : G.Plain) (hc : G.Cubic) {k : D → Color}
    (hk : G.Coloring k) : EdgeColoring G (taitEdge G k) where
  edge x := by simp only [taitEdge, hG.edge_edge, add_comm]
  ne_zero x := by
    simp only [taitEdge, ne_eq, Color.add_eq_zero_iff]
    exact (hk.edge x).symm
  node x := by
    -- Across the edge of `y` lies the face of `node⁻¹ y`.
    have hke : ∀ y, k (G.edge y) = k (G.node⁻¹ y) := fun y => by
      rw [← hk.face (G.edge y), Perm.eq_inv_iff_eq.2 (G.edgeK y)]
    have hinv : ∀ y, G.node⁻¹ y = G.node (G.node y) := fun y =>
      Perm.inv_eq_iff_eq.2 (hc.node_node_node y).symm
    have hni : ∀ y, G.node⁻¹ (G.node y) = y := fun y => by simp
    intro h
    simp only [taitEdge, hke, hni] at h
    rw [hinv] at h
    -- The faces of `node x` and `node (node x)` would then have the same colour,
    -- but they are on the two sides of the edge of `node (node x)`.
    have h' : k (G.node x) = k (G.node (G.node x)) := by
      rw [add_comm] at h
      exact add_left_cancel h
    have := hk.edge (G.node (G.node x))
    rw [hke, hni] at this
    exact this h'

/-! ### From edge colourings to face colourings, on the sphere -/

/-- Three different non-zero colours add up to zero. -/
theorem add_three_eq_zero : ∀ a b c : Color, a ≠ 0 → b ≠ 0 → c ≠ 0 →
    a ≠ b → b ≠ c → c ≠ a → a + b + c = 0 := by decide

/-- In a cubic hypermap, a sum over the darts at the vertex of `x` has the three
terms `x`, `node x`, `node (node x)`. -/
theorem sum_sameCycle_node_of_cubic [Fintype D] [DecidableEq D] {G : Hypermap D}
    (hc : G.Cubic) {M : Type*} [AddCommMonoid M] (f : D → M) (x : D) :
    ∑ y ∈ Finset.univ.filter (fun y => G.node.SameCycle x y), f y =
      f x + f (G.node x) + f (G.node (G.node x)) := by
  have hn3 : ∀ x, G.node (G.node (G.node x)) = x := fun x => hc.node_node_node x
  have hne : ∀ x, G.node x ≠ x := fun x => hc.node_ne x
  have hS : Finset.univ.filter (fun y => G.node.SameCycle x y) =
      {x, G.node x, G.node (G.node x)} := by
    ext y
    simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_insert,
      Finset.mem_singleton]
    exact sameCycle_node_iff hc
  have h1 : x ≠ G.node x := (hne x).symm
  have h2 : x ≠ G.node (G.node x) := fun h => hne x <|
    calc G.node x = G.node (G.node (G.node x)) := by rw [← h]
      _ = x := hn3 x
  have h3 : G.node x ≠ G.node (G.node x) := fun h => hne x (G.node.injective h).symm
  rw [hS, Finset.sum_insert (by simp [h1, h2]), Finset.sum_insert (by simp [h3]),
    Finset.sum_singleton, ← add_assoc]

/-- The colours of a proper 3-edge-colouring of a cubic map sum to zero at every
vertex: they are the three non-zero colours. -/
theorem EdgeColoring.sum_node_eq_zero [Fintype D] [DecidableEq D] {G : Hypermap D}
    (hc : G.Cubic) {e : D → Color} (he : EdgeColoring G e) (x : D) :
    ∑ y ∈ Finset.univ.filter (fun y => G.node.SameCycle x y), e y = 0 := by
  rw [sum_sameCycle_node_of_cubic hc]
  exact add_three_eq_zero _ _ _ (he.ne_zero _) (he.ne_zero _) (he.ne_zero _)
    (he.node x).symm (he.node _).symm
    (fun h => he.node (G.node (G.node x)) (by rw [hc.node_node_node, h]))

/-- **On the sphere, every proper 3-edge-colouring of a cubic map comes from a
face 4-colouring.** The three colours at a vertex are the three non-zero
colours, which sum to zero, so `FourCT.exists_facePotential` gives face colours
whose sums across the edges are the edge colours. Adjacent faces then differ,
because an edge colour is never zero. -/
theorem exists_coloring_of_edgeColoring [Fintype D] [DecidableEq D] {G : Hypermap D}
    (hG : G.Plain) (hc : G.Cubic) (hp : G.Planar) {e : D → Color} (he : EdgeColoring G e) :
    ∃ k, G.Coloring k ∧ taitEdge G k = e := by
  obtain ⟨k, hkf, hke⟩ := exists_facePotential G hG hp e he.edge (he.sum_node_eq_zero hc)
  refine ⟨k, ⟨fun x h => he.ne_zero x ?_, hkf⟩, funext hke⟩
  rw [← hke x, h, Color.add_self]

/-! ### The correspondence is four-to-one -/

private theorem color_add_add : ∀ a b c d : Color, a + b = c + d ↔ a + c = b + d := by decide

private theorem color_eq_add : ∀ a b c : Color, a + b = c ↔ b = a + c := by decide

/-- Two face colourings give the same edge colouring exactly when their sum is
constant on each component of the map. -/
theorem taitEdge_eq_taitEdge_iff {G : Hypermap D} {k k' : D → Color}
    (hk : ∀ x, k (G.face x) = k x) (hk' : ∀ x, k' (G.face x) = k' x) :
    taitEdge G k = taitEdge G k' ↔
      ∀ x y, Relation.EqvGen G.GLink x y → k x + k' x = k y + k' y := by
  constructor
  · intro h
    have he : ∀ x, k (G.edge x) + k' (G.edge x) = k x + k' x := fun x => by
      have := congrFun h x
      simp only [taitEdge] at this
      exact ((color_add_add _ _ _ _).1 this).symm
    have hf : ∀ x, k (G.face x) + k' (G.face x) = k x + k' x := fun x => by rw [hk, hk']
    have hn : ∀ x, k (G.node x) + k' (G.node x) = k x + k' x := fun x => by
      rw [← he (G.node x), ← hf (G.edge (G.node x)), G.nodeK]
    exact fun x y hxy => eq_of_eqvGen G (fun x => k x + k' x) he hn hf hxy
  · intro h
    funext x
    simp only [taitEdge]
    exact (color_add_add _ _ _ _).2 (h x (G.edge x) (.rel _ _ (G.glink_edge x)))

/-- **On a connected map, the correspondence is four-to-one**: two face
colourings give the same edge colouring exactly when one is the other plus a
constant colour. -/
theorem taitEdge_eq_taitEdge_iff_of_connected [Finite D] {G : Hypermap D}
    (hconn : G.Connected) {k k' : D → Color}
    (hk : ∀ x, k (G.face x) = k x) (hk' : ∀ x, k' (G.face x) = k' x) :
    taitEdge G k = taitEdge G k' ↔ ∃ c : Color, ∀ x, k' x = k x + c := by
  rw [taitEdge_eq_taitEdge_iff hk hk']
  have hsub : Subsingleton (Quotient G.gcompSetoid) := (Nat.card_eq_one_iff_unique.1 hconn).1
  have hrel : ∀ x y, Relation.EqvGen G.GLink x y := fun x y =>
    Quotient.exact (Subsingleton.elim (Quotient.mk G.gcompSetoid x) (Quotient.mk _ y))
  constructor
  · intro h
    rcases isEmpty_or_nonempty D with hD | hD
    · exact ⟨0, fun x => isEmptyElim x⟩
    · obtain ⟨x₀⟩ := hD
      exact ⟨k x₀ + k' x₀, fun x => (color_eq_add _ _ _).1 (h x x₀ (hrel x x₀))⟩
  · rintro ⟨c, hc⟩ x y _
    rw [hc x, hc y, ← add_assoc, ← add_assoc, Color.add_self, Color.add_self]

/-! ### Triangulations -/

namespace PlaneGraph

variable {D : Type} [Fintype D]

/-- A **plane triangulation**: every face of the plane graph is bounded by
exactly three darts, hence three edges. -/
structure IsTriangulation (T : PlaneGraph D) : Prop where
  /-- Going three steps around a face returns to the start. -/
  face_face_face : ∀ x, T.map.face (T.map.face (T.map.face x)) = x
  /-- No face has only one dart. -/
  face_ne : ∀ x, T.map.face x ≠ x

instance [DecidableEq D] (T : PlaneGraph D) : Decidable T.IsTriangulation :=
  decidable_of_iff ((∀ x, T.map.face (T.map.face (T.map.face x)) = x) ∧ ∀ x, T.map.face x ≠ x)
    ⟨fun ⟨a, b⟩ => ⟨a, b⟩, fun ⟨a, b⟩ => ⟨a, b⟩⟩

/-- The dual of a triangulation is cubic: the dual's vertices are the
triangulation's faces. -/
theorem IsTriangulation.cubic_dual {T : PlaneGraph D} (ht : T.IsTriangulation) :
    T.map.dual.Cubic where
  node_node_node x _ := by
    simp only [Hypermap.dual_node]
    rw [Perm.inv_eq_iff_eq, Perm.inv_eq_iff_eq, Perm.inv_eq_iff_eq, ht.face_face_face]
  node_ne x _ := by
    simp only [Hypermap.dual_node]
    intro h
    rw [Perm.inv_eq_iff_eq] at h
    exact ht.face_ne x h.symm

/-- **Tait's theorem.** A loopless plane triangulation `T` has a proper vertex
4-colouring (Mathlib's `SimpleGraph.Colorable` for its underlying graph)
exactly when its cubic dual has a proper 3-edge-colouring.

The dual's edges are `T`'s edges, and its vertices are `T`'s triangles. So the
right-hand side says: `T`'s edges can be coloured with three colours so that
every triangle has three different colours on its edges. -/
theorem tait [DecidableEq D] (T : PlaneGraph D) (hl : T.map.Loopless)
    (ht : T.IsTriangulation) :
    T.graph.Colorable 4 ↔ ∃ e, EdgeColoring T.map.dual e := by
  rw [← T.graphFourColorable_iff hl, ← Hypermap.fourColorable_dual_iff]
  have hpd : T.map.dual.Plain := (Hypermap.plain_dual _).2 T.plain
  constructor
  · rintro ⟨k, hk⟩
    exact ⟨_, edgeColoring_taitEdge hpd ht.cubic_dual hk⟩
  · rintro ⟨e, he⟩
    obtain ⟨k, hk, -⟩ := exists_coloring_of_edgeColoring hpd ht.cubic_dual
      ((Hypermap.planar_dual _).2 T.planar) he
    exact ⟨k, hk⟩

end PlaneGraph

end FourCT
