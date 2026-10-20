"""
Tech Dragon v4 animations (authored with anim_v4: key poses + follow-through + layers + leg IK + membrane fitting).

Timing notes for the Java side live in ANIM_EVENTS (hit frames etc., seconds).
"""
import math

import numpy as np

import anim_v4 as A
import dragon_v4
import rig_v4
from anim_v4 import Anim, wave

NECK = ["neck1", "neck2", "neck3", "neck4", "head"]
TAIL = ["tail%d" % (k + 1) for k in range(8)]
LEGS = ("fl", "fr", "hl", "hr")


# --------------------------------------------------------------------------------------------- wing poses

def _rest_dirs():
    S, E, W = map(np.array, (dragon_v4.S, dragon_v4.E, dragon_v4.W))
    T1 = np.array(dragon_v4.TIPS[0])
    return (E - S) / np.linalg.norm(E - S), (W - E) / np.linalg.norm(W - E), (T1 - W) / np.linalg.norm(T1 - W)


def wing_pose(dh, df, d1, n_hand, fan=(0.0, 0.0), n_arm=None):
    """Left-wing Euler angles from wanted chest-space directions of the humerus, forearm and leading finger, the
    hand plane normal, and the in-plane fan of fingers 2 and 3 (degrees added to their rest spread)."""
    dh0, df0, d10 = _rest_dirs()
    up = np.array([0.0, 1.0, 0.0])
    dh, df, d1 = [np.asarray(v, float) / np.linalg.norm(v) for v in (dh, df, d1)]
    if n_arm is None:
        n_arm = np.cross(dh, df)
        if np.linalg.norm(n_arm) < 1e-6:
            n_arm = up
    Rh = A.frame(dh, n_arm) @ A.frame(dh0, up).T
    Rf = A.frame(df, n_arm) @ A.frame(df0, up).T
    Rw = A.frame(d1, n_hand) @ A.frame(d10, up).T
    return {
        "wing_l": A.euler_from_matrix(Rh),
        "wing_l2": A.euler_from_matrix(Rh.T @ Rf),
        "wing_l3": A.euler_from_matrix(Rf.T @ Rw),
        "finger_l2": [0, fan[0], 0],
        "finger_l3": [0, fan[1], 0],
    }


# folded on the ground: elbow high over the back, forearm forward, fingers draped back along the flank as a curtain
FOLD = wing_pose(dh=(0.34, 0.40, 0.85), df=(0.10, -0.22, -0.97), d1=(0.10, -0.10, 0.99), n_hand=(-1.0, 0.25, 0.05), fan=(17, 36))
# folded but held a little away from the body (walking, alert)
FOLD_LOOSE = wing_pose(dh=(0.44, 0.40, 0.80), df=(0.18, -0.20, -0.96), d1=(0.20, -0.08, 0.975), n_hand=(-1.0, 0.35, 0.1), fan=(14, 30))
# draped on the ground while lying down
DRAPE = wing_pose(dh=(0.78, 0.12, 0.62), df=(0.55, -0.22, -0.80), d1=(0.62, -0.28, 0.73), n_hand=(-0.25, 1.0, 0.0), fan=(8, 18))
# raised and half open (roar, threat display)
DISPLAY = wing_pose(dh=(0.55, 0.78, 0.30), df=(0.70, 0.45, -0.55), d1=(0.85, 0.40, 0.35), n_hand=(-0.45, 0.85, -0.2), fan=(4, 8))
SPREAD = {"wing_l": [0, 0, 0], "wing_l2": [0, 0, 0], "wing_l3": [0, 0, 0], "finger_l2": [0, 0, 0], "finger_l3": [0, 0, 0]}


def merge(*ps):
    """Later poses override earlier ones. A later pose's left-side key also overrides the right side (its mirror) unless
    that pose gives the right side itself or marks the key one-sided ('!'): poses are symmetric by convention, and an
    earlier pose may already hold an explicit right side (add() returns sym()'d poses), which used to survive, e.g.
    merge(add(STAND, ...), UP_V) raised only the left wing (1.7.0 stomp, pylon_charge and 12 others)."""
    out = {}
    for n, p in enumerate(ps):
        if n == 0:
            out.update(p)
            continue
        plain = {k: v for k, v in p.items() if not k.endswith("!")}
        for k, v in A.sym(plain).items():
            if k not in p:
                out.pop(k + "!", None)
                out[k] = v
        out.update(p)
    return out


# --------------------------------------------------------------------------------------------- body poses

NECK_STAND = {"neck1": [-32, 0, 0], "neck2": [-14, 0, 0], "neck3": [4, 0, 0], "neck4": [14, 0, 0], "head": [24, 0, 0]}
NECK_LOW = {"neck1": [-10, 0, 0], "neck2": [-3, 0, 0], "neck3": [4, 0, 0], "neck4": [6, 0, 0], "head": [7, 0, 0]}
TAIL_STAND = {"tail1": [-10, 0, 0], "tail2": [-6, 0, 0], "tail3": [-3, 0, 0], "tail4": [-1, 0, 0], "tail5": [2, 0, 0], "tail6": [3, 0, 0],
              "tail7": [4, 0, 0], "tail8": [4, 0, 0]}
STAND = merge(NECK_STAND, TAIL_STAND, FOLD)


def tail_sway(period, amp=3.0, grow=0.6, lag=38, phase=0.0):
    def fn(t):
        return {TAIL[k]: [0, wave(t, period, amp + grow * k, phase - k * lag), 0] for k in range(8)}
    return fn


def breathe(period, depth=1.0):
    def fn(t):
        b = math.sin(2 * math.pi * t / period)
        return {"ribs@scale": [1 + 0.022 * depth * b, 1 + 0.018 * depth * b, 1],
                "body@pos": [0, 0.3 * depth * b, 0],
                "neck1": [-0.8 * depth * b, 0, 0], "head": [0.6 * depth * b, 0, 0]}
    return fn


def plant_all(a, legs=LEGS):
    for leg in legs:
        a.plant(leg)
    return a


# --------------------------------------------------------------------------------------------- animations

def idle():
    a = Anim("ground_idle", 6.0, True)
    look = [(0.0, {}), (1.0, {"neck3": [0, -6, 0], "neck4": [0, -8, 0], "head": [-4, -16, 0]}), (2.2, {"neck3": [0, -6, 0], "neck4": [0, -8, 0], "head": [-4, -16, 0]}),
            (3.0, {}), (4.0, {"neck3": [0, 5, 0], "neck4": [0, 7, 0], "head": [3, 13, 4]}), (5.0, {"neck3": [0, 5, 0], "neck4": [0, 7, 0], "head": [3, 13, 4]}), (6.0, {})]
    for t, p in look:
        a.key(t, add(STAND, p), "smooth")
    a.lag(NECK, 0.08).lag(TAIL, 0.1)
    a.layer(breathe(3.0)).layer(tail_sway(6.0, 2.5, 0.5))
    a.layer(blink([1.6, 4.4]))
    a.layer(lambda t: {"wing_l": [0, 0, wave(t, 3.0, 0.8, 60)]})
    return plant_all(a)


def walk():
    L = 1.6
    stride = 22.0
    a = Anim("walk", L, True)
    pose = merge(STAND, NECK_LOW, FOLD_LOOSE, {"neck1": [-16, 0, 0], "neck2": [-6, 0, 0]})
    a.key(0, pose).key(L, pose)
    duty = 0.7
    phases = {"hl": 0.0, "fl": 0.22, "hr": 0.5, "fr": 0.72}

    def foot(leg):
        lift = 4.0 if leg[0] == "f" else 3.4

        def off(t):
            ph = (t / L + phases[leg]) % 1.0
            if ph < duty:
                return (0.0, 0.0, -stride / 2 + stride * ph / duty)
            u = (ph - duty) / (1 - duty)
            return (0.0, lift * math.sin(math.pi * u), stride / 2 - stride * A.ease("smooth", u))

        def pitch(t):
            ph = (t / L + phases[leg]) % 1.0
            if ph < duty:
                return 0.0
            return 28 * math.sin(math.pi * (ph - duty) / (1 - duty))
        return off, pitch

    for leg in LEGS:
        off, pitch = foot(leg)
        a.plant(leg, off, foot=pitch)

    def body(t):
        return {"body@pos": [0, -0.5 * math.cos(4 * math.pi * t / L) + 0.3, 0],
                "body": [0, 0, wave(t, L, 1.4, 90)],
                "chest": [0, wave(t, L, 4.0, 0), 0], "hips": [0, wave(t, L, -3.5, 0), 0],
                "neck1": [wave(t, L / 2, 1.2, 60), wave(t, L, -3.0, 20), 0], "neck3": [0, wave(t, L, -2, 60), 0],
                "head": [wave(t, L / 2, -1.5, 80), wave(t, L, 3.0, 40), 0],
                "wing_l": [0, 0, wave(t, L / 2, 1.5, 30)]}
    a.layer(body).layer(tail_sway(L, 3.5, 0.6, 42, 180))
    return a


def rest():
    """Lying down (sphinx pose), breathing slowly."""
    a = Anim("rest", 6.0, True)
    a.key(0, rest_pose()).key(6.0, rest_pose())
    a.lag(NECK, 0.1)
    a.layer(breathe(4.0, 1.3)).layer(tail_sway(6.0, 1.5, 0.3, 30))
    a.layer(blink([2.5]))
    rest_legs(a)
    return a


def rest_pose():
    return merge(DRAPE, {
        "body@pos": [0, -13.2, 0], "chest": [2, 0, 0], "hips": [-1, 0, 0],
        "neck1": [8, 10, 0], "neck2": [2, 10, 0], "neck3": [-2, 9, 0], "neck4": [-4, 7, 0], "head": [-3, 5, 2],
        "tail1": [-14, -8, 0], "tail2": [4, -12, 0], "tail3": [4, -14, 0], "tail4": [3, -16, 0], "tail5": [2, -18, 0],
        "tail6": [1, -18, 0], "tail7": [0, -16, 0], "tail8": [0, -14, 0]})


def rest_legs(a):
    a.plant("fl", lambda t: (1.5, 0.0, -13.0), foot=lambda t: 0.0)
    a.plant("fr", lambda t: (-1.5, 0.0, -13.0), foot=lambda t: 0.0)
    a.plant("hl", lambda t: (2.5, 0.0, 2.0), foot=lambda t: -30.0)
    a.plant("hr", lambda t: (-2.5, 0.0, 2.0), foot=lambda t: -30.0)


def fly():
    L = 2.0
    a = Anim("fly", L, True)
    up = {"wing_l": [6, 10, -42], "wing_l2": [0, 22, 14], "wing_l3": [0, -30, 18], "finger_l2": [0, 10, 0], "finger_l3": [0, 20, 0]}
    down = {"wing_l": [-4, -6, 34], "wing_l2": [0, -4, -6], "wing_l3": [0, 6, -10], "finger_l2": [0, -3, 0], "finger_l3": [0, -4, 0]}
    mid_down = {"wing_l": [-6, -2, 0], "wing_l2": [0, 0, -10], "wing_l3": [0, 0, -16], "finger_l2": [0, -2, 0], "finger_l3": [0, -2, 0]}
    body = merge({"neck1": [-6, 0, 0], "neck2": [-2, 0, 0], "neck3": [2, 0, 0], "neck4": [3, 0, 0], "head": [5, 0, 0]}, LEGS_TUCKED,
                 {"tail1": [2, 0, 0], "tail2": [1, 0, 0]})
    a.key(0.0, merge(body, up), "smooth")
    a.key(0.46, merge(body, mid_down), "in2")
    a.key(0.85, merge(body, down), "out2")
    a.key(1.62, merge(body, {"wing_l": [2, 6, -18], "wing_l2": [0, 18, 10], "wing_l3": [0, -22, 14], "finger_l2": [0, 8, 0], "finger_l3": [0, 16, 0]}), "smooth")
    a.key(L, merge(body, up), "smooth")
    a.lag(["wing_l", "wing_l2", "wing_l3"], 0.055)
    a.lag(["wing_r", "wing_r2", "wing_r3"], 0.055)
    a.lag(NECK, 0.08).lag(TAIL, 0.1)

    def bob(t):
        return {"body@pos": [0, wave(t, L, 1.8, -100), 0], "body": [wave(t, L, 2.0, -60), 0, 0],
                "neck1": [wave(t, L, -2.0, -40), 0, 0], "head": [wave(t, L, 2.5, -20), 0, 0]}
    a.layer(bob).layer(lambda t: {TAIL[k]: [wave(t, L, 2.0 + 0.4 * k, -100 - k * 40), wave(t, 2 * L, 2 + 0.3 * k, -k * 35), 0] for k in range(8)})
    return a


LEGS_TUCKED = {"arm_l": [62, 0, -6], "forearm_l": [-95, 0, 0], "hand_l": [70, 0, 0], "claws_l": [25, 0, 0],
               "thigh_l": [58, 0, -4], "shin_l": [22, 0, 0], "meta_l": [40, 0, 0], "foot_l": [55, 0, 0]}


def bite():
    """Quick snap: pull back, strike forward-down, jaw opens wide then slams shut at the hit frame (0.45 s)."""
    a = Anim("bite", 1.0, False)
    base = STAND
    a.seq([
        (0.0, base, "smooth"),
        (0.28, add(base, {"body@pos": [0, 0.8, 1.5], "chest": [-3, 0, 0], "neck1": [-6, 0, 0], "neck2": [-6, 0, 0], "neck3": [-3, 0, 0],
                          "head": [-8, 0, 0], "jaw": [14, 0, 0], "crest@scale": [1.06, 1.06, 1.06]}), "out2"),
        (0.38, add(base, {"body@pos": [0, -0.6, -3.5], "chest": [4, 0, 0], "neck1": [10, 0, 0], "neck2": [9, 0, 0], "neck3": [3, 0, 0],
                          "neck4": [-2, 0, 0], "head": [-6, 0, 0], "jaw": [40, 0, 0]}), "in2"),
        (0.45, add(base, {"body@pos": [0, -0.8, -4], "chest": [5, 0, 0], "neck1": [13, 0, 0], "neck2": [10, 0, 0], "neck3": [3, 0, 0],
                          "neck4": [-2, 0, 0], "head": [-4, 0, 0], "jaw": [-2, 0, 0]}), "snap"),
        (0.62, add(base, {"body@pos": [0, -0.4, -2.5], "chest": [3, 0, 0], "neck1": [8, 0, 0], "neck2": [6, 0, 0], "neck3": [2, 0, 0],
                          "head": [2, 3, 0], "jaw": [0, 0, 0]}), "smooth"),
        (1.0, base, "smooth"),
    ])
    a.lag(NECK, 0.02).lag(TAIL, 0.06)
    a.layer(tail_sway(4.0, 2.0, 0.4)).layer(breathe(3.0, 0.5))
    a.events = {"hit": 0.45}
    return plant_all(a)


def claw_left():
    """Shift the weight back, swing the left forefoot out, up and forward, then rake it down and across (hit 0.52 s).
    The striking paw follows an IK path so it really travels through the space in front of the chest."""
    a = Anim("claw_left", 1.15, False)
    base = STAND
    up = {"body@pos": [0, 1.2, 1.8], "chest": [-7, -8, 3], "hips": [2, 0, 0], "neck1": [6, -10, 0], "neck2": [4, -4, 0], "neck3": [0, -4, 0],
          "head": [0, -8, 0], "jaw": [10, 0, 0]}
    strike = {"body@pos": [0, -0.6, -2.5], "chest": [5, 9, -3], "hips": [-1, 0, 0], "neck1": [14, 8, 0], "neck2": [6, 4, 0], "neck3": [2, 4, 0],
              "head": [8, 10, 0], "jaw": [22, 0, 0]}
    a.seq([
        (0.0, base, "smooth"),
        (0.38, add(base, up), "out2"),
        (0.52, add(base, strike), "in"),
        (0.72, add(base, merge(strike, {"chest": [3, 6, -2], "jaw": [6, 0, 0]})), "out2"),
        (1.15, base, "smooth"),
    ])
    a.lag(NECK, 0.04).lag(TAIL, 0.07)
    a.layer(tail_sway(3.0, 2.5, 0.5))
    paw = path([(0.0, (0, 0, 0), "smooth"), (0.12, (2, 3, 1), "out2"), (0.38, (16, 34, -18), "out2"), (0.47, (8, 20, -27), "in2"),
                (0.54, (-5, 4, -24), "out"), (0.72, (-3, 2, -16), "smooth"), (1.02, (0, 0, 0), "smooth")])
    curl = path([(0.0, 0, "smooth"), (0.38, -55, "out2"), (0.52, 35, "in"), (0.8, 10, "smooth"), (1.05, 0, "smooth")])
    a.plant("fl", paw, foot=curl)
    for leg in ("fr", "hl", "hr"):
        a.plant(leg)
    a.layer(lambda t: {"claws_l!": [path([(0.0, 0, "smooth"), (0.38, -35, "out2"), (0.5, 40, "in"), (0.8, 0, "smooth")])(t), 0, 0]})
    a.events = {"hit": 0.52}
    return a


def path(keys):
    """Keyframed value (number or tuple) as a function of time; each key's easing shapes the segment ending at it."""
    def fn(t):
        if t <= keys[0][0]:
            return keys[0][1]
        for i in range(1, len(keys)):
            t1, v1, e = keys[i]
            if t <= t1:
                t0, v0, _ = keys[i - 1]
                f = A.ease(e, (t - t0) / max(1e-9, t1 - t0))
                if isinstance(v0, tuple):
                    return tuple(v0[k] + (v1[k] - v0[k]) * f for k in range(len(v0)))
                return v0 + (v1 - v0) * f
        return keys[-1][1]
    return fn


def roar():
    a = Anim("roar", 2.8, False)
    base = STAND
    crouch = {"body@pos": [0, -1.5, 1.5], "chest": [5, 0, 0], "neck1": [6, 0, 0], "neck2": [8, 0, 0], "neck3": [4, 0, 0], "head": [-4, 0, 0],
              "jaw": [6, 0, 0]}
    rise = merge(DISPLAY, {"body@pos": [0, 1.6, 1.0], "chest": [-9, 0, 0], "hips": [2, 0, 0], "neck1": [-8, 0, 0], "neck2": [-2, 0, 0],
                           "neck3": [10, 0, 0], "neck4": [0, 0, 0], "head": [-26, 0, 0], "jaw": [42, 0, 0], "crest@scale": [1.18, 1.18, 1.18],
                           "core@scale": [1.25, 1.25, 1.25]})
    a.seq([
        (0.0, base, "smooth"),
        (0.5, add(base, crouch), "smooth"),
        (0.9, merge(add(base, rise), DISPLAY), "out"),
        (2.0, merge(add(base, rise), DISPLAY, {"head": [-12, 0, 0], "jaw": [38, 0, 0]}), "smooth"),
        (2.8, base, "smooth"),
    ])
    a.lag(NECK, 0.05).lag(TAIL, 0.08)

    def shake(t):
        k = smooth_window(t, 0.8, 1.0, 1.9, 2.1)
        return {"jaw": [k * wave(t, 0.09, 2.5), 0, 0], "head": [k * wave(t, 0.13, 1.2), k * wave(t, 0.21, 1.5), 0],
                "wing_l": [0, 0, k * wave(t, 0.16, 1.8)], "wing_l3": [0, 0, k * wave(t, 0.12, 2.5, 40)]}
    a.layer(shake).layer(tail_sway(2.0, 3.0, 0.8))
    a.events = {"roar": 0.85}
    return plant_all(a)


# --------------------------------------------------------------------------------------------- helpers

def add(pose, delta):
    """pose + delta (rotation/position add, scale multiply); delta keys ending in '!' stay one-sided."""
    out = A.sym(pose)
    for k, v in delta.items():
        one = k.endswith("!")
        kk = k[:-1] if one else k
        if kk.endswith("@scale"):
            cur = out.get(kk, [1, 1, 1])
            out[kk + ("!" if one else "")] = [cur[i] * v[i] for i in range(3)]
            if one:
                out.pop(kk, None)
        else:
            cur = out.get(kk, [0, 0, 0])
            nv = [cur[i] + v[i] for i in range(3)]
            if one:
                out.pop(kk, None)
                out[kk + "!"] = nv
            else:
                out[kk] = nv
                rk = A.side_name(kk.partition("@")[0], "r")
                if "_l" in kk.partition("@")[0]:
                    # keep the mirrored side in step with the edited left side
                    chan = kk.partition("@")[2]
                    rkey = rk + ("@" + chan if chan else "")
                    curr = out.get(rkey, [0, 0, 0])
                    mv = A.mirror_vec(v) if chan in ("", "rot") else ([-v[0], v[1], v[2]] if chan == "pos" else v)
                    out[rkey] = [curr[i] + mv[i] for i in range(3)]
    return out


def smooth_window(t, a, b, c, d):
    """0 before a, ramps to 1 by b, holds, back to 0 between c and d (smooth)."""
    if t <= a or t >= d:
        return 0.0
    if t < b:
        return A.ease("smooth", (t - a) / (b - a))
    if t <= c:
        return 1.0
    return 1.0 - A.ease("smooth", (t - c) / (d - c))


def blink(times, dur=0.22):
    def fn(t):
        k = 0.0
        for t0 in times:
            if t0 <= t <= t0 + dur:
                u = (t - t0) / dur
                k = max(k, math.sin(math.pi * u))
        return {"lid_l@pos": [0, -3.2 * k, 0]}
    return fn


ANIMS = [idle, walk, rest, fly, bite, claw_left, roar]
MIRRORED = {"claw_left": "claw_right"}

# multipart hitbox reference points (bone, rest-space point) exported per tick for the server (TechDragon parts)
PART_POINTS = [
    ("head", "headc", (0, 34, -104)), ("neck", "neck2c", (0, 31, -54)), ("chest", "ribs", (0, 28, -26)), ("hips", "hips", (0, 28, 7)),
    ("tail1", "tail2c", (0, 30, 33)), ("tail2", "tail4c", (0, 29.6, 57)), ("tail3", "tail7c", (0, 29, 92)),
    ("wing_l", "wing_l2", (51, 40.5, -30)), ("wing_r", "wing_r2", (-51, 40.5, -30)),
    ("wingtip_l", "finger_l2", (109, 41, -36)), ("wingtip_r", "finger_r2", (-109, 41, -36)),
    ("mouth", "mouth", (0, 30, -114)), ("saddle", "saddle", (0, 41.5, -22)), ("core", "core", (0, 20.4, -44.6)),
    ("hand_l", "hand_l", (12.5, 2, -33)), ("hand_r", "hand_r", (-12.5, 2, -33)), ("tailtip", "tail_tip", (0, 28.8, 112)),
]


def all_animations(dragon):
    import dragon_v4_anims2 as M2
    rig = A.Rig(dragon)
    anims = {}
    events = {}
    mirrored = dict(MIRRORED, **M2.MIRRORED)
    for fn in ANIMS + M2.ANIMS2:
        a = fn()
        anims[a.name] = A.bake(rig, a)
        events[a.name] = dict(a.events, length=a.length, loop=a.loop)
        if a.name in mirrored:
            m = a.mirrored(mirrored[a.name])
            anims[m.name] = A.bake(rig, m)
            events[m.name] = dict(a.events, length=a.length, loop=a.loop)
    import dragon_v5_anims as M5
    M5.add_to(anims, events, rig)
    import dragon_v6_anims as M6
    M6.add_to(anims, events, rig)
    import dragon_v7_anims as M7
    M7.add_to(anims, events, rig)
    import dragon_v8_anims as M8
    M8.add_to(anims, events, rig)
    return {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": anims}, events


def export_parts(dragon, data):
    """Per-tick model-space positions (px) of the hitbox points for every animation, as the client will play them."""
    skel = rig_v4.Skeleton(dragon.bones)
    rest = skel.rest_world()
    pre = []
    for name, bone, p in PART_POINTS:
        q = np.linalg.inv(rest[bone]) @ np.array([p[0], p[1], p[2], 1.0])
        pre.append((name, bone, q[:3]))
    out = {"points": [n for n, _, _ in pre], "animations": {}}
    for key, anim in data["animations"].items():
        name = key.split(".")[-1]
        L = anim["animation_length"]
        n = max(1, int(round(L * 20)))
        frames = []
        for i in range(n + 1):
            pose = rig_v4.sample_anim(anim, min(L, i / 20.0))
            w = skel.world(pose)
            row = []
            for _, bone, q in pre:
                v = skel.point(w, bone, q)
                row.extend([round(float(v[0]), 2), round(float(v[1]), 2), round(float(v[2]), 2)])
            frames.append(row)
        out["animations"][name] = {"length": L, "loop": anim.get("loop") is True, "frames": frames}
    return out


if __name__ == "__main__":
    import json
    import sys
    out = sys.argv[1]
    D = dragon_v4.build_dragon()
    data, ev = all_animations(D)
    json.dump(data, open(out + "/tech_dragon.animation.json", "w"))
    json.dump(export_parts(D, data), open(out + "/tech_dragon_parts.json", "w"), separators=(",", ":"))
    json.dump(ev, open(out + "/tech_dragon_events.json", "w"), indent=1)
    print(len(data["animations"]), "animations")
