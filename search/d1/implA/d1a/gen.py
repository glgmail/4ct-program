"""Half-foam generation (SPEC Sec. 6 with Amendment 1): GEN, the four moves,
the three modes.

GEN returns a list of (foam, deg, chain) with foam None when build=False
(count-only mode, used to check the N tables of SPEC 6.4 cheaply), or None
for FAIL under STRICT semantics.

Outer-face tracking (B19 mode) follows Amendment 1, A4: a *set* of marker
darts, one per connected component; the faces containing a marker dart are
ineligible.  A marker whose face loses all its vertices while its component
keeps vertices is a FAIL of that branch.
"""

from . import records as R
from .foam import EMPTY, compose
from .web import vert

FAIL = object()

EVENT_KEYS = (
    "degenerate_square_merges",       # A3: C4 joins producing the same K'-edge
    "extra_circles",                  # A3: circles created by joins other than a theta bigon
    "theta_bigon_circles",            # informational: theta component -> circle (A5 path)
    "bridge_fails",                   # A3
    "marker_losses",                  # A3/A4 (each is a FAIL of its branch)
    "component_splits",               # A3: K' has more vertex-components than K
    "split_components_without_outer_dart",   # a split-off component no outer dart reached
    "components_vanished_with_marker",       # a marked component lost all its vertices
    "boozer_distinctness_violations_bigon",  # A3 list: configurations B19's code aborts on
    "boozer_distinctness_violations_triangle",
    "boozer_distinctness_violations_square",
    "no_eligible_face_fails",         # informational (ordinary partial-semantics failure)
)


def new_events():
    return {k: 0 for k in EVENT_KEYS}


def carry(op, markers, ev):
    """Marker set of K' (tuple of darts), None (unmarked mode) or FAIL."""
    K, Kp = op.K, op.Kp
    nK = K.vertex_components()[1] if K.V else 0
    compp, nKp = Kp.vertex_components() if Kp.V else ([], 0)
    split = nKp > nK
    if split:
        ev["component_splits"] += 1
    if markers is None:
        return None
    if op.keep_marker:
        return markers
    D, dmap = op.D, op.dmap
    compK = K.vertex_components()[0]
    faces = K.faces()
    fo = K.face_of()
    new = {}
    for m in markers:
        cm = compK[vert(m)]
        if all(v in D for v in range(K.V) if compK[v] == cm):
            ev["components_vanished_with_marker"] += 1
            continue
        cands = [dmap[d] for d in faces[fo[m]] if vert(d) not in D]
        if not cands:
            ev["marker_losses"] += 1
            return FAIL
        for d2 in cands:
            c2 = compp[vert(d2)]
            if c2 not in new:
                new[c2] = d2
    if split:
        for c in range(nKp):
            if c not in new:
                ev["split_components_without_outer_dart"] += 1
    return tuple(sorted(new.values()))


def _record_events(op, ev):
    info = op.info
    if op.kind == "bigon":
        if info["theta"]:
            ev["theta_bigon_circles"] += info["circles"]
        else:
            ev["extra_circles"] += info["circles"]
            if not info["boozer_ok"]:
                ev["boozer_distinctness_violations_bigon"] += 1
    elif op.kind == "triangle":
        ev["extra_circles"] += info["circles"]
        if not info["boozer_ok"]:
            ev["boozer_distinctness_violations_triangle"] += 1
    elif op.kind == "square":
        ev["extra_circles"] += info["circles"]
        if info["degenerate_merge"]:
            ev["degenerate_square_merges"] += 1
        if not info["boozer_ok"]:
            ev["boozer_distinctness_violations_square"] += 1
    elif op.kind == "zip":
        ev["extra_circles"] += info["circles"]


def GEN(K, markers, strict, build, ev):
    fail = None if strict else []
    if K.V == 0 and K.m == 0:
        return [(EMPTY if build else None, 0, ())]
    if K.m > 0:
        op = R.op_disk(K)
        sub = GEN(op.Kp, carry(op, markers, ev), strict, build, ev)
        if sub is None:
            return None
        out = []
        for lab in ("C1", "C1d", "C1dd"):
            rec = op.make(lab) if (build and sub) else None
            dg = R.DEG[lab]
            for (h, d, ch) in sub:
                out.append((compose(rec, h) if build else None, d + dg, (lab,) + ch))
        return out
    if K.has_bridge():
        ev["bridge_fails"] += 1
        return fail
    faces = K.faces()
    excl = set()
    if markers:
        fo = K.face_of()
        excl = {fo[m] for m in markers}
    face = None
    for L in (2, 3, 4):
        for fid, f in enumerate(faces):
            if len(f) == L and fid not in excl:
                face = f
                break
        if face is not None:
            break
    if face is None:
        ev["no_eligible_face_fails"] += 1
        return fail
    L = len(face)
    if L == 2:
        branches = [(R.op_bigon(K, face), ("C2", "C2d"))]
    elif L == 3:
        branches = [(R.op_triangle(K, face), ("C3",))]
    else:
        branches = [(R.op_square(K, face, "a"), ("C4a",)),
                    (R.op_square(K, face, "b"), ("C4b",))]
    subs = []
    for op, labs in branches:
        _record_events(op, ev)
        mk = carry(op, markers, ev)
        if mk is FAIL:
            sub = fail
        else:
            sub = GEN(op.Kp, mk, strict, build, ev)
        if sub is None:
            return None
        subs.append((op, labs, sub))
    out = []
    for op, labs, sub in subs:
        for lab in labs:
            rec = op.make(lab) if (build and sub) else None
            dg = R.DEG[lab]
            for (h, d, ch) in sub:
                out.append((compose(rec, h) if build else None, d + dg, (lab,) + ch))
    return out


MODES = {
    # mode: (exclude outer face for Unzip/Saddle and carry markers, strict)
    "B19": (True, False),
    "STRICT-ALL": (False, True),
    "PARTIAL-ALL": (False, False),
}


def move_sites(K, outer_min_dart, mode):
    """Site list, in order: SPEC 6.2 for the ALL modes; Amendment 1 (A1) for
    B19 mode (Unzip, Zip, Saddle, IH; face pairs with j >= i+2, (0, L-1)
    skipped)."""
    excl_outer, strict = MODES[mode]
    edges = K.edge_ids()
    faces = K.faces()
    elig = [f for f in faces if not (excl_outer and f[0] == outer_min_dart)]

    def pairs(f):
        L = len(f)
        out = []
        for i in range(L):
            for j in range(i + 1, L):
                if mode == "B19" and (j < i + 2 or (i == 0 and j == L - 1)):
                    continue
                out.append((i, j))
        return out
    zips = [("zip", e) for e in edges]
    unz = [("unzip", f[0], i, j) for f in elig for (i, j) in pairs(f)]
    sad = [("saddle", f[0], i, j) for f in elig for (i, j) in pairs(f)]
    ihs = [("ih", e) for e in edges]
    if mode == "B19":
        return unz + zips + sad + ihs
    return zips + unz + sad + ihs


def site_op(K, site):
    faces = {f[0]: f for f in K.faces()}
    if site[0] == "zip":
        return R.op_zip(K, site[1])
    if site[0] == "ih":
        return R.op_ih(K, site[1])
    f = faces[site[1]]
    if site[0] == "unzip":
        return R.op_unzip(K, f, site[2], site[3])
    return R.op_saddle(K, f, site[2], site[3])


def generate(K, outer_min_dart, mode, build, callback, ev=None):
    """Iterate over the move sites; for each generated half-foam M o h call
    callback(site, foam_or_None, deg, chain).  Returns per-move counts."""
    if ev is None:
        ev = new_events()
    excl_outer, strict = MODES[mode]
    markers = (outer_min_dart,) if excl_outer else None
    counts = {"zip": 0, "unzip": 0, "saddle": 0, "ih": 0}
    for site in move_sites(K, outer_min_dart, mode):
        op = site_op(K, site)
        _record_events(op, ev)
        mk = carry(op, markers, ev)
        if mk is FAIL:
            continue
        sub = GEN(op.Kp, mk, strict, build, ev)
        if not sub:
            continue
        rec = op.make(site[0]) if build else None
        dg = R.DEG[site[0]]
        for (h, d, ch) in sub:
            callback(site, compose(rec, h) if build else None, d + dg, ch)
        counts[site[0]] += len(sub)
    return counts
