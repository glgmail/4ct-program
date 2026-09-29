#!/usr/bin/env python3
# Copyright (c) 2026 the 4ct-program contributors. Apache 2.0, see LICENSE.
"""D1 Phase 2: compare Implementation A (implA/) and Implementation B (implB/).

Written by the main session, after both implementations had finished, and
without changing either. For each web W1-W7 in B19 mode it checks:

* the half-foam files are byte-identical: A's file is gzip-compressed, so the
  SHA-256 of its uncompressed content is compared with B's file;
* every quantity both result files report is equal: N, N by move, Tait, V,
  the beta_n change points, ell, ell_q, r, r_q and N_ell;
* the Amendment 1 A2 subsets (the Unzip block alone, and the first N_e
  half-foams) have equal ell, ell_q, r and r_q in both implementations.

It prints one line per web and exits 0 only if everything agrees.

    python3 search/d1/compare.py          (from the repository root)
"""

import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEBS = [f"W{i}" for i in range(1, 8)]


def sha_a(path):
    with gzip.open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_b(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ranks(d):
    return {k: d.get(k) for k in ("ell", "ell_q", "r", "r_q")}


def main():
    ok = True
    for w in WEBS:
        da, db = HERE / "implA" / "out" / w / "B19", HERE / "implB" / "results" / w / "B19"
        ra = json.loads((da / "result.json").read_text())
        rb = json.loads((db / "result.json").read_text())
        problems = []
        ha, hb = sha_a(da / "halffoams.jsonl.gz"), sha_b(db / "halffoams.jsonl")
        if ha != hb:
            problems.append("halffoams differ")
        for key_a, key_b in [("N", "N"), ("N_by_move", "N_by_move"), ("Tait", "Tait"), ("V", "V"),
                             ("beta_changes", "beta_changes"), ("ell", "ell"), ("ell_q", "ell_q"),
                             ("r", "r"), ("r_q", "r_q"), ("N_ell", "N_ell_ours")]:
            if ra.get(key_a) != rb.get(key_b):
                problems.append(f"{key_a}: A={ra.get(key_a)!r} B={rb.get(key_b)!r}")
        # Amendment 1 A2 subsets
        sb = json.loads((db / "a2_subsets.json").read_text())
        for label, key_a, key_b in [("unzip block", "A2_unzip_block", "i_unzip_block"),
                                    ("first N_e", "A2_prefix_N_e", "ii_first_N_e")]:
            if key_b not in sb:
                problems.append(f"B has no A2 subset '{key_b}' (keys {sorted(sb)})")
            elif ranks(ra[key_a]) != ranks(sb[key_b]):
                problems.append(f"A2 {label}: A={ranks(ra[key_a])} B={ranks(sb[key_b])}")
        status = "AGREE" if not problems else "DISAGREE: " + "; ".join(problems)
        ok &= not problems
        print(f"{w}: N={ra['N']} ell={ra['ell']} Tait={ra['Tait']} r={ra['r']} halffoams={ha[:16]}  {status}")
    print("ALL AGREE" if ok else "DISAGREEMENT FOUND")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
