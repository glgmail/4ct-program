## What this changes

<!-- One or two sentences. Link the issue. -->

Closes #

## Evidence

<!-- The trust rule: a result is a Lean theorem that builds on the pinned
     toolchain, or a script whose output reruns identically from a clean
     checkout. Paste the command and the output, or link the CI run. -->

- [ ] `lean-build` passes, or this change touches no Lean.
- [ ] `checks` passes.
- [ ] Anything computational has a second, independent implementation that
      agrees — or this pull request says why not yet.

## Statement sign-off

<!-- Delete this section if the pull request touches no file in
     lean/Statements/. -->

This pull request adds or changes files under `lean/Statements/`, which need
**Gabriel's sign-off, recorded here**, before merge. Record it as given in the
Claude session: his words, the date, and the files it covers. Until then, say
it is outstanding. For each file:

- the statement in English, next to the Lean;
- what is quantified over, and what is assumed;
- where it differs from the textbook phrasing, and why.

The Lean kernel checks proofs. It does not check that a statement says what we
mean.

## Data and licences

- [ ] New files under `data/` are in Git LFS and have a `MANIFEST.csv` row
      with source, licence and sha256 — or this pull request adds no data.
- [ ] No code copied from an unlicensed upstream (see the end of
      `THIRD_PARTY_NOTICES.md`).
- [ ] Third-party licences and notices are intact.

## Leads, not results

<!-- Anything here that is an argument, a summary or a hunch rather than a
     checked result. These belong in notes/ under "Open leads". -->
