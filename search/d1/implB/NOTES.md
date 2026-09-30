# Implementation B: notes on ambiguities and choices

These are the places where `search/d1/SPEC.md` left a choice open, or where I
had to interpret it. Each item gives the choice made and the reason. Nothing
here is a result.

**Amendment 1 applied.** SPEC Amendment 1 (2026-09-29, A1–A6) was received
from the coordinator mid-task and is implemented: the A1 site order in B19
mode, the A2 subset ranks, the A3 event counts, the A4 marker sets, and the
A5/A6 conventions (both kept as SPEC says). All W results in `results/` were
produced after Amendment 1 was applied.

## Output format (SPEC 7.6)

1. **`halffoams.jsonl` serialisation.** SPEC shows the key order and the spacing
   `{"i": i, "site": ..., "chain": [...], "deg": d_i, "a": "..."}` but does not
   name a serialiser. Choice: keys in exactly that order, Python
   `json.dumps` default separators (`", "` and `": "`), ASCII, one `\n` per
   line, no trailing blank line, `i` 1-based. `site` is a JSON list
   (`["unzip", 0, 0, 2]`). If A serialises differently, the SHA-256 values
   will differ even when the content agrees; compare the parsed content first.
2. **`chain`** lists only the reduction labels from K′ down to ∅. It does not
   include the move label, which is already given in `site`.
3. **`result.json`**: `json.dumps(sort_keys=True, indent=1)` plus a newline.
   The key names are mine, because SPEC gives only descriptions: `web`,
   `mode`, `V`, `Tait`, `N`, `N_by_move` (`zip`, `unzip`, `saddle`, `ih`),
   `ell`, `ell_q`, `r`, `r_q`, `beta_changes` (list of `[n, beta_n]`),
   `N_ell_ours`, `halffoams_sha256`, `command`, `git_commit`,
   `implementation`. The degree→count maps use string keys and leave out zero
   entries.
4. **`git_commit`**: I was told not to run git, so this is `"unrecorded"`
   unless the command is given `--git-commit`.
5. **Extra files, outside SPEC 7.6:**
   - `a2_subsets.json` (Amendment A2);
   - `a3_events.json` (A3);
   - `remark42.json` (W1 only: ℓ for each move type alone, B19 Remark 4.2);
   - `pairsample.tsv` (the SPEC 7.5-2 sample pairs `i j value`, kept for the
     later comparison with A's direct closed-foam values);
   - `timing.txt` (not byte-reproducible, and deliberately kept out of
     `result.json` so that `result.json` reruns byte-identically).

## Mode T specifics

6. **Only reachable columns are carried.** GEN is computed top-down, starting
   from Tait(K) of the target. At each node, the Tait colourings of the
   smaller web that are needed are exactly those reached by a local
   colouring from a needed colouring above: the support of T_C. A column
   outside that set cannot influence any entry at the target, because
   T_C(t′, t) = 0 unless some local colouring connects t′ to t. So Tait
   colourings are enumerated by search only for the target webs (and the
   Lemma 4.11 chain webs). A check that every derived colouring is a proper
   Tait colouring runs by default (`--no-check` turns it off). It passed in
   every run.
7. **Order of intermediate Tait colourings**: the sorted list of the reached
   subset. SPEC allows any internal order.
8. **Identity sheets / e(C,c).** I use the §4.6 formula literally. As a side
   remark, the constant −nv + (Vb−Vt)/2 contributes −3·const ≡ 0 (mod 3), so
   e(C,c) = Σ_g (c(g)−1)(dots(g) − chi(g) + #bot-intervals(g)) mod 3. This is
   used only in the cup test of §9.4.
9. **§7.5 item 3** (degree recomputed from facet–seam data) does not apply,
   because B has no facets. Every record's degree is instead recomputed from
   its record data with the §4.3 formula and asserted against B19 Table 1.
10. **§7.5 item 2**: B cannot compute direct closed-foam values. On the 10 000
    sample pairs it asserts that β(a_i, a_j) ∈ F, and that β = 0 whenever
    d_i + d_j < 0 or 6 ∤ d_i + d_j. The values are saved in `pairsample.tsv`.
11. **Gram entries in F.** Pairing matrices are always built between
    original a-vectors (an independent subset), never between GF(4) echelon
    rows. So every entry is a genuine half-foam pairing and is asserted to lie
    in F. Ranks are then GF(2) ranks, which equal the GF(4) ranks.

## REBUILD and records

12. **Order of new circles** when several join chains close up: in the order
    of the first join of each chain in J. SPEC says only "appended". This
    never happened in any run (`extra_circle_other` = 0).
13. **Facet merging.** Nominal local facets are merged when they share a
    bottom item (the SPEC §4.3 rule) or a top item (my addition, for safety).
    An assertion fires if a merge is not the shared-sheet case. In the runs,
    no merge happened at all (`degenerate_square_merge` = 0).
14. **Lemma 4.11 chains 2 and 3**: "the face containing both new/joined
    edges". Exactly one face of K₁ qualified in each case, and the positions
    (i < j) of the two darts in its canonical form were used.

## Amendment 1

15. **A1 pair rule, 0-based.** Amendment 1 skips "(1, L)", which is 1-based.
    In SPEC's 0-based positions this is (0, L−1). The rule used: i < j,
    j ≥ i + 2, (i, j) ≠ (0, L−1), in lexicographic order. B19 mode only;
    STRICT-ALL and PARTIAL-ALL keep the §6.2 order and all pairs (the prism5
    and cube controls use STRICT-ALL, so they are unchanged). Within blocks,
    the "stored face and edge lists" are faces by increasing minimum dart and
    edges by increasing edge id.
16. **A4, "marker lost".** Amendment 1 says a lost marker ("its face
    disappears entirely") is a FAIL. The ambiguous case is a marked
    component all of whose vertices are deleted, e.g. a theta component
    whose outer bigon is marked, reduced through another bigon to a
    vertexless circle. There, no dart of the outer face survives, but the
    outer region itself does not disappear: it becomes one side of the new
    circle, and no face choice is ever needed again for that component.
    Choice: drop the marker silently and count the event as
    `marker_component_vanished`. A FAIL (`marker_loss_fail`) is raised only
    when no dart of the orbit survives but the component still has vertices.
    Reason: this is exactly the old §3.7 behaviour in the only case that
    occurs, and it reproduces all seven Table 2 N values. I also tested the
    other reading, with a throwaway run that is not part of the deliverable:
    treating the vanished case as FAIL gives **N = 0** for W1 and for W2.
    Every B19-mode reduction ends in a theta component whose outer face is
    marked, so every branch would fail. So that reading cannot be what
    Amendment 1 means. In all seven webs, `marker_loss_fail` = 0, so under my
    reading the FAIL branch never triggers. **Flag this for a decision if A
    reads it differently.**
17. **A4, new components.** For each old marker, the candidates are dmap(m)
    (if m's vertex survives) followed by the surviving darts of its old face
    orbit in orbit order from the orbit's minimum dart. The first candidate
    lying in each component of K′ becomes that component's marker. A
    component that gets no marker has all of its faces eligible, and this is
    counted. Neither case occurred (`component_split` = 0,
    `unmarked_component_created` = 0).
18. **A3 event definitions**, counted once per occurrence in the GEN recursion
    over all sites (a node reached through a disk or bigon step is visited
    once, not once per dot variant):
    - `degenerate_square_merge`: a square record whose two S sheets merged;
    - `extra_circle_theta` / `extra_circle_other`: circles created by
      REBUILD; `theta` means a bigon removed from a two-vertex component,
      which Boozer does too (A5);
    - `bridge_fail`: GEN step 3;
    - `marker_loss_fail`, `marker_component_vanished`: see item 16;
    - `component_split`: K′ has more vertex components than K;
    - `unmarked_component_created`: see item 17;
    - `no_eligible_face_fail`: GEN step 4 found no face. This is not a
      degeneracy, but it is reported for completeness;
    - `boozer_degenerate_bigon/triangle/square`: the chosen face fails
      Boozer's abort test, as I read A3:
      - a bigon that is not on a theta component, without 4 distinct vertices
        (the 2 bigon vertices plus the 2 leg ends) and 4 distinct edges;
      - a triangle without 6 distinct edges;
      - a square without 8 distinct edges and 8 distinct vertices.
19. **A3 findings.** Only W7 has events Boozer's program would abort on:
    two `boozer_degenerate_square` events, each followed by a `bridge_fail`.
    They occur at the Saddle sites `["saddle", 49, 1, 4]` and
    `["saddle", 49, 2, 5]`. Both lie in the Saddle block, beyond the Unzip
    block, so beyond N_e. With partial semantics they contribute nothing:
    the failed branch is empty. W7's N still equals Table 2's 101 970. Every
    web has many `extra_circle_theta` events, which are Boozer-legal.
    `no_eligible_face_fail` counts are W3: 5, W6: 91 and W7: 57.
20. **A2.** For every web, the three sets give identical ℓ, ℓ_q, r and r_q:
    (i) the Unzip block, (ii) the first N_e in A1 order, (iii) the full list.
    For W2–W7, N_e lies inside the Unzip block, as A2 says. As A2 warns, for
    W2–W7 our prefix need not be Boozer's, because each face's starting edge
    and direction in his data are unknown. Here the question is moot: the
    ranks were already saturated inside the prefix.

## Not done (by instruction or optional)

21. STRICT-ALL and PARTIAL-ALL were **not run on W1–W7**. Both are
    implemented (`python3 d1b.py web W1 --mode STRICT-ALL`). My instructions
    stop after B19 mode and forbid any enlarged dodecahedron search.
    STRICT-ALL was run only on the controls (prism5, cube, and GEN on the
    reducible webs).
22. Optional items not implemented: the §9.2 KM-rules evaluator, the §9.7 KM
    colouring half-foams, and the graded Smith-form cross-check of §7.3.
23. The §7.5-1 Mode G/Mode T comparison can only be done against A's files.

# Phase 2b (SPEC Amendment 2): ambiguities and choices

Amendment 2 is applied, including the decisions in §A2.13. These runs were
made: the mandatory families F0, KM, KMd, T2R, T2 and T3s, and controls
C0, C1, C2, C3, C4, C5, C6 and C8. T3 was run later (items 39–46), and
T4s after it (items 47–55). C7 compares A with B and cannot be run from B alone. No stop
criterion fired.

24. **Step 2 applies only to RET degrees.** F0 and KMd "retain all
    degrees". I read this as: every member is written to `h.jsonl` and
    enters the §7 ranks (`N`, `ell`, `ell_q`, `r`, `r_q`). Only members whose
    degree is in RET = {d ≤ −3, d ≡ 3 (mod 6)} go through the A3 check,
    novelty and stop rules of step 2. Otherwise every degree −1 member of F0
    would be an `A3_VIOLATION`, since A3 lies in degrees ≡ 3 (mod 6).
    `processed` counts all members written.
25. **`expanded_nodes` includes level `"0": 1`** (W1 itself, whose SITES are
    enumerated). KM and KMd have `"sites": {}` and `"expanded_nodes": {}`.
26. **Level-1 `sites` for T3s and T2s0 are restricted.** These families
    restrict M1 to s0, so their level-1 `sites` count only s0 (one
    IRREDUCIBLE Unzip), not all 300 sites of W1. For F0, T2R and T2, level 1
    counts all 300 sites.
27. **F0's `novel`/`start`/`final`.** These come from processing F0's own
    RET members from the F0 state. None is novel, so final = start, with
    ell 58.
28. **KMd rank fields** (`N`, `ell`, `ell_q`, `r`, `r_q`) in its
    `result.json` are for KMd alone. The ranks of F0 ∪ KMd (C8) are in
    `W1/A2/ctl-C8/result.json`.
29. **pairsample.tsv.**
    - The 1000-pair sample comes first. Then, for each novel member in
      order, come its pairs with the C3 members in C3 order.
    - Aut images of novel members have no member index, so they are not
      added.
    - The j column is the F0 index (1-based) of the F0₃ or C3 member.
    - No family had a novel member, so the second part is empty everywhere.
30. **Aut closure and union.**
    - `aut_novel` records only images that are novel.
    - `union.json` processes the novel members of KM, T2R, T2 and T3s,
      followed by the novel Aut images of T3s. KMd is left out, since its
      degree −3 members are the KM members.
    - The `union.json` schema is mine; §A2.8 does not fix it. Everything was
      empty.
31. **Step 3 recomputation.**
    - ℓ₋₃ is the GF(2) rank of the p-vectors of F0₋₃ ∪ the novel degree −3
      vectors, taken against C3.
    - ℓ₃ is the rank of the pairing matrix with rows = all 3150 F0₃ members
      and columns = a GF(4)-independent subset of those degree −3 vectors. By
      linearity the rank is the same as with all columns.
32. **dim R** = dim A3 − rank of the pairing between an F-basis of A3 (made
    of original a-vectors) and an F-basis of U0 (also original a-vectors).
    Every entry is asserted to be in F.
33. **Control outputs** (`ctl-C0`, `ctl-C3`, `ctl-C4`, `ctl-C5`, `ctl-C6`,
    `ctl-C8`) use my own `result.json` schemas; §A2.8 fixes only the family
    files.
    - C4 and C5 record span violations, plus the ranks of the baseline and of
      baseline ∪ family.
    - The C5 baseline is the Phase 2 B19-mode list in Amendment 1 A1 order,
      recomputed.
    - The C6 symmetry check writes its T2-restricted-to-s0 family to
      `W1/A2/T2s0/`.
34. **`h.jsonl` files are not committed** (A2.13 item 4). They were written
    in WSL under `~/d1B/a2out2/h/`. Their SHA-256 values are in each
    `result.json` (`h_sha256`) and in the README.
35. **KM facet-seam form.**
    - The foam is built exactly as §A2.5 describes: chi 1 for every facet,
      nv = 5, deg −3 (asserted).
    - The a-vector is evaluated by §4.5 with
      χ(H_ij) = Σ chi − nv − V/2 (§4.2).
    - Checked along the way: the 20 sets are exactly the colour classes of
      W1's 240 face 4-colourings (asserted), and the face minimum darts are
      as listed.
36. **The time estimate** in `run.json` is 45 µs per leaf (all degrees), the
    B scaling of §A2.10.
    - In the committed run (4 workers), every main pass stayed below 3× that
      estimate. The largest was T2R at 254 CPU s against 189 s estimated.
    - In an earlier, otherwise identical run with 8 workers, hyperthreading
      inflated CPU time: T2R's main pass took 586 CPU s, 3.1× the estimate.
      It still took only 75 s of wall time and stayed within the §A2.10 range
      for B (3–10 CPU min).
    - The two runs gave byte-identical `result.json`, `pairsample.tsv`,
      `union.json`, control files and `h.jsonl` files.
37. **Memoisation.** GEN is not memoised. Count-only outcomes use a
    degree-only GEN (`a2tree.gen_count`) that follows the same face choice
    and REBUILD calls as `core.gen`. The main pass asserts that its counts
    equal the count-only counts.
38. **F0 cross-check.** F0's a-vector list is asserted identical to the
    Phase 2 STRICT-ALL single-move list from `sites.generate`.

# Phase 2b, optional family T3 (Gabriel's go, 2026-09-30)

T3 is "T3s without the symmetry reduction": all 60 bigon moves as M1
(§A2.5), M2 IRREDUCIBLE, M3 REDUCIBLE and emitted, RET degrees retained, no
Aut closure (§A2.7 step 2.4 is for T3s and T4s only), so `aut_novel` is `[]`.
(T4s was implemented later; items 47–55.)

39. **Parallel units.** T3's units are its 5,220 level-2 nodes in DFS order
    (as for T3s, whose units are s0's 87 level-2 nodes). Each unit walks its
    subtree in a worker. The parent consumes unit results strictly in unit
    order, writes the h lines and does all of §A2.7 step 2 itself, so the
    output is the same as a sequential run (§A2.10). At most 4 × jobs units
    are in flight, which bounds memory. This bounded window replaced
    `Pool.imap` for every family; the order of results is unchanged. After
    the change, `family T2` and `family T3s` (8 workers) reproduced the
    mandatory run's `result.json`, `pairsample.tsv` and `h.jsonl` byte for
    byte, and so did F0.
40. **h.jsonl.** T3 has 3,715,620 retained members, more than 2,000,000, so
    `h.jsonl` is not written (§A2.8). The SHA-256 of the lines is computed on
    the fly, in order, and is `h_sha256`. `run.json` also records one digest
    per first move (`h_sha256_by_first_move`: label, first i, number of
    lines, SHA-256). `--hprefix N` writes the first N lines to a separate file;
    the full run used N = 61,927 for the s0 check (item 42). That file is not
    committed.
41. **Count-only checks.** Besides the §A2.5 T3 row (level 3, 245,149,920
    leaves, 3,715,620 retained, expanded L1 60 and L2 5,220), the run checks
    level 1 against the F0 row (0 / 60 / 60 / 180) and level 2 against the
    T2 row (240 / 4,260 / 5,220 / 11,400); these are the same sites. It also
    checks that each of the 60 first moves has exactly T3s's numbers:
    level 3 548 / 6,974 / 9,508 / 17,362, 87 level-2 nodes, 4,085,832 leaves
    and 61,927 retained. On any mismatch T3 stops before the main pass.
42. **Checks made before the full run.**
    - `--m1-limit 3` (a test option: only the first 3 first moves) run with
      1 worker and with 8 workers gave byte-identical `result.json`,
      `pairsample.tsv`, `h.jsonl` (185,781 lines) and per-first-move
      digests. Its result.json fails the count check by design, since only
      3 of the 60 subtrees are included.
    - The first 61,927 lines (the s0 subtree) are byte-identical to T3s's
      `h.jsonl` from the mandatory run (`~/d1B/a2out2/h/W1-A2-T3s-h.jsonl`);
      checked with `cmp` in the `--m1-limit 3` runs and again in the full run.
43. **Budget guard (§A2.10, §A2.13).** The estimate is 45 µs per leaf
    (11,032 CPU s for T3), and a wall estimate of that divided by
    min(jobs, 4). During T3's main pass the parent samples the CPU time of
    itself and its workers from `/proc` every 10 units, and stops the pass
    if CPU exceeds 3 × the estimate or wall time exceeds
    min(3 × the wall estimate, 4 h − 10 min − the count-pass wall time).
    It samples the summed RSS of all its processes in the same way
    (`peak_total_rss_mb_sampled` in `run.json`); `peak_rss_mb` is still the
    largest single process.
44. **Pair sample storage.** Retained a-vectors are kept packed, 15 bytes
    each (56 MB for T3), instead of as Python tuples. The sample is the same.
45. **Union with T3.** `family T3` redoes §A2.7 step 4 with the order KM,
    T2R, T2, T3s, T3. The novel members of the mandatory families are read
    from their `result.json` under `--prior`; all were empty, so the union
    processes T3's novel members only. If any mandatory family had novel
    members the command refuses and asks for a full rerun.
46. **What I read for T3.** Only `search/d1/implB/`, `search/d1/SPEC.md`
    (Amendment 2), `CLAUDE.md` and my own WSL files under `~/d1B`. I did not
    open `search/d1/implA/`, `~/d1A`, `search/d1/compare.py` or any `chk/`
    directory. Two things passed in front of me without being opened: a
    `git diff --stat` listed `search/d1/implA/a2run.py` and
    `search/d1/compare.py` as modified in the working tree (names and line
    counts only), and a `ps` listing on the shared WSL machine showed the
    command line of implementation A's concurrent T3 test run.

# Phase 2b, optional family T4s (Gabriel's go, 2026-09-30: "Run T4s")

T4s is paths (s0, M2, M3, M4) with M1 = s0 = `["unzip", 0, 0, 1]`, M2 and M3
IRREDUCIBLE (expanded), M4 REDUCIBLE and emitted, RET degrees retained
(§A2.5), followed by the Aut closure of the novel members (§A2.7 step 2.4).

47. **Units.** T4s's units are its 9,508 level-3 nodes in DFS order. The
    parent enumerates them (classifying the 1 + 352 + 34,392 sites of levels
    1–3 with the degree-only GEN, about 25 s), each worker walks one level-3
    node's subtree, and the parent consumes the results strictly in unit
    order and does all of §A2.7 step 2 itself, as for T3 (item 39). The 87
    level-2 nodes would have been too coarse for 8 workers: their subtrees
    range from 1.5M to 11.3M leaves, about 11 units per worker, so the tail
    would have been badly balanced.
    At most 4 × jobs units are in flight.
48. **Count-only checks.** Level 1 is s0 alone (0 / 0 / 1 / 0), level 2 the
    T2s0 row (4 / 71 / 87 / 190), level 3 the T3s row (548 / 6,974 / 9,508 /
    17,362), level 4 and the totals the §A2.5 T4s row; expanded L1 1, L2 87,
    L3 9,508. On any mismatch the command stops before the main pass. All
    matched. §A2.5 gives no per-move split for T4s; ours is in the README
    and in `result.json` (`sites["4"]`). The count-only log also lists, for
    each level-2 node, its level-3 nodes, leaves and retained members.
    The first two level-2 nodes (`["zip", 9]` and `["zip", 60]`) have no
    retained member at all.
49. **h.jsonl.** 5,300,704 retained members, so `h.jsonl` is not written
    (§A2.8). `h_sha256` is computed on the fly, in order. `run.json` has one
    digest per second move (`h_sha256_by_second_move`: label, first i,
    number of lines, SHA-256). Any novel member's h line would have been
    written to `W1-A2-T4s-novel.jsonl` and logged at once, so that a
    certificate could be built from it; there was none.
50. **Skipping a-vectors of non-retained leaves (§A2.4).** At an emitting
    level, `a2tree.classify` now decides the outcome with the degree-only
    GEN first. It computes the transfer and the full GEN (a-vectors) only
    if some leaf of the site has a retained degree; otherwise the leaves
    are counted from the degree multiset. Where the full GEN is computed,
    its degree multiset is asserted equal to the degree-only one. This
    changes no output (the main pass still asserts its counts equal the
    count-only pass). It applies to every family; the regression reruns of
    item 52 cover it. Measured main-pass CPU per leaf: about 88 µs on the
    first two level-2 nodes before the change; after it, 29 µs on the first
    three and 34 µs over the full T4s main pass (T3, before the change:
    60 µs).
51. **No chunking.** The count pass and a 3-level-2-node prefix put the full
    run at about 1.2–1.5 h wall with 8 workers, well under the 3.5 h at
    which the run would have been split. It took 1 h 15 min. The budget
    guard of item 43 was in force (stop at 3 × 36,362 CPU s, or at
    12,701 s wall so that the run stays under 4 h minus 10 min); the main
    pass used 0.75 × its estimate. So no chunked mode was written or
    tested.
52. **Checks made before the full run.**
    - Determinism: `--l2-limit 3` (a test option: only the units below the
      first 3 level-2 nodes; the first 2 have no retained member, so 2
      would have tested nothing) with 1 worker and with 8 workers gave
      byte-identical `result.json`, `pairsample.tsv`, `h.jsonl` (79,756
      lines; SHA-256 `e95670bd…`) and per-second-move digests. Its
      result.json fails the count check by design. The full run's digest of
      the same 79,756 lines (first entry of `h_sha256_by_second_move`) is
      the same `e95670bd…`.
    - Regression: `family T3s`, `family T2` and `family T2R` (8 workers)
      with the changed code reproduced their committed `result.json` and
      `pairsample.tsv` byte for byte, and F0's `result.json`; the `h.jsonl`
      digests are unchanged (T3s `5f31c4db…`, T2 `8c2c96ce…`, T2R
      `f211ed2c…`, F0 `f88b9948…`).
53. **Aut closure.** Same code as T3s: for each novel member in order and
    g = 1…119, g·a is processed as in step 2 items 1–3. T4s had no novel
    member, so nothing was processed and `aut_novel` is `[]`.
54. **Union with T4s.** `family T4s` redoes §A2.7 step 4 with the order KM,
    T2R, T2, T3s, T3, T4s. The earlier families' novel members come from
    their `result.json` under `--prior` (a copy of the committed
    `results/`); all were empty, so the union processes T4s's novel members
    and their novel Aut images only. The union is `EXHAUSTED` at dim U 9,
    ℓ₋₃ 9, ℓ 58.
55. **What I read for T4s.** Only `search/d1/implB/`, `search/d1/SPEC.md`
    (Amendment 2), `CLAUDE.md` and my own WSL files under `~/d1B`. I did
    not open `search/d1/implA/`, `~/d1A`, `search/d1/compare.py`,
    `search/d1/compare-result.txt` or any `chk/` directory. One thing passed
    in front of me without being opened: a `ps` listing on the shared WSL
    machine showed the command line of a concurrent implementation-A
    process (a T4s test run with `--l2-limit 3` and a `--seqcheck` flag).
    After that I listed only my own processes. And `git status` listed
    modified or new files under `search/d1/implA/` (`NOTES.md`,
    `README.md`, `a2run.py`, `d1a/tree.py`, `out/A2-SHA256SUMS.txt`,
    `out/A2-summary.json`, `out/W1/A2/union.json`, `out/W1/A2/T4s/`):
    names only.
