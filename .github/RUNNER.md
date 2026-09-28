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
  required and enforced against administrators too, no force pushes, no
  deletion.
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
self-hosted runner on a public repository, close both.

This is done in `/etc/wsl.conf`, **inside the distro**. Note two things
before you go looking for it:

- **It does not exist until you create it.** There is nothing to find and
  edit on a fresh install.
- It is a file named `wsl.conf` in `/etc` — not a directory `/etc/wsl/`.
  And it is a different file from `%UserProfile%\.wslconfig` in step 1:
  that one is on the Windows side and sets the VM's memory; this one is
  inside the distro and sets its behaviour. Neither exists by default.

From the Ubuntu shell:

```bash
sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[boot]
systemd=true

[interop]
enabled=false
appendWindowsPath=false

[automount]
enabled=false
EOF
```

`systemd=true` is also what makes `svc.sh` work in step 5 — WSL2 does not
enable systemd by default.

`appendWindowsPath=false` takes Windows executables off the distro's
`PATH`, so `gh` and friends from the Windows side stop being callable from
inside Ubuntu. That is the point, but it means **step 5's registration
token has to come from the Windows host**, not from the distro. Step 5 says
so.

Apply it with `wsl --shutdown` from PowerShell, then restart the distro and
check:

```bash
systemctl is-system-running    # running, or degraded — either is fine
ls /mnt                        # should be empty
```

## 3. Dependencies

```bash
sudo apt-get update
sudo apt-get install -y git git-lfs gcc g++ make cmake curl ca-certificates python3 python3-venv python3-numpy
sudo apt-get install -y libboost-program-options-dev libboost-thread-dev libspdlog-dev libfmt-dev
git lfs install
```

`cmake`, `g++`, `make` and the four `-dev` packages on the second line are
for task F1's C++ checks (`checks/f1/`). The upstream CMake build needs
Boost `program_options` and `thread`, spdlog and fmt, and it downloads
googletest itself at configure time. **`python3-numpy` is needed by the corun1024 port**: its
`scripts/bulkspace.py` imports numpy, and without it a build dies during
certificate generation, several minutes in. `port-build.yml` now checks for
it up front rather than letting you find out the slow way.

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

Run this **on the Windows host, in PowerShell**. Step 2 took Windows
executables off the distro's `PATH`, so `gh` is not callable from inside
Ubuntu:

```powershell
gh api -X POST repos/glgmail/4ct-program/actions/runners/registration-token --jq .token
```

Equivalently, and just as good: **Settings → Actions → Runners → New
self-hosted runner**, which shows the same token in the browser.

Then paste the token into the `config.sh` call below, which does run inside
the distro.

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

## 6. Keep the distro alive — this one is not optional

Two separate problems, and the second is the one that will waste your day.

**WSL2 does not start with Windows.** After a reboot the distro is down and
the runner with it.

**WSL2 also terminates an idle distro about 15-25 seconds after the last
`wsl.exe` client detaches — even with systemd running.** Observed on
2026-09-27: the runner service started, logged `√ Connected to GitHub`, and
16 seconds later `Runner listener exited with error code 0` as systemd shut
it down with the distro. Repeatedly. GitHub showed the runner flapping
between online and offline, jobs were picked up and orphaned mid-step, and
nothing in the runner's own logs said why, because from its point of view it
had exited cleanly.

A task that merely *boots* the distro does not fix this — it boots, exits,
and the distro dies twenty seconds later. Something must hold a client
**open**. From an elevated PowerShell:

```powershell
$action  = New-ScheduledTaskAction -Execute 'C:\Windows\System32\wsl.exe' `
             -Argument '-d Ubuntu -u root -e sleep infinity'
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName 'WSL runner keepalive' -Action $action -Trigger $trigger `
             -RunLevel Highest -User 'SYSTEM'
```

`sleep infinity` never returns, so the client never detaches and the distro
stays up. Start it now without rebooting:

```powershell
Start-Process wsl.exe -ArgumentList '-d','Ubuntu','-u','root','-e','sleep','infinity' -WindowStyle Hidden
```

Confirm it holds — this should read `RUNNING` indefinitely, not for twenty
seconds:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::Unicode
wsl.exe --list --running
```

Note the encoding line. `wsl.exe` emits UTF-16, and a script that greps its
output without accounting for that will report the distro stopped when it is
running. That mistake cost an hour of misdiagnosis.

A corollary worth knowing: a long build survives partly because the job
itself keeps a client attached. The first two-hour build here appeared to
work without a keepalive only because it was being polled every minute from
outside. Do not rely on that.

## 7. Confirm

From the Windows host again, for the same `PATH` reason as step 5:

```powershell
gh api repos/glgmail/4ct-program/actions/runners --jq '.runners[] | {name, status, labels: [.labels[].name]}'
```

Then re-run `lean-build` on the open pull request. Its first step prints the
kernel, the toolchain pin and the memory actually visible to the runner, and
fails fast on anything missing.

That is the runner done. **Do not turn on `enforce_admins`** while you are
the only collaborator — it would deadlock the repository, because GitHub
will not let you approve your own pull requests and `main` requires an
approving review. `.github/PROTECTION.md` explains the trade and when to
revisit it.

If you would rather run `gh` from inside the distro, install the Linux
build there (`https://github.com/cli/cli/blob/trunk/docs/install_linux.md`)
and `gh auth login` separately — the Windows login does not carry across
with interop off.

## Memory

The base port is built by corun's `scripts/build_pool.py`, via `build.sh`,
never by `lake build`. It schedules modules against a per-module cost table
and admits none whose predicted peak would break the budget. `lean-build.yml`
sets `JOBS=4` and `MEMORY=20` (**gigabytes**). The largest module peaks at
**20.3 GB** in a single process (measured, task A2), which is why `MEMORY`
must not go above 20 on this runner.

**Lake at v4.34.1 has no `--jobs` or `-j` option** — verified against
`src/lake/Lake/CLI/Main.lean` at that tag, whose short options are only
`q v d f o K U R h H J`. An earlier version of this file claimed
`LEAN_NUM_THREADS` caps `lake build`'s parallelism. corun's author, who
measured it, says Lake starts one job per hardware thread with no way to say
fewer. That is not verified either way here, and no longer matters: the one
build heavy enough for it to matter does not go through `lake build`.

Remember there are two limits now: the distro's `memory=` in `.wslconfig`,
and the host's 32 GB behind it. Raising the first past about 28 GB will
starve Windows.

## Disk

The distro started at 29 GB and **filled completely** after one corun build
(2026-09-27). The failure mode is worth knowing because nothing says "disk
full": `Runner.Listener` crashes at startup because it cannot write its own
diagnostic log, the wrapper relaunches it every five seconds forever, GitHub
shows the runner **offline**, and unrelated jobs die mid-step with no error.

Where it goes: about 8 GB per built port under `~/4ct-port-cache`, ~9 GB of
`~/.elan` toolchains (ours plus one per port, each on its own release
candidate), ~5 GB of `~/actions-runner/_work`, and the Mathlib cache.
RBarish's README asks for about 25 GB on its own.

The distro is now sized at 50 GB. To grow it further, from an elevated
PowerShell with the distro stopped:

```powershell
wsl --shutdown
wsl --manage Ubuntu --resize 60GB
```

The virtual disk is **sparse-by-growth**: the maximum is a ceiling, not a
reservation, so raising it does not consume host space until the distro
writes. Check host headroom first all the same — Windows running out of disk
is worse than a failed build.

Deleting files inside the distro frees them **for the distro** immediately,
which is all the runner needs. The backing `ext4.vhdx` does not shrink, so
host space is only returned by compacting. Do **not** use
`wsl --manage ... --set-sparse true`: Microsoft has disabled it over a
data-corruption bug, and `--allow-unsafe` is not worth it here. Use
`diskpart`'s `compact vdisk` with the distro shut down if you ever need the
host space back.

`port-build.yml` refuses to start below 15 GB free. That figure is measured,
not guessed: a built port tree is 8.0 GB for **both** corun1024 and RBarish,
plus about 3 GB for a toolchain not yet installed. RBarish's README asks for
about 25 GB, which is roughly three times what it actually used.

## Keeping the machine awake

A port build runs for hours. If Windows sleeps, WSL2 stops with it, the
runner service goes down, and the job is lost — GitHub will eventually mark
it failed with nothing useful in the log.

From an **elevated PowerShell on the Windows host**, stop it idling while on
mains power:

```powershell
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change disk-timeout-ac 0
```

Leave `monitor-timeout-ac` alone — the screen switching off is fine and does
not stop the build. Check what took effect with `powercfg /query` , and
`powercfg /requests` to see what is currently holding the machine awake.

Two things those settings do **not** cover:

- **Closing the laptop lid** still sleeps the machine. Change it under
  Control Panel → Power Options → "Choose what closing the lid does", or
  leave the lid open.
- **Windows Update restarts.** Set active hours, or pause updates, before a
  long build: Settings → Windows Update → Advanced options. A reboot mid-build
  loses the run even with the scheduled task bringing WSL2 back, because the
  job was already assigned to a runner that vanished.

If a build is interrupted anyway, re-dispatch `port-build` with `fresh` left
**off**: it reuses the existing checkout, so lake's incremental state and the
generated reducibility certificates survive and only the unfinished work
re-runs.

## Housekeeping

- The runner serves this repository only. Do not re-register it at account
  or organisation level.
- To remove it:
  ```bash
  sudo ./svc.sh stop && sudo ./svc.sh uninstall
  ./config.sh remove --token REMOVAL_TOKEN
  ```
