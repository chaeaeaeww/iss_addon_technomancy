"""
Iron's Technomancy 1.9 worn armour (GeckoLib, Iron's Spells armour bone layout), "Premium Fantasy" preset:

- clockwork_engineer: Create-workshop gear - leather aviator cap with brass goggles (amber lenses), leather coat with
  andesite shoulder plates, a brass cog on the chest, a copper boiler tank on the back with brass pipes, brass cuffs,
  knee plates and toe caps;
- hextech_engineer (ref: "Clockwork Mage Armor"): navy plate with brass trim, a glowing T visor and a crest cog, a big
  brass cog with a cyan core on the chest and a clockwork engine on the back, cog pauldrons, a split robe skirt and
  cyan rune strips. Emissive parts go to the glowmask.

Texture 128x128 at 2 texture px per model px. Every face is painted with hue-shifted ramps (premium.py), lit from the
top-left: lighter top/left edges, darker bottom/right edges, a coloured outline round the face.
"""
import math

from PIL import Image

from premium import MAT

TEX = 160
DENS = 2


class Cube:
    def __init__(self, bone, name, origin, size, paint, inflate=0.0, faces=("north", "east", "south", "west", "up", "down"), share=None, glow=False):
        self.bone, self.name, self.origin, self.size, self.paint = bone, name, origin, size, paint
        self.inflate, self.faces, self.share, self.glow = inflate, faces, share, glow
        self.uv = {}


def face_size(c, face):
    w, h, d = c.size
    return {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}[face]


def pack(cubes):
    owners = {c.name: c for c in cubes}
    faces = [(c, f) for c in cubes if not c.share for f in c.faces]
    faces.sort(key=lambda cf: (-math.ceil(face_size(*cf)[1] * DENS), -math.ceil(face_size(*cf)[0] * DENS)))
    x, y, shelf = 0, 0, 0
    for c, f in faces:
        fw, fh = [max(1, math.ceil(v * DENS)) for v in face_size(c, f)]
        if x + fw > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        c.uv[f] = (x, y, fw, fh)
        x += fw + 1
        shelf = max(shelf, fh)
    assert y + shelf <= TEX, "armour texture overflow (%d)" % (y + shelf)
    for c in cubes:
        if c.share:
            c.uv = dict(owners[c.share].uv)


# ------------------------------------------------------------------------------------------- face painters

def ramp_at(mat, t):
    r = mat.ramp
    return r[max(0, min(len(r) - 1, int(round(t * (len(r) - 1)))))]


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def plate(mat, base=None, edge=True, dither=None, tone=0.0):
    """Bevelled plate: light from the top-left, a lit top/left rim, a dark bottom/right rim, coloured outline."""
    def paint(img, x, y, w, h, face):
        b = (mat.base if base is None else base) + tone + (0.12 if face == "up" else -0.18 if face == "down" else 0)
        dz = mat.dither if dither is None else dither
        for j in range(h):
            for i in range(w):
                v = b + 0.22 * (0.5 - j / max(1, h - 1)) + 0.1 * (0.5 - i / max(1, w - 1))
                if edge:
                    if j == 1 or i == 1:
                        v += 0.18
                    if j == h - 2 or i == w - 2:
                        v -= 0.16
                if dz:
                    v += (BAYER[(y + j) % 4][(x + i) % 4] / 16.0 - 0.47) * 0.12
                col = ramp_at(mat, v)
                if edge and (i == 0 or j == 0 or i == w - 1 or j == h - 1):
                    col = mat.ramp[1] if (i == 0 or j == 0) and mat.base > 0.5 else mat.ramp[0]
                img.putpixel((x + i, y + j), col)
    return paint


def with_details(base, *details):
    def paint(img, x, y, w, h, face):
        base(img, x, y, w, h, face)
        for d in details:
            d(img, x, y, w, h, face)
    return paint


def rivets(mat, step=6, faces=("north", "south", "east", "west")):
    def d(img, x, y, w, h, face):
        if face not in faces or w < 5 or h < 5:
            return
        for (i, j) in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):
            img.putpixel((x + i, y + j), mat.ramp[-1])
            if i + 1 < w and j + 1 < h:
                img.putpixel((x + i + 1, y + j + 1), mat.ramp[1])
    return d


def stripe(mat, vertical=True, pos=0.5, width=1, faces=("north",)):
    def d(img, x, y, w, h, face):
        if face not in faces:
            return
        if vertical:
            cx = x + int(w * pos)
            for j in range(2, h - 2):
                for k in range(width):
                    img.putpixel((cx + k - width // 2, y + j), mat.ramp[5 if k == width // 2 else 3])
        else:
            cy = y + int(h * pos)
            for i in range(2, w - 2):
                for k in range(width):
                    img.putpixel((x + i, cy + k - width // 2), mat.ramp[5 if k == width // 2 else 3])
    return d


def cog_emblem(gear_mat, core_mat, faces=("north",), r_frac=0.42):
    def d(img, x, y, w, h, face):
        if face not in faces:
            return
        cx, cy = x + (w - 1) / 2, y + (h - 1) / 2
        R = min(w, h) * r_frac
        for j in range(h):
            for i in range(w):
                px, py = x + i, y + j
                dx, dy = px - cx, py - cy
                dist = math.hypot(dx, dy)
                a = (math.atan2(dy, dx) / (2 * math.pi) * 8) % 1.0
                if dist <= R * 0.45:
                    t = 0.95 - 0.5 * dist / (R * 0.45) - (dx + dy) * 0.04
                    img.putpixel((px, py), ramp_at(core_mat, t))
                elif dist <= R * 0.78 or (dist <= R and abs(a - 0.5) < 0.22):
                    t = 0.62 - (dx + dy) / (R * 4) + (0.15 if dist > R * 0.72 else 0)
                    img.putpixel((px, py), ramp_at(gear_mat, t))
                elif R < dist <= R + 0.8 or (R * 0.78 < dist <= R * 0.78 + 0.8):
                    img.putpixel((px, py), gear_mat.ramp[0])
    return d


def glyphs(mat, faces=("north",)):
    G = ["#.#.##.#", "##..#.##", ".#.##.#."]

    def d(img, x, y, w, h, face):
        if face not in faces:
            return
        for j in range(3, h - 3, 4):
            row = G[(j // 4) % 3]
            for i in range(3, w - 3):
                if row[(i + j) % len(row)] == "#" and (i + j) % 3:
                    img.putpixel((x + i, y + j), mat.ramp[4])
    return d


def lens(mat):
    def paint(img, x, y, w, h, face):
        for j in range(h):
            for i in range(w):
                dx, dy = (i - (w - 1) / 2) / max(1, w / 2), (j - (h - 1) / 2) / max(1, h / 2)
                img.putpixel((x + i, y + j), ramp_at(mat, 0.95 - 0.55 * math.hypot(dx + 0.3, dy + 0.3)))
        img.putpixel((x + 1, y + 1), mat.ramp[-1])
    return paint


def gear_side(mat):
    def paint(img, x, y, w, h, face):
        plate(mat)(img, x, y, w, h, face)
        if face in ("east", "west") and w >= 4:
            for (i, j) in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
                img.putpixel((x + i, y + j), (0, 0, 0, 0))
    return paint


B, BD, CU, LEA, AND, NAV, IRN = (MAT[k] for k in ("brass", "brass_dark", "copper", "leather", "andesite", "navy", "iron"))
AMB, CYA = MAT["amber_glow"], MAT["cyan_glow"]

HEAD, BODY, RA, LA, RL, LL, RB, LB, TORSO = ("armorHead", "armorBody", "armorRightArm", "armorLeftArm", "armorRightLeg", "armorLeftLeg",
                                            "armorRightBoot", "armorLeftBoot", "armorLeggingTorsoLayer")
BONES = [
    ("bipedHead", None, [0, 24, 0]), ("armorHead", "bipedHead", [0, 24, 0]), ("hat_gear", "armorHead", [4.5, 30, 0]),
    ("bipedBody", None, [0, 24, 0]), ("armorBody", "bipedBody", [0, 24, 0]), ("back_gear", "armorBody", [0, 18, 3.6]),
    ("armorLeggingTorsoLayer", "bipedBody", [0, 24, 0]),
    ("bipedRightArm", None, [-5, 22, 0]), ("armorRightArm", "bipedRightArm", [-5, 22, 0]),
    ("bipedLeftArm", None, [5, 22, 0]), ("armorLeftArm", "bipedLeftArm", [5, 22, 0]),
    ("bipedRightLeg", None, [-2, 12, 0]), ("armorRightLeg", "bipedRightLeg", [-2, 12, 0]), ("armorRightBoot", "bipedRightLeg", [-2, 12, 0]),
    ("bipedLeftLeg", None, [2, 12, 0]), ("armorLeftLeg", "bipedLeftLeg", [2, 12, 0]), ("armorLeftBoot", "bipedLeftLeg", [2, 12, 0]),
]


def mirror_pair(cubes, bone_r, bone_l, name, origin, size, paint, **kw):
    a = Cube(bone_r, name + "_r", origin, size, paint, **kw)
    x, y, z = origin
    w = size[0]
    b = Cube(bone_l, name + "_l", [-(x + w), y, z], size, paint, share=name + "_r", **{k: v for k, v in kw.items() if k != "share"})
    cubes += [a, b]


# ------------------------------------------------------------------------------------------- the two sets

def clockwork_cubes():
    leather = with_details(plate(LEA), rivets(B))
    coat = with_details(plate(LEA), stripe(LEA, True, 0.5, 1, ("north",)), rivets(B, faces=("south",)))
    cubes = [
        Cube(HEAD, "cap", [-4, 24, -4], [8, 8, 8], with_details(plate(LEA), stripe(LEA, False, 0.25, 1, ("north", "east", "west", "south"))), 0.5),
        Cube(HEAD, "band", [-4, 28.6, -4], [8, 1.6, 8], plate(LEA, tone=-0.25), 0.75, ("north", "east", "south", "west")),
        Cube(HEAD, "goggle_r", [-3.6, 28.0, -5.0], [3, 2.8, 1], lens(AMB), 0.0, glow=True),
        Cube(HEAD, "goggle_l", [0.6, 28.0, -5.0], [3, 2.8, 1], lens(AMB), 0.0, share="goggle_r", glow=True),
        Cube(HEAD, "goggle_rim_r", [-3.9, 27.7, -4.8], [3.6, 3.4, 0.6], plate(B), 0.0),
        Cube(HEAD, "goggle_rim_l", [0.3, 27.7, -4.8], [3.6, 3.4, 0.6], plate(B), 0.0, share="goggle_rim_r"),
        Cube(HEAD, "ear_r", [-4.7, 24.6, -1.5], [1, 3, 3], plate(CU), 0.0),
        Cube(HEAD, "ear_l", [3.7, 24.6, -1.5], [1, 3, 3], plate(CU), 0.0, share="ear_r"),
        Cube("hat_gear", "hat_gear", [4.4, 28.5, -1.5], [0.6, 3, 3], gear_side(B), 0.0),
        Cube(BODY, "coat", [-4, 12, -2], [8, 12, 4], coat, 0.75),
        Cube(BODY, "chest_cog", [-2, 17, -3.1], [4, 4, 0.6], with_details(plate(B), cog_emblem(B, AMB, ("north",), 0.5)), 0.0, glow=False),
        Cube(BODY, "belt", [-4, 12.5, -2], [8, 1.6, 4], with_details(plate(LEA, tone=-0.3), stripe(B, False, 0.5, 1, ("north", "south"))), 1.0),
        Cube(BODY, "tank", [-2.6, 13.5, 2.8], [5.2, 8.5, 2.8], with_details(plate(CU), stripe(B, False, 0.2, 2, ("south", "east", "west")),
                                                                         stripe(B, False, 0.8, 2, ("south", "east", "west"))), 0.0),
        Cube(BODY, "pipe_r", [-2.2, 22, 3.6], [1, 3.6, 1], plate(B), 0.0),
        Cube(BODY, "pipe_l", [1.2, 22, 3.6], [1, 3.6, 1], plate(B), 0.0, share="pipe_r"),
        Cube("back_gear", "back_gear", [-1.6, 16.4, 5.6], [3.2, 3.2, 0.6], with_details(plate(B), cog_emblem(B, AMB, ("south",), 0.48)), 0.0),
        Cube(TORSO, "waist", [-4, 12, -2], [8, 12, 4], plate(LEA, tone=-0.15), 0.4),
        Cube(RL, "trouser_r", [-4, 0, -2], [4, 12, 4], plate(LEA, tone=-0.15), 0.3),
        Cube(LL, "trouser_l", [0, 0, -2], [4, 12, 4], plate(LEA, tone=-0.15), 0.3, share="trouser_r"),
        Cube(RL, "knee_r", [-4, 5, -2], [4, 3, 4], with_details(plate(B), rivets(BD)), 0.6, ("north", "east", "west", "up")),
        Cube(LL, "knee_l", [0, 5, -2], [4, 3, 4], with_details(plate(B), rivets(BD)), 0.6, ("north", "east", "west", "up"), share="knee_r"),
        Cube(RB, "boot_r", [-4, 0, -2], [4, 6, 4], leather, 0.8),
        Cube(LB, "boot_l", [0, 0, -2], [4, 6, 4], leather, 0.8, share="boot_r"),
        Cube(RB, "toe_r", [-4, 0, -2.6], [4, 2, 2], plate(B), 0.9, ("north", "east", "west", "up")),
        Cube(LB, "toe_l", [0, 0, -2.6], [4, 2, 2], plate(B), 0.9, ("north", "east", "west", "up"), share="toe_r"),
        Cube(RB, "sole_r", [-4, 0, -2], [4, 1, 4], plate(AND, tone=-0.1), 1.0, ("north", "east", "south", "west", "down")),
        Cube(LB, "sole_l", [0, 0, -2], [4, 1, 4], plate(AND, tone=-0.1), 1.0, ("north", "east", "south", "west", "down"), share="sole_r"),
    ]
    mirror_pair(cubes, RA, LA, "sleeve", [-8, 12, -2], [4, 12, 4], with_details(plate(LEA), stripe(LEA, False, 0.5, 1, ("east", "west", "north", "south"))), inflate=0.6)
    mirror_pair(cubes, RA, LA, "pauldron", [-8.8, 21, -2.6], [5, 3, 5.2], with_details(plate(AND), rivets(B)), inflate=0.5)
    mirror_pair(cubes, RA, LA, "cuff", [-8, 12, -2], [4, 2.5, 4], with_details(plate(B), rivets(BD)), inflate=0.85)
    return cubes


def hextech_cubes():
    navy = with_details(plate(NAV), rivets(B))
    cubes = [
        Cube(HEAD, "helm", [-4, 24, -4], [8, 8, 8], with_details(plate(NAV), stripe(B, False, 0.12, 2, ("north", "east", "west", "south"))), 0.7),
        Cube(HEAD, "visor_bar", [-3.4, 28.4, -4.9], [6.8, 1.4, 0.6], plate(CYA), 0.0, glow=True),
        Cube(HEAD, "visor_stem", [-0.7, 25.2, -4.9], [1.4, 3.4, 0.6], plate(CYA), 0.0, glow=True),
        Cube(HEAD, "crest", [-0.8, 31.2, -4.9], [1.6, 2.8, 9.8], with_details(plate(B), rivets(BD, faces=("east", "west"))), 0.0),
        Cube(HEAD, "cheek_r", [-4.9, 24.4, -4.9], [1.2, 3.6, 4], plate(B), 0.0),
        Cube(HEAD, "cheek_l", [3.7, 24.4, -4.9], [1.2, 3.6, 4], plate(B), 0.0, share="cheek_r"),
        Cube("hat_gear", "hat_gear", [4.6, 28, -2], [0.6, 4, 4], gear_side(B), 0.0),
        Cube(BODY, "plate", [-4, 12, -2], [8, 12, 4], with_details(plate(NAV), stripe(CYA, True, 0.5, 1, ("north",)), glyphs(CYA, ("south",))), 0.85),
        Cube(BODY, "chest_cog", [-2.6, 16.4, -3.3], [5.2, 5.2, 0.8], with_details(plate(B), cog_emblem(B, CYA, ("north",), 0.5)), 0.0),
        Cube(BODY, "collar", [-4.4, 22.5, -2.4], [8.8, 1.6, 4.8], plate(B), 0.6),
        Cube(BODY, "engine", [-3, 13.2, 3], [6, 9, 2.6], with_details(plate(NAV, tone=-0.1), stripe(B, False, 0.15, 2, ("south", "east", "west"))), 0.0),
        Cube("back_gear", "back_gear", [-2, 16, 5.8], [4, 4, 0.6], with_details(plate(B), cog_emblem(B, CYA, ("south",), 0.5)), 0.0),
        Cube(BODY, "skirt_f", [-4.2, 6.5, -2.9], [8.4, 6.5, 0.8], with_details(plate(NAV), stripe(B, True, 0.5, 2, ("north",)), stripe(CYA, True, 0.5, 1, ("north",))), 0.0),
        Cube(BODY, "skirt_b", [-4.2, 6.5, 2.1], [8.4, 6.5, 0.8], with_details(plate(NAV), stripe(B, True, 0.5, 2, ("south",))), 0.0),
        Cube(TORSO, "waist", [-4, 12, -2], [8, 12, 4], with_details(plate(NAV, tone=-0.1), stripe(B, False, 0.9, 2, ("north", "south", "east", "west"))), 0.45),
        Cube(RL, "greave_r", [-4, 0, -2], [4, 12, 4], with_details(plate(NAV), stripe(CYA, True, 0.5, 1, ("north",))), 0.35),
        Cube(LL, "greave_l", [0, 0, -2], [4, 12, 4], with_details(plate(NAV), stripe(CYA, True, 0.5, 1, ("north",))), 0.35, share="greave_r"),
        Cube(RL, "knee_r", [-4, 4.6, -2], [4, 3.4, 4], with_details(plate(B), rivets(BD)), 0.65, ("north", "east", "west", "up")),
        Cube(LL, "knee_l", [0, 4.6, -2], [4, 3.4, 4], with_details(plate(B), rivets(BD)), 0.65, ("north", "east", "west", "up"), share="knee_r"),
        Cube(RB, "boot_r", [-4, 0, -2], [4, 6, 4], navy, 0.8),
        Cube(LB, "boot_l", [0, 0, -2], [4, 6, 4], navy, 0.8, share="boot_r"),
        Cube(RB, "boot_plate_r", [-4, 0, -2.7], [4, 3, 2], with_details(plate(B), stripe(CYA, True, 0.5, 1, ("north",))), 0.9, ("north", "east", "west", "up")),
        Cube(LB, "boot_plate_l", [0, 0, -2.7], [4, 3, 2], with_details(plate(B), stripe(CYA, True, 0.5, 1, ("north",))), 0.9, ("north", "east", "west", "up"), share="boot_plate_r"),
    ]
    mirror_pair(cubes, RA, LA, "arm", [-8, 12, -2], [4, 12, 4], with_details(plate(NAV), stripe(CYA, True, 0.5, 1, ("east", "west"))), inflate=0.65)
    mirror_pair(cubes, RA, LA, "pauldron", [-9.2, 20.4, -2.8], [5.6, 3.6, 5.6], with_details(plate(B), cog_emblem(B, CYA, ("east", "west", "up"), 0.42)), inflate=0.5)
    mirror_pair(cubes, RA, LA, "bracer", [-8, 12, -2], [4, 3.4, 4], with_details(plate(B), rivets(BD)), inflate=0.85)
    return cubes


def build(name, cubes):
    pack(cubes)
    img = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    glow = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    for c in cubes:
        if c.share:
            continue
        for face, (x, y, w, h) in c.uv.items():
            c.paint(img, x, y, w, h, face)
            for j in range(h):
                for i in range(w):
                    px = img.getpixel((x + i, y + j))
                    # glowing cubes, and the glow-palette pixels painted onto other faces (cyan/amber accents)
                    if px[3] and (c.glow or px in CYA.ramp[3:] or px in AMB.ramp[3:]):
                        glow.putpixel((x + i, y + j), px)
    bones = []
    for bname, parent, pivot in BONES:
        b = {"name": bname, "pivot": pivot}
        if parent:
            b["parent"] = parent
        own = [c for c in cubes if c.bone == bname]
        if own:
            b["cubes"] = []
            for c in own:
                e = {"origin": c.origin, "size": c.size, "uv": {}}
                for face, (x, y, w, h) in c.uv.items():
                    fw, fh = [v * DENS for v in face_size(c, face)]
                    # GeckoLib/Bedrock "east" is the cube's min-x side: the face painted for +x is written as "west"
                    key = {"east": "west", "west": "east"}.get(face, face)
                    e["uv"][key] = {"uv": [x, y + h], "uv_size": [fw, -fh]} if face == "down" else {"uv": [x, y], "uv_size": [fw, fh]}
                if c.inflate:
                    e["inflate"] = c.inflate
                b["cubes"].append(e)
        bones.append(b)
    geo = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry." + name, "texture_width": TEX, "texture_height": TEX,
                        "visible_bounds_width": 4, "visible_bounds_height": 5.5, "visible_bounds_offset": [0, 2.25, 0]},
        "bones": bones}]}
    anims = {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": {"idle": {"loop": True, "animation_length": 4.0, "bones": {
        "hat_gear": {"rotation": {"0.0": {"vector": [0, 0, 0]}, "4.0": {"vector": [360, 0, 0]}}},
        "back_gear": {"rotation": {"0.0": {"vector": [0, 0, 0]}, "4.0": {"vector": [0, 0, -360]}}}}}}}
    return geo, img, glow, anims


def clockwork():
    return build("clockwork_engineer_armor", clockwork_cubes())


def hextech():
    return build("hextech_engineer_armor", hextech_cubes())
