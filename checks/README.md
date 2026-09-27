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

## 2. Our own re-implementation of the near-linear proof checks

Task F2: an independent implementation written from the paper's pseudocode,
which must match the published target metrics. It must not be derived from the
unlicensed reimplementations, and it is a second implementation on purpose —
every computation in this program has two that agree (task F1 runs the MIT C++
code; this is the other one).

Nothing of it exists yet.
