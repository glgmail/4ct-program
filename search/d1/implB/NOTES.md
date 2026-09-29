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
