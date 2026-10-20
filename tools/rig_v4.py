"""
Forward kinematics for GeckoLib/Bedrock models, shared by the Tech Dragon v4 animation baker (dragon_v4_anim.py) and
the preview renderer (render_v4.py), so what the baker measures (feet on the ground, membranes spanning their fingers,
hitbox bone positions) is exactly what gets drawn.

Everything is in Bedrock model space (x = the model's left, y up, front = -z, 16 px = 1 block at scale 1).
GeckoLib conventions, worked out in Bedrock space:
  * bone/cube rotation [x, y, z] (degrees) = Rz(-z) * Ry(y) * Rx(-x) with right-handed axis matrices, so
    +x pitches the front (-z) down, +y turns +x toward -z, +z tilts +x down;
  * animation rotation is ADDED to the rest rotation (Euler sum), position is a translation in the parent frame,
    scale is applied after rotation (in the bone's own frame): M = parent * T(pos) * T(pivot) * R * S * T(-pivot).
"""
import math

import numpy as np


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


def rot3(deg):
    x, y, z = [math.radians(v) for v in deg]
    return rz(-z) @ ry(y) @ rx(-x)


def mat4(r=None, t=None):
    m = np.eye(4)
    if r is not None:
        m[:3, :3] = r
    if t is not None:
        m[:3, 3] = t
    return m


def bone_local(pivot, rest, rot=(0, 0, 0), pos=(0, 0, 0), scale=(1, 1, 1)):
    """Bone matrix relative to its parent."""
    p = np.asarray(pivot, dtype=float)
    r = rot3([rest[i] + rot[i] for i in range(3)])
    s = np.diag([scale[0], scale[1], scale[2]])
    return mat4(t=np.asarray(pos, dtype=float) + p) @ mat4(r @ s) @ mat4(t=-p)


class Skeleton:
    """bones: list of (name, parent, pivot, rest_rotation or None) in parent-before-child order."""

    def __init__(self, bones):
        self.order = [b[0] for b in bones]
        self.parent = {b[0]: b[1] for b in bones}
        self.pivot = {b[0]: list(b[2]) for b in bones}
        self.rest = {b[0]: list(b[3] or [0, 0, 0]) for b in bones}

    def world(self, pose):
        """pose: {bone: {"rotation": [..], "position": [..], "scale": [..]}} -> {bone: 4x4 world matrix}."""
        out = {}
        for name in self.order:
            p = pose.get(name, {})
            m = bone_local(self.pivot[name], self.rest[name], p.get("rotation", (0, 0, 0)), p.get("position", (0, 0, 0)),
                           p.get("scale", (1, 1, 1)))
            par = self.parent[name]
            out[name] = out[par] @ m if par else m
        return out

    @staticmethod
    def point(world, bone, p):
        """Rest-space point p carried by bone -> posed position."""
        v = world[bone] @ np.array([p[0], p[1], p[2], 1.0])
        return v[:3]

    def rest_world(self):
        return self.world({})


def cube_matrix(cube):
    """Cube rotation about its pivot (rest model space)."""
    if not cube.get("rotation"):
        return np.eye(4)
    p = np.asarray(cube.get("pivot"), dtype=float)
    return mat4(t=p) @ mat4(rot3(cube["rotation"])) @ mat4(t=-p)


def load_geo(geo):
    g = geo["minecraft:geometry"][0]
    bones = [(b["name"], b.get("parent"), b["pivot"], b.get("rotation")) for b in g["bones"]]
    return Skeleton(bones), g


def sample_track(track, t):
    """GeckoLib keyframe track sampled at t (linear, step and the smooth easings we emit)."""
    if track is None:
        return None
    if isinstance(track, (list, int, float, str)) or (isinstance(track, dict) and ("vector" in track or "post" in track)):
        return _vec(track)
    keys = sorted(((float(k), v) for k, v in track.items()), key=lambda kv: kv[0])
    vals = [_vec(v) for _, v in keys]
    if t <= keys[0][0]:
        return vals[0]
    for i in range(1, len(keys)):
        if t <= keys[i][0]:
            f = (t - keys[i - 1][0]) / max(1e-9, keys[i][0] - keys[i - 1][0])
            e = keys[i][1].get("easing") if isinstance(keys[i][1], dict) else None
            if e == "step":
                f = 0.0
            elif e == "easeInOutSine":
                f = -(math.cos(math.pi * f) - 1) / 2
            return [a + (b - a) * f for a, b in zip(vals[i - 1], vals[i])]
    return vals[-1]


def _vec(v):
    if isinstance(v, dict):
        v = v.get("vector", v.get("post", v.get("pre")))
        if isinstance(v, dict):
            v = v.get("vector")
    if not isinstance(v, list):
        v = [v, v, v]
    out = []
    for c in v:
        try:
            out.append(float(c))
        except (TypeError, ValueError):
            out.append(0.0)
    return out


def sample_anim(anim, t):
    pose = {}
    for bone, chans in anim.get("bones", {}).items():
        pose[bone] = {k: sample_track(v, t) for k, v in chans.items()}
    return pose
