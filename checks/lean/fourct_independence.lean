/-
Copyright (c) 2026 the 4ct-program contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: the 4ct-program contributors
-/
import FourCT

/-!
Run by `lean-build`, from `lean/`, as
`lake env lean ../checks/lean/fourct_independence.lean`.

Some theorems are only worth having if they are proved **without** the Four
Colour Theorem. Tait's correspondence, the flow correspondences and the
equivalences of the statement files are such theorems: for planar maps both of
their sides are true, because the theorem is proved, so an equivalence derived
from the theorem would say nothing. The axiom check cannot see this, since the
Four Colour Theorem uses only the three standard axioms.

`#assert_independent T` walks every constant that `T`'s statement and proof
mention, and every constant those mention, and so on. It fails if the walk
reaches the Four Colour Theorem or the results that prove it: the
reducibility of the configurations and the unavoidability of the arities 5 to
11. `#assert_dependent T` is the control. It checks that the same walk does
reach them from a theorem that uses the Four Colour Theorem, so the check is
not vacuous.

The workflow requires one line of output per command, each saying the
expected thing, and no other output.
-/

namespace FourCTCheck

open Lean Elab Command

/-- The Four Colour Theorem, and the results of the base port that prove it. -/
def banned : List Name :=
  [``FourColor.fourColorTheorem, ``FourColor.reducibility,
   ``FourColor.exclude5, ``FourColor.exclude6, ``FourColor.exclude7, ``FourColor.exclude8,
   ``FourColor.exclude9, ``FourColor.exclude10, ``FourColor.exclude11,
   ``FourColor.Hypermap.not_minimalCounterExample,
   ``FourCT.fourColor_base, ``FourCT.hypermap_fourColorable]

/-- Every constant that `n`'s type and value mention, transitively. -/
def closure (env : Environment) (n : Name) : NameSet := Id.run do
  let mut seen : NameSet := {}
  let mut todo : Array Name := #[n]
  while !todo.isEmpty do
    let m := todo.back!
    todo := todo.pop
    unless seen.contains m do
      seen := seen.insert m
      if let some ci := env.find? m then
        let used := ci.type.getUsedConstants ++
          ((ci.value? (allowOpaque := true)).map (·.getUsedConstants)).getD #[]
        for c in used do
          unless seen.contains c do
            todo := todo.push c
  return seen

/-- The first result of `banned` that `n` depends on, if any. -/
def bannedDependency (env : Environment) (n : Name) : Option Name :=
  let deps := closure env n
  banned.find? deps.contains

/-- Fail unless the theorem does not depend on the Four Colour Theorem. -/
elab "#assert_independent " id:ident : command => do
  let n ← liftCoreM <| realizeGlobalConstNoOverloadWithInfo id
  match bannedDependency (← getEnv) n with
  | some b => throwError "'{n}' depends on '{b}'"
  | none => logInfo m!"'{n}' does not depend on the Four Colour Theorem"

/-- The control: fail unless the theorem does depend on the Four Colour
Theorem. -/
elab "#assert_dependent " id:ident : command => do
  let n ← liftCoreM <| realizeGlobalConstNoOverloadWithInfo id
  match bannedDependency (← getEnv) n with
  | some b => logInfo m!"'{n}' depends on the Four Colour Theorem, through '{b}' (control)"
  | none => throwError "'{n}' was expected to depend on the Four Colour Theorem"

end FourCTCheck

#assert_independent FourCT.range_inc_face_eq
#assert_independent FourCT.exists_facePotential
#assert_independent FourCT.edgeColoring_taitEdge
#assert_independent FourCT.exists_coloring_of_edgeColoring
#assert_independent FourCT.taitEdge_eq_taitEdge_iff_of_connected
#assert_independent FourCT.PlaneGraph.graphFourColorable_iff
#assert_independent FourCT.PlaneGraph.tait
#assert_independent FourCT.Examples.tetrahedron_colorable_of_tait
#assert_independent FourCT.Examples.theta_torus
#assert_independent FourCT.edgeColoring_iff_nowhereZeroFlow
#assert_independent FourCT.nowhereZeroFlow_taitEdge
#assert_independent FourCT.exists_coloring_of_nowhereZeroFlow
#assert_independent FourCT.fourColorable_iff_nowhereZeroFlow
#assert_independent FourCT.PlaneGraph.colorable_four_iff_nowhereZeroFlow_dual
#assert_independent FourCT.Examples.triangle_fourColorable_of_flow
#assert_independent FourCT.Examples.theta_torus_flow
#assert_independent FourCT.exists_isNowhereZeroFlow_iff
#assert_independent FourCT.mapForm_of_cubic
#assert_independent FourCT.tait_iff_flows
#assert_independent FourCT.tait_iff_mapForm
#assert_independent FourCT.tait_iff_vertexForm
#assert_independent FourCT.flows_iff_vertexForm
#assert_independent FourCT.Examples.dumbbell_needs_bridgeless

#assert_dependent SimpleGraph.IsPlanar.colorable_four
#assert_dependent FourCT.Examples.not_isPlanar_K5
#assert_dependent FourCT.statements_tait
#assert_dependent FourCT.statements_flows
