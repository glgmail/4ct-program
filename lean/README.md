# lean/

The Lean package for the whole program. **This directory is the Lake package
root**: `lakefile.toml`, `lean-toolchain` and `lake-manifest.json` live here,
and every Lean command runs from here.

| Path | What | Built by |
| --- | --- | --- |
| `FourColor.lean`, `FourColor/` | **The base port** — corun1024/4ct, moved to Lean and Mathlib `v4.34.1` (task A2) | `./build.sh` only |
| `FourCT.lean`, `FourCT/` | The Rosetta Stone: one module per reformulation, and the Transfer tactic | `lake build FourCT` |
| `Statements/` | One human-readable statement file per reformulation; each needs Gabriel's written sign-off | `lake build Statements` |
| `scripts/`, `tools/`, `build.sh` | corun's build and verification tooling, unmodified | — |
| `UPSTREAM-README.md`, `formalization.yaml` | corun's own description of the development, unmodified | — |
| `LICENSES/corun1024-4ct.txt` | corun's MIT licence **and CeCILL-B credit**, which must travel with this code | — |

## Building

```bash
cd lean
JOBS=4 MEMORY=20 ./build.sh     # the base port: ~2 h cold, seconds when nothing changed
lake build FourCT               # our own library
```

`build.sh` fetches Mathlib from the cache, regenerates the reducibility
certificates if they are absent (about a core-hour; needs `gcc` and
`python3-numpy`), builds the 821 FourColor modules, and runs
`scripts/check.sh`. That last step fails unless it can print

```
THEOREM PROVED: FourColor.fourColorTheorem : FourColor.FourColorTheorem depends only on [propext, Classical.choice, Quot.sound]
```

having also found no `sorry`, no `native_decide` or other trusted-base escape
hatch in any of 115,342 declarations, and having passed the anti-vacuity
negative controls in `scripts/Audit.lean`.

`MEMORY` is in **gigabytes**. One module peaks at 20.3 GB; do not raise it
above 20 on the 26 GB WSL2 runner.

## Never `lake build FourColor`

The base port is built by `scripts/build_pool.py`, which runs the same `lean`
invocations Lake would, but never more than `JOBS` at a time and never
admitting a module whose predicted peak would break the `MEMORY` budget. It
writes **no Lake trace files**, so Lake does not recognise its output. Asking
Lake to build FourColor — directly, or by building anything that imports it —
rebuilds all 821 modules with one job per hardware thread and no memory
budget. With modules that peak at 20 GB, that is how the machine runs out of
memory.

Three things guard against it:

- `defaultTargets` in `lakefile.toml` is `FourCT`, so a bare `lake build`
  cannot reach the port;
- `checks/repo_guardrails.py` fails if `defaultTargets` ever includes
  FourColor;
- the same script fails if any `FourCT` or `Statements` module imports
  `FourColor`. **Task A3 will be the first to need that import**, and will
  have to extend the build (most likely by teaching `build_pool.py` to
  schedule FourCT modules too) before it can add it.

Also: `scripts/check.sh` calls `build_pool.py` without passing `JOBS` or
`MEMORY`, so it falls back to machine-derived defaults — 18 jobs and an 18 GB
budget on the runner. That is harmless after a complete `build.sh`, when there
is nothing left to build. Do not run `check.sh` on its own against a
half-built tree.

## Editing `lakefile.toml` rebuilds everything

`build_pool.py` fingerprints every FourColor module against the **whole** of
`lakefile.toml`, `lean-toolchain` and `lake-manifest.json`. Any edit to any of
them — even a comment — invalidates all 821 oleans: a full two-hour rebuild on
the next CI run. The `Statements` library is declared before it has any files
for exactly this reason. Batch lakefile changes, and expect the cost.

Adding or editing FourCT or Statements modules does not touch this.

## Relationship to upstream

The FourColor tree is **corun1024/4ct at commit `3db71e0`**, with exactly
these changes, all confined to build configuration:

| File | Change |
| --- | --- |
| `lean-toolchain` | `v4.34.0-rc2` → `v4.34.1` |
| `lakefile.toml` | Mathlib pinned to `rev = "v4.34.1"` (was unpinned, resolving to a `master` commit); merged with this program's package definition — see the comments in the file |
| `lake-manifest.json` | re-resolved against Mathlib `v4.34.1`; root package renamed to `FourCT` |
| `README.md`, `LICENSE` | moved to `UPSTREAM-README.md` and `LICENSES/corun1024-4ct.txt`, so neither is read as describing or licensing this program's own code |

**No Lean source was changed.** Every one of the 498 upstream `.lean` files is
byte-identical to upstream, verified by git blob hash when vendored. The
upstream repository stays pinned as a submodule in
`third_party/corun1024/4ct` as the reference to diff against.

## Licensing

The FourColor tree is MIT-licensed by Chris Emery, and contains data
translated mechanically from Gonthier and Werner's Coq proof, which is under
CeCILL-B. The CeCILL-B credit in `LICENSES/corun1024-4ct.txt` **must be
preserved** in any redistribution, modified or not.

This program's own code (FourCT, Statements) is licensed under **Apache
2.0**; see `LICENSE` at the repository root, whose README says precisely
what that covers. The corun tree is not relicensed by it: MIT and the
CeCILL-B credit still apply to everything that came from corun1024.

Mathlib's header linter, which corun's `weak.linter.mathlibStandardSet`
option switches on for the whole package, expects every FourCT and
Statements file to open with a Mathlib-style header:

```
/-
Copyright (c) 2026 <copyright holder>. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: <authors>
-/
```

Until those headers are added it warns on each such file. It is a warning,
not an error, and does not fail the build.
