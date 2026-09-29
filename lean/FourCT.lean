/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT.Base
import FourCT.Equivalences
import FourCT.Examples
import FourCT.Flow
import FourCT.Penrose
import FourCT.PlaneGraph
import FourCT.Potential
import FourCT.Tait
import FourCT.Transfer

/-!
# FourCT — the Rosetta Stone

Root module of the library. One module per reformulation is added under
`FourCT/`, plus the `Transfer` tactic that moves a statement from one
reformulation to another.

`FourCT.Base` is where the library meets the base port. Because it imports
`FourColor`, the library is built with the base port by
`scripts/build_pool.py`, never by `lake build`: see `lean/README.md`.
-/
