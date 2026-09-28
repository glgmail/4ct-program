# search/index/

A queryable index over the reducible configurations of the near-linear proof
(task F3), so that later tasks do not re-parse 8,200 files each time.

| File | What |
| --- | --- |
| `configurations.csv` | the index: one row per configuration of the set D, 8,202 rows |
| `build.py` | builds it from `data/near-linear-4ct/reducible-configurations/D/`; standard library only |
| `crosscheck.py` | checks it against an independent method (needs `networkx`) |

The index is a derived file. It is committed as plain CSV, not Git LFS, so a
change to it shows up in the pull request diff. It lives here rather than in
`data/` because `data/` holds only imported data. `build.py` regenerates it,
and `build.py --check` fails unless the committed copy is byte-identical to a
fresh build.

## Rows

8,200 rows come from the files `D0000` to `D8199`. The other two, `deg3` and
`deg4`, are the configurations consisting of a single vertex of degree 3 or 4.
The paper counts them in D (section 3), but upstream does not ship them as
files; here they have an empty `path`. See `notes/F-ai-and-computation-engine.md`
for how the 8,202 was reconciled.

## Columns

| Column | Meaning |
| --- | --- |
| `config` | `D0000` … `D8199`, or `deg3`, `deg4` |
| `path` | the data file, or empty for `deg3`, `deg4` |
| `ring_size` | R, the length of the ring |
| `vertices` | the configuration's own vertices (not counting the ring) |
| `edges` | edges between the configuration's own vertices |
| `degree_sequence` | their degrees in the triangulation, non-increasing, space-separated |
| `shape` | 16 hex digits; equal exactly when two configurations are isomorphic, mirror images included |
| `shape_oriented` | 16 hex digits; equal exactly when isomorphic by an orientation-preserving map |
| `chiral` | `1` if the configuration differs from its mirror image, else `0` |

How `shape` is computed is in the docstring of `build.py`.

## Query patterns

These are the patterns B1 (the strengthening-search harness) and F2 (the
independent checks) are expected to use:

- **By size**: filter on `ring_size`, `vertices` or `edges`. For example, every
  configuration with a ring of at most 12 is `ring_size <= 12`.
- **By degrees**: filter on `degree_sequence`. Each entry is a degree between 3
  and 12; `deg3` and `deg4` are the only configurations with a vertex of
  degree below 5.
- **Is this configuration in D?** Run
  `python3 search/index/build.py --lookup FILE` on a file in the same format.
  It prints the file's `shape` and any row that shares it, saying whether the
  row matches as drawn or as its mirror image. Vertex numbering does not
  matter.
- **Duplicates and mirror pairs**: group by `shape`. A group of two rows with
  different `shape_oriented` is a mirror pair.
- **Back to the data**: `path` is the file, and `data/MANIFEST.csv` gives its
  upstream permalink and sha256.

Any CSV reader works. With pandas: `pd.read_csv("search/index/configurations.csv", dtype=str)`,
then convert the numeric columns as needed. Read `shape` and `shape_oriented`
as strings: some start with digits.

## What the index says about D

- **No duplicates.** All 8,202 `shape`s are distinct, and so are all 8,202
  `shape_oriented`s. So no configuration appears twice, even allowing for
  reflection.
- **Mirror images are not listed separately.** 7,949 configurations are
  chiral and 253 are not. No chiral configuration's mirror image is in the
  set, so D lists each configuration once up to reflection. A consumer that
  needs both orientations must reflect each chiral configuration itself.
- **Ring sizes** run from 6 to 18 for the files: 12–16 account for 7,824 of
  them, and 14 is the most common, with 2,799. `deg3` and `deg4` have rings of
  3 and 4.

## Rebuilding and checking

```bash
python3 search/index/build.py             # rewrite configurations.csv
python3 search/index/build.py --check     # byte-identical, or exit 1
python3 search/index/crosscheck.py        # independent check; needs networkx
```

The data must be real files, not LFS pointers: install `git-lfs` and run
`git lfs pull` first. `build.py` stops with a message if it finds a pointer.

`build.py` refuses any file that breaks the format conventions it relies on,
and says which one. Every file at the pinned upstream commit satisfies all of
them; its docstring lists them.

`crosscheck.py` recomputes the plain columns with its own parser. It tests
`shape` by graph isomorphism of the free completions, which is equivalent by
Whitney's theorem, over every pair networkx cannot tell apart by hashing. It
recomputes `chiral` by an oriented isomorphism test against the mirror image,
and tests that `build.py`'s shapes survive relabelling and reflection. Its
docstring says why this is enough and what it does not cover.

Neither script runs in CI, which does not pull LFS objects.
`checks/repo_guardrails.py` does check, without the data, that the index has
exactly one row per configuration file in the manifest, plus `deg3` and `deg4`.
