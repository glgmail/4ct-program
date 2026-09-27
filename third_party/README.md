# third_party/

Read-only upstreams, each a git submodule pinned to a commit. Nothing here is
edited in this repository. Licences and the notices we must preserve are in
[`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

```
git submodule update --init --recursive
```

| Path | Upstream | Licence |
| --- | --- | --- |
| `near-linear-4ct/computer-checks` | [near-linear-4ct/computer-checks](https://github.com/near-linear-4ct/computer-checks) | MIT |
| `near-linear-4ct/reducible-configurations` | [near-linear-4ct/reducible-configurations](https://github.com/near-linear-4ct/reducible-configurations) | MIT |
| `near-linear-4ct/discharging-rules` | [near-linear-4ct/discharging-rules](https://github.com/near-linear-4ct/discharging-rules) | MIT |
| `corun1024/4ct` | [corun1024/4ct](https://github.com/corun1024/4ct) | MIT + CeCILL-B credit |
| `RBarish-UTokyo/FourColorTheorem-Lean4` | [RBarish-UTokyo/FourColorTheorem-Lean4](https://github.com/RBarish-UTokyo/FourColorTheorem-Lean4) | Apache 2.0 |

## Not vendored, and not to be copied from

These state **no licence**. We read them and follow their instructions and
target metrics; we copy nothing from them, and they are deliberately absent
from this directory:

- `near-linear-4ct/instructions-for-checking-reproducibility`
- the Codex, Claude Code and Gemini reimplementations of the checks

Our own implementation of the checks (task F2) is written from the paper's
pseudocode. See `checks/README.md`.
