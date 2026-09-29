"""Move sites at a target web (SPEC 6.2) and the generated list S(K) in Mode T."""

from core import (Web, tait_colourings, rec_zip, rec_ih, rec_unzip, rec_saddle,
                  update_markers, MarkerLost, gen_top, gen_empty, gen_rows_hex,
                  GenStats, count_event, n_components)

MODES = {
    # mode: (strict semantics, use outer-face marker)
    "B19": (False, True),
    "STRICT-ALL": (True, False),
    "PARTIAL-ALL": (False, False),
}


def enumerate_sites(K, mode, outer_dart):
    """Sites in SPEC 6.2 order (STRICT-ALL, PARTIAL-ALL), or in Amendment 1
    A1 order for B19 mode: Unzip, Zip, Saddle, IH blocks; faces in the stored
    order (increasing min dart), edges in increasing edge id; face pairs
    (i, j) with j >= i + 2, skipping (0, L-1) (0-based), lexicographic."""
    strict, marked = MODES[mode]
    excl = K.face_of[outer_dart] if (marked and outer_dart is not None) else -1

    def face_sites(kind):
        out = []
        for fi, f in enumerate(K.faces):
            if fi == excl:
                continue
            L = len(f)
            for i in range(L):
                for j in range(i + 1, L):
                    if mode == "B19" and (j < i + 2 or (i == 0 and j == L - 1)):
                        continue
                    out.append((kind, f[0], i, j))
        return out
    zips = [("zip", e) for e in K.edge_ids]
    ihs = [("ih", e) for e in K.edge_ids]
    if mode == "B19":
        return face_sites("unzip") + zips + face_sites("saddle") + ihs
    return zips + face_sites("unzip") + face_sites("saddle") + ihs


def move_record(K, site):
    kind = site[0]
    if kind == "zip":
        K2, rec, dmap, D, _ = rec_zip(K, site[1])
        return K2, rec, dmap, D
    if kind == "ih":
        K2, rec, dmap, D = rec_ih(K, site[1])
        return K2, rec, dmap, D
    f = K.faces[K.face_of[site[1]]]
    assert f[0] == site[1]
    if kind == "unzip":
        K2, rec, dmap = rec_unzip(K, f, site[2], site[3])
    else:
        K2, rec, dmap = rec_saddle(K, f, site[2], site[3])
    return K2, rec, dmap, []


def run_site(K, S, site, mode, outer_dart, check=False):
    """Returns (list of (chain, deg, hexrow), gen nodes, A3 event counts)."""
    strict, marked = MODES[mode]
    markers = (outer_dart,) if marked else None
    K2, rec, dmap, D = move_record(K, site)
    Sp, tcols = rec.transfer(S)
    st = GenStats()
    if K2.m > K.m:
        count_event(st.ev, "extra_circle_other", K2.m - K.m)
    if n_components(K2) > n_components(K):
        count_event(st.ev, "component_split")
    try:
        mk2 = update_markers(K, K2, markers, D, dmap, st.ev)
        G = gen_top(K2, Sp, strict, mk2, st, check)
    except MarkerLost:
        G = gen_empty(len(Sp))
    # a_{M o h} = a_h . T_M
    cols = []
    gc = G.cols
    for entries in tcols:
        lo = hi = 0
        for k, code in entries:
            a, b = gc[k]
            if code == 1:
                lo ^= a
                hi ^= b
            elif code == 2:
                lo ^= b
                hi ^= a ^ b
            else:
                lo ^= a ^ b
                hi ^= a
        cols.append((lo, hi))

    class _H:
        pass
    H = _H()
    H.n, H.cols = G.n, cols
    rows = gen_rows_hex(H)
    out = [(list(G.chains[i]), G.degs[i] + rec.deg, rows[i]) for i in range(G.n)]
    return out, st.nodes, st.ev


# ------------------------------------------------------------- worker plumbing
_W = {}


def _init(alpha, m, mode, outer_dart, check):
    K = Web(alpha, m)
    _W["K"] = K
    _W["S"] = tait_colourings(K)
    _W["mode"] = mode
    _W["outer"] = outer_dart
    _W["check"] = check
    _W["sites"] = enumerate_sites(K, mode, outer_dart)


def _work(idx):
    site = _W["sites"][idx]
    out, nodes, ev = run_site(_W["K"], _W["S"], site, _W["mode"], _W["outer"], _W["check"])
    return idx, out, nodes, ev


def generate(K, mode, outer_dart, jobs=1, check=False, progress=None):
    """Returns (sites, per-site outputs) in site order."""
    sites = enumerate_sites(K, mode, outer_dart)
    results = [None] * len(sites)
    nodes = 0
    events = {}

    def addev(ev):
        for k, v in ev.items():
            events[k] = events.get(k, 0) + v
    if jobs <= 1:
        _init(K.alpha, K.m, mode, outer_dart, check)
        for idx in range(len(sites)):
            _, out, nd, ev = _work(idx)
            results[idx] = out
            nodes += nd
            addev(ev)
            if progress:
                progress(idx + 1, len(sites))
    else:
        import multiprocessing as mp
        ctx = mp.get_context("fork") if hasattr(mp, "get_context") else mp
        with ctx.Pool(jobs, initializer=_init,
                      initargs=(K.alpha, K.m, mode, outer_dart, check)) as pool:
            done = 0
            for idx, out, nd, ev in pool.imap_unordered(_work, range(len(sites)), chunksize=1):
                results[idx] = out
                nodes += nd
                addev(ev)
                done += 1
                if progress:
                    progress(done, len(sites))
    return sites, results, nodes, events
