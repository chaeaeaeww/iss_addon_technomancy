"""
Tech Dragon v5 (1.7): the aggressive ground moveset added on top of the v4 animations - pounce, dash claws, dodges,
a horns-first ram, the storm call hover, the dive-chain bounce - and the per-frame hitbox regions the server places
the body parts with (export_boxes).

The entity moves itself (leaps, dashes, hops); these animations only pose the body for it, with the feet planted by IK
while they are on the ground and released while airborne.
"""
import math

import numpy as np

import anim_v4 as A
import rig_v4
from anim_v4 import Anim, wave
from dragon_v4_anims import (DISPLAY, FOLD, FOLD_LOOSE, LEGS, NECK, STAND, TAIL, add, blink, breathe, merge, path, plant_all,
                             smooth_window, tail_sway)
from dragon_v4_anims2 import (AIR, HOVER_BASE, LEGS_HANG, LOW_SPREAD, UP_V, WIDE, flap_layer, glow_pulse, jitter, rear,
                              tail_wave_air)

FRONT_REACH = {"arm_l": [-58, 0, -8], "forearm_l": [-14, 0, 0], "hand_l": [-28, 0, 0], "claws_l": [-45, 0, 0]}
HIND_PUSH = {"thigh_l": [42, 0, -3], "shin_l": [12, 0, 0], "meta_l": [24, 0, 0], "foot_l": [46, 0, 0]}
LEGS_TUCK_SOFT = {"arm_l": [26, 0, -10], "forearm_l": [-46, 0, 0], "hand_l": [34, 0, 0], "claws_l": [10, 0, 0],
                  "thigh_l": [22, 0, -4], "shin_l": [14, 0, 0], "meta_l": [12, 0, 0], "foot_l": [24, 0, 0]}


def window(t0, t1, t2, t3):
    """IK weight: 1 before t0, eases to 0 by t1, 0 until t2, eases back to 1 by t3 (feet leave and retake the ground)."""
    return lambda t: 1.0 - smooth_window(t, t0, t1, t2, t3)


def gallop(leg, t0, t1, cycles, stride, lift, phases):
    """Foot offset for a few galloping strides between t0 and t1 (feet sweep back while the body surges forward)."""
    L = (t1 - t0) / cycles
    duty = 0.42

    def off(t):
        if t <= t0 or t >= t1:
            return (0.0, 0.0, 0.0)
        fade = smooth_window(t, t0, t0 + 0.06, t1 - 0.06, t1)
        ph = ((t - t0) / L + phases[leg]) % 1.0
        if ph < duty:
            z = -stride / 2 + stride * ph / duty
            y = 0.0
        else:
            u = (ph - duty) / (1 - duty)
            z = stride / 2 - stride * A.ease("smooth", u)
            y = lift * math.sin(math.pi * u)
        return (0.0, y * fade, z * fade)
    return off


GALLOP = {"hl": 0.0, "hr": 0.1, "fl": 0.5, "fr": 0.6}


# --------------------------------------------------------------------------------------------- gap closers

def pounce():
    """Crouch, spring (0.38 s) with the forefeet reaching and the jaws opening, land on the prey forefeet first and
    snap (0.95 s). The entity flies the arc; the feet let go of the ground 0.42-0.86 s."""
    a = Anim("pounce", 1.6, False)
    crouch = add(STAND, {"body@pos": [0, -5.5, 3.5], "chest": [7, 0, 0], "hips": [-3, 0, 0], "neck1": [14, 0, 0], "neck2": [6, 0, 0], "neck3": [-2, 0, 0],
                         "head": [-12, 0, 0], "tail1": [10, 0, 0], "tail2": [5, 0, 0]})
    spring = merge(add(STAND, merge(rear(-20, 2.0), {"neck1": [-4, 0, 0], "neck3": [6, 0, 0], "head": [-8, 0, 0], "jaw": [18, 0, 0]})),
                   FRONT_REACH, HIND_PUSH, UP_V)
    soar = merge(add(STAND, {"body": [4, 0, 0], "body@pos": [0, 1.0, 0], "neck1": [4, 0, 0], "neck2": [4, 0, 0], "neck3": [2, 0, 0], "head": [-6, 0, 0],
                             "jaw": [40, 0, 0], "tail1": [6, 0, 0], "tail2": [4, 0, 0], "crest@scale": [1.1, 1.1, 1.1]}),
                 FRONT_REACH, {"arm_l": [-70, 0, -10]}, HIND_PUSH, WIDE)
    strike = merge(add(STAND, {"body@pos": [0, -4.5, -4], "chest": [9, 0, 0], "hips": [2, 0, 0], "neck1": [16, 0, 0], "neck2": [8, 0, 0], "neck3": [2, 0, 0],
                               "head": [-6, 0, 0], "jaw": [-2, 0, 0], "tail1": [6, 0, 0]}), LOW_SPREAD)
    a.seq([(0.0, STAND, "smooth"),
           (0.3, merge(crouch, FOLD_LOOSE), "out2"),
           (0.45, spring, "in2"),
           (0.72, soar, "out2"),
           (0.86, merge(soar, {"jaw": [44, 0, 0], "body": [8, 0, 0]}), "smooth"),
           (0.95, strike, "in"),
           (1.15, merge(add(STAND, {"body@pos": [0, -2.5, -2], "chest": [5, 0, 0], "neck1": [8, 0, 0], "head": [-2, 4, 0], "jaw": [6, 0, 0]}), LOW_SPREAD), "out2"),
           (1.6, STAND, "smooth")])
    a.lag(NECK, 0.03).lag(TAIL, 0.06)
    a.lag(["wing_l", "wing_l2", "wing_l3"], 0.03).lag(["wing_r", "wing_r2", "wing_r3"], 0.03)
    a.layer(tail_sway(1.6, 1.5, 0.4))
    land = path([(0.0, (0, 0, 0), "smooth"), (0.86, (0, 0, -10), "smooth"), (0.95, (0, 0, -10), "smooth"), (1.5, (0, 0, 0), "smooth")])
    for leg in ("fl", "fr"):
        a.plant(leg, (lambda t: land(t)) if leg == "fl" else (lambda t: (-land(t)[0], land(t)[1], land(t)[2])),
                weight=window(0.38, 0.48, 0.86, 0.95), foot=path([(0.0, 0, "smooth"), (0.3, 0, "smooth"), (0.95, 20, "in"), (1.3, 0, "smooth")]))
    for leg in ("hl", "hr"):
        a.plant(leg, weight=window(0.42, 0.52, 0.88, 1.0))
    a.events = {"leap": 0.38, "land": 0.95}
    return a


def dash_claw_left():
    """Surging two-stride dash (0.12-0.46 s, the entity rushes forward) that ends in a raking left forefoot (hit 0.6 s)."""
    a = Anim("dash_claw_left", 1.25, False)
    low = {"body@pos": [0, -3.0, -1.5], "chest": [6, 0, 0], "hips": [-2, 0, 0], "neck1": [6, 0, 0], "neck2": [4, 0, 0], "neck3": [2, 0, 0],
           "head": [-6, 0, 0], "jaw": [16, 0, 0], "tail1": [6, 0, 0], "tail2": [3, 0, 0]}
    up = {"body@pos": [0, 0.6, 0.8], "chest": [-7, -10, 4], "hips": [2, 0, 0], "neck1": [6, -12, 0], "neck2": [4, -6, 0], "neck3": [0, -4, 0],
          "head": [0, -10, 0], "jaw": [14, 0, 0]}
    strike = {"body@pos": [0, -1.4, -3.5], "chest": [6, 11, -4], "hips": [-1, 0, 0], "neck1": [14, 10, 0], "neck2": [6, 4, 0], "neck3": [2, 4, 0],
              "head": [8, 12, 0], "jaw": [28, 0, 0]}
    a.seq([(0.0, STAND, "smooth"),
           (0.12, add(STAND, {"body@pos": [0, -1.5, 2], "chest": [3, 0, 0], "neck1": [4, 0, 0]}), "out2"),
           (0.22, merge(add(STAND, low), FOLD), "in2"),
           (0.44, merge(add(STAND, low), FOLD), "smooth"),
           (0.52, add(STAND, up), "out2"),
           (0.62, add(STAND, strike), "in"),
           (0.82, add(STAND, merge(strike, {"chest": [3, 7, -2], "jaw": [6, 0, 0]})), "out2"),
           (1.25, STAND, "smooth")])
    a.lag(NECK, 0.03).lag(TAIL, 0.06)
    a.layer(lambda t: {"body@pos": [0, 1.2 * smooth_window(t, 0.14, 0.2, 0.4, 0.46) * math.sin(4 * math.pi * (t - 0.14) / 0.32), 0],
                       "body": [smooth_window(t, 0.14, 0.2, 0.4, 0.46) * wave(t - 0.14, 0.16, 3.0, 90), 0, 0]})
    a.layer(tail_sway(1.25, 2.0, 0.5))
    paw = path([(0.0, (0, 0, 0), "smooth"), (0.44, (0, 0, 0), "smooth"), (0.52, (16, 32, -18), "out2"), (0.58, (8, 18, -28), "in2"),
                (0.64, (-6, 4, -25), "out"), (0.82, (-3, 2, -16), "smooth"), (1.15, (0, 0, 0), "smooth")])
    run_fl = gallop("fl", 0.12, 0.46, 2, 30.0, 6.0, GALLOP)
    a.plant("fl", lambda t: tuple(paw(t)[k] + run_fl(t)[k] for k in range(3)),
            foot=path([(0.0, 0, "smooth"), (0.44, 0, "smooth"), (0.52, -55, "out2"), (0.62, 35, "in"), (0.9, 10, "smooth"), (1.15, 0, "smooth")]))
    for leg in ("fr", "hl", "hr"):
        a.plant(leg, gallop(leg, 0.12, 0.46, 2, 30.0, 6.0 if leg[0] == "f" else 5.0, GALLOP))
    a.layer(lambda t: {"claws_l!": [path([(0.0, 0, "smooth"), (0.46, 0, "smooth"), (0.52, -35, "out2"), (0.6, 40, "in"), (0.9, 0, "smooth")])(t), 0, 0]})
    a.events = {"dash": 0.12, "hit": 0.62}
    return a


def dodge_left():
    """A hop to its own left (+x): crouch, push off to the side (0.18 s), wings flicked open for balance, land (0.52 s)
    already turned back to the target."""
    a = Anim("dodge_left", 0.85, False)
    crouch = add(STAND, {"body@pos": [0, -4.0, 0], "body": [0, 0, 8], "chest": [4, 0, 0], "neck1": [6, -6, 0], "head": [-6, -8, 0]})
    air = merge(add(STAND, {"body@pos": [0, 1.5, 0], "body": [0, 0, -10], "neck1": [-2, 6, 0], "neck3": [0, 4, 0], "head": [-4, 10, 0], "jaw": [10, 0, 0],
                            "tail1": [0, -10, 0], "tail2": [0, -8, 0], "tail3": [0, -6, 0]}), LEGS_TUCK_SOFT, WIDE)
    land = merge(add(STAND, {"body@pos": [0, -3.0, 0], "body": [0, 0, 5], "chest": [4, 0, 0], "neck1": [6, 4, 0], "head": [-4, 6, 0], "jaw": [6, 0, 0],
                             "tail1": [0, 8, 0], "tail2": [0, 6, 0]}), LOW_SPREAD)
    a.seq([(0.0, STAND, "smooth"), (0.14, merge(crouch, FOLD_LOOSE), "out2"), (0.32, air, "out2"), (0.52, land, "in2"), (0.85, STAND, "smooth")])
    a.lag(NECK, 0.03).lag(TAIL, 0.05)
    a.lag(["wing_l", "wing_l2", "wing_l3"], 0.025).lag(["wing_r", "wing_r2", "wing_r3"], 0.025)
    w = window(0.17, 0.26, 0.46, 0.54)
    for leg in LEGS:
        a.plant(leg, weight=w)
    a.events = {"hop": 0.18, "land": 0.52}
    return a


def ram():
    """Horns-first charge (loop): head low and level so the horns and crest point forward, wings clamped, a long
    hammering gallop."""
    L = 0.6
    a = Anim("ram", L, True)
    pose = merge(add(STAND, {"neck1": [14, 0, 0], "neck2": [10, 0, 0], "neck3": [4, 0, 0], "neck4": [-6, 0, 0], "head": [-18, 0, 0],
                             "body@pos": [0, -2.5, 0], "chest": [6, 0, 0], "hips": [-2, 0, 0], "tail1": [8, 0, 0], "tail2": [4, 0, 0],
                             "crest@scale": [1.12, 1.12, 1.12]}), FOLD)
    a.key(0, pose).key(L, pose)
    A_legs = {"hl": 0.0, "hr": 0.12, "fl": 0.5, "fr": 0.62}
    from dragon_v4_anims2 import gait
    gait(a, L, 38.0, 0.4, A_legs, lift=7.0, hind_lift=6.0, toe=42.0)
    a.layer(lambda t: {"body@pos": [0, 1.6 * math.sin(4 * math.pi * t / L - 1.0), 0], "body": [wave(t, L, 4.0, 90), 0, 0],
                       "chest": [wave(t, L, -5.0, 60), 0, 0], "hips": [wave(t, L, 3.0, 60), 0, 0], "tail1": [wave(t, L, -2.5, 60), 0, 0],
                       "neck1": [wave(t, L, 3.0, 150), 0, 0], "head": [wave(t, L, -3.0, 180), 0, 0]})
    a.layer(tail_sway(L, 2.0, 0.5, 40, 180))
    a.lag(TAIL, 0.05)
    return a


# --------------------------------------------------------------------------------------------- sky skills

def storm():
    """Storm call (loop, 3.8 s): hanging high on huge beats, head thrown back, a roar into the clouds every loop while
    the core and crest blaze; the lightning itself is the server's."""
    L = 3.8
    a = Anim("storm", L, True)
    pose = merge(HOVER_BASE, {"body": [-30, 0, 0], "neck1": [-6, 0, 0], "neck2": [-4, 0, 0], "neck3": [8, 0, 0], "neck4": [2, 0, 0], "head": [-24, 0, 0],
                              "tail1": [14, 0, 0], "tail2": [6, 0, 0], "jaw": [10, 0, 0], "core@scale": [1.3, 1.3, 1.3], "crest@scale": [1.15, 1.15, 1.15]})
    a.key(0, pose).key(L, pose)
    a.layer(flap_layer(L / 2, 56, 1.0, 2.4)).layer(tail_wave_air(L / 2, 3.0))
    a.layer(lambda t: {"jaw": [34 * smooth_window(t, 0.6, 0.9, 2.0, 2.5), 0, 0], "head": [-8 * smooth_window(t, 0.6, 0.9, 2.0, 2.5), 0, 0],
                       "neck1": [wave(t, L / 2, -2.5, -40), 0, 0]})
    a.layer(jitter(1.0, ("head", "neck3"), 0.9, 2.0)).layer(glow_pulse(0.3, 1.25, 1.55))
    a.lag(NECK, 0.05)
    a.events = {"roar": 0.9}
    return a


def dive_bounce():
    """Between two dives of the dive chain: from the impact crouch straight back up on two big downbeats."""
    a = Anim("dive_bounce", 1.0, False)
    impact = merge(add(STAND, {"body@pos": [0, -6, 0], "chest": [8, 0, 0], "neck1": [20, 0, 0], "neck2": [8, 0, 0], "head": [-16, 0, 0], "jaw": [30, 0, 0]}),
                   LOW_SPREAD)
    a.seq([(0.0, impact, "smooth"),
           (0.25, merge(add(STAND, {"body@pos": [0, -5, 1], "chest": [6, 0, 0], "neck1": [10, 0, 0], "head": [-8, 0, 0]}), UP_V), "out2"),
           (0.42, merge(add(AIR, {"body": [-26, 0, 0], "body@pos": [0, 4, 0], "neck1": [-10, 0, 0], "head": [6, 0, 0]}), LEGS_HANG,
                        {"wing_l": [-6, -8, 36], "wing_l2": [0, -4, -8], "wing_l3": [0, 6, -12]}), "in2"),
           (0.72, merge(add(AIR, {"body": [-14, 0, 0], "body@pos": [0, 2, 0]}), {"wing_l": [6, 10, -42], "wing_l2": [0, 22, 14], "wing_l3": [0, -30, 18],
                                                                              "finger_l2": [0, 10, 0], "finger_l3": [0, 20, 0]}), "smooth"),
           (1.0, merge(AIR, {"body": [-4, 0, 0], "wing_l": [-4, -6, 30], "wing_l2": [0, -4, -6], "wing_l3": [0, 6, -10]}), "in2")])
    a.lag(NECK, 0.05).lag(TAIL, 0.07)
    a.lag(["wing_l", "wing_l2", "wing_l3"], 0.03).lag(["wing_r", "wing_r2", "wing_r3"], 0.03)
    w = lambda t: 1.0 - smooth_window(t, 0.3, 0.45, 9, 10)
    a.plant("fl", lambda t: (3.0, 0.0, -4.0), weight=w)
    a.plant("fr", lambda t: (-3.0, 0.0, -4.0), weight=w)
    a.plant("hl", lambda t: (2.0, 0.0, 2.0), weight=w)
    a.plant("hr", lambda t: (-2.0, 0.0, 2.0), weight=w)
    a.events = {"leap": 0.35}
    return a


ANIMS5 = [pounce, dash_claw_left, dodge_left, ram, storm, dive_bounce]
MIRRORED5 = {"dash_claw_left": "dash_claw_right", "dodge_left": "dodge_right"}


# --------------------------------------------------------------------------------------------- hitbox regions

# body regions of the multipart hitbox, by bone (cubes of the phase-two growth, fins, horns and crest are left out)
REGIONS = [
    ("head", ("headc", "jaw", "lid_l", "lid_r")),
    ("neck_a", ("neck1c", "neck2c")), ("neck_b", ("neck3c", "neck4c")),
    ("chest", ("ribs", "chest", "core")), ("hips", ("hips",)),
    ("leg_fl", ("arm_l", "forearm_l", "hand_l", "claws_l")), ("leg_fr", ("arm_r", "forearm_r", "hand_r", "claws_r")),
    ("leg_hl", ("thigh_l", "shin_l", "meta_l", "foot_l")), ("leg_hr", ("thigh_r", "shin_r", "meta_r", "foot_r")),
    ("tail_a", ("tail1c", "tail2c")), ("tail_b", ("tail3c", "tail4c")), ("tail_c", ("tail5c", "tail6c")), ("tail_d", ("tail7c", "tail8c")),
    ("wing_l_in", ("wing_l", "wing_l2", "memb_l0")), ("wing_l_out", ("wing_l3", "finger_l", "memb_l1", "memb_l2", "memb_l3")),
    ("wing_r_in", ("wing_r", "wing_r2", "memb_r0")), ("wing_r_out", ("wing_r3", "finger_r", "memb_r1", "memb_r2", "memb_r3")),
]
SKIP = ("fin_", "oc_", "crest", "horn", "frill", "teeth", "eye", "fang", "nostril", "lid", "tongue", "palate", "floor")


def region_of(bone):
    for name, prefixes in REGIONS:
        for p in prefixes:
            if bone == p or (p.startswith(("memb_", "finger_")) and bone.startswith(p)):
                return name
    return None


def box_corners(dragon):
    """Per region: (bone, 8 corner points in the bone's cube frame) for every cube that counts."""
    out = {name: [] for name, _ in REGIONS}
    for c in dragon.cubes:
        if c.name.startswith(SKIP) or any(s in c.name for s in ("_socket", "eye_trail")):
            continue
        reg = region_of(c.bone)
        if reg is None:
            continue
        cm = rig_v4.cube_matrix({"rotation": c.rotation, "pivot": c.pivot or [c.origin[i] + c.size[i] / 2 for i in range(3)]})
        o, s = c.origin, c.size
        pts = [cm @ np.array([o[0] + s[0] * dx, o[1] + s[1] * dy, o[2] + s[2] * dz, 1.0]) for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]
        out[reg].append((c.bone, np.array(pts).T))
    return out


def export_boxes(dragon, data):
    """Per-tick model-space AABB (centre, half size; px) of every region for every animation."""
    skel = rig_v4.Skeleton(dragon.bones)
    corners = box_corners(dragon)
    out = {"regions": [n for n, _ in REGIONS], "animations": {}}
    for key, anim in data["animations"].items():
        L = anim["animation_length"]
        n = max(1, int(round(L * 20)))
        frames = []
        for i in range(n + 1):
            w = skel.world(rig_v4.sample_anim(anim, min(L, i / 20.0)))
            row = []
            for name, _ in REGIONS:
                pts = np.concatenate([(w[b] @ p)[:3] for b, p in corners[name]], axis=1)
                lo, hi = pts.min(axis=1), pts.max(axis=1)
                c, h = (lo + hi) / 2, (hi - lo) / 2
                row.extend([round(float(v), 1) for v in (c[0], c[1], c[2], h[0], h[1], h[2])])
            frames.append(row)
        out["animations"][key] = frames
    return out


def add_to(anims, events, rig):
    for fn in ANIMS5:
        a = fn()
        anims[a.name] = A.bake(rig, a)
        events[a.name] = dict(a.events, length=a.length, loop=a.loop)
        if a.name in MIRRORED5:
            m = a.mirrored(MIRRORED5[a.name])
            anims[m.name] = A.bake(rig, m)
            events[m.name] = dict(a.events, length=a.length, loop=a.loop)
