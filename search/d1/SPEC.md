# D1 Phase 2 — Implementation specification: lower bounds on dim J♭(K)

Issue #40, Phase 2, option 1 (reproduce Boozer 2019), with option 2 (dodecahedron:
58 or 60?) as the follow-on. This document is the **only** thing the two
implementers read, apart from the papers. It says what to compute, exactly how,
and what the answers must be on the controls.

**Status of this document.** It is a specification, not a result. Nothing in it
is a result in the sense of `CLAUDE.md`. Some numbers below are marked
**[spec-check]**: the spec author confirmed them with a throwaway script while
writing this document (not committed, not an implementation, not a result). They
are expected values for the controls. Numbers marked **[B19]**, **[KR]** or
**[KM19]** are quoted from the papers.

## Contents

0. Sources, citation conventions, notation
1. What is being computed, and why it is a bound
2. Arithmetic: the rings, the KR formula, and exact evaluation over GF(4)
3. Webs: data model, faces, Tait colourings, canonical labels
4. Foams: the facet–seam representation, composition, gluing, evaluation
5. The twelve elementary cobordisms (Boozer's Figs 3 and 5), exactly
6. Half-foam generation: reducible bases, the four moves, the three modes
7. Rank computations: ℓ, ℓ_q, r, r_q, prefix ranks; output format
8. The webs: controls and W1–W7
9. Controls and expected values
10. Known pitfalls and open ambiguities (decisions for Gabriel)
11. Division of labour between Implementation A and Implementation B

Appendix A — rotation systems (authoritative web data)

---

## 0. Sources, citation conventions, notation

| Tag | Paper | Pages cited as |
| --- | --- | --- |
| **KR** | Khovanov–Robert, *Foam evaluation and Kronheimer–Mrowka theories*, arXiv 1808.09662v1 | PDF page numbers (the paper's own numbering; p.1 is the title page) |
| **B19** | Boozer, *Computer bounds for Kronheimer–Mrowka foam evaluation*, arXiv 1908.07133v2 | PDF page numbers |
| **KM19** | Kronheimer–Mrowka, *Tait colorings, and an instanton homology for webs and foams*, arXiv 1508.07205 | the paper's page numbers (§8.3 is pp.71–73) |

Notation.

- `F` = F₂ = {0,1}. All vector spaces are over F unless stated.
- `GF(4)` = F[ω]/(ω²+ω+1) = {0, 1, ω, ω²}, with ω² = ω+1, ω³ = 1. Encode an
  element a+bω (a,b ∈ F) as the integer a + 2b: 0→0, 1→1, ω→2, ω²=1+ω→3.
  Addition is XOR of the codes. Multiplication: nonzero elements are ω^0, ω^1,
  ω^2 (codes 1, 2, 3); ω^i·ω^j = ω^((i+j) mod 3).
- Colours are 1, 2, 3. X_c is the variable of colour c.
- "Web", "foam", "half-foam", "facet", "seam", "seam vertex" (= tetrahedral
  point), "dot" are as in B19 §2 (p.1–2, Fig 1) and KR Def 2.1 (p.4).
- A **half-foam with boundary K** is a foam F ⊂ R²×(−∞,0] with F ∩ (R²×{0}) = K
  (B19 p.2 calls this "top boundary K"; KR p.30 "foam into Γ").

---

## 1. What is being computed, and why it is a bound

### 1.1 Webs and Tait colourings

A **web** is a finite trivalent graph embedded in the plane R² (equivalently in
S², see §3.6), possibly with multiple edges, loops, and vertexless circles
(KR p.30, "closed web"; B19 p.1). A **Tait colouring** assigns a colour in
{1,2,3} to each edge and to each vertexless circle so that the three edge-ends at
every vertex carry distinct colours. `Tait(K)` is the number of Tait colourings
(B19 p.2). Conventions: `Tait(∅) = 1` (B19 Remark 3.2, p.4); a vertexless
circle contributes a factor 3; a web with a loop has `Tait = 0`; a planar web with
a bridge has `Tait = 0` (KR Prop 3.16, p.40).

### 1.2 Closed-foam evaluation and J♭

For a closed foam F in R³, KR define ⟨F⟩ ∈ F[E₁,E₂,E₃] (§2 below; KR eq (7),
p.12). The **combinatorial KM evaluation** is

    J♭(F) = ⟨F⟩ with E₁ = E₂ = E₃ = 0          (KR Thm 2.35, p.23; B19 eq (7), p.7)

For a web K let V(K) be the F-vector space with basis the half-foams with
boundary K (isotopy classes rel boundary). The pairing

    (F₁, F₂) = J♭(F₁ ∪_K F̄₂)                    (B19 p.3; KR p.32)

glues F₁ to the top-to-bottom mirror F̄₂ of F₂ along K. Then

    J♭(K) = V(K) / V(K)^⊥,   V(K)^⊥ = { v : (v, w) = 0 for all w ∈ V(K) }

(B19 p.3, eq (17) p.11; KM19 p.72–73; KR Prop 4.3, p.42: J♭(Γ) = ⟨Γ⟩_k). The
pairing descends to a non-degenerate form on J♭(K) (B19 Remark 2.2).

### 1.3 Why a Gram rank is a lower bound

Let S = (F₁,…,F_N) be any finite list of half-foams with boundary K, W = span S ⊂
V(K), and G the N×N Gram matrix G_ij = (F_i, F_j). Then

    ℓ := rank_F G = dim W / (W ∩ W^⊥_W)  ≤  dim (image of W in J♭(K))  ≤  dim J♭(K).

(B19 Remark 2.4, p.4; graded version B19 Thm 4.1, p.12, with proof: the image W̄
of W in J♭(K) surjects onto W/W^⊥_W because W^⊥ in V(K) is contained in the
W-radical.) So **any** finite family gives a lower bound; no completeness claim is
needed. The bound is the only output of this program. It is **not** a claim
that the family spans J♭(K).

### 1.4 Why reaching Tait(K) makes the bound exact

`dim J♭(K) ≤ Tait(K)` for every planar web (B19 Cor 2.1, p.3; Cor 3.1, p.9;
from KR Prop 4.18, p.53). Sketch (B19 p.9): with ψ : F[E₁,E₂,E₃] → F[E],
E₁,E₂ ↦ 0, E₃ ↦ E (deg E = 6), the ψ-state space ⟨K⟩_ψ is a free F[E]-module of
rank Tait(K) (KR Prop 4.18). The J♭ pairing is the ψ-pairing followed by E ↦ 0,
so the ψ-radical is inside the J♭-radical, and J♭(K) is a quotient of
⟨K⟩_ψ/E⟨K⟩_ψ, of dimension Tait(K). Hence if ℓ = Tait(K) then
`dim J♭(K) = Tait(K)` exactly (this is how B19 proves Thm 1.1 / Thm 4.2 for W2
and W3, p.13).

Graded refinements (B19 p.11–13), all computed by §7:

- ℓ_q(K) = Σ_d q^d · dim (W/W^⊥)_d ≤ qdim J♭(K) coefficientwise (B19 Thm 4.1).
- r(K) = rank of the ψ-Gram matrix over F[E] ≤ Tait(K); r_q(K) its graded rank.
- If r(K) = Tait(K) then the image of the family in ⟨K⟩_ψ is free of full rank
  with graded rank r_q(K) (B19 Thm 4.3, p.13). For W1, B19 derives the dichotomy
  dim J♭(W1) ∈ {58, 60} with qdim either 9q⁻³+20q⁻¹+20q+9q³ or
  10q⁻³+20q⁻¹+20q+10q³ (B19 eqs (35)–(37), p.13).

---

## 2. Arithmetic: the rings, the KR formula, exact evaluation over GF(4)

### 2.1 Rings and degrees (KR p.11; B19 p.6–7)

- R′ = F[X₁,X₂,X₃], deg X_i = 2.
- R = F[E₁,E₂,E₃] ⊂ R′ (symmetric polynomials), E₁ = X₁+X₂+X₃,
  E₂ = X₁X₂+X₁X₃+X₂X₃, E₃ = X₁X₂X₃; deg E_i = 2i.
- R″ = R′[(X₁+X₂)⁻¹, (X₁+X₃)⁻¹, (X₂+X₃)⁻¹].

### 2.2 Admissible colourings and bicoloured surfaces

Let F be a closed foam with facet set f(F). A **colouring** is c : f(F) → {1,2,3}.
It is **admissible** iff the three facets around every seam get three distinct
colours (B19 p.6; KR p.5 "pre-admissible"). For foams in R³ every pre-admissible
colouring is admissible in KR's stronger sense (KR Prop 2.20, p.15); **no
orientability test is needed** for anything built in this program (see §4.8).
For i<j, F_ij(c) is the closure of the union of the facets coloured i or j; it is
a closed orientable surface containing all seams (KR Prop 2.2, p.6).

### 2.3 The KR formula (KR eqs (4)–(7), p.11–12; B19 eqs (4)–(6), p.7)

    P(F,c) = Π_{facets f} X_{c(f)}^{d(f)}                       (d(f) = number of dots on f)
    Q(F,c) = Π_{1≤i<j≤3} (X_i + X_j)^{χ(F_ij(c))/2}
    ⟨F⟩    = Σ_{c admissible} P(F,c) / Q(F,c)

⟨F⟩ lies in R (KR Thm 2.17, p.13): it is a symmetric polynomial, homogeneous of
degree deg F (defined in §4.1; KR Def 2.7 p.8; B19 eq (8) p.8, Remark 3.7). If F
has no admissible colouring, ⟨F⟩ = 0. The J♭ value is the **image of ⟨F⟩ under
E₁,E₂,E₃ ↦ 0**, i.e. the **degree-0 part (the constant term) of ⟨F⟩ as a
polynomial in E₁,E₂,E₃** (KR p.23: "kills R in all positive degrees, keeping only
the ground field"). Consequently J♭(F) = 0 whenever deg F ≠ 0, and for
deg F = 0, J♭(F) = ⟨F⟩ ∈ F.

### 2.4 Exact evaluation at one point of GF(4)³ (use this; it is not approximate)

Let Φ : R″ → GF(4) be the ring homomorphism X₁ ↦ 1, X₂ ↦ ω, X₃ ↦ ω². It is
well defined because the images of X₁+X₂, X₁+X₃, X₂+X₃ are ω², ω, 1, all
nonzero. Moreover Φ(E₁) = 1+ω+ω² = 0, Φ(E₂) = ω+ω²+ω³ = 0, Φ(E₃) = ω³ = 1.

**Lemma.** For every closed foam F in R³, Φ(Σ_c P/Q) = Φ(⟨F⟩) equals the
coefficient of E₃^{deg F / 6} in ⟨F⟩ (read as 0 if deg F < 0 or 6 ∤ deg F).
Hence

    J♭(F)   = Φ(Σ_c P/Q)             if deg F = 0,   and 0 otherwise;
    ⟨F⟩_ψ   = Φ(Σ_c P/Q) · E^{deg F/6}  if deg F ≥ 0 and 6 | deg F, and 0 otherwise.

*Proof.* Σ_c P/Q = ⟨F⟩ in R″ (KR Thm 2.17), and Φ is a ring map, so Φ may be
applied term by term. ⟨F⟩ is a sum of monomials E₁^a E₂^b E₃^e with
2a+4b+6e = deg F; Φ kills all with a+b > 0. ∎

Computing Φ of one term. With X_c = ω^{c−1}, (X₁+X₂)^{m} = ω^{2m},
(X₁+X₃)^{m} = ω^{m}, (X₂+X₃)^m = 1, and m/2 ≡ 2m (mod 3):

    Φ(P(F,c)/Q(F,c)) = ω^{e(F,c)},
    e(F,c) = Σ_f d(f)·(c(f) − 1) − χ(F_12(c)) − 2·χ(F_13(c))      (mod 3).

So Φ(Σ_c P/Q) = n₀ + n₁ω + n₂ω² where n_k = #{admissible c : e(F,c) ≡ k}, taken
mod 2. **Assert** n₁ ≡ n₂ (mod 2) (the value must lie in F); the value is then
(n₀ + n₂) mod 2. **Assert** the value is 0 when deg F < 0 or 6 ∤ deg F. Both
asserts are free consistency checks and must be enabled in every run.

The same formula is used for foams with boundary (half-foams and cobordisms),
where χ(F_ij) may be odd: the exponent is still taken mod 3, which is legitimate
because every element of GF(4) has a unique square root (this is KR's square
roots of X_i, p.33–34, evaluated at Φ). Only the **pairing** of two half-foams
is guaranteed to lie in F; individual half-foam values lie in GF(4).

### 2.5 Full-polynomial evaluation (unit tests only)

To test the implementation of P/Q beyond the E₃-part, evaluate Σ_c P/Q at points
of GF(2⁸) = F[x]/(x⁸+x⁴+x³+x+1) (polynomial 0x11B) with three distinct
coordinates, and compare with the expected symmetric polynomial evaluated at the
same point (compute h_m by the recurrence of complete homogeneous polynomials,
and Schur functions by Jacobi–Trudi, s_λ = det(h_{λ_i − i + j})). Use the points
(X₁,X₂,X₃) = (0x02, 0x03, 0x05) and (0x53, 0xCA, 0x01). Any three distinct
elements work.

---

## 3. Webs: data model, faces, Tait colourings, canonical labels

### 3.1 Darts and rotation systems

A web with V trivalent vertices and m vertexless circles is stored as:

- vertices 0,…,V−1; vertex v owns the three **darts** 3v, 3v+1, 3v+2, listed in
  **counter-clockwise** order around v;
- σ(3v+k) = 3v + ((k+1) mod 3) (rotation);
- α: a fixed-point-free involution on the 3V darts (α(d) is the other end of the
  edge of d); an **edge** is a pair {d, α(d)}; its **edge id** is min(d, α(d));
  a **loop** is an edge with both darts at one vertex;
- m: the number of vertexless circles, with circle ids 0,…,m−1.

Input files (Appendix A) give, for simple graphs, each vertex's three neighbours
in CCW order: `v: w0 w1 w2`. Then dart 3v+k points to w_k, and
α(3v+k) = 3w_k + (position of v in w_k's list). Webs with multiple edges are given
by the α array directly.

Validation on load: α is an involution without fixed points; V − E + F = 2·(number
of connected components with vertices) where E = 3V/2 and F is the number of faces
(§3.2). A mirror-image rotation system (all lists reversed) describes the mirror
web; every quantity in this spec is invariant under mirroring.

### 3.2 Faces

Face successor φ(d) = σ(α(d)). **Faces** are the φ-orbits. The face of an orbit
lies on the **right** of each of its darts (travelling from the dart's vertex along
its edge). A face is written in **canonical form** (f₀, f₁, …, f_{L−1}): the orbit
starting at its minimum dart, f_{i+1} = φ(f_i). Let v_i be the vertex of f_i. Dart
f_i runs along the edge from v_i to v_{i+1} (α(f_i) is at v_{i+1}). The **leg** at
v_i is ℓ_i = σ(f_i) (the three darts at v_i in CCW order are α(f_{i−1}), f_i, ℓ_i).
Faces are listed in increasing order of their minimum dart.

A **bridge** is an edge {d, α(d)} with d and α(d) in the same face orbit. A web
with a bridge (this includes any web with a loop) has Tait = 0.

Faces are computed per connected component (each component on its own sphere).
This is legitimate: see §3.6.

### 3.3 Tait colourings and their canonical order

Edges are ordered by edge id (min dart); circles follow in circle-id order. A Tait
colouring t is the vector (t(e₀), t(e₁), …, t(circle₀), …) with entries in {1,2,3}.
The **canonical order** of Tait colourings is the lexicographic order of these
vectors. Index them 0,…,Tait(K)−1. (Only the target web's order is visible in
outputs; intermediate webs may use any order internally.)

### 3.4 The web operation REBUILD (defines every web change in §5)

`REBUILD(K; D; NV; J)` where D is a set of vertices to delete; NV is a list of new
vertices, each a CCW triple of **slots**, a slot being either a **port** (a dart p
of a deleted vertex whose edge the new slot takes over) or an **internal label**
(the two slots carrying the same label are joined by a new edge); J is a list of
**join pairs** (p, q) of ports, meaning the leg through p and the leg through q
are spliced into one edge.

Result K′:

1. Surviving vertices keep their relative order and become 0,…,s−1; their darts
   keep their slot numbers. New vertices become s, s+1, … in list order; slot k of
   new vertex i is dart 3(s+i)+k.
2. α′ of a surviving dart d, or of a new port slot with port p: start at x = α(d)
   (resp. x = α(p)) and repeat: if x is at a surviving vertex, the partner is
   (the new id of) x; if x is a port assigned to a new slot, the partner is that
   slot; if x belongs to a join pair (x, y), set x ← α(y) and continue. Reaching
   any other dart of a deleted vertex is an error.
3. Two slots with the same internal label are partners.
4. Every chain of join pairs that closes up without reaching an endpoint becomes
   one new vertexless circle, appended after the existing circles.
5. Existing circles keep their ids.

For each join pair, the **K′-edge of the join** is the K′ edge through that chain
(named by a K′ dart on it, or by its circle id). REBUILD also returns the map
`dmap` from surviving K-darts to K′-darts.

### 3.5 Identity edges

An edge of K both of whose darts are at surviving vertices, and which is not a
top edge of any local facet of the operation (§5), is an **identity edge**; it
corresponds to the K′ edge {dmap(d), dmap(α(d))}. Circles of K that are not
removed are identity circles (same id in K′).

### 3.6 Why per-component faces and S² faces are correct

J♭(K) depends only on K ⊂ S² up to isotopy: the half-space R²×(−∞,0]
compactifies to a 3-ball whose boundary sphere contains R², and isotopies of the
boundary sphere extend over the ball, carrying half-foams to half-foams and
preserving the pairing. If K = K₁ ⊔ K₂, K₁ lies in a disk face of K₂ (faces of a
connected plane graph are disks), so the two components can be separated by a
circle and their half-foams built in disjoint half-balls; each component is then
a web on its own sphere. Hence faces are per-component φ-orbits and the
unbounded face is not special **mathematically**. (It is special in B19's
program; see the B19 mode in §6.4.)

### 3.7 The outer-face marker (B19 mode only)

In B19 mode (§6.4) one face of the target web is the **outer (unbounded) face** of
Boozer's drawing (B19 Fig 6, p.10). It is tracked through every operation by a
**marker dart** m whose face orbit is the outer face:

- Initially m = the minimum dart of the designated outer face (Appendix A).
- After an operation with deleted vertex set D: if m's vertex survives, the new
  marker is dmap(m); else take the first dart of m's face orbit (in orbit order
  starting from the orbit's minimum dart) whose vertex survives, mapped by dmap;
  if none survives, the web becomes **unmarked** and stays unmarked below this
  point of the recursion (all faces eligible).
- Operations that delete no vertices (Unzip, Saddle, disk removal) keep m.

---

## 4. Foams: the facet–seam representation

### 4.1 What the KR formula needs

Only these data of a closed foam F enter ⟨F⟩ and deg F:

- the facets f, and for each its **dot count** d(f) and **Euler characteristic**
  χ(f) of the open facet (= χ of the compact surface whose interior it is:
  1 for a disk, 0 for an annulus or torus, 2 for a sphere, 2−2g−b in general);
- the **seam triples**: for every seam (component of s(F) minus the seam
  vertices; an open arc or a circle, KR p.5), the multiset of the three facets
  around it;
- nv(F), the number of seam vertices (tetrahedral points).

Indeed, for an admissible colouring c,

    χ(F_ij(c)) = Σ_{f : c(f) ∈ {i,j}} χ(f) + χ(s(F)),     χ(s(F)) = −nv(F)

(KR Def 2.7 and the lines after it, p.8: s(F) is 4-valent, so it has twice as
many non-circular edges as vertices), and

    deg F = 2·Σ_f d(f) − 2·Σ_f χ(f) + 3·nv(F)                  (KR Def 2.7, p.8).

A colouring is admissible iff every seam triple is rainbow; a triple with a
repeated facet has no rainbow colouring, so such a foam evaluates to 0.
Orientability data are not needed (§4.8). Hence the whole program can work with
the following **facet–seam representation**, and never needs coordinates, cell
complexes, or genus computations.

### 4.2 Half-foams

A half-foam H with boundary K is stored as:

- a list of facets; facet f has an integer `chi[f]` (see below), an integer
  `dots[f]`, and the set of top edges it contains;
- `owner`: every edge of K and every vertexless circle of K belongs to exactly one
  facet (the facet containing e × {0});
- a list of seam triples (facet, facet, facet);
- `nv`: number of seam vertices.

`chi[f]` is the compactly supported Euler characteristic of f°, the facet with its
seams **and its top-boundary edges** removed. Examples: a cup (disk bounding a
circle) has chi = 1; the sheet e×[−1,0] over an interval edge has chi = 1; the
sheet over a circle has chi = 0.

Derived quantities (V = number of vertices of K):

    deg H        = 2·Σ dots − 2·Σ chi + 3·nv + (3/2)·V
    χ(H_ij(c))   = Σ_{f : c(f) ∈ {i,j}} chi[f] − nv − V/2

The second line is χ of the compact surface H_ij(c) (whose boundary is the
ij-cycles of the boundary colouring). Both follow from the partition
H = (∪ f°) ⊔ (s(H) minus boundary points) ⊔ K, using χ(s(H)) = −nv + V/2 (the seam
graph has nv 4-valent and V 1-valent vertices), χ(K) = −V/2, and the fact that a
Tait colouring gives exactly V interval edges a colour in {i,j}.

The **empty half-foam** (boundary ∅) has no facets, nv = 0, deg 0.

### 4.3 Cobordism records and composition (Mode G)

Every elementary cobordism C : K′ → K (bottom K′, top K) used in this program is
the identity outside a local region. It is stored as a **record**:

- local facets g, each with `chi`, `dots`, a set `bot(g)` of K′-edges (or
  circles) and a set `top(g)` of K-edges (or circles);
- local seam triples (over local facets only);
- `nv` (local seam vertices), `Vt` = number of vertices of K not in K′
  (created), `Vb` = number of vertices of K′ not in K (destroyed).

Every K′-edge is either an identity edge (§3.5) or in bot(g) of exactly one local
facet (an **involved** bottom edge); every K-edge is an identity edge or in top(g)
of exactly one local facet. If an operation would put the same K′-edge into two
nominal local facets, those nominal facets are **one** facet: take the union of
their top sets and count the sheet's chi once (this happens only in degenerate
square eliminations, §5.4). Identity edges carry an implicit identity sheet (chi 1
for an interval edge, 0 for a circle) that is never materialised: its facet simply
passes through.

The seams over surviving vertices (v × [0,1]) are part of the identity and need
no triple: their constraint is already implied by t′ and t being Tait colourings.

**Composition H′ = C ∘ H** (H has boundary K′):

1. Union–find on (facets of H) ⊔ (local facets of C). For every local facet g and
   every ε ∈ bot(g): union(g, owner_H(ε)).
2. chi of a class = Σ chi of its members − (number of involved bottom
   **interval** edges inside the class). (Each glued open edge contributes −1;
   glued circles contribute 0.)
3. Dots add. owner′(e) = class(owner_H(e′)) for an identity edge e with K′-image
   e′ (§3.5); owner′(e) = class(g) for e ∈ top(g).
4. Seam triples of H and of C, mapped to classes. nv′ = nv(H) + nv(C).
5. deg H′ = deg H + deg C, where

       deg C = 2·Σ_g dots(g) − 2·(Σ_g chi(g) − b) + 3·nv(C) + (3/2)·(Vt − Vb),
       b = number of involved bottom interval edges.

   Assert that deg C equals B19 Table 1 (p.9) and that deg H′ equals the §4.2
   formula recomputed from scratch.

### 4.4 Closed foams by gluing, and their evaluation (Mode G)

Given half-foams H₁, H₂ with the same boundary K, the closed foam
F = H₁ ∪_K H̄₂ (B19 p.3) has:

- facets: classes of facets(H₁) ⊔ facets(H₂) under union(owner₁(e), owner₂(e))
  for every edge and circle e of K;
- chi(class) = Σ chi of members − (number of interval edges of K in the class);
- dots add; seam triples = union (mapped); nv = nv(H₁) + nv(H₂).

The mirror H̄₂ has the same representation as H₂ (evaluation depends only on the
underlying pre-foam; KR p.15). Evaluate by §2.4 with χ(F_ij(c)) =
Σ_{f: c(f)∈{i,j}} chi[f] − nv, enumerating colourings by backtracking over facets
with the seam triples as constraints. This is the analogue of B19 §3.2
steps (1)–(4) (p.7) and Remark 3.6.

### 4.5 The a-vector of a half-foam, and the factorisation of the pairing

For a half-foam H with boundary K and a Tait colouring t of K let Col(H,t) be the
admissible colourings c of H with c(owner(e)) = t(e) for every edge and circle e
of K (facets owning no boundary edge are free, constrained only by seams). Define

    a_H(t) = Σ_{c ∈ Col(H,t)} ω^{e(H,c)} ∈ GF(4),
    e(H,c) = Σ_f dots[f]·(c(f)−1) − χ(H_12(c)) − 2·χ(H_13(c))      (mod 3)

with χ(H_ij(c)) from §4.2. The **a-vector** of H is (a_H(t)) over Tait colourings
in canonical order (§3.3).

**Pairing identity.** For half-foams H₁, H₂ with boundary K,

    Φ(⟨H₁ ∪_K H̄₂⟩) = Σ_t a_{H₁}(t) · a_{H₂}(t)                (in GF(4))

This is KR Prop 3.8 (p.36) evaluated at Φ: admissible colourings of the glued
foam are exactly pairs of colourings agreeing on K, dots add, and
χ(F_ij) = χ(H₁,ij) + χ(H₂,ij) because the gluing locus K_ij(t) is a disjoint union
of circles (χ = 0). Consequently

    (H₁,H₂)       = [deg H₁ + deg H₂ = 0] · Σ_t a_{H₁}(t) a_{H₂}(t)
    (H₁,H₂)_ψ     = Σ_t a_{H₁}(t) a_{H₂}(t) · E^{(deg H₁ + deg H₂)/6}

and each pairing value lies in F (assert it). The second line is 0 automatically
when deg H₁ + deg H₂ is negative or not divisible by 6 (assert on samples).

### 4.6 Transfer matrices (Mode T)

For a record C : K′ → K define the Tait(K′)×Tait(K) matrix over GF(4)

    T_C(t′, t) = Σ_c ω^{e(C,c)}

over **local** colourings c (local facets → colours) such that: c(g) = t′(ε) for
every ε ∈ bot(g); c(g) = t(e) for every e ∈ top(g); t′ and t agree on identity
edges and circles; every local seam triple is rainbow. Here

    e(C,c)       = Σ_g dots(g)·(c(g)−1) − χ₁₂(C,c) − 2·χ₁₃(C,c)       (mod 3)
    χ_ij(C,c)    = Σ_{g : c(g) ∈ {i,j}} chi(g) − b_ij − nv(C) + (Vb − Vt)/2
    b_ij         = #{involved bottom interval edges ε with t′(ε) ∈ {i,j}}

(Derivation: apply §4.2's partition to a cobordism with both boundaries and add
the identity sheets; the identity contributions cancel because each colour class
of interval edges of K′ has exactly |V(K′)|/2 edges.) Then

    a_{C∘H} = a_H · T_C       (row vector times matrix),

starting from a_∅ = (1) for the empty half-foam. Mode T never builds facets of
half-foams; it needs only the records of §5 and the Tait colourings of every web
in every chain.

### 4.7 Mode G ⇔ Mode T consistency

For every half-foam, Mode G (compose facets, then §4.5 directly) and Mode T
(multiply transfer matrices) must give the **identical** a-vector. This is the
central cross-check between the two implementations (§11).

### 4.8 Orientability

KR's admissibility (KR p.6) also requires every F_ij(c) to be orientable. For foams
in R³ this is automatic (KR Prop 2.20, p.15); for foams with boundary in
R²×[0,1] likewise (KR p.33). Everything built here is an embedded foam: webs are
planar and every elementary cobordism is a local embedded model (B19 Figs 3, 5).
So no orientability test is performed. Two cheap consistency checks replace it:

- for a closed foam, every χ(F_ij(c)) of an admissible colouring is even (assert);
- Φ-values of pairings lie in F (§2.4, assert).

If an implementation carries a 2-cell complex instead (as B19 does, Remark 3.1
p.4 and Remark 3.6 p.7), orientability of F_ij(c) can be decided by sign
propagation: orient each 2-cell, and require signs s(cell) ∈ {±1} such that for
every 1-cell with exactly two incident cell-sides in F_ij(c) the induced
orientations are opposite; BFS over cells, failure ⇔ non-orientable. This is
optional.

---

## 5. The twelve elementary cobordisms, exactly

Every operation below is written as a **web change K → K′** applied to the web K
that will be the **top** of the cobordism; the cobordism C runs **K′ → K** (bottom
K′, top K), exactly as in B19 (Fig 2 and Fig 4 show K → K′; Figs 3 and 5 show
C : K′ → K). Notation from §3.2: for a face in canonical form, f_i, v_i, ℓ_i;
E(d) is the K-edge of dart d; E′(·) a K′-edge; `sheet(ε)` = 1 if ε is an interval
edge (including loops), 0 if ε is a vertexless circle. All local facets not
called "sheet" have chi = 1 (they are disks). The geometric reading of each
record is given so that it can be checked against the figures.

Degrees (B19 Table 1, p.9) follow from §4.3 and are asserted:

| C | C1 | Ċ1 | C̈1 | C2 | Ċ2 | C3 | C4a | C4b | Zip | Unzip | Saddle | IH |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deg | −2 | 0 | 2 | −1 | 1 | 0 | 0 | 0 | 1 | 1 | 2 | 1 |

### 5.1 Disk: C1, Ċ1, C̈1 (B19 Fig 2(a), Fig 3(a); KR Prop 3.12, Fig 18)

- Precondition: K has m ≥ 1 circles.
- K′ = K with circle m−1 removed (no REBUILD; darts unchanged).
- Record: one facet D (the cup): bot ∅, top {circle m−1}, chi 1,
  dots 0 / 1 / 2 for C1 / Ċ1 / C̈1. No seams. nv 0, Vt = Vb = 0.

### 5.2 Bigon: C2, Ċ2 (B19 Fig 2(b), Fig 3(b); KR Prop 3.13, Fig 19)

- Face (f₀, f₁) of length 2, vertices v₀ ≠ v₁, legs ℓ₀ = σ(f₀), ℓ₁ = σ(f₁).
- K′ = REBUILD(K; D = {v₀, v₁}; NV = []; J = [(ℓ₀, ℓ₁)]). Let a = K′-edge of the
  join (a circle if α(ℓ₀) = ℓ₁, e.g. when K is a theta web).
- Record:
  - S ("sheet with a notch"): bot {a}, top {E(ℓ₀), E(ℓ₁)} (one element if equal),
    chi = sheet(a);
  - B1 (half of the bowl): top {E(f₀)}, chi 1, dots 0 (C2) or 1 (Ċ2);
  - B2 (other half of the bowl): top {E(f₁)}, chi 1;
  - seam (S, B1, B2) (the semicircular seam from v₀ down and up to v₁);
  - nv 0, Vt 2, Vb 0.
- Reading of Fig 3(b): the vertical sheet over the arc, with a hemispherical bowl
  whose rim is the bigon; the sheet is notched along the bowl's cross-section.
  The dot of Ċ2 is on a bowl half; which half does not matter for the span
  (dot migration, KR Prop 2.32 p.22, at E=0: dot(B1) = dot(B2) + dot(S), and
  dot(S) = C2∘(dotted h) is already in the span). This spec fixes it on B1, the
  half containing the bigon edge of the canonical dart f₀.

### 5.3 Triangle: C3 (B19 Fig 2(c), Fig 3(c); KR Prop 3.15, Fig 21)

- Face (f₀, f₁, f₂), vertices v₀, v₁, v₂, legs ℓ_k = σ(f_k).
- K′ = REBUILD(K; D = {v₀,v₁,v₂}; NV = [(ℓ₀, ℓ₂, ℓ₁)]; J = []). The new vertex y
  has slot 0 ↔ ℓ₀, slot 1 ↔ ℓ₂, slot 2 ↔ ℓ₁ (the legs of a clockwise-traversed
  face appear in the reverse cyclic order around y).
- Record (nv 1: one tetrahedral point x):
  - A_k (k = 0,1,2): bot {E′(slot of y for ℓ_k)}, top {E(ℓ_k)}, chi 1 (sheets);
  - T_k (k = 0,1,2): top {E(f_k)} (the triangle edge v_k v_{k+1}), chi 1;
  - seams: (A₀, A₁, A₂) (vertical seam from y up to x) and, for k = 0,1,2,
    (A_k, T_k, T_{k−1 mod 3}) (seam from x up to v_k);
  - nv 1, Vt 3, Vb 1.
- Reading of Fig 3(c): three sheets meet along the vertical seam over y, which
  ends at a tetrahedral point; from it three seams rise to the triangle's
  vertices, and the three small triangular facets T_k fill the triangle.

### 5.4 Square: C4a, C4b (B19 Fig 2(d), Fig 3(d); KR Prop 3.14, Fig 20)

- Face (f₀, f₁, f₂, f₃), vertices v₀…v₃, legs ℓ₀…ℓ₃. Two smoothings:
  - **K′_a** = REBUILD(K; D = {v₀,…,v₃}; NV = []; J = [(ℓ₀,ℓ₁), (ℓ₂,ℓ₃)]):
    arcs run along the square edges v₀v₁ and v₂v₃;
  - **K′_b** = REBUILD(K; D = {v₀,…,v₃}; NV = []; J = [(ℓ₁,ℓ₂), (ℓ₃,ℓ₀)]).
  (Which smoothing is B19's "4a" is a matter of drawing; this spec calls the
  (ℓ₀,ℓ₁),(ℓ₂,ℓ₃) smoothing "a".)
- Record C4a : K′_a → K. Let a₀₁, a₂₃ be the K′-edges of the two joins.
  - S₀₁: bot {a₀₁}, top {E(ℓ₀), E(ℓ₁)}, chi = sheet(a₀₁);
  - S₂₃: bot {a₂₃}, top {E(ℓ₂), E(ℓ₃)}, chi = sheet(a₂₃);
  - I₀₁: top {E(f₀)} (square edge v₀v₁), chi 1 (half-disk under that edge);
  - I₂₃: top {E(f₂)} (square edge v₂v₃), chi 1;
  - Tstrip: top {E(f₁), E(f₃)} (the two square edges joining the arcs), chi 1
    (a strip hanging under the square from edge v₁v₂ to edge v₃v₀);
  - seams (S₀₁, I₀₁, Tstrip) (from v₀ down and up to v₁) and
    (S₂₃, I₂₃, Tstrip) (from v₂ to v₃);
  - nv 0, Vt 4, Vb 0.
- Record C4b : K′_b → K: the same with indices shifted by one: sheets S₁₂
  (top {E(ℓ₁),E(ℓ₂)}) and S₃₀ (top {E(ℓ₃),E(ℓ₀)}), half-disks I₁₂ (top {E(f₁)})
  and I₃₀ (top {E(f₃)}), strip with top {E(f₂), E(f₀)}, seams (S₁₂, I₁₂, strip),
  (S₃₀, I₃₀, strip).
- Degenerate case: if the two joins produce the **same** K′-edge (possible only
  when two adjacent legs are the same edge, i.e. a bigon sits on a square edge;
  this happens only in B19 mode, where an outer bigon is never eliminated),
  S₀₁ and S₂₃ are one facet (§4.3): top = union, chi = sheet counted once.
- Reading of Fig 3(d) and KR Fig 20 (bottom row): the two sheets of the smoothing
  pass straight up; under each square edge parallel to an arc hangs a half-disk
  bounded by a seam; the strip joining the two seams carries the two square
  edges that cross between the arcs.

### 5.5 Zip (B19 Fig 4(a), Fig 5(a); KR Fig 22 F_{||→I}, degree 1, p.46–47)

- Site: an edge {d_u, d_w} of K with d_u = its min dart, d_w = α(d_u), u, w its
  vertices. Write x_u = σ(d_u), y_u = σ²(d_u), x_w = σ(d_w), y_w = σ²(d_w). The
  legs on one side of the edge are x_u and y_w; on the other side y_u and x_w
  (the face on the right of d_u has the edges of y_u and x_w on its boundary,
  since φ(d_u) = x_w and φ(α(y_u)) = d_u).
- Precondition: the four legs are four distinct edges, none equal to the site
  edge (true for every edge of W1–W7).
- K′ = REBUILD(K; D = {u,w}; NV = []; J = [(x_u, y_w), (y_u, x_w)]): delete the
  edge and join the two legs on each side (Fig 4(a): K = "I" → K′ = ")(").
- Record:
  - L: bot {K′-edge of join (x_u,y_w)}, top {E(x_u), E(y_w)}, chi 1;
  - R: bot {K′-edge of join (y_u,x_w)}, top {E(y_u), E(x_w)}, chi 1;
  - M: top {E(d_u)} (the new edge), chi 1 (half-disk);
  - seam (L, R, M); nv 0, Vt 2, Vb 0.

### 5.6 Unzip (B19 Fig 4(b), Fig 5(b); KR Fig 22 F_{H→=}, degree 1)

- Site: a face f in canonical form and 0 ≤ i < j < L; x = E(f_i) (from v_i to
  v_{i+1}), y = E(f_j) (from v_j to v_{j+1}). Both have f on their right.
- K′ ("fuse x and y", Fig 4(b): K = ")(" → K′ = "I"): no deletions; append
  vertices t = V and b = V+1 with darts
  t: (tS, tR, tL) = (3t, 3t+1, 3t+2),  b: (bN, bL, bR) = (3b, 3b+1, 3b+2),
  and set α′: tS↔bN, tL↔α(f_i), tR↔f_j, bL↔f_i, bR↔α(f_j); all other pairs
  unchanged. (t is joined to v_{i+1} and v_j, b to v_i and v_{j+1}; the new edge
  tS–bN runs between them inside f.)
- Record:
  - L: bot {E′(bL), E′(tL)}, top {x}, chi 1 (sheet over x, notched from below);
  - R: bot {E′(tR), E′(bR)}, top {y}, chi 1;
  - M: bot {E′(tS)}, chi 1 (half-disk above the fused edge);
  - seam (L, R, M) (from t up and down to b); nv 0, Vt 0, Vb 2.
- If x and y share a vertex, K′ has a bigon; K′ is then never reducible (bigon
  removal gives back K), so these sites contribute nothing. Enumerate them anyway.
- Note: the other conceivable "unzip" (a rung inserted between x and y) is the IH
  image of this K′ and is **not** B19's Unzip; the N-values of §9.6 confirm the
  fuse reading.

### 5.7 Saddle (B19 Fig 4(c), Fig 5(c); KR Fig 22 F_{=→||}, degree 2)

- Site: as for Unzip (face f, i < j, x = E(f_i), y = E(f_j)).
- K′ ("reconnect through the face", Fig 4(c): ")(" → "⌣⌢"): no vertex change;
  α′: f_i ↔ α(f_j), f_j ↔ α(f_i) (all else unchanged). The new edges are
  n₁ = {f_i, α(f_j)} (joins v_i and v_{j+1}) and n₂ = {f_j, α(f_i)} (joins v_j and
  v_{i+1}).
- Record: one facet Σ: bot {n₁, n₂}, top {x, y}, chi 1 (the saddle disk). No
  seams. nv 0, Vt = Vb = 0.
- If x and y share a vertex, K′ has a loop, hence a bridge; S(K′) = ∅.

### 5.8 IH (B19 Fig 4(d), Fig 5(d); KR Fig 22 F_{I→H}, degree 1)

- Site: an edge as for Zip (d_u, d_w, x_u, y_u, x_w, y_w). Same precondition.
- K′ = REBUILD(K; D = {u,w}; NV = [(ι, y_w, x_u), (ι, y_u, x_w)]; J = []), where ι
  is an internal label (new edge e′ between slot 0 of the two new vertices
  t = s and b = s+1). This is the planar Whitehead flip: the two legs on each
  side of the edge become attached to one new vertex.
- Record (nv 1):
  - P₁: bot {E′(3t+1)}, top {E(y_w)}; P₂: bot {E′(3t+2)}, top {E(x_u)};
    P₃: bot {E′(3b+1)}, top {E(y_u)}; P₄: bot {E′(3b+2)}, top {E(x_w)}; all chi 1;
  - B: bot {E′(3t)} (= e′), chi 1; Tf: top {E(d_u)}, chi 1;
  - seams (B, P₁, P₂) [t up to x], (B, P₃, P₄) [b up to x],
    (Tf, P₂, P₃) [x up to u], (Tf, P₄, P₁) [x up to w];
  - nv 1, Vt 2, Vb 2.

### 5.9 Structural self-tests of the records

- Degrees: every record's deg equals the table above (assert at start-up).
- KR Lemma 4.11 (p.47): the four composites Unzip∘IH (I→H→=), Saddle∘Unzip
  (H→=→||), Zip∘Saddle (=→||→I) and IH∘Zip (||→I→H), taken at the same local
  square, have **no** admissible colourings. Test: in W1, take the face f of
  dart 0 in canonical form, the pair (f₀, f₂), and edge 0; build the three-level
  chains as in §9.5 and check that the Boolean product of the two transfer
  supports is empty while each factor is non-empty **[spec-check]**.

---

## 6. Half-foam generation

### 6.1 Reducible webs and their bases (B19 §3.1, p.4–6; KR §3.3, p.38–40)

B19's definition (p.4): ∅ is reducible; a nonempty K is reducible if one of the
replacements of Fig 2 (disk, bigon, triangle, square) gives reducible K′₁, K′₂,
K′₃, or both K′₄a and K′₄b reducible. For reducible K the recursion below yields a
list S(K) with |S(K)| = Tait(K) (B19 Remark 3.2, p.4) which is a **basis** of
J♭(K) (KR Props 3.12–3.15 with Prop 4.2; B19 p.4: "their results provide an
algorithm for constructing a basis"). Hence for STRICT semantics (below) the span
of C∘S(K′) is the image of J♭(C) and does not depend on any of the choices this
spec fixes (face order, dot placement, order of variants).

**GEN(K, semantics, marker)** returns a list of (half-foam, degree), in order:

1. If K has no vertices and no circles: return [empty half-foam].
2. If K has a circle: K′ = remove circle m−1 (§5.1);
   return C1∘GEN(K′) ++ Ċ1∘GEN(K′) ++ C̈1∘GEN(K′)
   (block order: all of C1 first, in the order of GEN(K′), then Ċ1, then C̈1).
3. If K has a bridge: return FAIL.
4. Eligible faces: all faces, except (if K is marked, §3.7) the face containing the
   marker dart. Among eligible faces of length 2, else 3, else 4 (disks were
   handled in step 2), take the one with the **smallest minimum dart**, in
   canonical form. If there is none: return FAIL.
5. Length 2: K′ = §5.2; return C2∘GEN(K′) ++ Ċ2∘GEN(K′).
   Length 3: K′ = §5.3; return C3∘GEN(K′).
   Length 4: K′_a, K′_b = §5.4; return C4a∘GEN(K′_a) ++ C4b∘GEN(K′_b).
   Marker: pass the updated marker (§3.7) to each recursive call.
6. FAIL handling:
   - **STRICT**: if any recursive call fails, this call fails (so a square step
     needs both branches; B19 p.4 definition).
   - **PARTIAL**: a failed call contributes the empty list; nothing fails upward.

This is B19 Remark 3.3's greedy algorithm ("attempt to eliminate disks, bigons,
triangles, and squares, in that order"), made deterministic. No backtracking.
**[spec-check]**: on every web K′ arising in this program from W1–W7, STRICT-ALL
greedy succeeds exactly when a full backtracking search over all small faces
succeeds, so greediness costs nothing there.

Composition "C∘list" means: apply C (Mode G: §4.3 composition; Mode T: multiply
the a-vector by T_C) to every element, keeping order. Degrees add (Table §5).

### 6.2 Moves at the target web (B19 p.5, Figs 4–5)

For the target web K (one of W1–W7, all simple and 3-connected) the **move sites**
are, in this order:

1. **Zip** at every edge, edges in increasing edge id (§5.5);
2. **Unzip** at every eligible face f (faces in increasing minimum dart) and every
   pair 0 ≤ i < j < L in lexicographic order (§5.6);
3. **Saddle** at the same face pairs in the same order (§5.7);
4. **IH** at every edge, in increasing edge id (§5.8).

"Eligible faces" for Unzip and Saddle: all faces (ALL modes), or all faces except
the designated outer face (B19 mode). Zip and IH are applied at **every** edge in
every mode, including edges of the outer face.

For each site M with bottom web K′_M, compute GEN(K′_M) (with the marker carried
through M as in §3.7 in B19 mode) and append M∘h for h in GEN(K′_M), in order.
If GEN fails (STRICT) or returns [], the site contributes nothing. The
concatenation over all sites is **S(K)**, indexed 1…N.

### 6.3 Degrees

deg(M∘h) = deg(h) + deg(M). For a reducible K′ (STRICT) the degree multiset of
GEN(K′) is qdim J♭(K′) (KR §4.4, p.51–52), symmetric about 0. S(K) may contain
half-foams of many degrees; under J♭ only pairs with degrees summing to 0 pair
nontrivially (§4.5). The degree of every half-foam is also recomputed from its
facet–seam data (§4.2) and must agree with the sum of Table §5 degrees.

### 6.4 The three generation modes

| Mode | Unzip/Saddle faces | Reductions may use the outer face? | Failure semantics | Purpose |
| --- | --- | --- | --- | --- |
| **B19** | all except outer | no (marker, §3.7) | PARTIAL | reproduce B19's generating set; N matches Table 2 for all seven webs **[spec-check]** |
| **STRICT-ALL** | all | yes (unmarked) | STRICT | the mathematically canonical set: each used K′ contributes a basis of J♭(K′) |
| **PARTIAL-ALL** | all | yes | PARTIAL | largest family: every site, every partial basis (not literally a superset of the B19-mode list, whose reductions avoid the outer face) |

**Primary reproduction target:** B19 mode. B19 does not state the outer-face
exclusion or the partial semantics. They were inferred while writing this spec,
because they are the only reading found (several others were tried) under which
the total count N reproduces B19 Table 2 for **all seven** webs; see §10, item 1.
Report all three modes for every web.

Expected N (number of half-foams generated) **[spec-check]**:

| Web | B19 mode (= B19 Table 2 N) | STRICT-ALL | PARTIAL-ALL |
| --- | ---: | ---: | ---: |
| W1 | 11 160 | 11 880 | 11 880 |
| W2 | 27 792 | 30 600 | 30 600 |
| W3 | 45 960 | 48 864 | 48 864 |
| W4 | 47 196 | 50 040 | 50 040 |
| W5 | 40 704 | 43 992 | 43 992 |
| W6 | 53 172 | 41 664 | 58 044 |
| W7 | 101 970 | 116 730 | 117 486 |

B19 mode, by move type **[spec-check]**:

| Web | Zip | Unzip | Saddle | IH |
| --- | ---: | ---: | ---: | ---: |
| W1 | 1 080 | 3 960 | 3 960 | 2 160 |
| W2 | 2 808 | 9 864 | 10 224 | 4 896 |
| W3 | 4 188 | 16 872 | 16 800 | 8 100 |
| W4 | 4 248 | 17 496 | 16 956 | 8 496 |
| W5 | 3 744 | 14 784 | 14 832 | 7 344 |
| W6 | 4 704 | 19 404 | 19 068 | 9 996 |
| W7 | 9 036 | 37 296 | 39 564 | 16 074 |

STRICT-ALL, by move type **[spec-check]**: W1 1080/4320/4320/2160;
W2 2808/11088/11808/4896; W3 4188/18336/18240/8100; W4 4248/19008/18288/8496;
W5 3744/16416/16488/7344; W6 3696/13776/17304/6888; W7 10188/43488/45828/17226
(Zip/Unzip/Saddle/IH).

These counts are independent of the labelling of the web and (checked with
randomised face choices for W6, W7 in B19 mode) of the greedy face choice.

---

## 7. Rank computations

Input: S(K) = (h₁,…,h_N) with degrees d_i and a-vectors a_i ∈ GF(4)^T,
T = Tait(K). Write β(u,v) = Σ_t u(t)v(t) (a symmetric bilinear form on GF(4)^T).
The Gram matrices are G_ij = [d_i + d_j = 0]·β(a_i,a_j) (J♭) and
G^ψ_ij = β(a_i,a_j)·E^{(d_i+d_j)/6} (ψ), by §4.5. Their entries lie in F; ranks
over GF(4) of F-matrices equal ranks over F. Never form the N×N matrix: work with
row spaces, which have dimension ≤ T.

### 7.1 ℓ and ℓ_q (B19 eq (18), p.11)

For each degree d let U_d = span{a_i : d_i = d} ⊂ GF(4)^T, with a basis B_d in
reduced row echelon form (rows). Then

    ℓ_d = rank(B_d · B_{−d}ᵀ)       (the pairing matrix between the two bases),
    ℓ_q(K) = Σ_d ℓ_d q^d,     ℓ(K) = Σ_d ℓ_d.

Assert ℓ_d = ℓ_{−d}. (Rank of the Gram matrix between two spanning sets equals the
rank between bases of their spans.)

### 7.2 Prefix ranks β_n (B19 p.9, Fig 7)

β_n = ℓ computed from (h₁,…,h_n). Maintain U_d incrementally; when a new a_i
enlarges U_{d_i}, recompute ℓ_{d_i} and ℓ_{−d_i}. Output every n at which β_n
changes, and N_ℓ(ours) = the first n with β_n = β_N. B19's N_ℓ and N_e depend on
B19's unknown ordering and are **not** reproduction targets (§10, item 3).

### 7.3 r and r_q (B19 eqs (19)–(32), p.11–12) without a Smith form

Let C = [β(a_i,a_j)] (all i, j). Then r(K) = rank C = rank(B·Bᵀ) with B a basis of
span{a_i}. For r_q: the F[E]-module N(K)/N(K)^⊥ is isomorphic to the image of
v ↦ (v, ·)_ψ in the graded dual, whose degree-k part has dimension

    h(k) = rank of [β(a_i, a_j)]_{i ∈ I_k, j ∈ J_k},
    I_k = {i : d_i ≤ k, d_i ≡ k (mod 6)},   J_k = {j : d_j ≥ −k, d_j ≡ −k (mod 6)}

(compute via bases of span{a_i : i ∈ I_k} and span{a_j : j ∈ J_k}). A free graded
F[E]-module with generators in degrees g_s has dimension #{s : g_s ≤ k,
g_s ≡ k mod 6} in degree k, so the number of generators in degree k is

    g(k) = h(k) − h(k−6),       r_q(K) = Σ_k g(k) q^k,

for k from min d_i to max(max d_i, −min d_i) (h is 0 below and constant above).
Assert g(k) ≥ 0 and Σ_k g(k) = r(K). Derivation: with N free on the h_i in degree
d_i and N* free on duals of degree −d_j, E^m·(h_i, ·)_ψ in degree k = d_i + 6m has
coordinates β(a_i,a_j) at the basis element E^{(k+d_j)/6} h_j*; entries with
d_i + d_j < 0 or 6 ∤ d_i + d_j vanish automatically (§2.4).
This is equivalent to B19's Smith-form computation (B19 eq (24)–(32)); an
implementation may use a graded Smith form over F[E] instead, as a cross-check.

### 7.4 Linear algebra over GF(4)

Gaussian elimination with the multiplication table of §0 (inverse: 1↔1, ω↔ω²).
Pivot rule: leftmost column, first row. Everything is exact; there is no
randomness anywhere in this program.

### 7.5 Mandatory cross-checks in every run

1. Mode G vs Mode T a-vectors identical for all half-foams (between the two
   implementations; see §11). Compare the SHA-256 of the a-vector file.
2. For 10 000 pairs (i, j) chosen by the rule i = 1 + (7919·k mod N),
   j = 1 + (104729·k mod N), k = 1…10 000: the direct closed-foam value
   Φ(⟨h_i ∪ h̄_j⟩) of §4.4 equals β(a_i, a_j) computed from the a-vectors, lies in
   F, and is 0 when d_i + d_j < 0 or 6 ∤ d_i + d_j. (Implementation A does this
   internally; Implementation B, which has no facets, instead checks the same
   pairs against A's direct values once A exists.)
3. deg recomputed from facet–seam data equals the Table §5 sum (Mode G).
4. ℓ_d = ℓ_{−d}; g(k) ≥ 0; ℓ ≤ r ≤ T.

### 7.6 Output

Per (web, mode):

- `halffoams.jsonl`: one line per half-foam i: `{"i": i, "site": ..., "chain":
  [...], "deg": d_i, "a": "<T hex digits, one per Tait colouring, codes of §0>"}`.
  `site` = `["zip", edge_id]`, `["unzip", face_min_dart, i, j]`,
  `["saddle", face_min_dart, i, j]` or `["ih", edge_id]`; `chain` = the list of
  reduction cobordism labels from K′ downwards to ∅ (`C1`, `C1d`, `C1dd`, `C2`,
  `C2d`, `C3`, `C4a`, `C4b`).
- `result.json` (keys sorted): web, mode, V, Tait, N, N by move type, ℓ, ℓ_q
  (as a map degree→count), r, r_q, the list of (n, β_n) change points,
  N_ℓ(ours), SHA-256 of `halffoams.jsonl`, the command line, the git commit, and
  the implementation name. Results must rerun byte-identically (house rule).

---

## 8. The webs

Appendix A is **authoritative**: both implementations load the same files, so
their Tait orders, dart numbers and a-vectors coincide. This section says how the
webs were identified and how to re-verify the identification.

### 8.1 Controls (reducible)

circle (V=0, m=1); two circles (V=0, m=2); theta (V=2, α = [3,5,4,0,2,1]); K4
(tetrahedron); prism3 (triangular prism); cube; prism5 (pentagonal prism);
prism6 (hexagonal prism). All are reducible (KR §3.3; B19 eq (2)).

### 8.2 W1, W2, W6: the family D(n)

B19 Fig 6 (p.10) shows W1, W2 and W6 as: an outer n-gon, n spokes, a ring of 2n
vertices, n spokes, an inner n-gon, with n = 5, 6, 7. Label o_k = k (outer),
r_j = n + j (ring), i_k = 3n + k (inner), k ∈ Z/n, j ∈ Z/2n. Edges:
o_k–o_{k+1}, o_k–r_{2k}, r_j–r_{j+1}, r_{2k+1}–i_k, i_k–i_{k+1}. Rotation: counter-
clockwise order of neighbours in the straight-line drawing with o_k at radius 3,
angle 2πk/n; r_j at radius 2, angle πj/n; i_k at radius 1, angle (2k+1)π/n.

- **W1** = D(5) = the dodecahedron (B19 p.10 caption; "the unique fullerene with
  20 vertices", Remark 4.1). Faces 12 pentagons. |Aut| = 120. Tait = 60.
- **W2** = D(6) = the unique C24 fullerene (Remark 4.1), D6d. Faces 12 pentagons
  + 2 hexagons. |Aut| = 24. Tait = 120.
- **W6** = D(7). B19 does not call W6 a fullerene; it is read off Fig 6: outer
  heptagon, 7 spokes, 14-ring, 7 spokes, inner heptagon, 14 pentagons, 28
  vertices, symmetry D7d, |Aut| = 28, **Tait = 252** (matches B19 Table 2). The
  ring alternates outward and inward spokes (the only way to make all other
  faces pentagons, as in the figure).

### 8.3 W3, W4, W5, W7: fullerenes

B19 Remark 4.1 (p.9): W5 is the unique C26; W3 and W4 are the two C28; W7 is one
of the six C34. Identification (all **[spec-check]**, by exhaustive spiral
enumeration and exact Tait counts; spirals are the lexicographically minimal
Fowler–Manolopoulos face spirals, 1-based pentagon positions; isomer numbers are
the positions in the lexicographic order of these spirals, the atlas convention):

| Web | V | isomer | spiral (pentagon positions) | point group | order of Aut | faces | Tait |
| --- | --- | --- | --- | --- | --- | --- | --- |
| W2 | 24 | C24 | 1 2 3 4 5 7 8 10 11 12 13 14 | D6d | 24 | 12×5, 2×6 | 120 |
| W5 | 26 | C26 | 1 2 3 4 5 7 9 11 12 13 14 15 | D3h | 12 | 12×5, 3×6 | 192 |
| W3 | 28 | C28:1 | 1 2 3 4 5 7 10 12 13 14 15 16 | D2 | 4 | 12×5, 4×6 | 162 |
| W4 | 28 | C28:2 | 1 2 3 5 7 9 10 11 12 13 14 15 | Td | 24 | 12×5, 4×6 | 180 |
| W7 | 34 | C34:6 | 1 2 3 5 7 10 11 14 15 17 18 19 | C3v | 6 | 12×5, 7×6 | 312 |

The two C28 isomers have Tait 162 and 180, which fixes W3 and W4 by B19 Table 2.
The six C34 isomers have Tait 384, 492, 288, 390, 300, 312 (spiral order); only
C34:6 has 312, so W7 = C34:6. It has a vertex shared by three hexagons, matching
Fig 6 (three hexagons meet at the centre of the drawing).

Re-verification options (optional; no C compiler was available on the machine
where this spec was written, so these are untested): `fullgen 28 code 1` from the
vendored `third_party/plantri` (fullgen-guide.txt: code 1 = planar code of each
fullerene) lists both C28 isomers; alternatively `plantri_maxd -m5 -D6 -d F`
(maxdeg.c plugin; F = V/2 + 2 faces) generates the fullerenes with F faces, and
`plantri -m5 -d 16` followed by a face-size filter {5:14, 7:2} finds W6. Match
by graph isomorphism against Appendix A.

### 8.4 Outer faces (B19 mode)

The outer face of B19's drawing (Fig 6) for each web, as a face of Appendix A
(min dart; vertex cycle):

| Web | outer face min dart | vertices | size | remark |
| --- | --- | --- | --- | --- |
| W1 | 1 | 0 1 2 3 4 | 5 | all pentagons equivalent under Aut |
| W2 | 1 | 0 1 2 3 4 5 | 6 | both hexagons equivalent |
| W3 | 6 | 2 6 12 19 13 7 | 6 | the four hexagons give the same N |
| W4 | 3 | 1 4 10 17 11 5 | 6 | the four hexagons are equivalent |
| W5 | 6 | 2 6 12 19 13 7 | 6 | the three hexagons are equivalent |
| W6 | 1 | 0 1 2 3 4 5 6 | 7 | both heptagons equivalent |
| W7 | 13 | 4 7 13 21 16 10 | 6 | **the unique hexagon on the C3 axis**; the other hexagon classes give N = 106 950 or 108 318, not 101 970 |

---

## 9. Controls and expected values

Every control must pass in both implementations before any W-result is reported.

### 9.1 Closed-foam evaluation (KR Example 2.15 and Cor 2.16, p.12–13)

Closed foams are given directly in facet–seam form (§4.1). Expected values are
the polynomial ⟨F⟩ **[KR]**, Φ(⟨F⟩) **[spec-check]**, and J♭(F).

| # | Foam | facets (chi, dots) · seams · nv | ⟨F⟩ | Φ | J♭ |
| --- | --- | --- | --- | --- | --- |
| 1 | empty | none | 1 | 1 | 1 |
| 2 | sphere, n dots | (2, n) · – · 0 | h_{n−2}(X) (0 for n<2) | 1 iff n ≡ 2 (mod 3) | 1 iff n = 2 |
| 3 | theta foam θ(n₁,n₂,n₃) | (1,n₁),(1,n₂),(1,n₃) · (0,1,2) · 0 | s_{(n₁−2, n₂−1, n₃)} for n₁≥n₂≥n₃ (KR eq (8)); 0 if two n's equal | 1 iff {n₁,n₂,n₃} ∈ {{0,1,2},{1,2,3}} (for n_i ≤ 3) | 1 iff {n₁,n₂,n₃} = {0,1,2} |
| 4 | torus, n dots | (0, n) · – · 0 | p_n = X₁ⁿ+X₂ⁿ+X₃ⁿ | 1 iff 3 ∣ n | 1 iff n = 0 |
| 5 | genus-2 surface, n dots | (−2, n) · – · 0 | Σ_i X_iⁿ (X_i+X_j)(X_i+X_k) | 1 iff n ≡ 1 (mod 3) | 0 |
| 6 | Γ × S¹ (Γ a web) | one annulus (0,0) per edge, one torus (0,0) per circle · one seam per vertex, triple = its three edges · 0 | Tait(Γ) mod 2 (KR Ex 2.15(5)) | same | same |
| 7 | torus + meridian disk + longitude disk (KR Ex 2.15(2)) | A=(1,0), Dm=(1,0), Dl=(1,0) · (A,A,Dm), (A,A,Dl) · 1 | 0 (no admissible colouring) | 0 | 0 |

Row 2 in detail (KR Cor 2.16, p.13): n = 0, 1 → 0; n = 2 → 1; n = 3 → E₁;
n = 4 → E₁² + E₂ (Φ = 0 for n = 3, 4; J♭ = 0). Row 2 with n = 5 has Φ = 1: the E₃
coefficient of h₃ is 1.
Specific values for rows 3 and 6: θ(2,1,0) → 1 (KR Cor 2.16/Ex (4)); θ(1,1,0) → 0;
θ(1,2,3) → Φ = 1, deg 6 (s_{(1,1,1)} = E₃); θ × S¹ = theta web × S¹ → 6 mod 2 = 0;
circle × S¹ = torus → 1.

Full-polynomial tests (§2.5): rows 2–5 at the two GF(2⁸) points, n = 0…6, and
θ(n₁,n₂,n₃) for all 0 ≤ n_i ≤ 4, compared with h_m and Jacobi–Trudi Schur values.

Relation tests (KR §2.5, evaluated with Φ; optional): dot migration
Φ(θ(1,0,0)) + Φ(θ(0,1,0)) + Φ(θ(0,0,1)) = Φ(E₁)·Φ(θ(0,0,0)) = 0, and
Σ over the three facets of θ(n+1 on one facet) = 0 for any fixed dot vector n
(KR Prop 2.32, p.22).

### 9.2 KM19 §8.3 rules (independent cross-check for vertex-free foams; optional)

KM19 p.71–72 evaluate a closed pre-foam by: (a) J = 0 if the seam graph is not
bipartite; (b) cancel seam vertices in pairs along a perfect matching (KR Prop
2.26, p.20); (c) J = 0 if the monodromy of the three sheets around a seam circle is
nontrivial; (d) neck-cut the three facets next to each seam circle — at E = 0 each
neck-cut is the sum of the three terms with (2,0), (1,1), (0,2) dots on the two new
disks (KR Prop 2.22, p.15; KM19 Prop 6.1, p.50–51); (e) evaluate: θ(k₁,k₂,k₃) = 1
iff {k} = {0,1,2} (KM19 Prop 5.6, p.46); sphere = 1 iff exactly 2 dots; dotless
torus = 1; everything else 0 (including non-orientable). KR Thm 2.35 (p.23) proves
this equals J♭ for foams **in R³**, and KR p.27–30 show step (b) is ill-defined for
some non-embeddable pre-foams. Use only on vertex-free test foams (rows 2–6
above), with a representation that tracks which facet boundary circles lie on
which seam circle.

### 9.3 Pairings on the circle and theta webs (explicit vectors) **[spec-check]**

Circle (m = 1; Tait order: circle colour 1, 2, 3). GEN = [C1, Ċ1, C̈1] with
degrees −2, 0, 2 and a-vectors (hex codes of §0) `132`, `111`, `123`. J♭ Gram
matrix: antidiagonal [[0,0,1],[0,1,0],[1,0,0]] (sphere with 2 dots), ℓ = 3.

Theta (α = [3,5,4,0,2,1]; edges e₀={0,3}, e₁={1,5}, e₂={2,4}; Tait order 123, 132,
213, 231, 312, 321 as colours of (e₀,e₁,e₂)). The greedy picks the bigon (0,4);
its legs 1, 5 are the same edge, so K′ is a circle. GEN = C2∘[C1,Ċ1,C̈1] ++
Ċ2∘[C1,Ċ1,C̈1] with degrees −3, −1, 1, −1, 1, 3 and a-vectors

    111111, 231312, 321213, 112233, 232131, 322332.

J♭ Gram matrix (rows/cols in this order):

    0 0 0 0 0 1
    0 0 0 0 1 0
    0 0 0 1 0 0
    0 0 1 0 1 0
    0 1 0 1 0 0
    1 0 0 0 0 0

rank 6; ℓ_q = q⁻³ + 2q⁻¹ + 2q + q³. (Each entry is θ(a+a′, b+b′, 0) with a, a′ the
cup dots and b, b′ the Ċ2 dots: 1 iff the multiset is {0,1,2}.)

### 9.4 Reducible webs: the generated basis reaches Tait **[spec-check]**

GEN (STRICT, all faces) on the reducible controls gives exactly Tait(K) half-foams,
ℓ = Tait(K), and ℓ_q = qdim J♭(K) (KR §4.4; B19 eq (2)):

| Web | Tait | ℓ_q |
| --- | --- | --- |
| circle | 3 | q⁻² + 1 + q² |
| two circles | 9 | q⁻⁴ + 2q⁻² + 3 + 2q² + q⁴ |
| theta, K4, prism3 | 6 | q⁻³ + 2q⁻¹ + 2q + q³ |
| cube | 24 | 2q⁻⁴ + 6q⁻² + 8 + 6q² + 2q⁴ |
| prism5 | 30 | q⁻⁵ + 5q⁻³ + 9q⁻¹ + 9q + 5q³ + q⁵ |
| prism6 | 72 | q⁻⁶ + 7q⁻⁴ + 17q⁻² + 22 + 17q² + 7q⁴ + q⁶ |

Also r = Tait and r_q = ℓ_q for these (§7.3) **[spec-check]**, as it must be
(for reducible K the basis is a basis of the free module ⟨K⟩, KR p.52), and every
ℓ_q above is divisible by [3]! = (q²+1+q⁻²)(q+q⁻¹) except for the circle webs
(B19 p.14).

A test of §7.3 where r_q ≠ ℓ_q **[spec-check]**: on the circle take the three
half-foams "cup with δ dots" (one facet, chi 1, dots δ, owning the circle; deg
2δ−2) for δ = 0, 1, 5, i.e. degrees −2, 0, 8, a-vectors `132`, `111`, `123`.
Then ℓ_q = 1 (only the pair (1,1) has degree sum 0), r = 3, and
r_q = q⁻² + 1 + q⁸ (the pair (0,5) is a sphere with 5 dots, ⟨·⟩_ψ = E). With
δ = 0, 1, 2, 3 instead: ℓ_q = r_q = q⁻² + 1 + q².

### 9.5 Moves exercised on reducible webs **[spec-check]**

Apply §6.2 (all faces, STRICT) to reducible targets. Expected:

| Target | N | Zip / Unzip / Saddle / IH | ℓ | ℓ_q |
| --- | --- | --- | --- | --- |
| prism5 | 3 660 | 360 / 2 190 / 840 / 270 | 30 | as in §9.4 |
| cube | 2 160 | 288 / 1 224 / 576 / 72 | 24 | as in §9.4 |

KR Lemma 4.11 chains on W1 (Appendix A), site face F₀ = (0, 13, 40, 43, 16) (the
canonical face of dart 0), pair (f₀, f₂) = (0, 40), and edge 0 = {0, 12}:

1. K₁ = Unzip(W1; F₀; 0, 2); K₂ = IH(K₁; edge with min dart 60 = tS). Supports
   (number of (t′,t) pairs with at least one local colouring): 36 (Unzip),
   36 (IH); Boolean product empty.
2. K₁ = Saddle(W1; F₀; 0, 2); K₂ = Unzip(K₁; the face containing both new edges
   n₁, n₂, at their darts). Supports 24, 48; product empty.
3. K₁ = Zip(W1; edge 0); K₂ = Saddle(K₁; the face containing both joined edges).
   Supports 24, 12; product empty.
4. K₁ = IH(W1; edge 0); K₂ = Zip(K₁; edge with min dart 54 = the new edge e′).
   Supports 36, 36; product empty.
5. Contrast: K₁ = Unzip(W1; F₀; 0, 2), K₂ = Zip(K₁; edge with min dart 60):
   product non-empty (36 pairs).

### 9.6 The B19 targets

**B19 Table 2 (p.10)** [B19]:

| Web | ℓ(K) | Tait(K) | N_ℓ | N_e | N |
| --- | ---: | ---: | ---: | ---: | ---: |
| W1 | 58 | 60 | 156 | 6 727 | 11 160 |
| W2 | 120 | 120 | 747 | 5 322 | 27 792 |
| W3 | 162 | 162 | 822 | 4 902 | 45 960 |
| W4 | 178 | 180 | 1 193 | 6 351 | 47 196 |
| W5 | 188 | 192 | 2 447 | 7 153 | 40 704 |
| W6 | 248 | 252 | 1 726 | 6 331 | 53 172 |
| W7 | 308 | 312 | 1 190 | 5 458 | 101 970 |

**B19 Table 3 (p.14)** [B19]: ℓ_q(K), and in parentheses r_q(K) − ℓ_q(K) when
nonzero; r(K) = Tait(K) for all seven.

| Web | ℓ_q(K) | r_q − ℓ_q |
| --- | --- | --- |
| W1 | 9q⁻³ + 20q⁻¹ + 20q + 9q³ | 2q³ |
| W2 | 3q⁻⁵ + 2q⁻⁴ + 16q⁻³ + 6q⁻² + 29q⁻¹ + 8 + 29q + 6q² + 16q³ + 2q⁴ + 3q⁵ | 0 |
| W3 | 2q⁻⁵ + 7q⁻⁴ + 13q⁻³ + 21q⁻² + 24q⁻¹ + 28 + 24q + 21q² + 13q³ + 7q⁴ + 2q⁵ | 0 |
| W4 | q⁻⁶ + 11q⁻⁴ + 10q⁻³ + 29q⁻² + 19q⁻¹ + 38 + 19q + 29q² + 10q³ + 11q⁴ + q⁶ | q + q⁵ |
| W5 | 4q⁻⁵ + 31q⁻³ + 59q⁻¹ + 59q + 31q³ + 4q⁵ | q + 2q³ + q⁵ |
| W6 | 20q⁻⁴ + 62q⁻² + 84 + 62q² + 20q⁴ | 2q² + 2q⁴ |
| W7 | 4q⁻⁵ + 5q⁻⁴ + 41q⁻³ + 15q⁻² + 79q⁻¹ + 20 + 79q + 15q² + 41q³ + 5q⁴ + 4q⁵ | q + 2q³ + q⁵ |

(Coefficient sums check: ℓ_q(1) = ℓ and r_q(1) = Tait in every row.)

Acceptance for the reproduction (B19 mode, whole list S(K)):

- N equals Table 2 N (already confirmed at spec time, §6.4);
- ℓ(K) ≥ Table 2 ℓ(K) (B19 used only the first N_e half-foams in its own order,
  so a larger value is possible in principle; see §10, item 2), and ℓ(W2) = 120,
  ℓ(W3) = 162 exactly (they cannot exceed Tait);
- ℓ_q, r and r_q as in Table 3, **or** a documented difference;
- B19 Remark 4.2 (p.10–11): for W1, each move type alone (only Zip sites, only
  Unzip, only Saddle, only IH) gives ℓ = 58.

### 9.7 Optional: KM's colouring half-foams for W1 (B19 Remark 4.3, p.11)

For a proper 4-colouring c₄ of the faces of K, F(K,c₄) = (T×{0}) ∪ (K×[0,1]) where T
is the union of faces not coloured 4 (B19 eq (12)). In facet–seam form: one
"floor" facet per face in T; one "wall" facet e×[0,1] per edge e; a wall whose one
side is a 4-face merges with the floor on its other side; seams: e×{0} for edges
between two T-faces (triple: two floors, wall), v×[0,1] (walls), and seam vertices
at each vertex with no adjacent 4-face. For W1 there are 240 face 4-colourings,
giving 20 distinct half-foams of degree −3; with 0–3 dots added they give ℓ = 58
[B19, KM19 p.73]. B19 does not say on which facets the dots go (§10, item 9).

---

## 10. Known pitfalls and open ambiguities (decisions for Gabriel)

Each item says what this spec does and what needs a decision.

1. **B19 mode is inferred, not stated.** B19 does not say that the unbounded face
   is excluded from Unzip/Saddle sites and from reductions, nor that failed
   square branches are simply dropped ("partial" semantics); B19 p.6 says only
   that a web the greedy fails on is treated "as if it were nonreducible". The
   straightforward reading (STRICT-ALL) gives N = 11 880 for W1 against B19's
   11 160, and differs for every web (§6.4). With the outer face excluded
   everywhere and partial semantics, N matches **all seven** Table 2 values
   exactly; this is strong evidence but not proof. Consequences: in PARTIAL
   semantics, S(K′) is no longer a basis of J♭(K′), and the generated span may in
   principle depend on the greedy face choice (the count N does not, §6.4).
   *Decision:* accept B19 mode as the reproduction target, or ask for Boozer's
   Mathematica code (B19 ref [3]; downloading needs Gabriel's approval) to
   confirm.
2. **B19 evaluated only a prefix.** B19's ℓ is the value of β_n for n ≤ N_e (6 727
   of 11 160 for W1), in B19's order. This spec computes ℓ over the whole list.
   If ℓ(W1) came out as 59 or 60 here, that is not a contradiction of B19, but it
   would be the first evidence for dim J♭(W1) = 60 and must be treated as a lead
   until both implementations agree and Gabriel has reviewed it. Note B19 Remark
   4.2 (each move type alone gives 58).
3. **Order-dependent quantities are not reproducible.** N_ℓ, N_e and the β_n
   curve (B19 Fig 7) depend on B19's ordering of S(K), which is not given. This
   spec fixes its own order (§6.1–6.2: block order of variants, Zip/Unzip/Saddle/IH,
   sites by dart order); report our β_n but do not compare it to B19's.
4. **Order and choices inside the reducible basis.** B19 (rule (1), p.5) does not
   say whether C1, Ċ1, C̈1 are applied in blocks or interleaved, which face is
   eliminated first, which smoothing is "4a", or on which bowl half Ċ2's dot sits.
   In STRICT semantics none of these affects ℓ, ℓ_q, r, r_q (the span is the image
   of J♭(C)); they only affect the list order and the a-vector file.
5. **Reading of Fig 4.** Zip = delete the edge and join the legs on each side
   (")(" parallel to the edge); Unzip = fuse two edges of a face into a new edge
   parallel to them (the exact inverse replacement); Saddle = reconnect through
   the face; IH = planar flip. The "rung" reading of Unzip (a new edge across the
   face) and the "delete edge and join legs at the same vertex" reading of Zip
   were both tested and give wrong N. Adjacent-edge Unzip and Saddle sites are
   enumerated but never contribute (bigon back to K, resp. a loop).
6. **Outer-face tracking when the marker is lost** (§3.7). When every vertex of
   the outer face is deleted, this spec stops excluding any face. This reproduces
   all seven N values, but other rules were not tested. It matters only in
   B19 mode.
7. **W identification.** W6 is read from the figure (B19 never calls it a
   fullerene); W3/W4 are fixed by Tait counts and W7 by its unique Tait count
   among the six C34 isomers; all seven N values then match, which also confirms
   the identifications. The designated outer face of W7 matters (§8.4).
8. **Mirror images and labelling.** Rotation systems may be the mirror image of
   B19's drawings; nothing depends on this. Labels matter only for the a-vector
   file and the β_n curve.
9. **B19 Remark 4.3 (KM's half-foams)**: where the 0–3 dots go is not stated. If
   this control is run, use "every multiset of k ≤ 3 dots on the facets" and
   report the reading.
10. **Degree convention.** Half-foam degree is KR eq (9) (p.30) = B19 eq (8);
    q-dimensions are Σ q^{deg}. B19 Table 1's degrees are reproduced by §4.3;
    KR Fig 22's degrees (1,1,2,1) agree.
11. **J♭ of a degree-≠0 foam is 0**, but do not skip the evaluation: the
    automatic vanishing of Φ when the degree is negative or not divisible by 6 is
    a free check (§2.4).
12. **Pre-foams vs foams.** KM's Conjecture 8.9 (evaluation of abstract pre-foams)
    is false in general (KR p.27–30); KR Thm 2.35 covers foams in R³ only. Every
    closed foam here is a gluing of two embedded half-foams, hence embedded.
13. **Degenerate webs in B19 mode.** Because the outer face is never reduced,
    a bigon can survive while triangles and squares are eliminated, so legs can
    coincide (§5.4 degenerate case) and joins can create circles. The REBUILD
    rules and the "one facet per bottom edge" rule of §4.3 handle this; assert
    that no K′-edge ends up in two distinct local facets after merging.
14. **Bridges.** Any web with a bridge (including a loop) has Tait 0, is never
    reducible, and GEN returns FAIL/[] for it; check bridges before choosing a
    face (face orbits of bridged webs are degenerate).
15. **Tooling.** No C compiler was available where this spec was written, so the
    plantri/fullgen commands in §8.3 are untested. They are optional.
16. **Runtime.** Mode G enumerates colourings for about 10⁵ half-foams × up to 312
    boundary colourings (W7): write it in a compiled language or vectorise.
    Mode T is matrix products over GF(4) of size ≤ a few hundred. Heavy runs go
    to the self-hosted runner with `JOBS`/`MEMORY` respected (`search/README.md`).

---

## 11. Division of labour between Implementation A and Implementation B

Both implementations implement §3 (webs, REBUILD, faces, Tait colourings), §5
(records), §6 (GEN, moves, three modes) and §7 (ranks) independently, from this
spec only, without reading each other's code (house rule).

- **Implementation A (Mode G, B19-like):** builds facet–seam half-foams by
  composition (§4.3), computes a-vectors by direct colouring enumeration (§4.5),
  and evaluates glued closed foams directly (§4.4) for the §7.5 sample of pairs
  and for all controls of §9.1–9.3.
- **Implementation B (Mode T):** never builds half-foams; computes a-vectors by
  transfer-matrix products (§4.6); evaluates the §9.1 foams by §2.4 directly.

Agreement criteria: identical `halffoams.jsonl` (hence identical SHA-256) for every
(web, mode), identical `result.json` apart from the implementation name and
timing, and all §9 controls passing in both. Either implementation may add the
optional graded-Smith-form check (§7.3) or the KM-rules evaluator (§9.2).

Suggested layout (not binding): `search/d1/impl_a/`, `search/d1/impl_b/`,
`search/d1/webs/` (Appendix A as files), `search/d1/results/<impl>/<web>/<mode>/`,
with the command lines logged in `notes/D-topology-and-gauge-theory.md`.

---

## Appendix A — rotation systems (authoritative)

Format: `v: w0,w1,w2` = the neighbours of v in counter-clockwise order (dart 3v+k
points to w_k). All are simple graphs except theta. Each line was checked
**[spec-check]** for: α an involution, V − E + F = 2, the face-size vector, |Aut|
and Tait as stated.

**circle**: V = 0, m = 1. **two circles**: V = 0, m = 2.

**theta**: V = 2, m = 0, α = [3, 5, 4, 0, 2, 1] (darts 0,1,2 at vertex 0; 3,4,5 at
vertex 1). Faces (0,4), (1,3), (2,5). Tait 6.

**K4** (faces 4×3, |Aut| 24, Tait 6):

    0:1,2,3 1:2,0,3 2:3,0,1 3:2,1,0

**prism3** (faces 2×3 + 3×4, |Aut| 12, Tait 6):

    0:1,2,3 1:4,0,3 2:5,0,4 3:5,1,0 4:5,2,1 5:4,3,2

**cube** (faces 6×4, |Aut| 48, Tait 24):

    0:1,2,3 1:4,0,5 2:6,0,4 3:6,5,0 4:7,2,1 5:7,1,3 6:7,3,2 7:4,5,6

**prism5** (faces 5×4 + 2×5, |Aut| 20, Tait 30):

    0:1,2,3 1:4,0,5 2:6,0,4 3:6,7,0 4:8,2,1 5:8,1,7 6:9,3,2 7:9,5,3 8:4,5,9 9:8,7,6

**prism6** (faces 6×4 + 2×6, |Aut| 24, Tait 72):

    0:1,2,3 1:4,0,5 2:6,0,4 3:6,7,0 4:8,2,1 5:8,1,9 6:10,3,2 7:10,9,3 8:4,5,11
    9:11,5,7 10:11,7,6 11:8,9,10

**W1** = D(5), dodecahedron (V 20; faces 12×5; |Aut| 120; Tait 60; outer face
min dart 1):

    0:4,1,5 1:2,7,0 2:3,9,1 3:4,11,2 4:0,13,3 5:14,0,6 6:15,5,7 7:6,1,8 8:9,16,7
    9:10,8,2 10:11,17,9 11:3,12,10 12:13,18,11 13:4,14,12 14:13,5,19 15:19,6,16
    16:17,15,8 17:18,16,10 18:12,19,17 19:18,14,15

**W2** = D(6), C24 (V 24; faces 12×5 + 2×6; |Aut| 24; Tait 120; outer face min
dart 1):

    0:5,1,6 1:8,0,2 2:3,10,1 3:4,12,2 4:5,14,3 5:0,16,4 6:17,0,7 7:18,6,8 8:7,1,9
    9:10,19,8 10:11,9,2 11:12,20,10 12:13,11,3 13:14,21,12 14:4,15,13 15:16,22,14
    16:15,5,17 17:16,6,23 18:23,7,19 19:20,18,9 20:21,19,11 21:13,22,20
    22:15,23,21 23:22,17,18

**W3** = C28:1, D2 (V 28; faces 12×5 + 4×6; |Aut| 4; Tait 162; outer face min
dart 6):

    0:1,2,3 1:4,0,5 2:6,0,7 3:8,9,0 4:10,7,1 5:11,1,9 6:12,8,2 7:13,2,4 8:14,3,6
    9:15,5,3 10:16,4,11 11:10,5,17 12:18,6,19 13:19,7,20 14:18,21,8 15:17,9,21
    16:22,20,10 17:22,11,15 18:23,14,12 19:24,12,13 20:25,13,16 21:26,15,14
    22:16,17,27 23:24,26,18 24:23,19,25 25:24,20,27 26:27,21,23 27:25,22,26

**W4** = C28:2, Td (V 28; faces 12×5 + 4×6; |Aut| 24; Tait 180; outer face min
dart 3):

    0:1,2,3 1:4,0,5 2:6,0,7 3:8,9,0 4:10,7,1 5:11,1,9 6:12,8,2 7:13,2,4 8:14,3,6
    9:15,5,3 10:16,4,17 11:17,5,18 12:19,6,20 13:20,7,16 14:19,21,8 15:18,9,21
    16:22,13,10 17:23,10,11 18:24,11,15 19:25,14,12 20:26,12,13 21:27,15,14
    22:26,16,23 23:22,17,24 24:23,18,27 25:26,27,19 26:25,20,22 27:24,21,25

**W5** = C26, D3h (V 26; faces 12×5 + 3×6; |Aut| 12; Tait 192; outer face min
dart 6):

    0:1,2,3 1:4,0,5 2:6,0,7 3:8,9,0 4:10,7,1 5:11,1,9 6:12,8,2 7:13,2,4 8:14,3,6
    9:15,5,3 10:16,4,11 11:10,5,17 12:18,6,19 13:19,7,16 14:18,20,8 15:17,9,20
    16:21,13,10 17:22,11,15 18:23,14,12 19:24,12,13 20:25,15,14 21:24,16,22
    22:21,17,25 23:24,25,18 24:23,19,21 25:22,20,23

**W6** = D(7) (V 28; faces 14×5 + 2×7; |Aut| 28; Tait 252; outer face min dart 1):

    0:6,1,7 1:9,0,2 2:3,11,1 3:4,13,2 4:5,15,3 5:6,17,4 6:5,0,19 7:20,0,8 8:21,7,9
    9:8,1,10 10:22,9,11 11:12,10,2 12:13,23,11 13:14,12,3 14:15,24,13 15:4,16,14
    16:17,25,15 17:5,18,16 18:19,26,17 19:18,6,20 20:19,7,27 21:27,8,22
    22:23,21,10 23:24,22,12 24:25,23,14 25:16,26,24 26:18,27,25 27:26,20,21

**W7** = C34:6, C3v (V 34; faces 12×5 + 7×6; |Aut| 6; Tait 312; outer face min
dart 13):

    0:1,2,3 1:4,0,5 2:6,0,7 3:8,9,0 4:10,7,1 5:11,1,9 6:12,8,2 7:13,2,4 8:14,3,6
    9:15,5,3 10:16,4,17 11:17,5,18 12:19,6,20 13:20,7,21 14:19,22,8 15:18,9,22
    16:23,21,10 17:24,10,11 18:25,11,15 19:26,14,12 20:27,12,13 21:28,13,16
    22:29,15,14 23:30,16,24 24:23,17,25 25:24,18,31 26:27,32,19 27:26,20,28
    28:27,21,33 29:31,22,32 30:31,33,23 31:30,25,29 32:33,29,26 33:32,28,30
