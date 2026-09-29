# lean/

The Lean package for the whole program. **This directory is the Lake package
root**: `lakefile.toml`, `lean-toolchain` and `lake-manifest.json` live here,
and every Lean command runs from here.

| Path | What | Built by |
| --- | --- | --- |
| `FourColor.lean`, `FourColor/` | **The base port** — corun1024/4ct, moved to Lean and Mathlib `v4.34.1` (task A2) | `./build.sh` only |
| `FourCT.lean`, `FourCT/` | The Rosetta Stone: one module per reformulation, and the Transfer tactic. `FourCT.Base` imports the base port | `./build.sh` |
| `Statements/` | One human-readable statement file per reformulation; each needs Gabriel's written sign-off | `./build.sh` |
| `scripts/`, `tools/`, `build.sh` | corun's build and verification tooling; `scripts/build_pool.py` is modified (see below), the rest unmodified | — |
| `UPSTREAM-README.md`, `formalization.yaml` | corun's own description of the development, unmodified | — |
| `LICENSES/corun1024-4ct.txt` | corun's MIT licence **and CeCILL-B credit**, which must travel with this code | — |

## Building

```bash
cd lean
JOBS=4 MEMORY=20 ./build.sh     # everything: ~2 h cold, seconds when nothing changed
lake env lean ../checks/lean/fourct_axioms.lean   # the axioms FourCT's theorems use
```

`build.sh` fetches Mathlib from the cache, regenerates the reducibility
certificates if they are absent (about a core-hour; needs `gcc` and
`python3-numpy`), builds the 821 FourColor modules and the program's own
FourCT and Statements modules, and runs
`scripts/check.sh`. That last step fails unless it can print

```
THEOREM PROVED: FourColor.fourColorTheorem : FourColor.FourColorTheorem depends only on [propext, Classical.choice, Quot.sound]
```

having also found no `sorry`, no `native_decide` or other trusted-base escape
hatch in any of 115,342 declarations, and having passed the anti-vacuity
negative controls in `scripts/Audit.lean`.

`MEMORY` is in **gigabytes**. One module peaks at 20.3 GB; do not raise it
above 20 on the 26 GB WSL2 runner.

## Never `lake build`

Everything here is built by `scripts/build_pool.py`: the base port, FourColor,
and since task A3 the program's own FourCT and Statements. It runs the same
`lean` invocations Lake would, but never more than `JOBS` at a time and never
admitting a module whose predicted peak would break the `MEMORY` budget. It
writes **no Lake trace files**, so Lake does not recognise its output. Asking
Lake to build FourColor, directly or by building anything that imports it
(and `FourCT.Base` does), rebuilds all 821 modules with one job per hardware
thread and no memory budget. With modules that peak at 20 GB, that is how the
machine runs out of memory.

`build_pool.py` rebuilds a module only when its input changed. Its
fingerprint of a module covers the module's source, every module it imports,
transitively, the build options, `lean-toolchain`, `lakefile.toml` and
`lake-manifest.json`. That is what makes it safe to verify with.

**Checking one file at the keyboard:** after `./build.sh`, run
`lake env lean FourCT/Foo.lean`. It compiles that one file against the
existing build in seconds, without involving Lake's build logic. Rerun
`./build.sh` afterwards: it is incremental, rebuilds exactly what depends
on your change, and is what CI verifies with.

**Not `lake build --old`.** It would accept this build if `build_pool.py`
also wrote each module's C file, where Lake looks for it. But emitting C made
the bulk certificate modules (`FourColor.Bulk.Cfg.Grp*`) 23× slower, about 7
extra hours per cold build, so `build_pool.py` does not. `--old` would not be
verification anyway: it ignores changes in a module's imports. The
measurements are on issue #4.

**An editor may try the full rebuild.** Opening a module that imports
FourColor in an editor runs Lake's `setup-file`, and so will most likely try
to rebuild the port. This has not been tested.

These guard against a `lake build` reaching the port:

- `defaultTargets` in `lakefile.toml` is `FourCT`; a bare `lake build` would
  still reach FourColor through `FourCT.Base`, so do not run one;
- `checks/repo_guardrails.py` fails if `defaultTargets` includes FourColor,
  if `build_pool.py` stops building FourCT or Statements, if `lean-build`
  runs `lake build`, or if any workflow uses `--old`.

Also: `scripts/check.sh` calls `build_pool.py` without passing `JOBS` or
`MEMORY`, so it falls back to machine-derived defaults — 18 jobs and an 18 GB
budget on the runner. That is harmless after a complete `build.sh`, when there
is nothing left to build. Do not run `check.sh` on its own against a
half-built tree.

## Editing `lakefile.toml` rebuilds everything

`build_pool.py` fingerprints every FourColor module against the **whole** of
`lakefile.toml`, `lean-toolchain` and `lake-manifest.json`. Any edit to any of
them — even a comment — invalidates all 821 oleans: a full two-hour rebuild on
the next CI run. The `Statements` library was declared before it had any files
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

Every FourCT and Statements file opens with this header, then its imports,
then its `/-! ... -/` module doc-string:

```
/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
```

Mathlib's header linter, which corun's `weak.linter.mathlibStandardSet`
option switches on for the whole package, checks this only under
`lake build`. `build_pool.py` compiles with plain `lean`, under which it does
not run. So `checks/repo_guardrails.py` checks the header instead, textually,
and fails the `checks` status check on a file without it. Copy the block
above.
