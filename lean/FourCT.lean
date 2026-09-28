/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT.Transfer

/-!
# FourCT — the Rosetta Stone

Root module of the library. One module per reformulation is added under
`FourCT/`, plus the `Transfer` tactic that moves a statement from one
reformulation to another.

Nothing is proved here. This file exists so that `lake build` has a root and
the pinned toolchain is exercised by CI from the first commit.
-/
