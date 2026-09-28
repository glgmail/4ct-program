#!/usr/bin/env python3
"""Summarize an F1 run: compare each metric with its published target.

    python3 checks/f1/summarize.py WORK [--smoke]

Called by checks/f1/reproduce.sh at the end of a run. Reads the logs and
status files it left in WORK and writes:

- WORK/results/results.txt: targets, observed values and exit statuses.
  Deterministic; two runs of the same commits must produce identical files.
- WORK/results/timings.tsv: wall time and peak memory per step. These vary
  between runs and are never compared.

The targets are the eleven values published in
near-linear-4ct/instructions-for-checking-reproducibility (read, not copied:
that repository has no licence; the numbers are facts about the paper).
Lemmas A.4-A.6 have no numeric target: they pass when the check exits 0,
since every unresolved case aborts through assert().

Exits 0 only if every target is met and every check passed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# (step, metric, published value, how to read the observed value)
TARGETS = [
    ("A.1", "size of R*", 1832, ("log", "all.log", r"Generated (\d+) combined rules\.")),
    ("A.1", "maximum charge of a combined rule in R*", 8,
     ("log", "all.log", r"Max amount among combined rules: (\d+)")),
    ("A.2", "size of R*-D", 671, ("log", "non_blocked.log", r"Generated (\d+) combined rules\.")),
    ("A.2", "maximum charge of a combined rule in R*-D", 5,
     ("log", "non_blocked.log", r"Max amount among combined rules: (\d+)")),
    ("A.3", "bad cartwheels with tail ranges, centre degree 7", 9366, ("zero", "d7_")),
    ("A.3", "bad cartwheels with tail ranges, centre degree 8", 728, ("zero", "d8_")),
    ("A.3", "wheels from enumPossibleBadWheels, centre degree 7", 5439,
     ("log", "wheels_d7.log", r"Generated (\d+) wheels\.")),
    ("A.3", "wheels from enumPossibleBadWheels, centre degree 8", 6790,
     ("log", "wheels_d8.log", r"Generated (\d+) wheels\.")),
    ("A.3", "wheels from enumPossibleBadWheels, centre degree 9", 3285,
     ("log", "wheels_d9.log", r"Generated (\d+) wheels\.")),
    ("A.3", "wheels from enumPossibleBadWheels, centre degree 10", 626,
     ("log", "wheels_d10.log", r"Generated (\d+) wheels\.")),
    ("A.3", "wheels from enumPossibleBadWheels, centre degree 11", 8,
     ("log", "wheels_d11.log", r"Generated (\d+) wheels\.")),
]

SMOKE_LOGS = {"all.log", "non_blocked.log", "wheels_d7.log"}

# Pass/fail checks: (lemma, step name, log, line that must be present)
CHECKS = [
    ("A.4", "A4_check_deg8", "check_deg8.log", "Finished checking degree 8 vertices."),
    ("A.5", "A5_check_7triangle", "check_7triangle.log", "Finished checking 7-triangles."),
    ("A.6", "A6_check_deg7", "check_deg7.log", "Finished checking degree 7 vertices."),
]
CONTROLS = [
    ("A.4", "control_A4_no_configurations", "control_check_deg8.log"),
    ("A.5", "control_A5_no_configurations", "control_check_7triangle.log"),
    ("A.6", "control_A6_no_configurations", "control_check_deg7.log"),
]


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def status(work: Path, name: str) -> str:
    s = read(work / "log" / "status" / name).strip()
    return s if s else "not run"


def observe(work: Path, how) -> int | None:
    if how[0] == "log":
        m = re.findall(how[2], read(work / "log" / how[1]))
        return int(m[-1]) if m else None
    if how[0] == "zero":
        zero = work / "wheels" / "zero"
        return sum(1 for p in zero.glob(how[1] + "*.cartwheel")) if zero.is_dir() else None
    raise ValueError(how)


def remaining(work: Path, log: str) -> str:
    m = re.findall(r"(\d+) cartwheels remain\.", read(work / "log" / log))
    return m[-1] if m else "?"


def main() -> int:
    work = Path(sys.argv[1]).resolve()
    smoke = "--smoke" in sys.argv[2:]
    out = work / "results"
    out.mkdir(exist_ok=True)
    lines: list[str] = []
    ok = True

    head = read(out / "env.txt").splitlines()
    upstream = next((l for l in head if l.startswith("upstream:")), "upstream: ?")
    lines += ["# F1: near-linear computer checks, reproduced with the upstream C++ code",
              f"# {upstream}",
              "# data: data/near-linear-4ct/ (reducible-configurations c2ce7a9, discharging-rules d85bfe0)",
              f"# mode: {'smoke' if smoke else 'full'}",
              ""]

    lines.append("## build")
    for name in ("build_configure", "build", "unit_tests"):
        st = status(work, name)
        lines.append(f"{name:18s} exit {st}")
        ok &= st == "0"
    tests = re.findall(r"(\d+)% tests passed, (\d+) tests failed out of (\d+)",
                       read(work / "log" / "unit_tests.log"))
    if tests:
        lines.append(f"unit tests: {tests[-1][2]} run, {tests[-1][1]} failed")
    # ctest exits 0 when it finds no tests at all; that is not a pass.
    ok &= bool(tests) and int(tests[-1][2]) > 0 and tests[-1][1] == "0"
    if not tests:
        lines.append("unit tests: none found")
    lines.append("")

    lines.append("## published targets")
    lines.append(f"{'lemma':5s}  {'metric':52s} {'published':>9s} {'observed':>9s}  result")
    met = 0
    considered = 0
    for lemma, metric, want, how in TARGETS:
        # --smoke runs A.1, A.2 and the degree-7 wheels only
        if smoke and not (how[0] == "log" and how[1] in SMOKE_LOGS):
            continue
        considered += 1
        got = observe(work, how)
        if got is None:
            result = "MISSING"
            ok = False
        elif got == want:
            result = "met"
            met += 1
        else:
            result = "DIFFERS"
            ok = False
        lines.append(f"{lemma:5s}  {metric:52s} {want:>9d} {('-' if got is None else str(got)):>9s}  {result}")
    lines.append("")

    if not smoke:
        lines.append("## A.3 detail (no published target)")
        for d in (7, 8, 9, 10, 11):
            files = read(work / "log" / "status" / f"wheel_files_d{d}").strip() or "?"
            sdir = work / "log" / "status" / "cartwheels"
            sts = [read(p).strip() for p in sdir.glob(f"d{d}_*")] if sdir.is_dir() else []
            bad = sum(1 for s in sts if s != "0")
            zero = observe(work, ("zero", f"d{d}_"))
            lines.append(f"centre degree {d:2d}: {files} wheel files, {len(sts)} enum_cartwheels jobs, "
                         f"{bad} non-zero exits, {zero} bad cartwheels written")
            ok &= bad == 0 and str(len(sts)) == files
        lines.append("")

        lines.append("## pass/fail checks (no numeric target; a failure aborts via assert)")
        for lemma, name, log, done in CHECKS:
            st = status(work, name)
            finished = done in read(work / "log" / log)
            passed = st == "0" and finished
            ok &= passed
            lines.append(f"{lemma:5s}  {name:32s} exit {st:>3s}  {remaining(work, log):>6s} cartwheels checked  "
                         f"{'passed' if passed else 'FAILED'}")
        lines.append("")

        lines.append("## anti-vacuity controls (the same checks with no configurations; must fail)")
        for lemma, name, log in CONTROLS:
            st = status(work, name)
            asserted = "Assertion" in read(work / "log" / log)
            good = st not in ("0", "not run") and asserted
            ok &= good
            lines.append(f"{lemma:5s}  {name:32s} exit {st:>3s}  assertion fired: {'yes' if asserted else 'no'}  "
                         f"{'as expected' if good else 'UNEXPECTED'}")
        lines.append("")

    verdict = (f"{met} of {considered} published targets met"
               + ("" if smoke else "; A.4-A.6 passed and their controls failed as they must")
               if ok else f"NOT REPRODUCED: {met} of {considered} published targets met; see above")
    lines.append(f"verdict: {verdict}")
    (out / "results.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # timings, never compared
    rows = ["step\twall_seconds\tpeak_rss_mb"]
    for t in sorted((work / "log" / "time").glob("*.txt")):
        text = read(t)
        wall = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): ([\d:.]+)", text)
        rss = re.search(r"Maximum resident set size \(kbytes\): (\d+)", text)
        secs = "?"
        if wall:
            parts = [float(x) for x in wall.group(1).split(":")]
            secs = f"{sum(p * 60 ** i for i, p in enumerate(reversed(parts))):.0f}"
        rows.append(f"{t.stem}\t{secs}\t{int(rss.group(1)) // 1024 if rss else '?'}")
    cw = work / "log" / "time" / "cartwheels"
    if cw.is_dir():
        for d in (7, 8, 9, 10, 11):
            vals = [read(p).split() for p in cw.glob(f"d{d}_*.txt")]
            vals = [v for v in vals if len(v) == 2]
            if vals:
                rows.append(f"cartwheel_jobs_d{d} (n={len(vals)}; sum / max job)\t"
                            f"{sum(float(v[0]) for v in vals):.0f} / {max(float(v[0]) for v in vals):.0f}\t"
                            f"max {max(int(v[1]) for v in vals) // 1024}")
    (out / "timings.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    print((out / "results.txt").read_text(encoding="utf-8"))
    print(f"timings: {out / 'timings.tsv'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
