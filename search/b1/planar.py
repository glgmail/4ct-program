"""Triangulations as plantri writes them, and what B1 needs to know about them.

plantri's planar code (plantri-guide.txt, "Output formats") is a header
">>planar_code<<" followed, for each graph, by the number of vertices n (one
byte for n <= 255) and then, for each vertex 1..n in turn, its neighbours in
clockwise order, each a byte, closed by a 0 byte.

A Tri holds one graph with 0-based vertices:

- rot[v]: v's neighbours in clockwise order;
- boundary: None for a triangulation of the sphere; for a triangulation of a
  disc (plantri -P), the outer cycle, listed so that the outer face lies on
  the left of every step b[i] -> b[i+1].

Faces are traced with one rule: arriving at v along u -> v, the face on the
left of that dart continues along v -> w, where w follows u clockwise around
v. The self-checks in run.py confirm the rule on every graph they read: every
face of a sphere triangulation is a triangle, and the face left of plantri's
first dart of a disc has exactly the disc size plantri was asked for.
"""
from __future__ import annotations

HEADER = b">>planar_code<<"


class Tri:
    __slots__ = ("n", "rot", "boundary", "_pos")

    def __init__(self, rot, boundary=None):
        self.n = len(rot)
        self.rot = rot
        self.boundary = boundary
        self._pos = None

    @property
    def is_disc(self):
        return self.boundary is not None

    def pos(self):
        """pos[v][w]: the index of w in rot[v]."""
        if self._pos is None:
            self._pos = [{w: i for i, w in enumerate(r)} for r in self.rot]
        return self._pos

    def next_on_left(self, u, v):
        """The vertex after v on the face to the left of the dart u -> v."""
        r = self.rot[v]
        return r[(self.pos()[v][u] + 1) % len(r)]

    def face_left_of(self, u, v):
        face = [u]
        a, b = u, v
        while b != u:
            face.append(b)
            a, b = b, self.next_on_left(a, b)
            if len(face) > 2 * self.n:
                raise ValueError("face traversal did not close")
        return face

    def edges(self):
        return [(v, w) for v in range(self.n) for w in self.rot[v] if v < w]

    def faces(self):
        """Every face once, each as the vertex list traced on its left."""
        seen = set()
        out = []
        for v in range(self.n):
            for w in self.rot[v]:
                if (v, w) in seen:
                    continue
                f = self.face_left_of(v, w)
                for i in range(len(f)):
                    seen.add((f[i], f[(i + 1) % len(f)]))
                out.append(f)
        return out

    def ascii(self):
        """plantri's ascii code: vertices a, b, c, ...; rotations clockwise."""
        name = lambda v: chr(ord("a") + v) if v < 26 else f"[{v + 1}]"
        return f"{self.n} " + ",".join("".join(name(w) for w in r) for r in self.rot)


def read_planar_code(stream, disc=False):
    """Yield a Tri for each graph in a planar_code byte stream."""
    head = stream.read(len(HEADER))
    if head != HEADER:
        raise ValueError(f"not planar code: header {head!r}")
    while True:
        b = stream.read(1)
        if not b:
            return
        n = b[0]
        if n == 0:
            raise ValueError("graphs with more than 255 vertices are not supported")
        rot = []
        for _ in range(n):
            nb = []
            while True:
                x = stream.read(1)[0]
                if x == 0:
                    break
                nb.append(x - 1)
            rot.append(nb)
        t = Tri(rot)
        if disc:
            # plantri -P: "v-w is an edge and the outer face is on the left
            # when looking from v-w, where v is the first vertex and w is the
            # second vertex."
            t.boundary = t.face_left_of(0, 1)
        yield t


def check_structure(t: Tri, disc_size=None):
    """Raise if t is not what B1 assumes: a triangulation of the sphere, or of
    a disc whose inner faces are all triangles and whose outer face is a
    chordless cycle of the requested size."""
    n = t.n
    for v in range(n):
        if len(set(t.rot[v])) != len(t.rot[v]) or v in t.rot[v]:
            raise ValueError(f"vertex {v}: repeated or self neighbour")
        for w in t.rot[v]:
            if v not in t.pos()[w]:
                raise ValueError(f"{v}-{w} is not symmetric")
    faces = t.faces()
    e = len(t.edges())
    if n - e + len(faces) != 2:
        raise ValueError("Euler characteristic is not 2")
    if not t.is_disc:
        if any(len(f) != 3 for f in faces):
            raise ValueError("a face of a sphere triangulation is not a triangle")
        if e != 3 * n - 6:
            raise ValueError("wrong edge count")
        return
    outer = t.boundary
    k = len(outer)
    if disc_size is not None and k != disc_size:
        raise ValueError(f"boundary has length {k}, plantri was asked for {disc_size}")
    if len(set(outer)) != k:
        raise ValueError("boundary is not a simple cycle")
    inner = [f for f in faces if sorted(f) != sorted(outer) or len(f) != k]
    if len(inner) != len(faces) - 1 or any(len(f) != 3 for f in inner):
        raise ValueError("an inner face is not a triangle")
    on = set(outer)
    for i, v in enumerate(outer):
        for w in t.rot[v]:
            if w in on and w not in (outer[i - 1], outer[(i + 1) % k]):
                raise ValueError("the boundary has a chord")


def with_apex(t: Tri):
    """A disc capped by a new vertex joined to its whole boundary: a sphere
    triangulation in which the new vertex (numbered n) stands for the outer
    face. Used to put discs in canonical form."""
    k = len(t.boundary)
    apex = t.n
    rot = [list(r) for r in t.rot]
    b = t.boundary
    for i, v in enumerate(b):
        prev, nxt = b[i - 1], b[(i + 1) % k]
        r = rot[v]
        j = r.index(prev)
        # the outer face at v is the angle from prev to nxt (clockwise)
        if r[(j + 1) % len(r)] != nxt:
            raise ValueError("outer face is not where expected")
        r.insert(j + 1, apex)
    for order in (list(reversed(b)), list(b)):
        cand = Tri(rot + [order])
        try:
            check_structure(cand)
            return cand
        except ValueError:
            continue
    raise ValueError("could not cap the disc")
