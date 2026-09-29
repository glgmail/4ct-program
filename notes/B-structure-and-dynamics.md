# Workstream B — Structure and dynamics

Results log. Newest first. One row per result, added in the pull request that
produced it.

A row belongs here only if it meets the trust rule: a Lean theorem that builds
on the pinned toolchain, or a script whose output reruns identically from a
clean checkout. Leads, partial arguments and AI-written summaries go under
"Open leads" instead, and are not results.

| Date | Result | Evidence | Tier | PR |
| --- | --- | --- | --- | --- |
| 2026-09-28 | **No triangulation of the sphere with at most 16 vertices is a counterexample to BAL2 or FL1.** BAL2: a 4-colouring with every class smaller than n/2 exists (a published theorem). FL1: the dual is Hamiltonian (false in general, from 21 vertices). That is 20,295,520 triangulations, every one up to isomorphism. This is a computation, not a proof: FL1 survives and is false. | `search/b1/run.py all`, clean clone at `9f7a9b9`; `search/b1/results/tier2-report.txt` | B1 | #32 |
| 2026-09-28 | **Five candidate strengthenings of the 4CT are false, with smallest counterexamples.** PE1 at 5 vertices (control). PE2, boundary colourings with at most 3 colours extend, at 6. BAL1, an equitable 4-colouring exists, at 7. FL2, a Tait colouring with all three colour pairs Hamiltonian, at 6 (the octahedron). K1, all 4-colourings are Kempe-equivalent, at 8. Each counterexample is written out in `tier1-report.txt` and can be checked by hand. | `search/b1/run.py all`, clean clone at `9f7a9b9`; `search/b1/results/tier1-report.txt`, byte-identical on rerun; K1 confirmed separately by brute force | B1 | #32 |

## B1: the strengthening-search harness

**Bound** (Gabriel, #9): tier 1 tests every candidate against all
triangulations with at most 13 vertices, both of the sphere (58,716) and of a
disc with a chordless boundary (2,198,080). Tier 2 tests the survivors up to
16 vertices (sphere: 20,236,804 more).

**Enumeration:** plantri 5.8, vendored in `third_party/plantri/`. The count
at every size equals OEIS A000109 (spheres) and A342056 (discs).

**Machinery checked before every search:** 60 self-checks, listed in
`search/b1/README.md`. They include colourings counted two independent ways
(vertex and Tait), Hamiltonian cycles counted two ways, disc extension
against brute force, and the canonical form checked on every graph up to 11
vertices.

**Cost:** 34 minutes for everything, on 17 processes. Almost all of it is the
16-vertex step: 31 minutes, 8.8 CPU-hours.

| Id | Candidate | Verdict | Smallest counterexample |
| --- | --- | --- | --- |
| PE1 | every 4-colouring of a disc's boundary extends | killed (control, as expected) | 5 vertices: the 4-wheel, boundary coloured 0,1,2,3 |
| PE2 | every boundary colouring with at most 3 colours extends | **killed** | 6 vertices: a 4-cycle boundary around two adjacent inner vertices, coloured 0,1,2,1; both inner vertices are forced to colour 3 |
| K1 | all 4-colourings are Kempe-equivalent | **killed** | 8 vertices: 3 colourings up to permutation, in 2 Kempe classes (sizes 1 and 2) |
| BAL1 | an equitable 4-colouring exists | killed (as expected) | 7 vertices: two universal vertices joined to a path of five; best class sizes 3,2,1,1 |
| BAL2 | a 4-colouring with every class < n/2 exists | not killed up to 16 | — (a theorem: Kawarabayashi, Yoneda, Yoneda, arXiv:2607.13025) |
| FL1 | the dual is Hamiltonian | not killed up to 16 | — (false from 21 vertices: Tutte 1946; Holton and McKay 1988) |
| FL2 | a Tait colouring with all three colour pairs Hamiltonian | **killed** | 6 vertices: the octahedron (dual: the cube); at most 2 of 3 pairs |
| L1 | every triangulation is 4-choosable | rejected before running (Voigt 1993) | — |

**Reading the survivors.** Both survivors were known in advance.
- **BAL2** is a published theorem, so its survival is the positive control
  working.
- **FL1** is Tait's conjecture, which is false. Its smallest counterexample
  has 21 vertices, beyond the bound. It is the reminder that "not killed up
  to 16" says nothing about truth.

No candidate that was open to us survived. The next step is better
candidates, not a larger bound.

**The K1 counterexample.** The literature has not been checked for whether
this example is known. Here it is in plantri's ascii code, with vertices a–h
and neighbours clockwise:

    8 bcde,aefgc,abghd,achfe,adfb,bedhg,bfhc,cgfd

Its 4-colourings up to permutation are three, and one of them, (0, 1, 2, 3,
2, 0, 3, 1) on a..h, admits no Kempe change that leads to either of the
other two. A separate brute-force script, with labelled colourings and no
normal form, found the same thing: 72 labelled colourings in Kempe classes of
24 and 48. As a control, the octahedron's 96 colourings form a single class.

## Open leads

- Candidates that survive, and could be tested next: restrictions of PE2
  (for example, boundary colourings in which some colour appears at most
  once), and Kempe statements restricted to classes where K1's example
  cannot occur (for example, Eulerian or 5-connected triangulations). These
  are ideas, not results.
