"""
Clockwork Engineer armor: GeckoLib geo (per-face UV on a 96x96 sheet, same layout conventions as Iron's armors)
plus a painted texture and an orthographic preview renderer for checking the result without launching the game.
"""
import math

from PIL import Image

from pixelart import BRASS, CLOTH, COPPER, CYAN, IRON, LEATHER, OUTLINE, CLEAR, line, new, noise, put, ramp, rect

TEX = 96


class Cube:
    def __init__(self, bone, name, origin, size, material, inflate=0.0, faces=("north", "east", "south", "west", "up", "down"), share=None):
        self.bone, self.name, self.origin, self.size, self.share = bone, name, origin, size, share
        self.material, self.inflate, self.faces = material, inflate, faces
        self.uv = {}


def face_size(cube, face):
    w, h, d = cube.size
    return {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}[face]


def pack(cubes):
    """Shelf-pack faces (tallest first) into the texture with 1px padding. Cubes with `share` reuse another cube's UV."""
    owners = {c.name: c for c in cubes}
    faces = [(c, f) for c in cubes if not c.share for f in c.faces]
    faces.sort(key=lambda cf: (-math.ceil(face_size(cf[0], cf[1])[1]), -math.ceil(face_size(cf[0], cf[1])[0])))
    x, y, shelf = 0, 0, 0
    for cube, face in faces:
        fw, fh = [max(1, math.ceil(v)) for v in face_size(cube, face)]
        if x + fw > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        cube.uv[face] = (x, y, fw, fh)
        x += fw + 1
        shelf = max(shelf, fh)
    assert y + shelf <= TEX, "armor texture overflow (%d)" % (y + shelf)
    for c in cubes:
        if c.share:
            c.uv = dict(owners[c.share].uv)


# ------------------------------------------------------------------------------------------- materials

def shade_v(colors, x, y, w, h, img, base=0.55, spread=0.35, seed=0, grain=0.05):
    for j in range(h):
        for i in range(w):
            t = base + spread * (0.5 - j / max(1, h - 1)) * 0.6 + spread * (0.5 - abs(i - (w - 1) / 2) / max(1, w)) * 0.5
            put(img, x + i, y + j, ramp(colors, t))
    if grain:
        noise(img, x, y, x + w - 1, y + h - 1, grain, seed)


def border(img, x, y, w, h, color):
    line(img, x, y, x + w - 1, y, color)
    line(img, x, y + h - 1, x + w - 1, y + h - 1, color)
    line(img, x, y, x, y + h - 1, color)
    line(img, x + w - 1, y, x + w - 1, y + h - 1, color)


def rivets(img, x, y, w, h):
    if w >= 3 and h >= 3:
        for rx, ry in ((x + 1, y + 1), (x + w - 2, y + 1), (x + 1, y + h - 2), (x + w - 2, y + h - 2)):
            put(img, rx, ry, BRASS[5])
            put(img, rx + 1, ry + 1, BRASS[1]) if rx + 1 < x + w - 1 and ry + 1 < y + h - 1 else None


def paint_leather_cap(img, x, y, w, h, face):
    if face == "north":
        # only the brow band; the face stays visible
        shade_v(LEATHER, x, y, w, 3, img, 0.6, seed=1)
        line(img, x, y + 2, x + w - 1, y + 2, LEATHER[0])
    elif face in ("east", "west"):
        shade_v(LEATHER, x, y, w, h, img, 0.55, seed=2)
        # ear flap with a brass snap
        for j in range(3, h):
            for i in range(0, w):
                if j > 5 and (i < 2 or i > w - 3):
                    put(img, x + i, y + j, CLEAR)
        put(img, x + w // 2, y + 5, BRASS[4])
    elif face == "south":
        shade_v(LEATHER, x, y, w, h - 2, img, 0.5, seed=3)
        line(img, x + w // 2, y, x + w // 2, y + h - 3, LEATHER[0])
    else:
        shade_v(LEATHER, x, y, w, h, img, 0.62, seed=4)
        line(img, x + w // 2, y, x + w // 2, y + h - 1, LEATHER[1])


def paint_hat_crown(img, x, y, w, h, face):
    shade_v(CLOTH, x, y, w, h, img, 0.55, spread=0.5, seed=5, grain=0.04)
    if face in ("north", "south", "east", "west"):
        line(img, x, y, x + w - 1, y, CLOTH[3])
        put(img, x + 1, y + 1, CLOTH[3])


def paint_hat_brim(img, x, y, w, h, face):
    shade_v(CLOTH, x, y, w, h, img, 0.35, spread=0.2, seed=6, grain=0.03)
    if face == "up":
        border(img, x, y, w, h, CLOTH[2])
        border(img, x + 1, y + 1, w - 2, h - 2, CLOTH[0])


def paint_brass_band(img, x, y, w, h, face):
    shade_v(BRASS, x, y, w, h, img, 0.6, spread=0.5, seed=7, grain=0.03)
    line(img, x, y, x + w - 1, y, BRASS[4])
    line(img, x, y + h - 1, x + w - 1, y + h - 1, BRASS[1])
    if face == "north" and w >= 6:
        # buckle
        cx = x + w // 2
        put(img, cx - 1, y, IRON[4])
        put(img, cx, y, IRON[4])
        put(img, cx - 1, y + h - 1, IRON[3])
        put(img, cx, y + h - 1, IRON[3])


def paint_lens(img, x, y, w, h, face):
    if face == "north":
        rect(img, x, y, x + w - 1, y + h - 1, BRASS[3])
        border(img, x, y, w, h, BRASS[1])
        put(img, x, y, BRASS[4])
        if w >= 3 and h >= 3:
            rect(img, x + 1, y + 1, x + w - 2, y + h - 2, CYAN[2])
            put(img, x + 1, y + 1, CYAN[4])
    else:
        shade_v(BRASS, x, y, w, h, img, 0.45, grain=0)


def paint_brass_plate(img, x, y, w, h, face):
    shade_v(BRASS, x, y, w, h, img, 0.55 if face not in ("up",) else 0.75, spread=0.55, seed=x * 7 + y, grain=0.04)
    border(img, x, y, w, h, BRASS[1])
    line(img, x, y, x + w - 1, y, BRASS[4])
    rivets(img, x, y, w, h)


def paint_pauldron(img, x, y, w, h, face):
    shade_v(BRASS, x, y, w, h, img, 0.42 if face != "up" else 0.62, spread=0.45, seed=x * 5 + y, grain=0.05)
    border(img, x, y, w, h, BRASS[0])
    line(img, x, y, x + w - 1, y, BRASS[3])
    rivets(img, x, y, w, h)


def paint_coat(img, x, y, w, h, face):
    shade_v(LEATHER, x, y, w, h, img, 0.62, spread=0.45, seed=x + y * 13, grain=0.07)
    if face == "north":
        mid = x + w // 2
        # lapels (top) and front opening (below the belt line)
        line(img, mid - 1, y, mid - 1, y + 4, LEATHER[0])
        line(img, mid, y, mid, y + 4, LEATHER[0])
        put(img, mid - 2, y + 1, LEATHER[3])
        put(img, mid + 1, y + 1, LEATHER[3])
        line(img, mid - 1, y + 9, mid - 1, y + h - 1, LEATHER[0])
        line(img, mid, y + 9, mid, y + h - 1, OUTLINE)
        # double-breasted brass buttons
        for by in (y + 3, y + 5, y + 7):
            put(img, mid - 3, by, BRASS[4])
            put(img, mid + 2, by, BRASS[4])
            put(img, mid - 3, by + 1, BRASS[1])
            put(img, mid + 2, by + 1, BRASS[1])
        # pocket flaps
        for px in (x + 1, x + w - 3):
            line(img, px, y + 11, px + 1, y + 11, LEATHER[0])
            put(img, px, y + 12, BRASS[3])
        # hem trim
        line(img, x, y + h - 1, x + w - 1, y + h - 1, LEATHER[0])
        line(img, x, y + h - 2, x + w - 1, y + h - 2, BRASS[2])
    elif face == "south":
        mid = x + w // 2
        line(img, mid, y + 2, mid, y + 8, LEATHER[1])
        line(img, mid - 1, y + 10, mid - 1, y + h - 1, OUTLINE)  # coat tails split
        line(img, mid, y + 10, mid, y + h - 1, LEATHER[0])
        line(img, x, y + h - 2, x + w - 1, y + h - 2, BRASS[2])
        line(img, x, y + h - 1, x + w - 1, y + h - 1, LEATHER[0])
    elif face in ("east", "west"):
        line(img, x + w // 2, y + 1, x + w // 2, y + h - 1, LEATHER[1])
        line(img, x, y + h - 2, x + w - 1, y + h - 2, BRASS[2])
        line(img, x, y + h - 1, x + w - 1, y + h - 1, LEATHER[0])


def paint_collar(img, x, y, w, h, face):
    shade_v(LEATHER, x, y, w, h, img, 0.68, spread=0.3, seed=9, grain=0.05)
    line(img, x, y, x + w - 1, y, LEATHER[4])
    if face == "north":
        # open front: cut the middle so the face/neck shows
        for j in range(h):
            for i in range(2, w - 2):
                put(img, x + i, y + j, CLEAR)
    if face in ("up", "down"):
        for j in range(1, h - 1):
            for i in range(1, w - 1):
                put(img, x + i, y + j, CLEAR)


def paint_belt(img, x, y, w, h, face):
    shade_v(LEATHER, x, y, w, h, img, 0.25, spread=0.2, seed=10, grain=0.04)
    line(img, x, y, x + w - 1, y, LEATHER[2])
    if face == "north":
        cx = x + w // 2 - 1
        rect(img, cx - 1, y, cx + 2, y + h - 1, BRASS[3])
        border(img, cx - 1, y, 4, h, BRASS[1])
        put(img, cx, y, BRASS[5])
    if face in ("east", "west"):
        # tool pouch
        rect(img, x + 1, y, x + w - 2, y + h - 1, LEATHER[3])
        put(img, x + w // 2, y, BRASS[4])


def paint_tank(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            t = 0.75 - abs(i - (w - 1) / 2) / max(1, w) * 0.9 if face in ("south", "north") else 0.45
            put(img, x + i, y + j, ramp(COPPER, t))
    noise(img, x, y, x + w - 1, y + h - 1, 0.04, 12)
    if h >= 6:
        for by in (y + 1, y + h - 2, y + h // 2):
            line(img, x, by, x + w - 1, by, BRASS[3])
            put(img, x, by, BRASS[1])
    if face == "south" and w >= 5 and h >= 6:
        # pressure gauge
        cx, cy = x + w // 2, y + h // 2 - 2
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            put(img, cx + dx, cy + dy, BRASS[4])
        put(img, cx, cy, IRON[5])
        put(img, cx + 1, cy - 1, OUTLINE)
    border(img, x, y, w, h, COPPER[0])


def paint_pipe(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            put(img, x + i, y + j, ramp(BRASS, 0.7 - 0.3 * (i / max(1, w - 1))))
    put(img, x, y, BRASS[5])


def paint_sleeve(img, x, y, w, h, face):
    shade_v(LEATHER, x, y, w, h, img, 0.5, spread=0.4, seed=x * 3 + y, grain=0.07)
    if face in ("north", "south", "east", "west"):
        line(img, x, y + 3, x + w - 1, y + 3, LEATHER[1])
        put(img, x + 1, y + 6, LEATHER[3])
    if face == "down":
        rect(img, x, y, x + w - 1, y + h - 1, LEATHER[0])


def paint_cuff(img, x, y, w, h, face):
    paint_brass_plate(img, x, y, w, h, face)
    if face == "north" and w >= 3 and h >= 3:
        # little dial on the gauntlet
        cx, cy = x + w // 2, y + h // 2
        put(img, cx, cy, CYAN[3])
        put(img, cx - 1, cy, IRON[4])
    if face in ("up", "down"):
        for j in range(1, h - 1):
            for i in range(1, w - 1):
                put(img, x + i, y + j, CLEAR)


def paint_trousers(img, x, y, w, h, face):
    shade_v(CLOTH, x, y, w, h, img, 0.55, spread=0.5, seed=x + 5 * y, grain=0.06)
    if face in ("east", "west"):
        line(img, x + w // 2, y, x + w // 2, y + h - 1, CLOTH[3])
    if face == "north":
        put(img, x + 1, y + 1, CLOTH[3])


def paint_waist(img, x, y, w, h, face):
    paint_trousers(img, x, y, w, h, face)
    line(img, x, y, x + w - 1, y, LEATHER[1])
    line(img, x, y + 1, x + w - 1, y + 1, LEATHER[2])
    if face == "north":
        mid = x + w // 2
        put(img, mid - 1, y + 1, BRASS[4])
        put(img, mid, y + 1, BRASS[3])


def paint_boot(img, x, y, w, h, face):
    shade_v(LEATHER, x, y, w, h, img, 0.32, spread=0.35, seed=x + y * 11, grain=0.05)
    line(img, x, y, x + w - 1, y, LEATHER[3])
    if face == "north":
        for ly in range(y + 1, y + h - 2, 2):
            put(img, x + 1, ly, BRASS[3])
            put(img, x + w - 2, ly, BRASS[3])
            line(img, x + 1, ly + 1, x + w - 2, ly + 1, LEATHER[0]) if ly + 1 < y + h - 2 else None


def paint_sole(img, x, y, w, h, face):
    shade_v(IRON, x, y, w, h, img, 0.3, spread=0.2, seed=13, grain=0.03)
    line(img, x, y + h - 1, x + w - 1, y + h - 1, IRON[0])
    if face == "north":
        # brass toe cap
        line(img, x + 1, y, x + w - 2, y, BRASS[3])
        put(img, x + 1, y, BRASS[5])
    if face == "up":
        for j in range(1, h - 1):
            for i in range(1, w - 1):
                put(img, x + i, y + j, CLEAR)


def paint_strap(img, x, y, w, h, face):
    shade_v(LEATHER, x, y, w, h, img, 0.2, spread=0.1, grain=0.02)
    if face in ("east", "west"):
        put(img, x + w // 2, y, BRASS[4])
    if face in ("up", "down"):
        for j in range(1, h - 1):
            for i in range(1, w - 1):
                put(img, x + i, y + j, CLEAR)


def paint_gear_side(img, x, y, w, h, face):
    shade_v(BRASS, x, y, w, h, img, 0.6, spread=0.5, grain=0)
    if face in ("east", "west") and w >= 3 and h >= 3:
        put(img, x, y, CLEAR)
        put(img, x + w - 1, y, CLEAR)
        put(img, x, y + h - 1, CLEAR)
        put(img, x + w - 1, y + h - 1, CLEAR)
        put(img, x + w // 2, y + h // 2, CYAN[3])


# ------------------------------------------------------------------------------------------- model

def cubes():
    head, body, ra, la, rl, ll, rb, lb = "armorHead", "armorBody", "armorRightArm", "armorLeftArm", "armorRightLeg", "armorLeftLeg", "armorRightBoot", "armorLeftBoot"
    return [
        # helmet: leather cap + top hat with goggles on the band
        Cube(head, "cap", [-4, 24, -4], [8, 8, 8], paint_leather_cap, 0.4),
        Cube(head, "brim", [-6, 32.2, -6], [12, 1, 12], paint_hat_brim, 0.0),
        Cube(head, "crown", [-3.5, 33.2, -3.5], [7, 7, 7], paint_hat_crown, 0.0),
        Cube(head, "band", [-3.5, 33.2, -3.5], [7, 2, 7], paint_brass_band, 0.15, ("north", "east", "south", "west")),
        Cube(head, "lens_r", [-3.3, 33.0, -4.6], [3, 3, 1], paint_lens, 0.0),
        Cube(head, "lens_l", [0.3, 33.0, -4.6], [3, 3, 1], paint_lens, 0.0, share="lens_r"),
        Cube("hat_gear", "hat_gear", [3.55, 34.4, -1.5], [0.5, 3, 3], paint_gear_side, 0.0),
        # coat
        Cube(body, "coat", [-4, 6, -2], [8, 18, 4], paint_coat, 1.0),
        Cube(body, "collar", [-4, 22, -2], [8, 3, 4], paint_collar, 1.4),
        Cube(body, "belt", [-4, 11, -2], [8, 2, 4], paint_belt, 1.25),
        Cube(body, "tank", [-2.5, 13, 3.2], [5, 9, 2.5], paint_tank, 0.0),
        Cube(body, "pipe_r", [-2.2, 22, 4.1], [1, 3.5, 1], paint_pipe, 0.0),
        Cube(body, "pipe_l", [1.2, 22, 4.1], [1, 3.5, 1], paint_pipe, 0.0, share="pipe_r"),
        Cube("armorLeggingTorsoLayer", "waist", [-4, 12, -2], [8, 12, 4], paint_waist, 0.4),
        # arms
        Cube(ra, "sleeve_r", [-8, 12, -2], [4, 12, 4], paint_sleeve, 0.9),
        Cube(ra, "pauldron_r", [-8.6, 21.5, -2.5], [5, 2.5, 5], paint_pauldron, 0.6),
        Cube(ra, "cuff_r", [-8, 12, -2], [4, 2.5, 4], paint_cuff, 1.05),
        Cube(la, "sleeve_l", [4, 12, -2], [4, 12, 4], paint_sleeve, 0.9, share="sleeve_r"),
        Cube(la, "pauldron_l", [3.6, 21.5, -2.5], [5, 2.5, 5], paint_pauldron, 0.6, share="pauldron_r"),
        Cube(la, "cuff_l", [4, 12, -2], [4, 2.5, 4], paint_cuff, 1.05, share="cuff_r"),
        # legs
        Cube(rl, "trouser_r", [-4, 0, -2], [4, 12, 4], paint_trousers, 0.3),
        Cube(rl, "knee_r", [-4, 5, -2], [4, 3, 4], paint_brass_plate, 0.55, ("north", "east", "west")),
        Cube(ll, "trouser_l", [0, 0, -2], [4, 12, 4], paint_trousers, 0.3, share="trouser_r"),
        Cube(ll, "knee_l", [0, 5, -2], [4, 3, 4], paint_brass_plate, 0.55, ("north", "east", "west"), share="knee_r"),
        # boots
        Cube(rb, "boot_r", [-4, 0, -2], [4, 7, 4], paint_boot, 0.8),
        Cube(rb, "sole_r", [-4, 0, -2], [4, 2, 4], paint_sole, 1.05),
        Cube(rb, "strap_r", [-4, 5, -2], [4, 1, 4], paint_strap, 0.95),
        Cube(lb, "boot_l", [0, 0, -2], [4, 7, 4], paint_boot, 0.8, share="boot_r"),
        Cube(lb, "sole_l", [0, 0, -2], [4, 2, 4], paint_sole, 1.05, share="sole_r"),
        Cube(lb, "strap_l", [0, 5, -2], [4, 1, 4], paint_strap, 0.95, share="strap_r"),
    ]


BONES = [
    ("bipedHead", None, [0, 24, 0]), ("armorHead", "bipedHead", [0, 24, 0]), ("hat_gear", "armorHead", [3.8, 35.9, 0]),
    ("bipedBody", None, [0, 24, 0]), ("armorBody", "bipedBody", [0, 24, 0]), ("armorLeggingTorsoLayer", "bipedBody", [0, 24, 0]),
    ("bipedRightArm", None, [-5, 22, 0]), ("armorRightArm", "bipedRightArm", [-5, 22, 0]),
    ("bipedLeftArm", None, [5, 22, 0]), ("armorLeftArm", "bipedLeftArm", [5, 22, 0]),
    ("bipedRightLeg", None, [-2, 12, 0]), ("armorRightLeg", "bipedRightLeg", [-2, 12, 0]), ("armorRightBoot", "bipedRightLeg", [-2, 12, 0]),
    ("bipedLeftLeg", None, [2, 12, 0]), ("armorLeftLeg", "bipedLeftLeg", [2, 12, 0]), ("armorLeftBoot", "bipedLeftLeg", [2, 12, 0]),
]


def build():
    cs = cubes()
    pack(cs)
    img = new(TEX)
    for c in cs:
        if c.share:
            continue
        for face, (x, y, w, h) in c.uv.items():
            c.material(img, x, y, w, h, face)
    bones = []
    for name, parent, pivot in BONES:
        b = {"name": name, "pivot": pivot}
        if parent:
            b["parent"] = parent
        own = [c for c in cs if c.bone == name]
        if own:
            b["cubes"] = []
            for c in own:
                entry = {"origin": c.origin, "size": c.size, "uv": {}}
                for face, (x, y, w, h) in c.uv.items():
                    fw, fh = face_size(c, face)
                    if face == "down":
                        entry["uv"][face] = {"uv": [x, y + h], "uv_size": [fw, -fh]}
                    else:
                        entry["uv"][face] = {"uv": [x, y], "uv_size": [fw, fh]}
                if c.inflate:
                    entry["inflate"] = c.inflate
                b["cubes"].append(entry)
        bones.append(b)
    geo = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry.clockwork_engineer_armor", "texture_width": TEX, "texture_height": TEX,
                        "visible_bounds_width": 4, "visible_bounds_height": 5.5, "visible_bounds_offset": [0, 2.25, 0]},
        "bones": bones}]}
    return geo, img, cs


# ------------------------------------------------------------------------------------------- preview

def render_view(cs, img, view, scale=8):
    """Orthographic render of one side ('north' = front, 'south' = back, 'east' = side), painter's algorithm."""
    W, H = 34 * scale, 46 * scale
    out = Image.new("RGBA", (W, H), (40, 40, 46, 255))
    items = []
    for c in cs:
        if view not in c.uv:
            continue
        i = c.inflate
        ox, oy, oz = c.origin
        w, h, d = c.size
        if view == "north":
            depth = oz - i
            x0, x1 = ox - i, ox + w + i
        elif view == "south":
            depth = -(oz + d + i)
            x0, x1 = -(ox + w + i), -(ox - i)
        else:
            depth = -(ox + w + i)
            x0, x1 = oz - i, oz + d + i
        items.append((depth, c, x0, x1, oy - i, oy + h + i))
    items.sort(key=lambda t: -t[0])
    for depth, c, x0, x1, y0, y1 in items:
        u, v, fw, fh = c.uv[view]
        for sy in range(int((46 - y1) * scale), int((46 - y0) * scale)):
            for sx in range(int((x0 + 17) * scale), int((x1 + 17) * scale)):
                fx = (sx / scale - 17 - x0) / (x1 - x0)
                fy = ((46 - sy / scale) - y0) / (y1 - y0)
                tx = u + min(fw - 1, int(fx * face_size(c, view)[0]))
                ty = v + min(fh - 1, int((1 - fy) * face_size(c, view)[1]))
                px = img.getpixel((tx, ty))
                if px[3] > 0 and 0 <= sx < W and 0 <= sy < H:
                    out.putpixel((sx, sy), px)
    return out


def preview(path):
    geo, img, cs = build()
    views = [render_view(cs, img, v) for v in ("north", "south", "east")]
    sheet = Image.new("RGBA", (sum(v.width for v in views) + 96 * 3, views[0].height), (40, 40, 46, 255))
    x = 0
    for v in views:
        sheet.paste(v, (x, 0))
        x += v.width
    sheet.paste(img.resize((288, 288), Image.NEAREST), (x, 0))
    sheet.save(path)
