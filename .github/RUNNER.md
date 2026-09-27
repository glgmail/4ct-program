# The self-hosted runner

One **Windows** machine with 32 GB of RAM, registered **against this
repository only** — not against an account or an organisation.

Labels: `self-hosted`, `windows`, `32gb`.
`.github/workflows/lean-build.yml` selects `[self-hosted, windows, 32gb]`.

## Read this first: the repository is public

GitHub advises against attaching a self-hosted runner to a **public**
repository, because a pull request from a fork can otherwise run arbitrary
code on the machine. This repository is public, so the mitigations below are
not optional.

Already set on the repository:

- **Fork pull request workflows require approval from all outside
  contributors** (`all_external_contributors`), not just first-time ones. No
  fork PR runs anything until someone approves that specific run.
- `main` is protected: pull request required, `lean-build` and `checks`
  required, code-owner review required, no force pushes, no deletion.
- The default `GITHUB_TOKEN` is read-only and cannot approve pull requests.

Left to you, and it matters:

- **Never click "Approve and run" on a fork pull request without reading the
  diff**, including every workflow file and every script a workflow calls.
  One approval is one arbitrary code execution on this machine.
- Run the runner as a **dedicated low-privilege local user**, not your own
  account and not an administrator.
- Keep nothing on that machine you would not want a stranger to read. No SSH
  keys, no cloud credentials, no password manager.
- Consider a VM or a spare box rather than your daily-driver desktop.

If the repository goes back to private, this whole section relaxes.

## 1. Dependencies

From an elevated PowerShell:

```powershell
winget install --id Git.Git --silent --accept-package-agreements --accept-source-agreements
winget install --id GitHub.GitLFS --silent --accept-package-agreements --accept-source-agreements
winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
```

Then, as the user that will run the runner:

```powershell
git lfs install
git config --global core.longpaths true
```

`core.longpaths` is **required**, not advice. `.lake/packages/mathlib/...`
under a deep workspace path passes Windows' 260-character limit, and git
fails with `Filename too long`. The `lean-build` workflow checks this setting
and fails fast if it is not `true`.

Also enable long paths at the OS level, from an elevated PowerShell:

```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name LongPathsEnabled -Value 1 -PropertyType DWORD -Force
```

Check:

```powershell
git --version; git lfs version; python --version; git config --get core.longpaths
```

## 2. A C/C++ toolchain

Lean's Windows toolchain bundles clang as `leanc`, so **building `lean/`
needs nothing extra**. A separate compiler is only needed by the C++ work:
task F1 builds `near-linear-4ct/computer-checks` with CMake.

```powershell
winget install --id Kitware.CMake --silent --accept-package-agreements --accept-source-agreements
winget install --id Microsoft.VisualStudio.2022.BuildTools --silent --accept-package-agreements --accept-source-agreements --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

See "A note on task F1" at the end — the C++ side of this program was written
for Linux and will need work either way.

## 3. elan and the pinned toolchain

```powershell
Invoke-WebRequest -Uri https://elan.lean-lang.org/elan-init.ps1 -OutFile $env:TEMP\elan-init.ps1
& $env:TEMP\elan-init.ps1 -NoPrompt 1 -DefaultToolchain none
$env:Path = "$env:USERPROFILE\.elan\bin;$env:Path"
elan toolchain install leanprover/lean4:v4.34.1
elan default leanprover/lean4:v4.34.1
lean --version   # expect: Lean (version 4.34.1, ...)
```

Make the PATH entry permanent for this user:

```powershell
[Environment]::SetEnvironmentVariable('Path', "$env:USERPROFILE\.elan\bin;" + [Environment]::GetEnvironmentVariable('Path','User'), 'User')
```

`lake` ships with the toolchain, so `Get-Command lake` should now answer.

## 4. Get a registration token

Generate it yourself — it lasts one hour and must never be written into a
file in this repository.

```powershell
gh api -X POST repos/glgmail/4ct-program/actions/runners/registration-token --jq .token
```

Equivalently: **Settings → Actions → Runners → New self-hosted runner**.

## 5. Install and register the runner

```powershell
mkdir C:\actions-runner; cd C:\actions-runner
Invoke-WebRequest -Uri https://github.com/actions/runner/releases/download/v2.337.0/actions-runner-win-x64-2.337.0.zip -OutFile actions-runner-win-x64.zip
Expand-Archive -Path actions-runner-win-x64.zip -DestinationPath C:\actions-runner -Force
```

```powershell
.\config.cmd --url https://github.com/glgmail/4ct-program --token REGISTRATION_TOKEN --name 4ct-32gb --labels self-hosted,windows,32gb --work _work --unattended --replace --runasservice
```

`--labels` adds to the defaults, so the runner ends up with `self-hosted`,
`Windows`, `X64`, `windows` and `32gb`. The workflow matches on
`self-hosted`, `windows`, `32gb`.

`C:\actions-runner` is deliberately short: the work directory holds
`.lake\packages\mathlib\...`, and starting from a deep path is how you meet
the 260-character limit even with `core.longpaths` set.

## 6. Run it as a service

`--runasservice` above installs it. To manage it:

```powershell
Get-Service actions.runner.* | Format-Table Name, Status
Start-Service actions.runner.*
```

The service runs as the account you gave `config.cmd`. It must be the account
that has elan on its `PATH` and `core.longpaths` set — those are per-user
settings, and a service running as `NETWORK SERVICE` will have neither. If a
workflow reports `missing: elan` or the longpaths check fails, that is why.

## 7. Confirm

```powershell
gh api repos/glgmail/4ct-program/actions/runners --jq '.runners[] | {name, status, labels: [.labels[].name]}'
```

Then re-run `lean-build` on the open pull request. Its first step prints the
toolchain pin and the machine's memory, and fails fast on anything missing.

## Memory

`lean-build.yml` sets `JOBS=2`, `MEMORY=12000` and `LEAN_NUM_THREADS=2` so
peak memory stays under 32 GB. Some modules of the corun1024 port peak around
20 GB on their own — when a job builds that port (tasks A1 and A2), drop to
`JOBS=1`.

Windows has no `ulimit`, so these caps are advisory: nothing will stop a
runaway Lean process except the page file. Watch the first full build.

Disk: the Mathlib cache plus `data/` in Git LFS runs to tens of gigabytes,
all under `C:\actions-runner\_work`.

## A note on task F1

The near-linear C++ checks
(`third_party/near-linear-4ct/computer-checks`) are built with CMake and
driven by shell scripts — `enum_all_bad_cartwheels.sh`,
`enum_possible_bad_wheels.sh`. Those do not run natively on Windows.

Two ways through, and F1 should pick one and say which:

1. **Native Windows** — build with MSVC (step 2) and port the two shell
   drivers to PowerShell. The C++ itself is portable; the scripts are the
   work. Everything stays on one runner.
2. **WSL2** — install Ubuntu under WSL2 and run the C++ side there. The
   upstream instructions then apply unchanged, which matters because F1 must
   reproduce *published* metrics and any porting is a difference to explain.
   Cap WSL2's memory in `%UserProfile%\.wslconfig` (for example
   `memory=24GB`) so it cannot starve a concurrent Lean build.

Option 2 is the lower-risk one for F1 specifically, because the task is to
reproduce someone else's numbers and a ported script is one more reason they
might not match. Option 1 keeps the machine simpler. Gabriel decides.

The Lean side (`lean-build`) is unaffected either way and runs natively on
Windows.

## Housekeeping

- The runner serves this repository only. Do not re-register it at account or
  organisation level.
- To remove it:
  ```powershell
  cd C:\actions-runner; .\config.cmd remove --token REMOVAL_TOKEN
  ```
