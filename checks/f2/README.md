# F2: the near-linear computer checks, reimplemented independently

Task F2. This is a second implementation of the computer checks in
"The Four Color Theorem with Linearly Many Reducible Configurations and
Near-Linear Time Coloring" (Inoue, Kawarabayashi, Miyashita, Mohar,
Thomassen, Thorup; **arXiv:2603.24880v2, 7 May 2026**). It is written from
the paper's pseudocode (appendix A) and main text only. Its value is as a
cross-check of the upstream C++ run in task F1, so it was written without
looking at that code or at any other reimplementation. The **Independence
log** at the end lists everything that was consulted.

**Status: phase 1.** Lemma A.1, Lemma A.2 and `enumPossibleBadWheels` for
centre degree 7 are implemented, run and measured. All five phase-1 numbers
match the published targets. The later steps (the bad-cartwheel enumeration
and Lemmas A.4-A.6) are transcribed from the pseudocode, but they have only
been run on samples, for timing. Treat them as drafts.

## Phase 1 results

These were run on the self-hosted machine (WSL2 Ubuntu, 20 CPUs, 25 GB,
Python 3.14.4), one process each, measured with `/usr/bin/time -v`. The
full record is in `results/phase1/`.

| Check | Observed | Published target | Wall time | Peak RSS |
| --- | --- | --- | --- | --- |
| A.1: size of R* | **1832** | 1832 | 2.2 s | 31 MB |
| A.1: max charge in R* | **8** | 8 | (same run) | |
| A.2: size of R*-D | **671** | 671 | 1.6 s | 66 MB |
| A.2: max charge in R*-D | **5** | 5 | (same run) | |
| A.9.7, centre degree 7: wheels kept | **5439** | 5439 | 16.9 s | 68 MB |

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
| `--literal`: no speed-ups (A.6.6 tried over all 19,754 configurations, no prefilters, no early exit) | A.2 and the degree-7 wheels give byte-identical payloads (A.2: 13.6 s; wheels: 87 s on 16 processes). |
| Windows, Python 3.12 vs WSL, Python 3.14 | Identical payload digests for A.1, A.2 and the degree-7 wheels. |
| `ginclude` read the other way round (a scratch experiment, not in the code; see ambiguity 1) | A.2 gives 889 combinations with max charge 6, and 5439 becomes 6174. The targets therefore discriminate between the two readings, and only the one we use reproduces them. |

Payload sha256 digests (WSL run, `results/phase1/summary.json`):
A.1 `a91da734…`, A.2 `937b336e…`, degree 7 `cf0f6e83…`.

## How to run

```bash
git lfs pull                                   # the data must be real files
python3 checks/f2/run.py phase1                # A.1, A.2, X/T73 checks, wheels d=7
python3 checks/f2/run.py a1 [--order reversed]
python3 checks/f2/run.py a2 [--order reversed] [--literal]
python3 checks/f2/run.py wheels --degree 7 [--jobs 16] [--literal]
python3 checks/f2/run.py special
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
| `nl4ct/badcartwheels.py` | A.9.8-A.9.10, A.9.14-A.9.22 (**draft**, run only on samples) |
| `nl4ct/cartcombine.py` | A.10.1-A.10.12, Lemmas A.4-A.6 (**draft, never run**) |
| `nl4ct/special.py` | self-consistency checks of the X/T73 transcription |
| `data/special-configurations.json` | our transcription of X (Figure 12), X+w (Figure 13) and T73 |
| `results/phase1/` | the record of the phase-1 run on the self-hosted machine: `summary.json` (results and payload digests), `timings.json`, `special.txt`, `samples.json` (projection samples) and the `/usr/bin/time -v` outputs. The payload files themselves are not committed; `run.py` rebuilds them in seconds, and their sha256 is in `summary.json`. |

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
reject. `--literal` turns all of them off, and the phase-1 payloads are
byte-identical with and without it.

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
7. **Later phases (drafts):**
   - A.9.21 line 7, "assert C = 0", is read as "the upper bound of A.9.13
     equals 0". The text of section 11.2 says "We checked that all of them
     are 0".
   - Sets are sets. The final C′ of A.9.21 deduplicates cartwheels with
     equal degree ranges, which affects the published counts 9366 and 728.
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

## Projection of the full run (Python, not run)

The projection comes from the measurements above and from samples. The
per-wheel times come from `timings.json` and `results/phase1/samples.json`.
Nothing heavy was run.

| Step | Basis | Projected CPU time | On 18 processes |
| --- | --- | --- | --- |
| A.9.7 wheels, d=8, 9, 10, 11 (48,915 / 217,045 / 976,887 / 4,438,925 wheels) | 2,000-wheel samples: 1.14, 1.19, 1.35, 1.41 ms per wheel | 1 min, 4 min, 22 min, 1.7 h; about 2.2 h in all | about 8 min |
| memory for d=11 | the wheel list is held in memory | about 0.7 GB (main process) | + about 70 MB per worker |
| enumBadCartwheels (A.9.21) on C0 = 5439 / 6790 / 3285 / 626 / 8 wheels | samples of 40 / 40 / 20 / 10 wheels: mean 1.01 / 2.95 / 1.12 / 0.14 s per wheel, heavy tail (max 32 s) | about 1.5 h + 5.6 h + 1.0 h + 2 min + negligible, so **about 8 h** (sampling error: perhaps 5-15 h) | about 30-60 min |
| A.10, Lemmas A.4-A.6 | not measurable yet (needs C_all); see below | **unknown**: from about 1 h to days | |

For comparison, the other implementation took about 70 minutes end to end
in optimized C++ on 20 threads. Its slowest step, the degree-11 wheel
enumeration, took 33 min single-threaded and 12.3 GB. Our projection for
that step is 1.7 h single-threaded and under 1 GB. The per-step speed ratio
between the two is therefore not a constant: our exact indexes matter more
than the language.

**A.10 is the open risk.** A literal A.10.2 tries every pair (cartwheel,
centre dart) against the root dart, about |C| × 7.5 free combinations per
root, where |C| is a few thousand after `deleteDegreeFromKto9`. We timed
free combinations of C0-like cartwheels whose centre and endpoint degrees
match, on WSL:

- a combination that fails costs about 190 µs;
- a combination that succeeds can produce hundreds to thousands of free
  images, because A.4.9 splits the [5,9] tail ranges. The test averaged
  about 1,370 images per success, at about 85 µs per image and 25 µs per
  blocking test.

The real C_all cartwheels have many tails already refined, so this figure
is an upper-side guess, not a measurement. Our recommendation for phase 2:

1. Run the bad-cartwheel enumeration (about 8 h CPU, 30-60 min on 18
   processes) and **measure A.10 on a sample of C_all** before committing to
   a full run.
2. Add an exact prefilter for A.10.2, in the same spirit as the
   configuration index. The rotations around the two identified centres are
   both cyclic, so they must have equal length and pairwise intersecting
   ranges. Also parallelize over roots with `multiprocessing`, which is
   already used for the wheels.
3. Only if A.10 still projects to more than several hours on 18 processes:
   try PyPy first. It needs no code change, and the code is pure Python on
   lists. Only after that consider a compiled hot spot: A.2.1, A.3.1 and
   A.4.x. Changing language is Gabriel's decision, and we do not recommend
   it now.

## Unfinished, unverified, uncertain

- `badcartwheels.py` and `cartcombine.py` are drafts. The first ran on 110
  sampled wheels, where no assertion of A.9.21 failed, and the numbers of
  bad cartwheels per wheel were in line with 9366/5439 and 728/6790. The
  second has never run. Neither output has been compared with anything.
- The degree 8-11 wheel counts (6790, 3285, 626, 8) have not been computed.
  The samples only suggest they are in range: the pool fractions give
  roughly 6,880, 3,390 and 580 for degrees 8-10.
- The agreement with Figures 7 and 8 rests on rule sets and counts, not on
  an isomorphism check.
- The X transcription has passed consistency checks but has not been
  checked against the figure by a second person.

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
