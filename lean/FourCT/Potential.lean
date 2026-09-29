/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourColor.Coloring
import Mathlib.Algebra.Field.ZMod
import Mathlib.LinearAlgebra.Matrix.Rank

/-!
# FourCT.Potential — edge labels that sum to zero at every vertex

Label each edge of a plane graph with a colour, the colours being the Klein
four-group `ℤ₂ × ℤ₂` (`FourColor.Color`). Suppose the labels around every
vertex sum to zero. Then on the sphere there is a labelling of the *faces*
such that each edge's label is the sum of the labels of the two faces on its
sides (`exists_facePotential`). This is the discrete fact behind Tait's
correspondence (`FourCT.Tait`) and behind the duality between flows and face
colourings.

It genuinely needs the sphere. On a torus, going once around the torus can
change the face label, and the statement fails (`FourCT.Examples`). Here the
sphere enters only through Euler's formula, as a count of dimensions over
`ℤ₂`:

* the edge labellings of the form "sum of the two faces" have dimension
  `F − C` (faces, minus one for each component, since adding a constant
  to the faces of a component changes nothing);
* the edge labellings that sum to zero at every vertex have dimension
  `E − V + C` (edges, minus the rank `V − C` of the vertex–edge incidence
  matrix);
* every labelling of the first kind is of the second kind, and on the sphere
  `V − E + F = 2C`, so the two dimensions agree and the spaces are equal.

Nothing here uses the Four Colour Theorem, or any module that proves it: this
file imports only the base port's definitions of hypermaps and colourings.

## Main definitions

* `FourCT.Orbit σ`, `FourCT.orbit σ x`: the orbits of a permutation of the
  darts, and the orbit of a dart. Edges, vertices and faces are the orbits of
  `edge`, `node` and `face`.
* `FourCT.inc G σ`: the incidence matrix over `ℤ₂` between the edges and
  the orbits of `σ`.

## Main results

* `FourCT.range_inc_face_eq`: on a plain genus-0 hypermap, the edge
  labellings over `ℤ₂` that are sums of face labels are exactly those that
  sum to zero at every vertex.
* `FourCT.exists_facePotential`: the same for labels in the Klein four-group.
-/

namespace FourCT

open FourColor Equiv Equiv.Perm Matrix

variable {D : Type*} [Fintype D] [DecidableEq D]

/-! ### Orbits -/

/-- The orbit relation of a permutation of a finite type is decidable, via
Mathlib's `Equiv.Perm.instDecidableRelSameCycle`. -/
instance instDecidableRelSetoidSameCycle (σ : Perm D) :
    DecidableRel (SameCycle.setoid σ).r :=
  fun x y => instDecidableRelSameCycle σ x y

/-- The orbits of a permutation `σ` of the darts. The edges, vertices and faces
of a hypermap are the orbits of `edge`, `node` and `face`. -/
abbrev Orbit (σ : Perm D) : Type _ := Quotient (SameCycle.setoid σ)

/-- The orbit of the dart `x`. -/
def orbit (σ : Perm D) (x : D) : Orbit σ := Quotient.mk _ x

omit [Fintype D] [DecidableEq D] in
theorem orbit_eq_iff {σ : Perm D} {x y : D} : orbit σ x = orbit σ y ↔ σ.SameCycle x y :=
  Quotient.eq

omit [Fintype D] [DecidableEq D] in
@[simp] theorem orbit_apply (σ : Perm D) (x : D) : orbit σ (σ x) = orbit σ x :=
  orbit_eq_iff.2 (sameCycle_apply_left.2 (SameCycle.refl _ _))

omit [Fintype D] [DecidableEq D] in
@[simp] theorem orbit_inv_apply (σ : Perm D) (x : D) : orbit σ (σ⁻¹ x) = orbit σ x := by
  rw [← orbit_apply σ (σ⁻¹ x)]
  simp

omit [Fintype D] [DecidableEq D] in
/-- Everything in the orbit of `x` lies in any set that contains `x` and is
closed under `σ` and `σ⁻¹`. -/
theorem mem_of_sameCycle {σ : Perm D} {S : Set D} {x y : D} (hx : x ∈ S)
    (hS : ∀ z ∈ S, σ z ∈ S) (hS' : ∀ z ∈ S, σ⁻¹ z ∈ S) (h : σ.SameCycle x y) : y ∈ S := by
  obtain ⟨i, rfl⟩ := h
  induction i using Int.induction_on with
  | zero => simpa using hx
  | succ n ih =>
    rw [add_comm, zpow_add, zpow_one, Perm.mul_apply]
    exact hS _ ih
  | pred n ih =>
    rw [sub_eq_add_neg, add_comm, zpow_add, zpow_neg_one, Perm.mul_apply]
    exact hS' _ ih

omit [Fintype D] [DecidableEq D] in
/-- In a plain hypermap an edge has exactly two darts, `x` and `edge x`. -/
theorem sameCycle_edge_iff {G : Hypermap D} (hG : G.Plain) {x y : D} :
    G.edge.SameCycle x y ↔ y = x ∨ y = G.edge x := by
  have hinv : ∀ z, G.edge⁻¹ z = G.edge z := fun z =>
    Perm.inv_eq_iff_eq.2 (hG.edge_edge z).symm
  refine ⟨mem_of_sameCycle (S := {y | y = x ∨ y = G.edge x}) (Or.inl rfl) ?_ ?_, ?_⟩
  · rintro z (rfl | rfl) <;> simp [hG.edge_edge]
  · rintro z (rfl | rfl) <;> simp [hinv, hG.edge_edge]
  · rintro (rfl | rfl)
    · exact SameCycle.refl _ _
    · exact G.cedge_edge x

/-! ### Components -/

section Components

variable (G : Hypermap D)

omit [Fintype D] [DecidableEq D] in
/-- A function of the darts that is unchanged by `edge`, `node` and `face` is
constant on each component. -/
theorem eq_of_eqvGen {α : Type*} (g : D → α) (he : ∀ x, g (G.edge x) = g x)
    (hn : ∀ x, g (G.node x) = g x) (hf : ∀ x, g (G.face x) = g x) {x y : D}
    (h : Relation.EqvGen G.GLink x y) : g x = g y := by
  induction h with
  | rel x y hxy => rcases hxy with rfl | rfl | rfl <;> simp [he, hn, hf]
  | refl => rfl
  | symm _ _ _ ih => exact ih.symm
  | trans _ _ _ _ _ ih₁ ih₂ => exact ih₁.trans ih₂

omit [DecidableEq D] in
/-- The darts of one orbit of `edge`, `node` or `face` are in one component. -/
theorem eqvGen_of_sameCycle {σ : Perm D} (hσ : ∀ z, G.GLink z (σ z)) {x y : D}
    (h : σ.SameCycle x y) : Relation.EqvGen G.GLink x y := by
  obtain ⟨n, rfl⟩ := h.exists_nat_pow_eq
  clear h
  induction n with
  | zero => exact .refl _
  | succ n ih =>
    rw [pow_succ', Perm.mul_apply]
    exact .trans _ _ _ ih (.rel _ _ (hσ _))

end Components

/-! ### The incidence matrices -/

section Incidence

variable (G : Hypermap D)

private theorem zmod2_add_eq_zero : ∀ a b : ZMod 2, a + b = 0 ↔ a = b := by decide

private theorem zmod2_add_self : ∀ a : ZMod 2, a + a = 0 := by decide

/-- The incidence matrix over `ℤ₂` between the edges and the orbits of `σ`:
the entry for an edge and an orbit is the number of darts they share, mod 2.
For `σ = face` it sends a labelling of the faces to the labelling of each edge
by the sum of the faces on its two sides (`inc_mulVec`). The transpose of the
matrix for `σ = node` sends a labelling of the edges to the sum at each vertex
(`inc_transpose_mulVec`). -/
def inc (σ : Perm D) : Matrix (Orbit G.edge) (Orbit σ) (ZMod 2) :=
  fun ε a => ∑ x : D, if orbit G.edge x = ε ∧ orbit σ x = a then 1 else 0

/-- Summing over the darts in the orbit of `x` under `τ`. -/
private theorem sum_ite_orbit (τ : Perm D) {β : Type*} [Fintype β] [DecidableEq β]
    (p : D → β) (v : β → ZMod 2) (c : Orbit τ) :
    ∑ a : β, (∑ y : D, if orbit τ y = c ∧ p y = a then (1 : ZMod 2) else 0) * v a =
      ∑ y : D, if orbit τ y = c then v (p y) else 0 := by
  simp only [Finset.sum_mul, ite_mul, one_mul, zero_mul]
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun y _ => ?_
  by_cases hy : orbit τ y = c
  · simp [hy]
  · simp [hy]

/-- The face-sum labelling: the label of the edge of `x` is the sum of the
labels of the faces of `x` and of `edge x`, the two sides of the edge. -/
theorem inc_mulVec (hG : G.Plain) (σ : Perm D) (k : Orbit σ → ZMod 2) (x : D) :
    (inc G σ *ᵥ k) (orbit G.edge x) = k (orbit σ x) + k (orbit σ (G.edge x)) := by
  simp only [mulVec, dotProduct, inc]
  rw [sum_ite_orbit G.edge (orbit σ) k, ← Finset.sum_filter]
  have hS : Finset.univ.filter (fun y => orbit G.edge y = orbit G.edge x) = {x, G.edge x} := by
    ext y
    simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_insert,
      Finset.mem_singleton, orbit_eq_iff, sameCycle_edge_iff hG]
    constructor <;> rintro (rfl | rfl) <;> simp [hG.edge_edge]
  rw [hS, Finset.sum_pair (hG.edge_ne x).symm]

/-- The vertex sums: the transpose of `inc G σ` adds up the labels of the edges
at the darts of each orbit of `σ`. -/
theorem inc_transpose_mulVec (σ : Perm D) (w : Orbit G.edge → ZMod 2) (x : D) :
    ((inc G σ)ᵀ *ᵥ w) (orbit σ x) =
      ∑ y ∈ Finset.univ.filter (fun y => σ.SameCycle x y), w (orbit G.edge y) := by
  simp only [mulVec, dotProduct, transpose_apply, inc]
  simp_rw [and_comm (a := orbit G.edge _ = _)]
  rw [sum_ite_orbit σ (orbit G.edge) w, ← Finset.sum_filter]
  refine Finset.sum_congr (Finset.filter_congr fun y _ => ?_) fun _ _ => rfl
  rw [orbit_eq_iff, sameCycle_comm]

/-- The labellings of the orbits of `node` or `face` that `inc` sends to zero
are those constant on each component, so they form a space of dimension the
number of components. -/
theorem finrank_ker_inc (hG : G.Plain) {σ : Perm D} (hσ : σ = G.node ∨ σ = G.face) :
    Module.finrank (ZMod 2) (LinearMap.ker (inc G σ).mulVecLin) = G.compCount := by
  have hlink : ∀ z, G.GLink z (σ z) := by
    rcases hσ with rfl | rfl
    exacts [G.glink_node, G.glink_face]
  let π : Orbit σ → Quotient G.gcompSetoid :=
    Quotient.map' id fun x y h => eqvGen_of_sameCycle G hlink h
  have hπ : Function.Surjective π := by
    rintro ⟨x⟩
    exact ⟨orbit σ x, rfl⟩
  have hker : LinearMap.ker (inc G σ).mulVecLin =
      LinearMap.range (LinearMap.funLeft (ZMod 2) (ZMod 2) π) := by
    ext k
    simp only [LinearMap.mem_ker, LinearMap.mem_range, mulVecLin_apply]
    constructor
    · intro hk
      -- `k` agrees across every edge ...
      have he : ∀ x, k (orbit σ (G.edge x)) = k (orbit σ x) := fun x => by
        have h := congrFun hk (orbit G.edge x)
        rw [inc_mulVec G hG, Pi.zero_apply, zmod2_add_eq_zero] at h
        exact h.symm
      -- ... so it is constant on each component.
      have hn : ∀ x, k (orbit σ (G.node x)) = k (orbit σ x) := by
        rcases hσ with rfl | rfl
        · exact fun x => orbit_apply _ x ▸ rfl
        · intro x
          rw [← he (G.node x), ← orbit_apply G.face (G.edge (G.node x)), G.nodeK]
      have hf : ∀ x, k (orbit σ (G.face x)) = k (orbit σ x) := by
        rcases hσ with rfl | rfl
        · intro x
          rw [← orbit_apply G.node (G.face x), ← he (G.node (G.face x)), G.faceK]
        · exact fun x => orbit_apply _ x ▸ rfl
      refine ⟨Quotient.lift (fun x => k (orbit σ x))
        (fun x y h => eq_of_eqvGen G (fun x => k (orbit σ x)) he hn hf h), ?_⟩
      funext a
      induction a using Quotient.inductionOn
      rfl
    · rintro ⟨c, rfl⟩
      funext ε
      induction ε using Quotient.inductionOn with
      | h x =>
        show (inc G σ *ᵥ _) (orbit G.edge x) = 0
        rw [inc_mulVec G hG]
        show c (π (orbit σ x)) + c (π (orbit σ (G.edge x))) = 0
        have : π (orbit σ (G.edge x)) = π (orbit σ x) :=
          Quotient.sound (.symm _ _ (.rel _ _ (G.glink_edge x)))
        rw [this, zmod2_add_self]
  have := Fintype.ofFinite (Quotient G.gcompSetoid)
  rw [hker, LinearMap.finrank_range_of_inj
      (LinearMap.funLeft_injective_of_surjective _ _ π hπ),
    Module.finrank_fintype_fun_eq_card, Hypermap.compCount, Nat.card_eq_fintype_card]

/-- Reindexing a sum over an orbit by `σ⁻¹`, which permutes the orbit. -/
theorem sum_sameCycle_inv (σ : Perm D) (x : D) {M : Type*} [AddCommMonoid M] (g : D → M) :
    ∑ y ∈ Finset.univ.filter (fun y => σ.SameCycle x y), g (σ⁻¹ y) =
      ∑ y ∈ Finset.univ.filter (fun y => σ.SameCycle x y), g y := by
  refine Finset.sum_nbij' (fun y => σ⁻¹ y) (fun y => σ y) (fun y hy => ?_) (fun y hy => ?_) (fun y _ => by simp)
    (fun y _ => by simp) (fun y _ => rfl)
  · simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hy ⊢
    exact hy.trans ⟨-1, by simp⟩
  · simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hy ⊢
    exact hy.trans ⟨1, by simp⟩

/-- A face-sum labelling sums to zero at every vertex. Around a vertex, the
faces met are the faces of its darts, and each one is met twice: once as the
face of a dart `y`, and once as the face across the edge of `node y`. -/
theorem inc_node_transpose_mulVec_inc_face (hG : G.Plain) (k : Orbit G.face → ZMod 2) :
    (inc G G.node)ᵀ *ᵥ (inc G G.face *ᵥ k) = 0 := by
  funext v
  induction v using Quotient.inductionOn with
  | h x =>
    show ((inc G G.node)ᵀ *ᵥ (inc G G.face *ᵥ k)) (orbit G.node x) = 0
    rw [inc_transpose_mulVec]
    simp only [inc_mulVec G hG]
    have hF : ∀ y, orbit G.face (G.edge y) = orbit G.face (G.node⁻¹ y) := fun y => by
      rw [← Perm.eq_inv_iff_eq.2 (G.edgeK y), orbit_apply]
    simp only [hF, Finset.sum_add_distrib]
    rw [sum_sameCycle_inv G.node x (fun y => k (orbit G.face y)), zmod2_add_self]

/-- **On the sphere, the edge labellings over `ℤ₂` that sum to zero at every
vertex are exactly the sums of face labels.** `G` is a plain hypermap of
genus zero, and a labelling is a function on the edges. -/
theorem range_inc_face_eq (hG : G.Plain) (hp : G.Planar) :
    LinearMap.range (inc G G.face).mulVecLin =
      LinearMap.ker (inc G G.node)ᵀ.mulVecLin := by
  have hle : LinearMap.range (inc G G.face).mulVecLin ≤
      LinearMap.ker (inc G G.node)ᵀ.mulVecLin := by
    rintro _ ⟨k, rfl⟩
    rw [LinearMap.mem_ker, mulVecLin_apply, mulVecLin_apply]
    exact inc_node_transpose_mulVec_inc_face G hG k
  refine Submodule.eq_of_le_of_finrank_eq hle ?_
  -- Rank and nullity of the three maps.
  have h1 := LinearMap.finrank_range_add_finrank_ker (inc G G.face).mulVecLin
  have h2 := LinearMap.finrank_range_add_finrank_ker (inc G G.node).mulVecLin
  have h3 := LinearMap.finrank_range_add_finrank_ker (inc G G.node)ᵀ.mulVecLin
  have h4 : (inc G G.node)ᵀ.rank = (inc G G.node).rank := rank_transpose _
  rw [finrank_ker_inc G hG (Or.inr rfl)] at h1
  rw [finrank_ker_inc G hG (Or.inl rfl)] at h2
  simp only [Module.finrank_fintype_fun_eq_card] at h1 h2 h3
  unfold Matrix.rank at h4
  -- Euler's formula on the sphere, with two darts per edge.
  have heul := G.evenGenus
  have hcard := hG.card_eq
  have hp' : G.genus = 0 := hp
  simp only [Hypermap.EvenGenus, Hypermap.EulerLhs, Hypermap.EulerRhs, hp', cycleCount,
    Nat.card_eq_fintype_card] at heul hcard
  have eV : Fintype.card (Orbit G.node) = Fintype.card (Quotient (SameCycle.setoid G.node)) :=
    Fintype.card_congr' rfl
  have eF : Fintype.card (Orbit G.face) = Fintype.card (Quotient (SameCycle.setoid G.face)) :=
    Fintype.card_congr' rfl
  have eE : Fintype.card (Orbit G.edge) = Fintype.card (Quotient (SameCycle.setoid G.edge)) :=
    Fintype.card_congr' rfl
  omega

end Incidence

/-! ### Labels in the Klein four-group -/

/-- The high bit of a colour, as an element of `ℤ₂`. -/
def hiBit : Color →+ ZMod 2 where
  toFun c := if c.hi then 1 else 0
  map_zero' := rfl
  map_add' := by decide

/-- The low bit of a colour, as an element of `ℤ₂`. -/
def loBit : Color →+ ZMod 2 where
  toFun c := if c.lo then 1 else 0
  map_zero' := rfl
  map_add' := by decide

/-- The colour with high bit `a` and low bit `b`. -/
def colorOfBits (a b : ZMod 2) : Color := Color.ofBits (decide (a = 1)) (decide (b = 1))

theorem hiBit_colorOfBits : ∀ a b : ZMod 2, hiBit (colorOfBits a b) = a := by decide

theorem loBit_colorOfBits : ∀ a b : ZMod 2, loBit (colorOfBits a b) = b := by decide

theorem color_ext_bits : ∀ c d : Color, hiBit c = hiBit d → loBit c = loBit d → c = d := by
  decide

variable (G : Hypermap D)

/-- **Edge labels that sum to zero at every vertex are face differences, on the
sphere.** Let `G` be a plain hypermap of genus zero and `w` a labelling of its
edges by colours (`w (edge x) = w x`) whose labels sum to zero around every
vertex. Then there is a labelling `k` of the faces (`k (face x) = k x`) with
`k x + k (edge x) = w x`: each edge's label is the sum of the labels of the
faces on its two sides.

Proved one bit at a time from `range_inc_face_eq`. -/
theorem exists_facePotential (hG : G.Plain) (hp : G.Planar) (w : D → Color)
    (hw : ∀ x, w (G.edge x) = w x)
    (hsum : ∀ x, ∑ y ∈ Finset.univ.filter (fun y => G.node.SameCycle x y), w y = 0) :
    ∃ k : D → Color, (∀ x, k (G.face x) = k x) ∧ ∀ x, k x + k (G.edge x) = w x := by
  have hbit : ∀ p : Color →+ ZMod 2, ∃ kp : Orbit G.face → ZMod 2,
      ∀ x, kp (orbit G.face x) + kp (orbit G.face (G.edge x)) = p (w x) := by
    intro p
    let wp : Orbit G.edge → ZMod 2 := Quotient.lift (fun x => p (w x)) fun x y h => by
      rcases (sameCycle_edge_iff hG).1 h with rfl | rfl
      · rfl
      · simp [hw]
    have hwp : wp ∈ LinearMap.ker (inc G G.node)ᵀ.mulVecLin := by
      rw [LinearMap.mem_ker, mulVecLin_apply]
      funext v
      induction v using Quotient.inductionOn with
      | h x =>
        show ((inc G G.node)ᵀ *ᵥ wp) (orbit G.node x) = 0
        rw [inc_transpose_mulVec]
        show ∑ y ∈ _, p (w y) = 0
        rw [← _root_.map_sum, hsum, map_zero]
    rw [← range_inc_face_eq G hG hp] at hwp
    obtain ⟨kp, hkp⟩ := hwp
    refine ⟨kp, fun x => ?_⟩
    have := congrFun hkp (orbit G.edge x)
    rwa [mulVecLin_apply, inc_mulVec G hG] at this
  obtain ⟨kh, hkh⟩ := hbit hiBit
  obtain ⟨kl, hkl⟩ := hbit loBit
  refine ⟨fun x => colorOfBits (kh (orbit G.face x)) (kl (orbit G.face x)),
    fun x => by simp only [orbit_apply], fun x => ?_⟩
  apply color_ext_bits
  · rw [map_add, hiBit_colorOfBits, hiBit_colorOfBits, hkh]
  · rw [map_add, loBit_colorOfBits, loBit_colorOfBits, hkl]

end FourCT
