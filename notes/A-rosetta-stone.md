# Workstream A — The Rosetta Stone

Results log. Newest first. One row per result, added in the pull request that
produced it.

A row belongs here only if it meets the trust rule: a Lean theorem that builds
on the pinned toolchain, or a script whose output reruns identically from a
clean checkout. Leads, partial arguments and AI-written summaries go under
"Open leads" instead, and are not results.

| Date | Result | Evidence | Tier | PR |
| --- | --- | --- | --- | --- |
| 2026-09-27 | `corun1024/4ct` builds clean on its own pinned toolchain, and `FourColor.fourColorTheorem` depends on no axioms beyond `propext`, `Classical.choice`, `Quot.sound`. 115,342 declarations, no sorries. | port-build run [36336993686](https://github.com/glgmail/4ct-program/actions/runs/36336993686), artifact `port-build-corun1024` | evidence for A1 | #20 |

## Open leads

- _(none yet)_

---

# A1 — statement review of the two Lean ports

**Status: statement comparison complete; build evidence outstanding.**

Nothing below is a result under the trust rule. It is a reading of source
text, not a theorem that built. The build half of A1 — times, peak memory,
clean build, `#print axioms` — needs the 32 GB runner and is gathered by
`.github/workflows/port-build.yml`, which nobody has run yet. Treat the
recommendation as provisional until it has.

Sources read, all pinned:

| What | Commit |
| --- | --- |
| `corun1024/4ct` | `3db71e0a786a1f19be04c5266fe3d06fed216885` |
| `RBarish-UTokyo/FourColorTheorem-Lean4` | `20fa34599f5189dd569d96dd22f306c94ab1c446` |
| `rocq-community/fourcolor` (Gonthier, formerly `math-comp/fourcolor`) | `c1d6b1cd5288bea4b067aac13cdde3c18dffe018` |

## The three final statements

Gonthier, `theories/proof/fourcolor.v`, inside
`Section FourColorTheorem` with `Variable Rmodel : Real.model`:

```coq
Theorem four_color m : simple_map m -> colorable_with 4 m.
```

RBarish, `Solution.lean`:

```lean
theorem four_color (m : Map) (h : SimpleMap m) : ColorableWith 4 m :=
  compactness_extension four_color_finite m h
```

corun1024, `FourColor/RealPlane.lean` and `FourColor/Complete.lean`:

```lean
def FourColorTheorem : Prop := ∀ m : PlaneMap, SimpleMap m → ColorableWith 4 m

theorem fourColorTheorem : FourColorTheorem :=
  fourColorTheorem_of_checks reducibility
    exclude5 exclude6 exclude7 exclude8 exclude9 exclude10 exclude11
```

All three say the same thing, and both ports follow Gonthier's proof
architecture as well as his statement: the general case comes from the finite
case by compactness (`compactness_extension` / `finitize`), the finite case
from discretisation to a hypermap plus the combinatorial 4CT.

## Definitions, against Gonthier's `realplane.v`

Both ports transcribe the same chain of definitions in the same order. The
statement's meaning rests entirely on these, so they are what matters.

| Gonthier (`realplane.v`) | RBarish | corun1024 |
| --- | --- | --- |
| `point := Point (x y : Real.val R)` | `structure Point where x y : ℝ` | `abbrev Point := ℝ × ℝ` |
| `region := point -> Prop` | `abbrev Region := Point → Prop` | `abbrev Region := Set Point` |
| `map := point -> region` | `abbrev Map := Point → Region` | `abbrev PlaneMap := Point → Region` |
| `union`, `intersect`, `subregion`, `meet`, `nonempty` | each defined explicitly | Mathlib's `∪`, `∩`, `⊆`, `.Nonempty` |
| `plain_map` (`map_sym`, `map_trans`) | `PlainMap`, same two fields | `PlainMap`, same two fields |
| `cover m := fun z => m z z` | same | `{z \| z ∈ m z}` |
| `at_most_regions n m` | same | same |
| `open` (via open rectangles) | `Open` | `IsOpenRegion` |
| `closure` | `closure` | `regionClosure` |
| `connected` | `Connected` | `IsConnectedRegion` |
| `simple_map` | `SimpleMap` | `SimpleMap` |
| `border`, `corner_map`, `not_corner`, `adjacent` | same four | `border`, `cornerMap`, `notCorner`, `Adjacent` |
| `coloring` (4 fields) | `Coloring`, same 4 | `Coloring`, same 4 |
| `colorable_with n m` | `ColorableWith` | `ColorableWith` |

I read each definition against its Coq original. **No definition in either
port changes the meaning of the statement.** The traps worth checking
explicitly, and how each port handles them:

- **Adjacency excludes corners.** Both define `adjacent` as "different
  regions, and their common border contains a point lying in the closure of
  at most two regions". Without the corner exclusion the theorem is false —
  diagonally opposite squares of a checkerboard would count as adjacent. Both
  get this right.
- **Maps are partial equivalence relations, not total ones.** Points on
  borders belong to no region. Both keep `plain_map` as symmetry plus
  transitivity, with no reflexivity.
- **`coloring` requires all four conditions.** Dropping
  `coloring_consistent` would let each point take its own colour. Both carry
  all four fields.
- **Finiteness is not assumed.** The theorem is for all simple maps,
  including infinitely many regions. Both state the unrestricted version and
  derive it by compactness, as Gonthier does.

## Where both ports differ from Gonthier

One difference, shared by both, and it is the only substantive one:

**Gonthier quantifies over an arbitrary model of the reals.** `fourcolor.v`
takes `Variable Rmodel : Real.model`; the theorem holds for any such model.
Both Lean ports instead fix Mathlib's `ℝ`.

This is a genuine narrowing of the statement as written, though not a
mathematically serious one: Gonthier's `realcategorical.v` proves all models
of the reals isomorphic, and these definitions use only the order on `ℝ`.
RBarish states the specialisation explicitly in `Challenge.lean`'s docstring.
It should be recorded in `lean/Statements/` whichever port we take, so that a
later reader does not believe we have the more general theorem.

## Where the two ports differ from each other

### 1. Whether the statement mentions Mathlib

RBarish's statement is deliberately Mathlib-free: `Region` is `Point → Prop`,
and union, intersection, openness, closure and connectedness are all defined
from open rectangles. `Challenge.lean` says so, and imports only
`Mathlib.Basic.Real.Basic`. **No Mathlib topology anywhere in that repository**
(searched: no `IsPreconnected`, no `Mathlib.Topology`).

corun1024 uses `Set Point` and Mathlib's set operations, *and* ships
`FourColor/RealPlaneMathlib.lean`, which proves the elementary notions are
Mathlib's:

```lean
theorem isOpenRegion_iff (r : Region) : IsOpenRegion r ↔ IsOpen r
theorem regionClosure_eq (r : Region) : regionClosure r = closure r
theorem isConnectedRegion_iff_isPreconnected {r : Region} (hr : IsOpenRegion r) :
    IsConnectedRegion r ↔ IsPreconnected r
theorem simpleMap_iff (m : PlaneMap) :
    SimpleMap m ↔ PlainMap m ∧ (∀ z, IsOpen (m z)) ∧ ∀ z, IsPreconnected (m z)
```

For a statement meant to be read and disbelieved, RBarish's independence is
the better property. **For this program it is the wrong way round.** A3 and A4
need planar embedding, duality and flows stated against Mathlib, and the
Rosetta Stone's whole purpose is transfer between formulations. corun1024
already has the bridge; with RBarish we would have to build it, and building
it is exactly the kind of definitional work where a mistake is invisible to
the kernel.

### 2. Guards against a vacuous statement

corun1024 ships two things beyond the proof:

- `scripts/Audit.lean` — kernel-checked **negative controls**. Its own words:
  a proof "can be perfectly sound and still worthless if the *checkers* it
  relies on accept everything". It proves `theRedpart (Part.free 5) = false`
  and similar, so the reducibility oracle is not constantly `true`, and
  `QuizTree.size theQuizTree = 3361`, so the quiz data is the real data and
  not an empty tree that answers every query.
- `FourColor/Nonvacuity.lean` — builds an explicit four-region configuration
  in the plane with Mathlib closures computed, plus a pigeonhole lemma
  `not_colorable`: `n+1` pairwise adjacent regions cannot be `n`-coloured. So
  the four in "four colours" is not slack.

`build.sh` runs these as part of the standard build, alongside checks for no
`sorry`, no `native_decide`, and the axioms of `fourColorTheorem`.

RBarish has `scripts/check_challenge_sync.py`, which verifies that the
definitions in `Challenge.lean` are identical to those the proof uses — a
different and also valuable guard, against the statement drifting from the
proof. It also has `FourColor/Examples.lean`, unexamined so far; the build
task should look at whether it plays the non-vacuity role.

This program's trust rule says a statement that builds is not yet a result.
corun1024's audit is the closest thing either port has to mechanising that
rule.

### 3. `sorry`, `native_decide`, axioms

Neither port has a `sorry` in its proof.

Two things that look alarming and are not, recorded so nobody re-raises them:

- GitHub code search reports `sorry` in eight corun1024 files. Seven are
  tooling and documentation that *check for* `sorry`; the eighth,
  `FourColor/Embed.lean`, is a docstring reading "Every declaration below is
  fully proved, with no `sorry` and no new axioms". There is no `sorry` in
  corun1024's Lean proof.
- RBarish's `Challenge.lean` ends `theorem four_color ... := sorry`. That file
  is the statement-only specification, deliberately unproved; `Solution.lean`
  carries the real proof, and `check_challenge_sync.py` keeps the two in step.

`native_decide` appears in corun1024 only in tooling that forbids it. Both
ports appear to rely on kernel `decide` rather than compiled evaluation,
which matters: `native_decide` would put the Lean compiler in the trusted
base.

**None of this substitutes for `#print axioms` on a real build.** Source
reading cannot see what the elaborator actually admitted.

### 4. Distance from our pinned toolchain

| | Upstream toolchain | Distance to `v4.34.1` |
| --- | --- | --- |
| corun1024 | `leanprover/lean4:v4.34.0-rc2` | forward one patch, off the rc |
| RBarish | `leanprover/lean4:v4.35.0-rc2` | backward one minor, off the rc |

Both are on release candidates, which our pin forbids. corun1024 is the
smaller move, and forward rather than backward. Moving RBarish means
un-adopting whatever arrived in v4.35, which is the harder direction because
the compiler will not tell you what a lemma used to be called.

Both `Mathlib/Basic/Real/Basic.lean` and `Mathlib/Data/Real/Basic.lean` exist
at Mathlib `v4.34.1`, so RBarish's statement import is not itself a problem.

### 5. Build cost and how the build is driven

corun1024 has `scripts/build_pool.py`, which schedules modules against a
**cost table of per-module wall time and peak memory**
(`scripts/module_cost.tsv`, 27 KB) and admits a module only if its predicted
peak fits a budget. It takes `JOBS` and `--memory` **in GB**:
`JOBS=8 MEMORY=40 ./build.sh`.

That is directly useful to us, because the self-hosted runner is WSL2 with a
~26 GB share, and corun's own documentation says single modules peak near
20 GB.

RBarish has `scripts/engine_memtime.py`, `final_run.sh` and
`palomar_check.sh`; the plan of record records it as needing about 16 GB and
25 GB of disk, 2.4–3.3 hours on 16 cores.

## Recommendation: corun1024/4ct — now with build evidence

On the statement itself there is nothing to choose between them. Both are
faithful transcriptions of Gonthier, and both narrow the reals in the same
defensible way. The recommendation turns entirely on what the port is *for*
in this program.

1. **The Mathlib bridge already exists.** A3 and A4 need planar embedding,
   duality, Tait and flows stated against Mathlib. `RealPlaneMathlib.lean`
   connects the statement's elementary topology to `IsOpen`, `closure` and
   `IsPreconnected` today. With RBarish we would write that ourselves, in the
   one area where an error is invisible to the kernel.
2. **It mechanises our trust rule.** The anti-vacuity audit and the
   non-vacuity construction are precisely the "a statement that builds is not
   yet a result" discipline, already in Lean and already kernel-checked.
3. **It is closer to the pin**, and moving forward off an rc is easier than
   moving back a minor version.
4. **Its build is memory-aware**, which matters on a 26 GB WSL2 share.

Two of the four things that could have overturned this are now settled, in
corun1024's favour:

- **`#print axioms` is clean** — `[propext, Classical.choice, Quot.sound]`
  and nothing more, across 115,342 declarations. Had anything else appeared
  it would have been decisive against the port regardless of its other
  merits.
- **Peak memory fits**, though not comfortably: 20.2 GB in a 25 GB share.

What could still change it:

- **RBarish builds clean on `v4.34.1` and corun1024 does not**, or corun
  needs changes touching statements rather than proofs when moved. That is
  A2's question, and portability beats convenience.
- **RBarish's `#print axioms` is equally clean and its `Examples.lean` gives
  comparable non-vacuity coverage**, which would neutralise the audit
  advantage and leave the Mathlib bridge as the only differentiator.

Neither is known yet: **RBarish has not been built.** The comparison is
still one-sided, and a recommendation resting on one measured port and one
unmeasured one should be read accordingly.

Gabriel decides. This is a recommendation with its reasons, not a choice.

## Build attempt 1 — corun1024, 2026-09-27 (failed: environment)

Run [36305441480], `JOBS=1`, `memory_gb=20`, self-hosted runner. **Failed
after 5 min 13 s of `build.sh`, on a missing Python package** — not on
anything about the port.

```
File ".../port/scripts/bulkspace.py", line 17, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
```

corun's `scripts/bulkspace.py` imports numpy; the runner had no numpy. Fixed
by adding `python3-numpy` to the runner dependencies, and `port-build.yml`
now checks for it before starting rather than five minutes in.

Not a measurement of the port. But three things did come out of it:

- **The toolchain coexists.** `elan` installed the port's `v4.34.0-rc2`
  alongside our `v4.34.1` with no conflict, and `lake exe cache get` restored
  Mathlib from cache (8,905 files decompressed, nothing downloaded). The
  build reached corun's own code.
- **`JOBS=1` is not honoured by every phase.** `/usr/bin/time` reported
  **1101 % CPU** over the 5 min 13 s — roughly eleven cores — during the
  reducibility-certificate generation, which corun's own output describes as
  "about one core-hour". That phase parallelises independently of `JOBS`.
  Peak memory was only 2.3 GB, so it did no harm here, but it means the
  memory ceiling during certificate generation is not something `JOBS`
  controls. Watch it on the next run.
- **Peak memory sampling works.** 2.3 GB observed from `/proc/meminfo`,
  against a `Maximum resident set size` of 0.8 GB from `/usr/bin/time` —
  which is the single largest process and, as expected, understates a
  parallel pool.

Wall-clock for the whole run was 57 minutes, most of it Mathlib cache
decompression and toolchain install rather than the 5 minutes of `build.sh`.
Budget for that on a first run of the other port too.

## Build attempt 2 — corun1024, 2026-09-27: **clean**

Run [36336993686], `JOBS=4`, `memory_gb=20`, self-hosted runner (WSL2, 25 GB
share). **821/821 modules, exit 0, 2 h 00 m 12 s.** Zero module failures.

### Axioms — the question that could have sunk the recommendation

```
'FourColor.fourColorTheorem' depends on axioms: [propext, Classical.choice, Quot.sound]
```

and from corun's own `scripts/check.sh`:

```
THEOREM PROVED: FourColor.fourColorTheorem : FourColor.FourColorTheorem
  depends only on [propext, Classical.choice, Quot.sound]
checked 115342 FourColor declarations: no sorries, no extra axioms
anti-vacuity audit: negative controls pass
```

Exactly the three standard axioms of classical Lean, and nothing else. No
`sorryAx`, no `Lean.ofReduceBool` (which is what `native_decide` would have
introduced, putting the compiler in the trusted base). The source reading in
the statement review said there was no `sorry` and no compiled evaluation;
the kernel now agrees, across all 115,342 declarations rather than the
handful a human can read.

The anti-vacuity audit passing is the part worth dwelling on: it is a
kernel-checked statement that corun's *checkers* are not degenerate — that
`theRedpart` is not constantly `true` and the quiz tree is the real data.
Sound and vacuous is the failure mode this program's trust rule exists to
catch, and corun catches it mechanically.

### Cost

| | |
| --- | --- |
| Wall clock | 2 h 00 m 12 s at `JOBS=4` |
| Total work | 7.9 core-hours (corun's own estimate, borne out) |
| `build_pool.py` prediction | 135 min at 4 jobs — it was accurate |
| Peak single process | **20.2 GB** (`/usr/bin/time` max RSS) |
| Peak system-wide | 18.9 GB (sampled every 5 s from `/proc/meminfo`) |
| Modules | 821, none failed |

**The 20 GB module is real.** corun's warning was not conservative: one
process reached 20.2 GB, in a 25 GB WSL2 share. That leaves under 5 GB of
headroom, so the `memory_gb=20` budget should not be raised, and `JOBS` above
4 is not obviously safe — the risk is not the average module but that one.

Note the sampler *understated* the peak (18.9 vs 20.2 GB): a 5-second
interval can miss a spike. For a hard ceiling, trust `/usr/bin/time`'s max
RSS; the sampler is for the shape of the run, not its worst moment.

### Two bugs in my own harness, both now fixed

- **The run is marked `failure` despite the build succeeding.** The
  orphan-sweep step I added runs under `bash -e` with `pipefail`, and its
  first pipeline greps for orphaned processes — which, on a clean run, match
  nothing, so `grep` exits 1 and kills the step. A cleanup step invented to
  handle a failure mode manufactured a false one.
- **The resume never worked.** `actions/checkout` cleans the workspace at
  the start of every job, so the `port/` directory from the previous run was
  deleted before the resume check could see it. That is why the reducibility
  certificates were regenerated despite `fresh` being off. The port checkout
  now lives in `$HOME/4ct-port-cache/<port>`, outside the workspace.

Neither affects the result above: the build, the axioms and the audit all
ran before the sweep, and a full rebuild is if anything the stronger
evidence.

## What the build must still produce

`.github/workflows/port-build.yml`, run once per port, on the self-hosted
runner. For each:

- wall-clock time and peak RSS, at the `JOBS` and memory budget used;
- whether it builds clean on its **own** pinned toolchain (not ours — moving
  it is A2);
- `#print axioms` on the final theorem, pasted verbatim;
- whether the upstream's own checks pass (corun's `scripts/check.sh` and
  `Audit.lean`; RBarish's `check_challenge_sync.py` and `palomar_check.sh`);
- for RBarish, what `FourColor/Examples.lean` actually establishes.

Until that exists, the four numbered claims above rest on reading source, and
point 3 and point 4 in particular are predictions rather than measurements.
