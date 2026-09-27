/-
# FourCT — the Rosetta Stone

Root module of the library. One module per reformulation is added under
`FourCT/`, plus the `Transfer` tactic that moves a statement from one
reformulation to another.

Nothing is proved here. This file exists so that `lake build` has a root and
the pinned toolchain is exercised by CI from the first commit.
-/

import FourCT.Transfer
