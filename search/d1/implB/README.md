# D1 Phase 2: Implementation B (Mode T, transfer matrices)

This is the second, independent implementation of `search/d1/SPEC.md`,
including its Amendment 1. It computes lower bounds ℓ(K) ≤ dim J♭(K) by
reproducing Boozer (2019), arXiv 1908.07133. It uses Python 3's standard
library only and exact arithmetic over F₂ and GF(4). There is no randomness,
and the output is deterministic.

Status: these are **leads until A and B agree**. The house rule says a
computation needs two agreeing implementations. This directory is one of the
two.

## Command

From this directory (run in WSL Ubuntu, Python 3.14.4):

    python3 d1b.py all --jobs 4

This runs every SPEC §9 control. If any control fails, it stops. Otherwise it
runs W1–W7 in B19 mode and writes `results/`.

Other entry points:

- `python3 d1b.py controls` runs the controls only.
- `python3 d1b.py web W3 --mode B19|STRICT-ALL|PARTIAL-ALL --jobs N` runs one
  web in one mode.
- `--no-check` skips the check that every derived Tait colouring is proper.
- `--git-commit C` records C in `result.json`.

## Method

- **Files.**
  - `core.py`: webs, faces, Tait colourings, REBUILD (§3), the twelve
    cobordism records (§5) and GEN (§6.1).
  - `sites.py`: move sites. B19 mode uses the Amendment 1 A1 order.
  - `ranks.py`: §7.
  - `closedfoam.py`: §9.1 closed foams, evaluated directly by §2.4 and at
    GF(2⁸) points by §2.5.
  - `controls.py`: all §9 controls.
  - `webs.py`: Appendix A, transcribed.
- **Mode T.**
  - No foam is ever built. A generated list of half-foams with boundary K is
    held as its a-vectors, stored column-wise. Each Tait colouring t
    corresponds to a pair of big integers whose bit i is the F-coordinate
    (1, ω) of a_{h_i}(t).
  - Every elementary cobordism C contributes its transfer matrix T_C (§4.6),
    obtained by enumerating local colourings from each top colouring t.
  - a_{C∘H} = a_H·T_C then takes a few XORs per nonzero entry.
- **Top-down colourings.** Only the colourings reachable from the target's
  Tait colourings are carried. This is exact, because T_C(t′, t) = 0 unless a
  local colouring joins t′ to t (NOTES item 6).
- **A4 marker sets.** B19 mode tracks a set of outer-face darts, one per
  component (Amendment 1 A4).
- **Ranks.**
  - Ranks are computed on packed GF(4) row vectors. Gram and pairing matrices
    are built only between original a-vectors, so every entry is a genuine
    pairing and is asserted to lie in F.
  - ℓ, ℓ_q and the prefix curve β_n follow §7.1–7.2. r and r_q follow §7.3,
    via h(k) and g(k). The run asserts g ≥ 0, Σg = r, ℓ_d = ℓ_{−d} and
    ℓ ≤ r ≤ T.
- **Built-in asserts.** Each run also checks:
  - every record's degree against B19 Table 1;
  - the §2.4 asserts on every closed foam;
  - the 10 000 §7.5 sample pairs: value in F, and 0 in forbidden degrees.

## Controls (SPEC §9): all PASS

The full log is in `results/controls/controls.txt`.

- **§9.1**:
  - the closed-foam table (Φ and J♭ for every row, and the stated specific
    values);
  - the dot-migration relations;
  - the full-polynomial tests at (0x02, 0x03, 0x05) and (0x53, 0xCA, 0x01):
    rows 2–5 for n = 0..6, and θ(n₁,n₂,n₃) for 0 ≤ nᵢ ≤ 4, against h_m and
    Jacobi–Trudi.
- **§9.3**:
  - circle: a-vectors `132 111 123`, antidiagonal Gram, ℓ = 3;
  - theta: a-vectors `111111 231312 321213 112233 232131 322332`, the stated
    Gram, ℓ_q = q⁻³+2q⁻¹+2q+q³.
- **§9.4**:
  - GEN STRICT on circle, two circles, theta, K4, prism3, cube, prism5 and
    prism6 gives N = Tait = ℓ = r, with ℓ_q = r_q as tabulated;
  - [3]! divides ℓ_q for the non-circle webs;
  - the cup r_q test (δ = 0,1,5 → r_q = q⁻²+1+q⁸; δ = 0..3 → r_q = ℓ_q).
- **§9.5**:
  - prism5 STRICT-ALL: N = 3660 (360/2190/840/270), ℓ = 30;
  - cube: N = 2160 (288/1224/576/72), ℓ = 24;
  - Lemma 4.11 chains 1–4: supports (36,36), (24,48), (24,12), (36,36), and
    every Boolean product is empty;
  - chain 5: the product has 36 pairs.

## W1–W7, B19 mode (Amendment 1 order)

Every N matches B19 Table 2, and so does every ℓ. Every ℓ_q, and every
r_q − ℓ_q, matches B19 Table 3, and r = Tait throughout.

| Web | N | Zip/Unzip/Saddle/IH | Tait | ℓ | r | r_q − ℓ_q | N_ℓ (ours) | match B19 |
| --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |
| W1 | 11 160 | 1080/3960/3960/2160 | 60 | 58 | 60 | 2q³ | 113 | yes |
| W2 | 27 792 | 2808/9864/10224/4896 | 120 | 120 | 120 | 0 | 307 | yes |
| W3 | 45 960 | 4188/16872/16800/8100 | 162 | 162 | 162 | 0 | 362 | yes |
| W4 | 47 196 | 4248/17496/16956/8496 | 180 | 178 | 180 | q + q⁵ | 493 | yes |
| W5 | 40 704 | 3744/14784/14832/7344 | 192 | 188 | 192 | q + 2q³ + q⁵ | 1381 | yes |
| W6 | 53 172 | 4704/19404/19068/9996 | 252 | 248 | 252 | 2q² + 2q⁴ | 553 | yes |
| W7 | 101 970 | 9036/37296/39564/16074 | 312 | 308 | 312 | q + 2q³ + q⁵ | 2737 | yes |

The ℓ_q values (identical to B19 Table 3):

- W1: 9q⁻³+20q⁻¹+20q+9q³.
- W2: 3q⁻⁵+2q⁻⁴+16q⁻³+6q⁻²+29q⁻¹+8+29q+6q²+16q³+2q⁴+3q⁵.
- W3: 2q⁻⁵+7q⁻⁴+13q⁻³+21q⁻²+24q⁻¹+28+…
- W4: q⁻⁶+11q⁻⁴+10q⁻³+29q⁻²+19q⁻¹+38+…
- W5: 4q⁻⁵+31q⁻³+59q⁻¹+…
- W6: 20q⁻⁴+62q⁻²+84+…
- W7: 4q⁻⁵+5q⁻⁴+41q⁻³+15q⁻²+79q⁻¹+20+…

Amendment 1 findings:

- **A2.** The Unzip block alone, the first N_e (N_e as in Table 2) and the full
  list give identical ℓ, ℓ_q, r and r_q for every web (`a2_subsets.json`).
- **A3.** Only W7 has events Boozer's program would abort on: two degenerate
  squares, each followed by a bridge FAIL, at Saddle sites
  `["saddle",49,1,4]` and `["saddle",49,2,5]`. These lie beyond N_e.
  Otherwise the only events are the Boozer-legal theta→circle ones, plus the
  `no_eligible_face_fail` counts: W3 5, W6 91, W7 57. Details are in NOTES
  items 18–19.
- **B19 Remark 4.2.** For W1, each move type alone gives ℓ = 58 (see
  `results/W1/B19/remark42.json`).

## Run times and memory

The machine was WSL2 Ubuntu (20 cores), and the whole `all` run used 4
workers.

| Part | Time |
| --- | --- |
| Whole `all` run | 3 min 42 s wall, peak RSS 117 MB |
| Controls | ≈ 3.5 min (mostly the Tait-colouring searches and support enumerations of the §9.5 checks) |
| W1 | 0.5 s |
| W2 | 1.3 s |
| W3 | 2.3 s |
| W4 | 2.5 s |
| W5 | 2.3 s |
| W6 | 3.1 s |
| W7 | 6.9 s |

Per-web times include generation and ranks; see each `timing.txt`.

**Reproducibility.** A rerun of W1–W7 with `--jobs 1` gave byte-identical
`halffoams.jsonl`, `a2_subsets.json`, `a3_events.json` and `pairsample.tsv`.
`result.json` was also identical apart from the `command` line.

## Output files and SHA-256

`results/<web>/B19/` holds:

- `halffoams.jsonl` and `result.json` (the SPEC §7.6 format; see NOTES
  items 1–5);
- the extras `a2_subsets.json`, `a3_events.json`, `pairsample.tsv` and
  `timing.txt`;
- `remark42.json`, for W1 only.

`results/controls/` holds `controls.txt` and the prism5 and cube STRICT-ALL
files. In total, `results/` is about 119 MB, mostly the W `halffoams.jsonl`
files. Whether to commit them, or only their digests, is Gabriel's call.

| File | SHA-256 |
| --- | --- |
| W1/B19/halffoams.jsonl | f6393c5115c6418faf3862b6b0fa12bf0a95470a73a0be2b60ef93c3cf69ea04 |
| W2/B19/halffoams.jsonl | d355be47ad510cc267af0fe81545d5e6d8794988b16ed9843041092beea7780c |
| W3/B19/halffoams.jsonl | a6fcea907edef8329349229c4de23bbd3b720cda96df7df12f70ed40fef61d23 |
| W4/B19/halffoams.jsonl | cffacecaa83a109dc7797a023d9f3e9ae4cc814b52f535f38efdd6c5014a20ca |
| W5/B19/halffoams.jsonl | f3f2c2db7546e6135f8002eb8712083d930a12ac528c92bbc05929a6f9ee4e90 |
| W6/B19/halffoams.jsonl | 160cead62e416e2cbfcb705f3a772cde7da7c2aa247052cd3ddc9d7e42d11af5 |
| W7/B19/halffoams.jsonl | 5829e354ec44bb9909a7c5e00641db397e4df818a799b7e17cf3fde7560cbf7e |
| W1/B19/result.json | 4e587d77f915c630c03571ead3d31d03b7dff751f4a22806f9b670cf755018f5 |
| W2/B19/result.json | e6bef21eaafcef1624864f2adaffff2f557d5a4ee1c555f836b43d3850737ad2 |
| W3/B19/result.json | fc7d2b543520c1d832a405d56785e986803e4e02b70120ede29a0d2859eb365d |
| W4/B19/result.json | a6a164e7c159c2fd1230180a8e3f8957667c35755794887385af8746c29a7161 |
| W5/B19/result.json | 6da5d5826170cba9bb23efe8338fde8f175757236fcc0f5bbb757013e1c25e33 |
| W6/B19/result.json | 7bacb549dacb52739fb91fe2ef9c71e8b655f72c9a57bd80ed90fce34aea2b17 |
| W7/B19/result.json | ceb8751e18213eeda777c8d4a2b57b45329834a1c78d43388b97ed3ab81639e3 |
| controls/prism5/STRICT-ALL/halffoams.jsonl | ad27359fe4841fdaa8ca66d9ec47084582526e744f58e7ca11774d79371fe7b1 |
| controls/cube/STRICT-ALL/halffoams.jsonl | 67a0b1a4e674b3aabfef149f68f688b3919bb09b7edf42c43521bbe6c56d30a5 |

The `result.json` digests depend on the recorded `command` and `git_commit`
strings (`python3 d1b.py all --jobs 4`, `unrecorded`).

## Not done

- STRICT-ALL and PARTIAL-ALL are implemented but were not run on W1–W7
  (stopping point of the task).
- No dodecahedron enlargement was started.
- The optional §9.2, §9.7 and Smith-form checks were not implemented.

---

# Phase 2b (SPEC Amendment 2): the dodecahedron families

## Command

From this directory, in WSL:

    python3 a2run.py all --jobs 4 --out results

This runs:

- F0, which gives the start state: C3, A3, U0, R and P;
- controls C0, C4 and C5;
- families KM, KMd, T2R, T2 and T3s;
- control C6 (Aut and the T2-restricted-to-s0 symmetry check);
- controls C3, C1, C2 and C8;
- the union (step 4).

The optional family T3 was run separately, on Gabriel's go of 2026-09-30
("Run T3 on all 60 bigon sites"):

    python3 a2run.py family T3 --jobs 8 --prior ~/d1B/a2out2 --hprefix 61927 --out ~/d1B/t3/full

This recomputes F0 as the start state, runs T3's count-only pass (it stops
there if any count differs from §A2.5, including the per-first-move check),
then the main pass, then the union (§A2.7 step 4) with T3 after T3s.
`--prior` names the results root of the mandatory run, whose `result.json`
files supply the other families' novel members (all empty). Only
`W1/A2/T3/` and `W1/A2/union.json` were copied into `results/`.

The optional family T4s was run on Gabriel's go of 2026-09-30 ("Run T4s"):

    python3 a2run.py family T4s --jobs 8 --prior ~/d1B/t4s/implB/results --out ~/d1B/t4s/full

It recomputes F0, runs T4s's count-only pass (it stops there if any count
differs from §A2.5), the main pass and the Aut closure of the novel members
(§A2.7 step 2.4), then the union with T4s after T3. `--prior` is a copy of
this `results/` tree, which holds the committed KM, T2R, T2, T3s and T3
`result.json` files. Only `W1/A2/T4s/` and `W1/A2/union.json` were copied
back into `results/`.

## Files

| File | Contents |
| --- | --- |
| `a2tree.py` | SITES, outcomes, paths, leaves (§A2.4), in Mode T with column-packed transfer products. Includes a degree-only GEN for the count-only pass; at an emitting level, a-vectors are computed only for sites with a retained leaf (NOTES item 50). |
| `km.py` | Facet-based KM/KMd half-foams, evaluated directly by §4.5. This is B's only facet code. |
| `a2run.py` | Families, the span state (A3, U, P, C3, R), automorphisms (§A2.6) and output writers. |
| `a2controls.py` | Controls and orchestration. |

## Results (all controls PASS; no stop criterion fired)

| Family | Leaves | Retained deg −3 | Novel | final ℓ | ℓ₋₃ | dim U | A3 viol. | stop | wall / CPU (4 workers) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| F0 | 11 880 | 810 (all 11 880 kept) | 0 | 58 | 9 | 9 | 0 | EXHAUSTED | 1.4 s / 1.4 s |
| KM | 20 | 20 | 0 | 58 | 9 | 9 | 0 | EXHAUSTED | <0.1 s |
| KMd | 58 500 | 20 (all 58 500 kept) | 0 | 58 | 9 | 9 | 0 | EXHAUSTED | 0.8 s |
| T2R | 4 190 400 | 107 430 | 0 | 58 | 9 | 9 | 0 | EXHAUSTED | 74 s / 296 s |
| T2 | 1 499 040 | 50 220 | 0 | 58 | 9 | 9 | 0 | EXHAUSTED | 26 s / 103 s |
| T3s (+ Aut closure) | 4 085 832 | 61 927 | 0 (0 Aut) | 58 | 9 | 9 | 0 | EXHAUSTED | 47 s / 185 s |
| T3 (optional; no Aut closure) | 245 149 920 | 3 715 620 | 0 | 58 | 9 | 9 | 0 | EXHAUSTED | 35 min 05 s / 16 800 s (8 workers) |
| T4s (optional; + Aut closure) | 808 040 304 | 5 300 704 | 0 (0 Aut) | 58 | 9 | 9 | 0 | EXHAUSTED | 1 h 15 min 17 s / 35 602 s (8 workers) |

T3 details:

- Count-only numbers equal the §A2.5 T3 row: expanded L1 60, L2 5,220;
  level 3 32,880 / 418,440 / 570,480 / 1,041,720; 245,149,920 leaves;
  3,715,620 retained. Level 1 equals F0's and level 2 equals T2's outcomes.
  Each of the 60 first moves has exactly T3s's numbers (548 / 6,974 /
  9,508 / 17,362; 87 level-2 nodes; 61,927 retained).
- `h.jsonl` is not written (more than 2,000,000 members, §A2.8); its
  SHA-256 was computed on the fly and is `h_sha256` in `result.json`.
  The s0 subtree (lines 1–61,927) is byte-identical to T3s's `h.jsonl`.
- `--m1-limit 3` runs with 1 and 8 workers gave byte-identical outputs
  (NOTES item 42).
- The union with T3 after T3s is still `EXHAUSTED` at dim U 9, ℓ₋₃ 9.

T4s details:

- Count-only numbers equal the §A2.5 T4s row: expanded L1 s0, L2 87,
  L3 9,508; level 4 78,764 / 847,536 / 1,253,672 / 1,985,780 (4,165,752
  sites); 808,040,304 leaves; 5,300,704 retained (all of degree −3).
  Levels 2 and 3 equal the T2s0 and T3s rows.
- Level 4 by move type (PRECOND / BRIDGE / IRREDUCIBLE / REDUCIBLE):
  Zip 39,382 / 5,161 / 49,118 / 268,850; Unzip 0 / 43,392 / 998,167 /
  678,806; Saddle 0 / 797,181 / 157,306 / 765,878; IH 39,382 / 1,802 /
  49,081 / 272,246.
- `h.jsonl` is not written (more than 2,000,000 members); `h_sha256` was
  computed on the fly. `run.json` has one digest per second move
  (`h_sha256_by_second_move`).
- No novel member, so the Aut closure had nothing to process
  (`aut_novel` is `[]`). The union with T4s after T3 is still `EXHAUSTED`
  at dim U 9, ℓ₋₃ 9.
- Checks before the full run (NOTES item 52): `--l2-limit 3` with 1 and 8
  workers gave byte-identical outputs, and T3s, T2 and T2R rerun with the
  changed code reproduced their committed files and `h.jsonl` digests.

F0 details:

- ℓ_q = 9q⁻³+20q⁻¹+20q+9q³ and r_q = 9q⁻³+20q⁻¹+20q+11q³, both equal to
  [P2].
- C3 has 20 members.
- Start state: dim U0 = 9, dim A3 = 20, dim R = 11, ℓ₋₃ = 9, all as SPEC
  asserts.

KMd:

- KMd alone has ℓ = 58, the same ℓ_q as F0, r = 60, and r_q equal to F0's.
- F0 ∪ KMd gives the same values (C8).

## Controls

| Control | Result |
| --- | --- |
| C0 | PASS. All 765 B19 degree −3 vectors lie in U0, all 2955 degree 3 vectors lie in A3, and ℓ(F0) = 58. |
| C1 | PASS: zero A3 violations. |
| C2 | PASS: T2R has no novel member. |
| C3 | PASS. Every count-only number equals §A2.5, and T2 is uniform: all 60 first moves give 4/71/87/190 and 837 retained. |
| C4 | PASS for prism5 (566 700 leaves) and cube (250 056). No span violations, and ℓ_q = r_q = §9.4 with ℓ = r = Tait. |
| C5 | PASS for W2 (4 603 104 leaves; 14 232 retained at deg −5, 147 216 at deg −3) and W3 (8 835 096; 8 444 and 159 612). No span violations, and ℓ(baseline ∪ family) = Tait. |
| C6 | PASS. There are 120 automorphisms, all images lie in U0 or A3, β is invariant on the sample, and the symmetry check (T2 restricted to s0 plus Aut closure) matches full T2's dim U 9 and ℓ₋₃ 9. |
| C8 | Reported above. |

## Resource ledger (Phase 2b, this implementation)

- **Committed run** (4 workers): 7 min 10 s wall, 1666 CPU s, peak RSS 124 MB.
- **Identical run with 8 workers**: 8 min 04 s wall, 3656 CPU s (inflated by
  hyperthreading), 163 MB. It gave byte-identical outputs, including every
  `h.jsonl`.
- **Tests**: about 35 s wall.
- **Total**: about 0.26 runner-hours and 1.5 CPU-hours.

T3 (optional), 2026-09-30, all in WSL while implementation A also ran:

| Run | Workers | Wall | CPU | Peak RSS, all processes |
| --- | ---: | --- | ---: | ---: |
| Smoke test (`--m1-limit 1`) | 8 | 1 min 10 s | 362 s | ≈ 280 MB |
| Count-only pass, all 60 first moves | 8 | 5 min 36 s | 2 583 s | 283 MB |
| Determinism, `--m1-limit 3` | 8 | 2 min 14 s | 941 s | 280 MB |
| Determinism, `--m1-limit 3` | 1 | 14 min 33 s | 873 s | 38 MB |
| **Full run** (count 276 s wall / 2 166 s CPU, main 1 828 s / 14 634 s) | 8 | 35 min 06 s | 16 802 s | 445 MB (in-process sampling), 461 MB (external sampler) |

The main pass estimate was 11,032 CPU s (45 µs per leaf), so the stop
threshold was 33,095 CPU s; the pass used 14,634 s (1.3×). A regression
rerun of T2 and T3s with the changed code (8 workers, 47 s wall, about
340 CPU s) reproduced the mandatory outputs byte for byte. T3 total: about
1.0 runner-hours and 6.1 CPU-hours.

T4s (optional), 2026-09-30, all in WSL while implementation A also ran:

| Run | Workers | Wall | CPU | Peak RSS, all processes |
| --- | ---: | --- | ---: | ---: |
| Smoke test (`--l2-limit 1`, before the item 50 change) | 8 | 41 s | 143 s | 275 MB |
| Prefix test (`--l2-limit 2`, before the item 50 change; no retained member) | 8 | 1 min 04 s | 316 s | 276 MB |
| Count-only pass | 8 | 13 min 29 s | 6 381 s | 300 MB |
| Determinism, `--l2-limit 3` | 8 | 1 min 40 s | 534 s | 281 MB |
| Determinism, `--l2-limit 3` | 1 | 9 min 34 s | 574 s | 36 MB |
| Regression T3s, T2, T2R | 8 | 3 min 39 s | 1 584 s | not sampled (largest single process 39 MB) |
| **Full run** (count 1 099 s wall / 8 502 s CPU, main 3 411 s / 27 093 s) | 8 | 1 h 15 min 17 s | 35 602 s | 614 MB (in-process sampling) |

The main pass estimate was 36,362 CPU s (45 µs per leaf), so the stop
thresholds were 109,085 CPU s and 12,701 s wall; the pass used 27,093 CPU s
(0.75×). T4s total: about 1.76 runner-hours and 12.5 CPU-hours.

Per-family wall and CPU times for the count-only and main passes are in each
`run.json`.

## Output digests (committed files)

The `h.jsonl` files are not committed. They are in WSL at
`~/d1B/a2out2/h/`.

| File | SHA-256 |
| --- | --- |
| W1/A2/F0/result.json | 31c6b8143868100ce1207482b6a4ffdcba350f1353d3be4c234b618af428103d |
| W1/A2/F0/pairsample.tsv | f8b971defedc4d8c72ac8a1afa3f89959df6ff015964c2711156d72e47d13742 |
| W1/A2/KM/result.json | 94479e75da739c358339ca71f916b4d3d56d87c0e1537424ec2ff374596b2b9b |
| W1/A2/KM/pairsample.tsv | a25d66521bf1f31dbccf03c0774bf5a5435aead297dfb43ac7c3c3931a0e21f2 |
| W1/A2/KMd/result.json | 3696abf5fb6d6e90651d8a20a85cbe09cec756435021fc18305829a52d4e05ba |
| W1/A2/KMd/pairsample.tsv | 8fc4d931b3c8373ae21c701ff32815d627b12100c6b0e8b011ec94fc405c090e |
| W1/A2/T2R/result.json | 65cbca84e772782368c9b8b7b5427c9ef9d8c5f4fa7e03bf422f0a2a9b6363c2 |
| W1/A2/T2R/pairsample.tsv | b2573106ec71218e1cdebbcb11b5898cddcfe0a215a3382cde94f2f5cec33d87 |
| W1/A2/T2/result.json | 5c3cf247cd13635477f44c2a901f78dff7525a77d9428e343f8be5ebf511b5c9 |
| W1/A2/T2/pairsample.tsv | 6a07899f0f9e8dd4d4b94fd42d6523be064bce3150953473ad7372ecb083172f |
| W1/A2/T3s/result.json | 43ed0315f6812cb22b76948bf0a68f40237a671d61b47e71dccd80a738d7b981 |
| W1/A2/T3s/pairsample.tsv | 497a64dacba4a9945df1494cca47cc5fe6539e703f3e232b97e3400b2c2d9749 |
| W1/A2/T2s0/result.json (C6) | 0aa7259cc4207514eb9945934f6548a619b004dad5b09644f623c92b3fe82f7e |
| W1/A2/T2s0/pairsample.tsv | e69cfd7960fd360969bd032ec7938f2eeecb8ebe0fa43606d1602d1d2e31a52f |
| W1/A2/T3/result.json | 8f703eb26b198825bbbd583aad8cc119a279cf3cdfe170f79797389244050ab5 |
| W1/A2/T3/pairsample.tsv | 849e4cdd06145629fbab4008699de3c7c2f64086d1d3d941f14032bad8de4742 |
| W1/A2/T4s/result.json | 8adb3bac9e2a975a432ad94d5c02736ffada7f643ea1e53ebe0af0cbef50da7d |
| W1/A2/T4s/pairsample.tsv | 749120654a94109113580a20500fbf47bb86142aec74e53e57246b7aa9736888 |
| W1/A2/union.json (with T3 and T4s) | 047a8c3f0be90abea39048865d7e559de8bdbda5e349883c8a1edf9a9869fe08 |
| W1/A2/controls.txt | 89e553559cdcb46b3dce3842aa9b3f08a3d28328778c549f7bc6db756afb4f7c |
| W1/A2/ctl-C0/result.json | 5b93949f6f3a737817138d1d20ae792b5deb438fb27458278e5a5dfe7b6a4a54 |
| W1/A2/ctl-C3/result.json | 2680f9ebb3a2dbd225193988fbb1106154904e2c9913c051b8cbfd2411ada390 |
| W1/A2/ctl-C6/result.json | 7f4eb662697de3a63183968956bb64531f00b52b0e798a046e13cfa301ed6ded |
| W1/A2/ctl-C8/result.json | 1de1610b28899ed450693f207ad51c38374b523346407f9f7e590c4cb71ff126 |
| prism5/A2/ctl-C4/result.json | c7450cdbc1f821a9c423d285dbe953503f6284da18546d348c33c58b064fa658 |
| cube/A2/ctl-C4/result.json | 8521bd242eff47809d2208b9a7a79518fceb0da234d795410abf6867b367b837 |
| W2/A2/ctl-C5/result.json | 2aada97e475f72d5c431734ebafe0edfdb6011ea8657c35c3d3837e9474462a7 |
| W3/A2/ctl-C5/result.json | ff244a961f4296f747c0a33ca55062187bc55f1ca4dfcb717a144fcdcacda048 |

`h.jsonl` digests (these are also `h_sha256` in each `result.json`):

| File | SHA-256 |
| --- | --- |
| F0 | f88b99480a96759a4975402fb6519c0c46e1937b0284f975abbc13adbe7f06b1 |
| KM | 788c2e92d6467bef3c555c9573287e5e2a95ebe411d2f5e100234d4012053d6c |
| KMd | b98430f7d29c4636894941344bcd88aa7f634799264e563bdf643e4cbabcbb2e |
| T2R | f211ed2cf019c747bd4fee75fc7e395b9c23aff387b984b350f0ddf323fc003f |
| T2 | 8c2c96ce95f42fe9fe92304fd2ff445f41a60100431bdae5316e208fdfb9c9ed |
| T3s | 5f31c4db60abf4fc893497544cfcb858a960cb98141864bbdb9302a12f7eedf2 |
| T3 (not written; computed on the fly) | 6ea3919a1e7c7a83d6c0416330dbe9be1f788eb5afdda4c001e72bfbb77b5542 |
| T4s (not written; computed on the fly) | d486c579806fea70f8cd6917b7d676da4c31523aac56865f8707c997485fdc80 |
| T2s0 | 009c5e0fa3d67de0f798ad04d70218b10ef45978a6cd9e8cac9da2537ccf7d0b |
| C4 prism5 | 8a6e97fec8f0713832d420f80e907566b51f511478fbeb499d3597501a688e87 |
| C4 cube | 4c381a952290f7eb3cd2243debdc25b127e07bac2d9de56a5198eef2b4f10881 |
| C5 W2 | c408290882cb6840703f35f02ab9b6e32c7ac22bb8a41d11fe7b9d7eeb8f37c6 |
| C5 W3 | 002ae566f44b5d73ff0e0bb0a8389c9fd64ad2875b6a8413c9dd77fa5afa0493 |

## Reading (SPEC §A2.2 framing)

- Every mandatory family, and the optional T3 and T4s, ended `EXHAUSTED`: ℓ₋₃ stayed at 9, dim U stayed
  at 9, and no family had a novel member.
- This decides nothing about 58 versus 60. It is consistent with both, and
  it is not evidence beyond B19.
- No certificate applies.
- All of this is a lead until A agrees byte for byte (C7).
