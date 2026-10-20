"""
Iron's Technomancy 1.9 item icons (16x16), drawn from shapes rather than by hand so they stay consistent:

- Clockwork tier (Create-mod feel: brass, copper, warm wood, andesite, leather, cream parchment, amber/maroon gems);
- Hextech tier (only for what the dragon core unlocks: navy plating, brass trim, cyan crystal glow).

Every shape is filled pixel by pixel with a colour function of the pixel (so it can shade with the light from the
top-left), then the whole icon gets a dark outline on its silhouette like vanilla/Create items.
"""
import math

from PIL import Image

from pixelart import BRASS, CLEAR, COPPER, IRON, LEATHER, OUTLINE, PAPER, rgb

ANDESITE = [rgb("33362F"), rgb("4B4F45"), rgb("666B5E"), rgb("848A79"), rgb("A3A894")]
WOOD = [rgb("2E1A0E"), rgb("472A16"), rgb("643D20"), rgb("84542D"), rgb("A6703E")]
CREAM = [rgb("8C7350"), rgb("B89C70"), rgb("DCC59A"), rgb("F2E4C2"), rgb("FFF8E6")]
MAROON = [rgb("2E0A16"), rgb("521428"), rgb("7C223E"), rgb("A8405C"), rgb("D27A90")]
AMBER = [rgb("6A2C04"), rgb("B05A0C"), rgb("E89020"), rgb("FFC04A"), rgb("FFE9A0")]
NAVY = [rgb("070C20"), rgb("0F1834"), rgb("18264E"), rgb("22366C"), rgb("31498C"), rgb("4566B0")]
HCYAN = [rgb("0A3A70"), rgb("1670C8"), rgb("38B4FF"), rgb("8AE0FF"), rgb("D8F8FF"), rgb("FFFFFF")]
VIOLET = [rgb("1E0A36"), rgb("3A1466"), rgb("5A28A0"), rgb("7E46D6"), rgb("B08AF4"), rgb("E4D6FF")]
SLOT = [rgb("8B8B8B", 0), rgb("FFFFFF", 90)]
LIGHT = (-0.62, -0.78)


def ramp(colors, t):
    t = max(0.0, min(0.999, t))
    return colors[int(t * len(colors))]


class Icon:
    def __init__(self, size=16):
        self.n = size
        self.px = [[None] * size for _ in range(size)]
        self.tag = [[None] * size for _ in range(size)]

    # ---- shape tests on pixel centres
    def fill(self, inside, color, tag=None):
        for y in range(self.n):
            for x in range(self.n):
                cx, cy = x + 0.5, y + 0.5
                if inside(cx, cy):
                    c = color(cx, cy) if callable(color) else color
                    if c is not None:
                        self.px[y][x] = c
                        self.tag[y][x] = tag
        return self

    def put(self, x, y, c):
        if 0 <= x < self.n and 0 <= y < self.n:
            self.px[y][x] = c

    def get(self, x, y):
        return self.px[y][x] if 0 <= x < self.n and 0 <= y < self.n else None

    def image(self, outline=OUTLINE, keep=()):
        """Dark outline on every opaque pixel touching transparency (except tags in keep)."""
        out = [row[:] for row in self.px]
        if outline is not None:
            for y in range(self.n):
                for x in range(self.n):
                    if self.px[y][x] is None or self.tag[y][x] in keep:
                        continue
                    if any(self.get(x + dx, y + dy) is None for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        out[y][x] = outline
        img = Image.new("RGBA", (self.n, self.n), CLEAR)
        for y in range(self.n):
            for x in range(self.n):
                if out[y][x] is not None:
                    img.putpixel((x, y), out[y][x])
        return img


# ---- shapes

def poly(points):
    def inside(x, y):
        c = False
        n = len(points)
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        return c
    return inside


def circle(cx, cy, r):
    return lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def ring(cx, cy, r0, r1):
    return lambda x, y: r0 * r0 <= (x - cx) ** 2 + (y - cy) ** 2 <= r1 * r1


def ellipse(cx, cy, rx, ry, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)

    def inside(x, y):
        dx, dy = x - cx, y - cy
        u, v = dx * c + dy * s, -dx * s + dy * c
        return (u / rx) ** 2 + (v / ry) ** 2 <= 1
    return inside


def ellipse_ring(cx, cy, rx, ry, w, rot=0.0):
    a, b = ellipse(cx, cy, rx + w / 2, ry + w / 2, rot), ellipse(cx, cy, max(0.1, rx - w / 2), max(0.1, ry - w / 2), rot)
    return lambda x, y: a(x, y) and not b(x, y)


def capsule(ax, ay, bx, by, r):
    def inside(x, y):
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
        px, py = ax + dx * t, ay + dy * t
        return (x - px) ** 2 + (y - py) ** 2 <= r * r
    return inside


def gear(cx, cy, r_out, r_root, teeth, hole=0.0, phase=0.0, tooth=0.5):
    def inside(x, y):
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        if d < hole:
            return False
        if d <= r_root:
            return True
        if d > r_out:
            return False
        a = (math.atan2(dy, dx) / (2 * math.pi) * teeth + phase) % 1.0
        return abs(a - 0.5) < tooth / 2
    return inside


def rect(x0, y0, x1, y1):
    return lambda x, y: x0 <= x <= x1 and y0 <= y <= y1


def both(*fs):
    return lambda x, y: all(f(x, y) for f in fs)


def minus(a, b):
    return lambda x, y: a(x, y) and not b(x, y)


# ---- shading

def lit(colors, cx, cy, r, base=0.55, spread=0.45):
    """Sphere-ish shading around (cx, cy): lighter toward the top-left."""
    def col(x, y):
        nx, ny = (x - cx) / max(0.5, r), (y - cy) / max(0.5, r)
        t = base + spread * -(nx * LIGHT[0] + ny * LIGHT[1]) * 0.9
        return ramp(colors, t)
    return col


def vgrad(colors, y0, y1, a=0.85, b=0.25):
    return lambda x, y: ramp(colors, a + (b - a) * (y - y0) / max(0.1, y1 - y0))


def flat(c):
    return lambda x, y: c


# ============================================================================================ clockwork tier

def arcane_cog():
    """Create-style brass cog: eight square teeth, a copper ring and a little amber lens in a dark hub."""
    i = Icon()
    i.fill(gear(8, 8, 7.4, 5.6, 8, hole=0, tooth=0.42), lit(BRASS, 8, 8, 7, 0.55, 0.5))
    i.fill(ring(8, 8, 3.4, 4.6), lit(BRASS, 8, 8, 5, 0.3, 0.35))
    i.fill(circle(8, 8, 3.4), lit(COPPER, 8, 8, 3.4, 0.5, 0.5))
    i.fill(circle(8, 8, 2.0), flat(IRON[1]))
    i.fill(circle(8, 8, 1.2), lit(AMBER, 8, 8, 1.2, 0.7, 0.4))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        i.put(int(8 + math.cos(a) * 4), int(8 + math.sin(a) * 4), BRASS[5])
    i.put(7, 7, AMBER[4])
    return i.image()


def scroll_technomancy():
    """A spell scroll laid diagonally like the other schools' scrolls, but its rollers end in brass cogs and the
    writing is brass circuitry with a little gear seal."""
    i = Icon()
    ang = math.radians(-38)
    c, s = math.cos(ang), math.sin(ang)

    def local(x, y):
        dx, dy = x - 8, y - 8.2
        return dx * c - dy * s, dx * s + dy * c          # u along the scroll, v across

    def paper(x, y):
        u, v = local(x, y)
        return abs(u) <= 4.6 and abs(v) <= 3.6

    def roll(sign):
        return lambda x, y: (lambda u, v: abs(u - sign * 5.3) <= 1.25 and abs(v) <= 4.4)(*local(x, y))

    def paper_col(x, y):
        u, v = local(x, y)
        t = 0.62 + 0.1 * (-v / 3.6) - 0.06 * abs(u) / 4.6
        return ramp(CREAM, t)
    i.fill(paper, paper_col)
    # circuitry text lines
    for row in (-2.0, -0.4, 1.2):
        i.fill(lambda x, y, row=row: (lambda u, v: abs(v - row) <= 0.45 and -3.4 <= u <= 3.0 and (int(u * 1.3 + row * 3) % 3 != 0))(*local(x, y)),
               flat(BRASS[2]))
    i.fill(lambda x, y: (lambda u, v: (u - 2.6) ** 2 + (v - 2.6) ** 2 <= 1.1)(*local(x, y)), flat(MAROON[2]))
    for sign in (-1, 1):
        i.fill(roll(sign), lambda x, y: (lambda u, v: ramp(WOOD, 0.75 - 0.18 * v))(*local(x, y)))
    # cog knobs at the roller ends
    for sign in (-1, 1):
        for end in (-1, 1):
            u, v = sign * 5.3, end * 4.9
            x = 8 + u * c + v * s
            y = 8.2 - u * s + v * c
            i.fill(gear(x, y, 1.6, 1.1, 5, phase=0.1), lit(BRASS, x, y, 1.6, 0.6, 0.5))
    return i.image()


def dragon_core():
    """Tech Dragon Core (image ref: a brass cog ring around a violet chequered crystal)."""
    i = Icon()
    i.fill(gear(8, 8, 7.5, 6.2, 12, tooth=0.45), lit(BRASS, 8, 8, 7.5, 0.55, 0.5))
    i.fill(ring(8, 8, 4.6, 6.2), lit(BRASS, 8, 8, 6, 0.32, 0.3))
    i.fill(circle(8, 8, 4.6), flat(NAVY[0]))
    i.fill(poly([(8, 3.6), (12.2, 8), (8, 12.4), (3.8, 8)]), lambda x, y: ramp(VIOLET, (0.85 if (int(x) + int(y)) % 2 else 0.6) - 0.25 * (y - 4) / 8))
    i.put(7, 5, VIOLET[5])
    i.put(6, 6, VIOLET[4])
    for k in range(4):
        a = k * math.pi / 2
        i.put(int(8 + math.cos(a) * 5.4), int(8 + math.sin(a) * 5.4), BRASS[5])
    return i.image()


def dynamo_core():
    """Overcharged Dynamo Core (the summoning key): a brass-capped coil drum, copper windings, a violet arc window."""
    i = Icon()
    i.fill(rect(3, 3.5, 13, 12.5), lambda x, y: ramp(COPPER, 0.85 - 0.6 * (x - 3) / 10 if int(y) % 2 else 0.45 - 0.3 * (x - 3) / 10))
    i.fill(rect(2, 1.5, 14, 4), vgrad(BRASS, 1.5, 4, 0.95, 0.45))
    i.fill(rect(2, 12, 14, 14.5), vgrad(BRASS, 12, 14.5, 0.7, 0.25))
    i.fill(rect(5.5, 5.5, 10.5, 10.5), flat(NAVY[0]))
    i.fill(circle(8, 8, 2.4), lit(VIOLET, 8, 8, 2.4, 0.7, 0.4))
    for x, y in ((8, 5), (7, 6), (8, 7), (9, 8), (8, 9), (7, 10)):
        i.put(x, y, HCYAN[4])
    for x in (3, 7, 11):
        i.put(x, 2, BRASS[5])
        i.put(x + 1, 13, BRASS[3])
    return i.image()


def clockwork_spellbook():
    """Tier 1 spellbook: walnut leather, brass corners and spine bands, a brass cog with an amber core, cream pages."""
    i = Icon()
    i.fill(rect(3, 1.5, 13.5, 14.5), lambda x, y: ramp(PAPER, 0.75 if int(y) % 2 else 0.55))
    i.fill(rect(2, 1, 12.5, 14.5), lambda x, y: ramp(LEATHER, 0.7 - 0.35 * (y - 1) / 13.5 + (0.15 if x < 3.5 else 0)))
    i.fill(rect(2, 1, 3.6, 14.5), lambda x, y: ramp(LEATHER, 0.25))
    for y0 in (3, 7.5, 12):
        i.fill(rect(2, y0, 3.6, y0 + 0.9), flat(BRASS[3]))
    for (x, y) in ((11.5, 1.6), (11.5, 13.9)):
        i.fill(rect(x - 0.6, y - 0.6, x + 1, y + 0.6), flat(BRASS[4]))
    i.fill(gear(8, 7.8, 3.7, 2.8, 8, tooth=0.45), lit(BRASS, 8, 7.8, 3.7, 0.55, 0.5))
    i.fill(circle(8, 7.8, 1.5), lit(AMBER, 8, 7.8, 1.5, 0.75, 0.4))
    i.fill(rect(9.6, 13.5, 10.6, 15.5), flat(MAROON[3]))
    return i.image()


def clockwork_scepter():
    """Tier 1 staff (ref: Clockwork Apprentice Staff): walnut shaft with brass bands, a brass cog ring around a cream
    and maroon orb, and the big level gear ring circling it."""
    i = Icon()
    i.fill(capsule(2.2, 13.8, 9.2, 6.8, 0.75), lambda x, y: ramp(WOOD, 0.75 if (x - y) > -7.4 else 0.4))
    for t in (0.2, 0.45, 0.7):
        x, y = 2.2 + 7 * t, 13.8 - 7 * t
        i.fill(circle(x, y, 1.1), lit(BRASS, x, y, 1.1, 0.6, 0.4))
    i.fill(gear(2.2, 13.8, 1.7, 1.2, 6), lit(BRASS, 2.2, 13.8, 1.7, 0.5, 0.4))
    i.fill(gear(10.6, 5.4, 4.6, 3.6, 10, hole=2.4, tooth=0.45), lit(BRASS, 10.6, 5.4, 4.6, 0.55, 0.5))
    i.fill(circle(10.6, 5.4, 2.0), lit(MAROON, 10.6, 5.4, 2.0, 0.65, 0.5))
    i.put(10, 4, CREAM[4])
    i.fill(ellipse_ring(10.6, 5.6, 5.4, 1.6, 0.9, math.radians(-18)), lambda x, y: BRASS[4] if y < 5.6 else BRASS[2])
    return i.image()


def armor_clockwork(slot):
    """Clockwork Engineer pieces, Create style: leather, brass, copper, andesite."""
    i = Icon()
    if slot == "helmet":
        i.fill(poly([(3, 12), (3, 6), (5, 3), (11, 3), (13, 6), (13, 12)]), lambda x, y: ramp(LEATHER, 0.75 - 0.4 * (y - 3) / 9))
        i.fill(rect(2.5, 6.6, 13.5, 8.6), flat(BRASS[3]))
        for cx in (5.6, 10.4):
            i.fill(circle(cx, 7.6, 2.1), lit(BRASS, cx, 7.6, 2.1, 0.6, 0.5))
            i.fill(circle(cx, 7.6, 1.2), lit(COPPER, cx, 7.6, 1.2, 0.8, 0.5))
        i.fill(rect(3, 10, 13, 12.5), lambda x, y: ramp(ANDESITE, 0.55))
        i.fill(gear(12.8, 3.6, 1.8, 1.3, 6), lit(BRASS, 12.8, 3.6, 1.8, 0.6, 0.4))
    elif slot == "chestplate":
        i.fill(poly([(1.5, 3), (5, 1.5), (11, 1.5), (14.5, 3), (14.5, 8), (12.5, 8), (12.5, 14.5), (3.5, 14.5), (3.5, 8), (1.5, 8)]),
               lambda x, y: ramp(LEATHER, 0.7 - 0.35 * (y - 1.5) / 13))
        for x0, x1 in ((1.5, 4.5), (11.5, 14.5)):
            i.fill(rect(x0, 2.4, x1, 6), lambda x, y: ramp(ANDESITE, 0.75 - 0.3 * (y - 2.4) / 3.6))
        i.fill(rect(7.2, 2, 8.8, 14.5), flat(LEATHER[1]))
        i.fill(gear(8, 7.4, 3.3, 2.5, 8, tooth=0.45), lit(BRASS, 8, 7.4, 3.3, 0.55, 0.5))
        i.fill(circle(8, 7.4, 1.2), lit(AMBER, 8, 7.4, 1.2, 0.8, 0.4))
        i.fill(rect(3.5, 11, 12.5, 12.2), flat(BRASS[2]))
        i.put(8, 11, BRASS[5])
    elif slot == "leggings":
        i.fill(poly([(3, 2), (13, 2), (13, 14.5), (9.2, 14.5), (8, 7), (6.8, 14.5), (3, 14.5)]), lambda x, y: ramp(LEATHER, 0.55 - 0.3 * (y - 2) / 12))
        i.fill(rect(3, 2, 13, 4), flat(LEATHER[1]))
        i.fill(rect(7, 2, 9, 4), flat(BRASS[4]))
        for x0, x1 in ((3, 6.6), (9.4, 13)):
            i.fill(rect(x0, 8.5, x1, 10.6), lambda x, y: ramp(BRASS, 0.75 - 0.3 * (y - 8.5) / 2))
    else:
        for x0 in (2, 9):
            i.fill(poly([(x0 + 0.5, 4), (x0 + 4.5, 4), (x0 + 4.5, 11), (x0 + 5.5, 11.5), (x0 + 5.5, 14.5), (x0, 14.5), (x0, 11)]),
                   lambda x, y: ramp(LEATHER, 0.65 - 0.35 * (y - 4) / 10))
            i.fill(rect(x0 + 0.5, 4, x0 + 4.5, 5.4), flat(ANDESITE[3]))
            i.fill(rect(x0, 13, x0 + 5.5, 14.5), lambda x, y: ramp(BRASS, 0.6))
            i.fill(gear(x0 + 2.5, 8.6, 1.4, 1.0, 6), lit(BRASS, x0 + 2.5, 8.6, 1.4, 0.6, 0.4))
    return i.image()


# ============================================================================================ hextech tier

def hextech_template():
    """Hextech upgrade template: the vanilla template plate shape in navy steel with a brass frame and a cyan crystal
    held in a brass cog."""
    i = Icon()
    i.fill(poly([(3, 1), (13, 1), (14, 2), (14, 14), (13, 15), (3, 15), (2, 14), (2, 2)]), lambda x, y: ramp(NAVY, 0.55 - 0.35 * (y - 1) / 14))
    i.fill(minus(poly([(3, 1), (13, 1), (14, 2), (14, 14), (13, 15), (3, 15), (2, 14), (2, 2)]), rect(3.2, 2.2, 12.8, 13.8)),
           lambda x, y: BRASS[4] if y < 8 else BRASS[2])
    i.fill(gear(8, 8, 4.4, 3.4, 8, hole=1.9, tooth=0.45), lit(BRASS, 8, 8, 4.4, 0.55, 0.5))
    i.fill(poly([(8, 4.6), (10, 8), (8, 11.4), (6, 8)]), lambda x, y: ramp(HCYAN, 0.9 - 0.45 * (y - 4.6) / 7))
    for x, y in ((4, 3), (12, 3), (4, 13), (12, 13)):
        i.put(x, y, HCYAN[3])
    return i.image()


def hextech_codex():
    """Hextech Codex (tier 2): navy plated cover, brass corners, a brass cog holding a cyan crystal, a glowing rune
    strip down the spine."""
    i = Icon()
    i.fill(rect(3, 1.5, 13.5, 14.5), lambda x, y: ramp(PAPER, 0.75 if int(y) % 2 else 0.55))
    i.fill(rect(2, 1, 12.5, 14.5), lambda x, y: ramp(NAVY, 0.6 - 0.35 * (y - 1) / 13.5))
    i.fill(rect(2, 1, 3.6, 14.5), flat(BRASS[2]))
    i.fill(rect(2.6, 2, 3.0, 13.5), flat(HCYAN[2]))
    for (x0, y0) in ((10.5, 1), (10.5, 13), (4.2, 1), (4.2, 13)):
        i.fill(rect(x0, y0, x0 + 2, y0 + 1.5), flat(BRASS[4]))
    i.fill(gear(8.2, 7.8, 3.9, 3.0, 8, tooth=0.45), lit(BRASS, 8.2, 7.8, 3.9, 0.55, 0.5))
    i.fill(poly([(8.2, 5.2), (9.9, 7.8), (8.2, 10.4), (6.5, 7.8)]), lambda x, y: ramp(HCYAN, 0.92 - 0.45 * (y - 5.2) / 5))
    return i.image()


def hextech_scepter(stars):
    """Hextech scepter: dark navy shaft, brass bands, armillary rings around a cyan crystal; each star adds a ring, a
    brighter crystal and sparks."""
    i = Icon()
    i.fill(capsule(2.2, 13.8, 9.0, 7.0, 0.75), lambda x, y: ramp(NAVY, 0.5 if (x - y) > -7.4 else 0.25))
    for t in (0.25, 0.55):
        x, y = 2.2 + 6.8 * t, 13.8 - 6.8 * t
        i.fill(circle(x, y, 1.1), lit(BRASS, x, y, 1.1, 0.6, 0.4))
    i.fill(poly([(1, 15), (2.4, 12.6), (3.6, 13.8)]), flat(BRASS[3]))
    cx, cy = 10.5, 5.4
    i.fill(ellipse_ring(cx, cy, 4.6, 4.6, 0.95), lambda x, y: BRASS[4] if x + y < cx + cy else BRASS[2])
    i.fill(ellipse_ring(cx, cy + 0.2, 5.0, 1.5, 0.9, math.radians(-20)), lambda x, y: BRASS[4] if y < cy else BRASS[1])
    if stars >= 2:
        i.fill(ellipse_ring(cx, cy, 1.6, 4.8, 0.9, math.radians(25)), lambda x, y: BRASS[3])
    glow = 0.15 * stars
    i.fill(poly([(cx, cy - 3.2), (cx + 1.8, cy), (cx, cy + 3.2), (cx - 1.8, cy)]), lambda x, y: ramp(HCYAN, 0.75 + glow - 0.4 * (y - cy + 3.2) / 6.4))
    i.put(int(cx) - 1, int(cy) - 1, HCYAN[5])
    if stars >= 1:
        for k in range(stars + 1):
            a = k * 2.1 + 0.4
            i.put(int(cx + math.cos(a) * 5.6), int(cy + math.sin(a) * 5.6), HCYAN[4])
    if stars >= 3:
        for x, y in ((15, 1), (5, 2), (15, 9)):
            i.put(x, y, HCYAN[5])
    return i.image()


def armor_hextech(slot):
    """Hextech Engineer pieces: navy plate with brass trim and glowing cyan seams (ref: Clockwork Mage armor)."""
    i = Icon()
    if slot == "helmet":
        i.fill(poly([(3, 13), (3, 6), (5, 2.5), (11, 2.5), (13, 6), (13, 13)]), lambda x, y: ramp(NAVY, 0.7 - 0.4 * (y - 2.5) / 10))
        i.fill(rect(4, 7, 12, 8.6), lambda x, y: ramp(HCYAN, 0.7))
        i.fill(rect(3, 5.2, 13, 6.2), flat(BRASS[3]))
        i.fill(rect(7.4, 2.5, 8.6, 6), flat(BRASS[4]))
        i.fill(gear(3.6, 10.6, 1.8, 1.3, 6), lit(BRASS, 3.6, 10.6, 1.8, 0.6, 0.4))
        i.fill(gear(12.4, 10.6, 1.8, 1.3, 6), lit(BRASS, 12.4, 10.6, 1.8, 0.6, 0.4))
    elif slot == "chestplate":
        body = poly([(1.5, 3), (5, 1.5), (11, 1.5), (14.5, 3), (14.5, 8), (12.5, 8), (12.5, 14.5), (3.5, 14.5), (3.5, 8), (1.5, 8)])
        i.fill(body, lambda x, y: ramp(NAVY, 0.65 - 0.35 * (y - 1.5) / 13))
        for x0, x1 in ((1.5, 4.8), (11.2, 14.5)):
            i.fill(rect(x0, 2.2, x1, 6.2), lambda x, y: ramp(BRASS, 0.8 - 0.4 * (y - 2.2) / 4))
        i.fill(rect(7.5, 9, 8.5, 14.5), flat(HCYAN[2]))
        i.fill(gear(8, 6.8, 3.4, 2.6, 8, tooth=0.45), lit(BRASS, 8, 6.8, 3.4, 0.55, 0.5))
        i.fill(circle(8, 6.8, 1.4), lit(HCYAN, 8, 6.8, 1.4, 0.85, 0.3))
    elif slot == "leggings":
        i.fill(poly([(3, 2), (13, 2), (13, 14.5), (9.2, 14.5), (8, 7), (6.8, 14.5), (3, 14.5)]), lambda x, y: ramp(NAVY, 0.6 - 0.3 * (y - 2) / 12))
        i.fill(rect(3, 2, 13, 4), flat(BRASS[2]))
        i.fill(rect(7, 2, 9, 4), flat(HCYAN[3]))
        for x0, x1 in ((3, 6.6), (9.4, 13)):
            i.fill(rect(x0, 8.4, x1, 10.4), lambda x, y: ramp(BRASS, 0.75 - 0.3 * (y - 8.4) / 2))
            i.fill(rect(x0 + 1.2, 11.2, x0 + 1.9, 14), flat(HCYAN[2]))
    else:
        for x0 in (2, 9):
            i.fill(poly([(x0 + 0.5, 4), (x0 + 4.5, 4), (x0 + 4.5, 11), (x0 + 5.5, 11.5), (x0 + 5.5, 14.5), (x0, 14.5), (x0, 11)]),
                   lambda x, y: ramp(NAVY, 0.65 - 0.35 * (y - 4) / 10))
            i.fill(rect(x0 + 0.5, 4, x0 + 4.5, 5.4), flat(BRASS[3]))
            i.fill(rect(x0, 13, x0 + 5.5, 14.5), lambda x, y: ramp(BRASS, 0.55))
            i.fill(rect(x0 + 1.8, 7, x0 + 2.6, 11), flat(HCYAN[2]))
    return i.image()


# ============================================================================================ empty smithing slots

def _slot(shape):
    i = Icon()
    i.fill(shape, flat(rgb("FFFFFF", 70)))
    return i.image(outline=None)


def empty_slot_dragon_core():
    return _slot(minus(gear(8, 8, 6.8, 5.4, 10), ring(8, 8, 2.8, 3.9)))


def empty_slot_scepter():
    return _slot(lambda x, y: capsule(2.5, 13.5, 9, 7, 0.8)(x, y) or ring(10.5, 5.5, 2.6, 4.2)(x, y))


def empty_slot_book():
    return _slot(minus(rect(3, 1.5, 13, 14.5), rect(5, 3.5, 11, 12.5)))


# ============================================================================================ effect icons (18x18)

def effect_icon(kind):
    i = Icon(18)
    if kind == "focus":
        i.fill(gear(9, 9, 7.4, 5.8, 10, hole=2.6), lit(BRASS, 9, 9, 7.4, 0.55, 0.5))
        i.fill(lambda x, y: (abs(x - 9) < 0.7 and 3.5 < y < 9.5) or (abs(y - 9) < 0.7 and 9 <= x < 13), flat(HCYAN[3]))
    else:
        i.fill(poly([(9, 1.5), (15.5, 9), (9, 16.5), (2.5, 9)]), lambda x, y: ramp(VIOLET, 0.9 - 0.5 * (y - 1.5) / 15))
        i.fill(poly([(10, 4), (7, 9.5), (9.5, 9.5), (8, 14), (11.5, 8), (9, 8)]), flat(HCYAN[4]))
    return i.image()


ICONS = {
    "arcane_cog": arcane_cog, "scroll_technomancy": scroll_technomancy, "tech_dragon_core": dragon_core, "overcharged_dynamo_core": dynamo_core,
    "clockwork_spellbook": clockwork_spellbook, "clockwork_codex": hextech_codex, "clockwork_scepter": clockwork_scepter,
    "hextech_upgrade_smithing_template": hextech_template,
    "hextech_scepter": lambda: hextech_scepter(0), "hextech_scepter_star1": lambda: hextech_scepter(1),
    "hextech_scepter_star2": lambda: hextech_scepter(2), "hextech_scepter_star3": lambda: hextech_scepter(3),
    "empty_slot_dragon_core": empty_slot_dragon_core, "empty_slot_scepter": empty_slot_scepter, "empty_slot_book": empty_slot_book,
}
for _s in ("helmet", "chestplate", "leggings", "boots"):
    ICONS["clockwork_engineer_" + _s] = (lambda s=_s: armor_clockwork(s))
    ICONS["hextech_engineer_" + _s] = (lambda s=_s: armor_hextech(s))


def write_all(out):
    for name, fn in ICONS.items():
        fn().save(out("textures/item/%s.png" % name))
    effect_icon("focus").save(out("textures/mob_effect/evolved_focus.png"))
    effect_icon("power").save(out("textures/mob_effect/evolved_power.png"))


def sheet(path, scale=6):
    names = list(ICONS)
    cols = 8
    rows = (len(names) + cols - 1) // cols
    W = Image.new("RGBA", (cols * 18 * scale, rows * 18 * scale), (139, 139, 139, 255))
    for k, name in enumerate(names):
        img = ICONS[name]().resize((16 * scale, 16 * scale), Image.NEAREST)
        x, y = (k % cols) * 18 * scale + scale, (k // cols) * 18 * scale + scale
        W.alpha_composite(img, (x, y))
    W.save(path)



# ============================================================================================ hand-authored small parts

def stamp(icon, x0, y0, rows, colors):
    """rows: strings; each letter maps to a colour or to a callable (x, y) -> colour; '.' is left alone."""
    for j, row in enumerate(rows):
        for k, ch in enumerate(row):
            if ch == ".":
                continue
            c = colors[ch]
            icon.put(x0 + k, y0 + j, c(x0 + k + 0.5, y0 + j + 0.5) if callable(c) else c)


COG16 = [
    "......oooo......",
    ".....oBBBBo.....",
    "..oo.oBBBBo.oo..",
    ".oBBooBBBBooBBo.",
    ".oBBBBBBBBBBBBo.",
    "..oBBBDDDDBBBo..",
    "ooBBBDccccDBBBoo",
    "oBBBBDcaacDBBBBo",
    "oBBBBDcaacDBBBBo",
    "ooBBBDccccDBBBoo",
    "..oBBBDDDDBBBo..",
    ".oBBBBBBBBBBBBo.",
    ".oBBooBBBBooBBo.",
    "..oo.oBBBBo.oo..",
    ".....oBBBBo.....",
    "......oooo......",
]


def arcane_cog():
    """Create-style brass cog: chunky teeth, a copper hub ring and an amber lens."""
    i = Icon()
    stamp(i, 0, 0, COG16, {"o": OUTLINE, "B": lit(BRASS, 8, 8, 8, 0.48, 0.5), "D": lit(BRASS, 8, 8, 3, 0.25, 0.25),
                           "c": lit(COPPER, 8, 8, 2.5, 0.55, 0.6), "a": lit(AMBER, 8, 8, 1.2, 0.75, 0.5)})
    i.put(7, 7, AMBER[4])
    return i.image(outline=None)


def scroll_technomancy():
    """A spell scroll laid out like the other schools' (a slightly tilted sheet whose top and bottom edges are rolled,
    a knob at each end of the rolls, a few lines of writing in the school colour) - Technomancy's: brass cog knobs and
    brass / copper circuit writing."""
    i = Icon()
    ang = math.radians(18)
    c, s = math.cos(ang), math.sin(ang)

    def local(x, y):
        dx, dy = x - 8, y - 8
        return dx * c + dy * s, -dx * s + dy * c       # u across, v down the sheet

    i.fill(lambda x, y: (lambda u, v: abs(u) <= 4.6 and abs(v) <= 4.3)(*local(x, y)),
           lambda x, y: (lambda u, v: ramp(CREAM, 0.72 - 0.22 * (u + 4.6) / 9.2))(*local(x, y)))
    for k, row in enumerate((-2.2, -0.6, 1.0, 2.6)):
        col = BRASS[1] if k % 2 == 0 else COPPER[1]
        i.fill(lambda x, y, row=row, k=k: (lambda u, v: abs(v - row) <= 0.45 and -3.4 <= u <= (2.8 if k < 3 else 0.8)
                                           and int((u + 4) * 1.4 + k) % 4 != 0)(*local(x, y)), flat(col))
    for end in (-1, 1):
        i.fill(lambda x, y, end=end: (lambda u, v: abs(u) <= 5.0 and abs(v - end * 4.9) <= 0.95)(*local(x, y)),
               lambda x, y, end=end: (lambda u, v: ramp(CREAM, 0.45 - 0.25 * (v - end * 4.9)))(*local(x, y)))
        for side in (-1, 1):
            u, v = side * 5.5, end * 4.9
            x = 8 + u * c - v * s
            y = 8 + u * s + v * c
            i.fill(gear(x, y, 1.55, 1.05, 5, phase=0.25), lit(BRASS, x, y, 1.5, 0.6, 0.5))
    return i.image()


def armor_clockwork_helmet():
    """Leather aviator cap with ear flaps, brass goggles with amber lenses pushed up on the forehead, a little cog."""
    i = Icon()
    i.fill(lambda x, y: ((x - 8) ** 2 + (y - 8.5) ** 2 <= 36 and y <= 9) or rect(2.2, 8.5, 13.8, 11)(x, y) or rect(2.2, 8, 4.6, 14)(x, y)
           or rect(11.4, 8, 13.8, 14)(x, y), lambda x, y: ramp(LEATHER, 0.78 - 0.45 * (y - 2.5) / 11 + (0.08 if x < 8 else 0)))
    i.fill(rect(2, 5.6, 14, 6.8), flat(LEATHER[1]))
    for cx in (5.5, 10.5):
        i.fill(circle(cx, 6.2, 2.3), lit(BRASS, cx, 6.2, 2.3, 0.6, 0.5))
        i.fill(circle(cx, 6.2, 1.35), lit(AMBER, cx, 6.2, 1.35, 0.7, 0.5))
    i.put(5, 5, AMBER[4])
    i.put(10, 5, AMBER[4])
    i.fill(rect(7.4, 5.6, 8.6, 6.8), flat(BRASS[2]))
    i.fill(rect(4.6, 11, 11.4, 12), flat(ANDESITE[2]))
    return i.image()


def clockwork_scepter():
    """Tier 1 staff (ref: Clockwork Apprentice Staff): walnut shaft with brass bands, a brass cog ring around a cream
    and maroon orb, and the big level ring of cogs circling it."""
    i = Icon()
    i.fill(capsule(2.0, 14.0, 8.6, 7.4, 0.95), lambda x, y: ramp(WOOD, 0.8 if (x - y) > -6.9 else 0.45))
    for t in (0.22, 0.5, 0.78):
        x, y = 2.0 + 6.6 * t, 14.0 - 6.6 * t
        i.fill(circle(x, y, 1.15), lit(BRASS, x, y, 1.15, 0.6, 0.45))
    cx, cy = 10.4, 5.6
    i.fill(gear(cx, cy, 5.0, 3.9, 10, hole=2.5, tooth=0.42), lit(BRASS, cx, cy, 5, 0.58, 0.5))
    i.fill(circle(cx, cy, 2.5), lit(MAROON, cx, cy, 2.5, 0.6, 0.55))
    i.put(int(cx) - 1, int(cy) - 1, CREAM[4])
    i.put(int(cx), int(cy) - 1, CREAM[3])
    i.fill(ellipse_ring(cx, cy + 0.6, 6.1, 1.7, 0.95, math.radians(-14)), lambda x, y: BRASS[5] if y < cy + 0.6 else BRASS[2])
    return i.image()


ICONS["arcane_cog"] = arcane_cog
ICONS["scroll_technomancy"] = scroll_technomancy
ICONS["clockwork_scepter"] = clockwork_scepter
ICONS["clockwork_engineer_helmet"] = armor_clockwork_helmet


if __name__ == "__main__":
    import sys
    sheet(sys.argv[1])
