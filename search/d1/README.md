# search/d1/ — lower bounds on dim J♭, reproducing Boozer (2019)

Task D1, Phase 2 (#40). J♭ is Khovanov–Robert's combinatorial version of Kronheimer–Mrowka's
foam theory, over F₂. For a planar web K, `dim J♭(K) ≤ Tait(K)`. Any finite family of half-foams
with boundary K gives a lower bound: the rank of their pairing matrix. Boozer (2019) computed such
bounds for seven non-reducible webs W1–W7 with a Mathematica program. This directory reproduces
his Tables 2 and 3 with open code, two independent ways.

## Contents

| Path | What |
| --- | --- |
| `SPEC.md` | The specification both implementations follow, with Amendment 1 (corrections from an audit of Boozer's own program; the program is not in this repository) |
| `implA/` | Implementation A: builds each half-foam explicitly and evaluates closed foams |
| `implB/` | Implementation B: computes the same half-foam vectors by transfer matrices, without building foams |
| `compare.py`, `compare-result.txt` | The main session's comparison of A and B, written after both finished |

**How independent A and B are.** Each was written by a separate agent from `SPEC.md` alone. Neither
read the other's code, the spec writer's scratch scripts, or Boozer's program. Their READMEs and
NOTES record what each read.

## Commands

In WSL (Python 3, standard library only):

```bash
cd search/d1/implA && python3 run_all.py --jobs 4
cd search/d1/implB && python3 d1b.py all --jobs 4
python3 search/d1/compare.py
```

- **Run time:** A takes about 2 minutes and B about 4 minutes. Most of B's time is its controls.
- **Memory:** under 250 MB for either.
- **Reproducible:** each implementation reruns byte-identically.
- **Not committed:** the half-foam files (119 MB uncompressed) and B's sample pairings. Gabriel's
  decision: they are regenerated on every run. Their SHA-256 digests are in `implA/README.md`,
  `implB/README.md` and `compare-result.txt`.

## Result

For every web, A and B produce **byte-identical half-foam files** (377,154 half-foams in all) and
equal values of every shared quantity. Both reproduce every entry of Boozer's Table 2 (N and ℓ)
and Table 3 (ℓ_q and r_q − ℓ_q):

| Web | Vertices | N | ℓ (lower bound on dim J♭) | Tait | r |
| --- | ---: | ---: | ---: | ---: | ---: |
| W1 (dodecahedron) | 20 | 11,160 | 58 | 60 | 60 |
| W2 | 24 | 27,792 | 120 | 120 | 120 |
| W3 | 28 | 45,960 | 162 | 162 | 162 |
| W4 | 28 | 47,196 | 178 | 180 | 180 |
| W5 | 26 | 40,704 | 188 | 192 | 192 |
| W6 | 28 | 53,172 | 248 | 252 | 252 |
| W7 | 34 | 101,970 | 308 | 312 | 312 |

**New:** Boozer evaluated only the first N_e half-foams. The full generated list gives the same
ℓ, ℓ_q, r and r_q, and so does the Unzip block alone. For the dodecahedron, each of the four
move types on its own gives 58 (as Boozer's Remark 4.2 says). So the gap at W1, W4–W7 is not an
artefact of his prefix: these half-foam families cannot close it.

**Caveats.**
- Boozer's generation procedure is reconstructed. Most of it is confirmed against his notebook,
  which contains only W1 and no Table 2 or 3 runs. The rest is inferred from matching all seven of
  his published counts N. See `SPEC.md` §10 and Amendment 1.
- W7 is the only web where the generation passes through configurations Boozer's code would abort
  on. They lie under two Saddle sites, and N still matches.

**Next** (Phase 2b, capped at 40 runner-hours): new half-foam families for the dodecahedron, to try
to lift its bound from 58 to 60. Reaching 60 would prove `dim J♭(W1) = 60 = Tait`. Staying at 58
proves nothing.
