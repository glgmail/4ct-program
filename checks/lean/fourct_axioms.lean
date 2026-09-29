/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT

/-!
Run by `lean-build`, from `lean/`, as `lake env lean ../checks/lean/fourct_axioms.lean`:
the axioms FourCT's theorems depend on. The workflow requires the three
standard ones and nothing else.
-/

#print axioms FourCT.fourColor_base
#print axioms FourCT.hypermap_fourColorable
#print axioms FourCT.PlaneGraph.four_colorable
#print axioms SimpleGraph.IsPlanar.colorable_four
#print axioms FourCT.Examples.isPlanar_K4
#print axioms FourCT.Examples.not_colorable_three_K4
#print axioms SimpleGraph.IsPlanar.of_isContained
#print axioms FourCT.Examples.isPlanar_of_card_le_four
#print axioms FourCT.Examples.not_isPlanar_K5
#print axioms FourCT.range_inc_face_eq
#print axioms FourCT.exists_facePotential
#print axioms FourCT.edgeColoring_taitEdge
#print axioms FourCT.exists_coloring_of_edgeColoring
#print axioms FourCT.taitEdge_eq_taitEdge_iff_of_connected
#print axioms FourCT.PlaneGraph.tait
#print axioms FourCT.Examples.taitEdge_tetraVertexColors
#print axioms FourCT.Examples.tetrahedron_colorable_of_tait
#print axioms FourCT.Examples.theta_torus
