# B2 Phase 1 — Specification: per-configuration D-reducibility data

Issue #48 (B2, "Explain reducibility"), Phase 1, as released by Gabriel on 2026-09-30 with four
decisions (recorded in the issue's latest comment):

1. scope: ring size ≤ 14 first, 5,897 configurations including `deg3` and `deg4`;
2. contrast class (b): the one-vertex deletions of configurations in 𝒟 that are not themselves in 𝒟;
3. no existing reducibility implementation is read, by anyone;
4. machine: WSL, at most 8 GB and at most 4 hours per run. Cap: 10 runner-hours for Phase 1 in
   both implementations together; stop and ask at 8.

This document is the **only** thing the two implementers read, apart from the input data, the
configuration index and `CLAUDE.md` (§10). It says what to compute, exactly how to serialise it,
and what the answers must be on the controls.

**Status of this document.** It is a specification, not a result. Nothing in it is a result in
the sense of `CLAUDE.md`. Numbers marked **[spec-check]** were confirmed by the spec author with
throwaway scripts while writing this document (not committed, not an implementation, not seen by
the implementers). Numbers marked **[derived]** were derived by hand and not checked by a script.
Numbers marked **[NL]**, **[idx]** are quoted from the sources of §0.

## Contents

0. Sources and notation
1. Input: configurations, the free completion, the ring labelling
2. Ring colourings
3. Round 0: colourings that extend
4. Kempe rounds
5. D-reducibility and the per-configuration record
6. The contrast class: one-vertex deletions
7. Output files (byte-comparable)
8. Controls, with expected values
9. Cost, the count-only pass, and the run plan
10. Independence rules and division of labour
11. Readings of the sources
12. Questions for Gabriel
13. Sources

---

## 0. Sources and notation

| Tag | Source | Cited as |
| --- | --- | --- |
| **NL** | Y. Inoue, K. Kawarabayashi, A. Miyashita, B. Mohar, C. Thomassen, M. Thorup, *The Four Color Theorem with Linearly Many Reducible Configurations and Near-Linear Time Coloring*, arXiv:2603.24880v2 (7 May 2026), read as the arXiv HTML page | section, lemma or algorithm number |
| **RSST** | N. Robertson, D. P. Sanders, P. D. Seymour, R. Thomas, *The four-colour theorem*, J. Combin. Theory Ser. B 70 (1997) 2–44 | **not re-read for this spec** (see §11, §12 Q4); cited only for context |
| **idx** | this repository's `search/index/build.py` (docstring and code) and `search/index/README.md` | function name |

Notation used throughout:

- The four colours are the integers 0, 1, 2, 3 (as in [NL App. A.1]; [NL §2.1] writes 1–4, which
  is immaterial). Identify them with the vectors of F₂² by their binary digits, so that addition
  is bitwise XOR, written ⊕.
- For θ ∈ {1, 2, 3}, the map x ↦ x ⊕ θ is the permutation of colours that swaps the two colours
  of each pair in the split {{0, θ}, {1, 2, 3} ∖ {θ}}. These three splits are exactly the three
  ways of dividing the four colours into two complementary pairs {a, b}, {c, d} of [NL §2.1], with
  θ = a ⊕ b = c ⊕ d (because 0 ⊕ 1 ⊕ 2 ⊕ 3 = 0). So "switch a and b on some ab-chains, and c and d
  on some cd-chains" is "XOR θ on some chains of either kind".
- Catalan numbers: Cat(m) = 1, 1, 2, 5, 14, 42, 132, 429 for m = 0, …, 7.

---

## 1. Input

### 1.1 Configurations in scope

𝒟 has 8,202 configurations [NL §3, Lemma 3.2]: 8,200 files
`data/near-linear-4ct/reducible-configurations/D/D0000.conf` … `D8199.conf`, plus the single
vertex of degree 3 (`deg3`) and of degree 4 (`deg4`), which have no file [NL §3; idx].
`search/index/configurations.csv` lists all 8,202, in the order D0000, …, D8199, deg3, deg4, with
ring size, vertex count, degree sequence and `shape`.

**In scope for Phase 1:** every row with `ring_size ≤ 14`, in the CSV's row order. That is 5,897
configurations **[spec-check]**:

| R | 3 | 4 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| configurations | 1 | 1 | 1 | 1 | 5 | 15 | 60 | 210 | 779 | 2,025 | 2,799 | 5,897 |

(There is no configuration with R = 5.) Ring sizes 15–18 (2,305 configurations) are Phase 1's
possible extension, decided later from measured costs.

### 1.2 The file format

As documented in the docstring of `search/index/build.py` [idx]:

- line 1 is empty; line 2 is `N R`; the free completion has N vertices, 1..R form the ring and
  R+1..N are the configuration's own vertices;
- then one line per configuration vertex: `v d n_1 … n_d`, its degree d (in the triangulation,
  the δ(v) of [NL §2.1]) and its d neighbours in cyclic order;
- the ring is the cycle 1, 2, …, R, 1; ring vertices have no line; there are no edges between
  ring vertices other than the ring's own R edges;
- orientation: if b follows a around v, then b precedes v around a; wherever two ring vertices
  are consecutive around v, the second is the next ring vertex (i ↦ i mod R + 1).

Read files with `build.parse` (or your own parser) and **always** run `build.validate` on the
result (§10 allows importing `search/index/build.py`). The files are Git LFS objects: a file that
starts with `version https://git-lfs` is a pointer, and the run must stop with a message.

`deg3` and `deg4` are built as `build.single_vertex(3)` and `build.single_vertex(4)`: N = d + 1,
R = d, the single configuration vertex d + 1 with neighbours 1, 2, …, d in that order.

### 1.3 Free completion and ring

The free completion Ẑ of a configuration (Z, δ) adds a cycle R around Z so that every vertex v of
Z has exactly δ(v) neighbours and every inner face is a triangle [NL §2.1]. For the files, Ẑ is
the graph the file describes: vertices 1..N, the ring edges {i, i mod R + 1}, and the edges
{v, n_j}. Its ring size satisfies |R| = Σ_{v∈Z} δ(v) − 2|E(Z)| − t, with t the length of Z's
outer facial walk [NL §2.1].

**Ring labelling (normative).** Ring vertex i (1 ≤ i ≤ R) of the file is **position** p = i − 1.
Positions 0, …, R−1 in increasing order walk the ring in the file's direction. Ring edge
**e_p** (p = 0, …, R−1) joins positions p and (p + 1) mod R. For `deg3`/`deg4` and for the wheels
of §8, the ring is the neighbours 1..d in order. For derived configurations (the contrast class),
§6.4 fixes the labelling. All counts in the record of §5 are invariant under relabelling and
reflection of the ring (§5.3); the labelling matters only for the order of colourings and hence
for `levels_sha256`.

---

## 2. Ring colourings

### 2.1 Definition

A **ring colouring** is a proper 4-colouring of the ring cycle: a sequence κ = (κ_0, …, κ_{R−1})
with κ_p ∈ {0, 1, 2, 3} and κ_p ≠ κ_{(p+1) mod R} for every p [NL §2.1: "a coloring φ of R";
[NL] colourings are proper vertex colourings, §2.1 first paragraph].

The spec uses **vertex 4-colourings of the ring**, as [NL §2.1] and [NL Alg. 1–3] do, not the
3-edge-colourings of the ring edges that RSST use (from memory, §11 R6). The two are equivalent: the edge colour of e_p is κ_p ⊕ κ_{p+1} ∈
{1, 2, 3}, and this map is 4-to-1 (translations κ ↦ κ ⊕ t) onto the edge colourings whose XOR
around the ring is 0 **[derived]**.

### 2.2 Colour permutations, canonical representative

Every permutation π of {0, 1, 2, 3} maps colourings of Ẑ to colourings of Ẑ, Kempe chains to
Kempe chains and Kempe changes to Kempe changes. So "extends" (§3) and "added in round k" (§4)
are unions of orbits of the permutation group S₄ acting on ring colourings, and everything is
computed on orbits.

The **canonical representative** of an orbit is its lexicographically least member, which is the
**restricted-growth** colouring: κ_0 = 0, and for p ≥ 1, κ_p ≤ 1 + max(κ_0, …, κ_{p−1}). For a
proper colouring with R ≥ 2 this forces κ_1 = 1. `canon(λ)` of any proper colouring λ relabels its
colours in order of first appearance along positions 0, 1, 2, … as 0, 1, 2, 3.

C* denotes the set of canonical ring colourings. **Order (normative):** C* is listed in increasing
lexicographic order of the tuple (κ_0, …, κ_{R−1}). The k-th element of this list (0-based) is
colouring number k.

### 2.3 Counts

The number of proper 4-colourings of the R-cycle is 3^R + 3·(−1)^R (chromatic polynomial of a
cycle, (q−1)^R + (−1)^R (q−1) at q = 4). Every S₄-orbit has 24 members except, for even R, the one
orbit of 2-colourings (0101…01), which has 12. Hence

  |C*| = N_R = (3^R + 15)/24 for even R,  (3^R − 3)/24 for odd R   **[derived; spec-check below]**

| R | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| N_R | 1 | 4 | 10 | 31 | 91 | 274 | 820 | 2,461 | 7,381 | 22,144 | 66,430 | 199,291 |

**[spec-check]**: enumeration of restricted-growth colourings equals the formula for R = 3..14; the
labelled counts 3^R + 3(−1)^R were checked by exhaustive enumeration for R = 3..8. For reference,
N_15..N_18 = 597,871; 1,793,614; 5,380,840; 16,142,521 **[derived]** (the issue's "about 16 million"
at R = 18). Σ N_R over the 5,897 in-scope configurations is 711,297,902 **[spec-check]**.

---

## 3. Round 0: colourings that extend

κ ∈ C* **extends** (is 0-extendible [NL §2.1]) iff there is a map f from the configuration's
vertices to {0, 1, 2, 3} with

- f(u) ≠ f(w) for every edge uw between two configuration vertices, and
- f(u) ≠ κ_{r−1} for every configuration vertex u and every ring vertex r among u's neighbours.

(The ring's own edges are satisfied because κ is proper.) E_0 ⊆ C* is the set of canonical
colourings that extend. Because a colour permutation maps extensions to extensions, testing the
canonical representative decides the whole orbit.

`direct` = |E_0|.

---

## 4. Kempe rounds

### 4.1 Transitions

Fix κ ∈ C* and θ ∈ {1, 2, 3}. Ring edge e_p is a **θ-transition** of κ iff κ_p ⊕ κ_{p+1} ≠ θ
(indices mod R), i.e. iff its two ends lie in different pairs of the split θ. Let

  T = T(κ, θ) = (t_0 < t_1 < … < t_{2m−1}), the positions p of the θ-transitions e_p.

|T| is even (the pairs alternate along the ring and the ring closes) **[derived]**; write
|T| = 2m, m ≥ 0.

### 4.2 Non-crossing matchings

𝓜(2m) is the set of **non-crossing perfect matchings** of the index set {0, 1, …, 2m−1}: sets of
m pairs (a, b) with a < b that partition the index set, such that no two pairs (a, b), (c, d)
satisfy a < c < b < d. |𝓜(2m)| = Cat(m). 𝓜(0) = {∅}.

A pair (a, b) of M is a **chord**. Its **arc** is the set of positions
A(a, b) = {t_a + 1, t_a + 2, …, t_b}. (Since t_a < t_b ≤ R − 1, an arc never wraps, and position 0
is in no arc.)

### 4.3 Flips and the reachable set

For S ⊆ M, the flip κ^S is the colouring with

  κ^S_p = κ_p ⊕ θ if p lies in an odd number of the arcs A(a, b), (a, b) ∈ S; κ^S_p = κ_p otherwise.

κ^S is a proper ring colouring and has the same θ-transitions as κ **[derived]**: an edge's two
ends are shifted by different amounts only if the edge is an endpoint of an odd number of chosen
chords, hence a θ-transition, and XOR θ on one end of a transition keeps it proper and a
transition.

  Reach(κ, θ, M) = { canon(κ^S) : S ⊆ M }  (2^m flips; S = ∅ gives κ itself).

**What this models.** Take any plane graph G′ that has the ring as a facial cycle, and any
4-colouring φ₀ of G′ that is κ on the ring [NL §2.1]. The Kempe chains of the split θ (the
components of the subgraphs of G′ induced by colours {0, θ} and by the other two colours) meet the
ring in blocks that are mutually non-crossing (the planarity fact quoted in [NL §2.1, "Computer
check of D-reducibility"]). Every such family of blocks is a refinement of the family that some
M ∈ 𝓜(2m) determines (§4.6), and the Kempe changes of [NL §2.1] with split θ then change the ring
colouring exactly into the members of Reach(κ, θ, M) (up to a global XOR θ, which canon removes).
A finer family only allows more changes, so quantifying over 𝓜(2m) is the worst case. §4.6 states
the equivalent block form used by [NL Alg. 3].

### 4.4 Rounds (normative)

E_0 is defined in §3. For k = 1, 2, 3, …:

  E_k = E_{k−1} ∪ { κ ∈ C* ∖ E_{k−1} : there is θ ∈ {1, 2, 3} such that for **every**
  M ∈ 𝓜(2m(κ, θ)), Reach(κ, θ, M) ∩ E_{k−1} ≠ ∅ }.

`added_k` = |E_k ∖ E_{k−1}|. The iteration stops at the first k ≥ 1 with added_k = 0, or as soon
as E_k = C*.

- The rounds are **simultaneous** (Jacobi): the test in round k uses E_{k−1} only, never
  colourings added earlier in the same round. The processing order inside a round must not affect
  anything. This is the paper's definition of i-extendible and of the reducibility level
  [NL §2.1]; it is **not** the in-place update of [NL Alg. 1, line 25] (see §11 R2).
- A colouring with m(κ, θ) = 0 for some θ gets nothing from that θ: 𝓜(0) = {∅}, Reach = {κ}, and
  κ ∉ E_{k−1}.
- The **level** of κ is the k with κ ∈ E_k ∖ E_{k−1} (0 for colourings in E_0) [NL §2.1,
  "reducibility level"]. Colourings in no E_k are **unresolved**.

Equivalently (for readers of RSST): the unresolved set is the largest set B ⊆ C* ∖ E_0 such that
for every κ ∈ B and every θ there is an M with Reach(κ, θ, M) ⊆ B — RSST's "consistent" set
(from memory, §11 R6). The iteration computes it from above.

### 4.5 What is allowed and what is not

Any algorithm that computes exactly the sets E_k of §4.4 is allowed. Ideas that are correct and
do not change any output:

- **Monotone witness pointer.** For fixed (κ, θ), check the matchings of 𝓜(2m) in a fixed order.
  Once a matching M has been found to meet E_{k−1}, it meets every later E_j, so a later round can
  resume the search at the first matching that failed before.
- **Grouping** colourings by θ and transition set T, and precomputing per M which classes of
  flips meet E_{k−1}.
- Storing E_k on labelled or translation-normalised colourings rather than canonical ones, if
  lookups then go through the orbit correctly.

Not allowed: updating E during a round (Gauss–Seidel), skipping a θ, using one θ for all
colourings instead of choosing it per colouring, or testing only some matchings.

### 4.6 The equivalent block form (normative for Implementation B, §10)

For κ, θ with m ≥ 1, the **runs** are the 2m maximal arcs of the ring between consecutive
θ-transitions: run j (j = 0, …, 2m−1) is the positions t_j + 1, …, t_{j+1} (mod R, with
t_{2m} = t_0 + R). All positions of a run lie in the same pair of the split, and the pairs
alternate with j. For M ∈ 𝓜(2m), chord (a, b) **separates** runs j and j′ iff exactly one of j, j′
lies in {a, a+1, …, b−1}. Runs j and j′ are in the same **block** of M iff no chord of M separates
them. Every block consists of runs of one parity (P-blocks: even j; Q-blocks: odd j), there are
m + 1 blocks, and the P-blocks and Q-blocks form two mutually non-crossing partitions (each the
other's Kreweras complement) **[derived]**.

For a set of blocks, XOR θ on all positions of all runs in them. Up to one global XOR θ, the
colourings so obtained are exactly {κ^S : S ⊆ M} **[derived]**, so

  Reach(κ, θ, M) = { canon(κ XOR θ on the union of β) : β a set of blocks of M }.

**[spec-check]**: the whole iteration was recomputed by brute force on labelled colourings,
quantifying over **all** pairs of mutually non-crossing partitions of the runs (not only the
complementary pairs from matchings) and flipping arbitrary sets of blocks. On deg3, deg4, W5, W6
and D0000–D0003 it gives the same per-round orbit counts as §4.4 (labelled counts are the orbit
counts weighted by orbit size; for D0000: 732 labelled colourings, 384 extend, labelled additions
108, 48, 96, 72, 24).

---

## 5. D-reducibility and the per-configuration record

### 5.1 Definition

A configuration is **D-reducible** iff the iteration of §4.4 ends with E_k = C* [NL §2.1:
"D_i-reducible if every 4-coloring of its ring is i-extendible, and D-reducible means
D_i-reducible for some finite i"; RSST's D-reducibility is the same notion, §11 R1].

### 5.2 The record

For every configuration the checker reports:

| Key | Meaning |
| --- | --- |
| `config` | the id: `D0000`…`D8199`, `deg3`, `deg4`; for the contrast class §6.6; for controls §8 |
| `R` | ring size |
| `vertices` | number of configuration vertices |
| `colourings` | N_R, the number of colourings in C* |
| `direct` | the number of colourings in E_0 |
| `added` | the list [added_1, …, added_r] of the rounds with added_k > 0, in order (the final round that adds nothing is **not** listed) |
| `rounds` | r = length of `added` (0 if no round adds anything) |
| `unresolved` | colourings − direct − Σ added |
| `D_reducible` | `true` iff unresolved = 0 |
| `levels_sha256` | SHA-256 (lowercase hex) of the byte string with one byte per colouring of C* in the order of §2.2: its level (0…254), or 255 if unresolved |

If any level would exceed 254, stop with an error (none is expected; [NL Lemma 3.2 (D3)] says 25
suffices for 𝒟).

For a D-reducible configuration, `rounds` is the maximum level, i.e. the least i with the
configuration D_i-reducible [NL §2.1]. For a configuration that is not D-reducible, `rounds` is the
number of productive rounds before the iteration stalled.

### 5.3 Invariance

`colourings`, `direct`, `added`, `rounds`, `unresolved` and `D_reducible` do not depend on the ring
labelling: rotating or reflecting the ring maps C* to itself (after canon), preserves properness,
extension, transitions, non-crossing matchings and flips **[derived]**. They are therefore
invariants of the configuration up to isomorphism and reflection, i.e. of its `shape`.
`levels_sha256` does depend on the labelling, which §1.3 and §6.4 fix.

---

## 6. The contrast class: one-vertex deletions

### 6.1 Candidates

For every in-scope configuration K (§1.1, in CSV order) and every configuration vertex v of K (in
increasing file label), the **candidate** K − v is the configuration Z′ = Z ∖ {v} with the degree
function δ restricted to Z′ (degrees in the triangulation are unchanged). There are 60,286
candidates **[spec-check]** (the sum of `vertices` over the 5,897).

### 6.2 Validity, in this order (the first failing test names the reason)

A configuration must be a near-triangulation with a degree function satisfying (Z1)–(Z3) of
[NL §2.1]; (Z1) and (Z2) hold automatically for Z′ once Z′ is a near-triangulation. The tests:

1. `empty`: Z has one vertex (deg3, deg4).
2. `interior`: v has no ring neighbour in K. (Deleting an inner vertex leaves a non-triangular inner
   face, so Z′ is not a near-triangulation.)
3. `disconnected`: the graph Z′ (configuration vertices of K except v, with the edges of K between
   them) is not connected.
4. `cut_vertices`: Z′ has two or more cut vertices ([NL §2.1 (Z3)]: "We only allow one
   cut-vertex"). A cut vertex is a vertex whose removal disconnects Z′; a graph with at most two
   vertices has none.
5. `cut_vertex_z3`: Z′ has exactly one cut vertex u, and either Z′ − u does not have exactly two
   components (u is not in exactly two blocks), or δ(u) − d_{Z′}(u) ≠ 2 [NL §2.1 (Z3)].
6. `completion`: the construction of §6.3 fails one of its checks, or `build.validate` rejects the
   result of §6.4. (Expected: never **[spec-check]**.)
7. `in_D`: the `shape` of K − v (§6.5) equals the `shape` of one of the 8,202 rows of
   `configurations.csv` (all of 𝒟, not only the in-scope part).
8. `duplicate`: the `shape` equals that of an earlier **accepted** candidate (earlier in the
   order of §6.1).
9. Otherwise the candidate is **accepted**: it is a member of the contrast class.

Expected counts **[spec-check]**:

| empty | interior | disconnected | cut_vertices | cut_vertex_z3 | completion | in_D | duplicate | accepted | total |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 3,259 | 1,213 | 19,133 | 10,893 | 0 | 7 | 4,607 | 21,172 | 60,286 |

### 6.3 The free completion of K − v (normative)

Work with K's file labels. For each u ∈ Z′ and each index i = 0, …, δ(u)−1 of u's neighbour list
rot_u (as in the file), the **slot** (u, i) is **outer** iff rot_u[i] ∉ Z′ (a ring vertex of K, or
v). The new ring vertices are classes of outer slots:

1. **Identify.** For every outer slot (u, i) such that b = rot_u[(i+1) mod δ(u)] ∈ Z′, identify
   (u, i) with (b, j), where j = (index of u in rot_b + 1) mod δ(b). Check that (b, j) is outer.
   (Slot (u, i) holds the outer vertex x of the triangular face u, x, b: around u, b comes right
   after x, and then, by the file's orientation convention, x comes right after u around b.)
   Take the equivalence classes generated (union–find). Each class is one new ring vertex.
2. **Check** that no class contains two slots of the same vertex (else the completion would have a
   multiple edge).
3. **Successor.** For every outer slot (u, i) such that (u, (i+1) mod δ(u)) is also outer, set
   succ(class(u, i)) = class(u, i+1). Check that this never assigns two different successors to
   one class, that succ is defined on every class, that it is a bijection, and that following
   succ from any class visits every class once before returning (one cycle).
4. **Size.** R′ = number of classes. Check R′ = (number of outer slots) − (number of identifying
   pairs in step 1); this is the formula |R| = Σδ − 2|E(Z′)| − t′ of [NL §2.1] with t′ the number
   of identifying pairs **[derived]**. Check R′ ≥ 3.

**Mandatory self-check of the construction on the data.** Apply steps 1–4 to every file with
Z′ = Z (no deletion; outer slots are then exactly the slots holding ring vertices). It must
reproduce the file's ring: R′ = R, every class is exactly the set of slots holding one ring vertex
r, and the map r ↦ (label of its class, per §6.4) is a rotation r ↦ ((r − 1 + s) mod R) + 1 for
some s (same direction). **[spec-check]**: holds for all 8,202 (deg3 and deg4 included), and
formula 4 holds for all 8,202 and all 21,172 accepted deletions.

### 6.4 The file form and ring labelling of K − v (normative)

- **Ring labels.** Label 1 is the class of the lexicographically least outer slot (u, i) (u by K's
  file label, then i). Label k + 1 is succ(label k), for k = 1, …, R′ − 1.
- **Configuration labels.** The vertices of Z′ in increasing K label get R′ + 1, …, R′ + |Z′|.
- **Neighbour lists.** The list of u keeps K's list rot_u, same starting index and order, with
  each entry replaced by its new label: a Z′ vertex by its configuration label, an outer slot
  (u, i) by the label of its class.

The result is a configuration in the file format of §1.2 with N′ = R′ + |Z′|. Run
`build.validate` on it (reason `completion` if it fails; expected never). Its ring labelling is the
one used for the colouring order of §2.2 and for `levels_sha256`.

### 6.5 Shape, and "not in 𝒟"

`shape(K − v)` is `build.row(cfg)["shape"]` of `search/index/build.py` applied to the file form of
§6.4, i.e. the first 16 hex digits of the SHA-256 of the canonical breadth-first code up to
isomorphism **and reflection** [idx: docstring "The shape"]. It does not depend on the labelling.
Two configurations are the same iff their shapes are equal (checked for 𝒟 by
`search/index/crosscheck.py` [idx README]). A configuration and its mirror image count as the same
configuration: 𝒟 lists each configuration once up to reflection [idx README], and D-reducibility is
invariant under reflection (§5.3).

"Not in 𝒟" means: the shape is not among the 8,202 `shape` values of `configurations.csv`.

### 6.6 Identity, order and size of the contrast class

- Id: `<parent>-v<label>`, e.g. `D0002-v13` (parent id, and the deleted vertex's label in the
  parent's file).
- Order: the order in which candidates are accepted (§6.1 order).
- The representative of a shape is the first accepted candidate with that shape; later candidates
  with the same shape are `duplicate`.

Accepted, by ring size R′ **[spec-check]** (the "with cut vertex" row counts members whose Z′ has
its one allowed cut vertex):

| R′ | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| members | 1 | 1 | 7 | 22 | 96 | 408 | 1,650 | 5,332 | 10,066 | 3,484 | 105 | 21,172 |
| with cut vertex | 0 | 0 | 2 | 7 | 32 | 132 | 527 | 1,665 | 3,171 | 1,411 | 59 | 7,006 |

**[spec-check]** Deletions of the 2,305 configurations with R = 15–18 give 11,555 further shapes,
**all** with R′ ≥ 15. So the part of the contrast class with R′ ≤ 14 (17,583 members) is the same
whether the parents are the in-scope configurations or all of 𝒟.

The first three members are `D0000-v7` (R′ 6, 3 vertices), `D0001-v8` (R′ 7, 3 vertices) and
`D0002-v13` (R′ 8, 6 vertices, with a cut vertex) **[spec-check]**. `D0004-v9` is the diamond of
§8 control C7 (same shape) **[spec-check]**.

### 6.7 Tiers

The contrast class is checked in tiers by ring size, because its cost is dominated by R′ = 14
(§9):

| Tier | Members | Status in Phase 1 |
| --- | --- | --- |
| X12 | R′ ≤ 12: 2,185 | run (stage 1 of §9.4) |
| X13 | R′ = 13: 5,332 | run only if the calibrated projection fits (stage 3 of §9.4) |
| X14 | R′ = 14: 10,066 | **not run without Gabriel's go** (§12 Q2) |
| X15+ | R′ ≥ 15: 3,589 | deferred with 𝒟's ring sizes 15–18 |

Every member of every tier is listed in `contrast.jsonl` (§7.2) whether or not its tier is run.

---

## 7. Output files (byte-comparable)

### 7.1 General rules

- Directory: `search/b2/implA/results/` for A, `search/b2/implB/results/` for B.
- All compared files are ASCII, lines end with `\n` only (write in binary mode or with
  `newline="\n"`; Windows must not produce `\r\n`), and every file ends with `\n`.
- **JSONL files**: one object per line, written with `json.dumps(obj, ensure_ascii=True)` —
  default separators `", "` and `": "`, **no** `sort_keys`, keys in exactly the order given below,
  integers as JSON integers, booleans as `true`/`false`.
- **JSON files** (`count.json`, `summary.json`): `json.dumps(obj, sort_keys=True, indent=1,
  ensure_ascii=True) + "\n"`. Maps keyed by a number (ring sizes, histograms) use the decimal
  string as key and omit keys whose entry would be zero or empty. Fields with fixed names are
  always present, zeros included.
- No timestamps, paths, implementation names, versions or timings in compared files; those go to
  `run.json`.
- Parallelism and sharding must not change any compared byte: collect, then write in the defined
  order.

### 7.2 The files

| File | Compared | Content |
| --- | --- | --- |
| `count.json` | yes | the count-only pass (§9.2) |
| `controls.jsonl` | yes | one record (§5.2) per control of §8.1, in the order of the table there |
| `D13.jsonl` | yes | one record per in-scope configuration of 𝒟 with R ≤ 13, in CSV order (D0000…D8199, then deg3, deg4, filtered): 3,098 lines |
| `D14.jsonl` | yes, when run | the same for R = 14: 2,799 lines |
| `contrast.jsonl` | yes | one line per accepted deletion, in §6.6 order: 21,172 lines |
| `X12.jsonl`, `X13.jsonl`, `X14.jsonl` | yes, for each tier run | one record per member of the tier, in §6.6 order |
| `summary.json` | yes | aggregates and digests (below) |
| `run.json` | **no** | implementation, command, git commit (or `"unknown"`), machine (CPU model, logical CPUs, OS, Python version), worker count, wall and CPU seconds per tier and per ring size, calibration timings and projection (§9.4), peak RSS per worker and in total, start and end times in UTC |

The record files are split by tier (§9.4) so that each is complete and comparable on its own,
whichever tiers have been run.

**Record line** (`controls.jsonl`, `D13.jsonl`, `D14.jsonl`, `X*.jsonl`), keys in this order:

    {"config": "D0000", "R": 6, "vertices": 4, "colourings": 31, "direct": 16, "added": [5, 2, 4, 3, 1], "rounds": 5, "unresolved": 0, "D_reducible": true, "levels_sha256": "c99eff27ac006884bc1c40a1df7f5429e72c1e681f0c783eb5474ab7af353477"}

(This line is the expected D0000 record **[spec-check]**.)

**`contrast.jsonl` line**, keys in this order: `config`, `parent`, `deleted`, `deleted_degree`,
`R`, `vertices`, `cut_vertex`, `shape`.

`deleted_degree` is δ(v) in the parent; `cut_vertex` is whether Z′ has a cut vertex; `R` is R′.
The first three lines of `contrast.jsonl` must be **[spec-check]**:

    {"config": "D0000-v7", "parent": "D0000", "deleted": 7, "deleted_degree": 5, "R": 6, "vertices": 3, "cut_vertex": false, "shape": "b6e0ac580ae82e33"}
    {"config": "D0001-v8", "parent": "D0001", "deleted": 8, "deleted_degree": 5, "R": 7, "vertices": 3, "cut_vertex": false, "shape": "e60688686ebfe179"}
    {"config": "D0002-v13", "parent": "D0002", "deleted": 13, "deleted_degree": 5, "R": 8, "vertices": 6, "cut_vertex": true, "shape": "fb94f2216196c44a"}

**`count.json`** — keys:

- `"D"`: `{"<R>": {"configs": n, "colourings": Σ N_R}}` over the in-scope configurations;
- `"deletions"`: `{"candidates", "empty", "interior", "disconnected", "cut_vertices",
  "cut_vertex_z3", "completion", "in_D", "duplicate", "accepted"}`;
- `"contrast"`: `{"<R′>": {"members": n, "cut_vertex": n, "colourings": Σ N_R′}}`;
- `"tiers"`: `{"D13": {"configs": 3098, "colourings": 153482393}, "D14": {"configs": 2799,
  "colourings": 557815509}, "X12": {"configs": 2185, "colourings": 39805384}, "X13": {"configs":
  5332, "colourings": 354204760}, "X14": {"configs": 10066, "colourings": 2006063206}, "X15+":
  {"configs": 3589, "colourings": 2271312034}}` **[spec-check]**.

**`summary.json`** — for each compared JSONL file that was written, under its file name:
`{"lines": n, "sha256": "<hex of the file's bytes>"}`; and for each record file (`D13.jsonl`,
`D14.jsonl`, `X*.jsonl`) also `"by_R": {"<R>": {"configs", "D_reducible", "not_D_reducible", "max_rounds",
"rounds": {"<r>": count}, "colourings", "direct", "unresolved"}}` (sums over the configurations of
that ring size; `rounds` is the histogram of the `rounds` field). `summary.json` also records
`"controls_pass": true|false` and `"self_checks_pass": true|false` (§8).

The SHA-256 of each record file run (`D13.jsonl`, `D14.jsonl`, `X*.jsonl`) and of
`contrast.jsonl` are the numbers to report and compare.

---

## 8. Controls, with expected values

All controls run first, in both implementations, before the main pass. A failed control stops the
run; nothing after it is reported as a result.

### 8.1 Record controls (`controls.jsonl`)

Configurations not in the data are given here in the file format of §1.2 (the text between the
fences is the whole file, line 1 empty). Expected records are **[spec-check]**.

| # | config | What | Source of the expectation |
| --- | --- | --- | --- |
| C1 | `deg3` | single vertex of degree 3 | [NL Lemma 2.1]: 0-extendible |
| C2 | `deg4` | single vertex of degree 4 | [NL Lemma 2.1]: 1-extendible, not 0 |
| C3 | `W5` | single vertex of degree 5: file `\n6 5\n6 5 1 2 3 4 5\n` | must **not** be D-reducible (issue #48; were it D-reducible, every triangulation would contain one and the 4CT would follow by induction) |
| C4 | `W6` | single vertex of degree 6: `\n7 6\n7 6 1 2 3 4 5 6\n` | not D-reducible [spec-check] |
| C5 | `W7` | single vertex of degree 7: `\n8 7\n8 7 1 2 3 4 5 6 7\n` | not D-reducible [spec-check] |
| C6 | `D0000` | the Birkhoff diamond | [NL §2.1, Fig. 3(a)]: D-reducible (Birkhoff) |
| C7 | `DIA56` | the diamond with its two middle vertices raised to degree 6 (below) | [NL §2.1, Fig. 3(b)] presents it as C-reducible; not D-reducible [spec-check] |
| C8 | `FRANKLIN` | a degree-6 vertex surrounded by six degree-6 vertices (below) | [NL §2.1, Fig. 3(c)] presents it as C-reducible (Franklin); not D-reducible [spec-check] |
| C9 | `D0001` | ring 7 | in 𝒟: D-reducible |
| C10 | `D0002` | ring 8 | in 𝒟 |
| C11 | `D0003` | ring 8 | in 𝒟 |

D0000 **is** the Birkhoff diamond: ring 6, four vertices of degree 5, edges 7–8, 7–10, 8–9, 8–10,
9–10, i.e. the triangles 7-8-10 and 8-9-10 sharing the edge 8–10; the tips 7 and 9 have three
ring neighbours each (3, 4, 5 and 1, 2, 6), the middle vertices 8 and 10 two each
**[spec-check, from the file]**.

`DIA56` (D0000 with vertices 8 and 10 given degree 6; shape `2b88eaf2026a6952`, the shape of the
contrast member `D0004-v9`):

```

12 8
9 5 1 2 12 10 8
10 6 8 9 12 11 6 7
11 5 6 10 12 4 5
12 6 4 11 10 9 2 3
```

`FRANKLIN` (shape `dfdeb876adbd3ec9`):

```

19 12
13 6 14 15 16 17 18 19
14 6 13 19 1 2 3 15
15 6 13 14 3 4 5 16
16 6 13 15 5 6 7 17
17 6 13 16 7 8 9 18
18 6 13 17 9 10 11 19
19 6 13 18 11 12 1 14
```

Both pass `build.validate` **[spec-check]**. Neither shape is in `configurations.csv`.

Expected `controls.jsonl`, exactly (11 lines) **[spec-check]**:

```
{"config": "deg3", "R": 3, "vertices": 1, "colourings": 1, "direct": 1, "added": [], "rounds": 0, "unresolved": 0, "D_reducible": true, "levels_sha256": "6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d"}
{"config": "deg4", "R": 4, "vertices": 1, "colourings": 4, "direct": 3, "added": [1], "rounds": 1, "unresolved": 0, "D_reducible": true, "levels_sha256": "b40711a88c7039756fb8a73827eabe2c0fe5a0346ca7e0a104adc0fc764f528d"}
{"config": "W5", "R": 5, "vertices": 1, "colourings": 10, "direct": 5, "added": [], "rounds": 0, "unresolved": 5, "D_reducible": false, "levels_sha256": "b0fbb814a0f8ca0bd8a2e20bea3702e641604a76f6ee99c93410f47e73a92d60"}
{"config": "W6", "R": 6, "vertices": 1, "colourings": 31, "direct": 11, "added": [], "rounds": 0, "unresolved": 20, "D_reducible": false, "levels_sha256": "ac04031b3f9b98101b60b18b245f087d6ecf0981783221709952fe64effd73ab"}
{"config": "W7", "R": 7, "vertices": 1, "colourings": 91, "direct": 21, "added": [], "rounds": 0, "unresolved": 70, "D_reducible": false, "levels_sha256": "92a2787da9db119bf8a33001d90499b5fb7ed8aa48590c42ec71e2a5cf5efdaa"}
{"config": "D0000", "R": 6, "vertices": 4, "colourings": 31, "direct": 16, "added": [5, 2, 4, 3, 1], "rounds": 5, "unresolved": 0, "D_reducible": true, "levels_sha256": "c99eff27ac006884bc1c40a1df7f5429e72c1e681f0c783eb5474ab7af353477"}
{"config": "DIA56", "R": 8, "vertices": 4, "colourings": 274, "direct": 81, "added": [15, 8, 6, 7, 3], "rounds": 5, "unresolved": 154, "D_reducible": false, "levels_sha256": "20e422d59da004cbd1cfab8e5509233d46dfe5ec2f76aac616d6c4cba335b5af"}
{"config": "FRANKLIN", "R": 12, "vertices": 7, "colourings": 22144, "direct": 2756, "added": [4164, 705, 330, 98, 30], "rounds": 5, "unresolved": 14061, "D_reducible": false, "levels_sha256": "99cf48949816f9ddc8e14e0a9456062780ab314af9099a9bbb59a4999d266a53"}
{"config": "D0001", "R": 7, "vertices": 4, "colourings": 91, "direct": 39, "added": [7, 6, 9, 12, 11, 7], "rounds": 6, "unresolved": 0, "D_reducible": true, "levels_sha256": "ef1dea829d7334df04300ba490d99cf21f4f460f6e5181b25e6661d9e4a2c410"}
{"config": "D0002", "R": 8, "vertices": 7, "colourings": 274, "direct": 111, "added": [37, 38, 19, 11, 22, 26, 10], "rounds": 7, "unresolved": 0, "D_reducible": true, "levels_sha256": "9240e7ead287f46f2a3cb2a39879b75b9c2f1b174e3e5c9b4972f15521813f47"}
{"config": "D0003", "R": 8, "vertices": 5, "colourings": 274, "direct": 100, "added": [34, 28, 18, 34, 35, 21, 4], "rounds": 7, "unresolved": 0, "D_reducible": true, "levels_sha256": "c2c72a880dbe424e380b6c5d02db7dd1ba92ebb3b310c079574504917c66f9f6"}
```

Hand-checkable detail, for debugging:

- deg4: C* = 0101, 0102, 0121, 0123 with levels 0, 0, 0, 1. The three colourings with at most
  three colours extend; 0123 needs one Kempe change, which is [NL Lemma 2.1]'s proof.
- W5: C* in order 01012, 01021, 01023, 01201, 01202, 01203, 01212, 01213, 01231, 01232; the five
  using three colours extend, the five using all four are unresolved.
- D0000 levels, in C* order: 010101:1 010102:0 010121:0 010123:1 010201:1 010202:0 010203:2
  010212:0 010213:3 010231:0 010232:0 012012:5 012013:4 012021:0 012023:0 012031:0 012032:4
  012101:0 012102:0 012103:0 012121:1 012123:0 012131:2 012132:3 012301:0 012302:3 012303:1
  012312:4 012313:3 012321:0 012323:0.

These round counts are from the spec author's script and from the brute force of §4.6, not from
the literature: no published per-round counts for these configurations were found. The literature
gives only C1 and C2's levels [NL Lemma 2.1], and that C6 is D-reducible.

### 8.2 Anti-vacuity

C3, C4, C5, C7 and C8 must come out **not** D-reducible, and C1, C2, C6, C9–C11 D-reducible.
Together they catch the usual quantifier errors **[spec-check]**, on the spec author's script with
the error deliberately introduced:

- "some matching" instead of "every matching": W5, W6 and DIA56 all become D-reducible;
- one split θ instead of three: D0000 and D0003 stop being D-reducible.

In addition, each implementation must run once with its extension test replaced by "never
extends" (E_0 = ∅) on C1–C11 and confirm that every one of them is then not D-reducible with
`direct` 0 (report this in `run.json`, not in compared files).

### 8.3 Self-checks (both implementations; failures stop the run)

- **S1 counts.** For R = 3..14, the enumerated |C*| equals the formula of §2.3; for R = 3..10, a
  brute force over all 4^R sequences finds 3^R + 3(−1)^R proper colourings and exactly N_R distinct
  canon values.
- **S2 completion.** §6.3's self-check on all 8,202 configurations.
- **S3 relabelling.** For D0000–D0003, deg4 and the first three R = 12 configurations in CSV order,
  rebuild the configuration with its ring rotated by one position and, separately, reflected
  (ring label i ↦ R + 1 − i, every neighbour list reversed), run `build.validate`, and check that
  every field of the record except `levels_sha256` is unchanged.
- **S4 block form = chord form.** On every in-scope configuration with R ≤ 8 and on C3–C5, C7,
  compute the iteration a second way — A with the block form of §4.6, B with the chord form of
  §4.3 — and check equal records. (This is a small in-implementation cross-check; the main
  independence is A against B.)
- **S5 contrast bookkeeping.** `count.json` equals the numbers of §6.2 and §6.6 and §1.1.
- **S6 D3.** Every record in `D13.jsonl` and `D14.jsonl` has `D_reducible` true and `rounds` ≤ 25
  [NL Lemma 3.2 (D1)–(D3)]. A violation is **not** a bug to be fixed: stop, keep the output, and
  report it (it would be a finding about 𝒟 or about this spec's reading, §11 R2).
- **S7 DIA56 = D0004-v9.** The X-record of `D0004-v9` (tier X12) has the same fields as the C7
  record except `config` and `levels_sha256`.
- **S8 𝒟 satisfies (Z3).** Every one of the 8,202 has at most one cut vertex, and the cut vertex,
  if any, lies in exactly two blocks with δ − d_Z = 2 (the tests of §6.2 applied to Z itself).
  **[spec-check]**: holds; 1,677 of the 8,202 have a cut vertex.

---

## 9. Cost, the count-only pass, and the run plan

### 9.1 What grows

Per configuration the work is dominated by the Kempe rounds on the unresolved colourings. N_R
grows by a factor of about 3 per unit of R (§2.3), a θ-test on a colouring with 2m transitions
touches up to Cat(m) matchings with up to 2^m flips each. In the sampled configurations of 𝒟 with
R ≥ 10, only 10–25 % of the colourings extend directly, so most colourings go through several
rounds. Measured rounds in 𝒟 (samples, R = 10–14): 6–16; contrast members that are not D-reducible stall after up to 37
productive rounds.

### 9.2 Count-only pass (run first; writes `count.json`)

No colouring work: parse and validate all 8,202; list the in-scope configurations with R and N_R;
enumerate the candidates of §6.1 and classify them (§6.2–§6.5, including the completion and
shapes); tally the tiers. It must reproduce §1.1, §2.3 (Σ N_R = 711,297,902) and §6.2/§6.6
exactly (self-check S5). Expected time: under a minute to a few minutes. It computes about 25,800
canonical codes with `build.py`, one for each candidate that reaches test 7. The spec author's
enumeration took 31 s.

Σ N over the contrast tiers **[spec-check]**: X12 39,805,384; X13 354,204,760; X14 2,006,063,206.

### 9.3 Measured cost of a reference script (not an implementation)

The spec author's throwaway script: pure CPython 3.12, chord form with a byte table indexed by
translation-normalised colourings (4^(R−1) bytes, 67 MB at R = 14) and the monotone witness
pointer of §4.5. Measured on the 20-logical-CPU Windows host that also runs the WSL machine, so
the WSL numbers should be of the same order but are not measured. Seconds per configuration:

| Part | Configs | Solo: s per config (samples) | Under load, 16 processes: s per config (samples) | Wall hours per implementation, 16 workers |
| --- | ---: | --- | --- | ---: |
| 𝒟, R ≤ 11 | 296 | ≤ 0.7 | — | < 0.05 |
| 𝒟, R = 12 | 779 | 1.5–3.3 (3) | ≈ 8 (scaled, not measured) | ≈ 0.1 |
| 𝒟, R = 13 | 2,025 | 8.6–12.4 (3) | mean 32 (16) | ≈ 1.1 |
| 𝒟, R = 14 | 2,799 | 28–53 (9) | mean 172, range 101–273 (32; wall 385 s for all 32) | ≈ 8.5–9.5 |
| X12 (R′ ≤ 12) | 2,185 | ≤ 6.3; ≈ 4 at R′ = 12 (4) | ≈ 20 (scaled) | ≈ 0.6 |
| X13 | 5,332 | 9–37 (7) | mean 74 (16) | ≈ 7 |
| X14 | 10,066 | 37–107 (4) | mean 248 (19) | ≈ 43 |

**[spec-check]**, all of it, with these caveats:

- **Parallel efficiency is poor.** The host is an Intel i9-13900H (6 performance and 8 efficiency
  cores, 20 threads, laptop power limits). 16 processes delivered about **3 times** the
  throughput of one process running alone, not 16 times. The last column uses the loaded
  numbers.
- Samples are small (3 to 32 configurations per row), spread evenly over the CSV or §6.6 order.
- The R = 13 and X rows were measured without the witness pointer, which saves about 10 %.
- Memory: about 200 MB per worker at R = 14 with the 67 MB table; 16 workers stay near 3.5 GB.

**Consequence.** At the reference script's speed, 𝒟 alone costs about 10–11 runner-hours **per
implementation**, so about 21 for A and B. That is twice the 10-hour cap. 𝒟 with R ≤ 13 and X12 cost
about 1.9 runner-hours per implementation (3.8 for both). X13 costs about 7 per implementation,
and X14 about 43. An implementation can be faster than the reference script (§4.5 lists correct
shortcuts), but nobody has measured one. So the plan below runs the cheap part first and makes
everything else conditional on a calibrated projection.

### 9.4 Run plan and budget

**Runner-hours** are wall-clock hours during which any Phase 1 job of either implementation runs
on the WSL machine; reruns and failed runs count; parallel workers do not multiply them. CPU-hours
are reported alongside. **Cap: 10 runner-hours for Phase 1, A and B together; stop and ask at 8.**
Keep a ledger (per run: wall and CPU hours, what was run) in each implementation's README; the main
session sums both.

**Stages** (A and B each; the budget column is for both together, at the reference speed of §9.3):

| Stage | Work | Output | Estimated runner-hours, A + B | Condition |
| --- | --- | --- | ---: | --- |
| 0 | controls (§8), self-checks, count-only pass | `controls.jsonl`, `count.json`, `contrast.jsonl` | < 0.2 | always |
| 1 | 𝒟 with R ≤ 13; contrast tier X12 | `D13.jsonl`, `X12.jsonl` | ≈ 3.8 | always |
| 2 | 𝒟 with R = 14 | `D14.jsonl` | ≈ 17–19 at reference speed | only if the calibrated projection for **both** implementations keeps the ledger under 8 hours; otherwise stop and ask (§12 Q1) |
| 3 | contrast tier X13 | `X13.jsonl` | ≈ 14 at reference speed | same condition, after stage 2 |
| — | contrast tier X14; everything with R or R′ ≥ 15 | — | ≈ 86 (X14) | not in Phase 1 without Gabriel's go (§12 Q2) |

After stage 1 both implementations stop. The main session compares their outputs and sums the
ledger. Stage 2 then starts only under its condition, or after Gabriel's answer to Q1.

Each run:

1. runs the controls (§8) and the count-only pass (§9.2);
2. **calibrates**: runs the full check on the first 4 configurations of each (tier, ring size)
   with R ≥ 12 in that tier's order, under the same worker count as the main pass, and logs
   seconds per configuration;
3. projects the main pass's wall time (Σ over ring sizes of count × mean seconds ÷ workers) and
   logs it in `run.json`;
4. starts the main pass only if the projection keeps the cumulative ledger (both implementations)
   under 8 runner-hours and the run under 4 hours; otherwise it stops and reports the projection.

A single run may not exceed 4 hours: split work by tier and ring size, and assemble the compared
files in the defined order at the end (partial per-R files are not compared). Memory: the total
over all workers must stay under 8 GB; measure the per-worker peak at R = 14 in calibration and
choose the worker count accordingly.

**Language.** Python 3 (CPython ≥ 3.10), standard library only, is the default and what §9.3
measures. Using anything else (PyPy, or a C kernel compiled with the system `cc`, as B1 compiles
plantri) needs Gabriel's approval: §12 Q1.

---

## 10. Independence rules and division of labour

### 10.1 What each implementer may read

Only:

- this file, `search/b2/SPEC.md`;
- `data/near-linear-4ct/reducible-configurations/` (the `D/*.conf` files, `README.md`, `LICENSE`);
- `search/index/` (`build.py`, `configurations.csv`, `README.md`, `crosscheck.py`);
- `CLAUDE.md`;
- your own directory (`search/b2/implA/` or `search/b2/implB/`), and the Python documentation.

`search/index/build.py` may be **imported** for `parse`, `validate`, `single_vertex`, `load_all`
and `row` (for `shape`). This is a declared common dependency: `shape` is the repository's
definition of "same configuration", already cross-checked by `crosscheck.py`. Everything else —
the completion of deletions (§6.3–§6.4), the validity tests, ring colourings, extension, the Kempe
rounds and the output — each implementation writes itself.

### 10.2 What nobody reads (Gabriel's decision 3, 2026-09-30)

- the other implementation (A never reads `implB/`, B never reads `implA/`), and the spec author's
  scratch scripts (not in the repository);
- **any existing reducibility implementation**: the near-linear repositories' code
  (`near-linear-4ct/computer-checks`, and the reducibility checker the paper links in App. A.1,
  `github.com/edge-coloring/reducibility_checker`), anything under `third_party/`, the Lean ports
  in `lean/FourColor/` (corun1024) and `third_party/RBarish-UTokyo/`, Gonthier et al.'s Coq/Rocq
  development (`math-comp/fourcolor`, `coq-community/fourcolor`), RSST's programs, and the
  unlicensed reimplementations listed at the end of `THIRD_PARTY_NOTICES.md`;
- anything else in this repository (`checks/`, `search/b1/`, `search/d1/`, `notes/`, …).

If you had to look at anything outside §10.1, say what and why in your README's independence log.
An implementation that quietly mirrors another is worth nothing as a cross-check (`CLAUDE.md`).

### 10.3 Division of labour (to make A and B differ where it is cheap)

| Part | Implementation A | Implementation B |
| --- | --- | --- |
| Kempe rounds (§4) | chord form §4.3 | block form §4.6 |
| S4 cross-check | block form | chord form |
| Extension (§3) | per canonical colouring: backtracking over the configuration's vertices | enumerate the proper colourings of the configuration's own vertices and collect the ring colourings each admits (or another method different from A's) |
| Deletion completion (§6.3) | as specified | as specified, written independently |

Both: all controls, all self-checks, all output files, `run.json`, a README with commands, the
ledger, digests and the independence log. Neither commits, pushes nor opens a pull request unless
the main session asks; the main session compares A and B (`search/b2/compare.py`, written after
both finish).

### 10.4 What counts as a result

Byte-identical `count.json`, `controls.jsonl`, `contrast.jsonl` and every record file run
(`D13.jsonl`, `D14.jsonl`, `X*.jsonl`), from A and B, with every control and self-check passing
and one command per implementation that reruns it from a clean checkout. Then:

- `D13.jsonl` and `D14.jsonl` are this repository's own check that the in-scope configurations of
  𝒟 (3,098 and 2,799) are D-reducible (or a finding if some are not), with their round statistics;
- the X files label the contrast class.

Anything interpretive (what predicts rounds, etc.) is Phase 2 and a lead until checked.

---

## 11. Readings of the sources

**R1. When is the colour split chosen?** [NL §2.1] defines i-extendible literally as: for every G′
and every φ₀ extending φ there is a Kempe change (switching on ab-chains, then on complementary
cd-chains) to an (i−1)-extendible colouring. Read literally, the split may depend on G′. [NL
Alg. 1] (lines 9–27) chooses the split (`colorPair`) first and then requires success for **every**
Kempe-chain structure (`AllKempeChains`); the paper says its program is "very similar to the one
from [26]" (RSST) and that its definition "is equivalent to that used in the original 4-coloring
theorem proof". This spec follows Alg. 1: ∃θ ∀M ∃S. It is the standard D-reducibility, and what 𝒟
was certified with. (The literal reading would need the joint realisability of the three splits'
chain structures, which Alg. 1 does not model.)

**R2. Rounds are simultaneous.** [NL §2.1] defines levels (i-extendible) inductively, so the set
of colourings of level ≤ i is E_i of §4.4; the "Computer check" paragraph describes rounds the same
way. [NL Alg. 1] as printed adds φ to 𝒞 immediately (line 25), so later colourings in the same
pass can use it: its passes can be fewer than the levels. The final closure, hence D-reducibility,
is the same either way; the round counts are not. The spec reports levels. [NL Lemma 3.2 (D3)]
("every 4-coloring … is 25-extendible") is a statement about levels; S6 tests it for R ≤ 14.

**R3. [NL Alg. 3] as printed.** At ')' it appends the top of the stack to L and then pops. Read
literally, each matched pair of parentheses gives two runs of opposite parity the same label,
which cannot be a Kempe chain, and the initial 0 on the stack is never used. Popping first and then
appending gives exactly the complementary non-crossing partitions of §4.6 (the 0 is the outer
region). The spec defines the structures directly (§4.2, §4.6), so nothing depends on this.

**R4. Complementary partitions suffice.** Chains in G′ can give finer families of blocks than the
complementary pairs; a finer family allows every change a coarser one allows, so the worst case
is a maximal (complementary) family, one per non-crossing matching. Checked by brute force on
small cases (§4.6).

**R5. Up to colour permutation.** [NL] iterates over labelled colourings; RSST (from memory)
normalise colourings. Orbits give the same sets (§2.2); counts in this spec are orbit counts.

**R6. RSST.** RSST's formulation — tri-colourings of the ring edges, signed matchings, "consistent"
sets, and D-reducible meaning the maximal consistent set disjoint from the extendible colourings is
empty — is recalled from memory, and the spec relies on it for nothing. The PDF was not downloaded
(§12 Q4). The spec's definitions rest on [NL §2.1, App. A.1] alone.

---

## 12. Questions for Gabriel

**Q1. Speed: Python only, or a compiled kernel?** At the reference script's measured speed (§9.3),
𝒟 with R = 14 costs about 8.5–9.5 runner-hours per implementation. That is about 17–19 for both,
against a 10-hour cap for all of Phase 1. Stage 1 (𝒟 with R ≤ 13, X12) fits: about 3.8 for both.
Options:

- (a) Allow the Kempe-round kernel in C, compiled at run time with the system `cc` (as B1 compiles
  plantri), with Python for everything else. This is not measured; typically it is 20–100 times
  faster, which would put all of 𝒟 and X13 well inside the cap.
- (b) Allow PyPy. Not measured, and it may not be installed in WSL.
- (c) Keep pure CPython. Run stage 1 now, and decide R = 14 after measuring the implementations'
  real speed; they may be faster than the reference script.
- (d) Raise the cap for R = 14.

The spec's default is (c): stage 1, then stop and ask with measured projections.

**Q2. The contrast tier with ring size 14.** Deletions with R′ = 14 number 10,066: 3.6 times 𝒟's
R = 14 count by colourings (2.0 × 10⁹ against 5.6 × 10⁸). At reference speed they cost about 86
runner-hours for both implementations. Options:

- run it only after Q1 (a);
- run a fixed sample, for example every 10th member in §6.6 order (1,007 members);
- defer it with ring sizes 15–18.

The default is to defer it. X12 (2,185 members) runs in stage 1 either way. X13 (5,332) runs only
if the projection allows.

This bears on Phase 2. **[spec-check]** None of the 536 members with R′ ≤ 11 is D-reducible, and
in the samples with R′ = 12–14 (about 60 members) only one was: `D7293-v24`, with R′ = 13. So
D-reducible deletions are rare, and a contrast class cut at R′ ≤ 12 may contain very few of them.
A class that is almost all "not D-reducible" still serves Phase 2's comparison of statistics
between 𝒟 and non-𝒟. It gives little to "predict D-reducibility" within the deletions.

**Q3. Deletions with a cut vertex.** Following [NL §2.1 (Z3)], a deletion is a configuration if it
has at most one cut vertex, lying in exactly two blocks with exactly two edges leaving
the configuration there. 7,006 of the 21,172 members have such a cut vertex, and 19,133 candidates
with two or more cut vertices are excluded. 𝒟 itself has 1,677 configurations with a cut vertex
(1,213 in scope) **[spec-check]**, so including them matches 𝒟. The spec includes them. Say if
you want them excluded.

**Q4. RSST.** The spec rests on [NL] alone; RSST is cited from memory (§11 R6). To confirm RSST's
section numbers and definitions, the main session would need to download the PDF
`https://thomas.math.gatech.edu/PAP/fc.pdf` (size not checked). This is optional and changes no
definition.

---

## 13. Sources

- **[NL]** arXiv:2603.24880v2, HTML version at `https://arxiv.org/html/2603.24880v2`: §2.1
  (configurations, (Z1)–(Z3), free completion, ring-size formula, Kempe chains and changes,
  i-extendible, level, D_i- and D-reducible, Lemma 2.1, C-reducibility and Fig. 3, "Computer check of
  D-reducibility"), §3 (𝒟, Lemma 3.2 (D0)–(D3)), App. A.1 (Algorithms 1–3, pseudocode only). Read
  as HTML; no PDF, no code.
- **[idx]** `search/index/build.py` (docstring: file format, conventions, shape; functions
  `parse`, `validate`, `single_vertex`, `row`), `search/index/README.md`,
  `search/index/configurations.csv`.
- `data/near-linear-4ct/reducible-configurations/README.md`; `data/README.md`;
  `notes/F-ai-and-computation-engine.md` (the 8,202 count); `THIRD_PARTY_NOTICES.md` (the list of
  what may not be read); issue #48 and its release comment.
- Robin Thomas's web page on the four colour theorem
  (`https://thomas.math.gatech.edu/FC/fourcolor.html`), read for context only; it contains no
  definitions used here.
- **[RSST]** not re-read (PDF only; not downloaded).
- Not read: any reducibility program (§10.2), `third_party/`, `lean/`.
