# Workstream F — AI and computation engine

Results log. Newest first. One row per result, added in the pull request that
produced it.

A row belongs here only if it meets the trust rule: a Lean theorem that builds
on the pinned toolchain, or a script whose output reruns identically from a
clean checkout. Leads, partial arguments and AI-written summaries go under
"Open leads" instead, and are not results.

| Date | Result | Evidence | Tier | PR |
| --- | --- | --- | --- | --- |
| 2026-09-28 | **Every computer check of the near-linear proof reproduces with the upstream C++ code: all 11 published target values are met, and Lemmas A.4, A.5 and A.6 pass.** Their anti-vacuity controls fail as they must. `results.txt` reruns byte-identically. Run on WSL2 on a Windows host, not on the authors' machine. | `checks/f1/reproduce.sh`, two full runs from clean clones at `13d13fa`, identical `checks/f1/results/results.txt` (sha256 `2a040b05b0a6500341ace07d7d066aa371d695697804d88fcf2a8b9c8b6c1ecb`); section "F1" below | F1 | PR_NUMBER |
| 2026-09-27 | **No two of the 8,202 configurations in D are isomorphic, even allowing reflection.** 7,949 are chiral and 253 are not, and no chiral configuration's mirror image is in D: the set lists each configuration once up to reflection. | `search/index/build.py` (canonical codes), confirmed by `search/index/crosscheck.py`: all 8,202 Weisfeiler–Lehman hashes of the free completions are distinct, so no pair is isomorphic; chirality recomputed by oriented isomorphism against each mirror image | F3 | #29 |
| 2026-09-27 | **The configuration index rebuilds byte-identically.** `search/index/configurations.csv`, 8,202 rows, sha256 `7e55964e402792b4e597b54e28b7daf9b23cdedca99aa0861f01be2ebe9b4e89`. | `python3 search/index/build.py --check`, run on Windows and on Linux | F3 | #29 |

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
