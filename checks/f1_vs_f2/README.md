# checks/f1_vs_f2/

F1 (the upstream C++, `checks/f1/`) and F2 (our independent Python,
`checks/f2/`) compared **object by object**, not just by count.

```bash
python3 checks/f1_vs_f2/compare.py F1_WORK F2_OUT F2_REPO data/near-linear-4ct/discharging-rules/R
```

- `F1_WORK` is the `WORK` directory of a `checks/f1/reproduce.sh` run.
- `F2_OUT` is the `--out` directory of `checks/f2/run.py all`.
- `F2_REPO` is a checkout of this repository, whose `checks/f2/nl4ct` rebuilds F2's cartwheels.

It takes about 15 seconds. `result.txt` holds the output of the comparison
reported in `notes/F-ai-and-computation-engine.md`.

## What is compared

| Objects | F1 files | F2 file |
| --- | --- | --- |
| R*, Lemma A.1 | `combined_rules/all/` | `a1-rstar.jsonl` |
| R*−D, Lemma A.2 | `combined_rules/non_blocked/` | `a2-rstar-d.jsonl` |
| surviving wheels C0, degrees 7–11 (A.3) | `wheels/d7/` … `wheels/d11/` | `wheels-<d>.txt`, lines marked `survives` |
| bad cartwheels C_all (A.3) | `wheels/zero/` | `call.jsonl` |

Both sides are reduced to one form: each vertex's degree range, and its
neighbours in clockwise order with the outer gap marked. Each object is
numbered breadth-first from a root:
- a combined rule from its dart s→t, carrying its charge and the set of
  original rules;
- a cartwheel from its centre, minimised over the darts into the centre.

Equal codes mean an orientation-preserving isomorphism that keeps the root,
the degree ranges, and for rules the charge and the rule set. Each object
set is compared as a multiset. When two sets differ, the script also reports
whether mirroring F2 would reconcile them, to tell a convention mismatch
from a real difference.

Lemmas A.4–A.6 are compared by verdict and by the size of the set each
check runs on. F1's checker does not record anything per case, so no finer
comparison is possible.

## Negative controls

A comparison that cannot fail proves nothing. Three changes were planted in
a copy of F2's output:
- one bad cartwheel's tail range narrowed from [5, 9] to [5, 8];
- one combined rule of R*−D with its charge raised by 1;
- one surviving degree-8 wheel replaced by its mirror image.

Each was reported as exactly one object only in F1 and one only in F2.
Mirroring F2 reconciled none of them. The controls were run by hand, and
their tampered copies were not kept.

## Independence

This script is neither implementation. It reads F1's intermediate files,
which are in the C++'s own formats (upstream `FORMAT.md`), and it rebuilds
F2's cartwheels with F2's own `generate_cartwheel`. It was written after F2
was finished, by the session that ran F1. F2's author never saw it.
