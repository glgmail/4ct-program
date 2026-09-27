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

## Not yet wired into the build

`lakefile.toml` globs `FourCT` and `FourCT.+` only. Task A4 adds the first
statement files (Tait and flow) and extends `globs` with `"Statements.+"` in
the same pull request.

## Order

Task A4 scaffolds these first, in this order:

1. Tait — 3-edge-colorings of bridgeless planar cubic graphs.
2. Flows — nowhere-zero `ℤ₂ × ℤ₂`-flows.

The remaining reformulations (Wagner, Kauffman, Bar-Natan, Penrose,
Diophantine) follow once the duality infrastructure from A3 is in place.
