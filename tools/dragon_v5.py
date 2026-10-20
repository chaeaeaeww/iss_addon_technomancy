"""
Tech Dragon v5 (1.7): the model rebuilt in the way Saint's Dragons builds its dragons (studied, nothing copied):
few large, heavily overlapping tapered boxes for the neck, body and tail so they stay continuous when they bend,
dorsal spines / crest / frills / teeth as single painted planes with alpha (not dozens of little sticks), armour as a
few thin plates flush with the body, and the detail in the texture.

The skeleton (bone names and pivots) is the v4 one, so the animation tools (leg IK, fan-sliced wing membranes,
follow-through) and every animation keep working.

Phase two ("overcharge", Godzilla style): a second texture/glowmask pair lights hextech veins across the scales and
the whole dorsal fin row, and extra glowing crystal fins grow out of the neck, back and tail (bones "oc_*", scaled
from 0 to 1 by TechDragonModel when the dragon is in phase two).
"""
import math

import numpy as np
from PIL import Image

import dragon_v4 as V4
import rig_v4
from dragon_v4 import (BELLY, BLUE, BRONZE, CLAW, CLEAR, GOLD, HIDE, LIGHT, MOUTH, TEETH, Ctx, Dragon, FACE_N, S, E, W, TAIL_N, TAIL_LEN, TAIL_Y,
                       body_axis, face_size, finger_rest, glow, h01, local_point, mirror_name, tail_z)
from pixelart import rgb, ramp

CYAN = [rgb("0A3A70"), rgb("1670C8"), rgb("38B4FF"), rgb("8AE0FF"), rgb("D8F8FF"), rgb("FFFFFF")]
NECK5 = [(30.0, -36.0, 15.0, 14.5), (31.0, -48.0, 12.6, 12.4), (32.0, -60.0, 10.8, 10.8), (33.0, -72.0, 9.4, 9.6)]
TAIL_W5 = (16, 13.8, 11.8, 10.0, 8.4, 7.0, 5.8, 4.6)
TAIL_H5 = (15, 13.0, 11.2, 9.6, 8.2, 6.8, 5.6, 4.6)
OC_BONES = []
SEAT = (0.0, 42.0, -25.0)   # rider's seat on the drake (model px), between the wing roots, in the gap of the dorsal fins
EYE_H = 3.2    # eye height = how far the lid drops to blink ("lid_l@pos" y -3.2 in the animations)
EYE_YAW = 8.0  # the eye's front end turned outward (degrees)
OC_X = 0.35   # phase-two fins: a pair of planes either side of the normal fin (no z-fighting with it)


def tri(v):
    """(color) or (color, glow) or (color, glow, glow2) -> normalised triple."""
    if isinstance(v, tuple) and len(v) == 3 and isinstance(v[0], tuple):
        return v
    if isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], tuple):
        return (v[0], v[1], v[1])
    return (v, None, None)


class Paints5(V4.Paints):
    """v4 painters plus planes (fins, teeth, frills, crystal fans), thin armour and the phase-two vein channel."""

    # ---- hide with hextech veins: engraved in phase one, glowing (glow2) in phase two
    def hide(self, x):
        base = super().hide(x)
        p = x.p
        cy, rh = body_axis(p)
        hv = (p[1] - cy) / max(3.0, rh)
        if hv < -0.35 or x.face == "down":
            return base
        armour = self.dorsal_armour(x, hv, rh)
        if armour is not None:
            return armour
        a = math.sin(p[2] * 0.33 + 2.1 * math.sin(p[1] * 0.27 + p[0] * 0.19))
        b = math.sin(p[1] * 0.61 - p[2] * 0.13 + 1.3 * math.sin(p[0] * 0.4))
        v = abs(a + 0.45 * b)
        if v < 0.07:
            return (mix(base, CYAN[1], 0.25), None, CYAN[3])
        if v < 0.13:
            return (base, None, CYAN[1])
        return base

    # ---- 1.10: hextech armour along the back - overlapping brass-brown scale plates with gold rims down the sides of the
    # spine, a row of sapphire hextech scales on the ridge itself (they light up in phase two)
    def dorsal_armour(self, x, hv, rh):
        p = x.p
        rotated = x.cube.rotation is not None and abs(x.cube.rotation[0]) + abs(x.cube.rotation[1]) > 20
        if rotated or hv < 0.62 and x.face != "up":
            return None
        half = max(2.2, min(6.5, rh * 0.62))
        if abs(p[0]) > half:
            return None
        s = 3.2
        row = math.floor(p[2] / s)
        xx = (p[0] + (1.6 if row % 2 else 0.0)) / s
        col = math.floor(xx)
        fu, fv = xx - col, p[2] / s - row
        # a scale: rounded, overlapping toward the tail (+z); its free rear edge is the rim
        d = ((fu - 0.5) * 1.25) ** 2 + (fv * 0.85) ** 2
        rim = fv > 0.78 or d > 0.62
        lit = LIGHT.get(x.face, 0.8)
        ridge = abs(p[0]) < 1.7
        if ridge:
            if rim:
                return (GOLD[2], None, None)
            t = 0.2 + 0.32 * (1 - fv) + (h01(row, 7) - 0.5) * 0.08
            return (ramp(BLUE, t * lit), None, ramp(CYAN, 0.45 + 0.3 * (1 - fv)))
        if rim:
            return GOLD[1] if fv > 0.9 else GOLD[3]
        t = 0.34 + 0.3 * (1 - fv) * lit + (h01(row, col) - 0.5) * 0.08 - 0.12 * abs(p[0]) / half
        return ramp(BRONZE, t)

    # ---- thin armour plate: bronze, a one-texel gold edge, a fine glowing hextech line
    def thin(self, key, line=True):
        seed = h01(sum(ord(c) for c in key), 5)

        def fn(x):
            i, j, w, h, face = x.i, x.j, x.w, x.h, x.face
            b = min(i, j, w - 1 - i, h - 1 - j)
            lit = LIGHT[face]
            t = 0.5 + 0.16 * (1 - j / max(1, h - 1)) - (0.25 if face == "down" else 0)
            if b == 0:
                return GOLD[3] if j < h / 2 else GOLD[1]
            if line and min(w, h) >= 8 and face not in ("down",):
                if (w >= h and abs(j - (h - 1) / 2) < 0.6 and 2 <= i < w - 2) or (h > w and abs(i - (w - 1) / 2) < 0.6 and 2 <= j < h - 2):
                    return (CYAN[2], CYAN[2], CYAN[4])
            if b == 1:
                return ramp(BRONZE, (t - 0.18) * lit)
            t += (h01(x.p[0] * 3, x.p[1] * 3, x.p[2] * 3) - 0.5) * 0.06 + (seed - 0.5) * 0.05
            return ramp(BRONZE, t * lit / 0.9)
        return fn

    # ---- dorsal fin row (plane): swept-back spikes, dark scaled base, crystal tips that glow
    def fin(self, spikes, crystal=0.45, oc=False):
        def fn(x):
            if x.face not in ("east", "west"):
                return CLEAR
            u = x.i / max(1, x.w - 1)
            if x.face == "west":
                u = 1 - u
            v = 1 - x.j / max(1, x.h - 1)
            s = (u * spikes) % 1.0
            k = math.floor(u * spikes)
            peak = 0.82 + 0.18 * h01(k, 3)
            # swept-back spike: long rising leading edge, the tip near the back, a short steep trailing edge
            prof = peak * ((s / 0.74) ** 1.35 if s < 0.74 else max(0.0, 1 - (s - 0.74) / 0.26))
            prof = max(prof, 0.12)
            if v > prof:
                return CLEAR
            edge = prof - v < 0.07
            if oc:
                q = v / max(0.01, prof)
                t = 0.35 + 0.42 * q + (0.18 if edge else 0)
                return glow(ramp(CYAN, t), ramp(CYAN, t * 0.9))
            q = v / max(0.01, prof)
            if q > 1 - crystal:
                # phase one: a dark sapphire tip, faintly lit; phase two: the whole tip blazes
                t = 0.18 + 0.3 * (q - (1 - crystal)) / crystal + (0.12 if edge else 0)
                return (ramp(BLUE, t), ramp(BLUE, t * 0.7) if edge else None, ramp(CYAN, 0.55 + 0.4 * q))
            if edge:
                return (GOLD[3], None, ramp(CYAN, 0.5))
            if q > 1 - crystal - 0.2:
                # 1.10: a band of blue hextech scales under the crystal tip
                t = 0.2 + 0.25 * (q - (1 - crystal - 0.2)) / 0.2
                return (ramp(BLUE, t), None, ramp(CYAN, 0.35 + 0.3 * q))
            t = 0.3 + 0.3 * q + (h01(k, x.j // 2) - 0.5) * 0.08
            return ramp(BRONZE, t) if (x.j // 2) % 3 else ramp(GOLD, 0.25 + 0.2 * q)
        return fn

    # ---- tooth row (plane facing out): triangular teeth, tips down (upper) or up (lower)
    def teeth_plane(self, down=True, size=4):
        def fn(x):
            u = x.i % size / max(1, size - 1)
            v = x.j / max(1, x.h - 1) if down else 1 - x.j / max(1, x.h - 1)
            # v = 0 at the gum, 1 at the tip
            if v > 1 - abs(u - 0.5) * 2 * 0.9:
                return CLEAR
            return ramp(TEETH, 0.9 - 0.45 * v + (0.08 if u < 0.5 else 0))
        return fn

    # ---- cheek frill (plane): spines fanning back with dark membrane between, crystal tips
    def frill(self, x):
        if x.face not in ("east", "west"):
            return CLEAR
        u = x.i / max(1, x.w - 1)
        if x.face == "west":
            u = 1 - u
        v = 1 - x.j / max(1, x.h - 1)
        top = 0.35 + 0.65 * u
        if v > top or u < 0.04:
            return CLEAR
        spine = abs(((v / max(0.05, top)) * 4) % 1.0 - 0.5) < 0.12
        if spine:
            return ramp(BRONZE, 0.5 + 0.2 * u)
        if top - v < 0.06:
            return glow(CYAN[3], CYAN[2])
        return ramp(HIDE, 0.18 + 0.12 * v)

    # ---- crystal fan (plane): a few long blades swept back from the base
    def crystal_fan(self, blades):
        def fn(x):
            if x.face not in ("east", "west"):
                return CLEAR
            u = x.i / max(1, x.w - 1)
            if x.face == "west":
                u = 1 - u
            v = 1 - x.j / max(1, x.h - 1)
            for k, (base_u, length, width) in enumerate(blades):
                # blade from (base_u, 0) leaning back toward (base_u + length * 0.8, 1)
                cu = base_u + v * length
                half = width * (1 - v) + 0.01
                if abs(u - cu) < half:
                    edge = half - abs(u - cu) < 0.025
                    lit = u < cu
                    t = 0.3 + 0.4 * v + (0.18 if lit else 0) + (0.15 if edge else 0)
                    return (ramp(BLUE, t), ramp(BLUE, t * 0.85), ramp(CYAN, min(0.95, t + 0.15)))
            return CLEAR
        return fn

    # ---- tail blade (plane): arrow-shaped crystal blade with a bronze spine
    def blade(self, horizontal=False):
        def fn(x):
            if horizontal:
                if x.face not in ("up", "down"):
                    return CLEAR
                u = 1 - x.j / max(1, x.h - 1)          # 0 at the root (front), 1 at the point (back)
                c = (x.i - (x.w - 1) / 2) / max(1, x.w / 2)
            else:
                if x.face not in ("east", "west"):
                    return CLEAR
                u = x.i / max(1, x.w - 1)
                if x.face == "west":
                    u = 1 - u
                c = (x.j - (x.h - 1) / 2) / max(1, x.h / 2)
            width = (u / 0.3) if u < 0.3 else max(0.0, 1 - (u - 0.3) / 0.7)
            if abs(c) > width:
                return CLEAR
            if abs(c) < 0.08:
                return ramp(BRONZE, 0.55)
            t = 0.4 + 0.5 * (1 - abs(c) / max(0.05, width))
            if width - abs(c) < 0.1:
                t = 1.0
            return glow(ramp(CYAN, t), ramp(CYAN, t * 0.9))
        return fn

    # ---- eye (1.8): reptile slit eye, glowing; phase two burns white-cyan
    def eye5(self, x):
        if x.face == "west":
            return rgb("05061A")
        if x.face == "east":
            cx, cy = (x.w - 1) * 0.5, (x.h - 1) * 0.5
            dx, dy = (x.i - cx) / max(1.0, x.w / 2), (x.j - cy) / max(1.0, x.h / 2)
            # almond: pointed at both ends, a little fuller toward the front (dx < 0 is the front end)
            half = 1.0 - (dx * dx) * (0.75 if dx > 0 else 0.6)
            if abs(dy) > half or abs(dx) > 0.97:
                return (rgb("05061A"), None, rgb("0A3A70"))
            r = math.hypot(dx * 0.9, dy / max(0.3, half))
            if abs(dx + 0.08) < 0.1 + 0.05 * (1 - abs(dy)) and abs(dy) < 0.86 * half:
                return (rgb("020818"), rgb("041030"), rgb("0A2050"))        # slit pupil
            if -0.6 < dx < -0.42 and -0.7 * half < dy < -0.4 * half:
                return (rgb("FFFFFF"), rgb("FFFFFF"), rgb("FFFFFF"))        # glint
            if abs(dy) > half - 0.22:
                return (ramp(BLUE, 0.62), ramp(BLUE, 0.6), ramp(CYAN, 0.36))  # dark-blue rim of the iris
            t = 0.8 - 0.34 * r
            # phase two: saturated electric cyan (not washed-out white), brightest around the pupil
            return (ramp(CYAN, t), ramp(CYAN, t), ramp(CYAN, 0.66 - 0.24 * r))
        if x.face == "north":
            return (ramp(CYAN, 0.75), ramp(CYAN, 0.7), CYAN[5])
        return (ramp(BLUE, 0.45), ramp(BLUE, 0.4), ramp(CYAN, 0.6))

    # ---- eye socket (plane on the snout): a dark recess around the eye, soft edge
    def socket5(self, x):
        cx, cy = (x.w - 1) / 2, (x.h - 1) / 2
        d = math.hypot((x.i - cx) / max(1.0, x.w / 2), (x.j - cy) / max(1.0, x.h / 2))
        if d > 1.0:
            return CLEAR
        if d > 0.86:
            return ramp(HIDE, 0.16)
        return rgb("070818") if d < 0.7 else ramp(HIDE, 0.06)

    # ---- hex scale plate (phase two growth on the flanks)
    def hexplate(self, x):
        if x.face not in ("east", "west"):
            return CLEAR
        hx = x.p[2] / 2.2
        hy = x.p[1] / 1.9 + (0.5 if math.floor(hx) % 2 else 0)
        fu, fv = hx % 1.0, hy % 1.0
        d = max(abs(fu - 0.5) * 1.15 + abs(fv - 0.5) * 0.6, abs(fv - 0.5) * 1.2)
        if d > 0.55:
            return CLEAR
        if d > 0.45:
            return glow(CYAN[4], CYAN[4])
        return glow(ramp(CYAN, 0.55 + 0.2 * h01(math.floor(hx), math.floor(hy))), ramp(CYAN, 0.5))


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


# --------------------------------------------------------------------------------------------- skeleton

def build_dragon():
    D = Dragon()
    P = Paints5()
    bone = D.bone
    bone("root", None, [0, 0, 0])
    bone("flight", "root", [0, 27, -10])
    bone("body", "flight", [0, 27, -10])
    bone("chest", "body", [0, 28, -8])
    bone("hips", "body", [0, 28, -4])
    bone("ribs", "chest", [0, 28, -26])
    bone("core", "chest", [0, 20.4, -43.6])
    bone("saddle", "chest", [0, 44, -30])
    parent = "chest"
    for k, (py, pz, w, h) in enumerate(NECK5):
        bone("neck%d" % (k + 1), parent, [0, py, pz])
        bone("neck%dc" % (k + 1), "neck%d" % (k + 1), [0, py, pz])
        parent = "neck%dc" % (k + 1)
    bone("head", parent, [0, 34, -84])
    bone("headc", "head", [0, 34, -84])
    bone("jaw", "headc", [0, 31, -92])
    bone("crest", "headc", [0, 41, -96])
    bone("mouth", "headc", [0, 30, -117])
    bone("lid_l", "headc", [5.4, 37.0, -106])
    bone("lid_r", "headc", [-5.4, 37.0, -106])
    for s, sg in (("l", 1), ("r", -1)):
        bone("arm_" + s, "chest", [sg * 11, 27, -28])
        bone("forearm_" + s, "arm_" + s, [sg * 12.5, 15, -24])
        bone("hand_" + s, "forearm_" + s, [sg * 12.5, 4.5, -28])
        bone("claws_" + s, "hand_" + s, [sg * 12.5, 1.5, -35])
        bone("thigh_" + s, "hips", [sg * 10.5, 27, 8])
        bone("shin_" + s, "thigh_" + s, [sg * 12, 14, 2])
        bone("meta_" + s, "shin_" + s, [sg * 12, 6.5, 13])
        bone("foot_" + s, "meta_" + s, [sg * 12, 1.8, 9])
        bone("wing_" + s, "chest", [sg * S[0], S[1], S[2]])
        bone("wing_%s2" % s, "wing_" + s, [sg * E[0], E[1], E[2]])
        bone("wing_%s3" % s, "wing_%s2" % s, [sg * W[0], W[1], W[2]])
        for k in range(3):
            ang, _ = finger_rest(k)
            bone("finger_%s%d" % (s, k + 1), "wing_%s3" % s, [sg * W[0], W[1], W[2]], [0, sg * ang, 0])
    parent = "hips"
    for n in range(TAIL_N):
        z = tail_z(n)
        bone("tail%d" % (n + 1), parent, [0, TAIL_Y[n], z])
        bone("tail%dc" % (n + 1), "tail%d" % (n + 1), [0, TAIL_Y[n], z])
        parent = "tail%dc" % (n + 1)
    bone("tail_tip", parent, [0, TAIL_Y[-1], tail_z(TAIL_N) + 6])
    # phase-two growth bones (scaled 0 -> 1 by the client model)
    OC_BONES.clear()
    for par in ["neck%dc" % (k + 1) for k in range(4)] + ["ribs", "chest", "hips"] + ["tail%dc" % (n + 1) for n in range(6)]:
        name = "oc_" + par
        piv = [b[2] for b in D.bones if b[0] == par][0]
        bone(name, par, piv)
        OC_BONES.append(name)

    torso(D, P)
    neck_and_head(D, P)
    legs(D, P)
    tail(D, P)
    V4.wing(D, P)
    overcharge(D, P)
    D.paints = P
    return D


# --------------------------------------------------------------------------------------------- parts

def plane_x(D, bone, x, y0, z0, h, d, paint, name, rot=None, pivot=None, mirror=False):
    """Vertical plane at x (painted east face; the renderer draws both sides)."""
    c = D.cube(bone, [x, y0, z0], [0, h, d], paint, name, faces=("east",), rotation=rot, pivot=pivot)
    if mirror:
        D.mirror(c)
    return c


def torso(D, P):
    c = D.cube
    c("ribs", [-10.5, 17.5, -41], [21, 22, 28], P.hide, "chest_box")
    c("ribs", [-8, 39.5, -38], [16, 1.8, 22], P.hide, "withers")
    c("ribs", [-8.5, 19.0, -43.2], [17, 18, 2.4], P.hide, "chest_front")
    c("ribs", [-7.5, 16.2, -38], [15, 1.6, 24], P.belly, "sternum", faces=("down", "east", "west", "north", "south"))
    c("chest", [-9, 20, -16], [18, 18, 21], P.hide, "waist")
    c("chest", [-6.5, 18.6, -15], [13, 1.6, 19], P.belly, "waist_belly", faces=("down", "east", "west", "north", "south"))
    # a gap in the dorsal row over the shoulders, where the rider of the summoned dragon sits (SEAT)
    plane_x(D, "chest", 0, 40.5, -43, 9.5, 11, P.fin(2), "fin_chest")
    plane_x(D, "chest", 0, 37.4, -14, 7, 18, P.fin(3), "fin_waist")
    # hextech core in a thin bronze ring on the chest
    c("chest", [-4.4, 15.8, -44.2], [8.8, 9.4, 0.9], P.thin("core_ring", line=False), "core_ring")
    c("core", [-3.0, 17.4, -44.9], [6.0, 6.0, 1.4], P.core, "core_gem", rotation=[0, 0, 45], pivot=[0, 20.4, -44.2])
    # thin shoulder and hip armour
    D.sym("chest", [10.3, 26.0, -37], [1.2, 10, 12], P.thin("shoulder"), "shoulder_plate", rotation=[0, 0, -12], pivot=[11, 31, -30])
    h = "hips"
    c(h, [-10, 21, -2], [20, 17, 21], P.hide, "pelvis")
    c(h, [-8.5, 22, 17.5], [17, 14.5, 4], P.hide, "rump")
    c(h, [-7, 19.6, -1], [14, 1.6, 18], P.belly, "hip_belly", faces=("down", "east", "west", "north", "south"))
    plane_x(D, h, 0, 38.0, 0, 7.5, 19, P.fin(3), "fin_hips")
    D.sym(h, [10.2, 24, 2.5], [1.2, 11, 14], P.thin("hip"), "hip_plate", rotation=[0, 0, -6], pivot=[11, 30, 10])


def neck_and_head(D, P):
    c = D.cube
    for k, (py, pz, w, h) in enumerate(NECK5):
        b = "neck%dc" % (k + 1)
        y0 = py + 0.5 - h / 2
        c(b, [-w / 2, y0, pz - 15], [w, h, 20], P.hide, "neck%d" % k)
        c(b, [-w / 2 + 1.4, y0 - 1.0, pz - 14], [w - 2.8, 1.4, 18], P.belly, "throat%d" % k, faces=("down", "east", "west", "north", "south"))
        plane_x(D, b, 0, y0 + h - 0.8, pz - 14, 7 - k, 18, P.fin(3), "fin_neck%d" % k)
    hb = "headc"
    c(hb, [-6.4, 29.6, -99], [12.8, 10.4, 16], P.hide, "cranium")
    c(hb, [-7.4, 29.6, -97.5], [14.8, 6.2, 11], P.hide, "cheeks")
    c(hb, [-5.0, 30.0, -111], [10.0, 7.8, 13], P.hide, "snout1")
    c(hb, [-4.0, 30.0, -121], [8.0, 6.4, 11], P.hide, "snout2")
    c(hb, [-3.4, 30.4, -122.2], [6.8, 5.2, 1.4], P.hide, "nose")
    c(hb, [-4.4, 29.7, -110.8], [8.8, 0.4, 12.6], P.mouth, "palate1", faces=("down",))
    c(hb, [-3.4, 29.7, -120.8], [6.8, 0.4, 10.6], P.mouth, "palate2", faces=("down",))
    D.seg(hb, [0, 40.6, -98.0], [0, 37.0, -121.6], 6.4, 1.0, P.thin("snout_plate"), "snout_plate")
    D.seg(hb, [4.6, 38.6, -109.5], [5.8, 41.2, -97.0], 3.2, 2.6, P.hide, "brow", extend=(0.4, 0.6), mirror=True)
    # eye (1.8): a big glowing slit eye on the side of the snout, its front end turned out (EYE_YAW) so it also
    # reads from the front, sitting in a dark socket; the lid rests above it and drops EYE_H to blink
    eye_rot, eye_piv = [0, EYE_YAW, 0], [5.0, 35.4, -102.2]
    D.sym(hb, [5.08, 32.9, -111.0], [0, 5.0, 9.6], P.socket5, "eye_socket", faces=("east",))
    D.sym(hb, [4.6, 37.0 - EYE_H, -109.8], [1.5, EYE_H, 7.6], P.eye5, "eye", rotation=eye_rot, pivot=eye_piv)
    D.sym(hb, [5.0, 35.5, -102.6], [0.7, 0.9, 5.4], P.eye_trail, "eye_trail", faces=("east", "up", "south"))
    # the lid stands out past the eye's surface (x 6.1) so it covers it when it drops; open, it sits above the eye
    D.cube("lid_l", [4.6, 37.0, -110.0], [1.85, EYE_H, 7.9], P.lid, "lid", rotation=eye_rot, pivot=eye_piv)
    D.mirror(D.cubes[-1], "lid_r")
    D.sym(hb, [1.8, 35.0, -122.4], [1.2, 0.9, 0.4], P.nostril, "nostril", faces=("north", "up"))
    # teeth rows, fangs
    plane_x(D, hb, 4.9, 27.6, -110.6, 2.4, 12.2, P.teeth_plane(True), "teeth_up1", mirror=True)
    plane_x(D, hb, 3.9, 27.9, -120.6, 2.1, 10.0, P.teeth_plane(True), "teeth_up2", mirror=True)
    c(hb, [-3.3, 28.0, -121.2], [6.6, 2.0, 0], P.teeth_plane(True), "teeth_front", faces=("north",))
    D.sym(hb, [3.4, 26.3, -112.2], [1.1, 3.8, 1.1], P.fang, "fang", rotation=[-6, 0, 0], pivot=[4, 29.5, -111.6])
    # cheek frills, horns, crystal crown
    plane_x(D, hb, 7.3, 28.5, -95, 8.5, 13.5, P.frill, "frill", rot=[0, -22, 0], pivot=[7.3, 32, -95], mirror=True)
    pts = [(4.2, 39.6, -92.0), (7.2, 43.2, -81.0), (8.8, 45.2, -70.0), (9.4, 48.4, -61.0), (9.2, 52.4, -55.0)]
    for k, wdt in enumerate((3.2, 2.7, 2.1, 1.5)):
        D.seg(hb, pts[k], pts[k + 1], wdt, wdt, P.horn(k), "horn%d" % k, extend=(0.8, 0.4), mirror=True)
    plane_x(D, "crest", 0, 39.6, -104, 15, 26, P.crystal_fan([(0.1, 0.55, 0.1), (0.36, 0.48, 0.11), (0.6, 0.36, 0.09)]), "crest_main")
    plane_x(D, "crest", 2.6, 39.6, -101, 11, 20, P.crystal_fan([(0.15, 0.5, 0.11), (0.5, 0.4, 0.1)]), "crest_side",
            rot=[0, -14, 0], pivot=[2.6, 40, -101], mirror=True)
    # jaw
    j = "jaw"
    c(j, [-6.0, 25.6, -97.5], [12, 5, 11.5], P.hide, "jaw_rear")
    c(j, [-4.8, 26.0, -110.5], [9.6, 4.0, 13.5], P.hide, "jaw1")
    c(j, [-3.8, 26.4, -121.0], [7.6, 3.6, 11], P.hide, "jaw2")
    c(j, [-4.2, 29.6, -110.2], [8.4, 0.4, 12.8], P.mouth, "floor1", faces=("up",))
    c(j, [-3.2, 29.6, -120.6], [6.4, 0.4, 10.4], P.mouth, "floor2", faces=("up",))
    c(j, [-2.4, 29.8, -117], [4.8, 0.8, 18], P.tongue, "tongue", faces=("up", "north", "east", "west"))
    plane_x(D, j, 4.5, 30.0, -110.2, 1.9, 12.0, P.teeth_plane(False), "teeth_low1", mirror=True)
    plane_x(D, j, 3.5, 30.0, -120.4, 1.7, 10.0, P.teeth_plane(False), "teeth_low2", mirror=True)
    D.seg(j, [0, 25.8, -97.0], [0, 26.6, -121.0], 7.0, 0.9, P.thin("chin", line=False), "jaw_plate")
    D.sym(j, [2.9, 30, -111.0], [1.0, 2.8, 1.0], P.fang, "fang_low")


def legs(D, P):
    s = "_l"
    D.seg("arm" + s, (11.0, 28.0, -28.5), (12.5, 15.0, -24.5), 8.2, 9.2, P.hide, "upper_arm", extend=(2, 1.5), mirror=True)
    D.sym("arm" + s, [7.8, 21, -34], [8.4, 11, 11], P.hide, "deltoid")
    D.seg("forearm" + s, (12.5, 15.0, -24.0), (12.5, 4.5, -28.0), 6.2, 6.8, P.hide, "foreleg", extend=(1.5, 1), mirror=True)
    D.seg("forearm" + s, (12.5, 13.0, -27.8), (12.5, 6.4, -30.3), 6.4, 1.0, P.thin("greave"), "greave", mirror=True)
    D.sym("hand" + s, [9, 0, -35], [7, 4.6, 9.5], P.hide, "palm")
    D.sym("hand" + s, [8.2, 0.4, -29.5], [1.8, 2.4, 3.5], P.claw, "dewclaw")
    for k, x in enumerate((9.2, 11.6, 14.0)):
        D.sym("claws" + s, [x, 0, -38], [2.0, 2.8, 3.6], P.hide, "finger%d" % k)
        D.seg("claws" + s, (x + 1.0, 1.6, -37.6), (x + 1.0, 0.2, -41.6), 1.6, 1.8, P.claw, "talon%d" % k, extend=(0, 0.3), mirror=True)
    D.sym("thigh" + s, [6.6, 16.5, -1.5], [9.8, 14, 16], P.hide, "haunch", rotation=[-10, 0, 0], pivot=[10.5, 27, 8])
    D.seg("thigh" + s, (10.5, 27.0, 8.0), (12.0, 14.0, 2.0), 8.4, 10.2, P.hide, "thigh", extend=(2, 1.5), mirror=True)
    D.seg("shin" + s, (12.0, 14.0, 2.0), (12.0, 6.5, 13.0), 5.6, 6.2, P.hide, "shin", extend=(1.5, 1.2), mirror=True)
    D.seg("shin" + s, (12.0, 13.0, 0.9), (12.0, 8.4, 7.9), 6.0, 0.9, P.thin("knee", line=False), "knee_plate", mirror=True)
    D.seg("meta" + s, (12.0, 6.5, 13.0), (12.0, 1.8, 9.0), 4.6, 4.6, P.hide, "meta", extend=(1.2, 1.0), mirror=True)
    D.seg("meta" + s, (12.0, 7.4, 15.0), (12.0, 10.8, 19.4), 1.6, 1.6, P.claw, "heel_spur", mirror=True)
    D.sym("foot" + s, [9, 0, 2], [6.6, 3.4, 9.4], P.hide, "foot")
    for k, x in enumerate((9.1, 11.3, 13.5)):
        D.sym("foot" + s, [x, 0, -1], [1.9, 2.6, 3.4], P.hide, "toe%d" % k)
        D.seg("foot" + s, (x + 0.95, 1.5, -0.6), (x + 0.95, 0.2, -4.2), 1.5, 1.7, P.claw, "toe_talon%d" % k, extend=(0, 0.3), mirror=True)


def tail(D, P):
    for n in range(TAIL_N):
        b = "tail%dc" % (n + 1)
        z = tail_z(n)
        w, h, y = TAIL_W5[n], TAIL_H5[n], TAIL_Y[n]
        L = TAIL_LEN[n]
        D.cube(b, [-w / 2, y - h / 2, z - 3], [w, h, L + 6], P.hide, "tail%d" % n)
        D.cube(b, [-w / 2 + 1, y - h / 2 - 0.8, z - 2], [w - 2, 1.2, L + 4], P.belly, "tail_belly%d" % n,
               faces=("down", "east", "west", "north", "south"))
        if n < TAIL_N - 1:
            plane_x(D, b, 0, y + h / 2 - 0.8, z - 2, max(2.6, 6.2 - 0.5 * n), L + 4, P.fin(2), "fin_tail%d" % n)
    zt = tail_z(TAIL_N)
    yt = TAIL_Y[-1]
    b = "tail8c"
    plane_x(D, b, 0, yt - 8, zt - 3, 16, 24, P.blade(), "blade_v")
    D.cube(b, [-7, yt, zt - 3], [14, 0, 21], P.blade(horizontal=True), "blade_h", faces=("up",))
    D.cube(b, [-1.8, yt - 1.8, zt - 4], [3.6, 3.6, 4], P.thin("blade_hub", line=False), "blade_hub")


def overcharge(D, P):
    """Phase-two growth: bigger glowing crystal fins over the normal ones, glowing hex scales on the flanks."""
    for k, (py, pz, w, h) in enumerate(NECK5):
        b = "oc_neck%dc" % (k + 1)
        y0 = py + 0.5 - h / 2 + h - 0.5
        plane_x(D, b, OC_X, y0, pz - 13, 11 - k * 1.2, 16, P.fin(3, oc=True), "oc_fin_neck%d" % k, mirror=True)
    plane_x(D, "oc_ribs", OC_X, 41, -43, 14, 11, P.fin(2, oc=True), "oc_fin_chest", mirror=True)
    plane_x(D, "oc_chest", OC_X, 38, -14, 11, 18, P.fin(3, oc=True), "oc_fin_waist", mirror=True)
    plane_x(D, "oc_hips", OC_X, 38.5, 0, 11, 18, P.fin(3, oc=True), "oc_fin_hips", mirror=True)
    plane_x(D, "oc_ribs", 10.6, 23, -38, 13, 22, P.hexplate, "oc_hex_chest", mirror=True)
    plane_x(D, "oc_hips", 10.1, 24, 1, 11, 15, P.hexplate, "oc_hex_hips", mirror=True)
    for n in range(6):
        b = "oc_tail%dc" % (n + 1)
        z = tail_z(n)
        y = TAIL_Y[n] + TAIL_H5[n] / 2 - 0.5
        plane_x(D, b, OC_X, y, z - 1, max(4, 10 - n * 1.1), TAIL_LEN[n] + 2, P.fin(2, oc=True), "oc_fin_tail%d" % n, mirror=True)


# --------------------------------------------------------------------------------------------- build (phase-two channel)

def build(D, identifier="tech_dragon"):
    tex_w, density = V4.TEX_W, V4.DENSITY
    tex_h = V4.pack(D.cubes, tex_w, density)
    tex_h = int(math.ceil(tex_h / 16.0) * 16)
    # texture, glow, texture2, glow2, drained (1.9: overload / EMP - the glowing parts dead grey), drained glow
    imgs = [Image.new("RGBA", (tex_w, tex_h), (0, 0, 0, 0)) for _ in range(6)]
    px = [im.load() for im in imgs]
    skel = rig_v4.Skeleton(D.bones)
    rest = skel.rest_world()
    for c in D.cubes:
        if c.share:
            continue
        cm = rest[c.bone] @ rig_v4.cube_matrix({"rotation": c.rotation, "pivot": c.pivot or [c.origin[i] + c.size[i] / 2 for i in range(3)]})
        r3 = cm[:3, :3]
        for face, (x0, y0, fw, fh) in c.uv.items():
            nrm = r3 @ np.array(FACE_N[face], dtype=float)
            nrm /= max(1e-9, np.linalg.norm(nrm))
            ctx = Ctx()
            ctx.face, ctx.w, ctx.h, ctx.size, ctx.cube, ctx.n = face, fw, fh, c.size, c, nrm
            for j in range(fh):
                for i in range(fw):
                    fu, fv = (i + 0.5) / fw, (j + 0.5) / fh
                    lp = local_point(c, face, fu, fv)
                    wp = cm @ np.array([lp[0], lp[1], lp[2], 1.0])
                    ctx.i, ctx.j, ctx.fu, ctx.fv, ctx.lp, ctx.p = i, j, fu, fv, lp, wp[:3]
                    r = c.paint(ctx)
                    if r is None:
                        continue
                    col, g, g2 = tri(r)
                    if len(col) == 3:
                        col = col + (255,)
                    if col[3] == 0:
                        continue
                    X, Y = x0 + i, y0 + j
                    px[0][X, Y] = col
                    if g is not None:
                        lum = (col[0] * 0.3 + col[1] * 0.5 + col[2] * 0.2) / 255.0
                        px[4][X, Y] = (int(24 + 52 * lum), int(27 + 56 * lum), int(36 + 66 * lum), col[3])
                        if (X * 7 + Y * 13) % 29 == 0:
                            px[5][X, Y] = (60, 20, 10, 255)   # a few dying embers
                    else:
                        px[4][X, Y] = col
                    if g is not None:
                        px[1][X, Y] = (g[0], g[1], g[2], 255)
                    # phase two: veins/fins lit; the base texture brightened where they glow
                    if g2 is not None:
                        px[2][X, Y] = (g2[0], g2[1], g2[2], 255)
                        px[3][X, Y] = (g2[0], g2[1], g2[2], 255)
                    else:
                        px[2][X, Y] = col
                        if g is not None:
                            px[3][X, Y] = (g[0], g[1], g[2], 255)
    geo = geo_json(D, tex_w, tex_h, density, identifier)
    return geo, imgs[0], imgs[1], imgs[2], imgs[3], imgs[4], imgs[5]


def geo_json(D, tex_w, tex_h, density, identifier):
    out_bones = []
    for name, parent, pivot, rotation in D.bones:
        b = {"name": name, "pivot": pivot}
        if parent:
            b["parent"] = parent
        if rotation:
            b["rotation"] = rotation
        own = [c for c in D.cubes if c.bone == name]
        if own:
            b["cubes"] = []
            for c in own:
                e = {"origin": c.origin, "size": c.size, "uv": {}}
                for face, (x, y, w, h) in c.uv.items():
                    fw, fh = [v * density for v in face_size(c, face)]
                    if face == "down":
                        e["uv"][face] = {"uv": [x, y + h], "uv_size": [fw, -fh]}
                    else:
                        e["uv"][face] = {"uv": [x, y], "uv_size": [fw, fh]}
                if c.mirror_of is not None:
                    for face, uvd in e["uv"].items():
                        uvd["uv"] = [uvd["uv"][0] + uvd["uv_size"][0], uvd["uv"][1]]
                        uvd["uv_size"] = [-uvd["uv_size"][0], uvd["uv_size"][1]]
                else:
                    # GeckoLib/Bedrock "east" is the cube's min-x side (Blockbench +x, mirrored on export) and runs
                    # its u the way local_point() paints "west", so what the painter calls east (+x) is written as
                    # "west" and vice versa. The mirrored copies already sit on the other side, so they keep the names.
                    # (1.7.0 missed this: the eyes' painted iris ended up on the inner face, buried in the snout.)
                    if "east" in e["uv"] or "west" in e["uv"]:
                        ea, we = e["uv"].get("east"), e["uv"].get("west")
                        e["uv"]["east"], e["uv"]["west"] = we, ea
                        e["uv"] = {k: v for k, v in e["uv"].items() if v is not None}
                if c.rotation:
                    e["rotation"] = c.rotation
                    e["pivot"] = c.pivot if c.pivot else [c.origin[i] + c.size[i] / 2 for i in range(3)]
                b["cubes"].append(e)
        out_bones.append(b)
    return {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry." + identifier, "texture_width": tex_w, "texture_height": tex_h,
                        "visible_bounds_width": 24, "visible_bounds_height": 12, "visible_bounds_offset": [0, 3, 0]},
        "bones": out_bones}]}


def tech_dragon():
    D = build_dragon()
    geo, img, glw, img2, glw2, img3, glw3 = build(D)
    D.drained = (img3, glw3)
    return D, geo, img, glw, img2, glw2


if __name__ == "__main__":
    import json
    import sys
    out = sys.argv[1]
    D, geo, img, glw, img2, glw2 = tech_dragon()
    json.dump(geo, open(out + "/tech_dragon.geo.json", "w"))
    img.save(out + "/tech_dragon.png")
    glw.save(out + "/tech_dragon_glowmask.png")
    img2.save(out + "/tech_dragon_overcharged.png")
    glw2.save(out + "/tech_dragon_overcharged_glowmask.png")
    print("bones", len(D.bones), "cubes", len(D.cubes), "texture", img.size)
