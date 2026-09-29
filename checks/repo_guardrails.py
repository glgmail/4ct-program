#!/usr/bin/env python3
"""Repository guardrails for 4ct-program.

Enforces the mechanical parts of the plan of record. Runs as the `checks`
status check on every pull request, and is meant to be run locally the same
way:

    python3 checks/repo_guardrails.py

Exits 0 if every check passes, 1 otherwise. Output is deterministic: the same
checkout produces the same bytes, so a run can be pasted into a pull request
as evidence.

    python3 checks/repo_guardrails.py --update-manifest

rewrites data/MANIFEST.csv with the digests of the files that are actually
there, leaving source_url and license alone for rows that already exist. It
never invents a source or a licence: new rows are written with empty cells and
the run fails until a human fills them in.
"""

from __future__ import annotations

import argparse
import configparser
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The whole program is pinned here. Re-pinned only at a gate review, and never
# to a release candidate.
LEAN_TOOLCHAIN = "leanprover/lean4:v4.34.1"
MATHLIB_REV = "v4.34.1"

# The Lean package root. Moved from the repository root to lean/ in task A2,
# so that the vendored corun1024 tree runs its own scripts unmodified.
LEAN_ROOT = ROOT / "lean"

MANIFEST = ROOT / "data" / "MANIFEST.csv"
MANIFEST_COLUMNS = ["path", "source_url", "license", "sha256"]

# Files under data/ that are deliberately not LFS-tracked research data.
DATA_EXEMPT = {"MANIFEST.csv", "README.md", ".gitkeep"}

# The index over the reducible configurations (task F3), built by
# search/index/build.py. One row per configuration of the paper's set D: a row
# per file under CONFIG_PREFIX, plus the two single-vertex configurations that
# D counts but upstream does not ship as files.
CONFIG_INDEX = ROOT / "search" / "index" / "configurations.csv"
CONFIG_PREFIX = "data/near-linear-4ct/reducible-configurations/D/"
CONFIG_INDEX_HEADER = ("config,path,ring_size,vertices,edges,degree_sequence,"
                       "shape,shape_oriented,chiral")
CONFIG_NOT_FILES = {"deg3", "deg4"}

EXPECTED_SUBMODULES = {
    "third_party/near-linear-4ct/computer-checks":
        "https://github.com/near-linear-4ct/computer-checks.git",
    "third_party/near-linear-4ct/reducible-configurations":
        "https://github.com/near-linear-4ct/reducible-configurations.git",
    "third_party/near-linear-4ct/discharging-rules":
        "https://github.com/near-linear-4ct/discharging-rules.git",
    "third_party/corun1024/4ct":
        "https://github.com/corun1024/4ct.git",
    "third_party/RBarish-UTokyo/FourColorTheorem-Lean4":
        "https://github.com/RBarish-UTokyo/FourColorTheorem-Lean4.git",
}

REQUIRED_NOTICES = [
    "near-linear-4ct/computer-checks",
    "near-linear-4ct/reducible-configurations",
    "near-linear-4ct/discharging-rules",
    "corun1024/4ct",
    "RBarish-UTokyo/FourColorTheorem-Lean4",
    "math-comp/fourcolor",
    "CeCILL-B",
    "Apache License, Version 2.0",
    "MIT License",
    "plantri",
]

# plantri has no git repository, so it is vendored unmodified from its
# release tarball rather than pinned as a submodule. PROVENANCE.md lists
# every file with its sha256.
PLANTRI_DIR = ROOT / "third_party" / "plantri"
PLANTRI_ROW = re.compile(r"^\| `([^`]+)` \| (\d+) \| `([0-9a-f]{64})` \|$", re.MULTILINE)

LFS_POINTER_OID = re.compile(rb"^oid sha256:([0-9a-f]{64})$", re.MULTILINE)

failures: list[str] = []
checked = 0


def report(ok: bool, name: str, detail: str = "") -> bool:
    global checked
    checked += 1
    mark = "ok  " if ok else "FAIL"
    line = f"{mark}  {name}"
    if detail:
        line += f"\n        {detail}"
    print(line)
    if not ok:
        failures.append(name)
    return ok


def content_sha256(path: Path) -> str:
    """sha256 of the file's real content.

    A Git LFS pointer already carries the sha256 of the content it stands for,
    so the digest can be checked without pulling the object.
    """
    raw = path.read_bytes()
    if raw.startswith(b"version https://git-lfs.github.com/spec/v1"):
        match = LFS_POINTER_OID.search(raw)
        if match:
            return match.group(1).decode()
    return hashlib.sha256(raw).hexdigest()


def data_files() -> list[Path]:
    if not (ROOT / "data").is_dir():
        return []
    out = []
    for path in sorted((ROOT / "data").rglob("*")):
        if not path.is_file():
            continue
        if path.relative_to(ROOT / "data").as_posix() in DATA_EXEMPT:
            continue
        out.append(path)
    return out


def read_manifest() -> tuple[list[dict[str, str]], list[str] | None]:
    if not MANIFEST.is_file():
        return [], None
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), reader.fieldnames


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_toolchain() -> None:
    # One toolchain file, in the package root. A second copy at the repository
    # root would be read by elan from there and could silently disagree.
    stray = [f for f in ("lean-toolchain", "lakefile.toml", "lake-manifest.json")
             if (ROOT / f).exists()]
    report(not stray, "no Lean package files left at the repository root",
           "" if not stray else "found: " + ", ".join(stray) + " (they belong in lean/)")
    path = LEAN_ROOT / "lean-toolchain"
    if not path.is_file():
        report(False, "lean/lean-toolchain exists")
        return
    got = path.read_text(encoding="utf-8").strip()
    report(got == LEAN_TOOLCHAIN,
           f"lean/lean-toolchain pins {LEAN_TOOLCHAIN}",
           "" if got == LEAN_TOOLCHAIN else f"found {got!r}")
    report("-rc" not in got, "lean-toolchain is not a release candidate")


def check_lakefile() -> None:
    path = LEAN_ROOT / "lakefile.toml"
    if not path.is_file():
        report(False, "lean/lakefile.toml exists")
        return
    text = path.read_text(encoding="utf-8")

    # A bare `lake build` must never build FourColor: it would rebuild 821
    # modules with no job cap or memory budget, and modules peak at 20 GB.
    m = re.search(r'^\s*defaultTargets\s*=\s*\[([^\]]*)\]', text, re.MULTILINE)
    targets = re.findall(r'"([^"]+)"', m.group(1)) if m else []
    report("FourColor" not in targets,
           "lakefile defaultTargets excludes FourColor (build it with build.sh)",
           "" if "FourColor" not in targets else f"defaultTargets = {targets}")
    revs = re.findall(r'^\s*rev\s*=\s*"([^"]+)"', text, re.MULTILINE)
    report(revs == [MATHLIB_REV] or (len(revs) == 1 and revs[0] == MATHLIB_REV),
           f"lean/lakefile.toml pins Mathlib to {MATHLIB_REV}",
           "" if revs == [MATHLIB_REV] else f"found revs {revs!r}")
    report(all("-rc" not in rev for rev in revs),
           "no lakefile dependency is a release candidate")


def check_lake_manifest() -> None:
    """The committed manifest pins every transitive dependency by commit.

    The lakefile says which Mathlib tag; the manifest says which commit that
    resolved to, and pins Mathlib's own dependencies too. It is what makes a
    build reproducible, and build_pool.py fingerprints against it.
    """
    path = LEAN_ROOT / "lake-manifest.json"
    if not path.is_file():
        report(False, "lean/lake-manifest.json is committed")
        return
    try:
        pkgs = json.loads(path.read_text(encoding="utf-8"))["packages"]
    except (ValueError, KeyError) as exc:
        report(False, "lean/lake-manifest.json parses", str(exc))
        return
    by_name = {p.get("name"): p for p in pkgs}
    ml = by_name.get("mathlib", {})
    report(ml.get("inputRev") == MATHLIB_REV,
           f"manifest resolves Mathlib from {MATHLIB_REV}",
           "" if ml.get("inputRev") == MATHLIB_REV else f"inputRev = {ml.get('inputRev')!r}")
    rcs = sorted(n for n, p in by_name.items() if "-rc" in (p.get("inputRev") or ""))
    report(not rcs, "no manifest dependency is pinned to a release candidate",
           "" if not rcs else "found: " + ", ".join(rcs))


def check_licence() -> None:
    """The program's own work is Apache 2.0, and says what that does not cover.

    A bare root LICENSE reads as covering the whole repository, including the
    vendored corun1024 code, which is MIT with a CeCILL-B credit and is not
    ours to relicense. The README's Licence section draws that line; if it
    ever disappears, the LICENSE file starts claiming more than it should.
    """
    lic = ROOT / "LICENSE"
    text = lic.read_text(encoding="utf-8") if lic.is_file() else ""
    report("Apache License" in text[:400] and "Version 2.0" in text[:400],
           "LICENSE is the Apache License, Version 2.0")
    readme = ROOT / "README.md"
    rtext = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    carved = "## Licence" in rtext and "lean/LICENSES/corun1024-4ct.txt" in rtext
    report(carved, "README states the licence does not cover the vendored port",
           "" if carved else "README.md needs a '## Licence' section naming "
                             "lean/LICENSES/corun1024-4ct.txt")


def check_vendored_port() -> None:
    """The base port is vendored under lean/, and must stay attributable."""
    lic = LEAN_ROOT / "LICENSES" / "corun1024-4ct.txt"
    ok = lic.is_file() and all(needle in lic.read_text(encoding="utf-8")
                               for needle in ("Chris Emery", "CeCILL-B", "CREDITS"))
    report(ok, "corun1024 licence and CeCILL-B credit kept with the vendored port",
           "" if ok else f"missing or incomplete: {lic.relative_to(ROOT).as_posix()}")

    # FourCT imports FourColor (task A3). FourColor is built by build_pool.py,
    # which writes no Lake traces, so Lake does not recognise it: any
    # `lake build` that reaches FourColor rebuilds all 821 modules with no job
    # cap and no memory budget. So build_pool.py builds our libraries too, and
    # lean-build never calls `lake build`.
    pool = LEAN_ROOT / "scripts" / "build_pool.py"
    m = re.search(r"^LIBRARIES = (.*)$", pool.read_text(encoding="utf-8"), re.MULTILINE) \
        if pool.is_file() else None
    libs = set(re.findall(r"\('(\w+)'", m.group(1))) if m else set()
    report({"FourColor", "FourCT", "Statements"} <= libs,
           "build_pool.py builds FourColor, FourCT and Statements",
           "" if m else "no LIBRARIES line in lean/scripts/build_pool.py")

    workflow = ROOT / ".github" / "workflows" / "lean-build.yml"
    calls = [line.strip() for line in workflow.read_text(encoding="utf-8").splitlines()
             if re.search(r"\blake build\b", line) and not line.strip().startswith("#")
             and "--no-build" not in line] if workflow.is_file() else []
    report(not calls, "lean-build never runs `lake build`",
           "" if not calls else "found: " + "; ".join(calls))

    # `lake build --old` accepts build_pool.py's output, but it ignores changes
    # in a module's imports: a stale olean would count as built. Fine at the
    # keyboard, never as verification.
    old = []
    for wf in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        for line in wf.read_text(encoding="utf-8").splitlines():
            if "--old" in line and not line.strip().startswith("#"):
                old.append(f"{wf.name}: {line.strip()}")
    report(not old, "no workflow relies on `lake build --old`",
           "" if not old else "; ".join(old))


def our_lean_files() -> list[Path]:
    """The program's own Lean files: FourCT and Statements, not the port."""
    out = []
    for base in ("FourCT", "Statements"):
        out += [LEAN_ROOT / f"{base}.lean"] + sorted((LEAN_ROOT / base).rglob("*.lean"))
    return [p for p in out if p.is_file()]


LEAN_HEADER = re.compile(
    r"\A/-\nCopyright \(c\) \d{4} the 4ct-program contributors\. All rights reserved\.\n"
    r"Released under Apache 2\.0 license as described in the file LICENSE\.\n"
    r"Authors: [^\n]+\n-/\n")


def check_our_lean() -> None:
    """FourCT and Statements carry the licence header, and contain no `sorry`.

    build_pool.py compiles them with plain `lean`, under which Mathlib's
    header linter does not run, so the header is checked here instead. The
    `sorry` check is textual, as corun's check.sh does for the port, and
    ignores a `sorry` written as code in backquotes.
    """
    files = our_lean_files()
    bad_header = [p.relative_to(ROOT).as_posix() for p in files
                  if not LEAN_HEADER.match(p.read_text(encoding="utf-8"))]
    report(not bad_header, f"FourCT and Statements files carry the licence header ({len(files)} files)",
           "" if not bad_header else "missing or malformed in: " + ", ".join(bad_header))
    sorries = []
    for p in files:
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\bsorry\b", re.sub(r"`[^`]*`", "", line)):
                sorries.append(f"{p.relative_to(ROOT).as_posix()}:{i}")
    report(not sorries, "no `sorry` in FourCT or Statements",
           "" if not sorries else "found at: " + ", ".join(sorries[:10]))


def check_gitattributes() -> None:
    path = ROOT / ".gitattributes"
    if not path.is_file():
        report(False, ".gitattributes exists")
        return
    text = path.read_text(encoding="utf-8")
    report(re.search(r"^data/\*\*\s+filter=lfs\b", text, re.MULTILINE) is not None,
           "data/** is tracked by Git LFS")


def check_notices() -> None:
    path = ROOT / "THIRD_PARTY_NOTICES.md"
    if not path.is_file():
        report(False, "THIRD_PARTY_NOTICES.md exists")
        return
    text = path.read_text(encoding="utf-8")
    missing = [needle for needle in REQUIRED_NOTICES if needle not in text]
    report(not missing,
           "THIRD_PARTY_NOTICES.md names every upstream and licence",
           "" if not missing else "missing: " + ", ".join(missing))


def check_submodules() -> None:
    path = ROOT / ".gitmodules"
    if not path.is_file():
        report(False, ".gitmodules exists")
        return
    parser = configparser.ConfigParser()
    parser.read_string(path.read_text(encoding="utf-8"))
    found = {}
    for section in parser.sections():
        if not section.startswith("submodule "):
            continue
        found[parser.get(section, "path", fallback="")] = \
            parser.get(section, "url", fallback="")

    for sub_path, url in sorted(EXPECTED_SUBMODULES.items()):
        got = found.get(sub_path)
        report(got == url, f"submodule {sub_path}",
               "" if got == url else f"expected {url}, found {got!r}")

    extra = sorted(set(found) - set(EXPECTED_SUBMODULES))
    report(not extra, "no unexpected submodules",
           "" if not extra else "found: " + ", ".join(extra))

    # .gitmodules only describes the submodules; the commit each is pinned to
    # lives in the tree as a gitlink. A plain `git add -A` run while the
    # submodule directories are not checked out will happily stage their
    # removal and leave .gitmodules untouched, so check the tree too.
    try:
        listing = subprocess.run(
            ["git", "ls-files", "-s", "--", "third_party"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        report(False, "gitlinks are present in the tree", f"could not run git: {exc}")
        return

    gitlinks = {}
    for line in listing.splitlines():
        meta, _, path = line.partition("\t")
        fields = meta.split()
        if fields and fields[0] == "160000":
            gitlinks[path] = fields[1]

    for sub_path in sorted(EXPECTED_SUBMODULES):
        sha = gitlinks.get(sub_path)
        report(sha is not None, f"gitlink {sub_path}",
               "" if sha else "no commit pinned in the tree; "
                              "the submodule is described but not recorded")

    # Nothing from an unlicensed upstream may be vendored.
    forbidden = ("instructions-for-checking-reproducibility",)
    bad = [p for p in found for f in forbidden if f in found[p] or f in p]
    report(not bad, "no unlicensed upstream is vendored",
           "" if not bad else "found: " + ", ".join(bad))


def check_vendored_plantri() -> None:
    """third_party/plantri is the release tarball, unmodified.

    Every file must match the digest PROVENANCE.md records for it, and there
    must be no file that PROVENANCE.md does not list. The licence must be
    among them.
    """
    prov = PLANTRI_DIR / "PROVENANCE.md"
    if not report(prov.is_file(), "third_party/plantri/PROVENANCE.md exists"):
        return
    rows = {m.group(1): (int(m.group(2)), m.group(3))
            for m in PLANTRI_ROW.finditer(prov.read_text(encoding="utf-8"))}
    on_disk = sorted(p.name for p in PLANTRI_DIR.iterdir()
                     if p.is_file() and p.name != "PROVENANCE.md")
    bad = []
    for name in sorted(set(rows) | set(on_disk)):
        path = PLANTRI_DIR / name
        if name not in rows:
            bad.append(f"{name}: not in PROVENANCE.md")
        elif not path.is_file():
            bad.append(f"{name}: missing")
        else:
            data = path.read_bytes()
            if (len(data), hashlib.sha256(data).hexdigest()) != rows[name]:
                bad.append(f"{name}: differs from the release tarball")
    report(not bad and "LICENSE-2.0.txt" in rows,
           f"third_party/plantri matches its release tarball ({len(rows)} files)",
           "; ".join(bad[:5]) if bad else ("" if "LICENSE-2.0.txt" in rows
                                           else "LICENSE-2.0.txt is not listed"))


def check_manifest() -> None:
    rows, fieldnames = read_manifest()
    if fieldnames is None:
        report(False, "data/MANIFEST.csv exists")
        return
    if not report(list(fieldnames) == MANIFEST_COLUMNS,
                  "data/MANIFEST.csv has the expected columns",
                  "" if list(fieldnames) == MANIFEST_COLUMNS
                  else f"found {list(fieldnames)!r}"):
        return

    by_path = {row["path"]: row for row in rows}
    report(len(by_path) == len(rows), "no duplicate paths in the manifest")

    on_disk = {p.relative_to(ROOT).as_posix(): p for p in data_files()}

    unlisted = sorted(set(on_disk) - set(by_path))
    report(not unlisted, "every file under data/ has a manifest row",
           "" if not unlisted else "unlisted: " + ", ".join(unlisted[:10]))

    missing = sorted(set(by_path) - set(on_disk))
    report(not missing, "every manifest row points at a file that is there",
           "" if not missing else "missing: " + ", ".join(missing[:10]))

    incomplete = sorted(
        path for path, row in by_path.items()
        if not (row.get("source_url") or "").strip()
        or not (row.get("license") or "").strip()
    )
    report(not incomplete, "every manifest row names a source and a licence",
           "" if not incomplete else "incomplete: " + ", ".join(incomplete[:10]))

    mismatched = []
    for path in sorted(set(by_path) & set(on_disk)):
        want = (by_path[path].get("sha256") or "").strip().lower()
        got = content_sha256(on_disk[path])
        if want != got:
            mismatched.append(f"{path}: manifest {want or '(empty)'} != file {got}")
    report(not mismatched, "every manifest digest matches the file",
           "" if not mismatched else "\n        ".join(mismatched[:10]))


def check_config_index() -> None:
    """The configuration index covers exactly the imported configurations.

    CI does not pull LFS objects, so it cannot rebuild the index here; that is
    `python3 search/index/build.py --check`. What it can check is that the
    index and the manifest agree on which configurations exist.
    """
    rows, _ = read_manifest()
    conf_paths = {r["path"] for r in rows if r["path"].startswith(CONFIG_PREFIX)
                  and r["path"].endswith(".conf")}
    if not conf_paths and not CONFIG_INDEX.is_file():
        return
    exists = CONFIG_INDEX.is_file()
    if not report(exists, "the configuration index exists",
                  "" if exists else f"{CONFIG_INDEX.relative_to(ROOT).as_posix()} is missing"):
        return
    text = CONFIG_INDEX.read_text(encoding="ascii")
    header = text.split("\n", 1)[0]
    if not report(header == CONFIG_INDEX_HEADER, "the configuration index has the expected columns",
                  "" if header == CONFIG_INDEX_HEADER else f"found {header!r}"):
        return
    index = list(csv.DictReader(text.splitlines()))
    names = [r["config"] for r in index]
    report(len(names) == len(set(names)), "no configuration is indexed twice")
    indexed = {r["path"] for r in index if r["path"]}
    not_files = {r["config"] for r in index if not r["path"]}
    ok = indexed == conf_paths and not_files == CONFIG_NOT_FILES
    detail = []
    if indexed - conf_paths:
        detail.append("indexed but not in the manifest: " + ", ".join(sorted(indexed - conf_paths)[:5]))
    if conf_paths - indexed:
        detail.append("in the manifest but not indexed: " + ", ".join(sorted(conf_paths - indexed)[:5]))
    if not_files != CONFIG_NOT_FILES:
        detail.append(f"rows without a file: {sorted(not_files)}, expected {sorted(CONFIG_NOT_FILES)}")
    report(ok, f"the configuration index covers the {len(conf_paths)} files and "
               f"{len(CONFIG_NOT_FILES)} single-vertex configurations",
           "; ".join(detail))


def check_statements_signoff_note() -> None:
    path = ROOT / "lean" / "Statements" / "README.md"
    ok = path.is_file() and "sign-off" in path.read_text(encoding="utf-8")
    report(ok, "lean/Statements/ carries the sign-off rule")


def check_house_rules() -> None:
    """CLAUDE.md is how the house rules reach every agent run.

    Claude Code reads it automatically as project context, in the GitHub
    Action and locally, so it is load-bearing rather than documentation. If
    a rule silently disappears from it, nothing else puts it back.
    """
    path = ROOT / "CLAUDE.md"
    if not path.is_file():
        report(False, "CLAUDE.md exists")
        return
    text = path.read_text(encoding="utf-8")
    required = {
        "never merge": "Never merge a pull request",
        "no tags or releases": "Never publish a release or push a tag",
        "no visibility change": "Never change the repository's visibility",
        "toolchain pin": LEAN_TOOLCHAIN.rsplit(":", 1)[-1],
        "statement sign-off": "sign-off",
        "trust rule": "reruns identically",
        "unlicensed upstreams": "Copy nothing",
    }
    missing = [name for name, needle in required.items() if needle not in text]
    report(not missing, "CLAUDE.md still carries every house rule",
           "" if not missing else "missing: " + ", ".join(missing))


# --------------------------------------------------------------------------
# manifest regeneration
# --------------------------------------------------------------------------

def update_manifest() -> int:
    rows, _ = read_manifest()
    by_path = {row["path"]: row for row in rows}

    out = []
    for path in data_files():
        rel = path.relative_to(ROOT).as_posix()
        previous = by_path.get(rel, {})
        out.append({
            "path": rel,
            "source_url": (previous.get("source_url") or "").strip(),
            "license": (previous.get("license") or "").strip(),
            "sha256": content_sha256(path),
        })

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS,
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)

    blank = [row["path"] for row in out
             if not row["source_url"] or not row["license"]]
    print(f"wrote {MANIFEST.relative_to(ROOT)} with {len(out)} row(s)")
    if blank:
        print("\nThese rows need a source URL and a licence before CI will pass:")
        for path in blank:
            print(f"  {path}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-manifest", action="store_true",
                        help="rewrite data/MANIFEST.csv from the files on disk")
    args = parser.parse_args()

    if args.update_manifest:
        return update_manifest()

    print(f"repository guardrails - {ROOT.name}\n")
    check_toolchain()
    check_lakefile()
    check_lake_manifest()
    check_licence()
    check_vendored_port()
    check_our_lean()
    check_gitattributes()
    check_notices()
    check_submodules()
    check_vendored_plantri()
    check_manifest()
    check_config_index()
    check_statements_signoff_note()
    check_house_rules()

    print()
    if failures:
        print(f"{len(failures)} of {checked} checks failed:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print(f"all {checked} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
