# D1 Phase 2, Implementation A (Mode G)

This directory implements `search/d1/SPEC.md`, **including Amendment 1**
(A1 site order in B19 mode, A2 three reported sets, A3 event counts, A4
outer-face dart sets), as Implementation A: it builds
half-foams explicitly as facet–seam data (SPEC §4.2–4.4). It computes their
a-vectors by enumerating colourings directly (§4.5), and on a fixed sample of
pairs it evaluates the glued closed foams directly (§4.4, §7.5). It was written
from SPEC alone. See "What was read" below.

Status: this is one of the two implementations the house rules require.
Nothing here is a result until Implementation B agrees byte for byte (SPEC
§11) and Gabriel has reviewed it.

## Command

```
cd search/d1/implA
python3 run_all.py            # controls, N table (3 modes), W1..W7 in B19 mode (sequential)
python3 run_all.py --jobs 4   # the same, with the webs run in 4 parallel subprocesses
python3 run_all.py --controls # controls only
python3 run_all.py --web W4   # controls, then one web
```

Requirements: Python ≥ 3.10 (it uses `int.bit_count`), standard library only.
There is no randomness anywhere. `D1_GIT_COMMIT=<sha>` fills the `git_commit`
field of `result.json` (the code runs no git commands). `D1_KEEP_JSONL=1` also
writes the uncompressed `halffoams.jsonl`.

The runner stops before W1–W7 if any control fails. It also stops if the
count-only N table differs from SPEC §6.4.

## Layout

| Path | Content |
| --- | --- |
| `d1a/webdata.py` | SPEC Appendix A, transcribed, with the expected invariants |
| `d1a/web.py` | darts, faces, bridges, Tait colourings in canonical order, REBUILD (§3.4), marker (§3.7), automorphism count |
| `d1a/records.py` | the twelve elementary cobordisms (§5) as web changes plus records, with the partition and degree asserts |
| `d1a/foam.py` | half-foams, composition (§4.3), gluing (§4.4), closed-foam evaluation (§2.4), a-vectors (§4.5) |
| `d1a/gen.py` | GEN (§6.1), move sites (§6.2; A1 order in B19 mode), the modes B19 / STRICT-ALL / PARTIAL-ALL (§6.4), outer-face dart sets (A4), event counters (A3) |
| `d1a/gf4.py`, `d1a/ranks.py` | GF(4) linear algebra; ℓ, ℓ_q, β_n, r, r_q (§7) |
| `d1a/controls.py` | SPEC §9 controls plus self-checks |
| `run_all.py` | driver |
| `out/controls.txt` | control results |
| `out/n_table.json` | N, N by move type and A3 event counts, count-only, all three modes, W1–W7 |
| `out/<W>/B19/result.json` | the SPEC §7.6 result file, plus the A2 sets (`A2_unzip_block`, `A2_prefix_N_e`) and the A3 events (`A3_events`) |
| `out/<W>/B19/halffoams.jsonl.gz` | the SPEC §7.6 half-foam file, gzip-compressed (see below) |
| `out/<W>/B19/extra.json` | ℓ for each move type alone, internal statistics, SHA-256 of the .gz |
| `out/<W>/B19/timing.json` | run time and peak RSS (kept out of `result.json` so that reruns are byte-identical) |

## Methods

- **Webs.** Faces are φ-orbits (φ = σ∘α) in canonical form, sorted by minimum
  dart. Tait colourings are enumerated by backtracking over edges in edge-id
  order, then circles; this gives the canonical lexicographic order directly.
  Every Appendix A web is checked on load: α is an involution, Euler's formula
  holds, and the face-size multiset, |Aut| (map automorphisms including
  reflections), Tait and the vertex cycle of the outer face are as SPEC states.
- **Records and composition.** Each operation builds K′ with REBUILD (or with
  the α-edits of §5.6/§5.7) and a record C : K′ → K. Every record asserts:
  - the K-edges are partitioned into identity edges and top edges, and the
    K′-edges into identity images and bottom edges;
  - no K′-edge lies in two local facets after merging;
  - deg C equals B19 Table 1.

  C∘H is computed by union–find exactly as in §4.3. For every generated
  half-foam, deg recomputed from the facet data (§4.2) equals the sum of the
  Table 1 degrees.
- **a-vectors (§4.5), bit-parallel over t.** The exponent of one colouring is
  e = Σ_f (c(f)−1)·(dots(f)−chi(f)) mod 3. This is SPEC's
  Σ dots·(c−1) − χ₁₂ − 2χ₁₃: the constants −nv − V/2 inside χ_ij contribute
  3(nv + V/2) ≡ 0. Colours are stored as bit-planes (p0, p1) over all T Tait
  colourings at once:
  - a facet that owns boundary edges takes its colour from t, and agreement
    between the edges it owns is enforced;
  - a facet in a seam whose other two facets are known gets the XOR of their
    codes, since for {1,2,3} the third colour is a XOR b;
  - a row dies unless every seam is rainbow;
  - a facet that cannot be determined is branched by replicating the rows
    three times. This never happened in W1–W7.

  e is accumulated in bit-sliced mod-3 counters, and a(t) = Σ ω^e over the
  surviving rows. A second, row-wise per-t backtracking enumerator
  (`avec_slow`) is compared against it on the controls and on every 37th W1
  half-foam.
- **Closed foams (§4.4, §2.4).** Glue by union–find over owners, then
  backtrack over facets with seam propagation. Count n₀, n₁, n₂ and assert:
  n₁ ≡ n₂ (mod 2); every χ(F_ij(c)) is even; the value is 0 when deg < 0 or
  6 ∤ deg. On the 10 000 SPEC §7.5 pairs, each direct value is compared with
  Σ_t a_i(t)a_j(t).
- **Ranks (§7).** Each degree has an echelon basis of U_d. ℓ_d is maintained
  incrementally by a pairing-rank structure (pivot rows plus a kernel of row
  vectors orthogonal to all columns), so β_n is exact at every n.
  - ℓ_d and ℓ_{−d} are kept in separate structures and asserted equal.
  - At the end, every ℓ_d is recomputed from scratch.
  - r and r_q come from h(k) as in §7.3, asserting g(k) ≥ 0, Σ g = r, and
    that h is constant above the range.
  - Every pairing entry between a-vectors is asserted to lie in F.
- **Site order (Amendment 1, A1).** In B19 mode, S(K) is ordered Unzip, Zip,
  Saddle, IH. Within a block, faces are in increasing minimum dart and edges in
  increasing edge id (our stored lists). Face pairs satisfy j ≥ i+2, with
  (0, L−1) skipped. STRICT-ALL and PARTIAL-ALL keep §6.2's order.
- **Outer faces (A4).** B19 mode carries a set of marker darts, one per
  connected component; faces containing a marker are ineligible. After a
  deleting operation:
  - each marker is replaced by the dmap images of the surviving darts of its
    old face orbit, taken in orbit order, keeping the first one in each
    component of K′;
  - if none survives while the component keeps vertices, the branch FAILs;
  - if the whole component was deleted (a theta component becoming a
    circle), the marker is dropped. This is an interpretation; see NOTES.md
    item 18.

## Results (B19 mode, A1 order)

Every web took under a minute; the whole run took 2 min 13 s. Every control
passed. For each web, the three A2 sets give identical values:
- (i) the Unzip block alone;
- (ii) the first N_e half-foams in A1 order, with N_e from B19 Table 2;
- (iii) the full list.

They match B19 Tables 2–3 in every entry that can be reproduced (N, ℓ, ℓ_q,
r, r_q − ℓ_q):

| Web | Tait | N | Unzip block | N_e | ℓ (i)/(ii)/(iii) | r | ℓ_q | r_q − ℓ_q | ℓ per move type (Zip/Unzip/Saddle/IH) | N_ℓ(ours) |
| --- | ---: | ---: | ---: | ---: | --- | ---: | --- | --- | --- | ---: |
| W1 | 60 | 11 160 | 3 960 | 6 727 | 58/58/58 | 60 | 9q⁻³+20q⁻¹+20q+9q³ | 2q³ | 58 each | 113 |
| W2 | 120 | 27 792 | 9 864 | 5 322 | 120/120/120 | 120 | 3q⁻⁵+2q⁻⁴+16q⁻³+6q⁻²+29q⁻¹+8+… | 0 | 120 each | 307 |
| W3 | 162 | 45 960 | 16 872 | 4 902 | 162/162/162 | 162 | 2q⁻⁵+7q⁻⁴+13q⁻³+21q⁻²+24q⁻¹+28+… | 0 | 162 each | 362 |
| W4 | 180 | 47 196 | 17 496 | 6 351 | 178/178/178 | 180 | q⁻⁶+11q⁻⁴+10q⁻³+29q⁻²+19q⁻¹+38+… | q+q⁵ | 178 each | 493 |
| W5 | 192 | 40 704 | 14 784 | 7 153 | 188/188/188 | 192 | 4q⁻⁵+31q⁻³+59q⁻¹+… | q+2q³+q⁵ | 188 each | 1 381 |
| W6 | 252 | 53 172 | 19 404 | 6 331 | 248/248/248 | 252 | 20q⁻⁴+62q⁻²+84+… | 2q²+2q⁴ | 248 each | 553 |
| W7 | 312 | 101 970 | 37 296 | 5 458 | 308/308/308 | 312 | 4q⁻⁵+5q⁻⁴+41q⁻³+15q⁻²+79q⁻¹+20+… | q+2q³+q⁵ | 308 each | 2 737 |

(ℓ_q is symmetric; only the negative half and the constant term are shown.
ℓ_q, r and r_q are also identical across the three sets. N_ℓ and β_n depend on
the order of the list and are not compared with B19; SPEC §10 item 3.
For W2–W7, set (ii) uses our face and edge order, which may differ from
Boozer's; Amendment 1 A2.)

**A3 events (B19 mode).**
- Every web: every theta component becomes a circle through a bigon whose legs
  are one edge (W1 765 times … W7 6 402). This is the ordinary theta path of
  A5. Each time, the marked component is fully deleted and its marker dropped.
- Zero in every web:
  - degenerate-square merges;
  - extra circles, meaning circles from joins other than a theta bigon;
  - marker losses;
  - component splits.
- Not zero:
  - **W7**: 2 bridge FAILs and 4 square eliminations that violate B19's
    distinctness conditions. All of them lie in the reductions below two
    Saddle sites, `["saddle", 49, 1, 4]` and `["saddle", 49, 2, 5]`, each of
    which still contributes 228 half-foams. B19's code aborts on such a
    configuration, so B19 cannot have reached those states. The N comparison
    for W7 must be read with that in mind.
  - Ordinary partial-semantics failures (no eligible face): W3 5, W6 91,
    W7 57.

## Run times and memory

WSL2 Ubuntu, Python 3.14.4, one core per web, sequential run
(`python3 run_all.py`), from `out/<W>/B19/timing.json`:

| Step | Total s | Generation + a-vectors s | Ranks s | 10 000 direct pairs s | Peak RSS MB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Controls | 2.1 | | | | |
| W1 | 3.4 | 1.7 | 0.0 | 1.0 | 82 |
| W2 | 8.6 | 4.7 | 0.1 | 1.9 | 122 |
| W3 | 14.1 | 9.5 | 0.3 | 1.6 | 147 |
| W4 | 16.0 | 9.6 | 0.3 | 2.4 | 147 |
| W5 | 13.8 | 7.8 | 0.5 | 1.6 | 129 |
| W6 | 19.8 | 10.6 | 0.6 | 1.6 | 149 |
| W7 | 40.3 | 27.1 | 1.2 | 1.7 | 239 |

The whole sequential run took 2 min 13 s wall clock, including the count-only
N table for all three modes. Peak RSS was 245 MB. With `--jobs 4` it took
76 s. The sequential and the parallel run produced byte-identical files for
all seven webs: `result.json`, `halffoams.jsonl.gz`, `extra.json`,
`controls.txt` and `n_table.json`. Only `timing.json` differs.

## Output files and SHA-256

`halffoams.jsonl` follows SPEC §7.6 exactly: one line per half-foam,
`{"i": i, "site": [...], "chain": [...], "deg": d, "a": "..."}` with
`json.dumps` default separators and `\n` line ends. It is stored gzip-compressed
(`gzip` with mtime 0 and level 9) because the uncompressed files total 122 MB.
The SPEC-relevant digest is that of the **uncompressed** content (`zcat … | sha256sum`),
and it is also the `halffoams_sha256` field of `result.json`.

| Web | SHA-256 of halffoams.jsonl (uncompressed) | SHA-256 of result.json |
| --- | --- | --- |
| W1 | f6393c5115c6418faf3862b6b0fa12bf0a95470a73a0be2b60ef93c3cf69ea04 | 473aeee4b5c0ff5d6e71eee792202658a330eabbd71fc565b5bb8a66c1bf72bf |
| W2 | d355be47ad510cc267af0fe81545d5e6d8794988b16ed9843041092beea7780c | 09770b6b6277c3a291572f58fc2a702d8d965d4d37fc9d68f2537ddf7e82e879 |
| W3 | a6fcea907edef8329349229c4de23bbd3b720cda96df7df12f70ed40fef61d23 | 525175e9e4185bbc8100c452122ba50a6022964cb7886e7b395d0beac3b7cf6c |
| W4 | cffacecaa83a109dc7797a023d9f3e9ae4cc814b52f535f38efdd6c5014a20ca | cee000eae1e9e92f43b9272fc2dd39763f1ad8d0f933c9c20e271b6f0e53b34d |
| W5 | f3f2c2db7546e6135f8002eb8712083d930a12ac528c92bbc05929a6f9ee4e90 | 77608e4871fea85196cae762505ebafb89d5e756f95bdef6105a6873ad4202af |
| W6 | 160cead62e416e2cbfcb705f3a772cde7da7c2aa247052cd3ddc9d7e42d11af5 | b747717ebdc6ca554b41a43f809217d3ed77a0c71d9f4b5a0b52ed5d7e26fe00 |
| W7 | 5829e354ec44bb9909a7c5e00641db397e4df818a799b7e17cf3fde7560cbf7e | 8011e1452c103915129524e14e54f3be6b69465b5ab29c7ee315c0d8dfc8360a |

The digests of the `.gz` files are in `extra.json`. They depend on the zlib
version and are not a cross-implementation target.

## Scope

- Only B19 mode was run with ranks on W1–W7. STRICT-ALL and PARTIAL-ALL are
  implemented and used for the controls (§9.4, §9.5). On W1–W7 they were run
  count-only, to check the N table of §6.4. Their ranks were not computed,
  and no enlarged search on W1 was started (task instruction; see NOTES.md).
- SPEC's optional items were not implemented: the KM-rules evaluator (§9.2),
  KM's colouring half-foams (§9.7), the graded Smith form, orientability sign
  propagation, and the plantri/fullgen re-identification (§8.3).
- The cross-implementation checks of §7.5 item 1 (a-vector SHA against
  Implementation B) and §11 are pending Implementation B.

## What was read

- Read: `search/d1/SPEC.md`, in full, including Amendment 1 (re-read when the
  coordinator announced it).
- Not read:
  - the paper page images (SPEC was clear enough);
  - `search/d1/implB/`;
  - the session scratchpad, including its `chk/` scripts;
  - any other repository code;
  - anything in WSL outside `~/d1A`.
- Seen but not opened: the repository's `CLAUDE.md` house rules were shown to
  the agent automatically by the harness. Listing the WSL home directory once
  (to check the environment) displayed other directory names. None of them
  was opened.

# Phase 2b (SPEC Amendment 2): the dodecahedron families

Amendment 2 is implemented from SPEC alone (branch d1/phase2b, SPEC commit
b400a9b), including §A2.13. Only the mandatory set is run: F0, KM, KMd, T2R,
T2 and T3s, with controls C0–C8. T3 and T4s are refused by the code. Nothing
here is a result until Implementation B agrees byte for byte (§A2.11).

## Command

```
cd search/d1/implA
python3 a2run.py --all --jobs 5      # all families and controls, then C6, union, summary
python3 a2run.py --family T2         # one family: F0 KM KMd T2R T2 T3s
python3 a2run.py --control C5-W3     # one control: C0 C4-prism5 C4-cube C5-W2 C5-W3 C6
```

C8 is written by the KMd run. C6 needs T2's `result.json`, and the union needs
the families' `novel.jsonl`. `D1_A2_OUT=<dir>` redirects the outputs.

## Code

| Path | Content |
| --- | --- |
| `d1a/tree.py` | SITES(K), site outcomes (PRECOND / BRIDGE / REDUCIBLE / IRREDUCIBLE), GEN_STRICT as a reduction tree with lazily composed, memoised leaf foams, depth-first path walk |
| `d1a/a2lib.py` | automorphisms of W1 and their action on a-vectors and on half-foams (§A2.6), KM half-foams (§A2.5), F-spans (§A2.7) |
| `a2run.py` | families, step 0–4 of §A2.7, direct-evaluation samples, certificates, controls, ledger |

- **Families.** Each family runs a count-only pass first; C3 is asserted
  there, and a mismatch aborts the run. The main pass then composes the
  retained leaves, M1∘…∘Mk∘h, as facet–seam half-foams (Mode G). a-vectors
  come from direct colouring enumeration, then A3 membership and novelty in
  the F-view, as in step 2.
- **Direct evaluation.** Every `pairsample.tsv` value is also evaluated
  directly on the glued closed foam, and the two are asserted equal.
- **Main pass = count pass.** The main pass re-derives every count and asserts
  that they equal the count-only pass.
- **F0 = Phase 2.** F0 is checked to be member-for-member identical (site,
  chain, degree and a-vector) to Phase 2's STRICT-ALL generator.

## Results

Every family ended **EXHAUSTED**. **No stop criterion fired**, and no family
produced a novel member.

| Family | Leaves (all degrees) | Retained / processed | Novel | Final ℓ₋₃ | Final dim U | Final ℓ | A3 violations | CPU s (count + main) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| F0 | 11 880 | 11 880 (all degrees) | – | 9 | 9 | 58 | 0 | 1.2 + ~5 setup |
| KM | 20 | 20 | 0 | 9 | 9 | 58 | 0 | 0.0 |
| KMd | 58 500 | 58 500 (all degrees; step 2 on the 20 of degree −3) | 0 | 9 | 9 | 58 | 0 | 7.0 |
| T2R | 4 190 400 | 107 430 | 0 | 9 | 9 | 58 | 0 | 35.2 + 104.5 |
| T2 | 1 499 040 | 50 220 | 0 | 9 | 9 | 58 | 0 | 9.5 + 45.1 |
| T3s | 4 085 832 | 61 927 | 0 (Aut closure: nothing to close) | 9 | 9 | 58 | 0 | 43.4 + 69.4 |
| union (KM, T2R, T2, T3s) | – | – | 0 | 9 | 9 | 58 | 0 | – |

**F0 (step 1):**
- ℓ = 58, with ℓ_q = 9q⁻³+20q⁻¹+20q+9q³ and r_q = 9q⁻³+20q⁻¹+20q+11q³.
  Both are exactly the [P2] values.
- C3_size = 20, dim U0 = 9, dim A3 = 20, dim R = 11, dim P = 9. All the
  [derived] assertions hold.

**KMd alone** has ℓ = 58, with the same ℓ_q and r_q as F0; so does F0 ∪ KMd
(C8). That is B19 Remark 4.3's value, under the "every multiset of ≤ 3 dots"
reading.

**Controls** (all pass):
- **C0:** all B19-mode degree −3 a-vectors lie in U0, all degree 3 ones in
  A3, and ℓ(F0) = 58.
- **C1:** 0 A3 violations.
- **C2:** T2R has no novel member.
- **C3:** every count in §A2.5 and §A2.9 matches, including:
  - T2's uniformity: 352 sites (4/71/87/190) and 837 retained for each of
    the 60 first moves;
  - the T3s level-3 counts for `["unzip", 18, 1, 2]`.
- **C4:**
  - prism5: 566 700 leaves; cube: 250 056 leaves.
  - 0 span violations.
  - For baseline ∪ family: ℓ = r = Tait, and ℓ_q = r_q = qdim of §9.4.
- **C5:**
  - W2: 161 448 retained; W3: 168 056 retained.
  - 0 span violations.
  - ℓ(baseline ∪ family) = Tait (120 and 162).
- **C6:**
  - 120 automorphisms; images of F0₋₃ lie in U0 and of F0₃ in A3.
  - β is invariant on the F0 sample for all g.
  - Relabelled image half-foams have a-vector g·a.
  - Symmetry check: T2 restricted to s0 (837 members) plus Aut closure gives
    dim U 9 and ℓ₋₃ 9, the same as the full T2.
- **C7:** pending Implementation B.
- **C8:** as above.

## Time, memory, ledger

- **Final run** (`--all --jobs 5`, WSL, Python 3.14.4):
  - 271 s wall, 806 s CPU;
  - peak RSS 305 MB (C5-W3), no process above 0.31 GB.
- **Per-family CPU** is in each `run.json` and in `out/A2-summary.json`.
  The ~5 s F0 set-up that every process repeats is not included in its
  phases.
- **Against the §A2.10 estimates:** every family's main pass finished well
  inside its estimate, far below the 3× stop.
- **Phase 2b runner time, including a first full run and development count
  runs:**
  - the first full run took 551 s wall, while another job was also running
    on the machine;
  - the development count runs took about 4 min;
  - together with the final run, about **0.25 runner-hours** of wall time and
    about **0.75 CPU-hours** in total.
- **Reproducibility:** the first and the final run produced byte-identical
  files everywhere:
  - every `result.json`, `pairsample.tsv` and `union.json`;
  - every `h.jsonl` (compared in WSL).

## Output files

- **What is here:** `out/<web>/A2/...` and `out/A2-summary.json`. SHA-256
  digests of every output file, including the uncommitted `h.jsonl` files,
  are in `out/A2-SHA256SUMS.txt`.
- **What is not here:** the `h.jsonl` files are not in the repository
  (§A2.13 item 4). Each one's digest is `h_sha256` in its `result.json`.
- **Formats:**
  - `result.json` follows §A2.8.
  - Where §A2.8 leaves the schema open (controls, union, level numbering),
    NOTES.md items 25–39 say what I chose.

## What was read for Phase 2b

- **Read:** `search/d1/SPEC.md` (Amendment 2 in full, including §A2.13) and
  my own files.
- **Not read:**
  - `implB/`;
  - the scratchpad;
  - Boozer's materials;
  - `search/d1/README.md`, `compare.py`, `compare-result.txt` and
    `.gitignore`;
  - any other repository file.
- **Seen incidentally:** one process listing in WSL showed that
  Implementation B's program was running at the time: its executable path
  under `/home/claude/d1B/` and one command-line flag. Nothing of B's was
  opened.
