"""Amendment 2 orchestration: F0 outputs, controls C0-C8, families, union."""

import hashlib
import json
import os
import time

from core import tait_colourings, hex_to_packed, gen
from webs import get_web, TARGETS
import a2tree as TR
import ranks
import sites as P2sites
import a2run as A
from a2run import (dumps, smap, fview, F2Space, State, cpu_seconds, utcnow,
                   base_run_info, write_run_json, is_ret)


def log(s):
    print(s, flush=True)


# ---------------------------------------------------------------- F0 (step 1)
def do_F0(args, hdir, command):
    started = A.utcnow()
    F = A.run_F0(args.jobs, hdir, log)
    R0, st = A.f0_state(F, log)
    # cross-check: F0 equals the Phase 2 STRICT-ALL single-move list
    K = get_web("W1")
    sites_, results, _, _ = P2sites.generate(K, "STRICT-ALL", None, jobs=1)
    p2 = [row for out in results for (_, _, row) in out]
    assert p2 == [l.split('"a": "')[1][:60] for l in F["lines"]], "F0 != Phase 2 STRICT-ALL list"
    d = os.path.join(args.out, "W1", "A2", "F0")
    os.makedirs(d, exist_ok=True)
    os.makedirs(hdir, exist_ok=True)
    hpath = os.path.join(hdir, "W1-A2-F0-h.jsonl")
    sha, n = A.write_h(hpath, F["lines"])
    # step 2 on the RET members of F0, from the F0 state (nothing can be novel)
    S = State(F["degs"], F["vecs"], F["T"])
    novel = []
    for i, (dg, v) in enumerate(zip(F["degs"], F["vecs"]), 1):
        if is_ret(dg):
            status, isnov = S.process(v, dg)
            assert status is None and not isnov
    nby = {"zip": 0, "unzip": 0, "saddle": 0, "ih": 0}
    for l in F["lines"]:
        nby[json.loads(l)["site"][0]] += 1
    fin = S.final(R0["ell_q"].get(-1, 0), R0["ell_q"].get(1, 0))
    cnt = F["ccnt"]
    res = {"amendment": 2, "web": "W1", "family": "F0", "sites": A.sites_json(cnt),
           "expanded_nodes": {str(k): v for k, v in sorted(cnt["expanded"].items())},
           "leaves_by_degree": smap(cnt["leaves"]), "N_leaves": sum(cnt["leaves"].values()),
           "N_retained": n, "processed": n, "h_sha256": sha, "a3_violations": 0,
           "novel": novel, "aut_novel": [], "start": S.start, "final": fin, "stop": "EXHAUSTED",
           "N": n, "ell": R0["ell"], "ell_q": smap(R0["ell_q"]), "r": R0["r"], "r_q": smap(R0["r_q"]),
           "N_by_move": nby, "C3_size": len(S.C3)}
    assert F["cnt"] == cnt
    with open(os.path.join(d, "result.json"), "w", newline="\n") as f:
        f.write(dumps(res))
    lines = A.pairsample_lines(n, lambda k: F["vecs"][k - 1], S, [])
    with open(os.path.join(d, "pairsample.tsv"), "w", newline="\n") as f:
        f.writelines(lines)
    write_run_json(d, base_run_info(command, args.jobs, F["times"],
                                    {"family": "F0", "start_utc": started, "end_utc": utcnow(),
                                     "count_check_ok": F["okc"], "count_check_msgs": F["msgs"],
                                     "h_path": hpath}))
    log("F0: N %d ell %d ell_q %s r_q %s C3 %d start %s final %s count-check %s %s"
        % (n, R0["ell"], R0["ell_q"], R0["r_q"], len(S.C3), S.start, fin, F["okc"], F["msgs"]))
    return F, R0, res


def st_factory_for(F):
    return lambda: State(F["degs"], F["vecs"], F["T"])


# ---------------------------------------------------------------- span controls C4, C5
def span_control(fam, base_degs, base_vecs, T, args, hdir, command, expect_q=None):
    spec = A.FAMILIES[fam]
    web = spec["web"]
    started = utcnow()
    t0, c0 = time.time(), cpu_seconds()
    units, ccnt = A.count_pass(fam, args.jobs)
    t1, c1 = time.time(), cpu_seconds()
    okc, msgs = A.check_expected(fam, ccnt)
    log("  %s count-only %.1fs: %s %s leaves %d retained %d" % (
        fam, t1 - t0, "ok" if okc else "MISMATCH", msgs, sum(ccnt["leaves"].values()),
        sum(ccnt["retained"].values())))
    spaces = {}

    def space(dg):
        if dg not in spaces:
            sp = F2Space()
            for bd, bv in zip(base_degs, base_vecs):
                if bd <= dg and (dg - bd) % 6 == 0:
                    sp.add(fview(bv, T))
            spaces[dg] = sp
        return spaces[dg]
    os.makedirs(hdir, exist_ok=True)
    hpath = os.path.join(hdir, "%s-A2-ctl-%s-h.jsonl" % (web, fam))
    h = hashlib.sha256()
    cnt = TR.enumerate_units(get_web(spec["web"]), spec["policies"], spec["unit"], spec["restrict"])[1]
    viol = 0
    mdegs, mvecs = [], []
    i = 0
    with open(hpath, "w", newline="\n") as fh:
        g_ = A.run_units(fam, units, "main", args.jobs)
        for c, out in g_:
            TR.merge_counts(cnt, c)
            for moves, chain, dg, hx in out:
                i += 1
                line = json.dumps({"i": i, "moves": moves, "chain": chain, "deg": dg, "a": hx}) + "\n"
                fh.write(line)
                h.update(line.encode("ascii"))
                v = hex_to_packed(hx)
                if not space(dg).contains(fview(v, T)):
                    viol += 1
                mdegs.append(dg)
                mvecs.append(v)
        g_.close()
    assert cnt == ccnt, "main/count mismatch"
    Rb = ranks.compute_all(base_degs, base_vecs, T)
    Ru = ranks.compute_all(base_degs + mdegs, base_vecs + mvecs, T)
    t2, c2 = time.time(), cpu_seconds()
    ok = okc and viol == 0 and Ru["ell"] == T and Ru["ell"] <= T
    if expect_q is not None:
        ok = ok and Ru["ell_q"] == expect_q and Ru["r_q"] == expect_q and Ru["r"] == T
    res = {"amendment": 2, "web": web, "control": fam.split("-")[0], "family": fam,
           "sites": A.sites_json(ccnt),
           "expanded_nodes": {str(k): v for k, v in sorted(ccnt["expanded"].items())},
           "leaves_by_degree": smap(ccnt["leaves"]), "N_leaves": sum(ccnt["leaves"].values()),
           "N_retained": sum(ccnt["retained"].values()), "processed": i, "h_sha256": h.hexdigest(),
           "span_violations": viol,
           "baseline": {"N": len(base_degs), "ell": Rb["ell"], "ell_q": smap(Rb["ell_q"]),
                        "r": Rb["r"], "r_q": smap(Rb["r_q"])},
           "union": {"N": len(base_degs) + i, "ell": Ru["ell"], "ell_q": smap(Ru["ell_q"]),
                     "r": Ru["r"], "r_q": smap(Ru["r_q"])},
           "pass": ok}
    d = os.path.join(args.out, web, "A2", "ctl-" + fam.split("-")[0])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "result.json"), "w", newline="\n") as f:
        f.write(dumps(res))
    write_run_json(d, base_run_info(command, args.jobs, (t0, t1, t2, c0, c1, c2),
                                    {"family": fam, "start_utc": started, "end_utc": utcnow(),
                                     "count_check_ok": okc, "count_check_msgs": msgs,
                                     "h_path": hpath}))
    log("%s: %s violations %d baseline ell %d union ell %d r %d ell_q %s r_q %s wall %.1fs cpu %.1fs"
        % (fam, "PASS" if ok else "FAIL", viol, Rb["ell"], Ru["ell"], Ru["r"], Ru["ell_q"],
           Ru["r_q"], t2 - t0, c2 - c0))
    return ok, res


def do_C4(args, hdir, command):
    from controls import EXP94
    ok = True
    for w in ("prism5", "cube"):
        K = get_web(w)
        S = tait_colourings(K)
        G = gen(K, S, True, None)
        base_vecs = []
        for i in range(G.n):
            base_vecs.append(TR.row_packed(G.cols, i))
        o, _ = span_control("C4-" + w, list(G.degs), base_vecs, len(S), args, hdir, command,
                            expect_q=EXP94[w])
        ok = ok and o
    return ok


def do_C5(args, hdir, command):
    ok = True
    for w in ("W2", "W3"):
        K = get_web(w)
        sites_, results, _, _ = P2sites.generate(K, "B19", TARGETS[w]["outer"], jobs=args.jobs)
        degs, vecs = [], []
        for out in results:
            for _, dg, row in out:
                degs.append(dg)
                vecs.append(hex_to_packed(row))
        assert len(degs) == {"W2": 27792, "W3": 45960}[w]
        o, _ = span_control("C5-" + w, degs, vecs, TARGETS[w]["tait"], args, hdir, command)
        ok = ok and o
    return ok


# ---------------------------------------------------------------- C0, C6
def do_C0(F, R0, args):
    K = get_web("W1")
    st = State(F["degs"], F["vecs"], F["T"])
    sites_, results, _, _ = P2sites.generate(K, "B19", TARGETS["W1"]["outer"], jobs=1)
    bad_m3 = bad_3 = n_m3 = n_3 = 0
    for out in results:
        for _, dg, row in out:
            v = hex_to_packed(row)
            if dg == -3:
                n_m3 += 1
                if not st.U.contains(fview(v, F["T"])):
                    bad_m3 += 1
            if dg == 3:
                n_3 += 1
                if not st.A3.contains(fview(v, F["T"])):
                    bad_3 += 1
    ok = bad_m3 == 0 and bad_3 == 0 and R0["ell"] >= 58
    res = {"amendment": 2, "web": "W1", "control": "C0", "b19_deg_m3": n_m3, "b19_deg_m3_not_in_U0": bad_m3,
           "b19_deg_3": n_3, "b19_deg_3_not_in_A3": bad_3, "ell_F0": R0["ell"], "pass": ok}
    d = os.path.join(args.out, "W1", "A2", "ctl-C0")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "result.json"), "w", newline="\n") as f:
        f.write(dumps(res))
    log("C0: %s %s" % ("PASS" if ok else "FAIL", res))
    return ok


def do_C6_perms(F, args):
    K = get_web("W1")
    perms = A.aut_perms(K, F["tait"])
    st = State(F["degs"], F["vecs"], F["T"])
    T = F["T"]
    bad_u = bad_a = 0
    for pi in perms:
        for v in st.f0_m3:
            if not st.U.contains(fview(A.act(pi, v), T)):
                bad_u += 1
        for v in st.f0_3:
            if not st.A3.contains(fview(A.act(pi, v), T)):
                bad_a += 1
    # beta invariance on the F0 direct-evaluation sample pairs
    n = len(F["vecs"])
    n3 = len(st.f0_3)
    bad_b = 0
    for k in range(1, 1001):
        i = 1 + (7919 * k) % n
        u = F["vecs"][i - 1]
        w = st.f0_3[(104729 * k) % n3]
        b0 = ranks.beta(u, w)
        for pi in perms:
            if ranks.beta(A.act(pi, u), A.act(pi, w)) != b0:
                bad_b += 1
    ident = perms[0] == list(range(len(F["tait"])))
    ok = len(perms) == 120 and ident and bad_u == 0 and bad_a == 0 and bad_b == 0
    return ok, {"n_aut": len(perms), "identity_first": ident, "F0_m3_images_not_in_U0": bad_u,
                "F0_3_images_not_in_A3": bad_a, "beta_invariance_failures": bad_b}


def do_C3_summary(results_by_fam, args):
    """C3: count-only numbers vs A2.5, and T2 per-first-move uniformity."""
    out = {}
    ok = True
    for fam, (okc, msgs) in results_by_fam.items():
        out[fam] = {"ok": okc, "msgs": msgs}
        ok = ok and okc
    uni = None
    if "T2" in A.LAST_UNIT_COUNTS:
        per = A.LAST_UNIT_COUNTS["T2"]
        sig = set()
        for c in per:
            lv = c["sites"][2]
            tot = tuple(sum(lv[k][o] for k in TR.KINDS) for o in TR.OUTCOMES)
            sig.add((tot, sum(c["retained"].values())))
        uni = {"units": len(per), "signatures": sorted([list(t) + [r] for t, r in sig])}
        uok = len(per) == 60 and sig == {((4, 71, 87, 190), 837)}
        uni["ok"] = uok
        ok = ok and uok
    res = {"amendment": 2, "web": "W1", "control": "C3", "families": out, "T2_uniformity": uni, "pass": ok}
    d = os.path.join(args.out, "W1", "A2", "ctl-C3")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "result.json"), "w", newline="\n") as f:
        f.write(dumps(res))
    log("C3: %s %s" % ("PASS" if ok else "FAIL", json.dumps(res, sort_keys=True)))
    return ok


# ---------------------------------------------------------------- union (step 4)
def do_union(F, R0, fam_novels, args):
    S = State(F["degs"], F["vecs"], F["T"])
    novel = []
    stop = None
    for fam, items in fam_novels:
        for (label, dg, v) in items:
            status, isnov = S.process(v, dg)
            if isnov:
                novel.append([fam] + list(label) + [dg, len(S.U), len(S.P)])
            if status:
                stop = status
                break
        if stop:
            break
    fin = S.final(R0["ell_q"].get(-1, 0), R0["ell_q"].get(1, 0))
    res = {"amendment": 2, "web": "W1", "order": [f for f, _ in fam_novels], "novel": novel,
           "start": S.start, "final": fin, "stop": stop or "EXHAUSTED"}
    d = os.path.join(args.out, "W1", "A2")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "union.json"), "w", newline="\n") as f:
        f.write(dumps(res))
    log("union: %s" % json.dumps(res, sort_keys=True))
    return res


# ---------------------------------------------------------------- main
def main(args, hdir, command):
    t_all = time.time()
    F, R0, f0res = do_F0(args, hdir, command)
    counts_ok = {"F0": (F["okc"], F["msgs"])}
    want = args.name
    ctl_ok = {}
    if args.cmd in ("all", "control"):
        if args.cmd == "all" or want == "C0":
            ctl_ok["C0"] = do_C0(F, R0, args)
        if args.cmd == "all" or want == "C4":
            ctl_ok["C4"] = do_C4(args, hdir, command)
        if args.cmd == "all" or want == "C5":
            ctl_ok["C5"] = do_C5(args, hdir, command)
    fam_list = []
    if args.cmd == "all":
        fam_list = ["KM", "KMd", "T2R", "T2", "T3s"]
    elif args.cmd == "family":
        fam_list = [want]
    elif want == "C6":
        fam_list = ["T2"]
    fam_res = {}
    fam_novels = []
    c8 = None
    for fam in fam_list:
        if fam == "F0":
            continue
        if fam in ("KM", "KMd"):
            res, extra, S, nm = A.run_km(fam, F, R0, st_factory_for(F), args.out, hdir, command, log)
            if extra:
                c8 = extra
        else:
            res, okc, msgs, S, nm, autn = A.process_family(fam, F, R0, None, args.jobs, args.out, hdir,
                                                             command, log, st_factory_for(F))
            counts_ok[fam] = (okc, msgs)
        fam_res[fam] = res
        if fam != "KMd":
            items = [((i,), dg, v) for (i, v), rec in zip(nm, res["novel"]) for dg in [rec[1]]]
            if fam == "T3s" and res["aut_novel"]:
                perms = A.aut_perms(get_web("W1"), F["tait"])
                vec_of = dict(nm)
                for (ii, g, dg, _, _) in res["aut_novel"]:
                    items.append(((ii, g), dg, A.act(perms[g], vec_of[ii])))
            fam_novels.append((fam, items))
    # C6: automorphisms + symmetry check
    if args.cmd == "all" or want == "C6":
        okp, info = do_C6_perms(F, args)
        res2, okc2, msgs2, S2, nm2, autn2 = A.process_family("T2s0", F, R0, None, args.jobs, args.out,
                                                             hdir, command, log, st_factory_for(F))
        counts_ok["T2s0"] = (okc2, msgs2)
        full = fam_res.get("T2")
        same = full is not None and full["final"]["dimU"] == res2["final"]["dimU"] and \
            full["final"]["ell_m3"] == res2["final"]["ell_m3"]
        info.update({"T2s0_final": res2["final"], "T2_final": full["final"] if full else None,
                     "symmetry_check_same": same})
        ok6 = okp and same
        res6 = {"amendment": 2, "web": "W1", "control": "C6", "pass": ok6}
        res6.update(info)
        d = os.path.join(args.out, "W1", "A2", "ctl-C6")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "result.json"), "w", newline="\n") as f:
            f.write(dumps(res6))
        ctl_ok["C6"] = ok6
        log("C6: %s %s" % ("PASS" if ok6 else "FAIL", json.dumps(res6, sort_keys=True)))
    if args.cmd == "all":
        ctl_ok["C3"] = do_C3_summary(counts_ok, args)
        c1 = all(r["a3_violations"] == 0 for r in fam_res.values())
        c2 = fam_res["T2R"]["novel"] == []
        ctl_ok["C1"] = c1
        ctl_ok["C2"] = c2
        log("C1 (zero A3 violations): %s; C2 (T2R no novel): %s" % (c1, c2))
        if c8 is not None:
            d = os.path.join(args.out, "W1", "A2", "ctl-C8")
            os.makedirs(d, exist_ok=True)
            r8 = {"amendment": 2, "web": "W1", "control": "C8"}
            r8.update(c8)
            with open(os.path.join(d, "result.json"), "w", newline="\n") as f:
                f.write(dumps(r8))
            log("C8: %s" % json.dumps(r8, sort_keys=True))
        do_union(F, R0, fam_novels, args)
        with open(os.path.join(args.out, "W1", "A2", "controls.txt"), "w", newline="\n") as f:
            for k in sorted(ctl_ok):
                f.write("%s %s\n" % (k, "PASS" if ctl_ok[k] else "FAIL"))
        log("controls: %s" % ctl_ok)
    log("total wall %.1fs" % (time.time() - t_all))
