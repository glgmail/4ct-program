# Third-party notices

This repository reuses code and data from the projects below. Each is pinned
as a git submodule under `third_party/`, at a commit; the upstream `LICENSE`
and `NOTICE` files travel with the submodule and are not edited there. This
file collects the notices that must be preserved in any redistribution.

**One project is vendored unmodified, because it has no git repository to
pin:** plantri, copied from its release tarball into `third_party/plantri/`,
where `PROVENANCE.md` records the source, the tarball's digest and every
file's digest. `checks/repo_guardrails.py` fails if any of them change.

**One project is also vendored, with modifications:** corun1024/4ct is copied
into `lean/` as this program's base port (task A2). Its licence and CeCILL-B
credit are kept alongside it at `lean/LICENSES/corun1024-4ct.txt`, and its
section below lists exactly what was changed.

Read-only upstreams that are **not** vendored and from which **no code is
copied** are listed at the end.

| Source | License | Use |
| --- | --- | --- |
| [near-linear-4ct/computer-checks](https://github.com/near-linear-4ct/computer-checks) (C++) | MIT | Reuse; keep notice |
| [near-linear-4ct/reducible-configurations](https://github.com/near-linear-4ct/reducible-configurations) | MIT | Reuse as the dataset; 8,200 files plus the degree-3 and degree-4 cases, matching the paper's 8,202 |
| [near-linear-4ct/discharging-rules](https://github.com/near-linear-4ct/discharging-rules) (84 rules) | MIT | Reuse; keep notice |
| [corun1024/4ct](https://github.com/corun1024/4ct) (Lean) | MIT, with CeCILL-B credit for data translated from Gonthier's proof | Reuse; keep both notices |
| [RBarish-UTokyo/FourColorTheorem-Lean4](https://github.com/RBarish-UTokyo/FourColorTheorem-Lean4) (Lean) | Apache 2.0 | Reuse; keep license and notices |
| [math-comp/fourcolor](https://github.com/math-comp/fourcolor) (Rocq) | CeCILL-B | Reference and attribution to Gonthier et al. |
| [plantri](https://users.cecs.anu.edu.au/~bdm/plantri/) 5.8 (C), Brinkmann and McKay | Apache 2.0 | Vendored unmodified in `third_party/plantri/`; B1's enumerator of triangulations |

---

## plantri

plantri 5.8 (4 March 2026), by Gunnar Brinkmann and Brendan McKay, with
Heidi Van den Camp: https://users.cecs.anu.edu.au/~bdm/plantri/. The copyright
statement below is reproduced from Appendix G of
`third_party/plantri/plantri-guide.txt`. The full licence is
`third_party/plantri/LICENSE-2.0.txt`.

```
Copyright is jointly held by the authors
 Gunnar Brinkmann, University of Gent, gunnar.brinkmann@ugent.be
 Brendan McKay, Australian National University, brendan.mckay@anu.edu.au

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this software except in compliance with the License.
A copy of the License is included in the package and you can also
view it at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

The files in `third_party/plantri/` are byte-identical to the release tarball
(sha256 in `third_party/plantri/PROVENANCE.md`). `search/b1/run.py` compiles
`plantri.c` as it is, with `cc -O4`, which is the build the plantri guide
gives.

---

## near-linear-4ct — computer-checks, reducible-configurations, discharging-rules

All three repositories are distributed under the MIT License. The notice below
is reproduced from `third_party/near-linear-4ct/computer-checks/LICENSE`; the
other two carry the same notice.

```
MIT License

Copyright (c) 2026 Yuta Inoue

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

These accompany "The Four Color Theorem with Linearly Many Reducible
Configurations and Near-Linear Time Coloring". Data imported from
`reducible-configurations` and `discharging-rules` into `data/` keeps its row
in `data/MANIFEST.csv`, naming this source and this license. The import (task
F3) is in `data/near-linear-4ct/`, unchanged, with each upstream `LICENSE`
file kept beside its data.

---

## corun1024/4ct

**Vendored into `lean/`, modified.** The FourColor library, its build and
verification scripts, and its tools are copied from commit `3db71e0` into
`lean/` as this program's base port. The modifications, all to build
configuration:

- `lean-toolchain`: `leanprover/lean4:v4.34.0-rc2` → `v4.34.1`;
- `lakefile.toml`: Mathlib pinned to `v4.34.1`, and merged with this
  program's own package definition;
- `lake-manifest.json`: re-resolved against Mathlib `v4.34.1`, root package
  renamed;
- `README.md` and `LICENSE` moved to `lean/UPSTREAM-README.md` and
  `lean/LICENSES/corun1024-4ct.txt`;
- `scripts/build_pool.py` (task A3) also builds this program's own libraries,
  FourCT and Statements, so that they can import FourColor. Every change is
  marked "4ct-program" in the file.

No Lean source file was modified: all 498 are byte-identical to upstream.

MIT, with a CeCILL-B credit that must be preserved. Reproduced from
`third_party/corun1024/4ct/LICENSE`, and kept verbatim beside the vendored
code at `lean/LICENSES/corun1024-4ct.txt`:

```
MIT License

Copyright (c) 2026 Chris Emery

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

--------------------------------------------------------------------------

CREDITS

This software follows the structure of, and contains data translated
mechanically from, the Coq proof of the Four Colour Theorem by Georges
Gonthier and Benjamin Werner (rocq-community/fourcolor), which is distributed
under the CeCILL-B Free Software Licence Agreement (http://www.cecill.info).
No Coq source text is copied here.  The translated data is
`FourColor/Configurations.lean` (from `configurations.v`), the presentation
scripts `FourColor/Present*.lean` (from `present*.v`), and the quiz data
computed from the configurations; each of those modules names its origin in
its header.

CeCILL-B article 5.3.2 permits distribution under a licence other than
CeCILL-B provided the credits required by its article 5.3.4 are given.  This
notice is that credit, and it must be preserved in redistributions of this
software, modified or not, along with the copyright notice above.

Reference: G. Gonthier, "Formal Proof - The Four-Color Theorem", Notices of
the AMS 55 (11), 2008.
```

---

## RBarish-UTokyo/FourColorTheorem-Lean4

Apache License, Version 2.0. The full licence is
`third_party/RBarish-UTokyo/FourColorTheorem-Lean4/LICENSE`, and the CeCILL-B
text it refers to is under `LICENSES/` in that submodule. Apache 2.0 section
4(d) requires the upstream `NOTICE` to be carried in redistributions; it is
reproduced here verbatim:

```
Four Color Theorem in Lean 4
Copyright 2026 the contributors to this repository
Written by Claude Opus 5.5 (Anthropic), working as an AI agent under the direction of
Robert D. Barish.

This work is licensed under the Apache License, Version 2.0 (see LICENSE).

It is a port to Lean 4 and Mathlib of the Coq/Rocq formal proof of the Four Color Theorem:

    fourcolor: a formal proof of the Four Color Theorem in Coq
    Georges Gonthier et al.
    Copyright (c) 2006-2018 Microsoft Corporation (Microsoft Research) and Inria
    Distributed under the terms of the CeCILL-B license (see LICENSES/CeCILL-B.txt)
    https://github.com/math-comp/fourcolor (now maintained as coq-community/fourcolor)

The definitions, the statements, the structure of the proofs and the combinatorial data (the
633 reducible configurations, the discharging rules and the unavoidability presentations) are
translated from that development, whose files carry the notice

    (c) Copyright 2006-2018 Microsoft Corporation and Inria.
    Distributed under the terms of CeCILL-B.

The configurations and discharging rules originate in N. Robertson, D. P. Sanders, P. D. Seymour
and R. Thomas, "The four-colour theorem", J. Combin. Theory Ser. B 70 (1997), 2-44.

This work depends on Lean 4 and Mathlib (Apache License, Version 2.0), which are not
redistributed here.
```

---

## math-comp/fourcolor (Gonthier et al.)

Not vendored. The original Rocq/Coq development is the reference against which
our statements are compared (task A1), and the ancestor of the combinatorial
data in both Lean ports.

```
fourcolor: a formal proof of the Four Color Theorem in Coq
Georges Gonthier et al.
(c) Copyright 2006-2018 Microsoft Corporation (Microsoft Research) and Inria.
Distributed under the terms of the CeCILL-B Free Software Licence Agreement
(http://www.cecill.info).
https://github.com/math-comp/fourcolor  (now maintained as coq-community/fourcolor)
```

Reference: G. Gonthier, "Formal Proof — The Four-Color Theorem", *Notices of
the AMS* 55 (11), 2008.

The configurations and discharging rules originate in N. Robertson,
D. P. Sanders, P. D. Seymour and R. Thomas, "The four-colour theorem",
*J. Combin. Theory Ser. B* 70 (1997), 2–44.

---

## Dependencies not redistributed here

- **Lean 4** (`leanprover/lean4`) and **Mathlib** (`leanprover-community/mathlib4`),
  both Apache License 2.0, pinned to `v4.34.1`. Fetched by `elan` and `lake`;
  no source is vendored.

---

## Read-only upstreams — no code copied

These carry **no stated license**. We may read them and follow their
instructions and target metrics, but nothing is copied from them into this
repository, and they are not added as submodules.

- [near-linear-4ct/instructions-for-checking-reproducibility](https://github.com/near-linear-4ct/instructions-for-checking-reproducibility)
  — follow the instructions and target metrics; do not copy text.
- The Codex, Claude Code and Gemini reimplementations of the near-linear
  checks — read only; no code copied. Our own implementation (task F2) is
  written from the paper's pseudocode.
