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

## Phase 2b (SPEC Amendment 2, branch d1/phase2b, SPEC commit b400a9b)

Amendment 2 was read in full, including §A2.13 (Gabriel's decisions). Only the
mandatory families (F0, KM, KMd, T2R, T2, T3s) and the §A2.9 controls are run;
`a2run.py` refused T3 and T4s (T3 was enabled later, items 40–46). The items below are the points where Amendment 2
left a choice. Where the choice affects a byte-compared file, it is marked
**[compared]**; B may have chosen differently, so these need reconciling.

25. **`expanded_nodes` levels [compared].** Level 0 is W1 itself and is
    counted as `"0": 1` in every tree family, including T3s, where only s0 is
    taken from W1's sites. So:
    - F0 `{"0": 1}`, T2R `{"0": 1, "1": 180}`, T2 `{"0": 1, "1": 60}`,
      T3s `{"0": 1, "1": 1, "2": 87}`.
    - KM and KMd have `"sites": {}` and `"expanded_nodes": {}`.
26. **`sites` for T3s level 1 [compared]** counts only s0 (one Unzip site,
    outcome IRREDUCIBLE). For every other tree family, level 1 counts all 300
    sites of W1.
27. **KMd and step 2 [compared].** KMd "retains all degrees", but step 2 (A3
    check, novelty, stops) is applied only to members whose degree is in RET,
    i.e. the 20 undotted members. Lemma 2(b) puts only degrees ≤ −3 with
    d ≡ 3 (mod 6) in A3; applied to degree −1 members, the A3 check would stop
    KMd at its second member for no mathematical reason. All 58 500 members
    are still written to `h.jsonl`, counted in `processed`, and used for the
    ranks. `a3_violations` counts RET members only.
28. **F0's common keys [compared].** Step 2 does not apply to F0 (it is the
    start state). F0's `result.json` therefore has `processed` = N = 11 880,
    `novel` = `aut_novel` = [], `a3_violations` = 0, `stop` = `EXHAUSTED`,
    and `final` = the start state (dimU 9, ℓ₋₃ 9, ℓ₃ 9, ℓ 58). F0 also gets
    a `pairsample.tsv`, with i ranging over all F0 members.
29. **`processed` [compared]** counts the member that triggers a stop. No stop
    fired, so this was not exercised.
30. **Pair-sample order [compared].** First the min(1000, N_ret) k-sample lines
    in k order; then, for each novel member in order, one line per C3 member
    in C3 order. Duplicate pairs are kept. Aut-closure images are not
    members, so they are not in `pairsample.tsv`. A still evaluates each novel
    image directly against every C3 member, using the relabelled half-foam
    g(H). No novel member occurred, so only the first part is present.
31. **Aut closure (T3s).** It runs over the novel members of the main pass only
    (images are not closed again, since g·(g′·a) = (gg′)·a is already among the
    images), and `aut_novel` records only images that were novel.
32. **`union.json` [compared] schema, my choice:**
    - `amendment`, `web`, `family` ("union"), `order`, `novel` (a list of
      `[family, i, g, deg, dimU, ell_m3]`), `a3_violations`, `start`, `final`,
      `stop`;
    - T3s's novel Aut images are included (with their g), after its main-pass
      novel members.
33. **Control outputs [compared] schema, my choice.**
    - C0, C4, C5, C6 and C8 write `result.json` in `<web>/A2/ctl-<name>/`:
      C4 in `prism5/` and `cube/`, C5 in `W2/` and `W3/`.
    - C4 and C5 use the tree-family keys plus `baseline`, `combined` (both
      {N, ell, ell_q, r, r_q}), `span_violations` and `pass`.
    - Their `pairsample.tsv` takes i over the family members and j over the
      **baseline** members (1-based), with the same k rule. SPEC defines the
      sample only for W1 families.
    - C8 holds `KMd` (alone) and `F0_union_KMd`.
    - C1, C2 and C3 are checks on the family runs. C3 is asserted inside every
      run: a count mismatch aborts that run. C1 and C2 are summarised with the
      ledger in `out/A2-summary.json`, which is not compared.
34. **Certificates [compared].** No stop fired, so no `certificate.json` was
    written. The code path exists but is untested by data. My reading of
    "the same construction" for the ±1 blocks:
    - rows = the F0₋₁ members, in F0 order, whose p-vectors (β against a
      greedy GF(4)-independent subset of F0₁) enter an F-span;
    - columns = the first F0₁ members that raise the column rank.
35. **Step 3 ℓ₃** uses every F0₃ member (3 150) as a row, not a basis.
36. **Budget rule.** The "estimate" of a run is the upper end of A's CPU range
    in §A2.10. The 3× stop is enforced on process CPU time during the main
    pass. For C4 + C5 I split the 2 h estimate as prism5 20 min, cube 10 min,
    W2 45 min and W3 45 min.
37. **Committed files (§A2.13 item 4).** The committed files are:
    - `result.json`, `pairsample.tsv`, `run.json`, `novel.jsonl` (empty
      here), `union.json`, `A2-summary.json` and `A2-SHA256SUMS.txt`.

    The `h.jsonl` files are **not** copied into the repository. They stay in
    WSL (`~/d1A/p2b/…`); their digests are `h_sha256` in each `result.json`
    and are also listed in `A2-SHA256SUMS.txt`. The Phase 2 files under
    `out/W*/B19/` (including `halffoams.jsonl.gz`) are left as they were.
38. **GEN as a tree.** For Phase 2b, GEN_STRICT is built as a tree of
    reductions (`d1a/tree.py`). Leaf degrees come without foams, and foams
    are composed only for retained leaves, memoised within one tree.
    - The F0 run asserts that this reproduces Phase 2's STRICT-ALL `generate`
      exactly: same sites, chains, degrees and a-vectors, member by member.
    - No GEN memoisation across webs is used.
39. **No shared counting code.** The count-only pass of every family is my
    own code. C3 matches every number in §A2.5 and §A2.9, including T2's
    per-first-move uniformity and the T3s level-3 counts for
    `["unzip", 18, 1, 2]`.

## Phase 2b, optional T3 (Gabriel's go, 2026-09-30; branch d1/phase2b-t3)

T3 is "T3s without the symmetry reduction: all 60 bigon moves as M1" (§A2.5).
T4s is still refused.

40. **T3 counts and keys [compared].**
    - `sites` level 1 counts all 300 sites of W1 (0 / 60 / 60 / 180), as for
      T2 and T2R; only T3s counts s0 alone (item 26). Levels 2 and 3 are
      summed over the 60 subtrees.
    - `expanded_nodes` = `{"0": 1, "1": 60, "2": 5220}` (item 25's
      convention).
    - This is what a single sequential walk with M1 free gives.
    - No Aut closure (§A2.7 step 2.4 is T3s/T4s only), so `aut_novel` is `[]`.
    - `h.jsonl` is not written (3 715 620 > 2 000 000 lines, §A2.8). Its
      SHA-256 is computed in the parent, in family order, and reported as
      `h_sha256`. The decision to write it is taken from `N_retained`; if a
      stop left ≤ 2 000 000 processed members, the file would still be
      missing (the run prints a note). Not exercised.
41. **Parallel run, identical to a sequential one.** Each of the 60 subtrees
    (M1 fixed) runs in a worker process (forkserver pool, at most 8). A worker
    returns its subtree's `h.jsonl` lines (with global i), its counts, the
    sample values it was asked for, and its *candidates*: the members whose
    a-vector lies outside A3 (only the first), or outside U0 + the span of the
    subtree's earlier candidates.
    - Any other member is already in the family's current U at its turn: U
      always contains U0 and every earlier processed vector. So step 2
      returns "not novel" for it, with no side effect.
    - The parent runs step 2 on the candidates in family order and hashes the
      lines in order. On a stop at i, only lines 1…i are hashed and
      `processed` = i. This reproduces the sequential computation exactly.
    - The main pass asserts, per subtree, that its counts equal the
      count-only pass.
    - Checked on the first 3 first moves (`--first-limit 3`): 1 worker and 8
      workers give byte-identical `result.json`, `pairsample.tsv`,
      `novel.jsonl` and `h.jsonl`. Lines 1–61 927 equal the T3s `h.jsonl` of
      the mandatory run byte for byte.
42. **Sample.** The min(1000, N_ret) k-pairs are assigned to the subtrees
    holding their i. Each worker evaluates its pairs directly on the glued
    closed foam and asserts equality with β. Every candidate is also
    evaluated directly against the C3 members in the worker; the values are
    used only if the parent finds it novel. On an early stop, the sample
    indices change with `processed`; the missing pairs are then computed by
    re-walking the subtrees concerned. That path is not exercised.
43. **Budget and memory rules for T3.**
    - Estimate: 60 × 69.4 s CPU, the measured T3s main pass on one worker, so
      4 164 s CPU and ⌈60 / J⌉ × 69.4 s wall.
    - The main pass stops at 3× the wall estimate, at 3× the summed worker
      CPU, or at 4 hours.
    - A thread samples the summed RSS of the parent, the forkserver and the
      workers every 0.5 s. The run aborts above 3 400 MB; `peak_rss_mb` in
      `run.json` is that sampled sum.
    - `--jobs` above 8 is refused.
44. **`union.json` [compared].** The order is KM, T2R, T2, T3s, then T3 when
    its `result.json` exists (§A2.7 step 4: "then the optional ones").
    `order` in `union.json` lists T3.
45. **Summary and digests.** `out/A2-summary.json` and
    `out/A2-SHA256SUMS.txt` were regenerated with the T3 files and the new
    `union.json`. The rerun reproduced every other digest in the file,
    including the uncommitted `h.jsonl` files of the mandatory run kept in
    WSL. The only changes are the `union.json` line and the four new T3
    lines; the summary gained the T3 ledger entry.
46. **What was read for T3.** `CLAUDE.md`, `search/d1/SPEC.md` (Amendment 2,
    §A2.4–§A2.13), `search/d1/README.md` and my own files, including my WSL
    outputs under `~/d1A`. Not read: `implB/`, `~/d1B`, `compare.py`, any
    `chk/` directory, the scratchpad. Seen incidentally, not opened: `git
    status` listing `compare.py` and `implB/a2run.py` as modified, and B's T3
    test command line in two WSL process listings.
