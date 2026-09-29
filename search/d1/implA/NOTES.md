# Implementation A: ambiguities and choices

Each item gives what SPEC leaves open or where this implementation departs
from SPEC, the choice made, and why. Items 1–14 are the choices for SPEC
before Amendment 1, items 15–21 are Amendment 1, and items 22–24 cover what
was not done.

## Output format (these matter for byte agreement with Implementation B)

1. **`i` is 1-based.** SPEC §6.2 says "indexed 1…N", and the §7.5 pair rule
   produces indices 1…N.
2. **The `halffoams.jsonl` line format** is `json.dumps` with its default
   separators (`", "`, `": "`), in the key order `i, site, chain, deg, a`,
   with `\n` line ends and ASCII only. This is SPEC §7.6's template read
   literally.
   - `site` uses 0-based face positions `i, j`, as in §5.6.
   - `chain` holds only the reduction labels, from K′ down to ∅. The move
     itself is in `site`.
3. **`result.json` schema.** SPEC names the contents but not the key names, so
   I chose them:
   - `web`, `mode`, `V`, `Tait`, `N`, `N_by_move` (keys `zip`, `unzip`,
     `saddle`, `ih`), `ell`, `ell_q`, `r`, `r_q`, `beta_changes` (a list of
     `[n, β_n]`), `N_ell`, `halffoams_sha256`, `command`, `git_commit`,
     `implementation`;
   - after Amendment 1: `site_order`, `A2_unzip_block`, `A2_prefix_N_e` and
     `A3_events`.

   `ell_q` and `r_q` map degree (a decimal string) to count, with nonzero
   entries only. The file is written with `json.dumps(sort_keys=True,
   indent=2)` plus a final newline. Implementation B will probably pick other
   names, so a key-by-key comparison will be needed unless the schema is
   fixed centrally. **Decision for Gabriel or the coordinator.**
4. **Timing is not in `result.json`.** It is in `timing.json`, so that
   `result.json` reruns byte-identically (house rule). SPEC §11 allows
   `result.json` to differ in timing; I avoided the difference altogether.
5. **`git_commit`.** The task forbids git commands, so the field is
   `"unknown"` unless `D1_GIT_COMMIT` is set. The committed files say
   `"unknown"`.
6. **`halffoams.jsonl` is stored gzip-compressed**, with mtime 0 and level 9,
   because the uncompressed files total 122 MB. `halffoams_sha256` in
   `result.json` and the table in README.md are digests of the
   **uncompressed** bytes. `D1_KEEP_JSONL=1` writes the raw file too.
7. **`command`** is recorded as `python3 run_all.py --web W --mode B19`, the
   exact per-web invocation that the full run's driver makes. It contains no
   absolute path, so it is machine-independent.
8. **N_ℓ(ours)** is the first n with β_n = β_N, where β_0 = 0.
   `beta_changes` lists every n at which β_n ≠ β_{n−1}.

## Data

9. **Appendix A was transcribed into `d1a/webdata.py`.** SPEC §8 speaks of
   files that both implementations load, but none exist and I may write only
   inside `implA/`. The transcription is checked on load against:
   - α being a fixed-point-free involution;
   - Euler's formula;
   - the face-size multiset;
   - |Aut|, counted as map automorphisms including reflections;
   - Tait;
   - the §8.4 outer-face vertex cycles.

   All match. A shared file would remove this risk.

## Algorithms

10. **REBUILD when a single operation closes several join chains into
    circles.** SPEC does not order the new circles. I number them in the
    order of the first unresolved join pair in J. This never happened in any
    run (counter `rebuilds_creating_several_circles` = 0).
11. **Merging nominal facets (§4.3, §5.4 degenerate case).** This is
    implemented generically: nominal facets with the same bottom set are
    merged, the sheet's chi is counted once, dots are added, and tops are
    united. A partial overlap is an error. It never triggered on W1–W7 or on
    the controls, so this code path is untested by data.
12. **The pivot rule of §7.4.** Pivots are the lowest coordinate, and bases are
    kept in echelon form rather than fully reduced. The stored basis vectors
    are the original a-vectors, so that every pairing entry can be asserted
    to lie in F. Ranks do not depend on this.
13. **§9.5 Lemma 4.11 chains 2 and 3.** "The face containing both new/joined
    edges" is taken to be the unique face of K₁ that contains a dart of each
    edge. Uniqueness is asserted, and the two positions are sorted into
    i < j. For chain 5, "36 pairs" is read as the number of (t₂, t₀) pairs
    in the Boolean product. All five chains give exactly SPEC's numbers.
14. **§9.1 row 6** was run on circle, two circles, theta, K4, prism3, cube,
    prism5 and W1. Row 7's seam triples contain a repeated facet, and such a
    foam evaluates to 0 immediately.

## Amendment 1 (applied 2026-09-29, on the coordinator's instruction)

15. **A1 applied.** In B19 mode the order is Unzip, Zip, Saddle, IH.
    - Within a block, "the web's stored face and edge lists" are our lists:
      faces by increasing minimum dart, edges by increasing edge id.
    - Face pairs are generated in lexicographic (i, j) order with j ≥ i+2,
      skipping (0, L−1), which is "(1, L)" in 1-based positions.
    - The ALL modes keep §6.2's order and pair set.
    - N is unchanged for every web and mode, as expected. `halffoams.jsonl`,
      its SHA-256, β_n and N_ℓ all changed, because the order changed.
16. **A2 applied.** `result.json` now reports ℓ, ℓ_q, r and r_q for three
    sets:
    - (i) the Unzip block, which in A1 order is indices 1…N_unzip (asserted);
    - (ii) the first N_e half-foams, with N_e from B19 Table 2: 6727, 5322,
      4902, 6351, 7153, 6331 and 5458;
    - (iii) the full list, in the top-level keys.

    For W2–W7 our within-block order is not Boozer's, as the amendment warns.
    All three sets give identical values for every web.
17. **A3 applied.** The counters are in `A3_events` in `result.json`, and in
    `n_table.json` for all three modes. Definitions:
    - `degenerate_square_merges`: a C4 operation whose two joins produce the
      same K′-edge.
    - `extra_circles`: circles created by joins in any operation other than a
      bigon whose two legs are one edge. That bigon is the theta case, counted
      separately as `theta_bigon_circles`, since A5 treats theta as Boozer's
      normal path.
    - `bridge_fails`: step 3 of GEN.
    - `marker_losses`: see A4 below.
    - `component_splits`: K′ has more vertex-components than K.

    I added two informational counters:
    - `boozer_distinctness_violations_{bigon,triangle,square}` count applied
      reductions that break the distinctness conditions A3 lists. For a
      non-theta bigon: 4 distinct vertices (the two bigon vertices and the far
      ends of the two legs) and 4 distinct edges. For a triangle: 6 distinct
      edges. For a square: 8 distinct edges and 8 distinct vertices.
    - `no_eligible_face_fails` counts GEN calls with no eligible face of
      length 2 to 4, which is ordinary partial-semantics failure.

    Events are counted in the count-only pass and again in the build pass, and
    the two counts are asserted equal.
18. **A4 applied, with one interpretation to confirm.** Markers are carried as
    a set, one dart per component. After an operation that deletes vertices,
    each marker's old face orbit is scanned from its minimum dart. The dmap
    images of the surviving darts give, for each component of K′ they reach,
    the first such dart. If none survives, the result is a FAIL (counted as a
    marker loss).
    - **Interpretation:** if every vertex of the marker's component is
      deleted, which happens exactly when a theta component becomes a circle,
      the marker is dropped silently and this is not a FAIL. A4 read
      literally ("its face disappears entirely") would FAIL every theta
      removal and destroy all the counts. A5 says Boozer removes a theta
      component in one step, so this is his normal path. Counted as
      `components_vanished_with_marker`.
    - **Nested components:** a component split off with no surviving
      outer-face dart (a split not through the outer region) would stay
      unmarked. This is counted, but it never happens. In fact no component
      split happens at all in B19 mode on W1–W7, so the set rule reduces to
      the single-marker rule on this data, and N is unchanged.
19. **A3 findings that matter for reading the N comparison.**
    - **W7:** 2 bridge FAILs and 4 square eliminations violating B19's
      distinctness conditions. All of them occur below the two Saddle sites
      `["saddle", 49, 1, 4]` and `["saddle", 49, 2, 5]`, each of which still
      contributes 228 half-foams.
    - **W1–W6:** no event of A3's list.
    - No web has a degenerate-square merge, an extra circle, a marker loss or
      a component split.
20. **A5:** kept §5.1/§5.2's theta convention. The dots stay on the bowl, and
    the circle cup gets 0–2 dots.
21. **A6:** kept §6's face rule (smallest minimum dart). This is a known
    difference from Boozer's rule ("first eligible face in his current list").
    It cannot change N, and under partial semantics it could in principle
    change the span. The ranks agree with B19 anyway.

## Scope decisions

22. **Modes.** SPEC §6.4 says to report all three modes for every web. The
    task instructions limit this stage to B19 mode for W1–W7 and forbid any
    enlarged dodecahedron search. So STRICT-ALL and PARTIAL-ALL are
    implemented and fully exercised on the controls (§9.4, §9.5), but on
    W1–W7 they were run count-only (N and the events, in `n_table.json`, all
    matching §6.4). Their ranks were not computed. `run_all.py` refuses
    `--mode` other than B19.
23. **Optional items not implemented:** the §9.2 KM-rules evaluator, §9.7
    (KM's colouring half-foams), the graded Smith form, orientability sign
    propagation, and the §8.3 plantri/fullgen re-identification.
24. **Runtime.** SPEC §10 item 16 suggests a compiled language. That was not
    needed: pure Python with bit-parallel colour planes runs W7 in about 40 s.
    Colour codes {1,2,3} make the third colour of a seam the XOR of the other
    two.
