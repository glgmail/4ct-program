# The self-hosted runner

One Linux machine with 32 GB of RAM, registered **against this repository
only** — not against an account or an organisation. A repository-level runner
is never offered to another repository, which is what we want: it holds the
Mathlib cache and the research data.

Labels: `self-hosted`, `linux`, `32gb`. `.github/workflows/lean-build.yml`
selects `[self-hosted, linux, 32gb]`.

Run everything below **on the 32 GB machine**, as the ordinary user that will
own the runner — not as root.

## 1. Dependencies

```bash
sudo apt-get update
sudo apt-get install -y git git-lfs gcc g++ make curl ca-certificates python3 python3-venv
git lfs install
```

Check:

```bash
git --version && git lfs version && gcc --version | head -1 && python3 --version
```

## 2. elan and the pinned toolchain

```bash
curl -sSfL https://elan.lean-lang.org/elan-init.sh | sh -s -- -y --default-toolchain none
echo '. "$HOME/.elan/env"' >> ~/.bashrc
. "$HOME/.elan/env"
elan toolchain install leanprover/lean4:v4.34.1
elan default leanprover/lean4:v4.34.1
lean --version   # expect: Lean (version 4.34.1, ...)
```

`lake` comes with the toolchain, so `command -v lake` should now answer.

## 3. Get a registration token

Generate it yourself — it is short-lived (one hour) and must not be written
into a file in this repository.

```bash
gh api -X POST repos/OWNER/4ct-program/actions/runners/registration-token --jq .token
```

Replace `OWNER` with your GitHub login. Equivalently: repository **Settings →
Actions → Runners → New self-hosted runner**, which shows the same token.

## 4. Install and register the runner

```bash
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.337.0/actions-runner-linux-x64-2.337.0.tar.gz
tar xzf actions-runner-linux-x64.tar.gz
```

```bash
./config.sh \
  --url https://github.com/OWNER/4ct-program \
  --token REGISTRATION_TOKEN \
  --name 4ct-32gb \
  --labels self-hosted,linux,32gb \
  --work _work \
  --unattended --replace
```

`--labels` adds to the defaults, so the runner ends up with `self-hosted`,
`Linux`, `X64`, `linux` and `32gb`. The workflow matches on
`self-hosted`, `linux`, `32gb`.

## 5. Run it as a service

```bash
sudo ./svc.sh install "$USER"
sudo ./svc.sh start
sudo ./svc.sh status
```

The service inherits the user's environment, so `elan` must be on that user's
`PATH` — that is what the `~/.bashrc` line in step 2 is for. If a workflow
reports `missing: elan`, add it to the service environment instead:

```bash
cd ~/actions-runner
echo "PATH=$HOME/.elan/bin:$PATH" >> .env
sudo ./svc.sh stop && sudo ./svc.sh start
```

## 6. Confirm

```bash
gh api repos/OWNER/4ct-program/actions/runners --jq '.runners[] | {name, status, labels: [.labels[].name]}'
```

Then re-run the `lean-build` check on an open pull request; its first step
prints the toolchain pin and the machine's memory.

## Memory

`lean-build.yml` sets `JOBS=2`, `MEMORY=12000` and `LEAN_NUM_THREADS=2` so
peak memory stays under 32 GB. Some modules of the corun1024 port peak around
20 GB on their own — when a job builds that port (task A1 and task A2), drop
to `JOBS=1` for it. The corun1024 `build.sh` reads `JOBS` and `MEMORY`
directly, so exporting them is enough.

Keep an eye on disk too: the Mathlib cache plus `data/` in Git LFS runs to
tens of gigabytes. `~/actions-runner/_work` is where it all lands.

## Housekeeping

- The runner serves this private repository only. Do not re-register it at
  account or organisation level.
- A self-hosted runner executes whatever a workflow says. That is acceptable
  here because only Gabriel can trigger runs and only Gabriel merges; keep it
  that way.
- To remove it: `sudo ./svc.sh stop && sudo ./svc.sh uninstall && ./config.sh remove --token REMOVAL_TOKEN`.
