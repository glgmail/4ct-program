#!/usr/bin/env bash
# F1: reproduce every computer check of the near-linear proof with the
# upstream MIT C++ code, near-linear-4ct/computer-checks, and log run times.
#
#   checks/f1/reproduce.sh            # every check (a day or more on 20 threads)
#   checks/f1/reproduce.sh --smoke    # build, A.1, A.2 and the degree-7 wheels only
#
# Environment:
#   WORK    scratch directory for the build and the checks' output
#           (default $HOME/f1-work; must not be under /mnt/)
#   JOBS    parallel enum_cartwheels jobs (default: nproc, as upstream's
#           enum_all_bad_cartwheels.sh; each job needs under 30 MB)
#   RESUME  1 to keep WORK and skip every step that already exited 0
#
# Writes WORK/results/: results.txt (published targets, observed values,
# exit statuses; compared for identity between runs), env.txt (the run
# header: commits, compiler, host, kernel, memory) and timings.tsv (wall
# time and peak memory per step, which vary and are never compared).
#
# The checks run exactly the command lines in the upstream README, from a
# pristine copy of the pinned upstream tree. Only the orchestration differs
# from upstream's two shell scripts. Both of them lose exit statuses:
# enum_possible_bad_wheels.sh backgrounds its jobs and exits without waiting,
# and enum_all_bad_cartwheels.sh ends in a bare `wait`. The failure signal of
# Lemmas A.4-A.6 is an assert() that aborts the process, so every status is
# kept here.
set -euo pipefail

SMOKE=0
[ "${1:-}" = "--smoke" ] && SMOKE=1

REPO=$(cd "$(dirname "$0")/../.." && pwd)
WORK=${WORK:-$HOME/f1-work}
JOBS=${JOBS:-$(nproc)}
RESUME=${RESUME:-0}
SUB=third_party/near-linear-4ct/computer-checks
DATA=$REPO/data/near-linear-4ct

die() { echo "reproduce.sh: $*" >&2; exit 1; }

# --- preflight ---------------------------------------------------------------
case "$REPO/" in /mnt/*) die "the repository is under /mnt/ ($REPO); clone it inside the distro" ;; esac
case "$WORK/" in /mnt/*) die "WORK is under /mnt/ ($WORK); use a directory inside the distro" ;; esac
case "$WORK" in "$HOME"/?*) ;; *) die "WORK must be a subdirectory of \$HOME, got $WORK" ;; esac
for tool in git cmake g++ make python3 /usr/bin/time; do
  command -v "$tool" >/dev/null || die "missing $tool"
done

# The data is the repository's own copy under data/, checked against the
# manifest; it is byte-identical to the upstream repositories at the commits
# the manifest links (task F3).
if grep -rlq '^version https://git-lfs' "$DATA" 2>/dev/null; then
  die "data/ holds LFS pointers; run 'git lfs pull' first"
fi
python3 "$REPO/checks/repo_guardrails.py" >/dev/null || die "repository guardrails fail (data manifest?)"

# The upstream checker, at the commit the superproject pins.
want=$(git -C "$REPO" ls-tree HEAD "$SUB" | awk '{print $3}')
[ -n "$want" ] || die "$SUB is not a submodule at HEAD"
git -C "$REPO" submodule update --init -- "$SUB" >/dev/null
have=$(git -C "$REPO/$SUB" rev-parse HEAD)
[ "$have" = "$want" ] || die "$SUB is at $have, the superproject pins $want"

# --- workspace ---------------------------------------------------------------
if [ "$RESUME" != 1 ]; then
  rm -rf -- "$WORK"
fi
mkdir -p "$WORK"
cd "$WORK"
if [ ! -f CMakeLists.txt ]; then
  git -C "$REPO/$SUB" archive "$want" | tar -x -C "$WORK"
fi
ln -sfn "$DATA/reducible-configurations" reducible-configurations
ln -sfn "$DATA/discharging-rules" discharging-rules
# As in the upstream README:
mkdir -p log/d{7..11} empty combined_rules/all combined_rules/non_blocked wheels/d{7..11} wheels/zero
mkdir -p results log/status log/time

# --- step runner ---------------------------------------------------------------
# step NAME 'COMMAND LINE': runs the command line with bash, under
# /usr/bin/time -v, and records its exit status. With RESUME=1 a step that
# already exited 0 is skipped.
step() {
  local name=$1 cmd=$2
  if [ "$RESUME" = 1 ] && [ "$(cat "log/status/$name" 2>/dev/null)" = 0 ]; then
    echo "[skip] $name (already exited 0)"; return 0
  fi
  echo "[$(date -u +%H:%M:%S)] $name: $cmd"
  printf '%s\n' "$cmd" > "log/status/$name.cmd"
  set +e
  /usr/bin/time -v -o "log/time/$name.txt" bash -c "$cmd"
  local rc=$?
  set -e
  echo "$rc" > "log/status/$name"
  echo "[$(date -u +%H:%M:%S)] $name: exit $rc"
}

# --- run header ------------------------------------------------------------------
{
  echo "upstream: near-linear-4ct/computer-checks @ $want"
  echo "repository: $(git -C "$REPO" rev-parse HEAD)"
  echo "data: data/near-linear-4ct/ (manifest-verified; see data/MANIFEST.csv)"
  echo "mode: $([ $SMOKE = 1 ] && echo smoke || echo full)"
  echo "jobs: $JOBS parallel enum_cartwheels; the A.4-A.6 checks use hardware_concurrency() threads"
  echo "seed: none (the upstream code uses no randomness)"
  echo "compiler: $(g++ --version | head -1)"
  echo "cmake: $(cmake --version | head -1)"
  echo "host: $(hostname)"
  echo "kernel: $(cat /proc/version)"
  grep -qi microsoft /proc/version && echo "platform: WSL2 on a Windows host"
  echo "cpus: $(nproc) visible to this process"
  echo "memory: $(free -g | awk '/^Mem:/ {print $2 " GB total"}') visible to the distro"
  echo "started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > results/env.txt

# --- build, exactly as the upstream README ------------------------------------------
step build_configure 'cmake -S . -B build > log/build_configure.log 2>&1'
step build 'cmake --build build > log/build.log 2>&1'
# Lemmas A.4-A.6 fail only by assert(); a build with NDEBUG would pass them
# vacuously. Upstream sets no build type, so none is defined. Make sure.
if grep -rqs -- '-DNDEBUG' build/src/CMakeFiles/*/flags.make; then
  die "the build defines NDEBUG, which disables the assertions A.4-A.6 rely on"
fi
grep -h 'CXX_FLAGS\|CXX_DEFINES' build/src/CMakeFiles/main.dir/flags.make > results/compile-flags.txt
# Upstream calls enable_testing() in test/CMakeLists.txt, so ctest must be
# pointed at build/test; at build/ it finds no tests and still exits 0.
step unit_tests 'ctest --test-dir build/test > log/unit_tests.log 2>&1'

# --- Lemma A.1 and A.2 ------------------------------------------------------------------
step A1_combine_rules './build/src/main --combine_rules -R discharging-rules/R -C empty -o combined_rules/all > log/all.log'
step A2_combine_rules './build/src/main --combine_rules -R discharging-rules/R -C reducible-configurations/D -o combined_rules/non_blocked > log/non_blocked.log'

# --- Lemma A.3: wheels (upstream runs the five degrees concurrently) ---------------------
degrees="7 8 9 10 11"
[ $SMOKE = 1 ] && degrees="7"
pids=()
for d in $degrees; do
  step "A3_enum_wheels_d$d" "./build/src/main --enum_wheels -d $d -R discharging-rules/R -C reducible-configurations/D -S combined_rules/non_blocked -o wheels/d$d > log/wheels_d$d.log" &
  pids+=($!)
done
for p in "${pids[@]}"; do wait "$p"; done

if [ $SMOKE = 0 ]; then
  # --- Lemma A.3: bad cartwheels from every wheel --------------------------------------
  # Upstream: enum_all_bad_cartwheels.sh DEGREE N, one job per wheel file,
  # with the wheel counts written into its README. N here is the number of
  # wheel files this run produced, so a count that differs from the paper's
  # cannot be masked by a hard-coded one.
  cat > job.sh <<'JOB'
#!/usr/bin/env bash
d=$1 idx=$2
st=log/status/cartwheels/d${d}_${idx}
if [ "${RESUME:-0}" = 1 ] && [ "$(cat "$st" 2>/dev/null)" = 0 ]; then exit 0; fi
wheel="wheels/d${d}/d${d}_${idx}.cartwheel"
/usr/bin/time -f '%e %M' -o "log/time/cartwheels/d${d}_${idx}.txt" \
  ./build/src/main --enum_cartwheels -w ${wheel} -C reducible-configurations/D -R discharging-rules/R -S combined_rules/non_blocked -o wheels/zero > log/d${d}/enum_d${d}_${idx}.log
rc=$?
echo "$rc" > "$st"
exit 0
JOB
  chmod +x job.sh
  mkdir -p log/status/cartwheels log/time/cartwheels
  for d in 7 8 9 10 11; do
    n=$(find "wheels/d$d" -name "d${d}_*.cartwheel" | wc -l)
    echo "$n" > "log/status/wheel_files_d$d"
    step "A3_enum_cartwheels_d$d" "seq 0 $((n - 1)) | RESUME=$RESUME xargs -P $JOBS -I{} ./job.sh $d {}"
  done

  # --- Lemmas A.4-A.6 --------------------------------------------------------------------
  step A4_check_deg8 './build/src/main --check_deg8 -W wheels/zero -C reducible-configurations/D > log/check_deg8.log'
  step A5_check_7triangle './build/src/main --check_7triangle -W wheels/zero -C reducible-configurations/D > log/check_7triangle.log'
  step A6_check_deg7 './build/src/main --check_deg7 -W wheels/zero -C reducible-configurations/D > log/check_deg7.log'

  # --- anti-vacuity controls ---------------------------------------------------------------
  # The same three checks with no reducible configurations to block
  # anything. They must fail, which shows that an assertion does fire in
  # this build when a case is left unresolved.
  step control_A4_no_configurations './build/src/main --check_deg8 -W wheels/zero -C empty > log/control_check_deg8.log 2>&1'
  step control_A5_no_configurations './build/src/main --check_7triangle -W wheels/zero -C empty > log/control_check_7triangle.log 2>&1'
  step control_A6_no_configurations './build/src/main --check_deg7 -W wheels/zero -C empty > log/control_check_deg7.log 2>&1'
fi

echo "finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> results/env.txt
python3 "$REPO/checks/f1/summarize.py" "$WORK" $([ $SMOKE = 1 ] && echo --smoke)
