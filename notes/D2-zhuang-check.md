# D2 — step-by-step check of Zhuang, arXiv:2202.13091

Issue #43. This is the full text of the second pass. `D-topology-and-gauge-theory.md` has the
summary.

**Status: AI-written lead, under review by Gabriel.** It is not a result under the trust rule.
Two agents wrote it: a first pass, then a second pass with the primary sources. The main session
then checked two claims against the page images:

- **[KM16] p.28:** the question whether dim J♯ equals the Tait count "is equivalent to" the
  four-term relation, Conjecture 10.1.
- **[B] p.3, Corollary 2.1:** dim J♭(K) ≤ Tait(K), "an easy corollary" of [KR] Prop 4.18.

The RII computation (Step 4a) was also **re-derived independently** before merge, at Gabriel's
request, by an agent that saw only Zhuang's definitions and [KM19]. It found H⁰ = 3, H¹ = 0, H² = 6
for both orientations, and reached the same conclusion.

The papers were downloaded from arXiv with Gabriel's approval. Neither they nor the page images and
crops the text refers to are committed.

**Status: AI-written draft for review by a human mathematician. This is a lead, not a result.** It does not conclude that Zhuang's Theorem 1 or the Kronheimer–Mrowka conjecture is true or false. Every verdict is about whether *the argument as written* is supported by the sources listed. Each step has exactly one verdict: **verified in full**, **gap** or **undetermined**.

## Sources and conventions

| Key | Source | Page convention |
|---|---|---|
| [Z] | Zhuang, arXiv:2202.13091v1, 9 pp. | printed page = file p-N |
| [KM19] | Kronheimer–Mrowka, *Tait colorings, and an instanton homology for webs and foams*, arXiv:1508.07205v1 | printed = file |
| [KM16] | Kronheimer–Mrowka, *Exact triangles for SO(3) instanton homology of webs*, arXiv:1508.07207v1 (J. Topol. 2016) | printed = file |
| [Kh] | Khovanov, *sl(3) link homology*, math/0304375 (AGT 4, 2004) | journal page = file page + 1044 (e.g. p.1072 = p-28) |
| [MV] | Mackaay–Vaz, *The universal sl3-link homology*, math/0603307**v2** | printed = file |
| [AK] | Agol–Krushkal, *Structure of the flow and Yamada polynomials of cubic graphs*, arXiv:1801.00502v1 | printed = file |
| [KM25] | Kronheimer–Mrowka, arXiv:2505.02755v1 | only pp.1–12, 60–72 rendered; the text of pp.66–67 and the bibliography were also read via text extraction |
| [KR] | Khovanov–Robert, arXiv:1808.09662v1 | printed = file |
| [B] | Boozer, arXiv:1908.07133v2 | printed = file |

**Method.**
- Figures were checked on the page images, including 3–4× crops (kept outside the repository).
- Text was extracted with `pdftotext`.
- Zhuang's figures are vector drawings. I rendered them from the PDF (with a small rendering script, kept outside the repository). The dots are **not** part of the drawings: they are typeset glyphs laid on top. Dot placement can therefore only be read from the 110-dpi page images. This limitation remains (see "Sources still missing").

**Notation.**
- The four ends near a crossing are NW, NE, SE, SW.
- `)(` joins NW–SW and NE–SE. `=` joins NW–NE and SW–SE.
- **I** has vertices on {NW,NE} and {SW,SE} joined by a vertical edge. **H** has vertices on {NW,SW} and {NE,SE} joined by a horizontal edge.
- In [KM16] p.28 notation: K₀ = `=`, K₁ = `)(`, L₀ = I, L₁ = H, and K₂ = a spatial crossing.
- D(k) is the disc with k dots. Θ(a,b,c) is the theta foam with dots. x±(a,b,c) are the half-theta (co)vectors of [KM19] p.47.
- F = F₂. "dim" means dim over F.

---

## Step 1. Definitions, cube, commutativity, d² = 0

**Verdict: verified in full.** Unchanged from the first pass.

- For an oriented virtual web D, F(D) is a well-defined cochain complex.
  - Squares commute by functoriality of J♯ on isotopy classes of foams ([KM19] Def 3.10, pp.38–39; p.39).
  - d² = 0 over F.
- The figures were re-checked at 3–4×:
  - **Fig 8** (p.6): both strands point up. The **0-resolution is `)(`** and the **1-resolution is I**.
  - **Fig 9** (p.7): the zip foam with a shaded half-disc facet. There is no dot glyph in the image, and none in the extracted page-7 text near the figure. The edge map is the **dotless zip**.
  - **Fig 11** (p.8) draws the same map d.
- New consistency remark ([KM16] Thm 1.2, p.2):
  - With i = 1, the exact triangle J♯(L₀) → J♯(K₂) → J♯(K₁) → J♯(L₀) holds for a spatial crossing K₂.
  - Reading K₁ → L₀ as the standard zip, dim J♯(K₂) = dim ker + dim coker of J♯(`)(`) → J♯(I).
  - That is the total cohomology of Zhuang's one-crossing cone. So for one crossing, F(D) has the "right" total dimension.
  - Without a Z/2 grading on J♯ ([KM19] Prop 8.11, p.73), this says nothing about the Euler characteristic.

**Remarks kept from the first pass.**
- "Graded" on p.6 means only the cube degree.
- Prop 4 has a typo: J(∅) should be J(U).
- "Figure 4 4" on p.5 is a broken reference.
- Prop 11 has no statement.

---

## Step 2. The local relations of [Z] §3 (and the unnumbered p.9 figure) against [KM19]

**Verdict: gap.** It is partly presentational, with three substantive items: Prop 7 over-claims, Prop 11 is unstated, and two figure relations are mis-drawn as rendered.

**What the list is meant to be.**
- [MV] Lemma 2.3 (p.6) lists (4C), (RD), (DR), (SqR). [MV] Fig 5 (p.7) gives the dot-exchange relations, and (3D, CN, S, Θ) are on p.5.
- Zhuang's §3 plus the p.9 figure are exactly these, reduced mod 2 with a = b = c = 0:
  - neck-cutting = CN (Fig 5)
  - bigon = DR (Fig 6)
  - square = SqR (Fig 7)
  - p.9 row 1 = RD
  - p.9 row 2 = 4C
  - p.9 rows 3–4 = [MV] Fig 5 rows 1–2
- This identifies the "four-term relation" that the first pass could not read.

| [Z] item | [KM19] counterpart | Status |
|---|---|---|
| Prop 3, 4, 5, 6 | Prop 3.12(a) p.40; Prop 5.1 p.44; Prop 5.2 p.44 + Cor 4.6 p.43; Cor 4.4 p.42 | established |
| Prop 7 | sphere: Prop 5.3 p.45; standard genus-g surfaces: Prop 6.2 p.51 | the non-orientable case claimed in [Z] is **not covered** |
| Prop 8 (neck-cutting) | Prop 6.1, pp.50–51 | map-level, established |
| Prop 9 / Fig 6 (bigon = MV's DR) | proof of Prop 6.5, pp.52–53: id = ac + bd with **one** dot per term (Fig 6 p.53) | map identity established inside the proof. **[Z] Fig 6 at 4× shows a dot in both the top and the bottom half of each term.** [MV] (DR) p.6 and [KM19] have one. As drawn it is not degree-homogeneous in KR's grading, so it is probably a drawing slip. |
| Prop 10 | Prop 5.6, p.46 | established |
| Prop 11 / Fig 7 (square = SqR) | proof of Prop 6.8, p.57; Lemma 5.12 (n=4) abbreviated, p.50 | map identity established modulo the two abbreviated steps noted in the first pass. Not stated in [Z]. |
| p.9 row 1 (RD) | Lemma 5.5 (pp.45–46) + Cor 4.6 + Props 5.3, 5.6 | **verified in full**. The 9-case closure check is redone here: Θ(i,j,0) = S(i+1)S(j) + S(i)S(j+1) for all i,j ∈ {0,1,2}. |
| p.9 row 2 (4C) | Lemma 5.5 + Cor 4.6 + Props 5.3, 5.6 + Cor 4.4 | **verified in full (new)**, reading the dot on the membrane as in [MV] (4C) p.6. The boundary is a 3-component unlink, so capping with D(k₁), D(k₂), D(k₃) reduces 4C to S(k₁+k₃)S(k₂) + S(k₁)Θ(k₂,k₃,1) + S(k₁+k₂)S(k₃) + S(k₁+1)Θ(k₂,k₃,0) = 0. All 27 cases hold. With the dot moved onto a tube wall instead, cases (2,0,2) and (2,1,1) fail, so the dot position matters. |
| p.9 row 3 | [KM19] Prop 3.9 p.36 (u₁+u₂+u₃ = 0) | **as drawn, wrong.** At 4× the first term clearly has **two** dots. u₁²+u₂+u₃ = u₁²+u₁ ≠ 0 on the theta web (Prop 5.7, p.47). Intended: one dot per term ([MV] Fig 5 row 1 with a = 0). |
| p.9 row 4 | [KM19] Prop 5.8, p.47 (u₁u₂+u₂u₃+u₃u₁ = 0) | established ([MV] Fig 5 row 2 with b = 0) |

**Maps or dimensions?** Chain homotopies need map-level identities.
- The map-level identities are available for: RD and 4C (unlink boundary, so Lemma 5.5 applies), the bigon (inside the proof of 6.5), and the square (inside the proof of 6.8, modulo the abbreviated steps).
- The *statements* Zhuang cites (6.5, 6.8) are dimension statements.
- Transfer from [MV] is not literally "verbatim". [MV] work in a quotient defined by the universal construction (Def 2.2, p.5), where "closures agree ⇒ foams equal" holds by definition. For J♯ that implication has to be supplied case by case: Lemma 5.5 for unlink boundaries, Prop 5.7 for the theta web, the proof of Prop 6.5 for the bigon.

---

## Step 3. Orientation (in)dependence of e(D)

**Verdict: gap.** It is substantive. What Zhuang needs is, by [KM16] §10, **equivalent to the conjecture itself**.

### 3a. Orientation independence ⇔ (T4) — *verified in full*

(T4) dim J♯(K₁) − dim J♯(L₀) = dim J♯(K₀) − dim J♯(L₁), i.e. `)(` − I = `=` − H.

This is [KM16] eq. (20), p.28: dim K₀ − dim K₁ + dim L₀ − dim L₁ = 0. It is also the [AK] Fig 2 relation I + `=` = H + `)(` (p.6), and the [KM25] "Tutte relation" (p.66).

**(⇒)** Start from planar webs K₀, K₁, L₀, L₁ that differ in a disc, with outside part P. Put a virtual crossing in the disc to get D.
- If the two strands through the crossing lie on different edges of D, reversing one of them switches the crossing type between (`)(`, I) and (`=`, H) ([Z] Fig 8 plus rotation).
- The two Euler characteristics are e = K₁ − L₀ and e = K₀ − L₁. So orientation independence gives (T4).
- Degenerate case: P joins two adjacent ends by a vertex-free arc, e.g. NE–SE. Then K₁ = 3X, K₀ = X, L₀ = 2X (a bigon, [KM19] Prop 6.5), and L₁ = 0 (an embedded bridge, [KM19] Prop 3.12(b), p.40). (T4) reads 3X − 2X = X − 0, so it holds unconditionally.

**(⇐)** e(D,o) is a multilinear sum over crossings of the per-crossing differences "dim(0-res) − dim(1-res)", with the other crossings resolved into planar webs. (T4) makes each difference type-independent.

### 3b. (T4) ⇔ the conjecture — *verified in full* (characterisation written out here; stated in three sources)

[KM16] p.27–28 states that the Tait count τ is "uniquely characterized, for planar webs" by four properties:
- (a) τ(circle) = 3;
- (b) bridge ⇒ 0;
- (c) multiplicativity;
- (d) the Tutte relation (19).

It then says (a)–(c) hold for dim J♯ (proved in [KM19]). Hence the question of whether dim J♯ equals the Tait count "is equivalent to the following conjecture": Conjecture 10.1 = (T4).

No proof of the characterisation is given there. [KM25] p.67 repeats it and cites Tutte 1998 and [AK]. [AK] p.6 presents the planar chromatic algebra by exactly (T4) and the lollipop relation, with loop value Q−1. It says these "are precisely the relations defining the flow polynomial of a planar cubic graph", deferring details to Fendley–Krushkal (their ref [6]). Tait(G) = F_G(4) for cubic G because a nowhere-zero Z₂²-flow on a cubic graph is a Tait colouring ([AK] p.12–13, citing Diestel Prop 6.4.5).

**An elementary proof of uniqueness (written here, to be checked).** Let f be any function on planar webs satisfying (a)–(d) and f(∅) = 1. Induct on the number of vertices.
- If W has a vertex, pick a face F of size k ≥ 1.
- k = 1: F is a loop and the loop's stem is a bridge, so f(W) = 0.
- k ≥ 2: pick an edge ε on F with distinct endpoints. (T4) gives f(W) = f(W_H) + [f(`)(`) − f(`=`)]. The bracketed webs have 2 fewer vertices. The flipped web W_H has the same vertex count, and F shrinks to size k − 1.
- Iterate until F has size 1. If an edge of F becomes a bridge, the value is 0 by (b).
- Vertex-free webs are unions of circles, handled by (a) and (c).

So f is determined, and f = Tait since Tait satisfies (a)–(d) (checked by boundary-colour cases in the first pass). For J♯: (a) is Prop 5.1; (b) is Prop 3.12(b); (c) is Cor 4.4 (planar disjoint unions are split).

### 3c. What the new sources say about (T4) for J♯

- **[KM16] does not prove (T4).** It is stated as Conjecture 10.1 (p.28).
- The octahedral diagram (Fig 1, p.3; Thm 9.1, pp.26–27) gives a 4-periodic complex J♯(L₀) → J♯(L₁) → J♯(K₀) → J♯(K₁) → J♯(L₀) (Lemma 10.2, p.28).
- **Lemma 10.3 (p.29)** shows the left side of (20) equals 2(rank a − rank b), where a: K₀ → K₂ and b: K₂ → K₁ are standard cobordisms. So (T4) ⇔ rank J♯(a) = rank J♯(b). This is a genuine reformulation and a candidate target for anyone pursuing this.
- Remark, p.30: exactness of the 4-periodic sequence "does not appear to be true in general". The suggested rank for the dodecahedron is 5, giving 58 ≤ dim J♯(dodecahedron) ≤ 70, with the 68 bound on p.31. So (T4) cannot be obtained from exactness, unlike [KR]'s conditional route for J♭.
- The exact triangles (Thm 1.1, 1.2) involve *spatial* webs K₂, L₂. They give total dimensions, not Euler characteristics, because J♯ has no Z/2 grading. [KM25] obtains (T4) only for χ of the Z/2-graded L♯ (p.66–67).

### 3d. Can Zhuang avoid orientation independence?

- **No vertex move in [Z].** A 3× crop of Fig 2 (p.3) shows "virtual RV III" is the **three-strand** move: six ends, three crossings, no vertex. [Z] allows only RI–RIII. So the first pass's "tree trick", which moved strands across vertices, is **not available** in Zhuang's framework.
- **What the skein step needs.** At an edge ε with top vertex u (ends NW, NE) and bottom vertex v (ends SW, SE), the new crossing must have type (`)(`, I). This forces: s(NW) = s(NE) = −s(SE) = −s(SW), where s = ±1 records whether the edge points out of or into the disc.
- **Where it can fail.** Once an edge carries crossings, its orientation is tied to others by parity constraints, one per crossing between distinct edges. A step is legal only if these constraints are consistent. Zhuang gives no argument that a legal ε always exists, nor that the recursion terminates.
- **Zhuang's actual claim is too strong.** The proof on p.7 asserts e(D) = P(D) for *every* oriented D. Since P is orientation-free, that assertion implies orientation independence, hence (T4), hence (3b) the conjecture.
- **Observation (lead, conditional).** Euler-level invariance under all oriented RI–RIII uses only [KM19] Props 5.1, 6.5, 6.8, Cor 4.4 and Prop 3.12 (Step 4d). So if a legal recursion always existed, it would prove dim J♯ = Tait for all planar webs from those propositions alone. [KM16] (pp.30–31) had these tools and obtained only 58–70 / ≤ 68 for the dodecahedron. That is not a proof that the recursion must fail. But it suggests the orientation bookkeeping is where the difficulty concentrates.
  - Suggested concrete test: a computer search for a legal recursion on the dodecahedron (about 2¹⁰ leaves).

---

## Step 4. Invariance under virtual moves (Theorem 2, Corollary 2)

**Verdict: gap.** Chain level:
- RI: verified (4b).
- RII: **contradicted by an explicit computation, for both orientations** (4a).
- RIII: undetermined (4c).

Euler level (Corollary 2): holds for all oriented RI–RIII (4d). No vertex move is claimed.

### 4a. RII chain-level counterexample — *verified in full; it stands, and extends to both orientations*

**Diagram and cube.**
- Take two circles overlapping in a lens, with virtual crossings c₁ (bottom) and c₂ (top). One RV II move makes them disjoint, so F(O⊔O) = J♯(O⊔O) ≅ F⁹ in degree 0 ([KM19] Cor 4.4, Prop 5.1).
- Cube, Fig 8 convention (0-res = oriented smoothing):
  - (0,0) = two disjoint circles.
  - (1,0) and (0,1) = theta webs.
  - (1,1) = a 4-cycle with two doubled edges.
- This was traced by hand for **both** orientations:
  - Parallel (one circle cw, one ccw): crossing type (`)(`, I); the (0,0) circles lie side by side.
  - Antiparallel (both ccw): crossing type (`=`, H); the (0,0) circles are nested.
- In both cases each edge map out of degree 0 is the zip O⊔O → θ.

**Ingredients, each checked in [KM19]:**
1. J♯(O⊔O) has basis D(k₁)⊔D(k₂), 0 ≤ kᵢ ≤ 2 (Cor 5.4 p.45, Cor 4.4 p.42).
2. The zip is dotless ([Z] Fig 9, checked above). By functoriality, Z(D(k₁)⊔D(k₂)) is the half-theta vector x₋(k₁,k₂,0) ([KM19] p.47, proof of Prop 5.7). Identifying the composite foam with the planar half-theta is an elementary isotopy inside R²×[0,1].
3. **D(2)⊔D(2) ∈ ker Z.** Dots act as the edge operators u_e (Def 3.8, p.36), so x₋(2,2,0) = u₁²u₂²·x₋(0,0,0). By Prop 5.8 (p.47), monomials of degree ≥ 4 vanish.
4. **D(0)⊔D(0) ∉ ker Z.** Pairing with x₊(0,1,2) gives Θ(0,1,2) = 1 (Prop 5.6, p.46).
5. **Exact rank.** The six x₊(0,k₁,k₂), k₁ ≤ 1, k₂ ≤ 2, pair non-singularly with the x₋ (Prop 5.7), so they span J♯(θ)*.
   - Computing Θ(k₁+a, k₂+b, c) over all 27 functionals gives rank Z = 6.
   - ker Z is 3-dimensional, spanned by D2D2, D1D2+D2D1, and D0D2+D1D1+D2D0.

**Conclusion.**
- d¹ = (Z₁, Z₂) with Z₁ and Z₂ given by the same formula, so H⁰ = ker d¹ ≅ F³.
- By items 3–4 alone, 0 < dim H⁰ < 9. So F(lens) is not homotopy equivalent to F⁹ concentrated in **any** single degree.
  - This uses neither the (1,1) dimension nor the Euler characteristic.
  - With e = 9 − 12 + 12 = 9 (Props 5.7, 6.5), H² ≥ 6.
- The same holds for the antiparallel lens.

**Readings of [Z], checked.**
- Fig 8: 0-res `)(`. Fig 9: no dots.
- Fig 2: the moves are drawn **unoriented**.
- §4 (p.6) says the orientations' sole role is to choose resolutions, and places no restriction on oriented moves.
- Even if RII were restricted to one orientation, *both* orientations fail, so the counterexample does not depend on this reading.

**Why, compared with [Kh] and [MV].**
- In [Kh] Fig 30 (p.1072) the two crossing signs have oppositely ordered complexes: [smoothing → web] versus [web → smoothing].
- Both RII proofs, [Kh] §5.2 (Figs 36–41, pp.1074–1077) and [MV] Figs 7–8 (pp.8–9), use one crossing of each sign. The both-smoothed resolution (D₁₀ in [Kh] Fig 36) sits in the **middle** degree, next to the digon web. [MV] place ⟨D′⟩ in the middle column.
- In [Z] there is one crossing type, so both RII cubes have the both-smoothed resolution at the degree-0 corner. That is the sl₃ cube of σ², not σσ⁻¹.

**Effect on Theorem 1.** Zhuang's proof of Theorem 1 uses only Corollary 2 (Euler level). Corollary 2 cannot be derived from Theorem 2 for RII, but it holds independently (4d). So 4a refutes the *stated chain-level* Theorem 2. It does not by itself break the Theorem 1 argument; the load-bearing gap is Step 3.

### 4b. RI chain level: does "carries verbatim" hold? — *verified in full (for [MV]'s maps)*

- **Citation.** Zhuang cites "[9], Figure 7". In [MV] arXiv v2, **RI is Figure 6** (p.7) and Figure 7 is RIIa (p.8). The published AGT numbering may differ; that version is not available. Zhuang's Fig 11 matches [MV] Fig 6 in shape (d, h, f⁰, g⁰).
- **Kinks.** With one crossing type, both kinks give [J(arc ⊔ O) → J(arc with bigon)], i.e. [MV]'s Fig 6 situation; the mirror kink is its reflection.
- **Identities [MV] use** (p.7):
  - g⁰f⁰ = id ("immediate")
  - df⁰ = 0 (via DR and RD)
  - dh = id (via DR)
  - f⁰g⁰ + hd = id (via 4C)
- **J♯ checks done here.** Zhuang's f⁰ = Σᵢ (sheet with 2−i dots)⊔(cup with i dots) equals [MV]'s f⁰ by neck-cutting (Prop 6.1). Local relations extend globally by Cor 4.6 (p.43).
  - *g⁰f⁰ = id*: the only surviving term is sheet ⊔ S(2) = sheet (Prop 5.3; Cor 4.4 for the split sphere).
  - *df⁰ = 0*: the local boundary is a theta web. df⁰ = Σᵢ x₋(2−i, i, 0), and pairing with x₊(a,b,c) gives Σᵢ Θ(2−i+a, i+b, c) = 0 for all (a,b,c). By Prop 5.7 non-degeneracy, df⁰ = 0.
  - *dh = id*: this is the bigon identity id = ac + bd, established in the proof of [KM19] Prop 6.5 (pp.52–53). d∘h is isotopic to its right-hand side.
  - *f⁰g⁰ + hd = id*: the local boundary is a 3-component unlink (arc-double A, bottom circle B, top circle T), so Lemma 5.5 applies. With [MV]'s dot placement (dot on the membrane in one term of h):
    Σᵢ S(2−i+k_A)S(k_B)S(i+k_T) + Θ(k_A,k_B,0)S(k_T+1) + Θ(k_A,k_B,1)S(k_T) = S(k_A)S(k_B+k_T)
    holds in all 27 cases. With the dot on the A-sheet or the B-tube instead, it fails in 2 cases.
- **Caveats.**
  1. Identifying each composite's closure as a product of spheres and theta foams is my elementary topology.
  2. Zhuang's Fig 11 dots in h cannot be resolved at 110 dpi. The verification is of [MV]'s maps.
- **So:** RI's invariance carries over. It is not "verbatim", because each [MV] justification must be replaced by a J♯ argument (Lemma 5.5, Prop 5.7, proof of 6.5, Cor 4.6).

### 4c. RIII chain level — *undetermined*

- [MV]'s RIII (pp.9–10, Fig 9) goes through a complex Q using RII-type homotopies (Bar-Natan's method). Those rest on the RII equivalence, which fails here (4a).
- [Kh] §5.3 (pp.1077–1079) treats one braid-like RIII with all crossings of the same sign (Fig 42) by a direct splitting (Prop 12, using digon and square decompositions). It then reduces other RIII's to it "modulo type I and II moves", which needs chain-level RII.
- In [Z] the braid-like RIII has the same cube shape as [Kh]'s, so [Kh] Prop 12 *may* transfer. I did not check it. The cyclic RIII is not covered by either source's direct argument.

### 4d. Euler level (Corollary 2) — unchanged, with one correction

- RI (both kinks), RII (both orientations), RIII braid-like and RIII cyclic all hold from [KM19] Props 5.1, 6.5, 6.8, Cor 4.4 (computations in the first pass, re-derived for braid-like RIII).
- **Correction:** the vertex move is **not** among Zhuang's moves (Fig 2). The first pass's finding that "the vertex move needs (T4)" is therefore not a gap in Theorem 2 as stated. It matters only for the orientation workaround (3d).

---

## Step 5. The conclusion: e = P and dim J = Tait

**Verdict: gap.** The logic and signs are verified. The needed input is Step 3.

- **Signs (unchanged).** P(D) = (−1)^{V/2}E(D). Prop 1 is consistent with [KM25] p.67 (all Tait colourings of a planar web have sign (−1)^{n/2}). Prop 2 follows from the ε-identity.
  - [AK] p.12 independently describes the Penrose number as ±R_G(1). It is a signed Tait count on immersed diagrams, invariant under regular homotopy and satisfying the same skein relation.
- **Base case.** Vertex-free oriented virtual diagrams reduce to unlinks by RI–RIII, and e is invariant under every oriented RI–RIII (4d). So e(vertex-free) = 3^k is available **without** Theorem 2.
- **Skein step.** Requires compatible orientations (3d). Zhuang's claim "e(D) = P(D) for all oriented D" is equivalent to the conjecture (3a + 3b).
- **Contrast with [KM25] p.66.** For χ(L♯) of spatial webs, the same reduction (skein relation to remove vertices, crossing change to reach an unlink) works. There, crossings are spatial with a crossing-change relation and a Z/2 grading. Zhuang's virtual crossings carry neither, so the orientation type enters e.

---

## Step 6. Transfer to J♭ (Khovanov–Robert); would it force 60?

**Verdict: gap.** Same gaps. The first pass's unsourced claim is now sourced, and a new tension appears.

- **dim J♭ ≤ Tait.** [B] Cor 2.1 (p.3) calls it "an easy corollary" of [KR] Prop 4.18.
  - [B] Thm 2.3 (p.2) also quotes, from KM's *A deformation of instanton homology for webs*, dim J♯(K) ≥ Tait(K). I have not seen that source.
  - If correct, the conjecture is equivalent to the upper bound dim J♯ ≤ Tait.
- **Dodecahedron W₁.**
  - [B] p.3: 58 ≤ dim J♭(W₁) ≤ 60.
  - [B] p.1 and §4: the computer results show it "must be either 58 and 60" and suggest 58. Remark 4.2 notes the bound 58 persists across generating sets.
  - The J♭ version of Zhuang's Theorem 1 would force 60. That is **in tension with Boozer's computational evidence**, which is evidence, not proof.
- **RII counterexample for J♭.** It carries over: the sphere and theta evaluations agree ([KR] Thm 2.35; [KM19] p.72), and non-degeneracy holds by construction ([B] Remark 2.2, p.3). So Z(D2⊔D2) = 0 and Z(D0⊔D0) ≠ 0 again.
- **(T4) for J♭.** Still open ([KR] p.47). [B] Remark 2.2 also notes J♭ is not known to be monoidal. The unlink values still hold by circle removal ([KR] Prop 3.12, Fig 18, p.38).

---

## Changes from the first pass

1. **Step 4a: the counterexample stands and is strengthened.**
   - It now needs only Prop 5.8 (degree-4 monomials vanish) and Θ(0,1,2) = 1. Rank 6 and kernel 3 were recomputed via Prop 5.7.
   - It **also holds for the antiparallel orientation**. The first pass had treated antiparallel RII as unchecked.
   - Fig 8 and Fig 9 readings were confirmed at 3–4×.
2. **Step 4, vertex move: withdrawn as a Theorem 2 gap.** Fig 2's RV III is the three-strand move, and [Z] lists no vertex move. The vertex-move analysis now only rules out the "tree trick" (Step 3d).
3. **Step 4b, RI: from "plausible, partly checked" to verified in full (for [MV]'s maps).**
   - All four homotopy identities were checked for J♯.
   - "Verbatim" is not literally accurate.
   - The citation "Figure 7" does not match [MV] v2, where RI is Figure 6.
4. **Step 4c, RIII chain level: from unchecked to undetermined, with reasons.** [MV]'s route needs RII; [Kh]'s reduction needs RII.
5. **Step 2.**
   - The p.9 four-term relation is identified as [MV] (4C) and verified in full for J♯.
   - p.9 row 3 is confirmed (at 4×) to be drawn with a two-dot term, which is wrong as drawn.
   - The first pass's "rendering artifact" guess is withdrawn.
6. **Step 3.** The equivalence "orientation independence ⇔ (T4) ⇔ conjecture" is now sourced to [KM16] §10, pp.27–28 (Conjecture 10.1), besides [KM25] p.67.
   - The characterisation of Tait counts has an elementary proof written out here, and matches [AK] p.6's presentation.
   - [KM16] Lemma 10.3 gives the reformulation rank a = rank b.
   - The p.30 remark rules out exactness.
7. **Step 6.** dim J♭ ≤ Tait is sourced ([B] Cor 2.1 p.3). Boozer's "58 or 60, suggests 58" is noted as tension with the J♭ transfer.

The Step 1 and Step 5 verdicts are unchanged.

---

## Sources still missing

- **Tutte, *Graph theory as I have known it* (1998)** and **Fendley–Krushkal** ([AK] ref [6]). These would give the published proof that (T4) + lollipop + loop value characterise flow/Tait counts on planar cubic graphs. That would confirm the elementary argument in 3b.
- **Kronheimer–Mrowka, *A deformation of instanton homology for webs*** (GT 2019). It would confirm dim J♯ ≥ Tait ([B] Thm 2.3), which would make the conjecture equivalent to an upper bound.
- **[MV] published AGT version.** To settle whether "Figure 7" is RI there.
- **[KM16] ref [5]** (dodecahedron foam calculations). Would confirm the rank-5 claim behind the 70 bound.
- **Zhuang's LaTeX source, or the dot-glyph positions.** The dots are typeset overlays on vector drawings, so this would settle the dots in Figs 6 and 11 and p.9.
- **[KM25] pp.13–59.** For the octahedral-diagram proof and the grading conventions behind its Tutte relation.
- **Published JEMS [KM19].** For a numbering check.
- **A reference on oriented virtual Reidemeister moves (e.g. Polyak-type generating sets).** Not needed now that both RII orientations fail, but it would help formalise which oriented moves Theorem 2 is meant to cover.

---

## Overall assessment (AI-written lead, not a result)

- **Sound parts.**
  - The cube F(D) is a well-defined complex.
  - The Penrose sign conventions and skein relation are correct.
  - The formal deduction "skein + unlinks + invariance ⇒ e = P ⇒ dim J = Tait" is sound.
- **Theorem 2 (chain level).**
  - RI invariance does carry over to J♯ with the Mackaay–Vaz maps, but each identity needs its own J♯ justification.
  - RII fails, by an explicit computation using only [KM19] Props 5.6–5.8 and Cor 4.4/5.4. The lens complex has H⁰ = F³ and H² ≥ 6, for **either** orientation. The cause: one crossing type makes every RII cube behave like sl₃'s σ², not σσ⁻¹.
  - The failure is at chain level only. Corollary 2 (Euler level) still holds for all of Zhuang's moves from KM's dimension relations.
- **The decisive gap is orientation.**
  - Zhuang's skein induction needs e(D) to be independent of the auxiliary orientations, or a bookkeeping argument he does not give.
  - Orientation independence is equivalent to the four-term Tutte relation (T4) for dim J♯.
  - By [KM16] §10 (Conjecture 10.1, pp.27–28; also [KM25] p.67 and [AK] p.6), (T4) is equivalent to the Kronheimer–Mrowka conjecture itself.
  - The virtual-move framework (no vertex move) offers no evident way around this.
  - If a restricted, orientation-compatible recursion always existed, the conjecture would follow from KM19's bigon and square relations alone. [KM16] did not obtain that from the same tools, but that does not prove it impossible.
- **J♭.** The same argument would force dim J♭(dodecahedron) = 60, whereas Boozer's computations suggest 58.

Everything above should be re-checked by a human. Priorities:
1. The 4a computation, especially the identification of the zip composite with x₋(k₁,k₂,0).
2. The elementary characterisation proof in 3b.
3. The 27-case closure checks in Step 2 and Step 4b.
4. The suggested computer test of the restricted recursion on the dodecahedron.
