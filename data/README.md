# data/

Configurations, discharging rules, polynomials and foam ranks.

Everything here except `MANIFEST.csv`, this file and `.gitkeep` is stored in
**Git LFS** (see `/.gitattributes`). Install `git-lfs` before cloning.

## MANIFEST.csv

Every file under `data/` has exactly one row:

| column | meaning |
| --- | --- |
| `path` | repository-relative path, e.g. `data/configurations/0001.conf` |
| `source_url` | where the file came from; the upstream permalink, pinned to a commit |
| `license` | SPDX id, or the licence as the upstream states it |
| `sha256` | lowercase hex digest of the file's bytes |

The manifest is checked by `checks/repo_guardrails.py`, which runs as the
`checks` status check on every pull request. It fails if a file under `data/`
has no row, if a row points at a file that is not there, or if a digest does
not match.

Regenerate the digests for files you added with:

```bash
python3 checks/repo_guardrails.py --update-manifest
```

and review the diff before committing.

## What goes here

- The 8,202 reducible configurations (8,200 files plus the degree-3 and
  degree-4 cases) and the 84 discharging rules from the near-linear proof —
  task F3, which also adds a queryable index.
- Polynomials and foam ranks produced by workstreams C and D.

Derived files that a script can rebuild do not belong here; the script does.
