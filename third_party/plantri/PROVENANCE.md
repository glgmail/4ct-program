# plantri 5.8, vendored

plantri generates embedded planar graphs, among them every triangulation of
the sphere and of a disc up to isomorphism. It is by Gunnar Brinkmann and
Brendan McKay, with Heidi Van den Camp. B1 (`search/b1/`) uses it as its
enumerator.

**Licence: Apache License, Version 2.0.** See `LICENSE-2.0.txt`, and Appendix G
of `plantri-guide.txt` for the copyright statement. It is the same licence as
this repository's own code.

plantri has no public git repository, so it cannot be a submodule like the
other upstreams in `third_party/`. Instead the release tarball's files are
copied here **unmodified**. The only addition is this file.

| | |
| --- | --- |
| Source | https://users.cecs.anu.edu.au/~bdm/plantri/plantri58.tar.gz |
| Version | 5.8, "March 4, 2026" (`VERSION` in `plantri.c`) |
| Tarball | 228408 bytes, sha256 `e78a944116fec9f2c9f5e484206276cc2b0043bae803e9815f4b2683614629b8` |
| Retrieved | 2026-09-28 |

Every file below is byte-identical to the tarball's `plantri58/` directory.
`checks/repo_guardrails.py` checks the digests and fails if a file is changed,
added or removed. Do not edit anything here. To upgrade, replace the whole
directory from a new tarball and regenerate this table.

| File | Bytes | sha256 |
| --- | --- | --- |
| `LICENSE-2.0.txt` | 11358 | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| `adj4.c` | 806 | `3df3829c82ddca410f09d106eb83eccd63f3cedf12b2b78aee109f0d40b0587c` |
| `allowed_deg.c` | 18088 | `ec0665899212863d3ca3edb1776f039f055e5382577307a3abfb6a99c5ef932b` |
| `degseq.c` | 4087 | `a299d84b65661ac7466aef4c94f4d31c3056852b39a364eb337e521b67d72a5d` |
| `faceorbits.c` | 1356 | `e741ebbff81d33bc3e4b3f76463a84122cd0f93a2ed2745e7d4ddf45cf77b936` |
| `fullgen-guide.txt` | 18676 | `93b069e2dcb900663b4dc52f20530fccad517d987cf8717bfd29a20b4247a3b4` |
| `fullgen.c` | 230528 | `16366ca7881fd3d79addc53991f6445bea31295f5e754ce29ea9ee53ed94a837` |
| `makefile` | 1809 | `d6acaaa8ff98871b3d17388cfd53edda8398db62e48a3fccdeacc87b35d3d9cf` |
| `maxdeg.c` | 7407 | `d787a43551b4c19891b82e761de31d1738dce05dc6027cd312498f222fe65811` |
| `mdcount.c` | 895 | `8a0239c4fe9c4262ca448cd03ce591732a0b47c22d4791a424cc968ec4a97808` |
| `more-counts.txt` | 59471 | `5f5d741ac63eb3dddc1a4d9c98a2035233a0fec6d24cdd982e109fbf8b6d986e` |
| `nft.c` | 1424 | `fca8ebd88203e22b873d73414bd3626ce421dab70ba468b2dbfe5fbfcc48b74f` |
| `plantri-guide.txt` | 81241 | `79bbe51083318aa22797d5ca1a28cc347bc38a6871c7cf35e057863de3f785fc` |
| `plantri.c` | 620349 | `3f70de5a3cacc78b2ed25b6a257588da94a518d8ae1dae74bcd0bf259cea07e8` |
| `rng.c` | 4826 | `c55be07495c2ff5f2f1f686cf959bebd4290238063ee25cea66e5121c1a98152` |
| `rng.h` | 1172 | `38b88add5ac47fc548f280b1041867f01a0e5a39ad1fe2a0d3e7fac3a25403ad` |
| `sumlines.c` | 55565 | `2047562d5b75957127d0c4fe7e3807303558d9959756d6e17b0b0501f58fde22` |
