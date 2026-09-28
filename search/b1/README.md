# search/b1/ — the strengthening-search harness

Task B1 (#9). Elegant colouring proofs often prove something **stronger**
than they need, so that the induction has more to hold on to; Thomassen's
proof that planar graphs are 5-choosable is the model. This harness exists
so that a candidate strengthening of the Four Colour Theorem can be killed
cheaply before anyone spends a month on it. It tests candidates against
every small triangulation and reports the smallest counterexample to each
one that fails. Which survivors could carry an induction is for people to
judge.

**A survivor has not been proved.** The harness reports it as "not killed
up to n vertices", never as true. FL1 below makes the point: it survives
every triangulation here, and it is false.

## One command

On the self-hosted runner (Linux in WSL2), from a clean checkout:

```bash
python3 search/b1/run.py all --jobs 17 --out DIR
```

This runs `selfcheck`, then `tier1`, then `tier2` (each can also be run on
its own). It needs `cc` and Python 3; everything else is the standard
library and the vendored plantri, which `run.py` compiles into `DIR/bin/`.
The committed results are in `results/`.

## The bound

Gabriel's decision, recorded on #9: **tiered, 13 then 16.**

- **Tier 1:** every candidate against every triangulation with at most 13
  vertices.
- **Tier 2:** the survivors of tier 1, up to 16 vertices.
- **Beyond 16:** only by a further decision.

The bounds are parameters (`--tier1-max`, `--tier2-max`), so raising one is a
rerun, not a rewrite.

Two classes of triangulation are enumerated:

| Domain | What | Generator | Count checked against |
| --- | --- | --- | --- |
| `sphere` | triangulations of the sphere | `plantri n` | OEIS A000109 |
| `disc` | triangulations of a disc with a chordless boundary cycle of any length | `plantri -P n` | OEIS A342056 |

The count at every size, in every run, must equal the OEIS term, or the run
stops. For scale: tier 1 covers about 59,000 spheres and 2.2 million discs,
tier 2 about 20 million spheres. At 16 vertices there are 906 million discs,
which is why tier 2 for a disc candidate would need its own decision.

## Why the numbers can be trusted

`selfcheck` runs before every search, and the search does not start unless
it passes. It checks:

- **Enumeration.** plantri's counts equal OEIS A000109 (spheres) and
  A342056 (discs). Every graph is checked structurally: all faces triangles,
  Euler's formula, and for discs a chordless boundary. For every disc size k
  asked of plantri, the traced boundary has exactly k vertices.
- **Colourings, two ways.** Vertex 4-colourings are counted by backtracking
  over vertices, and Tait colourings by backtracking over the dual's edges.
  They must agree on every triangulation. The two counts are equal by Tait's
  correspondence, but they are computed on different graphs by different
  code.
- **Hamiltonian cycles of the dual, two ways.** Direct search against the
  sum, over Tait colourings, of the colour pairs that form a Hamiltonian
  cycle. Each Hamiltonian cycle corresponds to exactly one such pair, so
  the numbers must be equal.
- **Precolouring extension against brute force.** On small discs, the
  boundary colourings that `extends` accepts must equal the set obtained by
  trying every colour assignment to every vertex.
- **The canonical form**, used to pick one well-defined smallest
  counterexample, must give distinct codes to plantri's distinct outputs.
  It must also give the same code to randomly relabelled and mirrored
  copies (seed recorded in the header).

The K1 counterexample was also confirmed outside the harness by brute force.
All 72 labelled 4-colourings of that 8-vertex triangulation fall into two
Kempe classes, of 24 and 48 colourings.

## The candidate language

A candidate is a `Candidate` in `candidates.py`: an id, a family, a domain
(`sphere` or `disc`), a palette, the statement in words exactly as tested,
what is expected and why, and a `test` that takes one triangulation and
returns `None` if the statement holds, or a witness if it fails.

**List-style candidates are rejected before they run.** Planar graphs are
not 4-choosable (Voigt 1993), so a candidate with `palette="lists"` is
already dead. L1 is there to show the rejection working.

To add a candidate, append it to `CANDIDATES`. The test must be
deterministic, and it sees one triangulation at a time.

## The candidates

The four families of the plan of record, with at least one candidate each.
Each also has one control: a candidate whose outcome is known in advance,
so the harness is seen to get it right.

| Id | Family | Statement (short) | Known in advance |
| --- | --- | --- | --- |
| PE1 | precolouring extension | every 4-colouring of a disc's boundary extends | false: control |
| PE2 | precolouring extension | every boundary colouring with at most 3 colours extends | open to us |
| K1 | Kempe connectivity | all 4-colourings are Kempe-equivalent | open to us |
| BAL1 | balanced colourings | an equitable 4-colouring exists | expected false |
| BAL2 | balanced colourings | a 4-colouring with every class < n/2 exists | a theorem: positive control |
| FL1 | flows | the dual has a Tait colouring with a Hamiltonian 2-colour cycle | false, but only from 21 vertices |
| FL2 | flows | the dual has a Tait colouring whose three 2-colour pairs are all Hamiltonian | open to us |
| L1 | (lists) | every triangulation is 4-choosable | rejected up front |

The full statements, the expectations and their sources are in
`candidates.py`. The results are in `results/` and in
`notes/B-structure-and-dynamics.md`.

## Outputs

`DIR/tier1-report.txt` and `DIR/tier2-report.txt` give, for each candidate:
- the verdict;
- the number of triangulations tested at each size;
- for a killed candidate:
  - the smallest counterexample, in plantri's ascii code (vertices a, b,
    c, …, neighbours clockwise), with its boundary cycle for a disc;
  - the witness;
  - how many counterexamples of that size there are.

The report depends only on the code, plantri and the bound, so it reruns
byte-identically. The smallest counterexample is well defined because it is
the one with the least canonical code, however the work was split between
processes. `*-summary.json` holds the same information, and
`*-timings.json` holds the run times, which are never compared.
