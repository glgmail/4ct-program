/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import Statements.Penrose
import FourCT.Tait

/-!
# FourCT.Penrose — Penrose's formula

**Penrose's formula** (`penrose_eq`): for a plain cubic map on the sphere,

  `penrose G = (-1) ^ (V / 2) * taitCount G`,

where `V` is the number of vertices and `taitCount G` the number of Tait
colourings, the proper 3-edge-colourings with colours `0, 1, 2`.
`Statements.penrose` is Penrose's contraction of the Levi-Civita tensor.

## Why it holds

A term of the contraction is non-zero exactly when the colouring is proper, and
it is then `±1`. The work is in showing that on the sphere every proper
colouring gives the same sign, `(-1) ^ (V / 2)`. Nothing global like the Jordan
curve theorem is needed, only counting:

* On the sphere, a Tait colouring comes from a colouring `k` of the faces by
  Tait's rule (`FourCT.exists_coloring_of_edgeColoring`, via the colours
  `c1, c2, c3` of the Klein four-group). This is where genus zero is used.
* At each vertex, the sign is `(-1)` to the sum over its three darts of a
  0/1 quantity `tau` that depends on the edge colour and the face colours at
  the dart (`levi_eq_neg_one_pow`, checked by `decide` over all colour
  triples).
* Summed over all darts, `tau` counts two things:
  - the `c2`-coloured darts whose face has high bit `0`. Across each
    `c2`-edge the high bit of the face colour changes, so this is one dart per
    `c2`-edge. There are `V / 2` such edges, one `c2`-edge-end at every vertex;
  - the `c1`-coloured darts with a certain property that both darts of a
    `c1`-edge share. That is an even number.

So the sign is `(-1) ^ (V / 2)`.

Off the sphere the sign can differ: the theta graph on the torus has
evaluation `+6` where the formula would give `-6` (`FourCT.Examples`).

Nothing here uses the Four Colour Theorem (checked by
`checks/lean/fourct_independence.lean`).

## Main results

* `FourCT.penrose_eq`: Penrose's formula.
* `FourCT.taitCount_ne_zero_iff`: a map has a Tait colouring exactly when it
  has a proper 3-edge-colouring in the sense of `FourCT.EdgeColoring`.
-/

namespace FourCT

open FourColor Equiv Equiv.Perm Statements

/-! ### Colours -/

/-- The three colours `0, 1, 2` as the non-zero colours `c1, c2, c3` of the Klein
four-group. -/
def colorOfFin3 : Fin 3 → Color := ![.c1, .c2, .c3]

/-- The inverse of `colorOfFin3` on the non-zero colours. -/
def fin3OfColor : Color → Fin 3
  | .c0 => 0
  | .c1 => 0
  | .c2 => 1
  | .c3 => 2

theorem fin3OfColor_colorOfFin3 : ∀ i, fin3OfColor (colorOfFin3 i) = i := by decide

theorem colorOfFin3_ne_zero : ∀ i, colorOfFin3 i ≠ 0 := by decide

theorem colorOfFin3_injective : Function.Injective colorOfFin3 := fun a b h => by
  simpa only [fin3OfColor_colorOfFin3] using congrArg fin3OfColor h

theorem fin3OfColor_injOn : ∀ a b : Color, a ≠ 0 → b ≠ 0 → fin3OfColor a = fin3OfColor b →
    a = b := by decide

/-! ### Tait colourings -/

variable {D : Type*} [Fintype D] [DecidableEq D]

/-- The number of **Tait colourings**: colourings of the edges with `0, 1, 2`
(both darts of an edge get its colour) in which consecutive darts round each
vertex get different colours. On a cubic map these are the proper
3-edge-colourings. -/
def taitCount (G : Hypermap D) : ℕ :=
  (Finset.univ.filter fun c : D → Fin 3 =>
    (∀ x, c (G.edge x) = c x) ∧ ∀ x, c (G.node x) ≠ c x).card

/-- A map has a Tait colouring exactly when it has a proper 3-edge-colouring in
the sense of `FourCT.EdgeColoring`: the colours `0, 1, 2` are `c1, c2, c3`. -/
theorem taitCount_ne_zero_iff (G : Hypermap D) : taitCount G ≠ 0 ↔ ∃ e, EdgeColoring G e := by
  constructor
  · intro h
    obtain ⟨c, hc⟩ := Finset.card_ne_zero.1 h
    simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hc
    exact ⟨fun x => colorOfFin3 (c x), fun x => by simp only [hc.1],
      fun x => colorOfFin3_ne_zero _, fun x h => hc.2 x (colorOfFin3_injective h)⟩
  · rintro ⟨e, he⟩
    refine Finset.card_ne_zero.2 ⟨fun x => fin3OfColor (e x), ?_⟩
    simp only [Finset.mem_filter, Finset.mem_univ, true_and]
    exact ⟨fun x => by simp only [he.edge],
      fun x h => he.node x (fin3OfColor_injOn _ _ (he.ne_zero _) (he.ne_zero _) h)⟩

/-! ### The sign at one vertex -/

/-- The 0/1 quantity whose sum round a vertex gives the sign there. For a dart
with edge colour `e`, face colour `a`, and face colour `b` at the next dart
round its vertex: `1` for a `c2`-dart whose face has high bit `0`, plus `1` for a
`c1`-dart whose next face has high bit `0`. -/
def tau (e a b : Color) : ℕ :=
  (if e = .c2 ∧ a.hi = false then 1 else 0) + (if e = .c1 ∧ b.hi = false then 1 else 0)

/-- **The sign at a vertex**, for faces coloured `a, b, c` round it in the order
of `node`. The edges between them then carry `a + c`, `b + a` and `c + b`.
Checked over all colour triples. -/
theorem levi_eq_neg_one_pow : ∀ a b c : Color, a ≠ b → b ≠ c → c ≠ a →
    levi (fin3OfColor (a + c)) (fin3OfColor (b + a)) (fin3OfColor (c + b)) =
      (-1) ^ (tau (a + c) a b + tau (b + a) b c + tau (c + b) c a) := by
  decide

/-! ### Counting -/

private theorem hi_of_ne : ∀ a b : Color, b + a ≠ 0 → b + a ≠ .c1 →
    (b.hi = false ↔ a.hi = true) := by decide

private theorem hi_of_c1 : ∀ a d : Color, a + d = .c1 → d.hi = a.hi := by decide

private theorem hi_of_c2 : ∀ a d : Color, a + d = .c2 → d.hi = !a.hi := by decide

private theorem eq_c2_of_three : ∀ p q r : Color, p ≠ 0 → q ≠ 0 → r ≠ 0 → p ≠ q → q ≠ r →
    r ≠ p → p = .c2 ∨ q = .c2 ∨ r = .c2 := by decide

omit [Fintype D] [DecidableEq D] in
/-- A finite set closed under a fixed-point-free involution has an even number
of elements. -/
private theorem even_card_of_involution {s : Finset D} (g : D → D) (hg : ∀ x ∈ s, g x ∈ s)
    (hgg : ∀ x, g (g x) = x) (hne : ∀ x, g x ≠ x) : Even s.card := by
  have h : ∑ _x ∈ s, (1 : ZMod 2) = 0 :=
    Finset.sum_involution (fun x _ => g x) (fun _ _ => by decide)
      (fun x _ _ => hne x) (fun x hx => hg x hx) (fun x _ => hgg x)
  rw [Finset.sum_const, nsmul_eq_mul, mul_one] at h
  exact (ZMod.natCast_eq_zero_iff_even).1 h

/-- **On the sphere, every Tait colouring of a plain cubic map has sign
`(-1) ^ (V / 2)`** in Penrose's contraction. -/
theorem prod_levi_of_proper {G : Hypermap D} (hG : G.Plain) (hc : G.Cubic) (hp : G.Planar)
    {c : D → Fin 3} (hce : ∀ x, c (G.edge x) = c x) (hcn : ∀ x, c (G.node x) ≠ c x) :
    ∏ x, levi (c x) (c (G.node x)) (c (G.node (G.node x))) =
      (-1) ^ (Fintype.card (Orbit G.node) / 2) := by
  -- The colouring in the Klein four-group, and a face colouring it comes from.
  set e : D → Color := fun x => colorOfFin3 (c x) with he_def
  have he : EdgeColoring G e :=
    ⟨fun x => by simp only [e, hce], fun x => colorOfFin3_ne_zero _,
      fun x h => hcn x (colorOfFin3_injective h)⟩
  obtain ⟨k, hk, hke⟩ := exists_coloring_of_edgeColoring hG hc hp he
  have hn3 : ∀ x, G.node (G.node (G.node x)) = x := hc.node_node_node
  have hinv : ∀ x, G.node⁻¹ x = G.node (G.node x) := fun x =>
    Perm.inv_eq_iff_eq.2 (hn3 x).symm
  have hkE : ∀ y, k (G.edge y) = k (G.node (G.node y)) := fun y => by
    rw [← hk.face (G.edge y), Perm.eq_inv_iff_eq.2 (G.edgeK y), hinv]
  have heE : ∀ y, e y = k y + k (G.edge y) := fun y => (congrFun hke y).symm
  have heK : ∀ y, e y = k y + k (G.node (G.node y)) := fun y => by rw [heE, hkE]
  have hc_e : ∀ y, c y = fin3OfColor (e y) := fun y => (fin3OfColor_colorOfFin3 _).symm
  -- The sign at each dart's vertex.
  set τ : D → ℕ := fun x => tau (e x) (k x) (k (G.node x)) with hτ
  have hlocal : ∀ x, levi (c x) (c (G.node x)) (c (G.node (G.node x))) =
      (-1) ^ (τ x + τ (G.node x) + τ (G.node (G.node x))) := by
    intro x
    have h1 : k x ≠ k (G.node x) := by
      have := hk.edge (G.node x)
      rw [hkE, hn3] at this
      exact this
    have h2 : k (G.node x) ≠ k (G.node (G.node x)) := by
      have := hk.edge (G.node (G.node x))
      rw [hkE, hn3] at this
      exact this
    have h3 : k (G.node (G.node x)) ≠ k x := by
      have := hk.edge x
      rw [hkE] at this
      exact this
    simp only [hτ, hc_e, heK, hn3]
    exact levi_eq_neg_one_pow _ _ _ h1 h2 h3
  -- Multiply over all darts: each dart's `tau` is counted three times.
  have hsum3 : ∑ x, (τ x + τ (G.node x) + τ (G.node (G.node x))) = 3 * ∑ x, τ x := by
    rw [Finset.sum_add_distrib, Finset.sum_add_distrib,
      Equiv.sum_comp G.node τ, Equiv.sum_comp (G.node * G.node) τ |>.symm.trans ?_]
    · ring
    · rfl
  rw [Finset.prod_congr rfl fun x _ => hlocal x, Finset.prod_pow_eq_pow_sum, hsum3, pow_mul]
  norm_num only
  -- Split the count into its two parts.
  have hsplit : ∑ x, τ x =
      (Finset.univ.filter fun x => e x = .c2 ∧ (k x).hi = false).card +
      (Finset.univ.filter fun x => e x = .c1 ∧ (k (G.node x)).hi = false).card := by
    simp only [hτ, tau, Finset.sum_add_distrib, Finset.card_filter]
  -- The `c1` part is even: both darts of a `c1`-edge count, or neither.
  have hA2 : Even (Finset.univ.filter fun x => e x = .c1 ∧ (k (G.node x)).hi = false).card := by
    have hS : (Finset.univ.filter fun x => e x = .c1 ∧ (k (G.node x)).hi = false) =
        Finset.univ.filter fun x => e x = .c1 ∧ (k x).hi = true := by
      refine Finset.filter_congr fun x _ => and_congr_right fun h1 => ?_
      have hnx : e (G.node x) = k (G.node x) + k x := by rw [heK, hn3]
      refine hi_of_ne (k x) (k (G.node x)) ?_ ?_
      · rw [← hnx]
        exact he.ne_zero _
      · rw [← hnx, ← h1]
        exact he.node x
    rw [hS]
    refine even_card_of_involution G.edge (fun x hx => ?_) hG.edge_edge hG.edge_ne
    simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hx ⊢
    refine ⟨by rw [he.edge]; exact hx.1, ?_⟩
    rw [hi_of_c1 (k x) (k (G.edge x)) (by rw [← heE]; exact hx.1)]
    exact hx.2
  -- The `c2` part is half the number of vertices: one `c2`-dart at each vertex,
  -- and across each `c2`-edge the high bit of the face colour changes.
  have hC2 : (Finset.univ.filter fun x => e x = .c2).card = Fintype.card (Orbit G.node) := by
    rw [← Finset.card_univ]
    refine Finset.card_bij (fun x _ => orbit G.node x) (fun _ _ => Finset.mem_univ _)
      (fun x₁ hx₁ x₂ hx₂ h => ?_) (fun v _ => ?_)
    · simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hx₁ hx₂
      rcases (sameCycle_node_iff hc).1 (orbit_eq_iff.1 h) with rfl | rfl | rfl
      · rfl
      · exact absurd (hx₂.trans hx₁.symm) (he.node x₁)
      · refine absurd (hx₁.trans hx₂.symm) fun h' => he.node (G.node (G.node x₁)) ?_
        rw [hn3, h']
    · induction v using Quotient.inductionOn with
      | h x =>
        have hx2 : e (G.node (G.node x)) ≠ e x := fun h' =>
          he.node (G.node (G.node x)) (by rw [hn3, h'])
        rcases eq_c2_of_three _ _ _ (he.ne_zero x) (he.ne_zero (G.node x))
            (he.ne_zero (G.node (G.node x))) (he.node x).symm (he.node (G.node x)).symm hx2 with
          h | h | h
        · exact ⟨x, by simp [h], rfl⟩
        · exact ⟨G.node x, by simp [h], orbit_apply _ _⟩
        · exact ⟨G.node (G.node x), by simp [h], by
            show orbit G.node (G.node (G.node x)) = orbit G.node x
            rw [orbit_apply, orbit_apply]⟩
  have hhalf : (Finset.univ.filter fun x => e x = .c2 ∧ (k x).hi = false).card =
      (Finset.univ.filter fun x => e x = .c2 ∧ ¬ (k x).hi = false).card := by
    refine Finset.card_bij (fun x _ => G.edge x) (fun x hx => ?_)
      (fun x₁ _ x₂ _ h => G.edge.injective h) (fun y hy => ⟨G.edge y, ?_, hG.edge_edge y⟩)
    · simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hx ⊢
      refine ⟨by rw [he.edge]; exact hx.1, ?_⟩
      rw [hi_of_c2 (k x) (k (G.edge x)) (by rw [← heE]; exact hx.1), hx.2]
      decide
    · simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hy ⊢
      refine ⟨by rw [he.edge]; exact hy.1, ?_⟩
      rw [hi_of_c2 (k y) (k (G.edge y)) (by rw [← heE]; exact hy.1)]
      simpa using hy.2
  have hA1 : 2 * (Finset.univ.filter fun x => e x = .c2 ∧ (k x).hi = false).card =
      Fintype.card (Orbit G.node) := by
    have hsp := Finset.card_filter_add_card_filter_not
      (s := Finset.univ.filter fun x => e x = .c2) (p := fun x => (k x).hi = false)
    rw [Finset.filter_filter, Finset.filter_filter] at hsp
    omega
  rw [hsplit, pow_add, hA2.neg_one_pow, mul_one, ← hA1, Nat.mul_div_cancel_left _ two_pos]

/-! ### Penrose's formula -/

/-- **Penrose's formula**: for a plain cubic map on the sphere, the Penrose
evaluation is `(-1) ^ (V / 2)` times the number of Tait colourings, where `V` is
the number of vertices. -/
theorem penrose_eq {G : Hypermap D} (hG : G.Plain) (hc : G.Cubic) (hp : G.Planar) :
    penrose G = (-1) ^ (Fintype.card (Orbit G.node) / 2) * taitCount G := by
  unfold penrose taitCount
  -- A term is the sign for a Tait colouring, and `0` for any other colouring.
  have hterm : ∀ c ∈ Finset.univ.filter (fun c : D → Fin 3 => ∀ x, c (G.edge x) = c x),
      ∏ x, levi (c x) (c (G.node x)) (c (G.node (G.node x))) =
        if (∀ x, c (G.node x) ≠ c x) then (-1) ^ (Fintype.card (Orbit G.node) / 2) else 0 := by
    intro c hc'
    simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hc'
    split_ifs with hp'
    · exact prod_levi_of_proper hG hc hp hc' hp'
    · simp only [not_forall, not_not] at hp'
      obtain ⟨x, hx⟩ := hp'
      refine Finset.prod_eq_zero (Finset.mem_univ x) ?_
      simp [levi, hx]
  rw [Finset.sum_congr rfl hterm, Finset.sum_ite, Finset.sum_const_zero, add_zero,
    Finset.sum_const, Finset.filter_filter, nsmul_eq_mul, mul_comm]

end FourCT
