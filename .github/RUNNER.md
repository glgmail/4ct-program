# The self-hosted runner

Linux, inside **WSL2**, on Gabriel's 32 GB Windows machine, registered
**against this repository only** — not against an account or an
organisation.

Labels: `self-hosted`, `linux`, `32gb`.
`.github/workflows/lean-build.yml` selects `[self-hosted, linux, 32gb]`.

Running the runner inside WSL2 rather than natively on Windows keeps the
whole program on Linux: task F1's CMake build and its `.sh` drivers work
unchanged against the published metrics, Lean and Mathlib are on their
best-supported platform, and Windows' 260-character path limit — which bites
hard on `.lake/packages/mathlib/...` — never comes up.

## Read this first: the repository is public

GitHub advises against attaching a self-hosted runner to a **public**
repository, because a pull request from a fork can otherwise run arbitrary
code on the machine. This repository is public, so the mitigations below are
not optional.

Already set on the repository:

- **Fork pull request workflows require approval from all outside
  contributors** (`all_external_contributors`), not just first-time ones.
  Nothing from a fork runs until someone approves that specific run.
- `main` is protected: pull request required, `lean-build` and `checks`
  required, code-owner review required, no force pushes, no deletion.
- The default `GITHUB_TOKEN` is read-only and cannot approve pull requests.

Left to you:

- **Never click "Approve and run" on a fork pull request without reading the
  diff**, including every workflow file and every script a workflow calls.
  One approval is one arbitrary code execution on this machine.
- Run the runner as a **dedicated non-root user** inside the distro.
- Step 2 below cuts the distro off from the Windows host. Do it.

## 1. WSL2, and the memory limit that will otherwise stop you

From an elevated PowerShell on the Windows host:

```powershell
wsl --install -d Ubuntu
```

**WSL2 defaults to roughly half the host's RAM — about 16 GB here.** That is
below the ~20 GB a single corun1024 module can take, so the build will fail
before it finishes. Raise it before anything else. Create
`%UserProfile%\.wslconfig`:

```ini
[wsl2]
memory=26GB
swap=8GB
```

26 GB leaves Windows enough to stay responsive. Then:

```powershell
wsl --shutdown
```

Start the distro again and **verify rather than assume**:

```bash
free -g
```

`MemTotal` should read about 26 GB. `lean-build`'s first step checks this
too and fails with a pointer back here if it is under 24 GB.

## 2. Cut the distro off from the Windows host

WSL2 is not a security boundary by default: it can reach your Windows drives
through `/mnt/c` and launch Windows executables through interop. With a
self-hosted runner on a public repository, close both. In the distro, edit
`/etc/wsl.conf`:

```ini
[boot]
systemd=true

[interop]
enabled=false
appendWindowsPath=false

[automount]
enabled=false
```

`systemd=true` is also what makes `svc.sh` work in step 5 — WSL2 does not
enable systemd by default.

Apply it with `wsl --shutdown` from PowerShell, then restart the distro and
check:

```bash
systemctl is-system-running    # running, or degraded — either is fine
ls /mnt                        # should be empty
```

## 3. Dependencies

```bash
sudo apt-get update
sudo apt-get install -y git git-lfs gcc g++ make cmake curl ca-certificates python3 python3-venv
git lfs install
```

`cmake`, `g++` and `make` are here for task F1's C++ checks, which now build
natively.

Check:

```bash
git --version && git lfs version && gcc --version | head -1 && python3 --version
```

## 4. elan and the pinned toolchain

```bash
curl -sSfL https://elan.lean-lang.org/elan-init.sh | sh -s -- -y --default-toolchain none
echo '. "$HOME/.elan/env"' >> ~/.bashrc
. "$HOME/.elan/env"
elan toolchain install leanprover/lean4:v4.34.1
elan default leanprover/lean4:v4.34.1
lean --version   # expect: Lean (version 4.34.1, ...)
```

`lake` ships with the toolchain, so `command -v lake` should now answer.

## 5. Get a registration token, install, register

Generate the token yourself — it lasts one hour and must never be written
into a file in this repository.

```bash
gh api -X POST repos/glgmail/4ct-program/actions/runners/registration-token --jq .token
```

Equivalently: **Settings → Actions → Runners → New self-hosted runner**.

```bash
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.337.0/actions-runner-linux-x64-2.337.0.tar.gz
tar xzf actions-runner-linux-x64.tar.gz
```

`~/actions-runner` is inside the distro's own ext4 filesystem, and that
matters: anything under `/mnt/c` crosses the 9p boundary on every file
operation, which is slow enough to notice across a Mathlib tree and the
8,202 configuration files from task F3. `lean-build` fails the run if the
workspace turns out to be under `/mnt/`.

```bash
./config.sh \
  --url https://github.com/glgmail/4ct-program \
  --token REGISTRATION_TOKEN \
  --name 4ct-32gb \
  --labels self-hosted,linux,32gb \
  --work _work \
  --unattended --replace
```

```bash
sudo ./svc.sh install "$USER"
sudo ./svc.sh start
sudo ./svc.sh status
```

The service inherits the user's environment, so `elan` must be on that
user's `PATH` — that is what the `~/.bashrc` line in step 4 is for. If a
workflow reports `missing: elan`:

```bash
cd ~/actions-runner
echo "PATH=$HOME/.elan/bin:$PATH" >> .env
sudo ./svc.sh stop && sudo ./svc.sh start
```

## 6. Make it survive a reboot

**WSL2 does not start with Windows.** Without this the runner is simply
offline after every reboot, and `lean-build` sits queued with nothing to say
why.

From an elevated PowerShell on the host, create a startup task that boots
the distro (systemd then starts the runner service):

```powershell
$action  = New-ScheduledTaskAction -Execute 'C:\Windows\System32\wsl.exe' -Argument '-d Ubuntu -- /bin/true'
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName 'Start WSL runner' -Action $action -Trigger $trigger -RunLevel Highest -User 'SYSTEM'
```

Reboot once and confirm the runner comes back idle on its own.

## 7. Confirm

```bash
gh api repos/glgmail/4ct-program/actions/runners --jq '.runners[] | {name, status, labels: [.labels[].name]}'
```

Then re-run `lean-build` on the open pull request. Its first step prints the
kernel, the toolchain pin and the memory actually visible to the runner, and
fails fast on anything missing.

Once it is green, turn on `enforce_admins` so the required checks bind
everyone, yourself included:

```bash
gh api -X POST repos/glgmail/4ct-program/branches/main/protection/enforce_admins
```

## Memory

`lean-build.yml` sets `JOBS=2`, `MEMORY=12000` and `LEAN_NUM_THREADS=2` so
peak memory stays inside the distro's 26 GB. Some modules of the corun1024
port peak around 20 GB on their own — when a job builds that port (tasks A1
and A2), drop to `JOBS=1`.

Remember there are two limits now: the distro's `memory=` in `.wslconfig`,
and the host's 32 GB behind it. Raising the first past about 28 GB will
starve Windows.

Disk: the Mathlib cache plus `data/` in Git LFS runs to tens of gigabytes,
inside the WSL virtual disk. It grows on demand but does **not** shrink when
files are deleted; reclaim with `wsl --manage Ubuntu --set-sparse true` from
the host if it gets tight.

## Housekeeping

- The runner serves this repository only. Do not re-register it at account
  or organisation level.
- To remove it:
  ```bash
  sudo ./svc.sh stop && sudo ./svc.sh uninstall
  ./config.sh remove --token REMOVAL_TOKEN
  ```
