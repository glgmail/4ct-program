# lean/Statements/

One short, human-readable file per reformulation, holding the statement alone:
the definitions it needs, the statement itself, and nothing else. Proofs, and
the equivalence of each statement with the Four Colour Theorem, live in the
modules under `lean/FourCT/` (`FourCT/Equivalences.lean`).

## Sign-off rule

**Every file in this directory needs Gabriel's sign-off, recorded in its pull
request, before merge.** The Lean kernel checks proofs; it does not check that a
statement says what we mean. A statement file that builds is not yet a result.

The sign-off is asked for as a decision in the Claude session, with each file's
Lean shown next to its English gloss. His answer goes into the pull request
description: his words, the date, and the files it covers. A sign-off he writes
on the pull request himself also counts. A merge on its own does not record
one. See `CLAUDE.md`.

A pull request touching this directory should carry, for each file:

- the statement in English, next to the Lean,
- what is quantified over and what is assumed,
- where the statement differs from the textbook phrasing, and why.

## How these get built

`lean/lakefile.toml` already declares a `Statements` library globbing
`Statements.+`, so adding a file here needs **no lakefile change**. That is
deliberate: `scripts/build_pool.py` fingerprints every FourColor module
against the whole lakefile, so editing it forces a two-hour rebuild of the
base port.

Since task A3, `scripts/build_pool.py` builds every file here together with the
base port and FourCT, from `lean/build.sh`. A statement file may therefore
import FourCT, and through it the base port. **Never `lake build` them**: Lake
does not recognise `build_pool.py`'s output, and would rebuild all 821 base-port
modules with no memory cap (see `lean/README.md`). To check one file quickly,
run `lake env lean Statements/Foo.lean` from `lean/` after `./build.sh`.

## The statements

| File | Statement | Tied to the 4CT by |
| --- | --- | --- |
| `Tait.lean` | every bridgeless plane cubic map has a proper 3-edge-colouring | `FourCT.tait_iff_vertexForm` |
| `Flows.lean` | every bridgeless plane graph has a nowhere-zero `ZMod 2 × ZMod 2`-flow | `FourCT.flows_iff_vertexForm` |

Both equivalences are proved without the Four Colour Theorem, and
`checks/lean/fourct_independence.lean` checks that in CI. Both statements are
then proved from the base port (`FourCT.statements_tait`,
`FourCT.statements_flows`).

The remaining reformulations (Wagner, Kauffman, Bar-Natan, Penrose,
Diophantine) follow.
