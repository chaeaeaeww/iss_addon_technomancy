"""
Automaton Mk.II "Blitz" (1.3): steam golem modelled on the Blitzcrank concept (idea/blitz.png).

* egg-shaped riveted brass hull made of horizontal bands (each band's faces are unique planes, so nothing z-fights),
  a recessed blue turbine on top behind a small boxy head with two round glowing eyes, a ringed chest emblem with a
  lightning bolt, rubber hoses into the shoulders, long piston upper arms ending in huge blocky gauntlets, thin
  piston legs on splayed spiked feet;
* authored at full size (about 3.4 blocks to the top of the head), painted at 2 texels per model pixel.

1.10 refinements (reference: a Blitzcrank reinterpretation on Sketchfab, studied for proportions only): open
three-fingered hands with a thumb (segmented golden fingers, like the Rocket Grab hand), two tall smokestacks with
flared caps on the back, a rounded shoulder pauldron, a mouth grille under the eyes.

Animations (all "servo" styled: held poses and quick snaps, GeckoLib step easing):
idle, walk, run (2.5 s overdrive sprint: both arms pump hard), vent (1 s slowdown after the sprint), jab_left,
jab_right, uppercut (wind-up, explosive rising swing, follow-through), grab (right fist launched), static, overload,
assemble and the looping "gears" layer (turbine spin, emblem pulse).

Coordinates: Bedrock model space, front is -Z, the golem's left is +X, 16 px = 1 block.
"""
import math

import armor
import models
from models import C, build
from models_v2 import RUBBER, anims, kf, mirror
from pixelart import BRASS, CYAN, IRON, OUTLINE, line, noise, put, ramp, rect, rgb
from surf import surf_cube

DENSITY = 2.0
TEX = 512
HULL = [rgb("4E3110"), rgb("774D1B"), rgb("A26F2A"), rgb("C8913A"), rgb("E2B45A"), rgb("F6D98E")]
BLUE = [rgb("0B2F6E"), rgb("1557C4"), rgb("3B8DFF"), rgb("8CC4FF"), rgb("E2F2FF")]


def gp(x, y, c):
    models.glow_put(x, y, c)


# ------------------------------------------------------------------------------------------- materials

def hull(img, x, y, w, h, face):
    """Riveted brass band: warm gradient, rivet rows along the top and bottom seams, light wear streaks."""
    base = {"up": 0.72, "down": 0.3}.get(face, 0.55)
    armor.shade_v(HULL, x, y, w, h, img, base, spread=0.5, seed=x * 5 + y * 3, grain=0.045)
    if face in ("north", "south", "east", "west"):
        line(img, x, y, x + w - 1, y, HULL[5])
        line(img, x, y + h - 1, x + w - 1, y + h - 1, HULL[1])
        for i in range(2, w - 1, 6):
            if h >= 6:
                put(img, x + i, y + 2, HULL[5])
                put(img, x + i + 1, y + 3, HULL[0])
                put(img, x + i, y + h - 3, HULL[5])
                put(img, x + i + 1, y + h - 2, HULL[0])
        # vertical panel seams
        for i in range(w // 3, w, max(8, w // 3)):
            line(img, x + i, y + 1, x + i, y + h - 2, HULL[1])
            line(img, x + i + 1, y + 1, x + i + 1, y + h - 2, HULL[4])
        # wear scratches
        for k in range(max(1, w * h // 160)):
            sx = x + (k * 37 + y * 11) % max(1, w)
            sy = y + (k * 23 + x * 7) % max(1, h)
            for t in range(3):
                put(img, sx + t, sy + (t // 2), HULL[2])
    else:
        armor.border(img, x, y, w, h, HULL[1])


def brass_plain(img, x, y, w, h, face):
    armor.shade_v(HULL, x, y, w, h, img, 0.6 if face != "down" else 0.32, spread=0.45, seed=x + y * 7, grain=0.04)
    armor.border(img, x, y, w, h, HULL[1])
    line(img, x, y, x + w - 1, y, HULL[5])


def gauntlet(img, x, y, w, h, face):
    """Huge forearm: thick plates with dark seams, bolts at the corners and a worn top edge."""
    brass_plain(img, x, y, w, h, face)
    if w >= 10 and h >= 10 and face in ("north", "south", "east", "west"):
        armor.border(img, x + 3, y + 3, w - 6, h - 6, HULL[2])
        line(img, x + 3, y + h // 2, x + w - 4, y + h // 2, HULL[1])
        for bx, by in ((x + 2, y + 2), (x + w - 3, y + 2), (x + 2, y + h - 3), (x + w - 3, y + h - 3)):
            rect(img, bx - 1, by - 1, bx, by, IRON[2])
            put(img, bx - 1, by - 1, IRON[4])
    noise(img, x, y, x + w - 1, y + h - 1, 0.03, x * 3 + y)


def knuckle(img, x, y, w, h, face):
    armor.shade_v(HULL, x, y, w, h, img, 0.5 if face != "up" else 0.66, spread=0.5, seed=x * 11 + y, grain=0.03)
    armor.border(img, x, y, w, h, HULL[0])
    if face == "north" and h >= 4:
        line(img, x + 1, y + h // 3, x + w - 2, y + h // 3, HULL[1])


def dark_iron(img, x, y, w, h, face):
    armor.shade_v(IRON, x, y, w, h, img, 0.28 if face != "up" else 0.4, spread=0.35, seed=x + y * 5, grain=0.04)
    armor.border(img, x, y, w, h, IRON[0])


def piston(img, x, y, w, h, face):
    """Polished steel rod with a highlight stripe and grease bands."""
    armor.shade_v(IRON, x, y, w, h, img, 0.55, spread=0.6, seed=x * 7 + y, grain=0.02)
    if face in ("north", "south", "east", "west"):
        line(img, x + w // 3, y, x + w // 3, y + h - 1, IRON[5])
        for j in range(4, h, 7):
            line(img, x, y + j, x + w - 1, y + j, IRON[1])


def hose(img, x, y, w, h, face):
    armor.shade_v(RUBBER, x, y, w, h, img, 0.5, spread=0.45, seed=x + y, grain=0.03)
    for k in range(0, max(w, h), 3):
        if h >= w:
            line(img, x, y + k, x + w - 1, y + k, RUBBER[0])
        else:
            line(img, x + k, y, x + k, y + h - 1, RUBBER[0])


def spike(img, x, y, w, h, face):
    armor.shade_v(IRON, x, y, w, h, img, 0.5, spread=0.7, seed=x + y, grain=0.02)
    put(img, x, y, IRON[5])


def blue_glow(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            d = abs(i - (w - 1) / 2) / max(1, w) + abs(j - (h - 1) / 2) / max(1, h)
            c = ramp(BLUE, 0.95 - d * 1.1)
            put(img, x + i, y + j, c)
            gp(x + i, y + j, c)


def turbine(img, x, y, w, h, face):
    """Glowing turbine seen from above: dark housing, bright core, curved fan blades."""
    if face != "up":
        dark_iron(img, x, y, w, h, face)
        return
    cx, cy = x + (w - 1) / 2, y + (h - 1) / 2
    r = min(w, h) / 2
    for j in range(h):
        for i in range(w):
            dx, dy = (x + i - cx) / r, (y + j - cy) / r
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            if d > 1.0:
                put(img, x + i, y + j, IRON[1])
                continue
            blade = ((a * 6 / math.pi + d * 2.2) % 2) < 0.55
            if d < 0.22:
                c = BLUE[4]
            elif blade:
                c = IRON[2] if d > 0.35 else IRON[3]
            else:
                c = ramp(BLUE, 0.9 - d * 0.55)
            put(img, x + i, y + j, c)
            if not blade or d < 0.22:
                gp(x + i, y + j, c)


def eye(img, x, y, w, h, face):
    """Round white eye with a blue rim (front face only)."""
    if face != "north":
        dark_iron(img, x, y, w, h, face)
        return
    cx, cy = x + (w - 1) / 2, y + (h - 1) / 2
    r = min(w, h) / 2
    for j in range(h):
        for i in range(w):
            d = math.hypot(x + i - cx, y + j - cy) / r
            if d <= 0.62:
                c = rgb("F6FCFF") if d < 0.45 else rgb("CFE9FF")
            elif d <= 1.0:
                c = BLUE[2] if d < 0.85 else BLUE[1]
            else:
                c = IRON[1]
            put(img, x + i, y + j, c)
            if d <= 1.0:
                gp(x + i, y + j, c)


def head_shell(img, x, y, w, h, face):
    brass_plain(img, x, y, w, h, face)
    if face == "north" and w >= 8 and h >= 6:
        # dark faceplate band where the eyes sit
        rect(img, x + 2, y + h // 3, x + w - 3, y + h - 3, IRON[1])
        line(img, x + 2, y + h // 3, x + w - 3, y + h // 3, IRON[0])


def emblem_ring(img, x, y, w, h, face):
    armor.shade_v(IRON, x, y, w, h, img, 0.5 if face == "north" else 0.35, spread=0.5, seed=x + y, grain=0.03)
    if face == "north":
        cx, cy = x + (w - 1) / 2, y + (h - 1) / 2
        r = min(w, h) / 2
        for j in range(h):
            for i in range(w):
                d = math.hypot(x + i - cx, y + j - cy) / r
                if 0.78 < d <= 0.98:
                    put(img, x + i, y + j, IRON[4] if (i + j) % 5 else IRON[5])
                elif d <= 0.78:
                    put(img, x + i, y + j, HULL[2] if d > 0.7 else HULL[3])
    armor.border(img, x, y, w, h, IRON[0])


def bolt_plate(img, x, y, w, h, face):
    """Lightning bolt on a brass disc."""
    armor.shade_v(HULL, x, y, w, h, img, 0.62, spread=0.4, seed=x, grain=0.02)
    if face != "north":
        return
    # zig-zag bolt polygon in unit space (x right, y down)
    pts = [(0.62, 0.02), (0.30, 0.50), (0.50, 0.50), (0.36, 0.98), (0.74, 0.40), (0.52, 0.40), (0.70, 0.02)]

    def inside(px, py):
        c = False
        n = len(pts)
        for k in range(n):
            ax, ay = pts[k]
            bx, by = pts[(k + 1) % n]
            if (ay > py) != (by > py) and px < (bx - ax) * (py - ay) / (by - ay + 1e-9) + ax:
                c = not c
        return c

    for j in range(h):
        for i in range(w):
            if inside((i + 0.5) / w, (j + 0.5) / h):
                c = BLUE[3] if (i + j) % 4 else BLUE[4]
                put(img, x + i, y + j, c)
                gp(x + i, y + j, c)


def vent(img, x, y, w, h, face):
    dark_iron(img, x, y, w, h, face)
    if face in ("north", "south", "east", "west"):
        for k in range(1, h - 1, 2):
            line(img, x + 1, y + k, x + w - 2, y + k, OUTLINE)


# ------------------------------------------------------------------------------------------- continuous surfaces

LIGHT = {"up": 1.0, "north": 0.86, "east": 0.76, "west": 0.76, "south": 0.66, "down": 0.42}


def _hash(*v):
    h = 2166136261
    for a in v:
        h = ((h ^ (int(a * 31) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (h % 1000) / 1000.0


def hull_fn(face, x, y, z, i, j, w, h):
    """One continuous riveted brass sphere across all hull bands."""
    t = (y - 19.5) / 30.0
    base = 0.28 + 0.5 * t
    if face in ("north", "south"):
        base -= 0.22 * (abs(x) / 15.5) ** 2
    elif face in ("east", "west"):
        base -= 0.22 * (abs(z) / 14.5) ** 2
    elif face == "up":
        base += 0.1
    base = base * LIGHT[face] + (_hash(x, y, z) - 0.5) * 0.06
    col = ramp(HULL, base)
    # vertical plate seams (continuous over every band) with rivets beside them
    seam = None
    if face in ("north", "south"):
        seam = min(abs(x - 9.5), abs(x + 9.5))
    elif face in ("east", "west"):
        seam = min(abs(z - 5.5), abs(z + 6.5))
    if seam is not None:
        if seam < 0.3:
            return HULL[1]
        if seam < 0.55:
            return HULL[4]
        if 1.1 < seam < 1.6 and (int(y * 2) % 6) == 0:
            return HULL[5]
    # horizontal seams with rivet rows
    if face in ("north", "south", "east", "west"):
        for sy in (25.5, 41.5):
            dy = y - sy
            if -0.3 < dy < 0.2:
                return HULL[1]
            if 0.2 <= dy < 0.5:
                return HULL[4]
            if 0.9 < abs(dy) < 1.4 and int((x + z) * 2) % 5 == 0:
                return HULL[5]
    # wear: scattered darker flecks
    if _hash(int(x * 2), int(y * 2), int(z * 2)) > 0.985:
        return ramp(HULL, base - 0.15)
    return col


def gauntlet_fn(face, x, y, z, i, j, w, h):
    """Forearm gauntlet: bright at the elbow end, darker towards the fist, one riveted plate seam."""
    t = (y - 9) / 15.0
    base = (0.3 + 0.4 * t) * LIGHT[face] + (_hash(x, y, z) - 0.5) * 0.05
    if face == "up":
        base += 0.15
    col = ramp(HULL, base)
    if face in ("north", "south", "east", "west"):
        if abs(y - 17) < 0.3:
            return HULL[1]
        if 0.3 <= y - 17 < 0.6:
            return HULL[4]
        if 0.9 < abs(y - 17) < 1.5 and int((x + z) * 2) % 6 == 0:
            return HULL[5]
    if _hash(int(x * 2), int(y * 2), int(z * 2)) > 0.98:
        return ramp(HULL, base - 0.15)
    return col


EMBLEM_C = (0.0, 28.0)
BOLT = [(1.6, 4.6), (-1.9, -0.2), (0.3, -0.2), (-1.4, -4.6), (2.4, 1.0), (0.2, 1.0), (2.2, 4.6)]


def _in_poly(px, py, pts):
    c = False
    n = len(pts)
    for k in range(n):
        ax, ay = pts[k]
        bx, by = pts[(k + 1) % n]
        if (ay > py) != (by > py) and px < (bx - ax) * (py - ay) / (by - ay + 1e-9) + ax:
            c = not c
    return c


def emblem_fn(face, x, y, z, i, j, w, h):
    """Round chest emblem spread over three overlapping plates: steel bolted ring, brass disc, glowing bolt."""
    if face != "north":
        return ramp(IRON, 0.35 * LIGHT[face] + 0.15)
    dx, dy = x - EMBLEM_C[0], y - EMBLEM_C[1]
    d = math.hypot(dx, dy)
    if d > 6.6:
        return ramp(IRON, 0.32 + (_hash(x, y) - 0.5) * 0.06)
    if d > 5.0:
        ang = math.atan2(dy, dx)
        if abs((ang * 8 / math.pi) % 2 - 1) < 0.14 and 5.4 < d < 6.2:
            return IRON[5]
        return ramp(IRON, 0.55 + 0.25 * (dy / 6.6))
    if d > 4.5:
        return HULL[1]
    if _in_poly(dx, dy, BOLT):
        c = BLUE[4] if (int(x * 2) + int(y * 2)) % 5 == 0 else BLUE[3]
        return (c, c)
    return ramp(HULL, 0.62 + 0.2 * (dy / 5.0))


# ------------------------------------------------------------------------------------------- model

HIP_Y = 18
SHOULDER = (-17.5, 39.0, 1.0)
ELBOW_Y = 24.0
WRIST_Y = 9.0
HULL_C = 33.0  # hull centre height
HULL_R = 15.0


def blitz():
    sx, sy, sz = SHOULDER
    bones = [
        ("root", None, [0, 0, 0], None),
        ("leg_r", "root", [-6, HIP_Y, 1], None),
        ("shin_r", "leg_r", [-7, 10, 0], None),
        ("foot_r", "shin_r", [-7, 3, 0], None),
        ("leg_l", "root", [6, HIP_Y, 1], None),
        ("shin_l", "leg_l", [7, 10, 0], None),
        ("foot_l", "shin_l", [7, 3, 0], None),
        ("body", "root", [0, HIP_Y, 0], None),
        ("hull", "body", [0, HULL_C, 0], None),
        ("emblem", "hull", [0, 28, -15.5], None),
        ("turbine", "hull", [0, 48.5, 3], None),
        ("head", "hull", [0, 46, -8], None),
        ("arm_r", "hull", [sx, sy, sz], None),
        ("forearm_r", "arm_r", [sx - 1, ELBOW_Y, sz], None),
        ("fist_r", "forearm_r", [sx - 1.5, WRIST_Y, sz], None),
        ("arm_l", "hull", [-sx, sy, sz], None),
        ("forearm_l", "arm_l", [-sx + 1, ELBOW_Y, sz], None),
        ("fist_l", "forearm_l", [-sx + 1.5, WRIST_Y, sz], None),
    ]
    cubes = []

    def add(bone, origin, size, mat, name=None, **kw):
        c = C(bone, [round(v, 3) for v in origin], [round(v, 3) for v in size], mat, name=name, **kw)
        cubes.append(c)
        return c

    def both(bone_r, bone_l, origin, size, mat, name, **kw):
        c = add(bone_r, origin, size, mat, name, **kw)
        cubes.append(mirror(c, bone_l))
        return c

    # ---------------- legs: thigh piston, knee ball, shin spring, splayed spiked foot
    both("leg_r", "leg_l", [-8.5, 12, -1.25], [5, 7, 4.5], dark_iron, "hip_block")
    both("leg_r", "leg_l", [-7.75, 9.5, -0.75], [3.5, 3, 3.5], piston, "thigh")
    both("leg_r", "leg_l", [-5.2, 11, 2.2], [1.2, 6, 1.2], piston, "thigh_rod")
    both("shin_r", "shin_l", [-9.25, 7.75, -2.25], [4.5, 4.5, 4.5], brass_plain, "knee")
    both("shin_r", "shin_l", [-8.25, 3, -1.25], [2.5, 5, 2.5], piston, "shin")
    both("shin_r", "shin_l", [-8.75, 4, -1.75], [3.5, 1, 3.5], dark_iron, "shin_collar")
    both("foot_r", "foot_l", [-10.5, 0, -6.5], [7, 2.5, 10.5], brass_plain, "foot")
    both("foot_r", "foot_l", [-9.5, 2.5, -4.5], [5, 1.25, 6], dark_iron, "ankle_plate")
    for k, xo in enumerate((-10.6, -8.1, -5.6)):
        both("foot_r", "foot_l", [xo, 0.1, -10], [2, 1.8, 4], spike, "toe%d" % k)
    both("foot_r", "foot_l", [-8, 0.1, 4], [2, 1.6, 3.5], spike, "heel")

    # ---------------- pelvis skirt under the hull
    add("body", [-8, 14.5, -7], [16, 4.5, 14], dark_iron, "pelvis")
    add("body", [-9.5, 17.5, -8.5], [19, 2, 17], vent, "pelvis_ring")

    # ---------------- hull: horizontal bands, an egg slightly wider above the middle. Every band is painted from its
    # model-space position (surf), so the whole sphere reads as one riveted shell.
    bands = ((19.5, 22.5), (22.5, 25.5), (25.5, 29), (29, 33), (33, 37.5), (37.5, 41.5), (41.5, 44.5), (44.5, 47), (47, 49))
    for i, (y0, y1) in enumerate(bands):
        yc = (y0 + y1) / 2
        t = (yc - HULL_C) / (HULL_R + (1.5 if yc > HULL_C else 0))
        r = HULL_R * math.sqrt(max(0.06, 1 - t * t)) + (0.6 if yc > HULL_C else 0)
        depth = r * 0.9
        cubes.append(surf_cube("hull", [-r, y0, -depth], [2 * r, y1 - y0, 2 * depth], hull_fn, "band%d" % i))
        # bevel: a narrower, deeper copy rounds the corners
        cubes.append(surf_cube("hull", [-r * 0.74, y0 + 0.02, -depth - 1.3], [r * 1.48, y1 - y0 - 0.04, 2 * depth + 2.6], hull_fn, "band%d_b" % i))
    # dark belt around the middle
    add("hull", [-15.8, 31.2, -14.1], [31.6, 1.6, 28.2], dark_iron, "belt")
    # shoulder sockets
    both("hull", "hull", [-17, 35.5, -2.5], [3.5, 7, 7], dark_iron, "socket")
    both("hull", "hull", [-17.6, 36.5, -1.5], [1, 5, 5], brass_plain, "socket_cap")
    # top: turbine collar (open ring) and back exhaust pipes
    for k, (o, s) in enumerate((([-7, 48.7, -4], [14, 2.2, 1.6]), ([-7, 48.7, 8.4], [14, 2.2, 1.6]),
                                ([-7, 48.7, -2.4], [1.6, 2.2, 10.8]), ([5.4, 48.7, -2.4], [1.6, 2.2, 10.8]))):
        add("hull", o, s, dark_iron, "collar%d" % k)
    # 1.10: two tall smokestacks with flared caps and a clamp band
    both("hull", "hull", [-8.0, 40, 11.4], [3.4, 17, 3.4], piston, "exhaust")
    both("hull", "hull", [-8.6, 56.6, 10.8], [4.6, 1.6, 4.6], dark_iron, "exhaust_cap")
    both("hull", "hull", [-8.4, 46, 11.0], [4.2, 1.2, 4.2], brass_plain, "exhaust_band")
    # turbine fan (spins)
    add("turbine", [-5.4, 48.75, -2.4], [10.8, 0.6, 10.8], turbine, "fan", glow=False)
    add("turbine", [-1.2, 49.3, 1.8], [2.4, 0.8, 2.4], brass_plain, "fan_hub")
    # chest emblem: steel ring, brass disc, lightning bolt
    for k, (o, size) in enumerate((([-6.8, 23.5, -16.4], [13.6, 9, 2.4]), ([-4.5, 21.2, -16.4], [9, 13.6, 2.4]),
                                   ([-5.9, 22.2, -16.4], [11.8, 11.6, 2.4]))):
        cubes.append(surf_cube("emblem", o, size, emblem_fn, "emblem%d" % k))
    # little boxy head on the front of the dome
    add("head", [-5, 44.5, -13], [10, 8.5, 8], head_shell, "skull")
    add("head", [-4, 52.9, -11.5], [8, 1.2, 5], brass_plain, "skull_top")
    add("head", [-0.7, 54, -10], [1.4, 3, 1.4], piston, "antenna")
    add("head", [-1.2, 56.9, -10.5], [2.4, 1.2, 2.4], blue_glow, "antenna_tip", glow=True)
    both("head", "head", [-4.2, 46, -13.6], [3.4, 3.4, 0.8], eye, "eye")
    both("head", "head", [-5.8, 46.5, -11], [1, 4, 4], dark_iron, "ear")
    # 1.10: a mouth grille under the eyes
    add("head", [-3.2, 44.9, -13.4], [6.4, 1.2, 0.6], vent, "grille")

    # ---------------- hoses from the back of the hull into the shoulders
    for k, (o, s, r) in enumerate((([-14, 42.5, 4], [3, 2.2, 2.2], [0, 0, -25]), ([-17.2, 42, 3], [3.2, 2.2, 2.2], [0, 0, -60]),
                                   ([-14, 30.5, 5], [3, 2.2, 2.2], [0, 0, 25]))):
        both("hull", "hull", o, s, hose, "hose_body%d" % k, rotation=r, pivot=[o[0] + s[0] / 2, o[1] + s[1] / 2, o[2] + s[2] / 2])

    # ---------------- arms: piston upper arm, elbow, huge gauntlet, blocky fist
    both("arm_r", "arm_l", [sx - 3.5, sy - 4, sz - 3.5], [6, 7, 7], brass_plain, "shoulder")
    # 1.10: a rounded pauldron over the shoulder (a block turned 45 degrees on top of it)
    both("arm_r", "arm_l", [sx - 3.2, sy + 1.2, sz - 3.2], [6.4, 2.4, 6.4], brass_plain, "pauldron", rotation=[0, 45, 0], pivot=[sx - 0.5, sy + 2.4, sz])
    both("arm_r", "arm_l", [sx - 2.5, ELBOW_Y + 1, sz - 1.75], [3.5, sy - ELBOW_Y - 4, 3.5], piston, "upper_arm")
    both("arm_r", "arm_l", [sx - 0.2, ELBOW_Y + 2, sz + 2.1], [1.2, sy - ELBOW_Y - 6, 1.2], piston, "upper_rod")
    for k in range(3):
        both("arm_r", "arm_l", [sx - 3.2 - k * 0.2, sy - 6.5 - k * 3.2, sz + 1.6], [1.8, 2.8, 1.8], hose, "arm_hose%d" % k,
             rotation=[12, 0, 8 - k * 6], pivot=[sx - 2.3, sy - 5 - k * 3.2, sz + 2.5])
    both("forearm_r", "forearm_l", [sx - 4, ELBOW_Y - 2.5, sz - 3], [6, 5, 6], dark_iron, "elbow")
    for k, (dx, dz) in enumerate(((5.5, 4.2), (4.2, 5.5))):
        g = surf_cube("forearm_r", [sx - 1.5 - dx, WRIST_Y + 1, sz - dz], [2 * dx, ELBOW_Y - WRIST_Y - 2.5, 2 * dz], gauntlet_fn, "gauntlet%d" % k)
        cubes.append(g)
        cubes.append(mirror(g, "forearm_l"))
    both("forearm_r", "forearm_l", [sx - 7.6, WRIST_Y + 7, sz - 3.5], [0.8, 6, 7], vent, "gauntlet_vent")
    both("forearm_r", "forearm_l", [sx - 7.3, ELBOW_Y - 4.3, sz - 5.8], [11.6, 2, 11.6], dark_iron, "gauntlet_band")
    both("forearm_r", "forearm_l", [sx - 7.3, WRIST_Y + 0.3, sz - 5.8], [11.6, 1.6, 11.6], dark_iron, "wrist_band")
    # 1.10: an open three-fingered hand with a thumb, held half-curled: a broad palm, each finger reaching forward from
    # the bottom of the palm and hooking down at the tip (golden segments, dark joints)
    both("fist_r", "fist_l", [sx - 6.6, WRIST_Y - 6, sz - 5], [10.2, 6.2, 8.6], knuckle, "palm")
    for k in range(3):
        fx = sx - 6.4 + k * 3.4
        both("fist_r", "fist_l", [fx, WRIST_Y - 5.6, sz - 9.6], [2.9, 2.6, 4.8], knuckle, "finger%d" % k)
        both("fist_r", "fist_l", [fx + 0.2, WRIST_Y - 8.2, sz - 10.6], [2.5, 3.4, 2.4], knuckle, "fingertip%d" % k,
             rotation=[22, 0, 0], pivot=[fx + 1.45, WRIST_Y - 4.8, sz - 9.4])
        both("fist_r", "fist_l", [fx + 0.6, WRIST_Y - 5.9, sz - 5.4], [1.7, 3.2, 0.8], dark_iron, "joint%d" % k)
    both("fist_r", "fist_l", [sx + 3.5, WRIST_Y - 6.4, sz - 7.6], [2.6, 3.0, 4.4], knuckle, "thumb", rotation=[0, -18, 0], pivot=[sx + 4.8, WRIST_Y - 5, sz - 3.4])

    geo, img, glow = build("clockwork_automaton_mk2", TEX, bones, cubes, (4.5, 4.2, 1.9), density=DENSITY, bedrock_sides=True)
    return geo, img, glow, anims(blitz_animations())


# ------------------------------------------------------------------------------------------- animations

def K(frames, easing=None, args=None):
    """{time: vector} -> keyframe dict. easing applies to every frame after the first."""
    out = {}
    for i, (t, v) in enumerate(sorted(frames.items())):
        out["%g" % t] = kf(v, easing if i else None, args if i and easing == "step" else None)
    return out


def blitz_animations():
    a = {}
    a["gears"] = {"loop": True, "animation_length": 1.0, "bones": {
        "turbine": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([0, 360, 0])}},
        "emblem": {"scale": {"0.0": kf([1, 1, 1]), "0.5": kf([1.03, 1.03, 1]), "1.0": kf([1, 1, 1])}},
    }}
    a["idle"] = {"loop": True, "animation_length": 4.0, "bones": {
        "hull": {"position": K({0: [0, 0, 0], 1.6: [0, 0, 0], 1.7: [0, -0.6, 0], 2.6: [0, -0.6, 0], 2.7: [0, 0, 0]}, "step", [2])},
        "arm_r": {"rotation": K({0: [0, 0, 4], 2.0: [-5, 0, 7], 4.0: [0, 0, 4]}, "step", [3])},
        "arm_l": {"rotation": K({0: [0, 0, -4], 2.0: [-5, 0, -7], 4.0: [0, 0, -4]}, "step", [3])},
        "forearm_r": {"rotation": K({0: [-8, 0, 0]})}, "forearm_l": {"rotation": K({0: [-8, 0, 0]})},
        "head": {"rotation": K({0: [0, 0, 0], 1.0: [0, 0, 0], 1.1: [0, 22, 0], 2.2: [0, 22, 0], 2.3: [0, -15, 0], 3.2: [0, -15, 0], 3.3: [0, 0, 0]}, "step", [2])},
    }}
    # walk: heavy, rocking, arms swinging against the legs in clicks
    a["walk"] = {"loop": True, "animation_length": 1.4, "bones": {
        "leg_r": {"rotation": K({0: [26, 0, 0], 0.7: [-26, 0, 0], 1.4: [26, 0, 0]})},
        "leg_l": {"rotation": K({0: [-26, 0, 0], 0.7: [26, 0, 0], 1.4: [-26, 0, 0]})},
        "shin_r": {"rotation": K({0: [0, 0, 0], 0.7: [0, 0, 0], 0.95: [34, 0, 0], 1.2: [0, 0, 0], 1.4: [0, 0, 0]})},
        "shin_l": {"rotation": K({0: [0, 0, 0], 0.25: [34, 0, 0], 0.5: [0, 0, 0], 1.4: [0, 0, 0]})},
        "foot_r": {"rotation": K({0: [-20, 0, 0], 0.35: [0, 0, 0], 0.7: [20, 0, 0], 1.05: [0, 0, 0], 1.4: [-20, 0, 0]})},
        "foot_l": {"rotation": K({0: [20, 0, 0], 0.35: [0, 0, 0], 0.7: [-20, 0, 0], 1.05: [0, 0, 0], 1.4: [20, 0, 0]})},
        "body": {"position": K({0: [0, -1.4, 0], 0.08: [0, 0.3, 0], 0.35: [0, 0.8, 0], 0.7: [0, -1.4, 0], 0.78: [0, 0.3, 0], 1.05: [0, 0.8, 0], 1.4: [0, -1.4, 0]}),
                 "rotation": K({0: [0, 4, 5], 0.6: [0, -4, -5], 1.3: [0, 4, 5], 1.4: [0, 4, 5]}, "step", [2])},
        "arm_r": {"rotation": K({0: [-18, 0, 4], 0.6: [18, 0, 4], 1.3: [-18, 0, 4], 1.4: [-18, 0, 4]}, "step", [3])},
        "arm_l": {"rotation": K({0: [18, 0, -4], 0.6: [-18, 0, -4], 1.3: [18, 0, -4], 1.4: [18, 0, -4]}, "step", [3])},
        "forearm_r": {"rotation": K({0: [-10, 0, 0]})}, "forearm_l": {"rotation": K({0: [-10, 0, 0]})},
    }}
    # run (overdrive sprint): leaning forward, legs pounding, both arms pumping hard in mechanical clicks
    run_len = 0.6
    h = run_len / 2
    a["run"] = {"loop": True, "animation_length": run_len, "bones": {
        "body": {"rotation": K({0: [16, 0, 0]}), "position": K({0: [0, -1.5, 0], 0.07: [0, 1.2, 0], h: [0, -1.5, 0], h + 0.07: [0, 1.2, 0], run_len: [0, -1.5, 0]})},
        "leg_r": {"rotation": K({0: [42, 0, 0], h: [-42, 0, 0], run_len: [42, 0, 0]})},
        "leg_l": {"rotation": K({0: [-42, 0, 0], h: [42, 0, 0], run_len: [-42, 0, 0]})},
        "shin_r": {"rotation": K({0: [0, 0, 0], h: [10, 0, 0], h + 0.12: [55, 0, 0], run_len: [0, 0, 0]})},
        "shin_l": {"rotation": K({0: [10, 0, 0], 0.12: [55, 0, 0], h: [0, 0, 0], run_len: [10, 0, 0]})},
        "arm_r": {"rotation": K({0: [-62, 0, 10], 0.1: [-62, 0, 10], h: [48, 0, 6], h + 0.1: [48, 0, 6], run_len: [-62, 0, 10]}, "step", [3])},
        "arm_l": {"rotation": K({0: [48, 0, -6], 0.1: [48, 0, -6], h: [-62, 0, -10], h + 0.1: [-62, 0, -10], run_len: [48, 0, -6]}, "step", [3])},
        "forearm_r": {"rotation": K({0: [-45, 0, 0], h: [-10, 0, 0], run_len: [-45, 0, 0]}, "step", [2])},
        "forearm_l": {"rotation": K({0: [-10, 0, 0], h: [-45, 0, 0], run_len: [-10, 0, 0]}, "step", [2])},
        "head": {"rotation": K({0: [-14, 0, 0]})},
        "turbine": {"scale": K({0: [1.1, 1.3, 1.1], h: [1.0, 1.0, 1.0], run_len: [1.1, 1.3, 1.1]})},
    }}
    # vent: the slowdown right after the sprint; hunched over, arms hanging, shaking while it blows steam
    a["vent"] = {"loop": True, "animation_length": 0.5, "bones": {
        "body": {"rotation": K({0: [20, 0, 2], 0.12: [21, 0, -2], 0.25: [20, 0, 2], 0.37: [21, 0, -2], 0.5: [20, 0, 2]}), "position": K({0: [0, -2, 0]})},
        "leg_r": {"rotation": K({0: [-12, 0, 0]})}, "leg_l": {"rotation": K({0: [-12, 0, 0]})},
        "shin_r": {"rotation": K({0: [24, 0, 0]})}, "shin_l": {"rotation": K({0: [24, 0, 0]})},
        "arm_r": {"rotation": K({0: [-6, 0, 10]})}, "arm_l": {"rotation": K({0: [-6, 0, -10]})},
        "head": {"rotation": K({0: [20, 0, 0]})},
        "turbine": {"position": K({0: [0, 0.6, 0], 0.25: [0, 0.2, 0], 0.5: [0, 0.6, 0]})},
    }}

    def jab(side):
        arm, fore = "arm_" + side, "forearm_" + side
        s = 1 if side == "r" else -1
        return {"animation_length": 0.6, "bones": {
            arm: {"rotation": K({0: [0, 0, 0], 0.1: [10, 0, s * 6], 0.18: [-88, s * 6, s * 4], 0.32: [-88, s * 6, s * 4], 0.6: [0, 0, 0]}, "step", [2])},
            fore: {"rotation": K({0: [0, 0, 0], 0.1: [-60, 0, 0], 0.18: [-4, 0, 0], 0.32: [-4, 0, 0], 0.6: [0, 0, 0]})},
            "hull": {"rotation": K({0: [0, 0, 0], 0.1: [0, -s * 12, 0], 0.18: [6, s * 22, 0], 0.32: [6, s * 22, 0], 0.6: [0, 0, 0]}, "step", [2])},
            "body": {"position": K({0: [0, 0, 0], 0.18: [0, 0, -1.5], 0.32: [0, 0, -1.5], 0.6: [0, 0, 0]})},
        }}
    a["jab_right"] = jab("r")
    a["jab_left"] = jab("l")

    # uppercut: crouch and load the right fist low behind the hip, explode upward through the target, hold, recover
    a["uppercut"] = {"animation_length": 1.2, "bones": {
        "body": {"position": K({0: [0, 0, 0], 0.32: [0, -3.5, 1], 0.4: [0, -3.5, 1], 0.5: [0, 2.2, -2], 0.72: [0, 2.2, -2], 1.2: [0, 0, 0]}),
                 "rotation": K({0: [0, 0, 0], 0.32: [18, 0, 0], 0.4: [18, 0, 0], 0.5: [-14, 0, 0], 0.72: [-14, 0, 0], 1.2: [0, 0, 0]})},
        "hull": {"rotation": K({0: [0, 0, 0], 0.32: [0, -34, 8], 0.4: [0, -36, 8], 0.5: [-6, 32, -6], 0.72: [-6, 32, -6], 1.2: [0, 0, 0]})},
        "leg_r": {"rotation": K({0: [0, 0, 0], 0.32: [-28, 0, 0], 0.4: [-28, 0, 0], 0.5: [8, 0, 0], 1.2: [0, 0, 0]})},
        "leg_l": {"rotation": K({0: [0, 0, 0], 0.32: [-22, 0, 0], 0.4: [-22, 0, 0], 0.5: [-4, 0, 0], 1.2: [0, 0, 0]})},
        "shin_r": {"rotation": K({0: [0, 0, 0], 0.32: [42, 0, 0], 0.4: [42, 0, 0], 0.5: [0, 0, 0], 1.2: [0, 0, 0]})},
        "shin_l": {"rotation": K({0: [0, 0, 0], 0.32: [36, 0, 0], 0.4: [36, 0, 0], 0.5: [6, 0, 0], 1.2: [0, 0, 0]})},
        # right arm: from low-behind (loaded) to straight up past the head
        "arm_r": {"rotation": K({0: [0, 0, 0], 0.32: [38, 0, 14], 0.4: [40, 0, 14], 0.46: [-70, 0, 4], 0.52: [-158, 0, -8], 0.72: [-158, 0, -8], 0.9: [-60, 0, 0], 1.2: [0, 0, 0]})},
        "forearm_r": {"rotation": K({0: [0, 0, 0], 0.32: [-22, 0, 0], 0.4: [-22, 0, 0], 0.46: [-70, 0, 0], 0.52: [-28, 0, 0], 0.72: [-28, 0, 0], 1.2: [0, 0, 0]})},
        "fist_r": {"rotation": K({0: [0, 0, 0], 0.4: [0, 0, 0], 0.52: [-20, 0, 0], 0.72: [-20, 0, 0], 1.2: [0, 0, 0]})},
        # left arm guards then swings back for balance
        "arm_l": {"rotation": K({0: [0, 0, 0], 0.32: [-50, 0, -18], 0.4: [-50, 0, -18], 0.52: [32, 0, -24], 0.72: [32, 0, -24], 1.2: [0, 0, 0]}, "step", [2])},
        "forearm_l": {"rotation": K({0: [0, 0, 0], 0.32: [-60, 0, 0], 0.4: [-60, 0, 0], 0.52: [-10, 0, 0], 1.2: [0, 0, 0]})},
        "head": {"rotation": K({0: [0, 0, 0], 0.32: [10, 0, 0], 0.5: [-26, 0, 0], 0.72: [-26, 0, 0], 1.2: [0, 0, 0]})},
        "turbine": {"scale": K({0: [1, 1, 1], 0.4: [1, 1, 1], 0.5: [1.25, 1.8, 1.25], 0.8: [1, 1, 1]})},
        "emblem": {"scale": K({0: [1, 1, 1], 0.4: [1, 1, 1], 0.5: [1.25, 1.25, 1.6], 0.8: [1, 1, 1]})},
    }}
    # rocket grab: the arm snaps forward; the code hides fist_r while the rocket hand is out
    a["grab"] = {"animation_length": 1.4, "bones": {
        "arm_r": {"rotation": K({0: [0, 0, 0], 0.2: [-30, 0, 10], 0.3: [-92, 0, 0], 1.1: [-92, 0, 0], 1.4: [0, 0, 0]}, "step", [3])},
        "forearm_r": {"rotation": K({0: [0, 0, 0], 0.3: [0, 0, 0], 1.4: [0, 0, 0]})},
        "hull": {"rotation": K({0: [0, 0, 0], 0.2: [0, -18, 0], 0.32: [4, 14, 0], 1.1: [4, 14, 0], 1.4: [0, 0, 0]}, "step", [2])},
        "turbine": {"scale": K({0: [1, 1, 1], 0.28: [1, 1, 1], 0.34: [1.2, 2, 1.2], 0.6: [1, 1, 1]})},
    }}
    a["static"] = {"animation_length": 1.0, "bones": {
        "arm_r": {"rotation": K({0: [0, 0, 0], 0.2: [0, 0, 72], 0.8: [0, 0, 72], 1.0: [0, 0, 0]}, "step", [2])},
        "arm_l": {"rotation": K({0: [0, 0, 0], 0.2: [0, 0, -72], 0.8: [0, 0, -72], 1.0: [0, 0, 0]}, "step", [2])},
        "emblem": {"scale": K({0: [1, 1, 1], 0.3: [1.3, 1.3, 1.6], 0.5: [1.1, 1.1, 1.2], 0.7: [1.3, 1.3, 1.6], 1.0: [1, 1, 1]})},
        "head": {"rotation": K({0: [0, 0, 0], 0.2: [-20, 0, 0], 0.8: [-20, 0, 0], 1.0: [0, 0, 0]})},
    }}
    a["overload"] = {"loop": True, "animation_length": 0.5, "bones": {
        "hull": {"rotation": K({0: [16, 0, 3], 0.125: [18, 0, -3], 0.25: [16, 0, 3], 0.375: [18, 0, -3], 0.5: [16, 0, 3]}),
                 "position": K({0: [0, -2, 0]})},
        "arm_r": {"rotation": K({0: [18, 0, -8]})}, "arm_l": {"rotation": K({0: [18, 0, 8]})},
        "forearm_r": {"rotation": K({0: [-6, 0, 0]})}, "forearm_l": {"rotation": K({0: [-6, 0, 0]})},
        "head": {"rotation": K({0: [32, 0, 0], 0.25: [34, 0, 4], 0.5: [32, 0, 0]})},
        "emblem": {"scale": K({0: [1, 1, 1], 0.1: [1.5, 1.5, 2], 0.25: [1, 1, 1], 0.35: [1.5, 1.5, 2], 0.5: [1, 1, 1]})},
        "turbine": {"rotation": K({0: [0, 0, 0], 0.5: [0, 1080, 0]})}}}
    a["assemble"] = {"animation_length": 1.4, "bones": {
        "root": {"scale": K({0: [0.2, 0.2, 0.2], 0.4: [0.2, 0.2, 0.2], 0.7: [1.06, 1.06, 1.06], 0.8: [1, 1, 1]})},
        "hull": {"position": K({0: [0, 12, 0], 0.5: [0, 12, 0], 0.75: [0, 0, 0]}, "easeOutBounce")},
        "arm_r": {"rotation": K({0: [0, 0, 80], 0.8: [0, 0, 80], 1.0: [0, 0, 0]}, "step", [3])},
        "arm_l": {"rotation": K({0: [0, 0, -80], 0.8: [0, 0, -80], 1.0: [0, 0, 0]}, "step", [3])},
        "head": {"position": K({0: [0, -4, 0], 0.9: [0, -4, 0], 1.05: [0, 0.6, 0], 1.15: [0, 0, 0]})},
    }}
    return a
