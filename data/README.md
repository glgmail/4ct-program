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

## What is here

| Path | What | Upstream, pinned |
| --- | --- | --- |
| `near-linear-4ct/reducible-configurations/` | `D/D0000.conf` … `D/D8199.conf`: 8,200 of the 8,202 reducible configurations in the paper's set D, plus upstream's `README.md` and `LICENSE` | [near-linear-4ct/reducible-configurations](https://github.com/near-linear-4ct/reducible-configurations) @ `c2ce7a96e35256201526e2abb51a39d04a588b53` |
| `near-linear-4ct/discharging-rules/` | `R/`: the 84 discharging rules, plus upstream's `README.md` and `LICENSE` | [near-linear-4ct/discharging-rules](https://github.com/near-linear-4ct/discharging-rules) @ `d85bfe09e9584d675fdf33a1da61067575ec4883` |

Both are MIT; the upstream `LICENSE` files are kept beside the data, and the
notice is also in `/THIRD_PARTY_NOTICES.md`. Imported in task F3, byte for byte
and unchanged. Each file's git blob matches upstream's at the pinned commit,
and each manifest row links the upstream file at that commit.

The other two configurations of D consist of a single vertex of degree 3 or 4.
They are not files upstream, so they are not files here. They appear as the
rows `deg3` and `deg4` of the configuration index, `search/index/`. The count
is reconciled in `notes/F-ai-and-computation-engine.md`.

The 84 rules are 43 rules and their mirror images. Two of the 43, `rule001` and
`rule040`, are symmetric, so they have one file each; the other 41 have
`_1` and `_2` files. That makes 41 × 2 + 2 = 84, the paper's count (section 4).

To re-import, fetch the pinned commit and write each blob out with
`git cat-file blob`. Do not use `git archive` or a checkout: on Windows,
`core.autocrlf` can rewrite line endings on the way out. Then compare
`git hash-object --no-filters` of every file with upstream's `git ls-tree`.

## What goes here later

- Polynomials and foam ranks produced by workstreams C and D.

Derived files that a script can rebuild do not belong here; the script does.
The configuration index is one: it lives in `search/index/` with its build
script.
