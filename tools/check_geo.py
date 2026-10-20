"""
Static checks for generated GeckoLib models (rest pose):

* z-fighting: two visible faces from different cubes lying in the same plane, facing the same way and overlapping
  (the flickering "textures stacked on each other" artefact). Faces that are fully transparent in the texture are
  ignored.
* faces whose UV rectangle is completely transparent while the cube is not a membrane/plane (invisible faces).

    python tools/check_geo.py <geo.json> <texture.png> [--min-area 0.05]
"""
import argparse
import json
import math
import sys

from PIL import Image

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from preview_geo import apply, mat_mul, rot_matrix, translate  # noqa: E402


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def norm(a):
    length = math.sqrt(dot(a, a)) or 1.0
    return [c / length for c in a]


def clip(subject, clipper):
    """Sutherland-Hodgman: convex polygon intersection in 2D."""
    def inside(p, a, b):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9

    def inter(p, q, a, b):
        a1, b1 = q[1] - p[1], p[0] - q[0]
        c1 = a1 * p[0] + b1 * p[1]
        a2, b2 = b[1] - a[1], a[0] - b[0]
        c2 = a2 * a[0] + b2 * a[1]
        det = a1 * b2 - a2 * b1
        if abs(det) < 1e-12:
            return q
        return ((b2 * c1 - b1 * c2) / det, (a1 * c2 - a2 * c1) / det)

    out = subject
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp:
            break
        s = inp[-1]
        for e in inp:
            if inside(e, a, b):
                if not inside(s, a, b):
                    out.append(inter(s, e, a, b))
                out.append(e)
            elif inside(s, a, b):
                out.append(inter(s, e, a, b))
            s = e
    return out


def area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))) / 2


def ccw(poly):
    s = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return poly if s > 0 else list(reversed(poly))


def faces_of(geo, tex):
    tw, th = geo["description"]["texture_width"], geo["description"]["texture_height"]
    sx, sy = tex.width / tw, tex.height / th
    bones = {b["name"]: b for b in geo["bones"]}
    world = {}

    def bone_matrix(name):
        if name in world:
            return world[name]
        b = bones[name]
        px, py, pz = b["pivot"]
        pv = [-px, py, pz]
        m = mat_mul(translate(*pv), mat_mul(rot_matrix(b.get("rotation", [0, 0, 0])), translate(*[-c for c in pv])))
        if b.get("parent"):
            m = mat_mul(bone_matrix(b["parent"]), m)
        world[name] = m
        return m

    out = []
    for b in geo["bones"]:
        m = bone_matrix(b["name"])
        for ci, cube in enumerate(b.get("cubes", [])):
            ox, oy, oz = cube["origin"]
            w, h, d = cube["size"]
            inf = cube.get("inflate", 0)
            x0, x1 = -(ox + w) - inf, -ox + inf
            y0, y1 = oy - inf, oy + h + inf
            z0, z1 = oz - inf, oz + d + inf
            cm = m
            if cube.get("rotation"):
                cp = cube.get("pivot", [ox + w / 2, oy + h / 2, oz + d / 2])
                cpv = [-cp[0], cp[1], cp[2]]
                cm = mat_mul(m, mat_mul(translate(*cpv), mat_mul(rot_matrix(cube["rotation"]), translate(*[-c for c in cpv]))))
            corners = {
                "north": [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)],
                "south": [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
                "east": [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
                "west": [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
                "up": [(x1, y1, z1), (x0, y1, z1), (x0, y1, z0), (x1, y1, z0)],
                "down": [(x1, y0, z0), (x0, y0, z0), (x0, y0, z1), (x1, y0, z1)],
            }
            normals = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (-1, 0, 0), "west": (1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
            uvmap = cube.get("uv", {})
            if isinstance(uvmap, list):
                continue
            for face, uvd in uvmap.items():
                u, v = uvd["uv"]
                uw, vh = uvd["uv_size"]
                if abs(uw) < 1e-6 or abs(vh) < 1e-6:
                    continue
                # opaque fraction of the face's texture rectangle
                ua, ub = sorted((u * sx, (u + uw) * sx))
                va, vb = sorted((v * sy, (v + vh) * sy))
                opaque = total = 0
                for ty in range(int(va), max(int(va) + 1, int(math.ceil(vb)))):
                    for tx in range(int(ua), max(int(ua) + 1, int(math.ceil(ub)))):
                        if 0 <= tx < tex.width and 0 <= ty < tex.height:
                            total += 1
                            opaque += tex.getpixel((tx, ty))[3] > 20
                pts = [apply(cm, c) for c in corners[face]]
                if area3(pts) < 1e-6:
                    continue
                n = norm(sub(apply(cm, normals[face]), apply(cm, (0, 0, 0))))
                out.append({"bone": b["name"], "cube": ci, "face": face, "pts": pts, "n": n, "d": dot(n, pts[0]),
                            "opaque": opaque / max(1, total)})
    return out


def area3(pts):
    c = cross(sub(pts[1], pts[0]), sub(pts[3], pts[0]))
    return math.sqrt(dot(c, c))


def check(geo_path, tex_path, min_area=0.05, quiet=False):
    geo = json.load(open(geo_path))["minecraft:geometry"][0]
    tex = Image.open(tex_path).convert("RGBA")
    problems = _problems(geo, tex, min_area)
    if not quiet:
        for a, fi, fj in problems[:60]:
            print("z-fight %.2f px^2: %s#%d.%s  <->  %s#%d.%s" % (a, fi["bone"], fi["cube"], fi["face"], fj["bone"], fj["cube"], fj["face"]))
        print("%s: %d z-fighting pairs" % (geo_path, len(problems)))
    return problems


def fix_geo(geo_json, tex, eps=0.06, rounds=12):
    """Removes z-fighting in place: for every coplanar overlapping pair the smaller face is pulled inward by eps (its
    cube shrinks by eps on that side, in the cube's own frame), so exactly one of the two faces wins. Returns the
    number of faces moved."""
    geo = geo_json["minecraft:geometry"][0]
    side = {"north": (2, True), "south": (2, False), "west": (0, True), "east": (0, False), "down": (1, True), "up": (1, False)}
    moved = 0
    for _ in range(rounds):
        problems = _problems(geo, tex)
        if not problems:
            break
        done = set()
        for a, fi, fj in problems:
            # move the face with the smaller area (keeps big panels intact)
            f = fi if area3(fi["pts"]) <= area3(fj["pts"]) else fj
            key = (f["bone"], f["cube"], f["face"])
            if key in done:
                continue
            done.add(key)
            cube = [b for b in geo["bones"] if b["name"] == f["bone"]][0]["cubes"][f["cube"]]
            if isinstance(cube.get("uv"), list):
                continue
            axis, at_origin = side[f["face"]]
            if cube.get("rotation") and "pivot" not in cube:
                cube["pivot"] = [cube["origin"][i] + cube["size"][i] / 2 for i in range(3)]
            e = min(eps, cube["size"][axis] * 0.25)
            if e <= 0:
                continue
            if at_origin:
                cube["origin"][axis] = round(cube["origin"][axis] + e, 4)
            cube["size"][axis] = round(cube["size"][axis] - e, 4)
            moved += 1
    return moved


def _problems(geo, tex, min_area=0.05):
    faces = [f for f in faces_of(geo, tex) if f["opaque"] > 0.02]
    buckets = {}
    for i, f in enumerate(faces):
        key = (round(f["n"][0], 2), round(f["n"][1], 2), round(f["n"][2], 2), round(f["d"] * 20))
        buckets.setdefault(key, []).append(i)
    problems = []
    for key, idx in buckets.items():
        cand = []
        for dd in (-1, 0, 1):
            cand += buckets.get(key[:3] + (key[3] + dd,), [])
        for i in idx:
            fi = faces[i]
            for j in cand:
                if j <= i:
                    continue
                fj = faces[j]
                if fi["bone"] == fj["bone"] and fi["cube"] == fj["cube"]:
                    continue
                if dot(fi["n"], fj["n"]) < 0.9999 or abs(fi["d"] - fj["d"]) > 0.02:
                    continue
                n = fi["n"]
                ax = [1, 0, 0] if abs(n[0]) < 0.9 else [0, 1, 0]
                e1 = norm(cross(n, ax))
                e2 = cross(n, e1)
                p1 = ccw([(dot(p, e1), dot(p, e2)) for p in fi["pts"]])
                p2 = ccw([(dot(p, e1), dot(p, e2)) for p in fj["pts"]])
                inter = clip(p1, p2)
                if len(inter) >= 3 and area(inter) > min_area:
                    problems.append((area(inter), fi, fj))
    problems.sort(key=lambda p: -p[0])
    return problems


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("geo")
    ap.add_argument("tex")
    ap.add_argument("--min-area", type=float, default=0.05)
    a = ap.parse_args()
    sys.exit(1 if check(a.geo, a.tex, a.min_area) else 0)
