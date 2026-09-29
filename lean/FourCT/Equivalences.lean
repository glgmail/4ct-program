/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import Statements.Tait
import Statements.Flows
import Statements.Penrose
import FourCT.Flow
import FourCT.Penrose

/-!
# FourCT.Equivalences — the statement files, tied to the Four Colour Theorem

The statements in `lean/Statements/` are only definitions of propositions. This
file proves them equivalent to each other and to the Four Colour Theorem in its
vertex form, and then proves them.

**The equivalences use no part of the Four Colour Theorem's proof.** Each of
them would be trivial if they did, since true statements are all equivalent.
`checks/lean/fourct_independence.lean` checks every one.

```
Statements.Penrose  ↔  Statements.Tait  ↔  MapForm  ↔  Statements.Flows
                                              ↕
                                         VertexForm   (every planar simple graph is 4-colourable)
```

* `VertexForm`: the Four Colour Theorem in Mathlib's vocabulary, the statement
  of `SimpleGraph.IsPlanar.colorable_four`.
* `MapForm`: every plain, genus-0, bridgeless hypermap is face 4-colourable,
  the base port's combinatorial form restricted to plain maps.

The steps:

* **Tait → MapForm.** A face colouring of a cubic map comes from its edge
  colouring on the sphere (`FourCT.exists_coloring_of_edgeColoring`). Every map
  reduces to a cubic one by the base port's minimal-counterexample argument,
  `Hypermap.fourColorable_of_no_minimalCounterExample`, since a minimal
  counterexample is cubic (`Hypermap.MinimalCounterExample.cubic`).
* **MapForm → Flows.** Tait's rule turns a face colouring into a nowhere-zero
  flow (`FourCT.nowhereZeroFlow_taitEdge`).
* **Flows → Tait.** On a cubic map a nowhere-zero flow is a proper
  3-edge-colouring (`FourCT.edgeColoring_iff_nowhereZeroFlow`).
* **MapForm ↔ VertexForm.** By duality: the vertices of a plane graph are the
  faces of its dual, and loopless graphs have bridgeless duals.
* **Penrose ↔ Tait.** By Penrose's formula (`FourCT.penrose_eq`), the evaluation
  is `±` the number of Tait colourings.

Then `VertexForm` holds by the Four Colour Theorem, and so do both statements
(`statements_tait`, `statements_flows`). Those two do use the theorem.
-/

namespace FourCT

open FourColor Equiv Equiv.Perm

/-! ### The forms -/

/-- **The Four Colour Theorem, vertex form**, in Mathlib's vocabulary: every
planar simple graph is 4-colourable. -/
def VertexForm : Prop := ∀ (V : Type) (G : SimpleGraph V), G.IsPlanar → G.Colorable 4

/-- **The Four Colour Theorem, map form**: every plain, genus-0, bridgeless
hypermap has a face 4-colouring. -/
def MapForm : Prop :=
  ∀ (D : Type) [Fintype D] (G : Hypermap D), G.Plain → G.Planar → G.Bridgeless →
    G.FourColorable

/-! ### Flows in `ZMod 2 × ZMod 2`, and in the port's colours -/

/-- In `ZMod 2 × ZMod 2` every element is its own negative, so a flow's
orientation convention does not matter. -/
theorem neg_eq_self_zmod2 : ∀ a : ZMod 2 × ZMod 2, -a = a := by decide

/-- The port's colours are `ZMod 2 × ZMod 2`: the high and low bits. -/
def colorEquiv : Color ≃+ ZMod 2 × ZMod 2 where
  toFun c := (hiBit c, loBit c)
  invFun p := colorOfBits p.1 p.2
  left_inv c := by cases c <;> decide
  right_inv p := Prod.ext (hiBit_colorOfBits _ _) (loBit_colorOfBits _ _)
  map_add' a b := Prod.ext (map_add hiBit a b) (map_add loBit a b)

/-- **The flow of `Statements.Flows` is the flow of `FourCT.Flow`**, up to
renaming the four colours. -/
theorem exists_isNowhereZeroFlow_iff {D : Type} [Fintype D] [DecidableEq D]
    (P : PlaneGraph D) :
    (∃ w, Statements.IsNowhereZeroFlow P w) ↔ ∃ w, NowhereZeroFlow P.map w := by
  constructor
  · rintro ⟨w, hedge, hne, hsum⟩
    refine ⟨fun x => colorEquiv.symm (w x), fun x => ?_, fun x h => ?_, fun x => ?_⟩
    · simp only [hedge, neg_eq_self_zmod2]
    · exact hne x (colorEquiv.symm.injective (h.trans (map_zero _).symm))
    · rw [← _root_.map_sum, hsum x, map_zero]
  · rintro ⟨w, hw⟩
    refine ⟨fun x => colorEquiv (w x), fun x => ?_, fun x h => ?_, fun x => ?_⟩
    · simp only [hw.edge, neg_eq_self_zmod2]
    · exact hw.ne_zero x (colorEquiv.injective (h.trans (map_zero _).symm))
    · rw [← _root_.map_sum, hw.sum_node x, map_zero]

/-! ### The equivalences -/

/-- Tait's statement colours every plain, genus-0, bridgeless cubic hypermap. -/
theorem fourColorable_of_tait (h : Statements.Tait) {D : Type} [Fintype D]
    (G : Hypermap D) (hG : G.Plain) (hp : G.Planar) (hb : G.Bridgeless) (hc : G.Cubic) :
    G.FourColorable := by
  classical
  obtain ⟨e, he⟩ := h D ⟨G, hG, hp⟩ hb hc
  obtain ⟨k, hk, -⟩ := exists_coloring_of_edgeColoring hG hc hp he
  exact ⟨k, hk⟩

/-- **The cubic case suffices**, by the base port's minimal-counterexample
argument: a smallest map that cannot be coloured is plain and cubic. -/
theorem mapForm_of_cubic
    (h : ∀ (D : Type) [Fintype D] (G : Hypermap D), G.Plain → G.Planar → G.Bridgeless →
      G.Cubic → G.FourColorable) : MapForm := by
  intro D _ G _ hp hb
  refine Hypermap.fourColorable_of_no_minimalCounterExample (fun {E} _ H hH => ?_) G ⟨hp, hb⟩
  have := Fintype.ofFinite E
  exact hH.noncolorable (h E H hH.plain hH.planar hH.bridgeless hH.cubic)

theorem mapForm_of_tait (h : Statements.Tait) : MapForm :=
  mapForm_of_cubic fun _ _ G hG hp hb hc => fourColorable_of_tait h G hG hp hb hc

theorem flows_of_mapForm (h : MapForm) : Statements.Flows := by
  intro D _ _ P hb
  obtain ⟨k, hk⟩ := h D P.map P.plain P.planar hb
  exact (exists_isNowhereZeroFlow_iff P).2 ⟨_, nowhereZeroFlow_taitEdge P.plain hk⟩

theorem tait_of_flows (h : Statements.Flows) : Statements.Tait := by
  intro D _ P hb hc
  classical
  obtain ⟨w, hw⟩ := (exists_isNowhereZeroFlow_iff P).1 (h D P hb)
  exact ⟨w, (edgeColoring_iff_nowhereZeroFlow hc).2 hw⟩

/-- **Tait's statement and the flow statement are equivalent**, without the
Four Colour Theorem. -/
theorem tait_iff_flows : Statements.Tait ↔ Statements.Flows :=
  ⟨fun h => flows_of_mapForm (mapForm_of_tait h), tait_of_flows⟩

theorem tait_iff_mapForm : Statements.Tait ↔ MapForm :=
  ⟨mapForm_of_tait, fun h => tait_of_flows (flows_of_mapForm h)⟩

theorem vertexForm_of_mapForm (h : MapForm) : VertexForm := by
  intro V G hG
  obtain ⟨D, _, Q, hl, ⟨f⟩⟩ := hG
  -- The dual of `Q` is plain, genus 0 and bridgeless, so its faces, which are
  -- `Q`'s vertices, can be coloured.
  have hd := h D Q.map.dual ((Hypermap.plain_dual _).2 Q.plain)
    ((Hypermap.planar_dual _).2 Q.planar) ((Hypermap.bridgeless_dual _).2 hl)
  exact SimpleGraph.Colorable.of_hom f.toHom
    (Q.colorable_of_graphFourColorable (Hypermap.fourColorable_dual_iff.1 hd))

theorem mapForm_of_vertexForm (h : VertexForm) : MapForm := by
  intro D _ G hG hp hb
  classical
  -- `G`'s faces are the vertices of its dual, a loopless plane graph.
  let Q : PlaneGraph D := ⟨G.dual, (Hypermap.plain_dual _).2 hG, (Hypermap.planar_dual _).2 hp⟩
  have hl : Q.map.Loopless := by
    rw [← Hypermap.bridgeless_dual]
    simpa only [Q, Hypermap.dual_dual] using hb
  have hc := h _ Q.graph ⟨D, inferInstance, Q, hl, ⟨SimpleGraph.Copy.id _⟩⟩
  have := Hypermap.fourColorable_dual_iff.2 ((Q.graphFourColorable_iff hl).2 hc)
  simpa only [Q, Hypermap.dual_dual] using this

/-- **Tait's statement is equivalent to the Four Colour Theorem in its vertex
form**, without the Four Colour Theorem. -/
theorem tait_iff_vertexForm : Statements.Tait ↔ VertexForm :=
  tait_iff_mapForm.trans ⟨vertexForm_of_mapForm, mapForm_of_vertexForm⟩

/-- **The flow statement is equivalent to the Four Colour Theorem in its vertex
form**, without the Four Colour Theorem. -/
theorem flows_iff_vertexForm : Statements.Flows ↔ VertexForm :=
  tait_iff_flows.symm.trans tait_iff_vertexForm

/-- On a plane cubic map, the Penrose evaluation is non-zero exactly when there
is a proper 3-edge-colouring (Penrose's formula). -/
theorem penrose_ne_zero_iff {D : Type} [Fintype D] [DecidableEq D] (P : PlaneGraph D)
    (hc : P.map.Cubic) : Statements.penrose P.map ≠ 0 ↔ ∃ e, EdgeColoring P.map e := by
  rw [penrose_eq P.plain hc P.planar, ← taitCount_ne_zero_iff]
  constructor
  · intro h h0
    exact h (by rw [h0, Nat.cast_zero, mul_zero])
  · intro h
    exact mul_ne_zero (pow_ne_zero _ (by norm_num)) (by exact_mod_cast h)

/-- **Penrose's statement is equivalent to Tait's**, without the Four Colour
Theorem. -/
theorem penrose_iff_tait : Statements.Penrose ↔ Statements.Tait := by
  constructor
  · intro h D _ P hb hc
    classical
    exact (penrose_ne_zero_iff P hc).1 (h D P hb hc)
  · intro h D _ _ P hb hc
    exact (penrose_ne_zero_iff P hc).2 (h D P hb hc)

/-- **Penrose's statement is equivalent to the Four Colour Theorem in its vertex
form**, without the Four Colour Theorem. -/
theorem penrose_iff_vertexForm : Statements.Penrose ↔ VertexForm :=
  penrose_iff_tait.trans tait_iff_vertexForm

/-! ### The statements hold

These use the Four Colour Theorem, through `SimpleGraph.IsPlanar.colorable_four`.
They show that neither statement is accidentally false. -/

theorem vertexForm : VertexForm := fun _ _ hG => hG.colorable_four

/-- **Tait's statement holds.** -/
theorem statements_tait : Statements.Tait := tait_iff_vertexForm.2 vertexForm

/-- **The flow statement holds.** -/
theorem statements_flows : Statements.Flows := flows_iff_vertexForm.2 vertexForm

/-- **Penrose's statement holds.** -/
theorem statements_penrose : Statements.Penrose := penrose_iff_vertexForm.2 vertexForm

end FourCT
