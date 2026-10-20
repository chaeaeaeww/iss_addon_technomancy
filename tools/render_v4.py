"""
Preview renderer for GeckoLib models (z-buffered, textured, lit, emissive glowmask, ground plane with a drop shadow),
used to review the Tech Dragon v4 model and its animations without launching the game.

    python tools/render_v4.py <geo.json> <texture.png> <out.png|gif> [--glow g.png] [--anim a.json --name n]
                              [--time t | --gif] [--yaw 35 --pitch 18 --size 640]

GIFs keep one fixed camera for the whole animation (fitted to every frame) so motion reads correctly.
"""
import argparse
import json
import math

import numpy as np
from PIL import Image

import rig_v4

FACES = ("north", "south", "east", "west", "up", "down")


def face_corners(o, s, face, inf=0.0):
    """TL, TR, BL corners of a face in rest cube space (Bedrock naming/UV orientation, see surf.py)."""
    x0, y0, z0 = o[0] - inf, o[1] - inf, o[2] - inf
    x1, y1, z1 = o[0] + s[0] + inf, o[1] + s[1] + inf, o[2] + s[2] + inf
    return {
        "north": ((x0, y1, z0), (x1, y1, z0), (x0, y0, z0)),
        "south": ((x1, y1, z1), (x0, y1, z1), (x1, y0, z1)),
        # GeckoLib (checked with GeckoDump, 1.9): "east" is drawn on the min-x side, "west" on the max-x side
        "east": ((x0, y1, z1), (x0, y1, z0), (x0, y0, z1)),
        "west": ((x1, y1, z0), (x1, y1, z1), (x1, y0, z0)),
        "up": ((x0, y1, z1), (x1, y1, z1), (x0, y1, z0)),
        "down": ((x0, y0, z0), (x1, y0, z0), (x0, y0, z1)),
    }[face]


def collect_faces(skel, geo, pose):
    """Posed faces: list of (TL, TR, BL world points, (u, v, uw, vh))."""
    world = skel.world(pose)
    out = []
    for b in geo["bones"]:
        m = world[b["name"]]
        for c in b.get("cubes", []):
            cm = m @ rig_v4.cube_matrix(c)
            uvmap = c.get("uv", {})
            if isinstance(uvmap, list):
                bu, bv = uvmap
                fw, fh, fd = [math.floor(x) for x in c["size"]]
                uvmap = {"east": {"uv": [bu, bv + fd], "uv_size": [fd, fh]}, "north": {"uv": [bu + fd, bv + fd], "uv_size": [fw, fh]},
                         "west": {"uv": [bu + fd + fw, bv + fd], "uv_size": [fd, fh]}, "south": {"uv": [bu + 2 * fd + fw, bv + fd], "uv_size": [fw, fh]},
                         "up": {"uv": [bu + fd, bv], "uv_size": [fw, fd]}, "down": {"uv": [bu + fd + fw, bv + fd], "uv_size": [fw, -fd]}}
            for face, uvd in uvmap.items():
                pts = face_corners(c["origin"], c["size"], face, c.get("inflate", 0.0))
                w = [(cm @ np.array([p[0], p[1], p[2], 1.0]))[:3] for p in pts]
                u, v = uvd["uv"]
                uw, vh = uvd["uv_size"]
                out.append((w[0], w[1], w[2], (u, v, uw, vh)))
    return out


def view_matrix(yaw, pitch):
    return rig_v4.rx(math.radians(pitch)) @ rig_v4.ry(math.radians(yaw))


class Raster:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.z = np.full((h, w), -1e9)
        self.col = np.zeros((h, w, 3))
        self.mask = np.zeros((h, w), dtype=bool)

    def face(self, a, b, c, shade_fn, sample_fn):
        """a, b, c: screen-space TL, TR, BL (x, y, depth). sample_fn(fa, fb) -> (rgb, alpha_ok)."""
        e1 = b[:2] - a[:2]
        e2 = c[:2] - a[:2]
        det = e1[0] * e2[1] - e1[1] * e2[0]
        if abs(det) < 1e-6:
            return
        d = b + c - a
        xs = [a[0], b[0], c[0], d[0]]
        ys = [a[1], b[1], c[1], d[1]]
        x0, x1 = max(0, int(math.floor(min(xs)))), min(self.w - 1, int(math.ceil(max(xs))))
        y0, y1 = max(0, int(math.floor(min(ys)))), min(self.h - 1, int(math.ceil(max(ys))))
        if x0 > x1 or y0 > y1:
            return
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        px, py = gx - a[0], gy - a[1]
        fa = (px * e2[1] - py * e2[0]) / det
        fb = (e1[0] * py - e1[1] * px) / det
        inside = (fa >= 0) & (fa <= 1) & (fb >= 0) & (fb <= 1)
        if not inside.any():
            return
        depth = a[2] + fa * (b[2] - a[2]) + fb * (c[2] - a[2])
        zs = self.z[y0:y1 + 1, x0:x1 + 1]
        ok = inside & (depth > zs)
        if not ok.any():
            return
        rgb, alpha = sample_fn(fa, fb)
        ok &= alpha
        if not ok.any():
            return
        zs[ok] = depth[ok]
        cs = self.col[y0:y1 + 1, x0:x1 + 1]
        cs[ok] = shade_fn(rgb[ok])
        self.mask[y0:y1 + 1, x0:x1 + 1] |= ok


class Model:
    def __init__(self, geo_path, tex_path, glow_path=None):
        geo_json = json.load(open(geo_path))
        self.skel, self.geo = rig_v4.load_geo(geo_json)
        self.tex = np.asarray(Image.open(tex_path).convert("RGBA")).astype(float)
        self.glow = np.asarray(Image.open(glow_path).convert("RGBA")).astype(float) if glow_path else None
        d = self.geo["description"]
        self.sx = self.tex.shape[1] / d["texture_width"]
        self.sy = self.tex.shape[0] / d["texture_height"]


LIGHT1 = np.array([0.45, 0.8, -0.4])
LIGHT1 /= np.linalg.norm(LIGHT1)
LIGHT2 = np.array([-0.5, 0.3, 0.6])
LIGHT2 /= np.linalg.norm(LIGHT2)


def render_pose(model, pose, yaw=35, pitch=18, size=640, frame=None, bg_top=(58, 66, 84), bg_bottom=(24, 26, 34), ss=2):
    """frame: (cx, cy, span) in view space to keep the camera fixed; computed from this pose if None."""
    faces = collect_faces(model.skel, model.geo, pose)
    V = view_matrix(yaw, pitch)
    if frame is None:
        frame = fit_frame([faces], V)
    cx, cy, span = frame
    W = size * ss
    k = W * 0.92 / span
    tex, glow = model.tex, model.glow
    th, tw = tex.shape[:2]

    def to_screen(p):
        q = V @ p
        return np.array([W / 2 + (q[0] - cx) * k, W / 2 - (q[1] - cy) * k, q[2]])

    R = Raster(W, W)
    # ground plane (checker, 1 block squares) with the model's drop shadow
    shadow = shadow_map(model, faces)
    gy = 0.0
    ext = span * 0.75
    gx0, gz0 = -ext, -ext
    corners = [np.array([gx0, gy, gz0]), np.array([gx0 + 2 * ext, gy, gz0]), np.array([gx0, gy, gz0 + 2 * ext])]
    sa, sb, sc = [to_screen(p) for p in corners]
    # push the ground slightly back so feet resting on it win the depth test
    sa[2] -= 0.05
    sb[2] -= 0.05
    sc[2] -= 0.05

    def ground_sample(fa, fb):
        x = gx0 + fa * 2 * ext
        z = gz0 + fb * 2 * ext
        chk = ((np.floor(x / 16) + np.floor(z / 16)) % 2).astype(float)
        base = 70 + 10 * chk
        fade = np.clip(1 - np.hypot(x, z) / ext, 0, 1) ** 0.6
        col = np.stack([base * 0.95, base, base * 1.08], axis=-1)
        if shadow is not None:
            sm, (sx0, sz0, res) = shadow
            ix = np.clip(((x - sx0) / res).astype(int), 0, sm.shape[1] - 1)
            iz = np.clip(((z - sz0) / res).astype(int), 0, sm.shape[0] - 1)
            col = col * (1 - 0.45 * sm[iz, ix])[..., None]
        bgc = np.array(bg_bottom, dtype=float)
        col = col * fade[..., None] + bgc * (1 - fade[..., None])
        return col, fade > 0.01

    if pitch > 2:
        R.face(sa, sb, sc, lambda c: c, ground_sample)
    glow_layer = np.zeros((W, W, 3))
    glow_mask = np.zeros((W, W), dtype=bool)
    for tl, tr, bl, (u, v, uw, vh) in faces:
        a, b, c = to_screen(tl), to_screen(tr), to_screen(bl)
        n = np.cross(tr - tl, bl - tl)
        nn = np.linalg.norm(n)
        if nn < 1e-9:
            continue
        n = n / nn
        if (V @ n)[2] < 0:
            n = -n
        lit = 0.42 + 0.48 * max(0.0, float(n @ LIGHT1)) + 0.18 * max(0.0, float(n @ LIGHT2)) + 0.08 * max(0.0, n[1])

        def sample(fa, fb, u=u, v=v, uw=uw, vh=vh):
            tu = np.clip(((u + fa * uw) * model.sx).astype(int), 0, tw - 1)
            tv = np.clip(((v + fb * vh) * model.sy).astype(int), 0, th - 1)
            px = tex[tv, tu]
            out = px[..., :3]
            if glow is not None:
                g = glow[tv, tu]
                out = np.concatenate([out, g[..., :3], (g[..., 3:4] > 10).astype(float)], axis=-1)
            return out, px[..., 3] > 20

        def shade(rgb, lit=lit):
            base = rgb[:, :3] * lit
            if rgb.shape[1] > 3:
                g = rgb[:, 6:7]
                base = base * (1 - g) + np.maximum(base, rgb[:, 3:6]) * g
            return base

        R.face(a, b, c, shade, sample)
    # background gradient
    img = np.zeros((W, W, 3))
    t = np.linspace(0, 1, W)[:, None]
    for i in range(3):
        img[:, :, i] = bg_top[i] * (1 - t) + bg_bottom[i] * t
    img[R.mask] = R.col[R.mask]
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if ss > 1:
        out = out.resize((size, size), Image.LANCZOS)
    return out


def shadow_map(model, faces, res=1.0):
    """Top-down coverage of the posed model (alpha-tested), blurred, as a ground shadow."""
    pts = np.array([p for f in faces for p in f[:3]])
    if len(pts) == 0:
        return None
    x0, z0 = pts[:, 0].min() - 8, pts[:, 2].min() - 8
    x1, z1 = pts[:, 0].max() + 8, pts[:, 2].max() + 8
    w, h = int((x1 - x0) / res) + 1, int((z1 - z0) / res) + 1
    R = Raster(w, h)
    tex = model.tex
    th, tw = tex.shape[:2]
    for tl, tr, bl, (u, v, uw, vh) in faces:
        a = np.array([(tl[0] - x0) / res, (tl[2] - z0) / res, 0.0])
        b = np.array([(tr[0] - x0) / res, (tr[2] - z0) / res, 0.0])
        c = np.array([(bl[0] - x0) / res, (bl[2] - z0) / res, 0.0])

        def sample(fa, fb, u=u, v=v, uw=uw, vh=vh):
            tu = np.clip(((u + fa * uw) * model.sx).astype(int), 0, tw - 1)
            tv = np.clip(((v + fb * vh) * model.sy).astype(int), 0, th - 1)
            return np.zeros(fa.shape + (3,)), tex[tv, tu][..., 3] > 20

        R.face(a, b, c, lambda c_: c_, sample)
    m = R.mask.astype(float)
    # soften: fade with height is ignored, just blur
    img = Image.fromarray((m * 255).astype(np.uint8)).resize((max(1, w // 2), max(1, h // 2)), Image.BILINEAR)
    img = img.resize((w, h), Image.BILINEAR)
    return np.asarray(img).astype(float) / 255.0, (x0, z0, res)


def fit_frame(face_sets, V):
    xs, ys = [], []
    for faces in face_sets:
        for f in faces:
            for p in f[:3]:
                q = V @ p
                xs.append(q[0])
                ys.append(q[1])
    xs, ys = np.array(xs), np.array(ys)
    span = max(xs.max() - xs.min(), ys.max() - ys.min()) * 1.04 or 1.0
    return ((xs.max() + xs.min()) / 2, (ys.max() + ys.min()) / 2, span)


def anim_frames(model, anim, fps=12, length=None):
    L = length or anim.get("animation_length") or 2.0
    n = max(1, int(round(L * fps)))
    return [rig_v4.sample_anim(anim, i * L / n) for i in range(n)], L / n


def render_gif(model, anim, out, yaw=35, pitch=18, size=480, fps=12, frame=None):
    poses, dt = anim_frames(model, anim, fps)
    V = view_matrix(yaw, pitch)
    if frame is None:
        frame = fit_frame([collect_faces(model.skel, model.geo, p) for p in poses[::max(1, len(poses) // 8)]], V)
    imgs = [render_pose(model, p, yaw, pitch, size, frame) for p in poses]
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=int(dt * 1000), loop=0, optimize=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("geo")
    ap.add_argument("tex")
    ap.add_argument("out")
    ap.add_argument("--glow")
    ap.add_argument("--anim")
    ap.add_argument("--name")
    ap.add_argument("--time", type=float, default=0.0)
    ap.add_argument("--yaw", type=float, default=35)
    ap.add_argument("--pitch", type=float, default=18)
    ap.add_argument("--size", type=int, default=640)
    a = ap.parse_args()
    m = Model(a.geo, a.tex, a.glow)
    anim = None
    if a.anim:
        anims = json.load(open(a.anim))["animations"]
        anim = anims[a.name if a.name in anims else "animation.tech_dragon." + a.name]
    if a.out.endswith(".gif"):
        render_gif(m, anim, a.out, a.yaw, a.pitch, a.size)
    else:
        pose = rig_v4.sample_anim(anim, a.time) if anim else {}
        render_pose(m, pose, a.yaw, a.pitch, a.size).save(a.out)
