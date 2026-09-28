# checks/

Two different things live here.

## 1. Repository guardrails — `repo_guardrails.py`

Runs as the `checks` status check on every pull request. It enforces the
mechanical parts of the plan of record:

- `lean/lean-toolchain` pins `leanprover/lean4:v4.34.1`, and `lean/lakefile.toml` pins
  Mathlib to the same tag. No release candidates.
- Every file under `data/` has a `MANIFEST.csv` row, and every digest matches.
- `.gitattributes` still routes `data/**` through Git LFS.
- `THIRD_PARTY_NOTICES.md` still names all four vendored upstreams.
- Submodules are pinned to commits and point at the expected upstreams.

Run it locally exactly as CI does:

```bash
python3 checks/repo_guardrails.py
```

It prints one line per check and exits non-zero on the first failure.

## 2. The upstream checks, reproduced — `f1/`

Task F1: every computer check of the near-linear proof, run with the upstream
MIT C++ code in one command, `checks/f1/reproduce.sh`, on the self-hosted
runner. The results, their comparison with the eleven published targets and
the run times are in `notes/F-ai-and-computation-engine.md`; how the run
works and where it departs from upstream's scripts is in `f1/README.md`.

## 3. Our own re-implementation of the near-linear proof checks — `f2/`

Task F2: an independent implementation, in Python, written from the paper's
pseudocode. It is a second implementation on purpose: every computation in
this program has two that agree, and F1 runs the MIT C++ code. It was written
without the C++ and without the unlicensed reimplementations; its
independence log is in `f2/README.md`. One command runs everything:
`python3 checks/f2/run.py all --jobs 17 --out DIR`, about an hour on the
self-hosted runner.

## 4. F1 against F2 — `f1_vs_f2/`

`f1_vs_f2/compare.py` compares the two implementations' outputs object by
object, up to isomorphism: the combined rules, the wheels and the bad
cartwheels. It is neither implementation. See `f1_vs_f2/README.md`.
