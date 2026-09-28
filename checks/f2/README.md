# F2: the near-linear computer checks, reimplemented independently

Task F2. This is a second implementation of the computer checks in
"The Four Color Theorem with Linearly Many Reducible Configurations and
Near-Linear Time Coloring" (Inoue, Kawarabayashi, Miyashita, Mohar,
Thomassen, Thorup; **arXiv:2603.24880v2, 7 May 2026**). It is written from
the paper's pseudocode (appendix A) and main text only. Its value is as a
cross-check of the upstream C++ run in task F1, so it was written without
looking at that code or at any other reimplementation. The **Independence
log** at the end lists everything that was consulted.

**Status: phase 3, complete.** Every computer check of appendix A has been
run in full.

- All eleven numerical targets match: the five of phase 1, the wheel
  counts for centre degrees 8-11, and the bad cartwheels for degrees 7
  and 8.
- **Lemmas A.4, A.5 and A.6 pass**, on every one of their 393, 1,320 and
  298 roots.
- No assertion, invariant or exception failed anywhere.
- The whole pipeline is one command (see "How to run"). It takes about
  an hour on 17 processes.

Nothing has yet been compared object by object with the F1 outputs.

## Phase 1 results

These were run on the self-hosted machine (WSL2 Ubuntu, 20 CPUs, 25 GB,
Python 3.14.4), one process each, measured with `/usr/bin/time -v`, at
commit 52e38a2. The full record is in `results/phase1/`. The A.2 and
wheel times include reading the 8,200 configuration files (about 0.4 s)
and, for the wheels, recomputing R*-D (about 1.5 s).

| Check | Observed | Published target | Wall time | Peak RSS |
| --- | --- | --- | --- | --- |
| A.1: size of R* | **1832** | 1832 | 2.1 s | 33 MB |
| A.1: max charge in R* | **8** | 8 | (same run) | |
| A.2: size of R*-D | **671** | 671 | 1.5 s | 67 MB |
| A.2: max charge in R*-D | **5** | 5 | (same run) | |
| A.9.7, centre degree 7: wheels kept | **5439** | 5439 | 16.6 s | 70 MB |

Details:

- **A.1.** R* contains the neutral rule R0 (charge 0), as A.8.2 builds it:
  1832 including R0. Exactly one combination has charge 8. It combines
  rule001 with both orientations of rule002, rule003 and rule004, which is
  what Figure 7's caption describes. The charge histogram (charge: count) is
  0:1, 1:83, 2:325, 3:546, 4:505, 5:276, 6:83, 7:12, 8:1.
- **A.2.** R*-D also includes R0. Ten combinations have charge 5. They come
  in five mirror pairs (for example, rule008_2 + rule009_2 + rule011_1 +
  rule023_2 + rule027_1 and its mirror), and Figure 8 draws five cases. The
  histogram is 0:1, 1:83, 2:227, 3:248, 4:102, 5:10. The combination loop
  made 35,296 calls to A.8.1 and 1,389 blocking tests against the 19,754
  entries of Ds.
- **Degree 7.** A.9.5 gives 11,165 wheels up to rotation. Of these, 5,497
  are pruned by the charge bound and 229 because they are blocked, leaving
  **5439**.
- **X and T73** (`run.py special`): all of the transcription's
  self-consistency checks pass (see "X and T73" below). One of them is
  independent evidence: X plus the vertex w of Figure 13 is blocked by D,
  through D1774. D1774 has degrees 5, 5, 5, 5, 5, 5, 7, 8, the same as the
  blue configuration in the figure. X alone is not blocked.

We did not compare against the figures by isomorphism. The agreement with
Figures 7 and 8 is by rule sets and counts only.

### Cross-checks that the numbers are not artefacts of our code

| Variation | Effect |
| --- | --- |
| `--order reversed`: rules added to A.8.2 in reverse order | A.1 and A.2 give byte-identical payloads. Each payload is the sorted list of canonical forms of the combined rules, so the *sets* of combined rules are identical up to isomorphism, not just their sizes. |
| `--literal`: no speed-ups (A.6.6 tried over all 19,754 configurations, no prefilters, no early exit) | A.2 and the degree-7 wheels give byte-identical payloads (A.2: 12.9 s; wheels: 84 s on 16 processes). |
| Windows, Python 3.12 vs WSL, Python 3.14 | Identical payload digests for A.1, A.2 and the degree-7 wheels. |
| `ginclude` read the other way round (a scratch experiment, not in the code; see ambiguity 1) | A.2 gives 889 combinations with max charge 6, and 5439 becomes 6174. The targets therefore discriminate between the two readings, and only the one we use reproduces them. |

Payload sha256 digests (WSL run, `results/phase1/summary.json`):
A.1 `a91da734…`, A.2 `937b336e…`, degree 7 `cf0f6e83…`.

## Phase 2 results

Run on the same machine, detached, with 17 worker processes. The code was
at commit dbe6576 for the wheels and 4c4ab0b for the rest. The record is
in `results/phase2/`:

- `steps.txt`: each step's wall time and its session peak memory, which is
  the summed RSS of every process in the job, sampled every 2 s;
- `time-*.txt`: the `/usr/bin/time -v` output of each step. Its "Maximum
  resident set size" covers only the largest single process;
- `summary.json`, `timings.json`, `a10-timing-summary.json`: results,
  timings and payload digests;
- `files.sha256`: whole-file digests of the full outputs, which stay in WSL
  at `/home/claude/f2-final/`.

| Check | Observed | Published target | Wall time (17 processes) | Session peak memory |
| --- | --- | --- | --- | --- |
| A.9.7 wheels kept, centre degree 8 | **6790** | 6790 | 11 s | 1.1 GB |
| A.9.7 wheels kept, centre degree 9 | **3285** | 3285 | 35 s | 1.1 GB |
| A.9.7 wheels kept, centre degree 10 | **626** | 626 | 3.0 min | 1.2 GB |
| A.9.7 wheels kept, centre degree 11 | **8** | 8 | 14.3 min | 1.8 GB |
| bad cartwheels with tail ranges, degree 7 | **9366** | 9366 | 31.8 min for all degrees (9.0 CPU-hours) | 1.2 GB |
| bad cartwheels with tail ranges, degree 8 | **728** | 728 | (same run) | |
| bad cartwheels, degrees 9, 10, 11 | **0, 0, 0** | (none published; A.9.21 line 8 requires 0) | (same run) | |

Details:

- **Wheels.** Of the 48,915 / 217,045 / 976,887 / 4,438,925 wheels up to
  rotation, the charge bound prunes 41,833 / 213,321 / 976,043 / 4,438,887
  and blocking prunes 292 / 439 / 218 / 30.
- **Bad cartwheels.** Every one of the 16,148 wheels of C0 went through
  fixInRules and fixOutRules: 5439 / 6790 / 3285 / 626 / 8 for degrees
  7-11. CPU time per degree was 11,266 / 15,173 / 5,532 / 417 / 2 s. The
  slowest single wheel took 181 s, and the largest worker used 63 MB.
- **Failures.** None, on any wheel:
  - the assertions of A.9.21 lines 7-9: the charge bound is 0, the centre
    degree is 7 or 8, and some neighbour has degree 7-9;
  - our C_all invariants: the centre and its neighbours have fixed degrees,
    every other range is a tail range [k, 9], and no range is empty;
  - exceptions.

  Failures are recorded per wheel in `bad-wheels.jsonl`; no wheel has any.
- **Deduplication did not matter.** A.9.21 turns the pairs (cartwheel, rule
  sets) into a set of cartwheels. There are exactly as many pairs as
  cartwheels (9,366 and 728), so reading C′ with or without deduplication
  gives the same counts.

### A.10 (Lemmas A.4-A.6): prefilter check and projection (not run in full)

The sets after `deleteDegreeFromKto9` hold 5,365 cartwheels for A.4, 1,618
for A.5, and 298 for A.6 (after removing those blocked by T73). The
*roots*, the cartwheels a check starts from, are:

- A.4: 393. There are 213 in case (i) (a degree-8 neighbour) and 180 in
  case (iii) (two or more degree-7 neighbours); no root falls in case (ii).
- A.5: 1,320, those with two consecutive degree-7 neighbours.
- A.6: 298. There are 23 with one degree-7 neighbour and 275 with two or
  more.

**The prefilter changes nothing.** 90 roots, 30 per check in strides, were
run both with and without the prefilter. For all 90, the results are
identical: the exact structure of every surviving combination, in order,
the number of assertions, and the failed assertions. None failed. The
prefilter rejects more than 99% of the identifications (for example
37,945 of 37,948 for one A.4 root) and cuts the mean time per root as
follows:

| Check | Mean per root without prefilter | Mean per root with prefilter (same roots) |
| --- | --- | --- |
| A.4 | 24.7 s | 7.6 s |
| A.5 | 7.95 s | 0.18 s |
| A.6 | 1.41 s | 0.18 s |

**Timing and projection**, with the prefilter. The samples are 120
strided roots for A.4 and A.5 and the 30 above for A.6. Nothing timed out
(cap 1500 s) and no assertion failed.

| Check | Roots | Sampled | Mean | Median | Max | Projected CPU |
| --- | --- | --- | --- | --- | --- | --- |
| A.4 (Lemma 8.3) | 393 | 120 | 12.7 s | 1.2 s | 120 s | 1.4 h |
| A.5 (Lemma 8.5) | 1,320 | 120 | 0.25 s | 0.11 s | 5.9 s | 0.09 h |
| A.6 (Lemma 8.6) | 298 | 30 | 0.18 s | 0.09 s | 0.96 s | 0.015 h |
| **total** | | | | | | **about 1.5 CPU-hours** |

- **How long the full run should take.** On 17 processes that is about 6
  minutes of balanced work, plus the slowest root (at least 2 minutes). We
  expect **10-20 minutes of wall time**. Memory would be about 2.5 GB: 17
  workers, each holding Ds and C_all. That was the session peak of the
  sample runs.
- **What drives the cost.** A.4 is heavy-tailed. The cost follows the number
  of free images, which runs to 290,000 for one root, because A.4.9 splits
  tail ranges. The A.4 mean rose from 7.6 s over 30 roots to 12.7 s over
  120, so allow 1-3 CPU-hours.
- **Without the prefilter** the same projection gives about 5.7 CPU-hours.
- **X is exercised.** In the sampled case (iii) roots of A.4, `containX`
  ran 5 times on surviving combinations and found X each time. The other
  71 pairs left no combination at all. So our transcription of Figure 12
  is now also used by, and satisfies, the check it exists for.

## Phase 3 results: Lemmas A.4-A.6 (A.10) in full

The run was detached, on 17 processes, at commit 7bf9ca7, with the
prefilter on. The record is in `results/phase3/`. The per-root payload is
`a10-roots.jsonl`, whose payload sha256 is `aeafff71…`; it stays in WSL at
`/home/claude/f2-final/`.

| Lemma | Check | Roots | Roots passed | Assertions checked | Failed | Exceptions | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8.3 | A.4 (A.10.4-A.10.8) | 393 | 393 | 528 | 0 | 0 | **pass** |
| 8.5 | A.5 (A.10.9) | 1,320 | 1,320 | 1,838 | 0 | 0 | **pass** |
| 8.6 | A.6 (A.10.10-A.10.12) | 298 | 298 | 630 | 0 | 0 | **pass** |

- **What the assertions were:**
  - A.4: 276 checks of case (i) ("88"). 247 case-(iii) pairs left no
    combination at all, and the 5 that did left combinations that all
    contain X ("787"). No root is in case (ii).
  - A.5: 1,838 degree-7 triangles, all blocked.
  - A.6: 23 case-(i) and 607 case-(ii) checks, all blocked.
- **Time and memory:** 4.3 min of wall time and 4,339 CPU-seconds (1.2 h;
  the projection was 1.5 h). By check, A.4/A.5/A.6 took 3,918/314/107
  CPU-seconds. The slowest root was A.4 #5001 at 156 s. The session peak
  was 2.5 GB, and the largest worker 212 MB.
- **Prefilter equivalence, second check.** 65 further roots were rerun
  without the prefilter and compared with the full run. They were the 20
  slowest A.4 roots plus 15 strided roots per check, none of them among
  the 90 compared in phase 2. **All 65 are identical**, down to the exact
  structure of every surviving combination and every assertion. The
  slowest root took 156 s with the prefilter and 257 s without. With
  phase 2, 155 distinct roots have now been compared, with no difference.
  That rerun took 4.3 min of wall time and 2,641 CPU-seconds, peaking at
  2.6 GB.

## How to run

The whole pipeline, from a clean checkout, is one command:

```bash
git lfs pull                                    # the data must be real files
python3 checks/f2/run.py all --jobs 17 --out DIR
```

It runs A.1, A.2, the X/T73 checks, the wheels for centre degrees 7-11,
the bad-cartwheel enumeration and Lemmas A.4-A.6, one after another, into
DIR. Results are in `DIR/summary.json`.

**Verified from a clean checkout.** On the self-hosted machine we made a
fresh clone at commit 7bf9ca7 (after `git lfs pull`, which took about 3
min) and ran `run.py all --jobs 17`.

- **Time:** 54 min of wall time, broken down as follows:
  - A.1, A.2 and the X checks: under 4 s;
  - wheels for degrees 7-11: 5 s, 10 s, 34 s, 2.8 min and 14.0 min;
  - bad cartwheels: 32.0 min;
  - A.10: 4.5 min.
- **Memory:** the session peak was 2.6 GB.
- **Output:** all eleven payloads were byte-identical to the step-by-step
  runs. Those are A.1, A.2, the X checks, the five wheel files, C_all, the
  per-wheel bad-cartwheel record and the A.10 per-root record. See
  `results/phase3/clean-all-compare.json`.

The steps can also be run one by one:

```bash
git lfs pull                                   # the data must be real files
python3 checks/f2/run.py phase1                # A.1, A.2, X/T73 checks, wheels d=7
python3 checks/f2/run.py a1 [--order reversed]
python3 checks/f2/run.py a2 [--order reversed] [--literal]
python3 checks/f2/run.py wheels --degree 7 [--jobs 16] [--literal]
python3 checks/f2/run.py special
# phase 2 (use --out DIR for all of these; `bad` reads wheels-7..11.txt there)
python3 checks/f2/run.py wheels --degree 11 --jobs 17 --out DIR
python3 checks/f2/run.py bad --jobs 17 --out DIR          # resumable
python3 checks/f2/run.py a10-sample --compare --count 30 --jobs 17 --out DIR
python3 checks/f2/run.py a10 --jobs 17 --out DIR          # reads call.jsonl; resumable
python3 checks/f2/run.py a10-verify --jobs 17 --heaviest 20 --count 15 --out DIR
# projection helpers (samples; not results):
python3 checks/f2/run.py sample-wheels --degree 11 --count 2000
python3 checks/f2/run.py sample-bad --degree 8 --count 40 --pool 12000
```

Output goes to `checks/f2/out/` (git-ignored) unless `--out DIR` is given.
Each run adds its entry to `summary.json` (results) and `timings.json`
(times, peak RSS). Standard library only. There is no randomness, and sets
are written in sorted order.

## Output formats (ours)

Every file begins with `# ` lines: tool, paper, repository commit (flagged if
`checks/f2` had local changes), Python version, host, platform, command,
and the sha256 of the payload, which is the rest of the file. The payload
depends only on the inputs and options, so reruns can be compared by
digest.

- `a1-rstar.jsonl`, `a2-rstar-d.jsonl`: one combined rule per line, as a
  JSON object `{charge, rules, lo, hi, head, rev, succ, pred}`. `rules`
  lists the file stems of the original rules combined. `lo`/`hi` are the
  degree ranges per vertex, with `null` for infinity. The four dart pointer
  lists use -1 for nil. The numbering is the canonical form described
  below; dart 0 is the rule's dart s->t, and its head is vertex 0. Lines
  are sorted.
- `wheels-<d>.txt`: one line per wheel of A.9.5, in A.9.5's order:
  `d n1 ... nd verdict`, where `n1..nd` are the neighbour degrees in
  clockwise order and the verdict is `survives`, `charge` (A.9.13 bound
  < 0) or `blocked` (A.7.1). The survivors are C^d_0.
- `special.txt`: one line per check, `name <TAB> ok|FAIL <TAB> check <TAB>
  detail`.
- `call.jsonl` (C_all): one bad cartwheel per line,
  `{"d", "wheel", "lo", "hi"}`. `d` and `wheel` (the neighbour degrees)
  rebuild the structure with A.9.6 `generateCartwheel(d, wheel)`, which
  fixes the vertex numbering: 0 is the centre, 1..d its neighbours
  clockwise, then the second neighbours in the order A.9.6 creates them.
  `lo`/`hi` are the degree ranges in that numbering. Lines are ordered by
  degree, then by the wheel's position in `wheels-<d>.txt`, then in the
  order A.9.21 produced them.
- `bad-wheels.jsonl`: one line per C0 wheel, in the same order:
  `{"d", "wheel", "bad", "pairs", "C_i", "failures"}`. These are the number
  of bad cartwheels, the number of (cartwheel, rule sets) pairs before
  deduplication, the size of each C_i in fixInRules, and every failed
  assertion or invariant (an empty list if none).
- `bad-progress.jsonl`: the working file of `bad`, one line per finished
  wheel with its time. It is not a payload, because its order depends on
  scheduling.
- `a10-roots.jsonl`: one line per root of Lemmas A.4-A.6, in
  (check, root) order:
  `{"check", "root", "call_index", "results", "failed", "exception", "signature"}`.
  - `root` is the root's position in the check's set after
    `deleteDegreeFromKto9`, and for A.6 after removing the cartwheels
    blocked by T73.
  - `call_index` is its line in `call.jsonl`, counting from 0.
  - `results` lists each assertion as `[kind, ok, detail]`. The kinds are
    `88`, `87`, `787`, `787 (no combination)`, `7triangle`, `77` and `777`,
    after the algorithms A.10.5-A.10.12. For the `88`, `87`, `7triangle`,
    `77` and `777` kinds, `detail` is the number of combinations left.
  - `signature` is the sha256 of the exact structure of every surviving
    combination.

  `a10-progress.jsonl` is the working file (with times); like
  `bad-progress.jsonl`, it is not a payload.
- `a10-sample` records its per-root rows in `summary.json`. Each row gives
  the time, the counters (identifications tried, prefiltered, free images,
  first-step survivors), the assertions, and a signature: the sha256 of the
  exact structure of every surviving combination, in order.
- `summary.json` / `timings.json`: one entry per run, keyed by step and
  variant.

## Language and dependencies

The implementation is Python with the standard library only. Python makes
the transcription easy to hold against the pseudocode, line by line, which
is the point of an independent check. Phase 1 turned out to be fast in
Python: seconds, not hours. Two things make that possible: exact indexes
(below) and the fact that most homomorphism attempts fail within a few
steps. No dependency was needed. The PDF was read as text with `pdftotext`
(Git for Windows) and the figures in a browser, and neither of those is part
of the code.

## Files

| File | What |
| --- | --- |
| `run.py` | entry point, output headers, summaries, timings |
| `nl4ct/pseudo.py` | dart representation; A.2.1 `homomorphism`; A.3.1 free homomorphism of a pseudo-triangulation; A.4.1-A.4.9 free homomorphism of a pseudo-configuration with degree ranges; A.5.1 `fromVRotations`; A.6.5 `mirror` |
| `nl4ct/inputs.py` | reading rules and configurations; A.6.1-A.6.4 (cut vertices, ring removal, special dart); building Ds; reading our X/T73 file |
| `nl4ct/blocking.py` | A.6.6-A.6.8 `containConf` (indexed, plus a literal version), A.7.1-A.7.2 blocking |
| `nl4ct/combine.py` | A.8.1-A.8.2 `combineRules` (Lemmas A.1, A.2) |
| `nl4ct/cartwheel.py` | A.9.1-A.9.7 and A.9.11-A.9.13: cartwheel generation, rule application, charge bounds, pruning, `enumPossibleBadWheels` |
| `nl4ct/badcartwheels.py` | A.9.8-A.9.10, A.9.14-A.9.22 (run in full in phase 2) |
| `nl4ct/cartcombine.py` | A.10.1-A.10.12, Lemmas A.4-A.6, organised by roots, with the exact prefilter for A.10.2 (run in full in phase 3) |
| `nl4ct/special.py` | self-consistency checks of the X/T73 transcription |
| `data/special-configurations.json` | our transcription of X (Figure 12), X+w (Figure 13) and T73 |
| `results/phase1/` | the record of the phase-1 run on the self-hosted machine: `summary.json` (results and payload digests), `timings.json`, `special.txt`, `samples.json` (projection samples) and the `/usr/bin/time -v` outputs. The payload files themselves are not committed; `run.py` rebuilds them in seconds, and their sha256 is in `summary.json`. |
| `results/phase2/` | the record of phase 2 (see "Phase 2 results"). The full outputs are not committed; they stay in WSL at `/home/claude/f2-final/`, with their digests in `summary.json` (payloads) and `files.sha256` (whole files). |
| `results/phase3/` | the record of phase 3: `summary.json` (including the per-lemma verdicts under `a10` and the equivalence rerun under `a10-verify`), `timings.json`, `steps.txt`, `time-a10*.txt`, and `files.sha256` for every full output, `a10-roots.jsonl` included. It also holds `clean-all-compare.json` and `time-clean-all.txt`, from the one-command run in a fresh clone. |

## Representation choices (where the paper leaves one open)

- **Pseudo-configurations** (`PC`) hold the four dart pointers of section 9.2
  as parallel integer lists `head`, `rev`, `succ`, `pred`, with -1 for nil.
  Degree ranges are two lists `lo`, `hi`, and infinity is the integer
  `INF = 2^20`. `succ` is the clockwise successor around the head.
  Operations never modify their inputs. After a free homomorphism, vertices
  and darts are renumbered in increasing order of their union-find roots.
- **Maps** (homomorphisms) are pairs of lists (vertex map, dart map).
- **Rule files** are 1-based and use 0 for infinity. The rule's dart is s->t,
  the dart with head t and tail s. On reading, we check that every inner
  vertex's range equals its degree, that every boundary vertex's lower bound
  exceeds its number of neighbours, and that every lower bound is at least
  5 (Definition 4.1).
- **Configuration files** give rotations only for the configuration's own
  vertices. A.6.1 and A.6.3 also need the rotation of the ring vertex that
  is kept when a cut vertex is extended. We derive it with the face rule: if
  q follows p around a, then around q, p follows a. The kept vertex's
  configuration neighbours form a fan, and `ring_fan` checks that the fan
  covers all of them.
- **Ds** is every configuration file, extended at its cut vertex if any (two
  extensions each), plus the mirror image of every entry. Mirrors are added
  even for symmetric configurations, which is harmless. That gives 19,754
  entries: 8,200 files, of which 1,677 have a cut vertex.
- **The single vertices of degree 3 and 4** (in D, but not files) are not in
  Ds. They cannot matter here. A vertex of degree 3 or 4 can only map to a
  target vertex whose representative degree is 3 or 4. Every rule range has
  a lower bound of at least 5, and so every combined-rule range has one too,
  except for the neutral rule R0, which A.8.2 never tests for blocking.
  Cartwheel degrees are 5-9. A one-vertex configuration also has no dart, so
  A.6.4 could not even choose its special dart.
- **Canonical form of a combined rule** (the output payload): darts and
  vertices are renumbered in breadth-first order from the rule's dart,
  following rev, succ and pred. Two combined rules have the same form
  exactly when an orientation-preserving isomorphism maps one onto the
  other, dart onto dart, with the same degree ranges and the same set of
  original rules.

## Speed-ups, and why they cannot change an answer

Each speed-up only skips calls to Algorithm A.2.1 that A.2.1 would itself
reject. `--literal` turns off 1-3, and the phase-1 payloads are
byte-identical with and without it. Item 4 was checked separately (see
"Phase 2 results").

1. **Configuration index** (`blocking.ConfIndex`). A.6.6 tries every
   configuration against every target dart whose endpoint degrees equal
   those of the configuration's special dart f = x->y. A.2.1 must map
   succ^k(f) to succ^k(f*) and pred^k(f) to pred^k(f*). It fails if the
   target pointer is nil where the source pointer is not. With `ginclude`,
   a source vertex of single degree must map to a target vertex of exactly
   that degree. So the degrees met walking around y from f must equal those
   met walking around head(f*) from f*. The only exceptions are auxiliary
   cut-vertex neighbours, which have a degree range, and we treat those
   positions as wildcards. We index by that sequence. Every candidate the
   index returns is still decided by A.2.1.
2. **Rule prefilter** (`cartwheel.amount_of_*`). Before calling A.2.1 for a
   rule and a dart, we apply the two degree tests A.2.1 performs first: at
   the head of the dart, then at its tail.
3. **Early exit in A.9.4.** A.9.4 wants the largest charge among the
   combined rules that do not "never apply". We try them in order of
   decreasing charge and stop at the first that sometimes applies.
4. **Prefilter for A.10.2** (`cartcombine.prefilter_ok`, phase 2). The free
   combination identifying e with e′ gives a homomorphism φ (Lemma 9.4)
   with φ(e) = φ(e′). Hence φ(succ^k e) = φ(succ^k e′) and
   φ(pred^k e) = φ(pred^k e′) wherever both sides are defined, and the
   heads and tails of those darts are identified. A.4.1 intersects the
   degree ranges of identified vertices and gives up on an empty
   intersection. So if the heads, or any such pair of tails, have disjoint
   ranges, the combination is empty and we skip it. We verified that it
   changes nothing on 90 sampled roots, with identical exact results.
   `--literal` does not switch this one off; `run_root(..., prefilter=False)`
   does.

## Ambiguities in the paper, and how we read them

1. **`ginclude` in A.2.** The prose before Algorithm A.2.1 says `ginclude`
   holds when "the degree range [δ*−(φ*(v)), δ*+(φ*(v))] includes the other
   degree range [δ−(v), δ+(v)]", i.e. the *target* range contains the
   *source* range. Every place it is used says the opposite. A.6.8 needs
   δ−(v) ≤ δ*(v*) ≤ δ+(v). Section 11.2.1 defines "always applies" by
   [δ−(v), δ+(v)] ⊇ [δC−(φ(v)), δC+(φ(v))]. A.9.1's output is "R applies
   for every (Z*, δ*)". We use **source ⊇ target**. The literal reading
   would also be unsound for A.9.1 and A.10.8. The scratch experiment above
   shows that the targets rule it out: 889/6 and 6174 instead of 671/5 and
   5439.
2. **What |R*| counts.** A.8.2 returns R* with the neutral rule R0 in it.
   Our 1832 and 671 include R0. Without it they would be 1831 and 670. The
   exact match suggests the published numbers include R0 as well.
3. **Lemma 10.2 and auxiliary vertices.** The proof says no vertex of a
   reducible configuration has degree above 12. The auxiliary vertex of a
   cut-vertex extension has range [d+1, ∞], so it can map to a vertex whose
   representative degree is its upper bound (A.7.2). This stays sound here
   because every auxiliary vertex in Ds has lower bound 4 or 5, which we
   checked: 5,808 entries have 4 and 900 have 5. Every target range starts
   at 5 or more, so such a map works for every concrete degree in the
   range.
4. **Vertex order in A.4.6 and A.4.9** ("for all v"). We use increasing
   vertex number. Reversing the *rule* order leaves the sets of combined
   rules unchanged, which is evidence that the result does not depend on
   such orders. We did not vary the vertex order itself.
5. **A.4.8** overwrites succ(rev(e_first)) and pred(rev(e_last)) without
   saying that they were nil. In a pseudo-configuration they must be (M5).
   We assert it, and the assertion has never fired.
6. **`gdominant`** (A.9.15): "δ+(v) = ∞ or δ*+(v*) < 9". This is our
   reading of section 11.2.4, confirmed from the MathML of the arXiv HTML.
7. **Later phases:**
   - A.9.21 line 7, "assert C = 0", is read as "the upper bound of A.9.13
     equals 0". The text of section 11.2 says "We checked that all of them
     are 0". It held for every element of C in phase 2.
   - Sets are sets. The final C′ of A.9.21 deduplicates cartwheels with
     equal degree ranges. In phase 2 this turned out not to matter: there
     are exactly as many pairs as cartwheels.
   - The assertions of A.9.21 are checked for every element of C, that is,
     every (cartwheel, rule sets) pair, as line 3 iterates over C, and not
     only once per deduplicated cartwheel.
   - A.10.10 line 3 replaces C by the cartwheels not blocked by T73. We use
     this filtered C both for the roots and as the partner set in
     A.10.11/A.10.12, as the pseudocode passes it on.
   - A.10.4 has no root in case (ii) (exactly one degree-7 neighbour and no
     degree-8 neighbour), so A.10.6 is never exercised on the real C_all.
     This is an observation, not a choice.
   - A.10.2 line 6 picks "an arbitrary vertex" as the centre for blocking.
     We pick the image of the first cartwheel's centre (see the
     `cartcombine.py` docstring for why this is harmless).
   - A.10.3 line 1 blocks the first combination with Ds even when the caller
     passes D ∪ {T73}. We follow the text.
   - A.10.8 `containX` uses `ginclude`, so X is found only where the image
     vertices have fixed degrees equal to X's.
   - A.9.9 can produce an empty range, for instance when two rule vertices
     map to one cartwheel vertex. A.9.10 then yields nothing, so the branch
     is dropped.

## X and T73

`data/special-configurations.json` is our own format. Each vertex has a
name, its degree, and its neighbours in clockwise order, with `|` for the
outer gap. The entries are:

- **X**, transcribed from Figure 12. The figure is `exception-zero.svg` on
  the paper's arXiv HTML page, and degrees follow Figure 2's shapes: filled
  disc 5, open circle 7, open square 8. X has 17 vertices: a centre of
  degree 8 (inner), two outer vertices of degree 8, two of degree 7, and
  twelve of degree 5.
- **Xw**: X with the degree-5 vertex w of Figure 13 (middle).
- **T73**: one triangle with three vertices of degree 7 (section 8).

`run.py special` checks each entry:

- inner vertices have exactly their degree, and boundary vertices have
  fewer neighbours than their degree;
- one incidence list per vertex (M6);
- every inner angle closes a consistently oriented triangle (M5);
- V − E + F = 1;
- the boundary is a single cycle, so there is no cut vertex;
- `resolveDegreeIssues` returns the entry unchanged;
- X is inner-centred of degree 8 and **not** blocked by Ds;
- Xw **is** blocked by Ds (by D1774, as Figure 13 shows).

These checks show that the transcription is a valid configuration. They do
not show that it is the configuration the authors meant, so a human should
compare the JSON with Figure 12. X is symmetric under the left-right
reflection, which is why A.10.8 does not need its mirror.

## Cost: projections against measurements

| Step | Phase-1 projection | Measured (17 processes) |
| --- | --- | --- |
| A.1, A.2, X/T73, wheels for degree 7 | (measured in phase 1) | about 20 s serially |
| wheels, degrees 8-11 | about 2.2 CPU-hours, about 8 min | 18.1 min wall; session peak 1.8 GB |
| enumBadCartwheels over all of C0 | about 8 CPU-hours (5-15 h), 30-60 min | 9.0 CPU-hours, 31.8 min wall; session peak 1.2 GB |
| A.10, Lemmas A.4-A.6 | unknown: 1 h to days (phase 2: about 1.5 CPU-hours) | 1.2 CPU-hours, 4.3 min wall; session peak 2.5 GB |

End to end, the pipeline takes about an hour on 17 processes. For
comparison, the other implementation took about 70 minutes end to end in
optimized C++ on 20 threads. Its slowest step, the degree-11 wheel
enumeration, took 33 min single-threaded and 12.3 GB. Ours took 14.3 min
on 17 processes and 1.8 GB for the whole session.

Python was enough, with no PyPy and no compiled code. The prefilter was
what made A.10 cheap. Without it, the A.10 samples project to about 5.7
CPU-hours.

## Unfinished, unverified, uncertain

- **No object-by-object comparison with F1 yet.** Our outputs are ready for
  it in WSL at `/home/claude/f2-final/`, with digests in
  `results/phase3/files.sha256`. The main session will do it. Until then,
  the agreement between F1 and F2 is on counts and pass/fail verdicts only.
- **Prefilter equivalence** rests on the argument under "Speed-ups" and on
  155 roots compared with and without it, all identical: the 90 of phase 2
  and the 65 of phase 3, including the 20 slowest A.4 roots. It was not
  compared on all 2,011 roots.
- **Resuming** (`bad`, `a10`) has been tested only on small slices; the
  full runs went straight through.
- **Figures 7 and 8.** The agreement rests on rule sets and counts, not on
  an isomorphism check.
- **X.** The transcription passed its consistency checks, and in the full
  A.4 run `containX` found X in all 5 cases that reached it. A second
  person has still not compared it with Figure 12.
- **A.10.6** (case (ii) of Lemma 8.3) has no root in C_all, so that branch
  of our code has never run on real input.

## Independence log

Everything consulted for this task beyond the paper PDF, `input-formats.md`
and the repository files the brief allows:

- **The paper's arXiv HTML page**, https://arxiv.org/html/2603.24880v2, which
  the brief allows. From it we used:
  - the SVG figures `exception-zero.svg` (Figure 12), `ShapesVertices.svg`
    (Figure 2) and `reducible_by_2X.svg` (Figure 13), plus the inline SVG of
    Figure 8 and the figure list (to count its pictures);
  - the MathML/TeX text of section A.2, section 11.2.1, section 11.2.4,
    Lemma 10.2 and Algorithms A.4.4-A.4.9, A.6.2, A.6.6, A.7.2, A.9.15,
    A.9.21 and A.10.1. We read these because `pdftotext` drops the relation
    symbols.
- **Tools, not sources**: `pdftotext` (Git for Windows' poppler) to read the
  PDF as text, and the browser pane to render the SVGs.
- **Our repository, beyond the list in the brief**:
  - `checks/README.md`, which mentions F1 only in general terms;
  - the headings of `notes/F-ai-and-computation-engine.md`, listed with
    `grep -n "^#"`, which showed the title of the F1 section but none of its
    text;
  - `git log --oneline -3` on `main`, which showed the subjects of the F1
    merge commit and of "F1: the near-linear computer checks reproduce;
    results and run times".
- **The session's memory notes** (Claude's auto-memory for this project)
  were in context. They say that F1 met all 11 targets, that A.4-A.6
  passed, and that the F1 run takes about 70 min and peaks at 12.3 GB,
  facts the brief also gives. They contain no implementation detail.
- **Not consulted**:
  - `third_party/near-linear-4ct/computer-checks` (the submodule was not
    initialized);
  - any upstream GitHub page or API other than the data already in the
    repository;
  - `checks/f1/`, the F1 section of the notes, PR #30 and issue #6;
  - `/home/claude/f1-artifacts`;
  - the unlicensed reimplementations and `instructions-for-checking-reproducibility`;
  - any web search.
- **Phases 2 and 3: unchanged.** Nothing beyond the list above was
  consulted, and no F1 output was looked at: `/home/claude/f1-artifacts`
  was not opened. The work in WSL used only these locations:
  - `/home/claude/f2-work`, `/home/claude/f2-final` and
    `/home/claude/f2-phase2`;
  - for the clean-checkout run of phase 3, `/home/claude/f2-clean` and
    `/home/claude/f2-clean-out`;
  - two scratch scripts of ours in `/home/claude` that broke the A.10
    sample down by case (since deleted).
