# lean/Statements/

One short, human-readable file per reformulation, holding the statement alone:
the definitions it needs, the statement itself, and nothing else. Proofs live
in the modules under `lean/FourCT/`.

## Sign-off rule

**Every file in this directory needs Gabriel's written sign-off in its pull
request before merge.** The Lean kernel checks proofs; it does not check that a
statement says what we mean. A statement file that builds is not yet a result.

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

Build them with `lake build Statements` from `lean/`.

One constraint, enforced by `checks/repo_guardrails.py`: a statement file
must not `import FourColor` until the build is extended to handle it. The
base port is built by `build_pool.py`, which writes no Lake traces, so a
Lake build that reaches FourColor would rebuild all 821 of its modules with
no memory cap. Task A3 is expected to hit this first.

## Order

Task A4 scaffolds these first, in this order:

1. Tait — 3-edge-colorings of bridgeless planar cubic graphs.
2. Flows — nowhere-zero `ℤ₂ × ℤ₂`-flows.

The remaining reformulations (Wagner, Kauffman, Bar-Natan, Penrose,
Diophantine) follow once the duality infrastructure from A3 is in place.
