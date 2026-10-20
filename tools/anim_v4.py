"""
Animation baker for the Tech Dragon v4 rig.

Animations are authored as eased key poses plus procedural layers, then baked at 20 fps into plain GeckoLib keyframes:

* key poses: per-bone rotation/position/scale keys with an easing per segment; rotations are interpolated through
  quaternions (no gimbal wobble when a wing swings from folded to spread);
* follow-through: chains (neck, tail) can lag behind their own keys, bone k sampled at t - k * lag;
* layers: additive functions of time (breathing, tail sway, flutter...);
* leg IK: feet/hands are planted on world-space targets (two-bone solve plus a level foot), blended per leg with a
  weight track, so feet never slide or sink while the body moves;
* membranes: every wing panel is re-fitted each frame so it spans from its owner bone to the next bone (2D map,
  decomposed into rotation * scale * rotation over the panel's two bones).

Rotations follow GeckoLib/Bedrock conventions (see rig_v4.py): +x pitches the front down (raises a limb's end
backward), +y turns +x toward -z (a forward-pointing head turns to the dragon's right), +z tilts +x down (lowers the
left wing, raises the right one).
"""
import math

import numpy as np

import rig_v4

FPS = 20


# --------------------------------------------------------------------------------------------- math helpers

def euler_from_matrix(r):
    """Bedrock Euler (degrees) of a rotation matrix R = Rz(-z) Ry(y) Rx(-x)."""
    sb = -r[2, 0]
    sb = max(-1.0, min(1.0, sb))
    b = math.asin(sb)
    if abs(sb) < 0.99999:
        a = math.atan2(r[2, 1], r[2, 2])
        c = math.atan2(r[1, 0], r[0, 0])
    else:
        a = math.atan2(-r[1, 2], r[1, 1])
        c = 0.0
    return [-math.degrees(a), math.degrees(b), -math.degrees(c)]


def quat_from_matrix(m):
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = [(m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s]
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = [(m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s]
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = [(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def matrix_from_quat(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def slerp(q0, q1, t):
    d = float(np.dot(q0, q1))
    if d < 0:
        q1, d = -q1, -d
    if d > 0.9995:
        q = q0 + t * (q1 - q0)
        return q / np.linalg.norm(q)
    th = math.acos(d)
    return (math.sin((1 - t) * th) * q0 + math.sin(t * th) * q1) / math.sin(th)


def lerp_euler(a, b, t):
    """Rotation interpolation through quaternions (Euler endpoints, Euler result)."""
    if max(abs(a[i] - b[i]) for i in range(3)) < 25:
        return [a[i] + (b[i] - a[i]) * t for i in range(3)]
    q = slerp(quat_from_matrix(rig_v4.rot3(a)), quat_from_matrix(rig_v4.rot3(b)), t)
    e = euler_from_matrix(matrix_from_quat(q))
    return closest_euler(e, [a[i] + (b[i] - a[i]) * t for i in range(3)])


def closest_euler(e, ref):
    """Among equivalent Euler triplets pick the one closest to ref (keeps baked curves continuous)."""
    cands = [e, [e[0] + 180, 180 - e[1], e[2] + 180]]
    best, bd = None, 1e18
    for c in cands:
        c = [c[i] + 360 * round((ref[i] - c[i]) / 360.0) for i in range(3)]
        d = sum((c[i] - ref[i]) ** 2 for i in range(3))
        if d < bd:
            best, bd = c, d
    return best


def frame(direction, normal):
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    n = np.asarray(normal, float)
    n = n - d * float(n @ d)
    n /= np.linalg.norm(n)
    return np.column_stack([d, n, np.cross(d, n)])


def ease(kind, f):
    f = max(0.0, min(1.0, f))
    if kind == "lin":
        return f
    if kind == "smooth":
        return -(math.cos(math.pi * f) - 1) / 2
    if kind == "in":
        return f * f * f
    if kind == "out":
        return 1 - (1 - f) ** 3
    if kind == "in2":
        return f * f
    if kind == "out2":
        return 1 - (1 - f) ** 2
    if kind == "snap":  # very fast start, long settle (strikes)
        return 1 - (1 - f) ** 5
    if kind == "back":  # overshoot then settle
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * (f - 1) ** 3 + c1 * (f - 1) ** 2
    if kind == "hold":
        return 0.0
    raise ValueError(kind)


def sin_deg(x):
    return math.sin(math.radians(x))


def wave(t, period, amp, phase=0.0):
    """amp * sin(2pi (t/period) + phase degrees)."""
    return amp * math.sin(2 * math.pi * t / period + math.radians(phase))


# --------------------------------------------------------------------------------------------- authoring

def mirror_vec(v):
    return [v[0], -v[1], -v[2]]


def side_name(b, s):
    """'wing_l2' with s='r' -> 'wing_r2' (only for names that carry the _l marker)."""
    return b.replace("_l", "_" + s, 1)


def sym(pose):
    """Copy every *_l entry to its *_r mirror unless the right side is given explicitly.
    A key ending in '!' is one-sided: it is used as is and not mirrored."""
    out = {}
    for k, v in pose.items():
        if k.endswith("!"):
            out[k[:-1]] = v
    for k, v in pose.items():
        if k.endswith("!"):
            continue
        out[k] = v
        bone, _, chan = k.partition("@")
        if "_l" in bone and "_r" not in bone:
            rk = side_name(bone, "r") + ("@" + chan if chan else "")
            if rk not in pose and rk + "!" not in pose:
                if chan in ("", "rot"):
                    out[rk] = mirror_vec(v)
                elif chan == "pos":
                    out[rk] = [-v[0], v[1], v[2]]
                else:
                    out[rk] = list(v)
    return out


def swap_side(b):
    if "_l" in b:
        return b.replace("_l", "_r", 1)
    if "_r" in b:
        return b.replace("_r", "_l", 1)
    return b


class Anim:
    def __init__(self, name, length, loop=True):
        self.name, self.length, self.loop = name, float(length), loop
        self.keys = {}       # (bone, chan) -> list of (t, vec, ease)
        self.layers = []
        self.lags = {}       # bone -> seconds of delay
        self.ik = {}         # leg -> dict(target=fn(t)->world point offset, weight=fn(t), foot=fn(t)->extra pitch)
        self.events = {}

    # keys -----------------------------------------------------------------------------------
    def key(self, t, pose, e="smooth"):
        """pose: {"bone": rot, "bone@pos": vec, "bone@scale": vec}; right side mirrored automatically."""
        for k, v in sym(pose).items():
            bone, _, chan = k.partition("@")
            chan = {"": "rotation", "rot": "rotation", "pos": "position", "scale": "scale"}[chan]
            self.keys.setdefault((bone, chan), []).append((float(t), [float(c) for c in v], e))
        return self

    def seq(self, frames):
        """frames: [(t, pose, ease)]; a bone missing from a frame takes its rest value there.
        One-sided keys ('name!') stay one-sided in every frame."""
        bones = set()
        one = set()
        for _, pose, _ in frames:
            bones |= set(sym(pose).keys())
            one |= {k[:-1] for k in pose if k.endswith("!")}
        for t, pose, e in frames:
            p = sym(pose)
            full = {}
            for b in bones:
                v = p[b] if b in p else ([1, 1, 1] if b.endswith("@scale") else [0, 0, 0])
                full[b + "!" if b in one else b] = v
            self.key(t, full, e)
        return self

    def layer(self, fn):
        self.layers.append(fn)
        return self

    def lag(self, chain, step):
        for k, b in enumerate(chain):
            self.lags[b] = k * step
        return self

    def plant(self, leg, offset=None, weight=None, foot=None):
        """IK for a leg ('fl', 'fr', 'hl', 'hr'): offset(t) -> world displacement of the foot target from rest."""
        self.ik[leg] = dict(offset=offset or (lambda t: (0.0, 0.0, 0.0)), weight=weight or (lambda t: 1.0),
                            foot=foot or (lambda t: 0.0))
        return self

    def mirrored(self, name):
        """Left/right swapped copy (keys, layers, lags and IK legs)."""
        m = Anim(name, self.length, self.loop)
        for (bone, chan), track in self.keys.items():
            nb = swap_side(bone)
            m.keys[(nb, chan)] = [(t, (mirror_vec(v) if chan == "rotation" else ([-v[0], v[1], v[2]] if chan == "position" else list(v))), e)
                                  for t, v, e in track]
        for fn in self.layers:
            def mf(t, fn=fn):
                out = {}
                for k, v in sym(fn(t)).items():
                    bone, _, chan = k.partition("@")
                    nk = swap_side(bone) + ("@" + chan if chan else "") + "!"
                    out[nk] = mirror_vec(v) if chan in ("", "rot") else ([-v[0], v[1], v[2]] if chan == "pos" else list(v))
                return out
            m.layers.append(mf)
        m.lags = {swap_side(b): v for b, v in self.lags.items()}
        for leg, spec in self.ik.items():
            nl = leg[0] + ("r" if leg[1] == "l" else "l")
            off = spec["offset"]
            m.ik[nl] = dict(offset=lambda t, off=off: (-off(t)[0], off(t)[1], off(t)[2]), weight=spec["weight"], foot=spec["foot"])
        m.events = dict(self.events)
        return m

    # sampling -------------------------------------------------------------------------------
    def _sample_keys(self, track, t, chan):
        track = sorted(track, key=lambda k: k[0])
        if len(track) == 1:
            return track[0][1]
        if self.loop is True:
            t = t % self.length if self.length > 0 else 0.0
        if t <= track[0][0]:
            if self.loop is True and track[-1][0] < self.length:
                # wrap from the last key to the first through the loop end
                t0, v0, _ = track[-1]
                t1, v1, e1 = track[0]
                span = self.length - t0 + t1
                f = ease(e1, (t + self.length - t0) / span) if span > 0 else 1
                return lerp_euler(v0, v1, f) if chan == "rotation" else [a + (b - a) * f for a, b in zip(v0, v1)]
            return track[0][1]
        for i in range(1, len(track)):
            t1, v1, e1 = track[i]
            if t <= t1:
                t0, v0, _ = track[i - 1]
                f = ease(e1, (t - t0) / max(1e-9, t1 - t0))
                return lerp_euler(v0, v1, f) if chan == "rotation" else [a + (b - a) * f for a, b in zip(v0, v1)]
        t0, v0, _ = track[-1]
        if self.loop is True and track[0][0] > 0:
            t1, v1, e1 = track[0]
            span = self.length - t0 + t1
            f = ease(e1, (t - t0) / span) if span > 0 else 1
            return lerp_euler(v0, v1, f) if chan == "rotation" else [a + (b - a) * f for a, b in zip(v0, v1)]
        return v0

    def base_pose(self, t):
        pose = {}
        for (bone, chan), track in self.keys.items():
            tt = t - self.lags.get(bone, 0.0)
            if self.loop is not True:
                tt = max(0.0, tt)
            pose.setdefault(bone, {})[chan] = list(self._sample_keys(track, tt, chan))
        for fn in self.layers:
            for k, v in sym(fn(t)).items():
                bone, _, chan = k.partition("@")
                chan = {"": "rotation", "rot": "rotation", "pos": "position", "scale": "scale"}[chan]
                cur = pose.setdefault(bone, {}).get(chan, [1, 1, 1] if chan == "scale" else [0, 0, 0])
                if chan == "scale":
                    pose[bone][chan] = [cur[i] * v[i] for i in range(3)]
                else:
                    pose[bone][chan] = [cur[i] + v[i] for i in range(3)]
        return pose


# --------------------------------------------------------------------------------------------- rig solvers

_STRAIGHT = {}


class Rig:
    def __init__(self, dragon):
        self.D = dragon
        self.skel = rig_v4.Skeleton(dragon.bones)
        self.rest = self.skel.rest_world()
        self.piv = {b: np.array(self.skel.pivot[b], float) for b in self.skel.order}
        self.legs = {}
        for s in ("l", "r"):
            self.legs["f" + s] = dict(kind="front", chain=["arm_" + s, "forearm_" + s, "hand_" + s], end="hand_" + s, parent="chest")
            self.legs["h" + s] = dict(kind="hind", chain=["thigh_" + s, "shin_" + s, "meta_" + s, "foot_" + s], end="foot_" + s, parent="hips")

    # world helpers
    def world(self, pose):
        return self.skel.world(pose)

    def bone_rot_world(self, world, b):
        return world[b][:3, :3]

    def point(self, world, b, p):
        return rig_v4.Skeleton.point(world, b, p)

    # --- leg IK
    def solve_leg(self, pose, world, leg, target, foot_pitch=0.0):
        """Place the leg's end pivot (hand / foot) on target (world) with the hand/foot level."""
        L = self.legs[leg]
        ch = L["chain"]
        Mp = world[L["parent"]]
        Mp_inv = np.linalg.inv(Mp)
        Rp = Mp[:3, :3]
        piv = self.piv
        if L["kind"] == "hind":
            hip, knee, ankle, footp = [piv[b] for b in ch]
            # meta keeps its rest world orientation (plus foot_pitch lifts the heel), so the ankle target follows
            R_meta_des = rig_v4.rot3([foot_pitch * 0.6, 0, 0])
            ankle_target = np.asarray(target) - R_meta_des @ (footp - ankle)
            x1, z1, x2 = self._two_bone(hip, knee, ankle, (Mp_inv @ np.append(ankle_target, 1))[:3], bend=+1)
            r1 = [x1, 0.0, z1]
            r2 = [x2, 0.0, 0.0]
            R1 = Rp @ rig_v4.rot3(r1)
            R2 = R1 @ rig_v4.rot3(r2)
            r3 = euler_from_matrix(R2.T @ R_meta_des)
            R3 = R2 @ rig_v4.rot3(r3)
            r4 = euler_from_matrix(R3.T @ rig_v4.rot3([foot_pitch * -0.6, 0, 0]))
            out = {ch[0]: r1, ch[1]: r2, ch[2]: r3, ch[3]: r4}
        else:
            sh, el, wr = [piv[b] for b in ch]
            x1, z1, x2 = self._two_bone(sh, el, wr, (Mp_inv @ np.append(np.asarray(target), 1))[:3], bend=-1)
            r1 = [x1, 0.0, z1]
            r2 = [x2, 0.0, 0.0]
            R2 = Rp @ rig_v4.rot3(r1) @ rig_v4.rot3(r2)
            r3 = euler_from_matrix(R2.T @ rig_v4.rot3([foot_pitch, 0, 0]))
            out = {ch[0]: r1, ch[1]: r2, ch[2]: r3}
        return out

    @staticmethod
    def _two_bone(a, b, c, target, bend):
        """Rotations (bedrock x1, z1 for the root; x2 hinge for the middle joint) bringing c onto target.
        a, b, c: rest pivots of root, middle, end (parent space). bend: preferred sign of the hinge angle."""
        v1 = b - a
        v2 = c - b
        d = float(np.linalg.norm(target - a))
        l1, l2 = float(np.linalg.norm(v1)), float(np.linalg.norm(v2))
        d = max(abs(l1 - l2) + 0.05, min(l1 + l2 - 0.05, d))

        def length(x2):
            return float(np.linalg.norm(v1 + rig_v4.rot3([x2, 0, 0]) @ v2))
        # find the straightest hinge angle (cached per leg), then search the bend side for the wanted length
        key = (tuple(np.round(a, 3)), tuple(np.round(b, 3)), tuple(np.round(c, 3)))
        x_straight = _STRAIGHT.get(key)
        if x_straight is None:
            xs = np.linspace(-180, 180, 1441)
            ls = [length(x) for x in xs]
            x_straight = _STRAIGHT[key] = float(xs[int(np.argmax(ls))])
        lo, hi = x_straight, x_straight + bend * 179.0
        if length(hi) > d:
            x2 = hi
        else:
            for _ in range(50):
                mid = (lo + hi) / 2
                if length(mid) > d:
                    lo = mid
                else:
                    hi = mid
            x2 = (lo + hi) / 2
        v = v1 + rig_v4.rot3([x2, 0, 0]) @ v2
        u = (target - a)
        u = u / np.linalg.norm(u) * np.linalg.norm(v)
        # root: Rz(c) Rx(a) v = u  (bedrock x1 = -a, z1 = -c)
        R = math.hypot(v[1], v[2])
        phi = math.atan2(v[2], v[1])
        best = None
        for asn in (math.asin(max(-1, min(1, u[2] / R))), math.pi - math.asin(max(-1, min(1, u[2] / R)))):
            aa = asn - phi
            vy = math.cos(aa) * v[1] - math.sin(aa) * v[2]
            cc = math.atan2(u[1], u[0]) - math.atan2(vy, v[0])
            cc = (cc + math.pi) % (2 * math.pi) - math.pi
            aa = (aa + math.pi) % (2 * math.pi) - math.pi
            score = abs(cc) + 0.3 * abs(aa)
            if best is None or score < best[0]:
                best = (score, aa, cc)
        _, aa, cc = best
        return -math.degrees(aa), -math.degrees(cc), x2

    # --- membranes
    def fit_membranes(self, pose, world, prev=None):
        """Fan slices of every panel: the far bone's angle in the panel plane sets how far the fan is open."""
        out = {}
        for pnl in self.D.panels:
            for s, sg in (("l", 1), ("r", -1)):
                owner = pnl["owner"].replace("_l", "_" + s, 1)
                far_bone = pnl["far_bone"].replace("_l", "_" + s, 1)
                piv = np.array(pnl["pivot"], float) * [sg, 1, 1]
                far = np.array(pnl["far"], float) * [sg, 1, 1]
                rest_y = sg * pnl["rest_y"] if pnl["owner"] == "wing_l" else 0.0
                M = world[owner] @ rig_v4.bone_local(piv, [0, rest_y, 0])
                far_pre = (np.linalg.inv(self.rest[far_bone]) @ np.append(far, 1))[:3]
                far_w = self.point(world, far_bone, far_pre)
                fl = (np.linalg.inv(M) @ np.append(far_w, 1))[:3] - piv
                # angles in the left-side sense: the mirrored (right) frame has its anchor along -x
                th = pnl["far_angle"]
                phi = math.atan2(fl[2], fl[0] * sg)
                phi = th + ((phi - th + math.pi) % (2 * math.pi) - math.pi)
                k = phi / th if abs(th) > 1e-6 else 1.0
                k = max(0.03, min(1.6, k))
                nsl = len(pnl["slices"])
                shrink = RADIAL_SHRINK.get(pnl["name"], 0.0)
                for j, sl in enumerate(pnl["slices"]):
                    a0, w = sl["a0"], sl["w"]
                    sx = 1.0 - (1.0 - min(1.0, k)) * shrink * (j / max(1, nsl - 1))
                    name = sl["name"].replace("_l", "_" + s, 1)
                    sc = math.tan(w * k) / math.tan(w) if abs(math.tan(w)) > 1e-6 else 1.0
                    sc = max(0.02, min(3.0, sc))
                    out[name] = {"rotation": [0.0, -sg * math.degrees(a0 * (k - 1)), 0.0], "scale": [sx, 1.0, sc]}
        return out


# folding pulls the far part of the inner membranes in toward the pivot (the trailing corner would otherwise swing
# out past the elbow): x-scale of the last slice at a fully closed fan
RADIAL_SHRINK = {"memb_l0": 0.62, "memb_l3": 0.25}


def decompose(A, prev=None):
    """A (2x2 on panel-local (x, z), det > 0) = Ry(al) * diag(s1, s2) * Ry(be) in bedrock y-rotation degrees.
    Among the equivalent decompositions pick the one closest to prev (continuity); a near-uniform A puts all the
    rotation into be."""
    U, sig, Vt = np.linalg.svd(A)
    if np.linalg.det(U) < 0:
        U[:, 1] *= -1
        Vt[1, :] *= -1
    # (x, z) 2D rotation by phi == bedrock y rotation of -phi
    al0 = -math.degrees(math.atan2(U[1, 0], U[0, 0]))
    be0 = -math.degrees(math.atan2(Vt[1, 0], Vt[0, 0]))
    pa, pb = prev if prev is not None else (0.0, 0.0)
    if abs(sig[0] - sig[1]) < 0.03:
        total = al0 + be0
        be = pa + pb + ((total - pa - pb + 180) % 360 - 180) - pa
        return pa, be, float((sig[0] + sig[1]) / 2), float((sig[0] + sig[1]) / 2)
    best = None
    for k in range(-3, 4):
        al = al0 + 90 * k
        be = be0 - 90 * k
        al += 360 * round((pa - al) / 360.0)
        be += 360 * round((pb - be) / 360.0)
        s1, s2 = (sig[1], sig[0]) if k % 2 else (sig[0], sig[1])
        d = abs(al - pa) + abs(be - pb)
        if best is None or d < best[0]:
            best = (d, al, be, float(s1), float(s2))
    return best[1:]


# --------------------------------------------------------------------------------------------- baking

CHAN_TOL = {"rotation": 0.12, "position": 0.012, "scale": 0.003}


def bake(rig, anim):
    n = max(1, int(round(anim.length * FPS)))
    times = [i / FPS for i in range(n + 1)]
    times[-1] = anim.length
    frames = []
    memb_prev = {}
    for t in times:
        pose = anim.base_pose(t)
        if anim.ik:
            world = rig.world(pose)
            for leg, spec in anim.ik.items():
                w = float(spec["weight"](t))
                if w <= 0:
                    continue
                L = rig.legs[leg]
                rest_end = rig.piv[L["end"]]
                off = np.asarray(spec["offset"](t), float)
                target = rest_end + off
                sol = rig.solve_leg(pose, world, leg, target, spec["foot"](t))
                for b, r in sol.items():
                    cur = pose.setdefault(b, {}).get("rotation", [0, 0, 0])
                    pose[b]["rotation"] = [cur[i] * (1 - w) + r[i] * w for i in range(3)] if w < 1 else list(r)
        world = rig.world(pose)
        for b, v in rig.fit_membranes(pose, world, memb_prev).items():
            pose[b] = v
        frames.append(pose)
    # continuity of Euler angles, then keyframe reduction
    bones = {}
    for f in frames:
        for b, chans in f.items():
            for c in chans:
                bones.setdefault(b, set()).add(c)
    out = {}
    for b in sorted(bones):
        if b in PROCEDURAL:
            raise ValueError("%s animates procedural bone %s" % (anim.name, b))
        entry = {}
        for c in sorted(bones[b]):
            default = [1, 1, 1] if c == "scale" else [0, 0, 0]
            vals = [list(f.get(b, {}).get(c, default)) for f in frames]
            if c == "rotation":
                for i in range(1, len(vals)):
                    vals[i] = closest_euler(vals[i], vals[i - 1])
            keep = reduce_keys(times, vals, CHAN_TOL[c])
            if all(max(abs(v[k] - default[k]) for k in range(3)) < CHAN_TOL[c] for v in vals):
                continue
            entry[c] = {fmt_t(times[i]): {"vector": [round(v, 3) for v in vals[i]]} for i in keep}
        if entry:
            out[b] = entry
    res = {"animation_length": round(anim.length, 4), "bones": out}
    if anim.loop is True:
        res["loop"] = True
    elif anim.loop == "hold":
        res["loop"] = "hold_on_last_frame"
    return res


def fmt_t(t):
    return ("%.4f" % t).rstrip("0").rstrip(".") if t else "0.0"


def reduce_keys(times, vals, tol):
    """Indices of keys to keep so linear interpolation stays within tol of every baked sample."""
    n = len(vals)
    if n <= 2:
        return list(range(n))
    keep = [0]
    i = 0
    while i < n - 1:
        j = i + 2
        while j < n:
            ok = True
            for k in range(i + 1, j):
                f = (times[k] - times[i]) / (times[j] - times[i])
                for c in range(3):
                    if abs(vals[i][c] + (vals[j][c] - vals[i][c]) * f - vals[k][c]) > tol:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
            j += 1
        keep.append(j - 1)
        i = j - 1
    return keep


PROCEDURAL = {"root", "flight", "headc", "tail_tip", "mouth", "saddle"} | {"neck%dc" % k for k in range(1, 5)} | {"tail%dc" % k for k in range(1, 9)}
