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
