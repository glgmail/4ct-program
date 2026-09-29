/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT.PlaneGraph
import FourCT.Flow
import Mathlib.Combinatorics.SimpleGraph.Hasse

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
  the sense of `SimpleGraph.IsPlanar` (`isPlanar_K4`). Hence **every simple
  graph on at most four vertices is planar** (`isPlanar_of_card_le_four`).
  That includes paths, graphs with isolated vertices and disconnected
  graphs, the cases a combinatorial definition of planarity most easily gets
  wrong.
* `K₄` is not 3-colourable (`not_colorable_three_K4`). So
  `SimpleGraph.IsPlanar.colorable_four` is tight: a planar graph can need
  all four colours, and the definition of planarity is not so narrow as to
  make the theorem trivial.
* **Tait's correspondence on the tetrahedron.** It is a triangulation
  (`tetrahedron_isTriangulation`). Colouring its vertices `0, c1, c2, c3`
  gives, by Tait's rule, the edge colouring by the three perfect matchings of
  `K₄` (`taitEdge_tetraVertexColors`), which is a proper 3-edge-colouring of
  the dual (`tetraEdgeColors_edgeColoring`). Tait's theorem then gives the
  4-colourability of `K₄` without the Four Colour Theorem.
* **The sphere is needed** (`theta_torus`). The theta graph (two vertices
  joined by three edges) drawn on the torus has a single face, of genus one.
  Its edges have a proper 3-edge-colouring, but its faces have no
  4-colouring, since the one face meets itself across every edge. So the
  genus-zero hypothesis of `FourCT.exists_coloring_of_edgeColoring` cannot be
  dropped.
* **Flows.** The tetrahedron's edge colouring is a nowhere-zero
  ℤ₂ × ℤ₂-flow on its dual (`tetraEdgeColors_flow`, by `decide`).
  - **A map that is not cubic:** a triangle, with three vertices of degree
    two. Every edge coloured `c1` is a flow, and it comes by Tait's rule from
    colouring the inside `0` and the outside `c1`
    (`taitEdge_triangleFaceColors`). The general flow theorem then gives the
    triangle's 4-colourability (`triangle_fourColorable_of_flow`).
  - **Off the sphere:** the theta graph on the torus has a nowhere-zero flow
    but no face 4-colouring (`theta_torus_flow`).

The other direction needs no separate check. The theorem is proved, so no
graph that needs five colours can be `IsPlanar`; in particular `K₅` is not
(`not_isPlanar_K5`). That consequence rests on the Four Colour Theorem itself,
not on an independent argument such as `E ≤ 3V − 6`.

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

/-- The number of orbits of a permutation, as a `Fintype.card` that `decide`
can evaluate. The orbit relation is decided by
`FourCT.instDecidableRelSetoidSameCycle`, at most `card D` iterations. -/
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
  ⟨Fin 12, inferInstance, tetrahedron, tetraMap_loopless, ⟨k4Embedding.toCopy⟩⟩

/-- **Every simple graph on at most four vertices is planar**: it is contained
in `K₄`. -/
theorem isPlanar_of_card_le_four {V : Type*} [Fintype V] (G : SimpleGraph V)
    (h : Fintype.card V ≤ 4) : G.IsPlanar := by
  obtain ⟨e⟩ := Function.Embedding.nonempty_of_card_le (h.trans_eq (Fintype.card_fin 4).symm)
  refine isPlanar_K4.of_isContained ⟨{ toHom := ⟨e, fun hab => ?_⟩, injective' := e.injective }⟩
  exact (SimpleGraph.top_adj _ _).2 (e.injective.ne hab.ne)

/-- A path is planar: one face, with a vertex met twice on its boundary. -/
example : (SimpleGraph.pathGraph 4).IsPlanar := isPlanar_of_card_le_four _ (by simp)

/-- A graph with no edges, so that every vertex is isolated, is planar. -/
example : (⊥ : SimpleGraph (Fin 3)).IsPlanar := isPlanar_of_card_le_four _ (by simp)

/-- A disconnected graph, two disjoint edges, is planar. -/
example : (SimpleGraph.fromEdgeSet {s(0, 1), s(2, 3)} : SimpleGraph (Fin 4)).IsPlanar :=
  isPlanar_of_card_le_four _ (by simp)

/-- **`K₄` needs four colours.** -/
theorem not_colorable_three_K4 : ¬ (⊤ : SimpleGraph (Fin 4)).Colorable 3 := by
  intro h
  have := h.chromaticNumber_le
  rw [SimpleGraph.chromaticNumber_top, Fintype.card_fin] at this
  norm_num at this

/-- **`K₅` is not planar.** This follows from the Four Colour Theorem, since
`K₅` needs five colours; it is not an independent check of the definition. -/
theorem not_isPlanar_K5 : ¬ (⊤ : SimpleGraph (Fin 5)).IsPlanar := fun h => by
  have := h.colorable_four.chromaticNumber_le
  rw [SimpleGraph.chromaticNumber_top, Fintype.card_fin] at this
  norm_num at this

/-- The Four Colour Theorem, applied: `K₄` is 4-colourable, and this is the
best possible bound for planar graphs. -/
example : (⊤ : SimpleGraph (Fin 4)).Colorable 4 ∧ ¬ (⊤ : SimpleGraph (Fin 4)).Colorable 3 :=
  ⟨isPlanar_K4.colorable_four, not_colorable_three_K4⟩

/-! ### Tait's correspondence on the tetrahedron

The tetrahedron is its own dual, and `K₄`'s six edges split into three
perfect matchings: `01, 23`, `02, 13` and `03, 12`. -/

/-- **The tetrahedron is a triangulation**: every face has three darts. -/
theorem tetrahedron_isTriangulation : tetrahedron.IsTriangulation := by decide

/-- Vertex `a` gets colour `a`: the darts `3a`, `3a + 1`, `3a + 2` are at
vertex `a`. -/
def tetraVertexColors : Fin 12 → Color :=
  ![.c0, .c0, .c0, .c1, .c1, .c1, .c2, .c2, .c2, .c3, .c3, .c3]

/-- It is a proper vertex colouring. -/
theorem tetraVertexColors_graphColoring : tetraMap.GraphColoring tetraVertexColors := by
  decide

/-- The three perfect matchings in three colours: `01, 23 ↦ c1`, `02, 13 ↦ c2`,
`03, 12 ↦ c3`. -/
def tetraEdgeColors : Fin 12 → Color :=
  ![.c1, .c2, .c3, .c1, .c2, .c3, .c2, .c3, .c1, .c3, .c1, .c2]

/-- It is a proper 3-edge-colouring of the dual: the three edges of every
triangle get three different colours. -/
theorem tetraEdgeColors_edgeColoring : EdgeColoring tetraMap.dual tetraEdgeColors := by
  decide

/-- Tait's rule turns the vertex colouring into that edge colouring: the edge
`ab` gets `a + b`. -/
theorem taitEdge_tetraVertexColors :
    taitEdge tetraMap.dual tetraVertexColors = tetraEdgeColors := by
  decide

/-- Tait's theorem, used backwards: the edge colouring alone shows that the
tetrahedron's graph `K₄` is 4-colourable. -/
theorem tetrahedron_colorable_of_tait : tetrahedron.graph.Colorable 4 :=
  (PlaneGraph.tait tetrahedron tetraMap_loopless tetrahedron_isTriangulation).2
    ⟨_, tetraEdgeColors_edgeColoring⟩

/-! ### The sphere is needed: the theta graph on the torus

Two vertices `u`, `v` joined by three edges `a`, `b`, `c`. Darts `0, 1, 2` are
the ends of `a, b, c` at `u`, and darts `3, 4, 5` their ends at `v`. Both
vertices turn the same way, `a → b → c`. Drawn in the plane, one vertex would
turn the other way; turning the same way needs a handle, and the drawing has
a single face. -/

/-- `edge` of the theta graph. -/
def thetaEdge : Perm (Fin 6) := ⟨![3, 4, 5, 0, 1, 2], ![3, 4, 5, 0, 1, 2], by decide, by decide⟩

/-- `node` of the theta graph: `a → b → c` at both vertices. -/
def thetaNode : Perm (Fin 6) := ⟨![1, 2, 0, 4, 5, 3], ![2, 0, 1, 5, 3, 4], by decide, by decide⟩

/-- `face` of the theta graph, `node⁻¹ ∘ edge`: a single cycle through all six
darts. -/
def thetaFace : Perm (Fin 6) := ⟨![5, 3, 4, 2, 0, 1], ![4, 5, 3, 1, 2, 0], by decide, by decide⟩

/-- The theta graph on the torus, as a hypermap. -/
def thetaTorus : Hypermap (Fin 6) where
  edge := thetaEdge
  node := thetaNode
  face := thetaFace
  node_face_edge := by decide

theorem thetaTorus_plain : thetaTorus.Plain := ⟨by decide, by decide⟩

theorem thetaTorus_cubic : thetaTorus.Cubic :=
  ⟨fun x _ => (by decide : ∀ y, thetaNode (thetaNode (thetaNode y)) = y) x,
    fun x _ => (by decide : ∀ y, thetaNode y ≠ y) x⟩

/-- **Genus one**: 3 edges, 2 vertices, 1 face, one component and 6 darts, so
`2·1 + 6 = 3 + 2 + 1 + 2·1`. -/
theorem thetaTorus_genus : thetaTorus.genus = 1 := by
  have hc : thetaTorus.compCount = 1 := connected_of_reach thetaTorus 0 6 (by decide)
  have hcounts : cycleCount thetaTorus.edge = 3 ∧ cycleCount thetaTorus.node = 2 ∧
      cycleCount thetaTorus.face = 1 := by
    simp only [cycleCount_eq_card]
    decide
  obtain ⟨he, hn, hf⟩ := hcounts
  simp only [Hypermap.genus, Hypermap.EulerLhs, Hypermap.EulerRhs, hc, he, hn, hf,
    Nat.card_eq_fintype_card, Fintype.card_fin]

/-- Each edge in its own colour. -/
def thetaEdgeColors : Fin 6 → Color := ![.c1, .c2, .c3, .c1, .c2, .c3]

/-- **The theta graph on the torus has a proper 3-edge-colouring but no face
4-colouring.** Its one face lies on both sides of every edge. So Tait's
converse fails in genus one, and `FourCT.exists_coloring_of_edgeColoring`
needs its genus-zero hypothesis. -/
theorem theta_torus :
    EdgeColoring thetaTorus thetaEdgeColors ∧ ¬ thetaTorus.FourColorable ∧
      thetaTorus.genus = 1 :=
  ⟨by decide, fun h => h.bridgeless 0 ⟨3, by decide⟩, thetaTorus_genus⟩

/-! ### Flows -/

/-- The tetrahedron's edge colouring is a nowhere-zero ℤ₂ × ℤ₂-flow on its dual,
checked directly from the definition. -/
theorem tetraEdgeColors_flow : NowhereZeroFlow tetraMap.dual tetraEdgeColors := by decide

/-! A triangle, whose vertices have degree two, so the map is not cubic.
Vertices `a, b, c`; darts `0, 1` are the ends of `ab` at `a` and `b`, darts
`2, 3` the ends of `bc` at `b` and `c`, darts `4, 5` the ends of `ca` at `c`
and `a`. The two faces are the inside and the outside. -/

/-- `edge` of the triangle. -/
def triEdge : Perm (Fin 6) := ⟨![1, 0, 3, 2, 5, 4], ![1, 0, 3, 2, 5, 4], by decide, by decide⟩

/-- `node` of the triangle: the two darts at each vertex. -/
def triNode : Perm (Fin 6) := ⟨![5, 2, 1, 4, 3, 0], ![5, 2, 1, 4, 3, 0], by decide, by decide⟩

/-- `face` of the triangle, `node⁻¹ ∘ edge`: the cycles `0 2 4` and `1 5 3`. -/
def triFace : Perm (Fin 6) := ⟨![2, 5, 4, 1, 0, 3], ![4, 3, 0, 5, 2, 1], by decide, by decide⟩

/-- The triangle as a hypermap. -/
def triMap : Hypermap (Fin 6) where
  edge := triEdge
  node := triNode
  face := triFace
  node_face_edge := by decide

theorem triMap_plain : triMap.Plain := ⟨by decide, by decide⟩

/-- Planar: 3 edges, 3 vertices, 2 faces, one component, 6 darts, so
`2·1 + 6 = 3 + 3 + 2`. -/
theorem triMap_planar : triMap.Planar := by
  refine planar_of_counts triMap (connected_of_reach triMap 0 6 (by decide)) ?_
  simp only [cycleCount_eq_card]
  decide

/-- Every edge coloured `c1`. -/
def triFlow : Fin 6 → Color := fun _ => .c1

/-- It is a nowhere-zero flow: each vertex has two edges, and `c1 + c1 = 0`. -/
theorem triFlow_flow : NowhereZeroFlow triMap triFlow := by decide

/-- The inside (darts `0, 2, 4`) coloured `0`, the outside coloured `c1`. -/
def triangleFaceColors : Fin 6 → Color := ![.c0, .c1, .c0, .c1, .c0, .c1]

/-- Tait's rule turns that face colouring into the flow. -/
theorem taitEdge_triangleFaceColors : taitEdge triMap triangleFaceColors = triFlow := by
  decide

/-- The flow alone shows that the triangle's faces are 4-colourable. -/
theorem triangle_fourColorable_of_flow : triMap.FourColorable :=
  (fourColorable_iff_nowhereZeroFlow triMap_plain triMap_planar).2 ⟨_, triFlow_flow⟩

/-- **Off the sphere, a flow need not come from a colouring.** The theta graph
on the torus has a nowhere-zero ℤ₂ × ℤ₂-flow but no face 4-colouring. -/
theorem theta_torus_flow :
    NowhereZeroFlow thetaTorus thetaEdgeColors ∧ ¬ thetaTorus.FourColorable :=
  ⟨by decide, theta_torus.2.1⟩

end FourCT.Examples
