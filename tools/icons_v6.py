"""
Iron's Technomancy 1.9 item icons, 32x32, "Premium Fantasy" preset (premium.py, ART_STYLE_PREMIUM_FANTASY.md).
Clockwork tier glows warm amber; Hextech tier glows cyan/violet.
"""
import math

from PIL import Image

from premium import (MAT, Canvas, capsule, circle, diamond, ellipse, ellipse_ring, gear, minus, poly, rect, ring, union)

B, BD, CU, WAL, LEA, CRM, AND, IRN, NAV = (MAT[k] for k in ("brass", "brass_dark", "copper", "walnut", "leather", "cream", "andesite", "iron", "navy"))
AMB, WIN, CYA, VIO = MAT["amber_glow"], MAT["wine"], MAT["cyan_glow"], MAT["violet_glow"]


def rot(cx, cy, ang):
    c, s = math.cos(ang), math.sin(ang)
    return lambda u, v: (cx + u * c - v * s, cy + u * s + v * c)


def local(cx, cy, ang):
    c, s = math.cos(ang), math.sin(ang)

    def f(x, y):
        dx, dy = x - cx, y - cy
        return dx * c + dy * s, -dx * s + dy * c
    return f


# ============================================================================================ clockwork

def scroll():
    """Like the other schools' scrolls (tilted sheet, rolled top and bottom, knobs at the roll ends, school-coloured
    writing) - Technomancy: brass cog knobs, brass circuit writing with copper nodes, an amber cog seal."""
    c = Canvas()
    ang = math.radians(16)
    L = local(16, 16, ang)
    P = rot(16, 16, ang)
    c.add(lambda x, y: (lambda u, v: abs(u) <= 9.2 and abs(v) <= 9.6)(*L(x, y)), CRM, bevel=2.5)
    for k, row in enumerate((-5.6, -2.4, 0.8, 4.0)):
        x0, x1 = -6.8, (6.4 if k < 3 else 1.6)
        a, b = P(x0, row), P(x1, row)
        c.add(capsule(a[0], a[1], b[0], b[1], 0.75), BD, flat=True, tone=-0.3)
        for j in range(3):
            nx, ny = P(x0 + 1.5 + j * 4.2 + (k % 2) * 1.6, row)
            c.add(circle(nx, ny, 0.9), CU, bevel=0.8)
    sx, sy = P(4.8, 4.6)
    c.add(gear(sx, sy, 3.0, 2.2, 6), B, bevel=1.2)
    c.add(circle(sx, sy, 1.3), AMB, bevel=1.0)
    for end in (-1, 1):
        a, b = P(-10.2, end * 10.6), P(10.2, end * 10.6)
        c.add(capsule(a[0], a[1], b[0], b[1], 2.0), CRM, bevel=2.0, tone=-0.12)
        for side in (-1, 1):
            kx, ky = P(side * 11.6, end * 10.6)
            c.add(gear(kx, ky, 3.1, 2.1, 6, phase=0.2), B, bevel=1.4)
            c.add(circle(kx, ky, 0.9), BD, flat=True, tone=-0.2)
    c.sparkle(*P(-7.5, 7.2), AMB)
    return c


def arcane_cog():
    """A Create-style brass cogwheel: chunky teeth, recessed spokes, a copper ring and an amber lens with rivets."""
    c = Canvas()
    c.add(gear(16, 16, 15.2, 12.2, 10, tooth=0.42), B, bevel=2.6)
    c.add(ring(16, 16, 8.4, 10.6), BD, bevel=1.2, tone=-0.15)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        x0, y0 = 16 + math.cos(a) * 6, 16 + math.sin(a) * 6
        x1, y1 = 16 + math.cos(a) * 10, 16 + math.sin(a) * 10
        c.add(capsule(x0, y0, x1, y1, 1.6), B, bevel=1.2)
    c.add(ring(16, 16, 4.8, 7.2), CU, bevel=1.6)
    c.add(circle(16, 16, 4.6), IRN, bevel=1.0, tone=-0.2)
    c.add(circle(16, 16, 3.0), AMB, dome=0.8, bevel=2)
    for k in range(4):
        a = k * math.pi / 2
        c.add(circle(16 + math.cos(a) * 6, 16 + math.sin(a) * 6, 0.8), B, bevel=0.8, tone=0.2)
    c.sparkle(26, 6, AMB)
    return c


def clockwork_spellbook():
    """Tier 1 book (ref: Clockwork Spell Book): cream cover in a walnut frame, brass corner fittings and clasp, a brass
    cog around an amber core, page edges and a bookmark."""
    c = Canvas()
    c.add(rect(6, 3, 28.5, 29), CRM, bevel=1.2, tone=0.05)
    for y in range(5, 28, 2):
        c.line(27, y, 28, y, CRM.ramp[2])
    c.add(rect(3, 2, 26, 29.5), WAL, bevel=1.6)
    c.add(rect(5.5, 4.5, 23.5, 27), CRM, bevel=1.2)
    c.add(rect(3, 2, 6.2, 29.5), WAL, bevel=1.4, tone=-0.1)
    for y0 in (6, 14.5, 23):
        c.add(rect(3, y0, 6.2, y0 + 1.6), B, bevel=0.8)
    for (x, y) in ((22.5, 2), (22.5, 26.5), (6.5, 2), (6.5, 26.5)):
        c.add(poly([(x, y), (x + 3.5, y), (x + 3.5, y + 3), (x, y + 3)]), B, bevel=1)
    c.add(gear(14.5, 15.5, 7.2, 5.6, 10, hole=3.4, tooth=0.42), B, bevel=1.8)
    c.add(circle(14.5, 15.5, 3.4), AMB, dome=0.8)
    c.add(rect(25.5, 13, 29.5, 18), B, bevel=1)
    c.add(poly([(17.5, 28.5), (20.5, 28.5), (20.5, 31.5), (19, 30.2), (17.5, 31.5)]), WIN, bevel=0.8)
    c.sparkle(29, 4, AMB)
    return c


def clockwork_scepter():
    """Tier 1 staff: walnut shaft with brass bands, a gear pommel with a wine gem, a brass cog ring around a wine and
    cream orb and the big level ring of cogs."""
    c = Canvas()
    c.add(capsule(4.5, 27.5, 18.5, 13.5, 1.6), WAL, bevel=1.4)
    for t in (0.16, 0.42, 0.68, 0.92):
        x, y = 4.5 + 14 * t, 27.5 - 14 * t
        c.add(capsule(x - 0.9, y - 0.9, x + 0.9, y + 0.9, 1.75), B, bevel=0.9)
    c.add(gear(4.0, 28.0, 3.6, 2.6, 7), B, bevel=1.3)
    c.add(circle(4.0, 28.0, 1.4), WIN, dome=0.6)
    cx, cy = 21.5, 10.5
    c.add(gear(cx, cy, 9.0, 7.4, 12, hole=5.2, tooth=0.42), B, bevel=1.8)
    c.add(circle(cx, cy, 5.0), WIN, dome=0.9)
    c.add(circle(cx - 1.6, cy - 1.8, 1.3), CRM, flat=True, tone=0.35)
    c.add(ellipse_ring(cx, cy + 1.0, 11.2, 3.0, 2.2, math.radians(-14)), B, bevel=1.0, tone=0.15)
    for u in (-10.6, 10.6):
        px, py = cx + u * math.cos(math.radians(-14)), cy + 1.0 + u * math.sin(math.radians(-14))
        c.add(gear(px, py, 2.4, 1.7, 6), CU, bevel=1)
    return c


def armor_clockwork(slot):
    c = Canvas()
    if slot == "helmet":
        # leather aviator cap: a round crown, ear flaps, brass goggles with amber lenses pushed up on the forehead
        crown = ellipse(16, 15, 12.5, 11.5)
        cap = union(lambda x, y: crown(x, y) and y <= 20, rect(3.6, 15, 9.5, 27.5), rect(22.5, 15, 28.4, 27.5))
        c.add(cap, LEA, bevel=3.0, dome=0.45)
        c.add(minus(ellipse(16, 21, 7.5, 5), rect(0, 0, 32, 17)), LEA, bevel=1, tone=-0.45)
        c.add(rect(3.2, 25, 9.8, 27.8), AND, bevel=0.9)
        c.add(rect(22.2, 25, 28.8, 27.8), AND, bevel=0.9)
        c.add(lambda x, y: abs(y - (11.5 + 0.02 * (x - 16) ** 2)) <= 1.3 and 3.5 <= x <= 28.5, LEA, flat=True, tone=-0.3)
        for cx in (10.5, 21.5):
            c.add(circle(cx, 12.5, 4.6), B, bevel=1.6)
            c.add(circle(cx, 12.5, 2.8), AMB, dome=0.9)
            c.add(circle(cx - 1.0, 11.5, 0.8), AMB, flat=True, tone=0.4)
        c.add(rect(14.6, 11.5, 17.4, 13.5), B, bevel=0.8)
        c.add(gear(24.5, 5.5, 3.2, 2.3, 7), CU, bevel=1.2)
    elif slot == "chestplate":
        body = poly([(3, 6), (10, 3), (22, 3), (29, 6), (29, 16), (25, 16), (25, 29), (7, 29), (7, 16), (3, 16)])
        c.add(body, LEA, bevel=2.5)
        c.add(rect(14.6, 4, 17.4, 29), LEA, bevel=1, tone=-0.25)
        for x0, x1 in ((2.5, 9.5), (22.5, 29.5)):
            c.add(rect(x0, 4.5, x1, 12), AND, bevel=1.8)
            c.add(circle((x0 + x1) / 2, 8.3, 1.0), B, bevel=0.8)
        c.add(gear(16, 14.5, 6.6, 5.0, 10, tooth=0.42), B, bevel=1.8)
        c.add(circle(16, 14.5, 2.6), AMB, dome=0.9)
        c.add(rect(7, 22, 25, 24.4), B, bevel=0.9, tone=-0.1)
        c.add(rect(14.5, 21.5, 17.5, 25), CU, bevel=0.8)
    elif slot == "leggings":
        legs = poly([(6, 4), (26, 4), (26, 29), (18.5, 29), (16, 14), (13.5, 29), (6, 29)])
        c.add(legs, LEA, bevel=2.2, tone=-0.08)
        c.add(rect(6, 4, 26, 8), LEA, bevel=1, tone=-0.25)
        c.add(rect(13.5, 3.5, 18.5, 8.5), B, bevel=1)
        for x0, x1 in ((6, 13.5), (18.5, 26)):
            c.add(rect(x0, 16.5, x1, 21), B, bevel=1.4)
            c.add(circle((x0 + x1) / 2, 18.8, 1.0), CU, bevel=0.8)
    else:
        for x0 in (3.5, 18):
            boot = poly([(x0 + 1, 8), (x0 + 9, 8), (x0 + 9, 22), (x0 + 11, 23), (x0 + 11, 29), (x0, 29), (x0, 22)])
            c.add(boot, LEA, bevel=2)
            c.add(rect(x0 + 1, 8, x0 + 9, 10.5), AND, bevel=1)
            c.add(rect(x0, 26, x0 + 11, 29), B, bevel=1.2)
            c.add(gear(x0 + 5, 17, 2.8, 2.0, 7), B, bevel=1.1)
            c.add(circle(x0 + 5, 17, 1.0), AMB, dome=0.5)
    return c


# ============================================================================================ hextech

def dragon_core():
    """Tech Dragon Core (ref: Dragon Core): a brass cog ring around a navy socket holding a violet chequered crystal,
    shards and energy wisps."""
    c = Canvas()
    c.add(gear(16, 16, 15.0, 12.6, 14, hole=9.6, tooth=0.45), B, bevel=2.0)
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        c.add(circle(16 + math.cos(a) * 11.1, 16 + math.sin(a) * 11.1, 1.0), BD, flat=True, tone=-0.1)
    c.add(circle(16, 16, 9.8), NAV, bevel=1.2, tone=-0.15)
    m = diamond(16, 16, 7.2, 8.6)
    c.add(m, VIO, bevel=3.0)
    for y in range(32):
        for x in range(32):
            if m(x + 0.5, y + 0.5) and (x // 2 + y // 2) % 2 == 0:
                c.px(x, y, VIO.ramp[5] if y < 14 else VIO.ramp[3])
    c.add(diamond(14.2, 12.5, 2.0, 2.6), VIO, flat=True, tone=0.4)
    c.sparkle(4, 4, VIO, big=True)
    c.sparkle(28, 27, VIO)
    return c


def dynamo_core():
    """Overcharged Dynamo Core (summoning key): brass end caps, copper coil windings and a window of violet arcs."""
    c = Canvas()
    c.add(rect(6, 7, 26, 25), CU, bevel=1.8)
    for y in range(8, 25, 2):
        c.line(6, y, 26, y, CU.ramp[1])
    c.add(ellipse(16, 7, 12, 3.6), B, bevel=2)
    c.add(ellipse(16, 25.5, 12, 3.6), B, bevel=2, tone=-0.1)
    c.add(rect(11, 11, 21, 21), NAV, bevel=1, tone=-0.2)
    c.add(circle(16, 16, 4.2), VIO, dome=0.9)
    for a, b in (((13, 12), (16, 16)), ((16, 16), (14, 19)), ((16, 16), (19.5, 13))):
        c.line(a[0], a[1], b[0], b[1], CYA.ramp[5], CYA)
    c.sparkle(27, 4, VIO)
    c.sparkle(4, 27, CYA)
    return c


def hextech_template():
    """Hextech upgrade template: the vanilla template plate in navy steel with a brass frame, cyan runes and a brass
    cog holding a cyan crystal."""
    c = Canvas()
    plate = poly([(6, 2), (26, 2), (29, 5), (29, 27), (26, 30), (6, 30), (3, 27), (3, 5)])
    c.add(plate, NAV, bevel=1.5)
    c.add(minus(plate, poly([(7, 5), (25, 5), (26, 6), (26, 26), (25, 27), (7, 27), (6, 26), (6, 6)])), B, bevel=1.4)
    c.add(gear(16, 16, 8.6, 6.8, 10, hole=3.6, tooth=0.42), B, bevel=1.8)
    c.add(diamond(16, 16, 3.6, 6.4), CYA, bevel=2)
    for (x, y, g) in ((8, 7, "a"), (22, 7, "c"), (8, 23, "f"), (22, 23, "d")):
        c.rune(x, y, g, CYA.ramp[4])
    c.sparkle(28, 3, CYA)
    return c


def hextech_codex():
    """Hextech Codex (ref: Clockwork Grimoire): navy cover in brass, corner fittings, a brass cog with a blue crystal,
    a glowing rune strip on the spine and a cyan bookmark."""
    c = Canvas()
    c.add(rect(6, 3, 28.5, 29), CRM, bevel=1.2)
    for y in range(5, 28, 2):
        c.line(27, y, 28, y, CRM.ramp[2])
    c.add(rect(3, 2, 26, 29.5), NAV, bevel=1.6)
    c.add(minus(rect(5, 4, 24, 27.5), rect(6.5, 5.5, 22.5, 26)), B, bevel=0.8)
    c.add(rect(3, 2, 6.2, 29.5), NAV, bevel=1.2, tone=-0.1)
    c.add(rect(4.2, 4, 5.0, 27.5), CYA, flat=True)
    for (x, y) in ((22.5, 2), (22.5, 26.5), (6.5, 2), (6.5, 26.5)):
        c.add(poly([(x, y), (x + 3.5, y), (x + 3.5, y + 3), (x, y + 3)]), B, bevel=1)
    c.add(gear(15, 15.5, 7.4, 5.8, 10, hole=3.4, tooth=0.42), B, bevel=1.8)
    c.add(diamond(15, 15.5, 3.2, 4.6), CYA, bevel=2)
    for (x, y, g) in ((8, 6, "b"), (19, 6, "e"), (8, 23, "c"), (19, 23, "a")):
        c.rune(x, y, g, CYA.ramp[4])
    c.add(poly([(17.5, 28.5), (20.5, 28.5), (20.5, 31.5), (19, 30.2), (17.5, 31.5)]), CYA, bevel=0.8)
    c.sparkle(29, 4, CYA, big=True)
    return c


def hextech_scepter(stars):
    """Hextech scepter: navy shaft, brass fittings, armillary rings around a tall cyan crystal with violet energy;
    every star adds crystal spikes, rings and particles."""
    c = Canvas()
    c.add(capsule(4.5, 27.5, 18, 14, 1.5), NAV, bevel=1.4)
    for t in (0.2, 0.5, 0.82):
        x, y = 4.5 + 13.5 * t, 27.5 - 13.5 * t
        c.add(capsule(x - 0.9, y - 0.9, x + 0.9, y + 0.9, 1.75), B, bevel=0.9)
    c.spike(5.5, 26.5, 1.5, 30.5, B, width=2.4)
    cx, cy = 21.5, 10.5
    c.add(ellipse_ring(cx, cy, 8.2, 8.2, 2.4), B, bevel=1.1, tone=0.1)
    c.add(ellipse_ring(cx, cy + 0.6, 10.4, 2.8, 2.2, math.radians(-16)), B, bevel=1.0, tone=0.15)
    if stars >= 2:
        c.add(ellipse_ring(cx, cy, 3.0, 8.4, 1.9, math.radians(28)), B, bevel=0.9, tone=-0.05)
    h = 6.4 + 0.5 * stars
    c.add(diamond(cx, cy, 2.8 + 0.2 * stars, h), CYA, bevel=2)
    c.add(diamond(cx - 0.8, cy - 1.6, 0.9, 2.2), CYA, flat=True, tone=0.4)
    if stars >= 1:
        for k in range(stars * 2):
            a = math.radians(-60 + k * 360 / (stars * 2))
            c.spike(cx + math.cos(a) * 9.6, cy + math.sin(a) * 9.6, cx + math.cos(a) * 13.2, cy + math.sin(a) * 13.2, VIO, width=1.8)
    if stars >= 3:
        c.spike(cx, cy - h, cx, cy - h - 4.5, CYA, width=2.0)
    spots = [(29, 2), (13, 3), (30, 18), (11, 16)]
    for k in range(min(len(spots), stars + 1)):
        c.sparkle(*spots[k], CYA if k % 2 == 0 else VIO, big=(k == 0 and stars >= 2))
    return c


def armor_hextech(slot):
    c = Canvas()
    if slot == "helmet":
        # hextech helm: a rounded navy dome with a brass crest cog, a glowing T visor, brass cheek guards, side spikes
        dome = ellipse(16, 15.5, 11.5, 12.5)
        helm = union(lambda x, y: dome(x, y) and y <= 21, rect(5, 18, 27, 28.5))
        c.add(helm, NAV, bevel=2.8, dome=0.4)
        c.add(minus(rect(9, 22, 23, 29), rect(0, 0, 32, 22.5)), NAV, bevel=1, tone=-0.4)
        c.add(rect(4.6, 9.6, 27.4, 11.6), B, bevel=0.9)
        c.add(poly([(8, 14), (24, 14), (24, 17), (17.6, 17), (17.6, 24), (14.4, 24), (14.4, 17), (8, 17)]), CYA, bevel=1.2)
        for x0, x1 in ((4.6, 9.5), (22.5, 27.4)):
            c.add(rect(x0, 19, x1, 28.6), B, bevel=1.4)
        c.add(gear(16, 4.6, 4.0, 2.9, 8), B, bevel=1.4)
        c.add(circle(16, 4.6, 1.4), CYA, dome=0.6)
        c.spike(5.5, 12, 1.5, 5, B, width=2.2)
        c.spike(26.5, 12, 30.5, 5, B, width=2.2)
        c.sparkle(29, 27, CYA)
    elif slot == "chestplate":
        body = poly([(3, 6), (10, 3), (22, 3), (29, 6), (29, 16), (25, 16), (25, 29), (7, 29), (7, 16), (3, 16)])
        c.add(body, NAV, bevel=2.5)
        for x0, x1 in ((2, 10), (22, 30)):
            c.add(rect(x0, 3.5, x1, 11.5), B, bevel=2)
            c.add(gear((x0 + x1) / 2, 7.5, 2.6, 1.9, 7), BD, bevel=1)
        c.add(rect(15, 20, 17, 29), CYA, flat=True)
        c.add(gear(16, 14.5, 7.0, 5.4, 10, tooth=0.42), B, bevel=1.8)
        c.add(circle(16, 14.5, 3.0), CYA, dome=0.9)
        for (x, y, g) in ((9, 20, "c"), (20, 20, "f")):
            c.rune(x, y, g, CYA.ramp[4])
        c.sparkle(29, 27, CYA)
    elif slot == "leggings":
        legs = poly([(6, 4), (26, 4), (26, 29), (18.5, 29), (16, 14), (13.5, 29), (6, 29)])
        c.add(legs, NAV, bevel=2.2)
        c.add(rect(6, 4, 26, 8), B, bevel=1)
        c.add(rect(14, 4.5, 18, 7.5), CYA, flat=True)
        for x0, x1 in ((6, 13.5), (18.5, 26)):
            c.add(poly([(x0, 16), (x1, 16), (x1, 20), ((x0 + x1) / 2, 22.5), (x0, 20)]), B, bevel=1.4)
            c.add(rect((x0 + x1) / 2 - 0.6, 23, (x0 + x1) / 2 + 0.6, 28), CYA, flat=True)
    else:
        for x0 in (3.5, 18):
            boot = poly([(x0 + 1, 8), (x0 + 9, 8), (x0 + 9, 22), (x0 + 11, 23), (x0 + 11, 29), (x0, 29), (x0, 22)])
            c.add(boot, NAV, bevel=2)
            c.add(rect(x0 + 0.5, 7.5, x0 + 9.5, 10.5), B, bevel=1)
            c.add(rect(x0, 25.5, x0 + 11, 29), B, bevel=1.2)
            c.add(rect(x0 + 4.4, 12, x0 + 5.6, 24), CYA, flat=True)
            c.spike(x0 + 9, 9, x0 + 12, 5, B, width=1.8)
    return c


ICONS = {
    "scroll_technomancy": scroll, "arcane_cog": arcane_cog, "clockwork_spellbook": clockwork_spellbook, "clockwork_scepter": clockwork_scepter,
    "tech_dragon_core": dragon_core, "overcharged_dynamo_core": dynamo_core, "hextech_upgrade_smithing_template": hextech_template,
    "clockwork_codex": hextech_codex,
    "hextech_scepter": lambda: hextech_scepter(0), "hextech_scepter_star1": lambda: hextech_scepter(1),
    "hextech_scepter_star2": lambda: hextech_scepter(2), "hextech_scepter_star3": lambda: hextech_scepter(3),
}
for _s in ("helmet", "chestplate", "leggings", "boots"):
    ICONS["clockwork_engineer_" + _s] = (lambda s=_s: armor_clockwork(s))
    ICONS["hextech_engineer_" + _s] = (lambda s=_s: armor_hextech(s))


def sheet(path, names=None, scale=4):
    names = names or list(ICONS)
    cols = 8
    rows = (len(names) + cols - 1) // cols
    W = Image.new("RGBA", (cols * 36 * scale, rows * 36 * scale), (139, 139, 139, 255))
    for k, name in enumerate(names):
        img = ICONS[name]().render().resize((32 * scale, 32 * scale), Image.NEAREST)
        W.alpha_composite(img, ((k % cols) * 36 * scale + 2 * scale, (k // cols) * 36 * scale + 2 * scale))
    W.save(path)


def write_all(out):
    for name, fn in ICONS.items():
        fn().render().save(out("textures/item/%s.png" % name))


if __name__ == "__main__":
    import sys
    sheet(sys.argv[1])
