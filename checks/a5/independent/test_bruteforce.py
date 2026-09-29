#!/usr/bin/env python3
"""Sanity test: compare the contraction (P) and backtracking (T) of run.py
against a literal sum over all 3^E edge colourings, for small graphs
(E <= 12: the named graphs except petersen, and plantri -d -a N for N <= 6).

Usage: python3 test_bruteforce.py --plantri /home/claude/b1-out/bin/plantri
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run import EPS, DISTINCT, evaluate, named_graphs, parse_ascii, product  # noqa: E402


def brute(g, tensor):
    s = 0
    for c in product(range(3), repeat=len(g.edges)):
        p = 1
        for r in g.rot:
            p *= tensor[(c[r[0]], c[r[1]], c[r[2]])]
            if p == 0:
                break
        s += p
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plantri", required=True)
    args = ap.parse_args()
    cases = [(n, g) for n, g in named_graphs() if len(g.edges) <= 12]
    for N in (4, 5, 6):
        out = subprocess.run([args.plantri, "-d", "-a", str(N)], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, check=True).stdout
        for i, line in enumerate(l for l in out.splitlines() if l.strip()):
            cases.append(("N%d-%d" % (N, i), parse_ascii(line)))
    bad = 0
    for name, g in cases:
        P, T = evaluate(g)
        bP, bT = brute(g, EPS), brute(g, DISTINCT)
        ok = (P, T) == (bP, bT)
        bad += not ok
        print(name, P, T, bP, bT, "ok" if ok else "MISMATCH")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
