# Workstream D — Topology and gauge theory

Results log. Newest first. One row per result, added in the pull request that
produced it.

A row belongs here only if it meets the trust rule: a Lean theorem that builds
on the pinned toolchain, or a script whose output reruns identically from a
clean checkout. Leads, partial arguments and AI-written summaries go under
"Open leads" instead, and are not results.

| Date | Result | Evidence | Tier | PR |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Open leads

- **Is dim J♭(dodecahedron) 58 or 60?** Boozer (2019) proved it is one of the
  two. It is the smallest web where the combinatorial theory's dimension is
  unknown. Zhuang (2022) claims his method also gives `dim J♭ = Tait` for
  planar webs, which would force 60. See D1 below.
- **Zhuang's argument, checked (D2, lead under review).** The step it leaves out,
  independence of the edge orientations, is equivalent to the four-term Tutte
  relation for dim J♯. By Kronheimer–Mrowka's own reformulation (1508.07207 p.28,
  Conjecture 10.1), that is equivalent to the conjecture. Its chain-level
  invariance theorem fails for RII. See D2 below and `D2-zhuang-check.md`.
- **The plan's status note needs updating.** Kronheimer–Mrowka (2025) proved
  the SU(3) analogue of their conjecture, and Zhuang (2022) claims the
  conjecture itself. "The route through J♭ is closed" needs qualifying. See
  D1 below. This is a lead for Gabriel and Cowork, not a result.

---

# D1 — Foam evaluation against Tait counts: specification (Phase 1)

Issue #40. Phase 1 is this specification; Phase 2 waits for Gabriel's decision.

**Sources read** (arXiv versions, downloaded with Gabriel's approval, and not
committed to the repository):
- Kronheimer–Mrowka, *Tait colorings, and an instanton homology for webs and
  foams*, arXiv 1508.07205 (JEMS 2019). Cited below as **KM19**.
- Khovanov–Robert, *Foam evaluation and Kronheimer–Mrowka theories*, arXiv
  1808.09662 (Adv. Math. 2021). Cited as **KR**.
- Boozer, *Computer bounds for Kronheimer–Mrowka foam evaluation*, arXiv
  1908.07133v2 (Exp. Math. 2021). Cited as **B19**.
- Boozer, *The combinatorial and gauge-theoretic foam evaluation functors are
  not the same*, arXiv 2304.07659v1 (Math. Ann. 392, 2025). Cited as **B23**.
- Zhuang, *The dimension of Kronheimer–Mrowka instanton homology group for
  plane trivalent graphs*, arXiv 2202.13091v1 (2022, one version, no journal
  reference). Cited as **Z22**.
- Kronheimer–Mrowka, *SU(3) instanton homology for webs and foams*, arXiv
  2505.02755v1 (2025). Cited as **KM25**.

**How they were read.** The papers were read from extracted text, so figures
were not seen and the ♯/♭ superscripts were recovered from context. Page
references are to the arXiv PDFs; journal versions may be numbered
differently. KM's *A deformation of instanton homology for webs* (arXiv
1710.05002) is cited below only as B19 reports it, and was not read.

## The theories, and what is proved about them

Webs are trivalent graphs; planar webs lie in `R² ⊂ R³`. `Tait(K)` counts
3-edge-colourings with labelled colours, so a circle has 3. All the theories
below are over `F = F₂`.

**J♯, the gauge theory (KM19).**
- **Non-vanishing (Thm 1.1, p.4):** `J♯(K) = 0` iff `K` has an embedded
  bridge. This holds for every web in `R³`, and for planar webs it means "has
  a bridge".
- **The conjecture (Conj 1.2, p.4):** for planar `K`, `dim J♯(K) = Tait(K)`.
  With Thm 1.1 it would imply the Four Colour Theorem (p.4–5).
- **Proved equalities:** `dim J♯ = Tait` for planar bipartite webs, and for
  webs that reduce to unlinks by 0-, 1-, 2-, 3- and 4-gon moves (§6.5, p.58).
  So a minimal counterexample has no face with at most four sides.
- **The inequality:** `dim J♯ ≥ Tait` is proved in KM's *Deformation* paper
  (B19, Thm 2.3). We did not read it.
- **Computability:** J♯ is defined by gauge theory. This program cannot
  compute it. Only its bounds are combinatorial.

**J♭, the combinatorial counterpart** (KM19 §8.3, p.71–73; made rigorous by
KR).
- **Definition:** closed foams in `R³` are evaluated by KM's rules. KR prove
  this well-defined: it is their formula `⟨F⟩ = Σ_c P(F,c)/Q(F,c)` over the
  admissible colourings, with `E₁ = E₂ = E₃ = 0` (KR Thm 2.35, p.23). `J♭(K)`
  is then the span of the half-foams bounding `K`, modulo the radical of the
  pairing (KR Prop 4.3, p.42).
- **Upper bound:** `dim J♭(K) ≤ Tait(K)` for every planar web. This follows
  from KR Prop 4.18 and B19 Cor 2.1, and we read it the same way.
- **Equality where known:** `dim J♭ = Tait` for reducible webs (KR p.52; B19
  eq. 2).
- **In general** it is open. KR ask whether `dim J♭ = Tait` for all planar
  webs (B19 Q2.1). They do not conjecture freeness of their state space
  (KR p.4).
- **Consequence:** since `dim J♭ ≤ Tait`, non-vanishing of `J♭` on
  bridgeless planar webs would already imply the Four Colour Theorem.
- **KR's parent theory ⟨Γ⟩** over `F₂[E₁,E₂,E₃]`. It is projective of rank
  `Tait` once the discriminant is inverted (Prop 4.13). It is free of rank
  `Tait` over `F₂[E]`, with `E₁, E₂ ↦ 0` and `E₃ ↦ E` (Prop 4.18). Whether it
  is free over the full ring is open.

**Boozer's computations (B19).**
- **What he computes:** lower bounds `β(K) ≤ dim J♭(K)`, as ranks over `F₂` of
  pairing matrices. These are Gram matrices of up to about 7,000 half-foams,
  generated by four "non-reducible" moves from reducible webs.
- **The code:** Mathematica, "available from the author's website". The run
  time is not stated.
- **Webs:** seven non-reducible planar webs. W1 is the dodecahedron, 20
  vertices, "the smallest nonreducible web". W2–W7 are fullerenes with 24–34
  vertices.

  | Web | β = lower bound on dim J♭ | Tait |
  | --- | ---: | ---: |
  | W1 | 58 | 60 |
  | W2 | 120 | 120 |
  | W3 | 162 | 162 |
  | W4 | 178 | 180 |
  | W5 | 188 | 192 |
  | W6 | 248 | 252 |
  | W7 | 308 | 312 |

- **Proved:** `dim J♭ = Tait` for W2 and W3.
- **The dodecahedron:** `dim J♭(W1)` is either 58, with graded dimension
  `9q⁻³+20q⁻¹+20q+9q³`, or 60, with `10q⁻³+20q⁻¹+20q+10q³` (p.13). The paper
  "suggests" 58, but does not prove it.
- **Earlier bounds:** `58 ≤ dim J♭(W1) ≤ 60` and `60 ≤ dim J♯(W1) ≤ 68`
  (B19 Thms 2.4–2.5).

**B23: J♭ and J♯ differ as functors.**
- **The construction:** a 4-periodic complex built at the fullerene W4 (28
  vertices). Its homology under J♭ vanishes at one corner and not at the
  opposite one, which J♯ forbids (KM's octahedral lemma).
- **What it shows:** the restriction of J♯ to planar webs is not J♭ as a
  functor.
- **What it does not show:** it shows no difference in dimension. The paper
  says it "does not refute" the Kronheimer–Mrowka conjecture.
- `dim J♭(W4)` is 178 or 180, undetermined.

**L♯, the SU(3) theory (KM25).**
- **Theorem 1.1 (p.4), proved:** for planar `K`, `dim L♯(K) = Tait(K)`.
- **No non-vanishing theorem:** `L♯` vanishes on the tangled handcuffs, a
  spatial web with no embedded bridge (Prop 10.4, p.80).
- **Our reading:** for planar webs, non-vanishing of `L♯` on bridgeless webs
  is then equivalent to the Four Colour Theorem, so it repackages the problem
  rather than solving it. KM25 do not mention the Four Colour Theorem.
- **The SO(3) statement:** KM25 describe it only as "stated as a conjecture in
  [18]". They cite neither Zhuang nor Boozer.

**Z22: a claimed proof of the conjecture.**
- **The claim** (Theorem 1, p.2): `dim J♯(G) = Tait(G)` for every plane
  trivalent graph, "suggesting that our methods also works for" J♭.
- **The argument:**
  - A cube of resolutions over virtual diagrams.
  - Its Euler characteristic satisfies Penrose's skein relation, taken from
    Jaeger (1989).
  - Invariance under virtual Reidemeister moves is "similar to" Khovanov's
    sl₃ proof.
- **How much is written out:** only RI is shown, and it is "carries verbatim".
  RII, RIII, and independence of the auxiliary edge orientations are not
  written out. The bigon and square foam identities are cited as "implicit"
  in KM19's proofs.
- **Our readers' assessment:** a sketch that does not, as written, establish
  the theorem. No definite error was found, and a gap is not a refutation.
- **Later work:** it is cited by neither B23 nor KM25, and KM25 still call
  the statement a conjecture.
- **A test it makes:** if the method also gives J♭, then
  `dim J♭(dodecahedron) = 60`. B19 leaves 58 open, so settling that case
  would test the claim.

## What this means for D1 as #40 described it

- **Almost every small web is uninformative.** On reducible webs both J♭ and
  J♯ equal the Tait count by theorem, so computing them re-derives known
  results. B19 calls the dodecahedron (20 vertices) the smallest
  non-reducible web. So below 20 vertices every planar web is reducible, and
  up to 20 vertices only the dodecahedron is informative.
- **"Ranks exceed Tait counts" cannot come from J♭.** Its dimension is at
  most the Tait count, by theorem. The plan's kill signal for D ("foam ranks
  exceed Tait counts on some web") is a statement about J♯, which this
  program cannot compute. So the plan's risk table should say so.
- **Only lower bounds on J♭ are computable.** Its spanning set is infinite,
  so computation gives lower bounds, exact only when they reach the Tait
  count, as for B19's W2 and W3.

## Phase 2 options, for Gabriel's decision

1. **Reproduce B19 with open, independent code.**
   - The pieces: a closed-foam evaluator (KR's formula at `E = 0`), a
     half-foam generator, and rank computation over `F₂`.
   - Two implementations, per the house rules.
   - Positive controls: KR's examples (the sphere with dots, the theta foam,
     `Γ × S¹`), `dim J♭ = Tait` on small reducible webs, and B19's
     lower-bound table for W1–W7.
   - Output: the program's first open tool in workstream D, and a check on a
     published computation.
2. **Try to settle `dim J♭(dodecahedron)`.**
   - Enlarge the half-foam families beyond B19's single moves. B19 Remark 3.4
     left iterated cobordisms untried.
   - **Reaching rank 60 would prove `dim J♭(W1) = 60 = Tait`.** That settles
     the first open case, answers KR's question for the smallest non-reducible
     web, and is consistent with Z22's J♭ claim.
   - **Staying at 58 proves nothing:** it's only a lower bound. Showing 58
     would need a new upper-bound argument.
   - Needs 1 first, and a stated cap on effort.
3. **Stop D1 at this review.** Update the plan's status note, and leave D's
   computational work until a task with a sharper target.

**Recommendation:** option 1, then option 2 with a cap. Separately, have
Cowork update the plan's D status note: the 2025 SU(3) theorem, Z22's claim
and its reception, and the qualification of "the route through J♭ is
closed". B23 closes the route through proving J♭ = J♯ as functors. It does
not close the route through J♭ non-vanishing, which, since `dim J♭ ≤ Tait`,
would itself imply the theorem.

---

# D2 — A check of Zhuang's claimed proof (lead, under review)

Issue #43. The full text is in `D2-zhuang-check.md`. **Everything in this section is an AI-written lead,
under review by Gabriel, and not a result.** It says nothing about whether the Kronheimer–Mrowka
conjecture is true or false. It judges only whether Zhuang's argument, *as written*, is supported by
its sources.

**Verdicts, step by step:**

| Step | Verdict |
| --- | --- |
| 1. The cube of resolutions is a well-defined complex | verified in full. Squares commute because foams in disjoint balls are isotopic, which Zhuang only asserts |
| 2. The local foam relations of §3 | gap. Prop 7 over-claims, Prop 11 has no statement, and two relations are drawn wrongly. The bigon and square identities are established inside [KM19]'s proofs, not in its statements |
| 3. Independence of the auxiliary edge orientations | **gap, equivalent to the conjecture itself** (below) |
| 4. Invariance under virtual moves (his Theorem 2) | gap. RI holds, but "verbatim" from Mackaay–Vaz is not accurate: each identity needs its own J♯ proof. **RII fails at chain level.** RIII is undetermined. The Euler-characteristic version (his Corollary 2) holds for all his moves |
| 5. The conclusion, e = Penrose number, so dim = Tait | gap. The logic and signs are sound, but the input is Step 3 |
| 6. The same argument for J♭ | gap, the same gaps. It would force dim J♭(dodecahedron) = 60, whereas Boozer's computations suggest 58: evidence, not proof |

**The decisive point (Step 3).**
- Zhuang's induction needs his Euler characteristic to be independent of the orientations he puts on
  the edges. He neither shows this nor gives a bookkeeping argument that avoids it. His proof asserts
  e(D) = P(D) for every oriented diagram.
- That independence is equivalent to the four-term "Tutte relation" for dim J♯ of planar webs. Tait
  counts satisfy the relation.
- Kronheimer–Mrowka, *Exact triangles* (arXiv 1508.07207, J. Topol. 2016), p.28, state that relation
  as Conjecture 10.1. They say the question whether dim J♯ equals the Tait count "is equivalent to"
  it. The main session checked this on the page image. KM 2025 p.67 repeats it.
- So the step Zhuang leaves out is, by Kronheimer–Mrowka's own reformulation, as strong as the
  theorem he claims.

**The RII counterexample (Step 4).**
- Take two circles overlapping in a lens. One virtual RII move separates them, giving F⁹ in a single
  degree.
- Zhuang has only one crossing type, so the lens's cube is 9 → 12 → 12. Its edge map (a zip to the
  theta web) kills the doubly-dotted pair of discs ([KM19] Prop 5.8) but not the undotted pair
  (Prop 5.6).
- So the degree-0 homology has dimension strictly between 0 and 9. It is 3, and the degree-2 homology
  is at least 6. That cannot be homotopy equivalent to F⁹ in any single degree.
- This holds for both orientations. It refutes Theorem 2 *as stated*. Khovanov and Mackaay–Vaz prove
  RII using one crossing of each sign, and Zhuang's single crossing type makes every RII cube behave
  like sl₃'s σ² rather than σσ⁻¹.
- It does not by itself break his Theorem 1, which uses only the Euler characteristic.
- **Independently re-derived (2026-09-29, before merge, at Gabriel's request).** A separate agent
  computed the lens complex from Zhuang's definitions and [KM19] alone, without seeing this check.
  - It found H⁰ = 3, H¹ = 0 and H² = 6 for both orientations.
  - H⁰ = 3 follows from stated results. H¹ = 0 needs one isotopy step, and without it H² − H¹ = 6.
  - Its conclusion, not homotopy equivalent in any degree, rests on the two facts above. It also
    survives alternative readings of Zhuang's Figs 8 and 9 (dots on the zip; the 0- and
    1-resolutions swapped).

**Other findings.**
- **A reformulation worth keeping:** [KM16] Lemma 10.3 shows the Tutte relation is equivalent to two
  specific maps having equal rank.
- **Agol–Krushkal:** they present the planar algebra by the Tutte and lollipop relations, but defer the
  characterisation of Tait counts to Fendley–Krushkal.
- **An elementary proof** that the Tutte relation, with the circle, bridge and product rules,
  characterises Tait counts is written out in the full text. It needs checking by a person.
- **The J♭ bound:** dim J♭ ≤ Tait is Boozer 2019 Corollary 2.1 (p.3), from Khovanov–Robert Prop 4.18.

**Priorities for review:**
1. the RII computation;
2. the elementary characterisation proof;
3. the 27-case closure checks for Step 2 and RI;
4. the suggested test: a computer search for an orientation-compatible recursion on the
   dodecahedron. If one exists, it would matter a great deal. The same tools gave Kronheimer–Mrowka
   only bounds, though that does not show it impossible.

**Sources still missing:**
- Tutte's 1998 book, which is copyrighted and was not fetched;
- Fendley–Krushkal;
- Kronheimer–Mrowka, *A deformation of instanton homology for webs*, for dim J♯ ≥ Tait;
- Zhuang's LaTeX source, for the dot positions in his figures.

**Constraints.** Nothing from D2 goes outside GitHub, and no one is contacted (house rules). Whether
to contact the author is Gabriel's decision.
