"""
Software preview of a GeckoLib geo model (optionally posed at a time of one animation), for checking generated models
without launching the game. Mirrors GeckoLib's conventions: bedrock X is mirrored, bone/cube rotations apply Z*Y*X with
X and Y negated, keyframe rotations/positions follow the same rules.

    python tools/preview_geo.py <geo.json> <texture.png> <out.png> [animation.json anim_name time] [--yaw 30 --pitch 20 --size 512]
"""
import argparse
import json
import math

from PIL import Image, ImageDraw


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def translate(x, y, z):
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]


def scale(x, y, z):
    return [[x, 0, 0, 0], [0, y, 0, 0], [0, 0, z, 0], [0, 0, 0, 1]]


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def apply(m, v):
    return [m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] + m[i][3] for i in range(3)]


def rot_matrix(deg):
    """Bedrock rotation -> GeckoLib matrix (x,y negated, applied Z*Y*X)."""
    x, y, z = [math.radians(d) for d in deg]
    return mat_mul(rz(z), mat_mul(ry(-y), rx(-x)))


def molang(v, t):
    """Evaluates the Molang subset used in keyframes (math.sin/cos in degrees, query.anim_time)."""
    if isinstance(v, (int, float)):
        return float(v)
    expr = str(v).lower().replace("query.anim_time", "(%f)" % t).replace("q.anim_time", "(%f)" % t)
    expr = expr.replace("math.sin", "_sin").replace("math.cos", "_cos").replace("math.abs", "abs").replace("math.clamp", "_clamp")
    try:
        return float(eval(expr, {"_sin": lambda d: math.sin(math.radians(d)), "_cos": lambda d: math.cos(math.radians(d)),
                                 "abs": abs, "_clamp": lambda x, a, b: max(a, min(b, x))}))
    except Exception:
        return 0.0


def vec(v, t):
    if isinstance(v, dict):
        v = v.get("vector", v.get("post", v.get("pre")))
        if isinstance(v, dict):
            v = v.get("vector")
    if not isinstance(v, list):
        v = [v, v, v]
    return [molang(c, t) for c in v]


def sample(track, t):
    """Linear sampling of a keyframe track {time: {"vector": [...]}} (easing ignored except step = hold)."""
    if track is None:
        return None
    if isinstance(track, (list, int, float, str)):
        return vec(track, t)
    if "vector" in track or "post" in track:
        return vec(track, t)
    keys = sorted(track.items(), key=lambda kv: float(kv[0]))
    times = [float(k) for k, _ in keys]
    vals = [vec(v, t) for _, v in keys]
    if t <= times[0]:
        return vals[0]
    for i in range(1, len(times)):
        if t <= times[i]:
            f = (t - times[i - 1]) / max(1e-6, times[i] - times[i - 1])
            if isinstance(keys[i][1], dict) and keys[i][1].get("easing") == "step":
                steps = (keys[i][1].get("easingArgs") or [2])[0]
                f = math.floor(f * steps) / steps
            return [a + (b - a) * f for a, b in zip(vals[i - 1], vals[i])]
    return vals[-1]


def render(geo_path, tex_path, out_path, anim_path=None, anim_name=None, time=0.0, yaw=30.0, pitch=20.0, size=512, bg=(40, 44, 52)):
    geo = json.load(open(geo_path))["minecraft:geometry"][0]
    tex = Image.open(tex_path).convert("RGBA")
    tw, th = geo["description"]["texture_width"], geo["description"]["texture_height"]
    sx, sy = tex.width / tw, tex.height / th
    pose = {}
    if anim_path:
        anim = json.load(open(anim_path))["animations"][anim_name]
        for bone, chans in anim.get("bones", {}).items():
            pose[bone] = {k: sample(v, time) for k, v in chans.items()}
    bones = {b["name"]: b for b in geo["bones"]}
    world = {}

    def bone_matrix(name):
        if name in world:
            return world[name]
        b = bones[name]
        px, py, pz = b["pivot"]
        pv = [-px, py, pz]
        m = translate(*pv)
        m = mat_mul(m, rot_matrix(b.get("rotation", [0, 0, 0])))
        p = pose.get(name, {})
        if p.get("position"):
            ppos = p["position"]
            m = mat_mul(translate(-ppos[0], ppos[1], ppos[2]), m)
        if p.get("rotation"):
            m = mat_mul(m, rot_matrix(p["rotation"]))
        if p.get("scale"):
            s = p["scale"]
            m = mat_mul(m, scale(*s))
        m = mat_mul(m, translate(*[-c for c in pv]))
        parent = b.get("parent")
        if parent:
            m = mat_mul(bone_matrix(parent), m)
        world[name] = m
        return m

    cam = mat_mul(rx(math.radians(pitch)), ry(math.radians(yaw)))
    quads = []
    for b in geo["bones"]:
        m = bone_matrix(b["name"])
        for cube in b.get("cubes", []):
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
            # corners in GeckoLib space (x already mirrored). Faces use bedrock naming.
            faces = {
                "north": [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)],
                "south": [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
                "east": [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
                "west": [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
                "up": [(x1, y1, z1), (x0, y1, z1), (x0, y1, z0), (x1, y1, z0)],
                "down": [(x1, y0, z0), (x0, y0, z0), (x0, y0, z1), (x1, y0, z1)],
            }
            uvmap = cube.get("uv", {})
            if isinstance(uvmap, list):
                bu, bv = uvmap
                fw, fh, fd = [math.floor(c) for c in (w, h, d)]
                uvmap = {"east": {"uv": [bu, bv + fd], "uv_size": [fd, fh]}, "north": {"uv": [bu + fd, bv + fd], "uv_size": [fw, fh]},
                         "west": {"uv": [bu + fd + fw, bv + fd], "uv_size": [fd, fh]}, "south": {"uv": [bu + 2 * fd + fw, bv + fd], "uv_size": [fw, fh]},
                         "up": {"uv": [bu + fd, bv], "uv_size": [fw, fd]}, "down": {"uv": [bu + fd + fw, bv + fd], "uv_size": [fw, -fd]}}
            for face, uvd in uvmap.items():
                u, v = uvd["uv"]
                uw, vh = uvd["uv_size"]
                corners = [apply(cam, apply(cm, c)) for c in faces[face]]
                # subdivide into texels
                nu, nv = max(1, int(abs(math.ceil(uw)))), max(1, int(abs(math.ceil(vh))))
                for j in range(nv):
                    for i in range(nu):
                        tu = u + (i + 0.5) * (uw / nu)
                        tv = v + (j + 0.5) * (vh / nv)
                        px = tex.getpixel((min(tex.width - 1, max(0, int(tu * sx))), min(tex.height - 1, max(0, int(tv * sy)))))
                        if px[3] < 20:
                            continue

                        def lerp(a, bb, f):
                            return [a[k] + (bb[k] - a[k]) * f for k in range(3)]

                        fu0, fu1, fv0, fv1 = i / nu, (i + 1) / nu, j / nv, (j + 1) / nv
                        top0, top1 = lerp(corners[0], corners[1], fu0), lerp(corners[0], corners[1], fu1)
                        bot0, bot1 = lerp(corners[3], corners[2], fu0), lerp(corners[3], corners[2], fu1)
                        poly = [lerp(top0, bot0, fv0), lerp(top1, bot1, fv0), lerp(top1, bot1, fv1), lerp(top0, bot0, fv1)]
                        depth = sum(p[2] for p in poly) / 4
                        shade = {"up": 1.0, "down": 0.55, "north": 0.85, "south": 0.75, "east": 0.7, "west": 0.8}[face]
                        quads.append((depth, poly, tuple(int(c * shade) for c in px[:3])))
    if not quads:
        raise SystemExit("nothing to draw")
    xs = [p[0] for q in quads for p in q[1]]
    ys = [p[1] for q in quads for p in q[1]]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1
    k = size * 0.9 / span
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    img = Image.new("RGB", (size, size), bg)
    dr = ImageDraw.Draw(img)
    quads.sort(key=lambda q: -q[0])
    for depth, poly, col in quads:
        pts = [(size / 2 - (p[0] - cx) * k, size / 2 - (p[1] - cy) * k) for p in poly]
        dr.polygon(pts, fill=col)
    img.save(out_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("geo")
    ap.add_argument("tex")
    ap.add_argument("out")
    ap.add_argument("anim", nargs="?")
    ap.add_argument("name", nargs="?")
    ap.add_argument("time", nargs="?", type=float, default=0.0)
    ap.add_argument("--yaw", type=float, default=30)
    ap.add_argument("--pitch", type=float, default=20)
    ap.add_argument("--size", type=int, default=512)
    a = ap.parse_args()
    render(a.geo, a.tex, a.out, a.anim, a.name, a.time, a.yaw, a.pitch, a.size)
