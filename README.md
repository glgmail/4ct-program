# 4ct-program

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
- This repository is public: anyone can read the work in progress. Being
  readable is not the same as being released. A result is announced only as
  a tagged release approved by Gabriel, and nothing here is a claim until
  then.
- No agent may change the repository's visibility, publish a release, push
  tags, or post to arXiv. Agent credentials carry no admin or release
  rights, and the `v*` tag ruleset blocks tag creation by anyone but
  Gabriel.
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

## Licence

This program's own work is licensed under the **Apache License, Version
2.0** — see [`LICENSE`](LICENSE). Apache 2.0 matches Mathlib, which this
program builds on and may one day contribute to.

**That licence does not cover third-party material in this repository**,
which keeps its own:

| Path | Licence |
| --- | --- |
| `lean/FourColor.lean`, `lean/FourColor/`, `lean/scripts/`, `lean/tools/`, `lean/build.sh`, `lean/formalization.yaml`, `lean/UPSTREAM-README.md` | corun1024/4ct: **MIT**, with a **CeCILL-B credit** to Gonthier and Werner that must be preserved — [`lean/LICENSES/corun1024-4ct.txt`](lean/LICENSES/corun1024-4ct.txt) |
| `third_party/` | each submodule under its own licence; see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) |
| `data/` | per file, as recorded in [`data/MANIFEST.csv`](data/MANIFEST.csv) |

Build configuration under `lean/` (`lakefile.toml`, `lean-toolchain`,
`lake-manifest.json`) was derived from corun1024's and merged with this
program's; modifications are listed in `THIRD_PARTY_NOTICES.md`.

## Layout

```
lean/            the Lake package root; see lean/README.md
  FourColor/     the base port: corun1024/4ct, on Lean and Mathlib v4.34.1
  FourCT/        Rosetta Stone: one module per reformulation + Transfer tactic
  Statements/    short human-readable statement files, one per reformulation
checks/          our own re-implementations of the near-linear proof checks
data/            configurations, rules, polynomials, foam ranks (Git LFS)
search/          unavoidable-set search, learned discharging, conjecture mining
  index/         queryable index of the 8,202 reducible configurations
notes/           per-workstream results log
third_party/     git submodules pinned to commits; read-only upstreams
```

## Working in this repository

- `main` is protected: every change arrives as a pull request, and
  `lean-build` and `checks` must pass before it can be merged — including
  for administrators. Only Gabriel merges. See
  [`.github/PROTECTION.md`](.github/PROTECTION.md) for exactly what is
  enforced, why no approving review is required while he is the only
  collaborator, and the fork-pull-request rules, which matter because the
  repository is public.
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

## Setting up

- [`.github/PROTECTION.md`](.github/PROTECTION.md) — what protects this
  repository, and the one open question about its visibility.
- [`.github/RUNNER.md`](.github/RUNNER.md) — registering the self-hosted
  runner that `lean-build` needs: Linux inside WSL2, on a 32 GB Windows
  host. Read its first two sections before registering — WSL2's default
  memory limit is too low for this build, and a self-hosted runner on a
  public repository needs care.
