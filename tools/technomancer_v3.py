"""
Technomancer v3 (1.4): a Minecraft-skin style "Hextech Viktor" (references: Prototype Viktor sheets and the original
Viktor splash: dark swept-back hair, goggles with green lenses, red officer coat with gold trim, gold pauldrons, black
glove, brass prosthetic arm with green lights, pinstripe trousers with a brass leg brace, long red cape panels and a
mechanical arm rising from a back rig ending in a green lamp).

Built the way the "3D Skin Layers" mod renders player skins: a normal 1-texel-per-pixel inner layer on the six body
parts, and the outer layer turned into small voxels (1 px cubes sitting on the surface, every face showing the same
texel), which gives hair, collar, goggles, trims and coat tails real depth. Clockwork accessories (pauldrons, back rig,
third arm, cape) are regular cubes at the same 1 texel/px density so everything matches.

Every Iron's Spells casting-mob bone is kept (same names/pivots, armor and item anchors), so ISS animations, held items
and armor still work. The extra bones (cape*, back_arm*, claw_*) are never keyframed; TechnomancerRenderer sets them
from their rest pose every frame (never additively), with a defined idle sway / casting raise / walking cape swing.
"""
import math

import models
from models import C, build
from pixelart import rgb, ramp

DENSITY = 1.0
TEX = 128

SKIN = [rgb("6E5446"), rgb("9A7A68"), rgb("BC9A86"), rgb("D6B8A2"), rgb("E8D0BC")]
HAIR = [rgb("120C0A"), rgb("1E1410"), rgb("2C1E17"), rgb("3D2A20"), rgb("52392B")]
RED = [rgb("3A0808"), rgb("5C0E0E"), rgb("821616"), rgb("A42020"), rgb("C43636")]
GOLD = [rgb("5A3C12"), rgb("86601F"), rgb("B48A34"), rgb("D8B252"), rgb("F2D88C")]
NAVY = [rgb("101420"), rgb("1A2032"), rgb("252D46"), rgb("34405E")]
BLACK = [rgb("0B0B0E"), rgb("15151A"), rgb("202027"), rgb("2D2D36")]
LEATHER = [rgb("24140A"), rgb("3A220F"), rgb("543317"), rgb("6E4520")]
GREEN = [rgb("0A4A2E"), rgb("138C55"), rgb("2CD487"), rgb("8AF5C2"), rgb("E0FFF0")]
IRON = [rgb("1C1E24"), rgb("30333C"), rgb("4A4E58"), rgb("6C717C")]

LIGHT = {"up": 1.0, "north": 0.92, "east": 0.82, "west": 0.82, "south": 0.74, "down": 0.55}

PARTS = {
    # name: (bone, x0, y0, z0, x1, y1, z1)
    "head": ("head", -4, 24, -4, 4, 32, 4),
    "torso": ("torso", -4, 12, -2, 4, 24, 2),
    "arm_r": ("right_arm", -8, 12, -2, -4, 24, 2),
    "arm_l": ("left_arm", 4, 12, -2, 8, 24, 2),
    "leg_r": ("right_leg", -4, 0, -2, 0, 12, 2),
    "leg_l": ("left_leg", 0, 0, -2, 4, 12, 2),
}


def _hash(*v):
    h = 2166136261
    for a in v:
        h = ((h ^ (int(a * 53 + 1000) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (h % 1000) / 1000.0


def sh(colors, face, t, x=0, y=0, z=0, grain=0.06):
    return ramp(colors, t * LIGHT[face] + (_hash(x, y, z) - 0.5) * grain)


def glow(c):
    return (c, c)


# ------------------------------------------------------------------------------------------- inner layer

def base_color(part, face, x, y, z):
    """Inner skin layer; (x, y, z) is the centre of the texel on the part's surface."""
    if part == "head":
        if face in ("up", "south"):
            return sh(HAIR, face, 0.5, x, y, z)
        if face == "down":
            return sh(SKIN, face, 0.5, x, y, z)
        if face in ("east", "west"):
            if y > 28 or z > 0.5:
                return sh(HAIR, face, 0.5, x, y, z)
            if -2 < z < 0 and 25 < y < 27.5:
                return SKIN[1]  # ear
            return sh(SKIN, face, 0.62, x, y, z, 0.02)
        # face (front)
        if y > 30:
            return sh(HAIR, face, 0.45, x, y, z)
        if 26 < y < 27 and abs(x) < 1.0:
            return SKIN[2]  # nose shade
        if 25 < y < 26:
            return SKIN[1] if abs(x) < 1.5 else sh(SKIN, face, 0.6, x, y, z, 0.02)  # mouth line
        if 29 < y < 30 and 0.5 < abs(x) < 3.5:
            return HAIR[2]  # brows
        return sh(SKIN, face, 0.64 - 0.06 * (y < 25.5), x, y, z, 0.02)
    if part == "torso":
        if face == "up":
            return sh(GOLD, face, 0.6, x, y, z)
        if face == "south" and 15 < y < 22 and abs(x) < 3:
            return sh(LEATHER, face, 0.5, x, y, z)  # rig harness
        return sh(RED, face, 0.55 + 0.08 * (y - 12) / 12, x, y, z)
    if part == "arm_r":
        if y < 15.5:
            return sh(BLACK, face, 0.6, x, y, z, 0.04)  # glove
        return sh(RED, face, 0.55, x, y, z)
    if part == "arm_l":
        seg = (y - 12) % 3
        if seg < 0.6:
            return IRON[1]
        return sh(GOLD, face, 0.5 + 0.12 * seg / 3, x, y, z)
    # legs: navy pinstripe trousers, dark boots
    if y < 3:
        return sh(LEATHER, face, 0.35, x, y, z, 0.04)
    if face in ("north", "south") and (x * 2) % 2 < 0.5 and int(x * 2) % 3 == 0:
        return NAVY[3]
    return sh(NAVY, face, 0.5, x, y, z)


# ------------------------------------------------------------------------------------------- outer layer (voxels)

def overlay(part, face, x, y, z):
    """Outer layer texel -> color (or (color, glow)), or None for no voxel."""
    if part == "head":
        if face == "up":
            return sh(HAIR, face, 0.55 + 0.25 * math.sin(x * 2.2 + z * 1.3), x, y, z)
        if face == "south":
            return sh(HAIR, face, 0.5 + 0.2 * math.sin(x * 2.5), x, y, z)
        if face in ("east", "west"):
            if abs(y - 28.5) < 0.6:
                return LEATHER[1]  # goggle strap
            if y > 29 or z > 0:
                return sh(HAIR, face, 0.5 + 0.2 * math.sin(z * 2 + y), x, y, z)
            return None
        if face == "north":
            if y > 30.5:
                # swept-up fringe, uneven
                return sh(HAIR, face, 0.6, x, y, z) if (y > 31 or _hash(x) > 0.35) else None
            if abs(y - 28.5) < 1.1:
                for cx in (-2, 2):
                    d = abs(x - cx)
                    if d < 0.9 and abs(y - 28.5) < 0.6:
                        return glow(GREEN[3] if x * cx > 0 else GREEN[2])  # lens
                    if d < 1.6:
                        return GOLD[3] if y > 28.5 else GOLD[1]  # brass rim
                if abs(y - 28.5) < 0.6:
                    return LEATHER[1]
            return None
        return None
    if part == "torso":
        if face == "north":
            if y > 22.5:
                return GOLD[3]  # high collar
            if abs(x) < 0.5:
                return GOLD[2]  # coat opening trim
            if 13.5 < y < 15:
                return GOLD[4] if abs(x) < 1.5 else LEATHER[2]  # belt + buckle
            for bx in (-1.5, 1.5):
                if abs(x - bx) < 0.5 and y in (16.5, 18.5, 20.5):
                    return GOLD[4]
            d = math.hypot(x - 2.0, y - 20.5)
            if d < 1.6:
                return glow(GREEN[3]) if d < 0.8 else GOLD[3]  # chest core emblem
            return None
        if face in ("east", "west"):
            if y > 22.5:
                return GOLD[3]
            if 13.5 < y < 15:
                return LEATHER[2]
            return None
        if face == "south":
            if y > 22.5:
                return GOLD[2]
            if 13.5 < y < 15:
                return LEATHER[2]
            return None
        return None
    if part == "arm_r":
        if face in ("up", "down"):
            return None
        if 15.5 < y < 17.5:
            return GOLD[3] if y > 16.5 else GOLD[1]  # cuff band
        if 14.5 < y < 15.5:
            return BLACK[3]  # glove cuff
        return None
    if part == "arm_l":
        if face in ("up", "down"):
            return None
        if face == "north" and abs(y - 14.5) < 0.5 and x > 5:
            return glow(GREEN[3])  # green lights (concept art)
        if abs(y - 18.5) < 1.0:
            return GOLD[4] if y > 18.5 else GOLD[2]  # elbow plate
        if abs(y - 13.0) < 0.6:
            return GOLD[3]
        return None
    # legs
    if face in ("up", "down"):
        return None
    if y > 8:
        if y < 8.9:
            return GOLD[3]  # coat-tail hem
        return sh(RED, face, 0.5, x, y, z)  # coat tails over the thighs
    if part == "leg_r" and face in ("north", "west", "east"):
        if 4 < y < 8 and (face == "north" or abs(z) < 1.2):
            if abs(y - 6) < 0.6:
                return GOLD[1]
            return sh(GOLD, face, 0.6, x, y, z)  # brass leg brace
    if 2.5 < y < 3.5:
        return LEATHER[3]  # boot top
    return None


def voxels(part, cubes, registry):
    """Turns the outer layer of a part into 1 px voxels (like the 3D Skin Layers mod)."""
    bone, x0, y0, z0, x1, y1, z1 = PARTS[part]
    t = 1.0 if part == "head" else 0.75
    for face in ("north", "south", "east", "west", "up", "down"):
        if face in ("north", "south"):
            us, vs = range(int(x0), int(x1)), range(int(y0), int(y1))
        elif face in ("east", "west"):
            us, vs = range(int(z0), int(z1)), range(int(y0), int(y1))
        else:
            us, vs = range(int(x0), int(x1)), range(int(z0), int(z1))
        for u in us:
            for v in vs:
                if face in ("north", "south"):
                    px, py = u + 0.5, v + 0.5
                    pz = z0 if face == "north" else z1
                    origin = [u, v, z0 - t] if face == "north" else [u, v, z1]
                    size = [1, 1, t]
                elif face in ("east", "west"):
                    pz, py = u + 0.5, v + 0.5
                    px = x1 if face == "east" else x0
                    origin = [x1, v, u] if face == "east" else [x0 - t, v, u]
                    size = [t, 1, 1]
                else:
                    px, pz = u + 0.5, v + 0.5
                    py = y1 if face == "up" else y0
                    origin = [u, y1, v] if face == "up" else [u, y0 - t, v]
                    size = [1, t, 1]
                r = overlay(part, face, px, py, pz)
                if r is None:
                    continue
                col, gl = (r if isinstance(r, tuple) and len(r) == 2 and isinstance(r[0], tuple) else (r, None))
                add_voxel(cubes, registry, bone, origin, size, col, gl)


def add_voxel(cubes, registry, bone, origin, size, col, gl):
    key = (col, gl)
    name = "vox%d" % len(cubes)
    share = registry.get(key)
    c = C(bone, list(origin), list(size), solid(col, gl), name=name, share=share)
    if share is None:
        registry[key] = name
    cubes.append(c)


def solid(col, gl=None):
    def paint(img, x, y, w, h, face):
        for j in range(h):
            for i in range(w):
                img.putpixel((x + i, y + j), col)
                if gl is not None:
                    models.glow_put(x + i, y + j, gl)
    return paint


class Surf:
    """Paints a cube texel by texel from fn(face, x, y, z) (model-space texel centre)."""

    def __init__(self, fn):
        self.fn = fn
        self.cube_ref = None

    def __call__(self, img, x, y, w, h, face):
        c = self.cube_ref
        ox, oy, oz = c.origin
        sw, sh_, sd = c.size
        for j in range(h):
            for i in range(w):
                fu, fv = (i + 0.5) / w, (j + 0.5) / h
                if face == "north":
                    p = (ox + fu * sw, oy + sh_ - fv * sh_, oz)
                elif face == "south":
                    p = (ox + sw - fu * sw, oy + sh_ - fv * sh_, oz + sd)
                elif face == "east":
                    p = (ox + sw, oy + sh_ - fv * sh_, oz + fu * sd)
                elif face == "west":
                    p = (ox, oy + sh_ - fv * sh_, oz + sd - fu * sd)
                elif face == "up":
                    p = (ox + fu * sw, oy + sh_, oz + sd - fv * sd)
                else:
                    p = (ox + fu * sw, oy, oz + sd - fv * sd)
                r = self.fn(face, *p)
                if r is None:
                    continue
                col, gl = (r if isinstance(r, tuple) and len(r) == 2 and isinstance(r[0], tuple) else (r, None))
                img.putpixel((x + i, y + j), col)
                if gl is not None:
                    models.glow_put(x + i, y + j, gl)


def surf(cubes, bone, origin, size, fn, name, **kw):
    s = Surf(fn)
    c = C(bone, [round(v, 3) for v in origin], [round(v, 3) for v in size], s, name=name, **kw)
    s.cube_ref = c
    cubes.append(c)
    return c


# ------------------------------------------------------------------------------------------- accessories

def gold_fn(face, x, y, z):
    t = {"up": 0.85, "down": 0.3}.get(face, 0.6)
    return sh(GOLD, face, t, x, y, z, 0.08)


def iron_fn(face, x, y, z):
    return sh(IRON, face, 0.55, x, y, z)


def lamp_fn(face, x, y, z):
    return glow(ramp(GREEN, 0.8 + 0.15 * math.sin(x * 3 + y * 2 + z)))


def rig_fn(face, x, y, z):
    if face == "south":
        d = math.hypot(x, y - 18.5)
        if d < 1.1:
            return glow(GREEN[3])
        if d < 2.0:
            return GOLD[4]
    return gold_fn(face, x, y, z)


def cape_fn(face, x, y, z):
    if face in ("east", "west", "up", "down"):
        return GOLD[2]
    t = 0.45 + 0.1 * math.sin(x * 1.7)
    if face == "north":
        t -= 0.15  # inner side is darker
    return sh(RED, face, t, x, y, z, 0.04)


def cape_trim_fn(face, x, y, z):
    return sh(GOLD, face, 0.55, x, y, z, 0.04)


# ------------------------------------------------------------------------------------------- model

def technomancer():
    bones = [
        ("body", None, [0, 12, 0], None),
        ("torso", "body", [0, 24, 0], None),
        ("armorBipedBody", "torso", [0, 24, 0], None),
        ("rig", "torso", [0, 20, 2], None),
        ("back_arm", "rig", [0, 21.5, 4], None),
        ("back_arm2", "back_arm", [0, 33, 5], None),
        ("claw_l", "back_arm2", [1, 36.5, 0], None),
        ("claw_r", "back_arm2", [-1, 36.5, 0], None),
        ("cape_l", "torso", [4.1, 23.5, 3.2], None),
        ("cape_l2", "cape_l", [4.1, 14, 3.2], None),
        ("cape_r", "torso", [-4.1, 23.5, 3.2], None),
        ("cape_r2", "cape_r", [-4.1, 14, 3.2], None),
        ("head", "body", [0, 24, 0], None),
        ("armorBipedHead", "head", [0, 24, 0], None),
        ("right_leg", "body", [-2, 12, 0], None),
        ("armorBipedRightFoot2", "right_leg", [-2, 12, 0], None),
        ("armorBipedRightLeg2", "right_leg", [-2, 12, 0], None),
        ("armorBipedRightLeg", "right_leg", [-2, 12, 0], None),
        ("armorBipedRightFoot", "right_leg", [-2, 12, 0], None),
        ("left_leg", "body", [2, 12, 0], None),
        ("armorBipedLeftFoot2", "left_leg", [2, 12, 0], None),
        ("armorBipedLeftLeg2", "left_leg", [2, 12, 0], None),
        ("armorBipedLeftLeg", "left_leg", [2, 12, 0], None),
        ("armorBipedLeftFoot", "left_leg", [2, 12, 0], None),
        ("right_arm", "body", [-5, 22, 0], None),
        ("armorBipedRightArm", "right_arm", [-5, 22, 0], None),
        ("bipedHandRight", "right_arm", [-6, 13, -1], None),
        ("rightItem", "right_arm", [-6, 12, 0], None),
        ("left_arm", "body", [5, 22, 0], None),
        ("armorBipedLeftArm", "left_arm", [5, 22, 0], None),
        ("bipedHandLeft", "left_arm", [6, 12, -1], None),
        ("leftItem", "bipedHandLeft", [6, 12, 0], None),
    ]
    cubes = []

    def anchor(bone, origin, size, inflate=0.0, rotation=None, pivot=None):
        cubes.append(C(bone, origin, size, None, inflate=inflate, faces=(), rotation=rotation, pivot=pivot))

    # ---- ISS anchor cubes (no faces; used by the armor and held-item layers)
    anchor("armorBipedBody", [-4, 12, -2], [8, 12, 4], 1)
    anchor("armorBipedHead", [-4, 24, -4], [8, 8, 8], 1)
    for b, inf in (("armorBipedRightFoot2", 1), ("armorBipedRightLeg2", 0.5), ("armorBipedRightLeg", 0.5), ("armorBipedRightFoot", 1)):
        anchor(b, [-4, 0, -2], [4, 12, 4], inf)
    for b, inf in (("armorBipedLeftFoot2", 1), ("armorBipedLeftLeg2", 0.5), ("armorBipedLeftLeg", 0.5), ("armorBipedLeftFoot", 1)):
        anchor(b, [0, 0, -2], [4, 12, 4], inf)
    anchor("armorBipedRightArm", [-8, 12, -2], [4, 12, 4], 1)
    anchor("armorBipedLeftArm", [4, 12, -2], [4, 12, 4], 1)
    anchor("bipedHandRight", [-6, 13, -1], [0, 0, 0])
    anchor("rightItem", [-6, 12, 0], [0, 0, 0], rotation=[-90, 0, 0], pivot=[-6, 12, 0])
    anchor("bipedHandLeft", [6, 12, -1], [0, 0, 0])
    anchor("leftItem", [6, 12, 0], [0, 0, 0])

    # ---- inner layer
    for part, (bone, x0, y0, z0, x1, y1, z1) in PARTS.items():
        surf(cubes, bone, [x0, y0, z0], [x1 - x0, y1 - y0, z1 - z0], (lambda p: lambda f, x, y, z: base_color(p, f, x, y, z))(part), part)
    # ---- outer layer as voxels
    registry = {}
    for part in PARTS:
        voxels(part, cubes, registry)

    # ---- clockwork accessories
    # tiered gold pauldrons with a green light on top
    for bone, sgn in (("right_arm", -1), ("left_arm", 1)):
        x_in = 3.6 if sgn > 0 else -8.9
        surf(cubes, bone, [x_in, 21.6, -2.9], [5.3, 3.2, 5.8], gold_fn, "pauldron_%s1" % bone, rotation=[0, 0, 10 * sgn], pivot=[5 * sgn, 23, 0])
        surf(cubes, bone, [x_in + (1.4 if sgn > 0 else 0.2), 19.9, -2.6], [3.7, 2.0, 5.2], gold_fn, "pauldron_%s2" % bone, rotation=[0, 0, 16 * sgn], pivot=[6.5 * sgn, 21, 0])
        surf(cubes, bone, [(6.2 if sgn > 0 else -7.4), 24.6, -0.6], [1.2, 0.7, 1.2], lamp_fn, "pauldron_lamp_%s" % bone)
    # back rig with a green core, mechanical third arm with a lamp between two claws
    surf(cubes, "rig", [-2.4, 15.2, 2.8], [4.8, 6.8, 2], rig_fn, "rig_box")
    surf(cubes, "back_arm", [-0.9, 21.2, 3.7], [1.8, 11.8, 1.8], gold_fn, "arm_lower")
    surf(cubes, "back_arm", [-1.3, 31.8, 3.4], [2.6, 2.6, 2.6], iron_fn, "arm_joint")
    surf(cubes, "back_arm2", [-0.8, 33.4, -0.6], [1.6, 1.6, 6.4], gold_fn, "arm_upper", rotation=[-12, 0, 0], pivot=[0, 34.2, 5])
    surf(cubes, "back_arm2", [-1.1, 34.8, -1.4], [2.2, 2.2, 2.2], lamp_fn, "arm_lamp")
    surf(cubes, "claw_l", [0.9, 34.0, -1.0], [0.7, 3.0, 0.7], gold_fn, "claw_left")
    surf(cubes, "claw_r", [-1.6, 34.0, -1.0], [0.7, 3.0, 0.7], gold_fn, "claw_right")
    # long cape panels from the shoulders (two segments each so they can sway)
    for side, sgn in (("l", 1), ("r", -1)):
        x0 = 2.6 if sgn > 0 else -5.6
        surf(cubes, "cape_" + side, [x0, 14, 2.9], [3.0, 9.6, 0.6], cape_fn, "cape_%s_top" % side)
        surf(cubes, "cape_%s2" % side, [x0, 4.5, 2.9], [3.0, 9.6, 0.6], cape_fn, "cape_%s_bottom" % side)
        surf(cubes, "cape_%s2" % side, [x0 - 0.1, 4.0, 2.85], [3.2, 0.6, 0.7], cape_trim_fn, "cape_%s_hem" % side)

    geo, img, glw = build("technomancer", TEX, bones, cubes, (3, 3.5, 1.5), density=DENSITY)
    return geo, img, glw, {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": {}}
