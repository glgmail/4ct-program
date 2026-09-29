/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT.Base
import Mathlib.Combinatorics.SimpleGraph.Coloring.Vertex
import Mathlib.Combinatorics.SimpleGraph.Copy

/-!
# FourCT.PlaneGraph — plane graphs, and the Four Colour Theorem for them

A **plane graph** is a finite graph drawn on the sphere, given combinatorially.
Take its *darts*, the half-edges, one for each end of each edge. Three
permutations of the darts describe the drawing:

* `edge` swaps the two darts of each edge;
* `node` moves each dart to the next one around its vertex;
* `face` moves each dart to the next one around its face.

Together they satisfy `node ∘ face ∘ edge = id`. This is the base port's
`FourColor.Hypermap` (Gonthier's hypermaps). A plane graph is a hypermap that
is `Plain`: `edge` swaps darts in pairs and fixes none, so every edge has
exactly two ends. It is also `Planar`: genus zero, by Euler's formula.

The graph a reader sees is Mathlib's `SimpleGraph` on the vertices, which are
the orbits of `node`. Two vertices are adjacent when some edge joins them.
Everything the program *states* about colourings uses that graph, so it is in
Mathlib's vocabulary. The hypermap is the machinery underneath. Why this
foundation was chosen is in `notes/A-rosetta-stone.md` (A3).

## Main definitions

* `FourCT.PlaneGraph`: a plane graph on a finite type of darts.
* `FourCT.PlaneGraph.Vertex`, `FourCT.PlaneGraph.graph`: its vertices and its
  underlying simple graph.
* `SimpleGraph.IsPlanar`: a finite simple graph is planar when it is
  contained in (Mathlib's `⊑`: a copy of it sits inside) the underlying graph
  of a loopless plane graph.

## Main results

* `FourCT.PlaneGraph.graphFourColorable_iff`: for a loopless plane graph, the
  base port's graph colourings are exactly the proper 4-colourings of the
  underlying simple graph.
* `FourCT.PlaneGraph.four_colorable`: **the Four Colour Theorem for plane
  graphs.** The underlying graph of every loopless plane graph is
  4-colourable.
* `SimpleGraph.IsPlanar.colorable_four`: **every planar simple graph is
  4-colourable**, in Mathlib's vocabulary.
-/

namespace FourCT

open FourColor Equiv Equiv.Perm

/-- A **plane graph** on the darts `D`: a hypermap (permutations `edge`,
`node`, `face` of the darts with `node ∘ face ∘ edge = id`) in which every
edge has exactly two darts (`Plain`) and whose genus is zero (`Planar`).

Loops (an edge from a vertex to itself) and multiple edges are allowed here.
Results about colourings assume no loops (`FourColor.Hypermap.Loopless`),
since a vertex joined to itself cannot be properly coloured. -/
structure PlaneGraph (D : Type) [Fintype D] where
  /-- The hypermap describing the drawing. -/
  map : Hypermap D
  /-- Every edge has exactly two darts. -/
  plain : map.Plain
  /-- Genus zero: the drawing is on the sphere. -/
  planar : map.Planar

namespace PlaneGraph

variable {D : Type} [Fintype D] (G : PlaneGraph D)

/-- The vertices of a plane graph: the orbits of `node`, i.e. for each vertex,
the set of darts around it. -/
def Vertex : Type := Quotient (SameCycle.setoid G.map.node)

/-- The vertex a dart is attached to. -/
def vertexOf (x : D) : G.Vertex := Quotient.mk _ x

theorem vertexOf_eq_iff {x y : D} : G.vertexOf x = G.vertexOf y ↔ G.map.node.SameCycle x y :=
  Quotient.eq

@[simp] theorem vertexOf_node (x : D) : G.vertexOf (G.map.node x) = G.vertexOf x :=
  G.vertexOf_eq_iff.2 (sameCycle_apply_left.2 (SameCycle.refl _ _))

theorem vertexOf_surjective : Function.Surjective G.vertexOf :=
  Quotient.mk_surjective

/-- The **underlying simple graph**: two distinct vertices are adjacent when an
edge of the plane graph joins them. Loops and repeated edges are forgotten, as
a simple graph cannot record them. -/
def graph : SimpleGraph G.Vertex where
  Adj u v := u ≠ v ∧ ∃ x : D, G.vertexOf x = u ∧ G.vertexOf (G.map.edge x) = v
  symm := ⟨by
    rintro u v ⟨hne, x, rfl, rfl⟩
    exact ⟨hne.symm, G.map.edge x, rfl, by rw [G.plain.edge_edge x]⟩⟩
  loopless := ⟨fun _ h => h.1 rfl⟩

theorem graph_adj {u v : G.Vertex} :
    G.graph.Adj u v ↔ u ≠ v ∧ ∃ x : D, G.vertexOf x = u ∧ G.vertexOf (G.map.edge x) = v :=
  Iff.rfl

/-- In a loopless plane graph, the two ends of every edge are adjacent. -/
theorem adj_vertexOf_edge (hl : G.map.Loopless) (x : D) :
    G.graph.Adj (G.vertexOf x) (G.vertexOf (G.map.edge x)) :=
  ⟨fun h => hl x (G.vertexOf_eq_iff.1 h), x, rfl, rfl⟩

/-! ### Colourings -/

/-- A graph colouring of the hypermap (colours constant around each vertex,
different at the two ends of each edge) gives a proper colouring of the
underlying simple graph. -/
def coloringOfGraphColoring {k : D → Color} (hk : G.map.GraphColoring k) :
    G.graph.Coloring Color :=
  SimpleGraph.Coloring.mk
    (Quotient.lift k fun _ _ h => congr_of_sameCycle hk.node h)
    (by
      rintro u v ⟨-, x, rfl, rfl⟩
      exact (hk.edge x).symm)

theorem card_color : Fintype.card Color = 4 := by decide

/-- The base port's four-colourability gives a proper 4-colouring of the
underlying simple graph. -/
theorem colorable_of_graphFourColorable (h : G.map.GraphFourColorable) :
    G.graph.Colorable 4 := by
  obtain ⟨k, hk⟩ := h
  have := (G.coloringOfGraphColoring hk).colorable
  rwa [card_color] at this

/-- **For a loopless plane graph, the base port's graph colourings are exactly
the proper 4-colourings of its underlying simple graph.** -/
theorem graphFourColorable_iff (hl : G.map.Loopless) :
    G.map.GraphFourColorable ↔ G.graph.Colorable 4 := by
  refine ⟨G.colorable_of_graphFourColorable, ?_⟩
  rintro ⟨c⟩
  let e : Fin 4 ≃ Color := Fintype.equivOfCardEq (by rw [card_color, Fintype.card_fin])
  refine ⟨fun x => e (c (G.vertexOf x)), ⟨fun x h => ?_, fun x => ?_⟩⟩
  · exact c.valid (G.adj_vertexOf_edge hl x) (e.injective h).symm
  · simp only [vertexOf_node]

/-! ### The Four Colour Theorem -/

/-- **The Four Colour Theorem for plane graphs**: the underlying graph of
every loopless plane graph is 4-colourable.

From the base port's combinatorial theorem (`FourCT.hypermap_fourColorable`)
applied to the dual, which is planar because the graph is
(`Hypermap.planar_dual`), and bridgeless because the graph is loopless
(`Hypermap.bridgeless_dual`). A colouring of the dual's faces is a colouring
of the graph's vertices (`Hypermap.fourColorable_dual_iff`). -/
theorem four_colorable (hl : G.map.Loopless) : G.graph.Colorable 4 := by
  have hpb : G.map.dual.PlanarBridgeless :=
    ⟨(Hypermap.planar_dual G.map).2 G.planar, (Hypermap.bridgeless_dual G.map).2 hl⟩
  exact G.colorable_of_graphFourColorable
    (Hypermap.fourColorable_dual_iff.1 (hypermap_fourColorable _ hpb))

end PlaneGraph

end FourCT

namespace SimpleGraph

open FourCT

/-- A finite simple graph is **planar** when it is contained in the underlying
graph of some loopless plane graph (`G ⊑ P.graph`, Mathlib's
`SimpleGraph.IsContained`). Its vertices map injectively to the plane graph's
vertices, sending adjacent vertices to adjacent vertices. The copy need not
be induced: non-adjacent vertices may map to adjacent ones.

For finite graphs this is the usual notion. A planar drawing of a simple graph
is a loopless plane graph, once each isolated vertex is given an edge to a new
vertex of its own. Conversely, deleting vertices and edges keeps a drawing
planar. A graph with infinitely many vertices is never planar in this sense,
since plane graphs are finite. -/
def IsPlanar {V : Type*} (G : SimpleGraph V) : Prop :=
  ∃ (D : Type) (_ : Fintype D) (P : PlaneGraph D), P.map.Loopless ∧ G ⊑ P.graph

/-- Planarity passes to everything contained in a planar graph: subgraphs, and
copies of subgraphs on other vertex types. -/
theorem IsPlanar.of_isContained {V W : Type*} {G : SimpleGraph V} {H : SimpleGraph W}
    (h : H.IsPlanar) (hGH : G ⊑ H) : G.IsPlanar := by
  obtain ⟨D, _, P, hl, hH⟩ := h
  exact ⟨D, inferInstance, P, hl, hGH.trans hH⟩

/-- **The Four Colour Theorem**: every planar simple graph is 4-colourable. -/
theorem IsPlanar.colorable_four {V : Type*} {G : SimpleGraph V} (h : G.IsPlanar) :
    G.Colorable 4 := by
  obtain ⟨D, _, P, hl, ⟨f⟩⟩ := h
  exact SimpleGraph.Colorable.of_hom f.toHom (P.four_colorable hl)

end SimpleGraph
