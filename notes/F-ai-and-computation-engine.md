# Workstream F — AI and computation engine

Results log. Newest first. One row per result, added in the pull request that
produced it.

A row belongs here only if it meets the trust rule: a Lean theorem that builds
on the pinned toolchain, or a script whose output reruns identically from a
clean checkout. Leads, partial arguments and AI-written summaries go under
"Open leads" instead, and are not results.

| Date | Result | Evidence | Tier | PR |
| --- | --- | --- | --- | --- |
| 2026-09-27 | **No two of the 8,202 configurations in D are isomorphic, even allowing reflection.** 7,949 are chiral and 253 are not, and no chiral configuration's mirror image is in D: the set lists each configuration once up to reflection. | `search/index/build.py` (canonical codes), confirmed by `search/index/crosscheck.py`: all 8,202 Weisfeiler–Lehman hashes of the free completions are distinct, so no pair is isomorphic; chirality recomputed by oriented isomorphism against each mirror image | F3 | PR_NUMBER |
| 2026-09-27 | **The configuration index rebuilds byte-identically.** `search/index/configurations.csv`, 8,202 rows, sha256 `7e55964e402792b4e597b54e28b7daf9b23cdedca99aa0861f01be2ebe9b4e89`. | `python3 search/index/build.py --check`, run on Windows and on Linux | F3 | PR_NUMBER |

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
