# checks/f1/

Task F1: every computer check of the near-linear proof, run with the upstream
MIT C++ code, [near-linear-4ct/computer-checks](https://github.com/near-linear-4ct/computer-checks)
at the commit the submodule `third_party/near-linear-4ct/computer-checks`
pins. This is the first of the two implementations the program requires;
the second is F2, written from the paper's pseudocode.

## One command

On the self-hosted runner (Linux inside WSL2), from a clean clone with the
LFS data pulled:

```bash
checks/f1/reproduce.sh            # everything: about 70 minutes on 20 threads
checks/f1/reproduce.sh --smoke    # build, A.1, A.2, degree-7 wheels: about a minute
```

It writes `results.txt`, `env.txt`, `timings.tsv` and `compile-flags.txt` to
`$WORK/results/` (default `WORK=$HOME/f1-work`). `results/` in this directory
holds the files from the run reported in `notes/F-ai-and-computation-engine.md`.

A rerun has reproduced it when its `results.txt` is byte-identical to
`checks/f1/results/results.txt`:

```bash
cmp "$HOME/f1-work/results/results.txt" checks/f1/results/results.txt
```

`env.txt` (host, kernel, compiler, start and finish times) and `timings.tsv`
are expected to differ between runs and are never compared.

Dependencies: `cmake`, `g++`, `make`, `python3`, and the Boost
`program_options` and `thread`, spdlog and fmt development packages; see
`.github/RUNNER.md`, section 3. The configure step downloads googletest from
GitHub, as upstream's CMakeLists does.

## What it runs

The upstream README's command lines, unchanged, against a pristine copy of
the pinned upstream tree (`git archive` of the submodule). The data is this
repository's `data/near-linear-4ct/`, which is byte-identical to the
upstream data repositories at the commits `data/MANIFEST.csv` links;
`reproduce.sh` runs the guardrails, which check every digest, before it
starts.

| Step | Upstream command | Lemma |
| --- | --- | --- |
| build | `cmake -S . -B build`, `cmake --build build` | |
| unit tests | `ctest --test-dir build/test` | |
| A1_combine_rules | `main --combine_rules -R discharging-rules/R -C empty -o combined_rules/all` | A.1 |
| A2_combine_rules | `main --combine_rules -R discharging-rules/R -C reducible-configurations/D -o combined_rules/non_blocked` | A.2 |
| A3_enum_wheels_dD | `main --enum_wheels -d D ...`, D = 7..11, concurrently | A.3 |
| A3_enum_cartwheels_dD | `main --enum_cartwheels -w wheels/dD/dD_i.cartwheel ...`, one job per wheel | A.3 |
| A4_check_deg8 | `main --check_deg8 -W wheels/zero -C reducible-configurations/D` | A.4 |
| A5_check_7triangle | `main --check_7triangle ...` | A.5 |
| A6_check_deg7 | `main --check_deg7 ...` | A.6 |

## Where it differs from upstream, and why

Only in orchestration; no command line and no source file is changed.

- **Every exit status is kept.** Upstream's `enum_possible_bad_wheels.sh`
  backgrounds its five jobs and exits without waiting for them, and
  `enum_all_bad_cartwheels.sh` ends in a bare `wait`. Neither can report a
  failed job. That matters because **Lemmas A.4-A.6, and the cartwheel
  enumeration, fail only by `assert()` aborting the process.** So
  `reproduce.sh` runs the same command lines itself and records every
  status, 16,148 cartwheel jobs included.
- **The build must not define `NDEBUG`.** With `NDEBUG` those assertions
  compile away and A.4-A.6 pass whatever the data. Upstream sets no build
  type, so none is defined. `reproduce.sh` refuses to continue if the flags
  say otherwise, and records them in `compile-flags.txt`.
- **Anti-vacuity controls.** A.4-A.6 are run a second time with no reducible
  configurations. They must abort with a failed assertion, and they do (exit
  134). This shows the passing runs are not passing vacuously.
- **The number of cartwheel jobs per degree is counted, not hard-coded.**
  Upstream's README passes the published wheel counts (5439, 6790, ...) to
  `enum_all_bad_cartwheels.sh`. Here the count is the number of wheel files
  this run produced, so a wrong count cannot be masked by a correct constant.
- **`ctest --test-dir build/test`.** Upstream calls `enable_testing()` in
  `test/CMakeLists.txt`, so at `build/` ctest finds no tests and still exits
  0. `summarize.py` treats zero tests as a failure.
- **Parallelism.** `JOBS` cartwheel jobs at once, default `nproc`, as
  upstream's `MAX_JOBS`. Each job peaks under 50 MB.

## Targets

The eleven expected values are those published in
`near-linear-4ct/instructions-for-checking-reproducibility`. That repository
has no licence: it was read and followed, and nothing was copied from it.
The values are facts about the paper and are stated in `summarize.py` with
their source. A.4-A.6 have no numeric target; each passes when the check
exits 0 and logs that it finished.

## Resuming

`RESUME=1 checks/f1/reproduce.sh` keeps `$WORK` and skips every step, and
every cartwheel job, that already exited 0. Use it after an interruption.
A run reported as a result should be a single uninterrupted run.
