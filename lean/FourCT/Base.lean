/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourColor

/-!
# FourCT.Base — the base port, as FourCT sees it

The one place where FourCT imports the base port, `FourColor`, vendored from
corun1024/4ct (task A2). The rest of FourCT reaches the base port through
this module, so the dependency on it is visible in one file.

The base port states the Four Colour Theorem for maps of the real plane:
`FourColor.FourColorTheorem` says that every simple map `m` (a
`FourColor.PlaneMap` satisfying `FourColor.SimpleMap`) is colourable with
four colours, `FourColor.ColorableWith 4 m`. Task A3 connects plane graphs
to this statement.

Building this module needs every FourColor module. It is built by
`scripts/build_pool.py`, never by `lake build`: see `lean/README.md`.
-/

namespace FourCT

/-- **The Four Colour Theorem, as the base port proves it**: every simple map
of the real plane can be coloured with four colours. This is
`FourColor.fourColorTheorem`, restated in the FourCT namespace. -/
theorem fourColor_base : FourColor.FourColorTheorem :=
  FourColor.fourColorTheorem

open FourColor in
/-- **The combinatorial Four Colour Theorem, as the base port proves it**: every
finite hypermap that is planar (genus zero) and bridgeless is four-colourable,
i.e. its faces can be coloured with four colours so that the two faces on
either side of every edge differ.

The base port proves this on the way to `fourColorTheorem`. Here it is
assembled from the port's unavoidability theorem and its reducibility and
presentation checks, the same inputs `FourColor.fourColorTheorem` uses. -/
theorem hypermap_fourColorable {D : Type} [Finite D] (G : Hypermap D)
    (hG : G.PlanarBridgeless) : G.FourColorable :=
  Hypermap.fourColorable_of_no_minimalCounterExample
    (fun H => Hypermap.not_minimalCounterExample (G := H)
      (redpartSound_theRedpart reducibility)
      exclude5 exclude6 exclude7 exclude8 exclude9 exclude10 exclude11) G hG

end FourCT
