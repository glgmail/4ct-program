# Workstream F — AI and computation engine

Results log. Newest first. One row per result, added in the pull request that
produced it.

A row belongs here only if it meets the trust rule: a Lean theorem that builds
on the pinned toolchain, or a script whose output reruns identically from a
clean checkout. Leads, partial arguments and AI-written summaries go under
"Open leads" instead, and are not results.

| Date | Result | Evidence | Tier | PR |
| --- | --- | --- | --- | --- |
| 2026-09-28 | **F1 and F2 agree object by object.** R* (1,832), R*−D (671), the surviving wheels for every centre degree 7–11 (5439 / 6790 / 3285 / 626 / 8) and the 10,094 bad cartwheels are identical as multisets up to orientation-preserving isomorphism. Lemmas A.4–A.6 run on sets of the same sizes (5,365 / 1,618 / 298) and both pass. | `checks/f1_vs_f2/compare.py` → `checks/f1_vs_f2/result.txt`; negative controls in `checks/f1_vs_f2/README.md`; section "F1 against F2" below | F2 | PR_NUMBER |
| 2026-09-28 | **An independent implementation of the near-linear checks, written from the paper's pseudocode, reproduces all 11 published targets. Lemmas A.4, A.5 and A.6 pass on every one of their 393, 1,320 and 298 roots**, with no assertion, invariant or exception failing. One command reruns it byte-identically from a clean checkout. | `python3 checks/f2/run.py all --jobs 17`, clean clone at `7bf9ca7`, all payloads byte-identical to the step-by-step runs; `checks/f2/README.md`, including its independence log | F2 | PR_NUMBER |
| 2026-09-28 | **Every computer check of the near-linear proof reproduces with the upstream C++ code: all 11 published target values are met, and Lemmas A.4, A.5 and A.6 pass.** Their anti-vacuity controls fail as they must. `results.txt` reruns byte-identically. Run on WSL2 on a Windows host, not on the authors' machine. | `checks/f1/reproduce.sh`, two full runs from clean clones at `13d13fa`, identical `checks/f1/results/results.txt` (sha256 `2a040b05b0a6500341ace07d7d066aa371d695697804d88fcf2a8b9c8b6c1ecb`); section "F1" below | F1 | #30 |
| 2026-09-27 | **No two of the 8,202 configurations in D are isomorphic, even allowing reflection.** 7,949 are chiral and 253 are not, and no chiral configuration's mirror image is in D: the set lists each configuration once up to reflection. | `search/index/build.py` (canonical codes), confirmed by `search/index/crosscheck.py`: all 8,202 Weisfeiler–Lehman hashes of the free completions are distinct, so no pair is isomorphic; chirality recomputed by oriented isomorphism against each mirror image | F3 | #29 |
| 2026-09-27 | **The configuration index rebuilds byte-identically.** `search/index/configurations.csv`, 8,202 rows, sha256 `7e55964e402792b4e597b54e28b7daf9b23cdedca99aa0861f01be2ebe9b4e89`. | `python3 search/index/build.py --check`, run on Windows and on Linux | F3 | #29 |

## F2: the checks, reimplemented independently

The second implementation. It is in Python, standard library only, and was
written from the paper's appendix A (arXiv:2603.24880v2) and main text. Its
author was a separate agent, never shown the upstream C++, F1's driver or
F1's outputs. It was given only the paper and the configuration and rule
sections of upstream's `FORMAT.md`, needed to read the input data. Its
independence log, in `checks/f2/README.md`, records everything else it
consulted: the paper's arXiv HTML page for figures and formulas, and a few
of our own files. None of it is an implementation.

| Lemma | Metric | Published | F2 |
| --- | --- | --- | --- |
| A.1 | size of R* / maximum charge | 1832 / 8 | 1832 / 8 |
| A.2 | size of R*−D / maximum charge | 671 / 5 | 671 / 5 |
| A.3 | wheels, centre degree 7 / 8 / 9 / 10 / 11 | 5439 / 6790 / 3285 / 626 / 8 | 5439 / 6790 / 3285 / 626 / 8 |
| A.3 | bad cartwheels with tail ranges, centre degree 7 / 8 | 9366 / 728 | 9366 / 728 |
| A.4 | degree-8 check (Lemma 8.3) | passes | passes: 393 roots, 528 checks |
| A.5 | 7-triangle check (Lemma 8.5) | passes | passes: 1,320 roots, 1,838 checks |
| A.6 | degree-7 check (Lemma 8.6) | passes | passes: 298 roots, 630 checks |

**Readings of the paper.** Two of them decide the results; the targets
confirm both, and both are argued in the F2 README:
- One sentence in the paper states the degree-range inclusion `ginclude`
  the wrong way round; every use of it needs the other reading. The
  other reading gives 889 and 6174 instead of 671 and 5439.
- The published |R*| counts the neutral combination R0.

**The special configurations.** X (Figure 12) and T₇³ (Section 8) were
transcribed from the paper. The session that ran F1, not F2's author, then
compared the transcribed X with the one in the unlicensed
`instructions-for-checking-reproducibility`. That was read-only, the copy
was discarded, and nothing was copied. They are the same configuration up to
relabelling and reflection; the comparison was confirmed to fail on a
deliberately altered X.

**Cost:**
- One command, `run.py all --jobs 17`, takes 54 minutes on the self-hosted
  machine (17 processes), with a summed peak of 2.6 GB. F1's C++ needed
  12.3 GB.
- The bad-cartwheel enumeration takes 32 minutes, the wheels 18 minutes
  (degree 11: 14), and A.4–A.6 4.5 minutes. The last uses an exact
  prefilter, shown to change nothing on 155 roots checked with and without it.

**Not covered:** case (ii) of Lemma 8.3 has no root in C_all, so that
branch of A.4 never runs on real input, in F2 or, presumably, in F1.

## F1 against F2

Compared object by object by `checks/f1_vs_f2/compare.py`. Each object is
put in a canonical form: a rule is rooted at its dart s→t, a cartwheel at
its centre. Two objects match when an orientation-preserving isomorphism
keeps the root and every degree range, and, for a rule, its charge and its
set of original rules. Each set is compared as a multiset.

| Item | F1 | F2 | Agreement |
| --- | --- | --- | --- |
| R* (A.1) | 1,832 | 1,832 | identical objects |
| R*−D (A.2) | 671 | 671 | identical objects |
| wheels C0, centre degree 7 / 8 / 9 / 10 / 11 (A.3) | 5439 / 6790 / 3285 / 626 / 8 | same | identical objects, each degree |
| bad cartwheels C_all (A.3) | 10,094 | 10,094 | identical objects, including the same 7 repeats (10,087 distinct) |
| bad cartwheels, centre degree 9–11 | 0 | 0 | agree |
| configurations as loaded (all mirrors and cut-vertex extensions) | 19,754 | 19,754 | agree (count) |
| A.4 working set after removing degree-9 neighbours | 5,365 | 5,365 | agree (count); both pass |
| A.5 working set | 1,618 | 1,618 | agree (count); both pass |
| A.6 working set | 298 | 298 | agree (count); both pass |

**No disagreement.** A.4–A.6 are compared only by verdict and by working-set
size: F1's checker does not record anything per case. The negative
controls for the comparison are in `checks/f1_vs_f2/README.md`.

## F1: the near-linear computer checks, reproduced

**Every published target was met.** All 11 values published in
`near-linear-4ct/instructions-for-checking-reproducibility` match, and
Lemmas A.4, A.5 and A.6, which have no numeric target, pass. Nothing differs.

**Setup:**
- **Code:** upstream `near-linear-4ct/computer-checks` @ `6cb8566`, unmodified, built as its README says.
- **Data:** `data/near-linear-4ct/` (F3), which is byte-identical to upstream.
- **Driver:** `checks/f1/reproduce.sh`; see `checks/f1/README.md` for how it works and where its orchestration departs from upstream's two shell scripts.
- **Platform:** these numbers were produced on **WSL2 on a Windows host**, not on the machine the authors used. The distro sees 20 CPUs and 25 GB of memory, runs kernel `6.18.33.2-microsoft-standard-WSL2`, and built with GCC 15.2.0, CMake 4.2.3 and `-std=gnu++23 -O2 -Wall`, without `NDEBUG`. The full header is in `checks/f1/results/env.txt`.

| Lemma | Metric | Published | Observed |
| --- | --- | --- | --- |
| A.1 | size of R* | 1832 | 1832 |
| A.1 | maximum charge of a combined rule in R* | 8 | 8 |
| A.2 | size of R*−D | 671 | 671 |
| A.2 | maximum charge of a combined rule in R*−D | 5 | 5 |
| A.3 | wheels from `enumPossibleBadWheels`, centre degree 7 | 5439 | 5439 |
| A.3 | … centre degree 8 | 6790 | 6790 |
| A.3 | … centre degree 9 | 3285 | 3285 |
| A.3 | … centre degree 10 | 626 | 626 |
| A.3 | … centre degree 11 | 8 | 8 |
| A.3 | bad cartwheels with tail ranges, centre degree 7 | 9366 | 9366 |
| A.3 | bad cartwheels with tail ranges, centre degree 8 | 728 | 728 |
| A.4 | degree-8 check (5,365 cartwheels) | passes | passes |
| A.5 | 7-triangle check (1,618 cartwheels) | passes | passes |
| A.6 | degree-7 check (298 cartwheels) | passes | passes |

**Also observed**, with no published target:
- **Degrees 9–11.** The cartwheel jobs for centre degrees 9, 10 and 11 (3,285, 626 and 8 jobs) produced no bad cartwheels. This is consistent with the checker's own assertion that a bad cartwheel has centre degree 7 or 8.
- **Exit statuses.** All 16,148 cartwheel jobs exited 0.
- **Configurations as loaded.** The checker loads the 8,200 configuration files as 19,754 configurations: it splits configurations at cut vertices and adds every mirror image itself. That fits F3's finding that D lists each configuration once up to reflection.
- **Unit tests.** Upstream's 25 unit tests pass.

**Anti-vacuity.** A.4–A.6 fail only through `assert()`. Re-run with no reducible configurations, each aborted on a failed `combined.size() == 0` assertion (exit 134). So the passes above are not vacuous.

**Run times**, from the first of the two runs. They vary between runs and are not part of what is compared:

| Step | Wall time | Peak memory |
| --- | --- | --- |
| build (configure + compile) | 35 s | 585 MB |
| A.1, A.2 | 1 s | 22 MB |
| A.3 wheels, degree 7 / 8 / 9 / 10 | 34 s / 41 s / 95 s / 7 min 15 s | 51 MB / 137 MB / 535 MB / 2.5 GB |
| A.3 wheels, degree 11 (long) | 32 min 49 s | 12.3 GB |
| A.3 cartwheels, degree 7 (5,439 jobs, 20 at a time) | 10 min 47 s | 31 MB per job |
| A.3 cartwheels, degree 8 (6,790 jobs) | 10 min 37 s | 48 MB per job |
| A.3 cartwheels, degrees 9–11 (3,919 jobs) | 2 min 56 s | 32 MB per job |
| A.4 | 7 min 15 s | 868 MB |
| A.5 | 2 min 45 s | 115 MB |
| A.6 | 26 s | 145 MB |
| **whole run** | **1 h 08 min** | **12.3 GB** (degree-11 wheels) |

The five wheel enumerations run concurrently, as upstream runs them. The degree-11 enumeration, which upstream's instructions warn about, is the critical path: about half the run.

## The 8,202 count (F3)

The paper, arXiv:2603.24880v2 (7 May 2026), section 3: "The set 𝒟 consists
of 8202 D-reducible configurations". It includes the configurations
consisting of a single vertex of degree 3 or 4, and all the others use only
vertices of degree at least 5.

Upstream's README for `reducible-configurations` says `D` holds the
configurations of 𝒟 "except for a vertex of degree 3,4".

Counted at the pinned commit `c2ce7a9`:

- `D/` holds **8,200** files, `D0000.conf` to `D8199.conf`. The repository
  holds **8,202** files in all, but the other two are `README.md` and
  `LICENSE`. The match with the paper's 8,202 is a coincidence of totals, not
  a correspondence, so nothing here counts files to reach 8,202.
- In the 8,200 files, every vertex has degree between 5 and 12, which agrees
  with the paper: only the two missing configurations have a vertex of
  degree 3 or 4.
- 8,200 files plus the single vertex of degree 3 plus the single vertex of
  degree 4 gives 8,202. The index, `search/index/configurations.csv`, has a
  row for each: 8,200 with a `path`, and `deg3` and `deg4` without one. Their
  ring sizes, 3 and 4, and shapes are computed from the wheel they complete
  to.
- No two of the 8,202 are the same configuration (first result above), so
  8,202 is a count of distinct configurations. That holds in particular up to
  reflection.

The 84 rules, counted at `d85bfe0`: `R/` holds 84 files covering 43 rules.
Two rules, `rule001` and `rule040`, are symmetric and have one file each; the
other 41 have a `_1` and a `_2` file each (41 × 2 + 2 = 84). This matches the
paper's section 4, where R(1) and R40 are the exceptions.

## Open leads

- _(none yet)_
