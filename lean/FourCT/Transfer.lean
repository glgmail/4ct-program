/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import Mathlib.Combinatorics.SimpleGraph.Basic

/-!
# FourCT.Transfer

The `Transfer` tactic: given a proved statement in one reformulation of the
Four Color Theorem, restate it in another, using the machine-checked
equivalences collected in this library.

Status: scaffold. The equivalences it will dispatch over do not exist yet —
they are task A3 (planar embedding and duality) and task A4 (the Tait and flow
statements). This module currently only fixes the namespace and checks that
the pinned Mathlib resolves.
-/

namespace FourCT

end FourCT
