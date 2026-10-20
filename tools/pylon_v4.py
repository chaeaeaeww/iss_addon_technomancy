"""
Tech Dragon v4 arena pieces (1.6):

* Hextech Pylon: the towers the dragon raises at 30% health. Built after the reference art the user gave: a white-silver
  octagonal shaft with gold zigzag inlay and a glowing blue seam, a gold cage collar, a dark globe with a gold equator
  and a hextech "eye" facing the dragon, two big gold gear arcs either side, and three runic rings floating in front of
  the eye while it charges. Native 9 blocks tall, rendered at 2x (18 blocks, about the dragon's size).
* Hextech Shell: the sphere of dark gold-framed plates that closes around the dying dragon before it explodes
  (26 plates on the faces of a rhombicuboctahedron), with an inner core whose light leaks through the seams.

Both are code-built and painted like the dragon (dragon_v4 Dragon/Cube/build), animations baked with anim_v4.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

import anim_v4 as A
import dragon_v4 as D4
from dragon_v4 import BLUE, CLEAR, GOLD, Dragon, glow, h01
from pixelart import rgb, ramp

SILVER = [rgb("4A5262"), rgb("6E7888"), rgb("96A0B0"), rgb("BCC4D0"), rgb("DCE2EA"), rgb("F4F7FA")]
STEEL = [rgb("0C1424"), rgb("16223A"), rgb("223252"), rgb("31466C"), rgb("44608A")]
NAVY = [rgb("070B1C"), rgb("0E1530"), rgb("17214A"), rgb("223064"), rgb("30427E")]
LIGHT = D4.LIGHT


# --------------------------------------------------------------------------------------------- painters

def stone(seam_axis=True, zig=True):
    """White-silver hextech stone: soft vertical gradient, gold zigzag inlay and a glowing centre seam on the sides."""
    def fn(x):
        i, j, w, h, face = x.i, x.j, x.w, x.h, x.face
        lit = LIGHT[face]
        b = min(i, j, w - 1 - i, h - 1 - j)
        if b == 0:
            return GOLD[3] if j < h / 2 else GOLD[1]
        if face in ("up", "down"):
            return ramp(SILVER, (0.55 if face == "up" else 0.3) * lit / 0.9)
        cx = (w - 1) / 2
        if seam_axis and abs(i - cx) < 0.8 and w >= 8:
            return glow(BLUE[4] if (j // 2) % 3 else BLUE[5], BLUE[3])
        if seam_axis and abs(i - cx) < 1.8 and w >= 8:
            return ramp(SILVER, 0.2)
        if zig and w >= 10:
            # chevron/zigzag inlay running up the shaft on both sides of the seam
            u = abs(i - cx) / max(1.0, w / 2)
            v = (x.p[1] / 6.0) % 1.0
            zz = abs(v - 0.5) * 2
            if abs(u - (0.35 + 0.45 * zz)) < 0.08:
                return GOLD[4] if face != "south" else GOLD[2]
            if abs(u - (0.35 + 0.45 * zz)) < 0.14:
                return GOLD[1]
        t = 0.62 + 0.18 * (j / max(1, h - 1)) * -1 + 0.1 + (h01(x.p[0], x.p[1], x.p[2]) - 0.5) * 0.05
        if (x.p[1] % 12.0) < 0.6:
            t -= 0.18
        return ramp(SILVER, t * lit / 0.9)
    return fn


def gold_plate(x):
    i, j, w, h = x.i, x.j, x.w, x.h
    b = min(i, j, w - 1 - i, h - 1 - j)
    t = 0.6 + 0.15 * (1 - j / max(1, h - 1)) - (0.25 if x.face == "down" else 0)
    if b == 0:
        return GOLD[5] if j < h / 2 else GOLD[1]
    if b == 2 and min(w, h) >= 8 and (i + j) % 5 == 0:
        return GOLD[5]
    return ramp(GOLD, t * LIGHT[x.face] / 0.9 + (h01(x.p[0], x.p[1], x.p[2]) - 0.5) * 0.06)


def cage(x):
    """Gold collar with arched windows (cut out) showing the glow inside."""
    i, j, w, h = x.i, x.j, x.w, x.h
    if x.face in ("up", "down"):
        return gold_plate(x)
    period = 8
    k = i % period
    if 2 <= k <= period - 2 and 2 <= j <= h - 3:
        top = 2 + abs(k - period / 2) * 0.8
        if j >= top:
            return CLEAR
    return gold_plate(x)


def core_glow(x):
    return glow(ramp(BLUE, 0.75 + 0.2 * h01(x.i, x.j)), BLUE[4])


def globe(x):
    """Dark steel globe with faint gold continents (concept art) and rivet lines."""
    p = x.p
    lon = math.atan2(p[0], p[2])
    lat = p[1]
    land = math.sin(lon * 3 + lat * 0.4) + math.sin(lon * 5 - lat * 0.25) * 0.6 > 0.9
    t = 0.45 + (0.15 if x.face == "up" else 0) - (0.2 if x.face == "down" else 0)
    if land:
        return ramp(GOLD, 0.35 + 0.2 * h01(math.floor(lon * 10), math.floor(lat)))
    if (x.i + x.j) % 9 == 0:
        return ramp(STEEL, 0.9)
    return ramp(STEEL, t * LIGHT[x.face] / 0.9 + (h01(x.i, x.j, x.p[1]) - 0.5) * 0.06)


def eye_disc(radius, cx, cy):
    def fn(x):
        if x.face not in ("north", "south"):
            return CLEAR
        dx, dy = x.lp[0] - cx, x.lp[1] - cy
        d = math.hypot(dx, dy) / radius
        if d > 1:
            return CLEAR
        if d > 0.86:
            return GOLD[4] if dy > 0 else GOLD[2]
        if d > 0.62:
            a = math.atan2(dy, dx)
            if abs(math.sin(a * 6)) < 0.18:
                return GOLD[5]
            return ramp(GOLD, 0.45 + 0.2 * dy / radius)
        if d > 0.5:
            return GOLD[1]
        if d > 0.3:
            return glow(BLUE[3], BLUE[3])
        return glow(BLUE[5], BLUE[5])
    return fn


def rune_ring(radius, cx, cy, seed):
    """Floating magic circle (both faces): two glowing rings with rune ticks between them, transparent elsewhere."""
    def fn(x):
        if x.face not in ("north", "south"):
            return CLEAR
        dx, dy = x.lp[0] - cx, x.lp[1] - cy
        d = math.hypot(dx, dy) / radius
        a = math.atan2(dy, dx)
        if 0.92 < d <= 1.0 or 0.66 < d < 0.72:
            return glow(BLUE[4], BLUE[4])
        if 0.74 < d < 0.9:
            seg = math.floor((a + math.pi) / (2 * math.pi) * 24)
            frac = ((a + math.pi) / (2 * math.pi) * 24) % 1.0
            if h01(seg, seed) > 0.35 and 0.2 < frac < 0.8 and (abs(d - 0.82) < 0.05 or abs(frac - 0.5) < 0.12):
                return glow(BLUE[3], BLUE[3])
        if 0.3 < d < 0.34:
            return glow(BLUE[3], BLUE[3])
        if d < 0.3 and abs(math.sin(a * 3)) < 0.08 and d > 0.12:
            return glow(BLUE[2], BLUE[2])
        return CLEAR
    return fn


def arc_tooth(x):
    return gold_plate(x)


# --------------------------------------------------------------------------------------------- pylon

PYLON_SPHERE_Y = 122.0


def octo(D, bone, x0, y0, z0, w, h, d, paint, name, **kw):
    """Octagonal prism from an axis-aligned box and a 45-degree copy (centred on x0, z0)."""
    D.cube(bone, [x0 - w / 2, y0, z0 - d / 2], [w, h, d], paint, name, **kw)
    k = 0.78
    D.cube(bone, [x0 - w * k / 2, y0, z0 - d * k / 2], [w * k, h, d * k], paint, name + "_r", rotation=[0, 45, 0], pivot=[x0, y0, z0], **kw)


def build_pylon():
    D = Dragon()
    b = D.bone
    b("root", None, [0, 0, 0])
    b("tower", "root", [0, 0, 0])
    b("head", "tower", [0, PYLON_SPHERE_Y, 0])
    b("globe", "head", [0, PYLON_SPHERE_Y, 0])
    b("eye", "head", [0, PYLON_SPHERE_Y, -16])
    b("arc_l", "head", [0, PYLON_SPHERE_Y, 0])
    b("arc_r", "head", [0, PYLON_SPHERE_Y, 0])
    for k in range(3):
        b("ring%d" % (k + 1), "head", [0, PYLON_SPHERE_Y, -22 - k * 9])
    b("beam", "head", [0, PYLON_SPHERE_Y, -17])
    st = stone()
    plain = stone(seam_axis=False, zig=False)
    # base plinth and steps
    octo(D, "tower", 0, 0, 0, 40, 5, 40, plain, "plinth")
    octo(D, "tower", 0, 5, 0, 32, 5, 32, gold_plate, "step")
    # shaft: lower, middle, upper sections (octagonal, tapering) with seams and zigzag
    octo(D, "tower", 0, 10, 0, 22, 56, 22, st, "shaft_low")
    octo(D, "tower", 0, 66, 0, 18.5, 34, 18.5, st, "shaft_mid")
    octo(D, "tower", 0, 64, 0, 24, 3, 24, gold_plate, "band1")
    # buttress fins on the four sides of the lower shaft
    for k, (o, sz) in enumerate((([11, 10, -2.5], [2, 40, 5]), ([-13, 10, -2.5], [2, 40, 5]), ([-2.5, 10, 11], [5, 40, 2]), ([-2.5, 10, -13], [5, 40, 2]))):
        D.cube("tower", o, sz, plain, "fin%d" % k)
    # gold cage collar and the glowing heart inside it
    octo(D, "tower", 0, 100, 0, 26, 9, 26, cage, "collar")
    octo(D, "tower", 0, 101, 0, 15, 7, 15, core_glow, "collar_glow")
    octo(D, "tower", 0, 109, 0, 20, 3, 20, gold_plate, "neck_ring")
    # globe: stacked octagonal layers
    y = PYLON_SPHERE_Y
    for k, (w, y0, hh) in enumerate(((14, y - 15, 3), (24, y - 12, 6), (30, y - 6, 12), (24, y + 6, 6), (14, y + 12, 3))):
        octo(D, "globe", 0, y0, 0, w, hh, w, globe, "globe%d" % k)
    octo(D, "globe", 0, y - 1.5, 0, 32.5, 3, 32.5, gold_plate, "equator")
    # hextech eye facing -z (the pylon turns to face the dragon)
    D.cube("eye", [-7, y - 7, -16.6], [14, 14, 1.2], eye_disc(7, 0, y), "eye_disc", faces=("north", "south"))
    D.cube("eye", [-4.5, y - 4.5, -16], [9, 9, 1.5], gold_plate, "eye_socket", faces=("east", "west", "up", "down"))
    # gear arcs either side: segments around a semicircle plus teeth
    for side, bone in ((1, "arc_l"), (-1, "arc_r")):
        R = 26.0
        n = 9
        for k in range(n):
            a0 = -80 + 160 * k / (n - 1)
            ar = math.radians(a0)
            cx, cy = side * R * math.cos(ar), y + R * math.sin(ar)
            D.cube(bone, [cx - 1.6, cy - 3.6, -2], [3.2, 7.4, 4], gold_plate, "arc%s%d" % ("l" if side > 0 else "r", k),
                   rotation=[0, 0, -side * (a0)], pivot=[cx, cy, 0])
            tx, ty = side * (R + 3.4) * math.cos(ar), y + (R + 3.4) * math.sin(ar)
            D.cube(bone, [tx - 1.4, ty - 1.4, -1.2], [2.8, 2.8, 2.4], arc_tooth, "tooth%s%d" % ("l" if side > 0 else "r", k),
                   rotation=[0, 0, -side * a0], pivot=[tx, ty, 0])
        # struts from the collar up to the arc
        D.cube(bone, [side * 12 - 1.5, y - 22, -1.5], [3, 10, 3], gold_plate, "strut" + ("l" if side > 0 else "r"),
               rotation=[0, 0, side * 40], pivot=[side * 12, y - 22, 0])
    # runic rings (both faces painted), the farther ones bigger
    for k in range(3):
        r = 9 + k * 3.5
        z = -22 - k * 9
        D.cube("ring%d" % (k + 1), [-r, y - r, z - 0.1], [2 * r, 2 * r, 0.2], rune_ring(r, 0, y, k), "ring%d" % k, faces=("north", "south"))
    return D


def pylon_animations(D):
    rig = A.Rig.__new__(A.Rig)
    rig.D = D
    import rig_v4
    rig.skel = rig_v4.Skeleton(D.bones)
    rig.rest = rig.skel.rest_world()
    rig.piv = {}
    rig.legs = {}
    D.panels = []
    out = {}
    rise = Anim("rise", 2.4, "hold")
    rise.seq([(0.0, {"tower@pos": [0, -150, 0], "ring1@scale": [0.01, 0.01, 1], "ring2@scale": [0.01, 0.01, 1], "ring3@scale": [0.01, 0.01, 1],
                     "arc_l": [0, 0, -60], "arc_r": [0, 0, 60]}, "smooth"),
              (1.6, {"tower@pos": [0, 3, 0], "ring1@scale": [0.01, 0.01, 1], "ring2@scale": [0.01, 0.01, 1], "ring3@scale": [0.01, 0.01, 1],
                     "arc_l": [0, 0, -20], "arc_r": [0, 0, 20]}, "out2"),
              (1.9, {"tower@pos": [0, 0, 0], "ring1@scale": [1, 1, 1], "ring2@scale": [0.4, 0.4, 1], "ring3@scale": [0.01, 0.01, 1]}, "smooth"),
              (2.4, {"tower@pos": [0, 0, 0], "ring1@scale": [1, 1, 1], "ring2@scale": [1, 1, 1], "ring3@scale": [1, 1, 1]}, "back")])
    rise.layer(lambda t: {"tower": [0, 0, 1.5 * math.sin(t * 40) * max(0.0, 1 - t / 1.6)]})
    charge = Anim("charge", 4.0, True)
    charge.key(0, {}).key(4.0, {})
    charge.layer(lambda t: {"ring1": [0, 0, 90 * t], "ring2": [0, 0, -60 * t], "ring3": [0, 0, 45 * t], "globe": [0, 90 * t, 0],
                            "arc_l": [0, 0, 6 * math.sin(2 * math.pi * t / 4.0)], "arc_r": [0, 0, -6 * math.sin(2 * math.pi * t / 4.0)],
                            "eye@scale": [1 + 0.08 * math.sin(2 * math.pi * t / 0.5)] * 3,
                            "ring2@pos": [0, 0, -1.5 * math.sin(2 * math.pi * t / 2.0)], "ring3@pos": [0, 0, -3 * math.sin(2 * math.pi * t / 2.0)]})
    collapse = Anim("collapse", 2.0, "hold")
    collapse.seq([(0.0, {}, "smooth"), (0.3, {"tower": [0, 0, 4], "head": [10, 0, 0], "ring1@scale": [0.01, 0.01, 1], "ring2@scale": [0.01, 0.01, 1],
                                               "ring3@scale": [0.01, 0.01, 1]}, "out2"),
                  (2.0, {"tower@pos": [0, -150, 0], "tower": [0, 0, 12], "head": [30, 0, 0], "ring1@scale": [0.01, 0.01, 1], "ring2@scale": [0.01, 0.01, 1],
                         "ring3@scale": [0.01, 0.01, 1], "arc_l": [0, 0, -50], "arc_r": [0, 0, 50]}, "in2")])
    for a in (rise, charge, collapse):
        out[a.name] = A.bake(rig, a)
    return {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": out}


Anim = A.Anim

# --------------------------------------------------------------------------------------------- hextech shell

SHELL_R = 72.0
SHELL_Y = 72.0


def shell_normals():
    out = []
    for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        out.append((np.array(v, float), 1.0))
    for a in range(3):
        for s1 in (1, -1):
            for s2 in (1, -1):
                v = [0.0, 0.0, 0.0]
                v[a] = s1
                v[(a + 1) % 3] = s2
                out.append((np.array(v) / math.sqrt(2), 1.0))
    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                out.append((np.array([sx, sy, sz], float) / math.sqrt(3), 0.62))
    return out


def shell_plate(seed):
    def fn(x):
        i, j, w, h = x.i, x.j, x.w, x.h
        if x.face not in ("north", "south"):
            return ramp(GOLD, 0.4)
        b = min(i, j, w - 1 - i, h - 1 - j)
        if b <= 1:
            return GOLD[4] if (i + j) % 2 else GOLD[2]
        if b == 2:
            return GOLD[1]
        if x.face == "south":  # inner face: lit from the core
            return glow(ramp(BLUE, 0.4 + 0.2 * h01(i, j)), BLUE[2])
        cx, cy = (w - 1) / 2, (h - 1) / 2
        # gold rune glyphs: concentric square + diagonal strokes chosen by seed
        u, v = (i - cx) / (w / 2), (j - cy) / (h / 2)
        r = max(abs(u), abs(v))
        if abs(r - 0.55) < 0.04 and h01(math.floor((math.atan2(v, u) + math.pi) * 2), seed) > 0.3:
            return GOLD[3]
        if r < 0.45:
            k = int(h01(seed, 3) * 4)
            strokes = [abs(u - v) < 0.06, abs(u + v) < 0.06, abs(u) < 0.05, abs(v) < 0.05]
            if strokes[k] or strokes[(k + 1) % 4] and r < 0.3:
                return GOLD[4]
            if abs(r - 0.2) < 0.04:
                return glow(BLUE[3], BLUE[3])
        if b == 3:
            return glow(BLUE[2], BLUE[1])
        return ramp(NAVY, 0.45 + 0.25 * (1 - j / max(1, h - 1)) + (h01(i, j, seed) - 0.5) * 0.08)
    return fn


def build_shell():
    D = Dragon()
    D.bone("root", None, [0, 0, 0])
    D.bone("core", "root", [0, SHELL_Y, 0])
    D.cube("core", [-20, SHELL_Y - 20, -20], [40, 40, 40], core_glow, "core_box")
    D.cube("core", [-16, SHELL_Y - 16, -16], [32, 32, 32], core_glow, "core_box2", rotation=[45, 45, 0], pivot=[0, SHELL_Y, 0])
    plates = []
    for k, (n, size) in enumerate(shell_normals()):
        rx = math.degrees(math.asin(max(-1.0, min(1.0, -n[1]))))
        ry = math.degrees(math.atan2(-n[0], -n[2]))
        name = "plate%d" % k
        D.bone(name, "root", [0, SHELL_Y, 0], [rx, ry, 0])
        a = 2 * SHELL_R * math.tan(math.radians(22.5)) * size + 2
        D.cube(name, [-a / 2, SHELL_Y - a / 2, -SHELL_R - 1], [a, a, 2], shell_plate(k), "plate%d" % k)
        plates.append((name, n))
    return D, plates


def shell_animations(D, plates):
    rig = A.Rig.__new__(A.Rig)
    rig.D = D
    import rig_v4
    rig.skel = rig_v4.Skeleton(D.bones)
    rig.rest = rig.skel.rest_world()
    rig.piv, rig.legs = {}, {}
    D.panels = []
    out = {}
    assemble = Anim("assemble", 3.0, "hold")
    burst = Anim("burst", 0.8, "hold")
    for k, (name, n) in enumerate(plates):
        delay = 0.15 + 1.6 * h01(k, 7)
        far = (n * 150).tolist()
        spin = [(h01(k, 1) - 0.5) * 200, (h01(k, 2) - 0.5) * 200, (h01(k, 3) - 0.5) * 200]
        assemble.key(0.0, {name + "@pos!": far, name + "!": spin, name + "@scale!": [0.3, 0.3, 0.3]}, "smooth")
        assemble.key(delay, {name + "@pos!": far, name + "!": spin, name + "@scale!": [0.3, 0.3, 0.3]}, "smooth")
        assemble.key(delay + 1.0, {name + "@pos!": (n * -2).tolist(), name + "!": [0, 0, 0], name + "@scale!": [1, 1, 1]}, "out")
        assemble.key(delay + 1.15, {name + "@pos!": [0, 0, 0], name + "!": [0, 0, 0], name + "@scale!": [1, 1, 1]}, "smooth")
        assemble.key(3.0, {name + "@pos!": [0, 0, 0], name + "!": [0, 0, 0], name + "@scale!": [1, 1, 1]}, "smooth")
        burst.key(0.0, {name + "@pos!": [0, 0, 0], name + "!": [0, 0, 0]}, "smooth")
        burst.key(0.8, {name + "@pos!": (n * 260).tolist(), name + "!": [s * 2 for s in spin]}, "out")
    assemble.key(0.0, {"core@scale": [0.2, 0.2, 0.2]}).key(2.0, {"core@scale": [0.5, 0.5, 0.5]}).key(3.0, {"core@scale": [0.8, 0.8, 0.8]})
    charge = Anim("charge", 1.0, True)
    charge.key(0, {"core@scale": [0.85, 0.85, 0.85]}).key(0.5, {"core@scale": [1.0, 1.0, 1.0]}).key(1.0, {"core@scale": [0.85, 0.85, 0.85]})

    def rattle(t):
        out_ = {}
        for k, (name, n) in enumerate(plates):
            d = 1.2 * (0.5 + 0.5 * math.sin(t * 40 + k * 1.3))
            out_[name + "@pos!"] = (n * d).tolist()
        return out_
    charge.layer(rattle)
    burst.key(0.0, {"core@scale": [1, 1, 1]}).key(0.25, {"core@scale": [2.6, 2.6, 2.6]}, "out").key(0.8, {"core@scale": [0.01, 0.01, 0.01]}, "in2")
    for a in (assemble, charge, burst):
        out[a.name] = A.bake(rig, a)
    return {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": out}


# --------------------------------------------------------------------------------------------- flat textures

def shield_texture(size=128):
    """Tileable hexagon energy pattern for the dragon's shield (drawn additive/translucent by the renderer)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    hexr = size / 8.0
    for y in range(size):
        for x in range(size):
            # axial hex grid distance to nearest edge
            q = (x * math.sqrt(3) / 3 - y / 3) / hexr
            r = (y * 2 / 3) / hexr
            cx, cz = q, r
            cy = -cx - cz
            rx, ry, rz = round(cx), round(cy), round(cz)
            dx, dy, dz = abs(rx - cx), abs(ry - cy), abs(rz - cz)
            if dx > dy and dx > dz:
                rx = -ry - rz
            elif dy > dz:
                ry = -rx - rz
            else:
                rz = -rx - ry
            d = max(abs(cx - rx), abs(cy - ry), abs(cz - rz))
            edge = max(0.0, (d - 0.36) / 0.14)
            a = int(min(255, 40 + 215 * edge ** 2))
            c = (int(140 + 115 * edge), int(200 + 55 * edge), 255, a)
            px[x, y] = c
    return img


def beam_texture():
    img = Image.new("RGBA", (16, 64), (0, 0, 0, 0))
    px = img.load()
    for y in range(64):
        for x in range(16):
            d = abs(x - 7.5) / 7.5
            core = max(0.0, 1 - d * 1.6)
            flick = 0.75 + 0.25 * math.sin(y * 0.8)
            a = int(255 * min(1.0, (core * 1.2 + (1 - d) * 0.35) * flick))
            px[x, y] = (int(150 + 105 * core), int(210 + 45 * core), 255, a)
    return img


def pylon():
    D = build_pylon()
    geo, img, glw = D4.build(D, "hextech_pylon", tex_w=512, density=2.0, bounds=(8, 10, 4))
    return geo, img, glw, pylon_animations(D)


def shell():
    D, plates = build_shell()
    geo, img, glw = D4.build(D, "hextech_shell", tex_w=1024, density=1.0, bounds=(12, 12, 4))
    return geo, img, glw, shell_animations(D, plates)


if __name__ == "__main__":
    import json
    import sys
    out = sys.argv[1]
    for name, fn in (("hextech_pylon", pylon), ("hextech_shell", shell)):
        geo, img, glw, anims = fn()
        json.dump(geo, open("%s/%s.geo.json" % (out, name), "w"))
        img.save("%s/%s.png" % (out, name))
        glw.save("%s/%s_glowmask.png" % (out, name))
        json.dump(anims, open("%s/%s.animation.json" % (out, name), "w"))
        print(name, img.size)
    shield_texture().save(out + "/dragon_shield.png")
    beam_texture().save(out + "/pylon_beam.png")
