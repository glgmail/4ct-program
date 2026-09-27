# 4ct-program (private)

Independent research program toward a conceptual proof of the Four Color Theorem.
Plan of record: the "Four Color Theorem: A Unified Research Program" doc.

## What counts as a result
- A result is either a Lean theorem that builds on the pinned toolchain,
  or a script whose output reruns identically from a clean checkout.
- Every file in lean/Statements/ needs Gabriel's written sign-off in its
  pull request before merge. The Lean kernel checks proofs; it does not
  check that a statement says what we mean.
- Every computation has two independent implementations that agree.
- AI-written arguments, notes and summaries are leads, not results.

## Releases and outside contact
- This repository is private. Nothing leaves it except as a tagged public
  release approved by Gabriel.
- No agent may make the repository public, publish a release, push tags,
  or post to arXiv. Agent tokens have no admin or release rights.
- A claimed tier 3 or tier 4 proof must be formalized in Lean before
  release approval or referee contact.
- Referees are contacted only for internally checked tier 3 or tier 4 results.

## Toolchain
- Lean and Mathlib pinned to v4.34.1. Re-pinned only at gate reviews,
  never to a release candidate.

## Attribution
- Reused code and data keep their licenses and notices: near-linear-4ct
  (MIT), corun1024/4ct (MIT, CeCILL-B credit), RBarish-UTokyo port
  (Apache 2.0), math-comp/fourcolor (CeCILL-B).

## Layout

```
lean/            Rosetta Stone: one module per reformulation + Transfer tactic
  Statements/    short human-readable statement files, one per reformulation
checks/          our own re-implementations of the near-linear proof checks
data/            configurations, rules, polynomials, foam ranks (Git LFS)
search/          unavoidable-set search, learned discharging, conjecture mining
notes/           per-workstream results log
third_party/     git submodules pinned to commits; read-only upstreams
```

## Working in this repository

- `main` is protected. Every change arrives as a pull request; only Gabriel
  merges.
- Two checks gate a pull request: `lean-build` (self-hosted 32 GB runner) and
  `checks` (repository guardrails, GitHub-hosted).
- `third_party/` holds git submodules pinned to commits. Clone with
  `git clone --recurse-submodules`, or run `git submodule update --init`
  after cloning. Nothing in `third_party/` is edited here.
- `data/` is stored in Git LFS. Install `git-lfs` before cloning, and keep
  `data/MANIFEST.csv` in step with what is added: every file needs a path,
  a source URL, a license and a sha256.

## Workstreams

| Key | Workstream |
| --- | --- |
| A | The Rosetta Stone |
| B | Structure and dynamics |
| C | Algebra |
| D | Topology and gauge theory |
| E | Logic and proof complexity |
| F | AI and computation engine |
