"""
GeckoLib entity models (Brass Sentry, Siege Sentry, Clockwork Automaton, Brass Gear) built from cubes with
per-face UV and painted materials, plus their animations. Glowmasks are produced from cubes flagged as glowing.
"""
import colorsys
import math

from PIL import Image

import armor
from pixelart import BRASS, COPPER, CYAN, IRON, OUTLINE, CLEAR, line, new, noise, put, ramp, rect


class C:
    def __init__(self, bone, origin, size, material, inflate=0.0, glow=False, faces=("north", "east", "south", "west", "up", "down"), share=None, name=None,
                 rotation=None, pivot=None):
        self.bone, self.origin, self.size, self.material = bone, origin, size, material
        self.rotation, self.pivot = rotation, pivot
        self.inflate, self.glow, self.faces, self.share = inflate, glow, faces, share
        self.name = name or "%s_%s" % (bone, id(self))
        self.uv = {}


def face_size(c, face):
    return armor.face_size(c, face)


GLOW = None


def glow_put(x, y, color):
    """Lets a material mark individual pixels as emissive (written to the glowmask of the model being built)."""
    if GLOW is not None and 0 <= x < GLOW.width and 0 <= y < GLOW.height:
        GLOW.putpixel((int(x), int(y)), color)


def pack(cubes, tex, density=1.0):
    owners = {c.name: c for c in cubes}
    faces = [(c, f) for c in cubes if not c.share for f in c.faces]
    faces.sort(key=lambda cf: (-math.ceil(face_size(cf[0], cf[1])[1] * density), -math.ceil(face_size(cf[0], cf[1])[0] * density)))
    x, y, shelf = 0, 0, 0
    for c, face in faces:
        fw, fh = [max(1, math.ceil(v * density)) for v in face_size(c, face)]
        if x + fw > tex:
            x, y, shelf = 0, y + shelf + 1, 0
        c.uv[face] = (x, y, fw, fh)
        x += fw + 1
        shelf = max(shelf, fh)
    assert y + shelf <= tex, "texture overflow (%d)" % (y + shelf)
    for c in cubes:
        if c.share:
            c.uv = dict(owners[c.share].uv)


def build(identifier, tex, bones, cubes, bounds, density=1.0, tex_h=None, bedrock_sides=False):
    """bones: list of (name, parent, pivot, rotation). Returns (geo json, texture, glowmask).
    density = texture pixels per model pixel (UVs are written in texture pixels)."""
    global GLOW
    pack(cubes, tex, density)
    img, glow = new(tex), new(tex)
    GLOW = glow
    for c in cubes:
        if c.share:
            continue
        for face, (x, y, w, h) in c.uv.items():
            c.material(img, x, y, w, h, face)
            if c.glow:
                for j in range(h):
                    for i in range(w):
                        px = img.getpixel((x + i, y + j))
                        if px[3]:
                            glow.putpixel((x + i, y + j), px)
    out_bones = []
    for name, parent, pivot, rotation in bones:
        b = {"name": name, "pivot": pivot}
        if parent:
            b["parent"] = parent
        if rotation:
            b["rotation"] = rotation
        own = [c for c in cubes if c.bone == name]
        if own:
            b["cubes"] = []
            for c in own:
                entry = {"origin": c.origin, "size": c.size, "uv": {}}
                for face, (x, y, w, h) in c.uv.items():
                    fw, fh = [v * density for v in face_size(c, face)]
                    e = {"uv": [x, y + h], "uv_size": [fw, -fh]} if face == "down" else {"uv": [x, y], "uv_size": [fw, fh]}
                    if getattr(c, "flip_u", False):
                        e["uv"][0] += w
                        e["uv_size"][0] = -fw
                    # bedrock_sides (1.9 models): GeckoLib's "east" is the cube's min-x side, so the face painted as +x
                    # is written as "west" (older models keep their in-game look with the old labels)
                    entry["uv"][{"east": "west", "west": "east"}.get(face, face) if bedrock_sides else face] = e
                if c.inflate:
                    entry["inflate"] = c.inflate
                if c.rotation:
                    entry["rotation"] = c.rotation
                    entry["pivot"] = c.pivot if c.pivot else [c.origin[i] + c.size[i] / 2 for i in range(3)]
                b["cubes"].append(entry)
        out_bones.append(b)
    geo = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry." + identifier, "texture_width": tex, "texture_height": tex,
                        "visible_bounds_width": bounds[0], "visible_bounds_height": bounds[1], "visible_bounds_offset": [0, bounds[2], 0]},
        "bones": out_bones}]}
    GLOW = None
    return geo, img, glow


def kf(vector, easing=None):
    k = {"vector": vector}
    if easing:
        k["easing"] = easing
    return k


# ------------------------------------------------------------------------------------------- extra materials

def iron_plate(img, x, y, w, h, face):
    armor.shade_v(IRON, x, y, w, h, img, 0.45 if face != "up" else 0.6, spread=0.45, seed=x * 3 + y * 7, grain=0.05)
    armor.border(img, x, y, w, h, IRON[0])
    line(img, x, y, x + w - 1, y, IRON[4])
    armor.rivets(img, x, y, w, h)


def dark_iron(img, x, y, w, h, face):
    armor.shade_v(IRON, x, y, w, h, img, 0.25, spread=0.3, seed=x + y * 5, grain=0.04)
    armor.border(img, x, y, w, h, IRON[0])


def brass(img, x, y, w, h, face):
    armor.paint_brass_plate(img, x, y, w, h, face)


def brass_dark(img, x, y, w, h, face):
    armor.paint_pauldron(img, x, y, w, h, face)


def copper(img, x, y, w, h, face):
    armor.paint_tank(img, x, y, w, h, face)


def barrel(img, x, y, w, h, face):
    armor.shade_v(IRON, x, y, w, h, img, 0.4, spread=0.5, seed=x + y, grain=0.03)
    if face == "north":
        rect(img, x, y, x + w - 1, y + h - 1, IRON[2])
        if w >= 2 and h >= 2:
            rect(img, x + (w - 1) // 2, y + (h - 1) // 2, x + w // 2, y + h // 2, OUTLINE)
    elif face in ("east", "west", "up", "down") and w >= 4:
        for k in range(1, w, 3):
            line(img, x + k, y, x + k, y + h - 1, IRON[1])


def muzzle_brake(img, x, y, w, h, face):
    armor.paint_pauldron(img, x, y, w, h, face)
    if face == "north" and w >= 3 and h >= 3:
        rect(img, x + 1, y + 1, x + w - 2, y + h - 2, OUTLINE)


def glow_core(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            edge = i in (0, w - 1) or j in (0, h - 1)
            put(img, x + i, y + j, CYAN[1] if edge and w > 2 and h > 2 else CYAN[2])
    if w >= 2 and h >= 2:
        put(img, x, y, CYAN[4])


def grill(img, x, y, w, h, face):
    iron_plate(img, x, y, w, h, face)
    if face in ("north", "south") and h >= 3:
        for k in range(1, h - 1, 2):
            line(img, x + 1, y + k, x + w - 2, y + k, OUTLINE)


def gear_face(img, x, y, w, h, face):
    armor.shade_v(BRASS, x, y, w, h, img, 0.65, spread=0.5, grain=0)
    if face in ("north", "south", "east", "west") and w >= 3 and h >= 3:
        for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
            put(img, cx, cy, CLEAR)
        put(img, x + w // 2, y + h // 2, OUTLINE)
        if w >= 5 and h >= 5:
            put(img, x + w // 2, y + 1, BRASS[1])
            put(img, x + w // 2, y + h - 2, BRASS[1])
            put(img, x + 1, y + h // 2, BRASS[1])
            put(img, x + w - 2, y + h // 2, BRASS[1])


def visor(img, x, y, w, h, face):
    if face == "north":
        rect(img, x, y, x + w - 1, y + h - 1, CYAN[2])
        line(img, x, y, x + w - 1, y, CYAN[4])
        if w >= 4:
            put(img, x + 1, y + h - 1, CYAN[1])
            put(img, x + w - 2, y + h - 1, CYAN[1])
    else:
        dark_iron(img, x, y, w, h, face)


# ------------------------------------------------------------------------------------------- recolor (Mk.II)

def recolor_mk2(img):
    """Gilded war-construct palette: iron becomes crimson-black steel, cyan glow becomes overdrive orange."""
    out = img.copy()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            if not a:
                continue
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if s < 0.18:  # iron / outline greys -> dark crimson steel
                nr, ng, nb = colorsys.hls_to_rgb(0.0, l * 0.9, 0.45)
            elif 0.42 < h < 0.6:  # cyan -> overdrive orange
                nr, ng, nb = colorsys.hls_to_rgb(0.065, min(0.75, l), 0.95)
            elif 0.05 < h < 0.17:  # brass -> brighter gold
                nr, ng, nb = colorsys.hls_to_rgb(h * 1.05, min(0.85, l * 1.08), min(1.0, s * 1.1))
            else:
                nr, ng, nb = r / 255, g / 255, b / 255
            out.putpixel((x, y), (int(nr * 255), int(ng * 255), int(nb * 255), a))
    return out


# ------------------------------------------------------------------------------------------- Brass Sentry

def brass_sentry():
    bones = [("root", None, [0, 0, 0], None), ("base", "root", [0, 8, 0], None)]
    cubes = [
        C("base", [-4, 7, -4], [8, 4, 8], brass_dark, name="base"),
        C("base", [-3, 6, -3], [6, 1, 6], dark_iron),
    ]
    for i, yaw in enumerate((0, 120, 240)):
        bones.append(("leg_mount_%d" % (i + 1), "base", [0, 8, 0], [0, yaw, 0]))
        bones.append(("leg_%d" % (i + 1), "leg_mount_%d" % (i + 1), [0, 8, 3], [25, 0, 0]))
        cubes.append(C("leg_%d" % (i + 1), [-1, 0, 2], [2, 8, 2], iron_plate, name="leg%d" % i, share=None if i == 0 else "leg0"))
        cubes.append(C("leg_%d" % (i + 1), [-1.5, 0, 1.5], [3, 1, 3], brass, name="foot%d" % i, share=None if i == 0 else "foot0"))
    bones += [
        ("head", "base", [0, 13, 0], None),
        ("barrel", "head", [0, 14, -3], None),
        ("muzzle", "barrel", [0, 14, -10], None),
        ("coil", "head", [0, 17, 0], None),
        ("gear_l", "head", [3.5, 14, 0], None),
        ("gear_r", "head", [-3.5, 14, 0], None),
        ("vent", "head", [0, 15, 3], None),
    ]
    cubes += [
        C("head", [-3, 11, -3], [6, 6, 6], brass, name="head"),
        C("head", [-2, 14, -3.4], [4, 2, 0.5], visor),
        C("barrel", [-1, 13, -10], [2, 2, 7], barrel),
        C("muzzle", [-1.5, 12.5, -11], [3, 3, 1], muzzle_brake, glow=False),
        C("coil", [-2, 17, -2], [4, 2, 4], glow_core, glow=True),
        C("gear_l", [3, 11.5, -2.5], [1, 5, 5], gear_face, name="gear_l"),
        C("gear_r", [-4, 11.5, -2.5], [1, 5, 5], gear_face, share="gear_l"),
        C("vent", [-1, 14, 3], [2, 3, 2], copper),
    ]
    geo, img, glow = build("brass_sentry", 64, bones, cubes, (2, 2.5, 0.75))
    legs = ["leg_1", "leg_2", "leg_3"]
    spawn = {"root": {"position": {"0.0": kf([0, -10, 0]), "0.6": kf([0, 1, 0], "easeOutBack"), "0.75": kf([0, 0, 0], "easeInOutSine")}},
             "head": {"scale": {"0.0": kf([0.2, 0.2, 0.2]), "0.5": kf([0.2, 0.2, 0.2]), "0.8": kf([1.1, 1.1, 1.1], "easeOutBack"), "1.0": kf([1, 1, 1])}}}
    despawn = {"root": {"position": {"0.0": kf([0, 0, 0]), "0.3": kf([0, 1, 0], "easeOutSine"), "0.75": kf([0, -10, 0], "easeInBack")}},
               "head": {"scale": {"0.0": kf([1, 1, 1]), "0.45": kf([0.2, 0.2, 0.2], "easeInBack")}}}
    for leg in legs:
        spawn[leg] = {"rotation": {"0.0": kf([-75, 0, 0]), "0.3": kf([-75, 0, 0]), "0.65": kf([0, 0, 0], "easeOutBounce")}}
        despawn[leg] = {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([-75, 0, 0], "easeInSine")}}
    anims = {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": {
        "spawn": {"animation_length": 1.0, "bones": spawn},
        "idle": {"loop": True, "animation_length": 2.0, "bones": {
            "gear_l": {"rotation": {"0.0": kf([0, 0, 0]), "2.0": kf([360, 0, 0])}},
            "gear_r": {"rotation": {"0.0": kf([0, 0, 0]), "2.0": kf([-360, 0, 0])}},
            "coil": {"scale": {"0.0": kf([1, 1, 1]), "1.0": kf([1.08, 1.0, 1.08], "easeInOutSine"), "2.0": kf([1, 1, 1], "easeInOutSine")}},
            "vent": {"position": {"0.0": kf([0, 0, 0]), "1.8": kf([0, 0, 0]), "1.9": kf([0, 0.3, 0]), "2.0": kf([0, 0, 0])}}}},
        "overclock": {"loop": True, "animation_length": 0.6667, "bones": {
            "gear_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.6667": kf([360, 0, 0])}},
            "gear_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.6667": kf([-360, 0, 0])}},
            "coil": {"scale": {"0.0": kf([1, 1, 1]), "0.1667": kf([1.2, 1.1, 1.2]), "0.3333": kf([1, 1, 1]), "0.5": kf([1.2, 1.1, 1.2]), "0.6667": kf([1, 1, 1])}},
            "barrel": {"position": {"0.0": kf([0, 0, 0]), "0.0833": kf([0.1, 0, 0]), "0.1667": kf([-0.1, 0, 0]), "0.25": kf([0, 0, 0])}},
            "vent": {"scale": {"0.0": kf([1, 1, 1]), "0.3333": kf([1.15, 1.2, 1.15]), "0.6667": kf([1, 1, 1])}}}},
        "shoot": {"animation_length": 0.25, "bones": {
            "barrel": {"position": {"0.0": kf([0, 0, 0]), "0.05": kf([0, 0, 1.5], "easeOutQuad"), "0.25": kf([0, 0, 0], "easeInOutSine")}},
            "muzzle": {"scale": {"0.0": kf([1, 1, 1]), "0.05": kf([1.4, 1.4, 1.4]), "0.2": kf([1, 1, 1])}}}},
        "despawn": {"animation_length": 0.75, "loop": "hold_on_last_frame", "bones": despawn},
    }}
    return geo, img, glow, anims


# ------------------------------------------------------------------------------------------- Siege Sentry

def siege_sentry():
    bones = [("root", None, [0, 0, 0], None), ("base", "root", [0, 6, 0], None)]
    cubes = [
        C("base", [-7, 0, -7], [14, 3, 14], dark_iron, name="plinth"),
        C("base", [-5.5, 3, -5.5], [11, 3, 11], brass_dark, name="ring"),
    ]
    for i, yaw in enumerate((45, 135, 225, 315)):
        mount = "leg_mount_%d" % (i + 1)
        bones.append((mount, "base", [0, 3, 0], [0, yaw, 0]))
        bones.append(("leg_%d" % (i + 1), mount, [0, 4, 5], None))
        cubes.append(C("leg_%d" % (i + 1), [-1.5, 0, 5], [3, 4, 6], iron_plate, name="strut%d" % i, share=None if i == 0 else "strut0"))
        cubes.append(C("leg_%d" % (i + 1), [-2, 0, 10], [4, 1.5, 3], brass, name="pad%d" % i, share=None if i == 0 else "pad0"))
    bones += [
        ("head", "base", [0, 10, 0], None),
        ("armor_l", "head", [6, 10, 0], None),
        ("armor_r", "head", [-6, 10, 0], None),
        ("barrel_l", "head", [-2.5, 10, -5], None),
        ("barrel_r", "head", [2.5, 10, -5], None),
        ("muzzle_l", "barrel_l", [-2.5, 10, -15], None),
        ("muzzle_r", "barrel_r", [2.5, 10, -15], None),
        ("coil", "head", [0, 15, 0], None),
        ("gear_back", "head", [0, 10.5, 5.5], None),
        ("drum", "head", [6.5, 9, 0], None),
        ("exhaust", "head", [0, 13, 3.5], None),
    ]
    cubes += [
        C("head", [-5, 6, -5], [10, 7, 10], brass, name="housing"),
        C("head", [-3.5, 13, -3.5], [7, 2, 7], copper, name="dome"),
        C("head", [-3, 9.5, -5.6], [6, 1.5, 0.6], visor, name="slit"),
        C("armor_l", [5, 6.5, -4], [1.5, 6, 8], iron_plate, name="side_plate"),
        C("armor_r", [-6.5, 6.5, -4], [1.5, 6, 8], iron_plate, share="side_plate"),
        C("barrel_l", [-3.5, 9, -14], [2, 2, 9], barrel, name="barrel"),
        C("barrel_r", [1.5, 9, -14], [2, 2, 9], barrel, share="barrel"),
        C("barrel_l", [-3.75, 8.75, -10], [2.5, 2.5, 1], brass, name="band"),
        C("barrel_r", [1.25, 8.75, -10], [2.5, 2.5, 1], brass, share="band"),
        C("muzzle_l", [-4, 8.5, -16], [3, 3, 2], muzzle_brake, name="brake"),
        C("muzzle_r", [1, 8.5, -16], [3, 3, 2], muzzle_brake, share="brake"),
        C("coil", [-1.5, 15, -1.5], [3, 3, 3], glow_core, glow=True, name="coil"),
        C("coil", [-2, 14.5, -2], [4, 0.5, 4], brass, name="coil_cap"),
        C("gear_back", [-3.5, 7, 5], [7, 7, 1], gear_face, name="gear_back"),
        C("drum", [6.5, 7, -2], [3, 4, 4], copper, name="drum"),
        C("exhaust", [2.5, 13, 2.5], [1.2, 4, 1.2], dark_iron, name="pipe_a"),
        C("exhaust", [-3.7, 13, 2.5], [1.2, 4, 1.2], dark_iron, share="pipe_a"),
    ]
    geo, img, glow = build("siege_sentry", 96, bones, cubes, (3.5, 3, 0.75))
    legs = ["leg_%d" % i for i in range(1, 5)]
    spawn = {"root": {"position": {"0.0": kf([0, -14, 0]), "0.7": kf([0, 1.5, 0], "easeOutBack"), "0.85": kf([0, 0, 0], "easeInOutSine")}},
             "head": {"scale": {"0.0": kf([0.3, 0.3, 0.3]), "0.6": kf([0.3, 0.3, 0.3]), "0.9": kf([1.12, 1.12, 1.12], "easeOutBack"), "1.1": kf([1, 1, 1])}},
             "barrel_l": {"position": {"0.0": kf([0, 0, 6]), "0.9": kf([0, 0, 6]), "1.2": kf([0, 0, 0], "easeOutBack")}},
             "barrel_r": {"position": {"0.0": kf([0, 0, 6]), "0.95": kf([0, 0, 6]), "1.25": kf([0, 0, 0], "easeOutBack")}}}
    despawn = {"root": {"position": {"0.0": kf([0, 0, 0]), "0.3": kf([0, 1, 0]), "0.75": kf([0, -14, 0], "easeInBack")}},
               "barrel_l": {"position": {"0.0": kf([0, 0, 0]), "0.25": kf([0, 0, 6], "easeInSine")}},
               "barrel_r": {"position": {"0.0": kf([0, 0, 0]), "0.25": kf([0, 0, 6], "easeInSine")}}}
    for k, leg in enumerate(legs):
        spawn[leg] = {"rotation": {"0.0": kf([-80, 0, 0]), "0.4": kf([-80, 0, 0]), "0.75": kf([0, 0, 0], "easeOutBounce")}}
        despawn[leg] = {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([-80, 0, 0], "easeInSine")}}

    def recoil(side):
        return {"barrel_" + side: {"position": {"0.0": kf([0, 0, 0]), "0.04": kf([0, 0, 2.2], "easeOutQuad"), "0.3": kf([0, 0, 0], "easeInOutSine")}},
                "muzzle_" + side: {"scale": {"0.0": kf([1, 1, 1]), "0.04": kf([1.5, 1.5, 1.5]), "0.2": kf([1, 1, 1])}},
                "head": {"position": {"0.0": kf([0, 0, 0]), "0.05": kf([0, 0, 0.4]), "0.3": kf([0, 0, 0])}}}

    anims = {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": {
        "spawn": {"animation_length": 1.3, "bones": spawn},
        "idle": {"loop": True, "animation_length": 3.0, "bones": {
            "gear_back": {"rotation": {"0.0": kf([0, 0, 0]), "3.0": kf([0, 0, 360])}},
            "coil": {"scale": {"0.0": kf([1, 1, 1]), "1.5": kf([1.12, 1.05, 1.12], "easeInOutSine"), "3.0": kf([1, 1, 1], "easeInOutSine")}},
            "drum": {"rotation": {"0.0": kf([0, 0, 0]), "3.0": kf([360, 0, 0])}},
            "exhaust": {"scale": {"0.0": kf([1, 1, 1]), "2.7": kf([1, 1, 1]), "2.85": kf([1.15, 1.25, 1.15]), "3.0": kf([1, 1, 1])}}}},
        "overclock": {"loop": True, "animation_length": 0.75, "bones": {
            "gear_back": {"rotation": {"0.0": kf([0, 0, 0]), "0.75": kf([0, 0, 360])}},
            "drum": {"rotation": {"0.0": kf([0, 0, 0]), "0.75": kf([360, 0, 0])}},
            "coil": {"scale": {"0.0": kf([1, 1, 1]), "0.1875": kf([1.3, 1.2, 1.3]), "0.375": kf([1, 1, 1]), "0.5625": kf([1.3, 1.2, 1.3]), "0.75": kf([1, 1, 1])}},
            "head": {"position": {"0.0": kf([0, 0, 0]), "0.0625": kf([0.1, 0, 0]), "0.125": kf([-0.1, 0, 0]), "0.1875": kf([0, 0, 0])}}}},
        "shoot_left": {"animation_length": 0.3, "bones": recoil("l")},
        "shoot_right": {"animation_length": 0.3, "bones": recoil("r")},
        "despawn": {"animation_length": 0.75, "loop": "hold_on_last_frame", "bones": despawn},
    }}
    return geo, img, glow, anims


# ------------------------------------------------------------------------------------------- Clockwork Automaton

def automaton():
    bones = [
        ("root", None, [0, 0, 0], None),
        ("body", "root", [0, 12, 0], None),
        ("boiler", "body", [0, 17, 3], None),
        ("chimney", "boiler", [2.5, 22, 4.5], None),
        ("gear_back", "boiler", [0, 17, 6.2], None),
        ("head", "body", [0, 22, 0], None),
        ("arm_r", "body", [-6, 20, 0], None),
        ("arm_l", "body", [6, 20, 0], None),
        ("leg_r", "root", [-2.5, 12, 0], None),
        ("leg_l", "root", [2.5, 12, 0], None),
    ]
    cubes = [
        C("body", [-5, 12, -3], [10, 10, 6], brass, name="torso"),
        C("body", [-3, 14, -3.6], [6, 5, 0.6], grill, name="grill"),
        C("body", [-1.5, 18.5, -3.8], [3, 2, 0.8], glow_core, glow=True, name="core"),
        C("body", [-5.5, 11.5, -3.5], [11, 2, 7], dark_iron, name="waist"),
        C("boiler", [-3.5, 13, 3], [7, 8, 3], copper, name="boiler"),
        C("chimney", [1.5, 21, 3.5], [2, 5, 2], dark_iron, name="chimney"),
        C("chimney", [1.25, 25, 3.25], [2.5, 1, 2.5], brass, name="chimney_cap"),
        C("gear_back", [-2.5, 14.5, 6], [5, 5, 0.6], gear_face, name="gear_back"),
        C("head", [-3, 22, -3], [6, 5, 6], iron_plate, name="head"),
        C("head", [-2.5, 23.5, -3.4], [5, 1.5, 0.5], visor, glow=True, name="visor"),
        C("head", [-3.5, 26.5, -3.5], [7, 1, 7], brass, name="brow"),
        C("head", [2.5, 25, -0.5], [0.6, 3, 1], brass, name="antenna"),
        C("arm_r", [-9, 18, -2.5], [4, 4, 5], brass_dark, name="shoulder"),
        C("arm_r", [-8.5, 10, -1.5], [3, 9, 3], iron_plate, name="arm"),
        C("arm_r", [-9, 6.5, -2], [4, 4, 4], brass, name="fist"),
        C("arm_r", [-8.2, 13, -1.9], [0.8, 4, 0.8], copper, name="piston"),
        C("arm_l", [5, 18, -2.5], [4, 4, 5], brass_dark, share="shoulder"),
        C("arm_l", [5.5, 10, -1.5], [3, 9, 3], iron_plate, share="arm"),
        C("arm_l", [5, 6.5, -2], [4, 4, 4], brass, share="fist"),
        C("arm_l", [7.4, 13, -1.9], [0.8, 4, 0.8], copper, share="piston"),
        C("leg_r", [-4, 2, -2], [3, 10, 4], iron_plate, name="leg"),
        C("leg_r", [-4.5, 0, -3.5], [4, 2.5, 5.5], brass_dark, name="foot"),
        C("leg_r", [-4.3, 6, -2.4], [3.6, 2, 0.6], brass, name="knee"),
        C("leg_l", [1, 2, -2], [3, 10, 4], iron_plate, share="leg"),
        C("leg_l", [0.5, 0, -3.5], [4, 2.5, 5.5], brass_dark, share="foot"),
        C("leg_l", [0.7, 6, -2.4], [3.6, 2, 0.6], brass, share="knee"),
    ]
    geo, img, glow = build("clockwork_automaton", 64, bones, cubes, (2, 3, 1))
    anims = {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": {
        "assemble": {"animation_length": 1.0, "bones": {
            "root": {"scale": {"0.0": kf([0.1, 0.1, 0.1]), "0.6": kf([1.08, 1.08, 1.08], "easeOutBack"), "0.8": kf([1, 1, 1])}},
            "head": {"position": {"0.0": kf([0, -4, 0]), "0.6": kf([0, -4, 0]), "0.9": kf([0, 0.5, 0], "easeOutBack"), "1.0": kf([0, 0, 0])}},
            "arm_r": {"rotation": {"0.0": kf([0, 0, -60]), "0.7": kf([0, 0, 0], "easeOutBounce")}},
            "arm_l": {"rotation": {"0.0": kf([0, 0, 60]), "0.7": kf([0, 0, 0], "easeOutBounce")}}}},
        "idle": {"loop": True, "animation_length": 2.0, "bones": {
            "body": {"position": {"0.0": kf([0, 0, 0]), "1.0": kf([0, -0.3, 0], "easeInOutSine"), "2.0": kf([0, 0, 0], "easeInOutSine")}},
            "gear_back": {"rotation": {"0.0": kf([0, 0, 0]), "2.0": kf([0, 0, 360])}},
            "arm_r": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([-3, 0, 2], "easeInOutSine"), "2.0": kf([0, 0, 0], "easeInOutSine")}},
            "arm_l": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([-3, 0, -2], "easeInOutSine"), "2.0": kf([0, 0, 0], "easeInOutSine")}},
            "chimney": {"scale": {"0.0": kf([1, 1, 1]), "1.8": kf([1, 1, 1]), "1.9": kf([1.1, 1.2, 1.1]), "2.0": kf([1, 1, 1])}}}},
        "walk": {"loop": True, "animation_length": 1.0, "bones": {
            "leg_r": {"rotation": {"0.0": kf([30, 0, 0]), "0.5": kf([-30, 0, 0], "easeInOutSine"), "1.0": kf([30, 0, 0], "easeInOutSine")}},
            "leg_l": {"rotation": {"0.0": kf([-30, 0, 0]), "0.5": kf([30, 0, 0], "easeInOutSine"), "1.0": kf([-30, 0, 0], "easeInOutSine")}},
            "arm_r": {"rotation": {"0.0": kf([-25, 0, 0]), "0.5": kf([25, 0, 0], "easeInOutSine"), "1.0": kf([-25, 0, 0], "easeInOutSine")}},
            "arm_l": {"rotation": {"0.0": kf([25, 0, 0]), "0.5": kf([-25, 0, 0], "easeInOutSine"), "1.0": kf([25, 0, 0], "easeInOutSine")}},
            "body": {"position": {"0.0": kf([0, 0, 0]), "0.25": kf([0, 0.6, 0], "easeOutSine"), "0.5": kf([0, 0, 0], "easeInSine"), "0.75": kf([0, 0.6, 0], "easeOutSine"), "1.0": kf([0, 0, 0], "easeInSine")},
                     "rotation": {"0.0": kf([0, 3, 0]), "0.5": kf([0, -3, 0], "easeInOutSine"), "1.0": kf([0, 3, 0], "easeInOutSine")}},
            "gear_back": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([0, 0, 360])}}}},
        "attack": {"animation_length": 0.45, "bones": {
            "arm_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.12": kf([45, 0, 10], "easeOutSine"), "0.22": kf([-100, 0, -5], "easeOutBack"), "0.45": kf([0, 0, 0], "easeInOutSine")}},
            "body": {"rotation": {"0.0": kf([0, 0, 0]), "0.12": kf([0, -15, 0]), "0.22": kf([5, 20, 0], "easeOutBack"), "0.45": kf([0, 0, 0])}}}},
        "volley": {"animation_length": 0.8, "bones": {
            "arm_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.3": kf([-90, 0, 10], "easeOutBack"), "0.6": kf([-90, 0, 10]), "0.8": kf([0, 0, 0], "easeInOutSine")}},
            "arm_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.3": kf([-90, 0, -10], "easeOutBack"), "0.6": kf([-90, 0, -10]), "0.8": kf([0, 0, 0], "easeInOutSine")}},
            "gear_back": {"rotation": {"0.0": kf([0, 0, 0]), "0.6": kf([0, 0, 720], "easeInSine")}},
            "boiler": {"scale": {"0.0": kf([1, 1, 1]), "0.5": kf([1.1, 1.08, 1.1]), "0.6": kf([0.95, 0.95, 0.95]), "0.8": kf([1, 1, 1])}}}},
    }}
    return geo, img, glow, anims


# ------------------------------------------------------------------------------------------- Brass Gear projectile

def gear_projectile():
    bones = [("gear", None, [0, 3, 0], None), ("teeth_diagonal", "gear", [0, 3, 0], [45, 0, 0])]
    teeth = [([-0.5, 5.5, -0.75], [1, 1, 1.5]), ([-0.5, -0.5, -0.75], [1, 1, 1.5]), ([-0.5, 2.25, -3.5], [1, 1.5, 1]), ([-0.5, 2.25, 2.5], [1, 1.5, 1])]
    cubes = [C("gear", [-0.5, 0.5, -2.5], [1, 5, 5], gear_face, name="disc")]
    for i, (o, s) in enumerate(teeth):
        cubes.append(C("gear", o, s, brass, name="t%d" % i))
        cubes.append(C("teeth_diagonal", o, s, brass, share="t%d" % i))
    geo, img, glow = build("gear_projectile", 32, bones, cubes, (1, 1, 0.2))
    anims = {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": {
        "spin": {"loop": True, "animation_length": 0.3333, "bones": {"gear": {"rotation": {"0.0": kf([0, 0, 0]), "0.3333": kf([-360, 0, 0])}}}}}}
    return geo, img, glow, anims
