/-
# FourCT.Transfer

The `Transfer` tactic: given a proved statement in one reformulation of the
Four Color Theorem, restate it in another, using the machine-checked
equivalences collected in this library.

Status: scaffold. The equivalences it will dispatch over do not exist yet —
they are task A3 (planar embedding and duality) and task A4 (the Tait and flow
statements). This module currently only fixes the namespace and checks that
the pinned Mathlib resolves.
-/

import Mathlib.Combinatorics.SimpleGraph.Basic

namespace FourCT

end FourCT
