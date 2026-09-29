# Workstream A — The Rosetta Stone

Results log. Newest first. One row per result, added in the pull request that
produced it.

A row belongs here only if it meets the trust rule: a Lean theorem that builds
on the pinned toolchain, or a script whose output reruns identically from a
clean checkout. Leads, partial arguments and AI-written summaries go under
"Open leads" instead, and are not results.

| Date | Result | Evidence | Tier | PR |
| --- | --- | --- | --- | --- |
| 2026-09-29 | **Tait's correspondence, proved without the Four Colour Theorem.** A loopless plane triangulation is vertex 4-colourable (Mathlib's `Colorable 4`) exactly when its cubic dual has a proper 3-edge-colouring (`FourCT.PlaneGraph.tait`). At the hypermap level: a face 4-colouring of a cubic map gives a proper 3-edge-colouring on any surface; on the sphere every proper 3-edge-colouring arises that way; and on a connected map the correspondence is four-to-one. The genus-zero step is a new lemma: an edge labelling in ℤ₂ × ℤ₂ that sums to zero at every vertex is a difference of face labels (`FourCT.exists_facePotential`), proved from Euler's formula by a rank count over ℤ₂. The theta graph on the torus shows that the genus-zero hypothesis is needed. | `lean/FourCT/{Potential,Tait,Examples}.lean`; `lean-build` checks the axioms, and checks that none of these theorems depends on the 4CT (`checks/lean/fourct_independence.lean`, with two controls that must) | A3 | #35 |
| 2026-09-29 | **Every planar simple graph is 4-colourable, stated in Mathlib's vocabulary** (`SimpleGraph.IsPlanar.colorable_four`). Also the 4CT for loopless plane graphs (`FourCT.PlaneGraph.four_colorable`) and for planar bridgeless hypermaps (`FourCT.hypermap_fourColorable`), all derived from the base port. Worked example: `K₄` is planar and not 3-colourable, so the theorem is tight. Every theorem depends only on `propext`, `Classical.choice`, `Quot.sound`. | `lean/FourCT/{Base,PlaneGraph,Examples}.lean`; `lean-build` checks the axioms of every theorem in `checks/lean/fourct_axioms.lean` | A3 | #34 |
| 2026-09-27 | **The four colour theorem builds on Lean and Mathlib `v4.34.1`**, the program's pinned toolchain, as `FourColor.fourColorTheorem` in `lean/`. Depends only on `propext`, `Classical.choice`, `Quot.sound`; 115,342 declarations, no sorries, no extra axioms; anti-vacuity controls pass. No Lean source changed from corun1024 `3db71e0`. | `lean/build.sh` on the self-hosted runner; `lean-build` on this PR | A2 | #26 |
| 2026-09-27 | `RBarish-UTokyo/FourColorTheorem-Lean4` builds clean on its own pinned toolchain, and `FourColor.RealPlane.four_color` depends on no axioms beyond `propext`, `Classical.choice`, `Quot.sound`. | port-build run [36350029344](https://github.com/glgmail/4ct-program/actions/runs/36350029344), artifact `port-build-RBarish-UTokyo` | evidence for A1 | #24 |
| 2026-09-27 | `corun1024/4ct` builds clean on its own pinned toolchain, and `FourColor.fourColorTheorem` depends on no axioms beyond `propext`, `Classical.choice`, `Quot.sound`. 115,342 declarations, no sorries. | port-build run [36336993686](https://github.com/glgmail/4ct-program/actions/runs/36336993686), artifact `port-build-corun1024` | evidence for A1 | #20 |

## Open leads

- **Tait's edge side in Mathlib's vocabulary.** For a simple triangulation
  with at least four vertices, the dual has no parallel edges, and
  `EdgeColoring` of the dual should match a proper colouring of the dual's
  `lineGraph`. Not stated or proved; only needed if A4 wants the edge side
  stated for `SimpleGraph`s.

---

# A3 — Mathlib survey, and the foundation for plane graphs

Issue #4 asks for a survey, before anything is written, of what Mathlib at
`v4.34.1` (commit `d13f23b`) already provides toward planarity, Euler's
formula, rotation systems, duality and nowhere-zero flows. The base port
turned out to matter as much as Mathlib, so it is surveyed alongside.

Mathlib was read in the runner's copy under `lean/.lake/packages/mathlib`,
and the base port under `lean/FourColor/`.

## What exists

| Concept | Mathlib `v4.34.1` | Base port (`FourColor`) |
| --- | --- | --- |
| Simple graphs | `SimpleGraph`, with walks, connectivity, matchings, Hamiltonian cycles and line graphs | — |
| Vertex colourings | `SimpleGraph.Coloring`, `Colorable`, `chromaticNumber` | `Hypermap.GraphColoring`, `GraphFourColorable` (colours constant on node orbits) |
| Half-edges | `SimpleGraph.Dart`: a pair of adjacent vertices, with no cyclic order | darts are the carrier type of a `Hypermap` |
| Edge colourings | `SimpleGraph.EdgeLabeling`: any labelling of edges, not required to be proper. A proper edge colouring is a vertex colouring of `lineGraph` | the Tait edge-colour traces in `Color.lean`, used internally |
| **Embeddings / rotation systems** | **none** | **`Hypermap`**: three permutations `edge`, `node`, `face` of the darts with `node * face * edge = 1` (`Hypermap.lean`) |
| **Faces** | **none** | orbits of `face` (`CFace`) |
| **Euler's formula** | **none**. `EulerCharacteristic` exists only for chain complexes | `EulerLhs`/`EulerRhs`/`genus`; `evenGenus` proves the formula exact (`Euler.lean`) |
| **Planarity** | **none**. The only "planar" in Mathlib is `Coplanar`, for affine spaces | `Planar : genus = 0` (`Hypermap.lean`) |
| **Duality** | **none** | `dual`, with `dual_dual`, `genus_dual`, `planar_dual` |
| Bridges and loops | — | `Bridgeless`, `Loopless`, and `bridgeless_dual : G.dual.Bridgeless ↔ G.Loopless` (`Geometry.lean`) |
| **Nowhere-zero flows** | **none** | none. `Color` is the Klein four-group ℤ₂ × ℤ₂ as `Bool × Bool` (`bitsEquiv`), which is the right group for them |
| **Tait's correspondence** | **none** | none stated. The colour traces are Tait-style, but there is no vertex-colouring ↔ edge-colouring theorem |
| **The combinatorial 4CT** | — | `Hypermap.fourColorable_of_no_minimalCounterExample` together with `Hypermap.not_minimalCounterExample`: every finite, planar, bridgeless hypermap is `FourColorable` |
| The 4CT for real-plane maps | — | `FourColor.fourColorTheorem`, plus a bridge to Mathlib's topology (`RealPlaneMathlib.lean`) |

**Summary.** Mathlib has graphs and colourings but no planar-graph layer at
all: no embeddings, faces, Euler formula, duality or flows. The base port has
the whole embedding layer, as Gonthier's hypermaps, up to and including a
combinatorial Four Colour Theorem. Neither has Tait's correspondence or
nowhere-zero flows.

## Decision: plane graphs are the base port's hypermaps

#4 asks A3 to choose between Mathlib's `SimpleGraph` and the base port's
hypermap encoding for plane graphs. **A3 builds on the base port's
`Hypermap` for the embedding, and states everything a reader sees through
Mathlib's `SimpleGraph`.** Concretely:

- A **plane graph** is a finite `FourColor.Hypermap` whose `edge` is an
  involution with no fixed points, which is a combinatorial map, and which is
  `Planar`. Faces, genus, Euler's formula and the dual all come with it.
- Its **underlying graph** is a Mathlib `SimpleGraph` on the node orbits,
  with two nodes adjacent when an `edge` step joins them. Colourings, edge
  colourings (through `lineGraph`) and flows are stated there, in Mathlib's
  vocabulary.
- The **bridge to the base port** is then short. A graph colouring of the
  underlying graph is a `GraphColoring` of the hypermap, and `GraphColoring`
  is a `Coloring` of the `dual` (`fourColorable_dual_iff`). The
  combinatorial 4CT above applies to that.

Why not rotation systems built from scratch on `SimpleGraph`:

- Everything the embedding needs already exists in the base port and is
  proved there: faces, genus, planarity, duality, bridges ↔ loops. A second
  encoding would duplicate it, and would then need its own equivalence proof
  before it could reach the combinatorial 4CT.
- The theorem A3 has to connect to is stated over hypermaps, so any other
  choice adds a layer between our statements and the proof.
- Readability is kept where it matters. What A4 states — colourings,
  Tait colourings, flows — is phrased with Mathlib's `SimpleGraph`, which
  anyone who knows Mathlib can read. The hypermap is the machinery
  underneath.

The risk is the one #4 names: a definition that is subtly wrong makes
everything downstream vacuous. So each definition gets an English gloss and
a worked example, the tetrahedron and the octahedron checked by `decide`,
before anything is built on it.

## What A3 has to build

1. `PlaneGraph`, the underlying `SimpleGraph`, and the colouring bridge to
   `Hypermap.GraphColoring`. Worked example: the tetrahedron's underlying
   graph is the complete graph on four vertices.
2. The combinatorial 4CT restated for plane graphs: every loopless plane
   graph's underlying graph is 4-colourable. It follows from the base port's
   combinatorial theorem through `dual` and `bridgeless_dual`.
3. Tait's correspondence: the vertex 4-colourings of a plane triangulation
   correspond to the proper 3-edge-colourings of its cubic dual.
4. Proper 3-edge-colourings correspond to nowhere-zero ℤ₂ × ℤ₂-flows, using
   the base port's `Color` as the group.

Items 1 and 2 are the bridge #4 calls load-bearing. Items 3 and 4 are the
correspondences A4 needs.

## Items 1 and 2: done

In `lean/FourCT/PlaneGraph.lean`, with the worked example in
`lean/FourCT/Examples.lean`. #4 asks for an English gloss of each definition:

- **`PlaneGraph D`**: a finite set of darts `D` with the base port's three
  permutations (`edge` pairs the two ends of each edge, `node` goes round a
  vertex, `face` goes round a face, and `node ∘ face ∘ edge = id`). Every edge
  has exactly two darts (`Plain`), and the genus is zero (`Planar`). Loops
  and multiple edges are allowed; results about colouring assume no loops.
- **`PlaneGraph.Vertex`**: the orbits of `node`, one per vertex.
- **`PlaneGraph.graph`**: Mathlib's `SimpleGraph` on the vertices, in which
  two distinct vertices are adjacent when an edge joins them. Loops and
  repeated edges are forgotten.
- **`SimpleGraph.IsPlanar G`**: `G` is contained in the underlying graph of
  some loopless plane graph (`G ⊑ P.graph`, Mathlib's `IsContained`). Its
  vertices map injectively to the plane graph's, with adjacency preserved but
  not necessarily reflected, so this is an ordinary subgraph, not an induced
  one. For finite graphs this is the usual notion. A graph with infinitely
  many vertices is never `IsPlanar`.

The theorems, all derived from the base port, with nothing new assumed:

| Theorem | Says |
| --- | --- |
| `FourCT.hypermap_fourColorable` | every finite planar bridgeless hypermap is four-colourable (assembled from the port's unavoidability theorem and its checks) |
| `FourCT.PlaneGraph.graphFourColorable_iff` | for a loopless plane graph, the port's graph colourings are exactly the proper 4-colourings of the underlying `SimpleGraph` |
| `FourCT.PlaneGraph.four_colorable` | the underlying graph of every loopless plane graph is 4-colourable (from the above, through `dual`, `planar_dual` and `bridgeless_dual`) |
| `SimpleGraph.IsPlanar.colorable_four` | **every planar simple graph is 4-colourable** |

**The worked example is the tetrahedron**: 12 darts, three per vertex, given
by explicit tables.
- **Checked by `decide`:** it is plain, satisfies the hypermap identity and
  is loopless.
- **Planar:** it is connected (a computable set of reachable darts, proved
  sound once) and has 6 edges, 4 vertices and 4 faces (orbit counts by
  `decide`). Euler's formula then gives genus zero: `2·1 + 12 = 6 + 4 + 4`.
- **K₄ is planar:** its underlying graph contains `K₄` (`k4Embedding`).
- **The theorem is tight:** `K₄` is not 3-colourable
  (`not_colorable_three_K4`, via Mathlib's `chromaticNumber_top`). So
  `IsPlanar` is not so narrow as to make the theorem trivial.
- **The tricky cases come out right:** every simple graph on at most four
  vertices is `IsPlanar` (`isPlanar_of_card_le_four`, as a subgraph of
  `K₄`). That includes a path, an edgeless graph and a disconnected graph.
  `K₅` is not planar (`not_isPlanar_K5`), but only as a consequence of the
  4CT itself, not an independent check.

**How the definition was chosen** (research, 2026-09-29). It was compared
with the other formal definitions of planarity found:

- **Gonthier's hypermaps, and the base port:** genus 0 by Euler's formula,
  with components counted.
- **Isabelle's AFP** (Noschinski, *Planarity_Certificates*): combinatorial
  maps of Euler genus 0, linked to Kuratowski's theorem.
- **devin-lai/jsp-000512-lean**, Lean 4: a topological `PlaneDrawing` in ℝ²,
  also covering infinite graphs by compactness.
- **abhishan82/Pancyclicity-in-4-connected-planar-graphs**, Lean 4: a
  rotation system with `V − E + F = 2` and simple face boundaries. That
  rules out every disconnected graph, and every graph with a cut vertex: a
  path's single face meets its middle vertex twice.

Mathlib has no definition of planarity.

The combinatorial, component-counting notion was kept. Its first version
used `G ↪g P.graph`, which in Mathlib is an *induced* embedding, while its
docstring said "subgraph". Both define the same class of finite graphs, but
the definition did not say what its gloss said, so it was changed to `⊑`
(Gabriel's decision). Not formalized here, and recorded as open:

- the equivalence with drawings in the plane, which is classical but needs
  Jordan–Schoenflies;
- infinite planar graphs, which are a compactness step away
  (De Bruijn–Erdős).

## Item 3: Tait's correspondence, done

In `lean/FourCT/Potential.lean` and `lean/FourCT/Tait.lean`, with worked
examples in `lean/FourCT/Examples.lean`.

**It must not use the Four Colour Theorem.** For planar maps both sides of
Tait's correspondence are true, since the theorem is proved, so an
equivalence derived from it would be empty. The axiom check cannot see the
difference: the 4CT itself uses only the three standard axioms. So
`lean-build` now runs a second check, `checks/lean/fourct_independence.lean`.
It walks every constant that a theorem's statement and proof mention,
transitively, and fails if the walk reaches `FourColor.fourColorTheorem`,
the port's `reducibility`, `exclude5` to `exclude11`,
`Hypermap.not_minimalCounterExample`, or our `fourColor_base` and
`hypermap_fourColorable`. Two controls, `IsPlanar.colorable_four` and
`not_isPlanar_K5`, must reach them, and do, through `reducibility`. Tested
against a theorem that uses the 4CT (fails as required) and a control that
does not (fails as required).

**The new definitions**, with English glosses:

- **`FourCT.EdgeColoring G e`**: a proper 3-edge-colouring of the hypermap
  `G`. Each edge gets one of the three non-zero colours of ℤ₂ × ℤ₂ (both of
  its darts carry the colour, and it is never `0`), and consecutive darts
  around a vertex get different colours. At a vertex of degree three, the
  three edges there get three different colours.
- **`FourCT.taitEdge G k`**: Tait's rule. From a colouring `k` of the faces,
  colour each edge by the sum of the colours of the faces on its two sides.
- **`FourCT.PlaneGraph.IsTriangulation T`**: every face of `T` has exactly
  three darts, so three edges.
- **`FourCT.Orbit σ`, `FourCT.inc G σ`**: the orbits of a permutation of the
  darts, and the ℤ₂ incidence matrix between edges and orbits (the number of
  shared darts, mod 2). These are proof machinery, not part of any
  statement A4 will use.

**The theorems:**

| Theorem | Says |
| --- | --- |
| `FourCT.edgeColoring_taitEdge` | a face 4-colouring of a plain cubic map gives a proper 3-edge-colouring. Any genus |
| `FourCT.range_inc_face_eq` | on a plain genus-0 map, the edge labellings over ℤ₂ that are sums of face labels are exactly those summing to zero at every vertex |
| `FourCT.exists_facePotential` | the same with labels in the Klein four-group `Color` |
| `FourCT.exists_coloring_of_edgeColoring` | on the sphere, every proper 3-edge-colouring of a cubic map is `taitEdge` of a face 4-colouring |
| `FourCT.taitEdge_eq_taitEdge_iff_of_connected` | on a connected map, two face colourings give the same edge colouring exactly when they differ by a constant colour: the correspondence is four-to-one |
| `FourCT.PlaneGraph.tait` | **a loopless plane triangulation is vertex 4-colourable (Mathlib's `Colorable 4`) exactly when its cubic dual has a proper 3-edge-colouring** |

**Where the sphere comes in.** Only in `range_inc_face_eq`, and only through
Euler's formula, by counting dimensions over ℤ₂:

- The face-sum labellings have dimension `F − C`: adding a constant to the
  faces of one component changes nothing.
- The labellings summing to zero at each vertex have dimension `E − V + C`.
  This is `E` minus the rank of the vertex–edge incidence matrix, which is
  `V − C`, via `Matrix.rank_transpose`.
- Every face-sum labelling sums to zero at each vertex: around a vertex,
  each face is met twice.
- Genus zero with two darts per edge gives `V − E + F = 2C`, so the two
  dimensions are equal and the spaces coincide.

The labels in `Color` are handled one bit at a time.

**Worked examples** (`FourCT/Examples.lean`):

- **The tetrahedron** is a triangulation, by `decide`. Colouring vertex `a`
  with colour `a` gives, by Tait's rule, the colouring of `K₄`'s edges by
  its three perfect matchings, `01, 23 ↦ c1`, `02, 13 ↦ c2`, `03, 12 ↦ c3`
  (by `decide`). That is a proper 3-edge-colouring of the dual (by
  `decide`). `tetrahedron_colorable_of_tait` then gets `K₄`'s
  4-colourability from the edge colouring alone, without the 4CT.
- **The theta graph on the torus** (`theta_torus`): two vertices joined by
  three edges, both turning the same way. Its genus is one, from the orbit
  counts: 3 edges, 2 vertices, 1 face. It has a proper 3-edge-colouring,
  but no face 4-colouring, since its single face lies on both sides of every
  edge. So the genus-zero hypothesis of `exists_coloring_of_edgeColoring`
  cannot be dropped.

**A departure from the plan above.** The decision section said edge
colourings would be stated through Mathlib's `lineGraph`. They are stated on
the hypermap instead. A cubic dual can have parallel edges: two triangles
sharing two edges, which happens when the triangulation has multiple edges,
as plane graphs may. A `SimpleGraph` forgets parallel edges, and a proper
edge colouring must still give them different colours. The vertex side of
`PlaneGraph.tait` is in Mathlib's vocabulary. The edge side is on the dual
hypermap, with the gloss above.

Item 4 (flows) comes next. Its core is already here: a nowhere-zero
ℤ₂ × ℤ₂-flow is an edge labelling with non-zero labels summing to zero at
every vertex, which is the hypothesis of `exists_facePotential`.

---

# A2 — the base port on the pinned toolchain

**Done, and it needed no Lean source changes at all.**

The base port, corun1024/4ct at `3db71e0`, was moved from
`leanprover/lean4:v4.34.0-rc2` with Mathlib unpinned (resolving to a
`master` commit, `141f6b6`) onto `v4.34.1` for both, and built with its own
`build.sh`:

```
plan: 821 modules, 7.9 core-hours, 4 jobs, 20 GB budget, predicted 135 min
anti-vacuity audit: negative controls pass
THEOREM PROVED: FourColor.fourColorTheorem : FourColor.FourColorTheorem
  depends only on [propext, Classical.choice, Quot.sound]
checked 115342 FourColor declarations: no sorries, no extra axioms
```

| | Upstream (A1) | On `v4.34.1` (A2) |
| --- | --- | --- |
| Axioms | `propext, Classical.choice, Quot.sound` | identical |
| Declarations checked | 115,342 | 115,342 |
| Modules | 821, none failed | 821, none failed |
| Wall clock at `JOBS=4` | 2 h 00 m | 2 h 07 m |
| Peak single process | 20.2 GB | 20.3 GB |

### What changed

Three files, all build configuration:

- `lean-toolchain`: `v4.34.0-rc2` → `v4.34.1`;
- `lakefile.toml`: `rev = "v4.34.1"` added to the Mathlib requirement;
- `lake-manifest.json`: re-resolved.

The "non-mechanical changes" list #3 asked for is **empty**. Nothing in
the proof needed adjusting for the patch release or for the move off Mathlib
master. The certificate generator reproduced the same outputs (62 bulk
groups, 110 walks, 152 bridge modules).

This was the outcome to hope for rather than to expect. The risk named in
#3 — that corun's heavy `decide +kernel` computations would show changed
kernel reduction as a timeout or memory blow-up — did not materialise: peak
memory moved by 0.1 GB.

### How it landed in the repository

`lean/` is now the Lake package root, with corun's tree laid out there
unchanged so its scripts run unmodified. All 498 upstream `.lean` files were
verified byte-identical to upstream by git blob hash when copied. See
`lean/README.md`.

The layout was forced by a constraint that is easy to miss and expensive to
get wrong: corun builds with `scripts/build_pool.py`, which writes **no Lake
trace files**. Lake therefore does not recognise its output, and any `lake
build` that reaches FourColor rebuilds all 821 modules with no job cap or
memory budget — an OOM on this runner. Guardrails now prevent that three
ways (see `lean/README.md`), and **task A3 will need to extend the build**
before any FourCT module can import FourColor.

### Per-PR CI cost

The decision #3 asked A2 to make: `lean-build` keeps its workspace between
runs (`clean: false`), so `build_pool.py`'s content fingerprints make a
pull request that does not touch the port rebuild none of it. The first run
after this merges pays the full ~2.5 hours once. Editing `lean/lakefile.toml`,
`lean/lean-toolchain` or `lean/lake-manifest.json` invalidates everything
again.

# A1 — statement review of the two Lean ports

**Status: statement comparison complete; build evidence outstanding.**

Nothing below is a result under the trust rule. It is a reading of source
text, not a theorem that built. The build half of A1 — times, peak memory,
clean build, `#print axioms` — needs the 32 GB runner and is gathered by
`.github/workflows/port-build.yml`, which nobody has run yet. Treat the
recommendation as provisional until it has.

Sources read, all pinned:

| What | Commit |
| --- | --- |
| `corun1024/4ct` | `3db71e0a786a1f19be04c5266fe3d06fed216885` |
| `RBarish-UTokyo/FourColorTheorem-Lean4` | `20fa34599f5189dd569d96dd22f306c94ab1c446` |
| `rocq-community/fourcolor` (Gonthier, formerly `math-comp/fourcolor`) | `c1d6b1cd5288bea4b067aac13cdde3c18dffe018` |

## The three final statements

Gonthier, `theories/proof/fourcolor.v`, inside
`Section FourColorTheorem` with `Variable Rmodel : Real.model`:

```coq
Theorem four_color m : simple_map m -> colorable_with 4 m.
```

RBarish, `Solution.lean`:

```lean
theorem four_color (m : Map) (h : SimpleMap m) : ColorableWith 4 m :=
  compactness_extension four_color_finite m h
```

corun1024, `FourColor/RealPlane.lean` and `FourColor/Complete.lean`:

```lean
def FourColorTheorem : Prop := ∀ m : PlaneMap, SimpleMap m → ColorableWith 4 m

theorem fourColorTheorem : FourColorTheorem :=
  fourColorTheorem_of_checks reducibility
    exclude5 exclude6 exclude7 exclude8 exclude9 exclude10 exclude11
```

All three say the same thing, and both ports follow Gonthier's proof
architecture as well as his statement: the general case comes from the finite
case by compactness (`compactness_extension` / `finitize`), the finite case
from discretisation to a hypermap plus the combinatorial 4CT.

## Definitions, against Gonthier's `realplane.v`

Both ports transcribe the same chain of definitions in the same order. The
statement's meaning rests entirely on these, so they are what matters.

| Gonthier (`realplane.v`) | RBarish | corun1024 |
| --- | --- | --- |
| `point := Point (x y : Real.val R)` | `structure Point where x y : ℝ` | `abbrev Point := ℝ × ℝ` |
| `region := point -> Prop` | `abbrev Region := Point → Prop` | `abbrev Region := Set Point` |
| `map := point -> region` | `abbrev Map := Point → Region` | `abbrev PlaneMap := Point → Region` |
| `union`, `intersect`, `subregion`, `meet`, `nonempty` | each defined explicitly | Mathlib's `∪`, `∩`, `⊆`, `.Nonempty` |
| `plain_map` (`map_sym`, `map_trans`) | `PlainMap`, same two fields | `PlainMap`, same two fields |
| `cover m := fun z => m z z` | same | `{z \| z ∈ m z}` |
| `at_most_regions n m` | same | same |
| `open` (via open rectangles) | `Open` | `IsOpenRegion` |
| `closure` | `closure` | `regionClosure` |
| `connected` | `Connected` | `IsConnectedRegion` |
| `simple_map` | `SimpleMap` | `SimpleMap` |
| `border`, `corner_map`, `not_corner`, `adjacent` | same four | `border`, `cornerMap`, `notCorner`, `Adjacent` |
| `coloring` (4 fields) | `Coloring`, same 4 | `Coloring`, same 4 |
| `colorable_with n m` | `ColorableWith` | `ColorableWith` |

I read each definition against its Coq original. **No definition in either
port changes the meaning of the statement.** The traps worth checking
explicitly, and how each port handles them:

- **Adjacency excludes corners.** Both define `adjacent` as "different
  regions, and their common border contains a point lying in the closure of
  at most two regions". Without the corner exclusion the theorem is false —
  diagonally opposite squares of a checkerboard would count as adjacent. Both
  get this right.
- **Maps are partial equivalence relations, not total ones.** Points on
  borders belong to no region. Both keep `plain_map` as symmetry plus
  transitivity, with no reflexivity.
- **`coloring` requires all four conditions.** Dropping
  `coloring_consistent` would let each point take its own colour. Both carry
  all four fields.
- **Finiteness is not assumed.** The theorem is for all simple maps,
  including infinitely many regions. Both state the unrestricted version and
  derive it by compactness, as Gonthier does.

## Where both ports differ from Gonthier

One difference, shared by both, and it is the only substantive one:

**Gonthier quantifies over an arbitrary model of the reals.** `fourcolor.v`
takes `Variable Rmodel : Real.model`; the theorem holds for any such model.
Both Lean ports instead fix Mathlib's `ℝ`.

This is a genuine narrowing of the statement as written, though not a
mathematically serious one: Gonthier's `realcategorical.v` proves all models
of the reals isomorphic, and these definitions use only the order on `ℝ`.
RBarish states the specialisation explicitly in `Challenge.lean`'s docstring.
It should be recorded in `lean/Statements/` whichever port we take, so that a
later reader does not believe we have the more general theorem.

## Where the two ports differ from each other

### 1. Whether the statement mentions Mathlib

RBarish's statement is deliberately Mathlib-free: `Region` is `Point → Prop`,
and union, intersection, openness, closure and connectedness are all defined
from open rectangles. `Challenge.lean` says so, and imports only
`Mathlib.Basic.Real.Basic`. **No Mathlib topology anywhere in that repository**
(searched: no `IsPreconnected`, no `Mathlib.Topology`).

corun1024 uses `Set Point` and Mathlib's set operations, *and* ships
`FourColor/RealPlaneMathlib.lean`, which proves the elementary notions are
Mathlib's:

```lean
theorem isOpenRegion_iff (r : Region) : IsOpenRegion r ↔ IsOpen r
theorem regionClosure_eq (r : Region) : regionClosure r = closure r
theorem isConnectedRegion_iff_isPreconnected {r : Region} (hr : IsOpenRegion r) :
    IsConnectedRegion r ↔ IsPreconnected r
theorem simpleMap_iff (m : PlaneMap) :
    SimpleMap m ↔ PlainMap m ∧ (∀ z, IsOpen (m z)) ∧ ∀ z, IsPreconnected (m z)
```

For a statement meant to be read and disbelieved, RBarish's independence is
the better property. **For this program it is the wrong way round.** A3 and A4
need planar embedding, duality and flows stated against Mathlib, and the
Rosetta Stone's whole purpose is transfer between formulations. corun1024
already has the bridge; with RBarish we would have to build it, and building
it is exactly the kind of definitional work where a mistake is invisible to
the kernel.

### 2. Guards against a vacuous statement

corun1024 ships two things beyond the proof:

- `scripts/Audit.lean` — kernel-checked **negative controls**. Its own words:
  a proof "can be perfectly sound and still worthless if the *checkers* it
  relies on accept everything". It proves `theRedpart (Part.free 5) = false`
  and similar, so the reducibility oracle is not constantly `true`, and
  `QuizTree.size theQuizTree = 3361`, so the quiz data is the real data and
  not an empty tree that answers every query.
- `FourColor/Nonvacuity.lean` — builds an explicit four-region configuration
  in the plane with Mathlib closures computed, plus a pigeonhole lemma
  `not_colorable`: `n+1` pairwise adjacent regions cannot be `n`-coloured. So
  the four in "four colours" is not slack.

`build.sh` runs these as part of the standard build, alongside checks for no
`sorry`, no `native_decide`, and the axioms of `fourColorTheorem`.

RBarish has `scripts/check_challenge_sync.py`, which verifies that the
definitions in `Challenge.lean` are identical to those the proof uses — a
different and also valuable guard, against the statement drifting from the
proof. It also has `FourColor/Examples.lean`, unexamined so far; the build
task should look at whether it plays the non-vacuity role.

This program's trust rule says a statement that builds is not yet a result.
corun1024's audit is the closest thing either port has to mechanising that
rule.

### 3. `sorry`, `native_decide`, axioms

Neither port has a `sorry` in its proof.

Two things that look alarming and are not, recorded so nobody re-raises them:

- GitHub code search reports `sorry` in eight corun1024 files. Seven are
  tooling and documentation that *check for* `sorry`; the eighth,
  `FourColor/Embed.lean`, is a docstring reading "Every declaration below is
  fully proved, with no `sorry` and no new axioms". There is no `sorry` in
  corun1024's Lean proof.
- RBarish's `Challenge.lean` ends `theorem four_color ... := sorry`. That file
  is the statement-only specification, deliberately unproved; `Solution.lean`
  carries the real proof, and `check_challenge_sync.py` keeps the two in step.

`native_decide` appears in corun1024 only in tooling that forbids it. Both
ports appear to rely on kernel `decide` rather than compiled evaluation,
which matters: `native_decide` would put the Lean compiler in the trusted
base.

**None of this substitutes for `#print axioms` on a real build.** Source
reading cannot see what the elaborator actually admitted.

### 4. Distance from our pinned toolchain

| | Upstream toolchain | Distance to `v4.34.1` |
| --- | --- | --- |
| corun1024 | `leanprover/lean4:v4.34.0-rc2` | forward one patch, off the rc |
| RBarish | `leanprover/lean4:v4.35.0-rc2` | backward one minor, off the rc |

Both are on release candidates, which our pin forbids. corun1024 is the
smaller move, and forward rather than backward. Moving RBarish means
un-adopting whatever arrived in v4.35, which is the harder direction because
the compiler will not tell you what a lemma used to be called.

Both `Mathlib/Basic/Real/Basic.lean` and `Mathlib/Data/Real/Basic.lean` exist
at Mathlib `v4.34.1`, so RBarish's statement import is not itself a problem.

### 5. Build cost and how the build is driven

corun1024 has `scripts/build_pool.py`, which schedules modules against a
**cost table of per-module wall time and peak memory**
(`scripts/module_cost.tsv`, 27 KB) and admits a module only if its predicted
peak fits a budget. It takes `JOBS` and `--memory` **in GB**:
`JOBS=8 MEMORY=40 ./build.sh`.

That is directly useful to us, because the self-hosted runner is WSL2 with a
~26 GB share, and corun's own documentation says single modules peak near
20 GB.

RBarish has `scripts/engine_memtime.py`, `final_run.sh` and
`palomar_check.sh`; the plan of record records it as needing about 16 GB and
25 GB of disk, 2.4–3.3 hours on 16 cores.

## Decision: corun1024/4ct (Gabriel, 2026-09-27)

**The base port is `corun1024/4ct`**, at pinned commit `3db71e0`. A2 moves
it to `v4.34.1`.

Taken with the full comparison below in view, including the case for
RBarish. What the choice commits the program to, so it is not rediscovered
later:

- **CI cost is now A2's problem to solve.** corun builds in ~2 hours at a
  20.2 GB peak. Once it lives in `lean/`, `lean-build` rebuilds it on every
  pull request unless A2 puts a persistent build cache in place. See #3.
- **The self-hosted runner stays on the critical path** for workstream A. A
  20.2 GB build will never fit a GitHub-hosted runner. Its reliability — the
  keepalive, the disk floor, the memory cap — is now load-bearing, not
  incidental.
- **`RealPlaneMathlib.lean` is the foundation A3 and A4 build on.** That was
  the main reason for the choice; A3 should start from it rather than
  re-derive the bridge.
- **corun's `Audit.lean` and `scripts/check.sh` become part of our
  verification**, and should keep passing after every change to the port —
  not only after A2.

RBarish remains pinned in `third_party/` as the second independent Lean
formalisation, and `check_challenge_sync.py` is worth imitating for
`lean/Statements/`: a mechanical check that the published statement and the
proved statement are the same text.

## Recommendation: corun1024/4ct — now with build evidence

On the statement itself there is nothing to choose between them. Both are
faithful transcriptions of Gonthier, and both narrow the reals in the same
defensible way. The recommendation turns entirely on what the port is *for*
in this program.

1. **The Mathlib bridge already exists.** A3 and A4 need planar embedding,
   duality, Tait and flows stated against Mathlib. `RealPlaneMathlib.lean`
   connects the statement's elementary topology to `IsOpen`, `closure` and
   `IsPreconnected` today. With RBarish we would write that ourselves, in the
   one area where an error is invisible to the kernel.
2. **It mechanises our trust rule.** The anti-vacuity audit and the
   non-vacuity construction are precisely the "a statement that builds is not
   yet a result" discipline, already in Lean and already kernel-checked.
3. **It is closer to the pin**, and moving forward off an rc is easier than
   moving back a minor version.
4. **Its build is memory-aware**, which matters on a 26 GB WSL2 share.

**Both ports are now built and measured, and the decision is close.** It was
not close when only corun had been measured, and I am recording the change
of view rather than quietly keeping the earlier answer.

Both produce exactly `[propext, Classical.choice, Quot.sound]`. The axiom
check, which was the one thing that could have been decisive, discriminates
between them not at all.

**The case for corun1024** rests on two things A3 and A4 will use directly:

- `RealPlaneMathlib.lean` already connects the statement's elementary
  topology to `IsOpen`, `closure` and `IsPreconnected`. A3 needs planar
  embedding and duality against Mathlib; A4 needs Tait and flows stated
  that way. With RBarish we write that bridge ourselves, and a wrong
  definition there is invisible to the kernel — the one category of error
  this program has no mechanical defence against.
- Its verification apparatus is stronger where it counts for a
  computational proof: 115,342 declarations checked for sorries and stray
  axioms, and negative controls proving the reducibility oracle and quiz
  data are not degenerate.

**The case for RBarish** is now much stronger than the statement review
suggested, and it is operational:

- **3.5 GB peak against 20.2 GB.** A 3.5 GB build runs on a GitHub-hosted
  runner; a 20.2 GB build never will. Choosing RBarish would take the
  self-hosted machine off workstream A's critical path entirely.
- **~22 minutes against 2 hours.** Every A2 iteration, every re-pin at a
  gate review, pays that difference.
- `check_challenge_sync.py` mechanically verifies the published statement
  matches the proved one — a guarantee corun does not offer.

**I still recommend corun1024, less confidently than before.** The Mathlib
bridge is load-bearing for the next two tasks and building it ourselves is
precisely the error-prone definitional work; the audit is closer to this
program's trust rule than anything RBarish has. But if the self-hosted
runner proves as much trouble over the next month as it was on day one,
that judgement should be revisited — the argument for RBarish is that it
makes an entire class of infrastructure problem go away, and today gave
real evidence about how expensive that class is.

The remaining unknown is **A2's question**: which port survives the move to
`v4.34.1`. corun moves forward one patch; RBarish moves back one minor,
un-adopting whatever arrived in v4.35, which is the harder direction. If
that turns out badly for corun, the case inverts.

Gabriel decides. This is a recommendation with its reasons, not a choice.

## Build attempt 1 — corun1024, 2026-09-27 (failed: environment)

Run [36305441480], `JOBS=1`, `memory_gb=20`, self-hosted runner. **Failed
after 5 min 13 s of `build.sh`, on a missing Python package** — not on
anything about the port.

```
File ".../port/scripts/bulkspace.py", line 17, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
```

corun's `scripts/bulkspace.py` imports numpy; the runner had no numpy. Fixed
by adding `python3-numpy` to the runner dependencies, and `port-build.yml`
now checks for it before starting rather than five minutes in.

Not a measurement of the port. But three things did come out of it:

- **The toolchain coexists.** `elan` installed the port's `v4.34.0-rc2`
  alongside our `v4.34.1` with no conflict, and `lake exe cache get` restored
  Mathlib from cache (8,905 files decompressed, nothing downloaded). The
  build reached corun's own code.
- **`JOBS=1` is not honoured by every phase.** `/usr/bin/time` reported
  **1101 % CPU** over the 5 min 13 s — roughly eleven cores — during the
  reducibility-certificate generation, which corun's own output describes as
  "about one core-hour". That phase parallelises independently of `JOBS`.
  Peak memory was only 2.3 GB, so it did no harm here, but it means the
  memory ceiling during certificate generation is not something `JOBS`
  controls. Watch it on the next run.
- **Peak memory sampling works.** 2.3 GB observed from `/proc/meminfo`,
  against a `Maximum resident set size` of 0.8 GB from `/usr/bin/time` —
  which is the single largest process and, as expected, understates a
  parallel pool.

Wall-clock for the whole run was 57 minutes, most of it Mathlib cache
decompression and toolchain install rather than the 5 minutes of `build.sh`.
Budget for that on a first run of the other port too.

## Build attempt 2 — corun1024, 2026-09-27: **clean**

Run [36336993686], `JOBS=4`, `memory_gb=20`, self-hosted runner (WSL2, 25 GB
share). **821/821 modules, exit 0, 2 h 00 m 12 s.** Zero module failures.

### Axioms — the question that could have sunk the recommendation

```
'FourColor.fourColorTheorem' depends on axioms: [propext, Classical.choice, Quot.sound]
```

and from corun's own `scripts/check.sh`:

```
THEOREM PROVED: FourColor.fourColorTheorem : FourColor.FourColorTheorem
  depends only on [propext, Classical.choice, Quot.sound]
checked 115342 FourColor declarations: no sorries, no extra axioms
anti-vacuity audit: negative controls pass
```

Exactly the three standard axioms of classical Lean, and nothing else. No
`sorryAx`, no `Lean.ofReduceBool` (which is what `native_decide` would have
introduced, putting the compiler in the trusted base). The source reading in
the statement review said there was no `sorry` and no compiled evaluation;
the kernel now agrees, across all 115,342 declarations rather than the
handful a human can read.

The anti-vacuity audit passing is the part worth dwelling on: it is a
kernel-checked statement that corun's *checkers* are not degenerate — that
`theRedpart` is not constantly `true` and the quiz tree is the real data.
Sound and vacuous is the failure mode this program's trust rule exists to
catch, and corun catches it mechanically.

### Cost

| | |
| --- | --- |
| Wall clock | 2 h 00 m 12 s at `JOBS=4` |
| Total work | 7.9 core-hours (corun's own estimate, borne out) |
| `build_pool.py` prediction | 135 min at 4 jobs — it was accurate |
| Peak single process | **20.2 GB** (`/usr/bin/time` max RSS) |
| Peak system-wide | 18.9 GB (sampled every 5 s from `/proc/meminfo`) |
| Modules | 821, none failed |

**The 20 GB module is real.** corun's warning was not conservative: one
process reached 20.2 GB, in a 25 GB WSL2 share. That leaves under 5 GB of
headroom, so the `memory_gb=20` budget should not be raised, and `JOBS` above
4 is not obviously safe — the risk is not the average module but that one.

Note the sampler *understated* the peak (18.9 vs 20.2 GB): a 5-second
interval can miss a spike. For a hard ceiling, trust `/usr/bin/time`'s max
RSS; the sampler is for the shape of the run, not its worst moment.

### Two bugs in my own harness, both now fixed

- **The run is marked `failure` despite the build succeeding.** The
  orphan-sweep step I added runs under `bash -e` with `pipefail`, and its
  first pipeline greps for orphaned processes — which, on a clean run, match
  nothing, so `grep` exits 1 and kills the step. A cleanup step invented to
  handle a failure mode manufactured a false one.
- **The resume never worked.** `actions/checkout` cleans the workspace at
  the start of every job, so the `port/` directory from the previous run was
  deleted before the resume check could see it. That is why the reducibility
  certificates were regenerated despite `fresh` being off. The port checkout
  now lives in `$HOME/4ct-port-cache/<port>`, outside the workspace.

Neither affects the result above: the build, the axioms and the audit all
ran before the sweep, and a full rebuild is if anything the stronger
evidence.

## Build attempt 3 — RBarish, 2026-09-27: **clean**

Run [36350029344], `JOBS=4`. **Exit 0, axiom check passed.**

```
'FourColor.RealPlane.four_color' depends on axioms: [propext, Classical.choice, Quot.sound]
```

and `scripts/check_challenge_sync.py`:

```
OK: Challenge.lean and FourColor/RealPlane.lean are in sync
```

So the statement-only spec and the definitions the proof actually uses are
identical, mechanically verified. That is a different guarantee from
corun's audit and a valuable one: it closes the gap between "the statement
we published" and "the statement we proved".

### Both ports side by side, measured

| | corun1024 | RBarish |
| --- | --- | --- |
| Axioms of the final theorem | `propext, Classical.choice, Quot.sound` | `propext, Classical.choice, Quot.sound` |
| Wall clock, from scratch | **2 h 00 m** | **~22 min** (7 m 29 s + 14 m 13 s resumed) |
| Peak single process | **20.2 GB** | **3.5 GB** |
| Peak system-wide | 18.9 GB | 6.4 GB |
| Built tree on disk | 8.0 GB | 8.0 GB |
| Declaration-wide audit | 115,342 declarations, no sorries, no extra axioms | none |
| Anti-vacuity | checkers are not degenerate; 4 colours genuinely needed | planarity predicate discriminates (`Examples.lean`) |
| Statement/proof sync check | none | `check_challenge_sync.py` |
| Mathlib topology bridge | `RealPlaneMathlib.lean` | none, by design |
| Distance to our pin | `v4.34.0-rc2`, forward one patch | `v4.35.0-rc2`, back one minor |

### The new fact that matters most

**RBarish peaks at 3.5 GB where corun peaks at 20.2 GB.** That is not a
marginal efficiency difference; it changes what hardware the program needs.
A 3.5 GB build fits a GitHub-hosted runner. A 20.2 GB build does not, and
cannot be made to.

If RBarish were the base port, `lean-build` could run on GitHub-hosted
runners and the self-hosted machine would stop being on the critical path
for workstream A. Given that today the self-hosted runner filled its disk,
crashed its listener, flapped online and offline, orphaned jobs and produced
one false red and one false green, that is worth more than it would have
been this morning.

### On `Examples.lean`

It is a real non-vacuity check, and narrower than corun's. It proves
`unitMap` is planar (genus 0) and that a `torus` hypermap is **not** planar
and not Jordan, exhibiting an explicit Moebius path — so the planarity
predicate discriminates rather than accepting everything.

What it does not cover is what corun's `Audit.lean` covers: that the
*reducibility oracle* is not constantly true, that the quiz tree is real
data, and that four colours are genuinely necessary. For a proof whose
weight rests on computation, corun's controls sit closer to the thing that
could silently be vacuous.

## What the build must still produce

`.github/workflows/port-build.yml`, run once per port, on the self-hosted
runner. For each:

- wall-clock time and peak RSS, at the `JOBS` and memory budget used;
- whether it builds clean on its **own** pinned toolchain (not ours — moving
  it is A2);
- `#print axioms` on the final theorem, pasted verbatim;
- whether the upstream's own checks pass (corun's `scripts/check.sh` and
  `Audit.lean`; RBarish's `check_challenge_sync.py` and `palomar_check.sh`);
- for RBarish, what `FourColor/Examples.lean` actually establishes.

Until that exists, the four numbered claims above rest on reading source, and
point 3 and point 4 in particular are predictions rather than measurements.
