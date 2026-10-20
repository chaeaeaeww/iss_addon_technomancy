"""
Iron's Technomancy 1.10 item icons at 32x32 ("Premium Fantasy"), replacing the 1.9 ones where the user asked:

- arcane_cog: the 1.9 cog kept as it is, now animated - the gold lens in the middle irises open on a blue gem that
  crackles with a few sparks, then closes again (animated strip + mcmeta);
- tech_dragon_core: hextech blue - a brass cog ring and a navy socket holding the same diamond gem the dragon wears
  on its chest (concentric rings, bright heart), arcs crackling over it (animated);
- overcharged_dynamo_core: hextech blue - navy body, brass end caps, glowing cyan coil windings, a window of arcs;
- clockwork_scepter (tier 1) and hextech_scepter (one icon for every Evolution): Iron's Spells staff form - a slim
  diagonal shaft, an ornate head top right;
- armour icons for the two sets after the user's concept sheets: Tier 1 "Steampunk Clockwork Mage" (a dark-brown
  wizard hat with brass cogs and goggles, a long dark coat with cream panels and brass gear buttons, banded trousers,
  buckled boots) and Tier 2 hextech (the same cut in navy and gold with blue crystals).
"""
import math

from PIL import Image

from premium import MAT, Canvas, Mat, capsule, circle, diamond, ellipse, ellipse_ring, gear, hue_ramp, minus, poly, rect, ring, union

B, BD, CU, WAL, LEA, CRM, IRN, NAV = (MAT[k] for k in ("brass", "brass_dark", "copper", "walnut", "leather", "cream", "iron", "navy"))
AMB, WIN, CYA, VIO, STL = MAT["amber_glow"], MAT["wine"], MAT["cyan_glow"], MAT["violet_glow"], MAT["steel_blade"]
COCOA = Mat(hue_ramp("#4A2C1E", 7, 0.03, 0.5, shift=0.04), base=0.5, spread=0.5, gloss=0.1, dither=True)
NAVY2 = Mat(hue_ramp("#1A2550", 8, 0.02, 0.5, shift=0.05), base=0.5, spread=0.5, gloss=0.2, dither=True)
GOLD = Mat(hue_ramp("#E0B040", 8, 0.12, 0.97, shadow_hue=0.05, light_hue=0.15), base=0.6, spread=0.55, gloss=0.4)
BLUEG = Mat(hue_ramp("#2A6CFF", 8, 0.12, 0.98, shadow_hue=0.7, light_hue=0.55, sat_curve=0.0), glow=True, base=0.7, spread=0.45, gloss=0.5)
GLASS = Mat(hue_ramp("#9AD8E8", 6, 0.3, 0.98, shift=0.03), base=0.6, spread=0.5, gloss=0.6)


def zap(c, pts, color):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        c.line(x0, y0, x1, y1, color)


def jag(x0, y0, x1, y1, n, amp, seed):
    pts = [(x0, y0)]
    for k in range(1, n):
        t = k / n
        o = ((seed * 7 + k * 13) % 5 - 2) / 2.0 * amp
        pts.append((x0 + (x1 - x0) * t + o * 0.6, y0 + (y1 - y0) * t - o))
    pts.append((x1, y1))
    return [(int(round(x)), int(round(y))) for x, y in pts]


# ------------------------------------------------------------------------------------------- arcane cog (animated)

def _cog_base():
    """The 1.9 Arcane Cog, unchanged."""
    c = Canvas()
    c.add(gear(16, 16, 15.2, 12.2, 10, tooth=0.42), B, bevel=2.6)
    c.add(ring(16, 16, 8.4, 10.6), BD, bevel=1.2, tone=-0.15)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        c.add(capsule(16 + math.cos(a) * 6, 16 + math.sin(a) * 6, 16 + math.cos(a) * 10, 16 + math.sin(a) * 10, 1.6), B, bevel=1.2)
    c.add(ring(16, 16, 4.8, 7.2), CU, bevel=1.6)
    c.add(circle(16, 16, 4.6), IRN, bevel=1.0, tone=-0.2)
    for k in range(4):
        a = k * math.pi / 2
        c.add(circle(16 + math.cos(a) * 6, 16 + math.sin(a) * 6, 0.8), B, bevel=0.8, tone=0.2)
    return c


def arcane_cog_frame(open_k, sparks=0):
    """open_k 0 = the gold lens closed (the 1.9 look), 1 = irised fully open on the blue gem."""
    c = _cog_base()
    if open_k > 0:
        c.add(circle(16, 16, 3.6), BLUEG, dome=0.9, tone=0.05)
        c.px(15, 14, BLUEG.ramp[-1])
    # the iris: four gold leaves sliding out from the centre
    r_in = 3.4 * open_k
    for k in range(4):
        a0 = k * math.pi / 2
        leaf = minus(lambda x, y, a0=a0: ((math.atan2(y - 16, x - 16) - a0) % (2 * math.pi)) < math.pi / 2 + 0.15 and (x - 16) ** 2 + (y - 16) ** 2 <= 3.1 ** 2,
                     circle(16, 16, r_in))
        c.add(leaf, AMB, bevel=1.0, tone=-0.05 + 0.05 * k)
    img = c.render()
    if sparks:
        cc = Canvas()
        for k in range(sparks):
            a = (k * 2.4 + sparks) % (2 * math.pi)
            x1, y1 = 16 + math.cos(a) * 9.5, 16 + math.sin(a) * 9.5
            pts = jag(16 + math.cos(a) * 3, 16 + math.sin(a) * 3, x1, y1, 3, 1.4, k + sparks)
            zap(cc, pts, CYA.ramp[-1] if k % 2 == 0 else CYA.ramp[-2])
            cc.sparkle(int(x1), int(y1), CYA)
        img.alpha_composite(cc.render(outline=False, shadow=False))
    return img


def arcane_cog_strip():
    """Frames: closed, half, open, open+sparks, open+more sparks, half (the mcmeta holds 'closed' for 3 s)."""
    frames = [arcane_cog_frame(0), arcane_cog_frame(0.5), arcane_cog_frame(1.0), arcane_cog_frame(1.0, 2), arcane_cog_frame(1.0, 3),
              arcane_cog_frame(1.0, 1), arcane_cog_frame(0.5)]
    strip = Image.new("RGBA", (32, 32 * len(frames)), (0, 0, 0, 0))
    for k, im in enumerate(frames):
        strip.paste(im, (0, 32 * k))
    meta = {"animation": {"interpolate": False, "frames": [{"index": 0, "time": 60}, {"index": 1, "time": 2}, {"index": 2, "time": 4},
                                                            {"index": 3, "time": 2}, {"index": 4, "time": 2}, {"index": 5, "time": 2},
                                                            {"index": 4, "time": 2}, {"index": 2, "time": 4}, {"index": 6, "time": 2}]}}
    return strip, meta


# ------------------------------------------------------------------------------------------- cores (hextech blue)

def chest_gem(c, cx, cy, r):
    """The dragon's chest gem: a square turned 45 degrees, concentric bands from a bright heart (like P.core)."""
    for y in range(32):
        for x in range(32):
            d = (abs(x + 0.5 - cx) + abs(y + 0.5 - cy)) / r
            if d <= 1.0:
                t = 1.0 - d * 0.85
                band = int(d * 4) % 2
                col = BLUEG.color(t + (0.06 if band else -0.04))
                c.px(x, y, col, BLUEG)
    c.px(int(cx) - 1, int(cy) - 2, BLUEG.ramp[-1], BLUEG)


def dragon_core_frame(f):
    c = Canvas()
    c.add(gear(16, 16, 15.0, 12.6, 14, hole=9.6, tooth=0.45, phase=0.0), B, bevel=2.0)
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        c.add(circle(16 + math.cos(a) * 11.1, 16 + math.sin(a) * 11.1, 1.0), CYA, flat=True, tone=-0.1 + 0.25 * ((k + f) % 3 == 0))
    c.add(circle(16, 16, 9.8), NAVY2, bevel=1.2, tone=-0.1)
    # the thin bronze frame the gem sits in on the dragon's chest
    c.add(minus(diamond(16, 16, 8.4, 8.4), diamond(16, 16, 7.0, 7.0)), BD, bevel=0.8, tone=0.1)
    chest_gem(c, 16, 16, 6.8)
    img = c.render()
    cc = Canvas()
    rnd = [(0.3, 2), (2.1, 3), (4.0, 1), (5.2, 4)][f % 4]
    for k in range(2):
        a = rnd[0] + k * math.pi
        pts = jag(16 + math.cos(a) * 6, 16 + math.sin(a) * 6, 16 + math.cos(a) * 13.5, 16 + math.sin(a) * 13.5, 3, 1.6, rnd[1] + k)
        zap(cc, pts, CYA.ramp[-1])
    cc.sparkle(4 + f % 3, 4, CYA, big=(f % 2 == 0))
    cc.sparkle(27, 26 - f % 2, BLUEG)
    img.alpha_composite(cc.render(outline=False, shadow=False))
    return img


def dragon_core_strip():
    frames = [dragon_core_frame(f) for f in range(4)]
    strip = Image.new("RGBA", (32, 128), (0, 0, 0, 0))
    for k, im in enumerate(frames):
        strip.paste(im, (0, 32 * k))
    return strip, {"animation": {"frametime": 3}}


def dynamo_core():
    """Overcharged Dynamo Core, hextech: navy body, brass caps, glowing cyan coil windings, a window of arcs."""
    c = Canvas()
    c.add(rect(7, 7, 25, 25), NAVY2, bevel=1.8)
    c.add(ellipse(16, 7, 11.5, 3.4), B, bevel=2)
    c.add(ellipse(16, 25.5, 11.5, 3.4), B, bevel=2, tone=-0.1)
    for y in (10, 13, 19, 22):
        c.add(rect(6.4, y, 25.6, y + 1.2), CYA, flat=True, tone=-0.05 + 0.08 * (y in (13, 19)))
    c.add(rect(11, 13.5, 21, 18.5), IRN, bevel=0.8, tone=-0.3)
    c.add(circle(16, 16, 3.0), BLUEG, dome=0.9)
    img = c.render()
    cc = Canvas()
    zap(cc, [(12, 15), (14, 17), (16, 15), (18, 17), (20, 15)], CYA.ramp[-1])
    cc.sparkle(27, 4, CYA, big=True)
    cc.sparkle(4, 28, CYA)
    img.alpha_composite(cc.render(outline=False, shadow=False))
    return img


# ------------------------------------------------------------------------------------------- staffs (ISS staff form)

def clockwork_scepter():
    """Tier 1 staff, ISS form: a slim walnut shaft from the lower left with brass bands and a leather grip, a gear
    pommel, the head top right: a brass cog crown cradling a wine-red orb, a small cog either side."""
    c = Canvas()
    c.add(capsule(3.0, 29.0, 20.0, 12.0, 1.2), WAL, bevel=1.0)
    c.add(capsule(6.5, 25.5, 9.5, 22.5, 1.5), LEA, bevel=0.8)
    for t in (0.06, 0.4, 0.62, 0.88):
        x, y = 3 + 17 * t, 29 - 17 * t
        c.add(capsule(x - 0.6, y - 0.6, x + 0.6, y + 0.6, 1.5), B, bevel=0.8)
    c.add(gear(3.0, 29.0, 2.6, 1.9, 6), B, bevel=1.0)
    cx, cy = 23.0, 9.0
    c.add(gear(cx, cy, 7.4, 5.8, 10, hole=4.2, tooth=0.45), B, bevel=1.6)
    c.add(circle(cx, cy, 4.2), WIN, dome=0.9)
    c.add(circle(cx - 1.4, cy - 1.5, 1.1), CRM, flat=True, tone=0.35)
    for (x, y) in ((cx - 7.6, cy + 1.6), (cx + 1.8, cy + 7.4)):
        c.add(gear(x, y, 2.2, 1.6, 6), CU, bevel=0.8)
    c.sparkle(29, 2, AMB)
    return c


def hextech_scepter():
    """The Hextech Scepter (one icon for every Evolution), ISS form: a navy shaft with gold bands, a pointed brass
    butt, the head top right: brass armillary rings round a tall cyan crystal crowned with spikes."""
    c = Canvas()
    c.add(capsule(3.5, 28.5, 19.5, 12.5, 1.2), NAV, bevel=1.0)
    for t in (0.15, 0.5, 0.85):
        x, y = 3.5 + 16 * t, 28.5 - 16 * t
        c.add(capsule(x - 0.6, y - 0.6, x + 0.6, y + 0.6, 1.5), GOLD, bevel=0.8)
    c.spike(4.5, 27.5, 1.0, 31.0, GOLD, width=2.2)
    cx, cy = 23.0, 9.0
    c.add(ellipse_ring(cx, cy, 7.0, 7.0, 1.8), GOLD, bevel=1.0, tone=0.05)
    c.add(ellipse_ring(cx, cy + 0.5, 8.8, 2.4, 1.7, math.radians(-16)), GOLD, bevel=0.9, tone=0.15)
    c.add(diamond(cx, cy, 2.8, 6.8), CYA, bevel=2)
    c.add(diamond(cx - 0.8, cy - 1.6, 0.9, 2.2), CYA, flat=True, tone=0.4)
    c.spike(cx, cy - 6.6, cx, cy - 9.2, CYA, width=1.8)
    for a in (-35, 215):
        r = math.radians(a)
        c.spike(cx + math.cos(r) * 7.6, cy + math.sin(r) * 7.6, cx + math.cos(r) * 10.4, cy + math.sin(r) * 10.4, VIO, width=1.6)
    c.sparkle(13, 3, CYA)
    c.sparkle(30, 18, VIO)
    return c


# ------------------------------------------------------------------------------------------- armour (concept sheets)

def armor(slot, tier):
    """tier 1: dark cocoa cloth, cream panels, brass cogs, amber lenses; tier 2: navy, gold trim, blue crystals."""
    cloth, trim, light, glowm = (COCOA, B, CRM, AMB) if tier == 1 else (NAVY2, GOLD, CRM, BLUEG)
    c = Canvas()
    if slot == "helmet":
        # wide-brimmed wizard hat: the brim, a tall crown bent back at the tip, a brass band with a cog and goggles
        c.add(ellipse(16, 22.5, 14.5, 4.4), cloth, bevel=1.6, tone=-0.05)
        c.add(poly([(8, 22), (10.5, 9), (15, 4.5), (22, 2.5), (19, 7), (21, 12), (24, 22)]), cloth, bevel=2.0)
        c.add(poly([(8.4, 20), (23.6, 20), (23.8, 22.6), (8.2, 22.6)]), trim, bevel=0.9)
        c.add(gear(17, 16, 4.0, 3.0, 8, hole=0), trim, bevel=1.0, tone=0.1)
        c.add(circle(17, 16, 1.6), glowm, dome=0.8)
        for x in (10.6, 13.4):
            c.add(circle(x, 18.0, 1.8), trim, bevel=0.6)
            c.add(circle(x, 18.0, 1.1), GLASS if tier == 1 else BLUEG, dome=0.6)
        c.add(circle(22.5, 3.0, 1.2), trim, bevel=0.6, tone=0.2)
        c.sparkle(28, 8, glowm)
    elif slot == "chestplate":
        # the long coat's body: lapels, cream panels down the front, a belt with a gear buckle, cog pauldrons
        c.add(poly([(7, 6), (12, 4), (20, 4), (25, 6), (27, 26), (21, 29), (11, 29), (5, 26)]), cloth, bevel=2.0)
        c.add(poly([(12.4, 4.5), (16, 12), (19.6, 4.5), (21, 6), (17.6, 27), (14.4, 27), (11, 6)]), light, bevel=1.0, tone=0.05)
        c.add(poly([(13.5, 4.5), (16, 10), (18.5, 4.5)]), cloth, bevel=0.6, tone=-0.2)
        c.add(rect(6, 18, 26, 20.6), LEA if tier == 1 else cloth, bevel=0.8, tone=-0.1)
        c.add(gear(16, 19.3, 2.8, 2.0, 8), trim, bevel=0.8, tone=0.1)
        c.add(circle(16, 19.3, 1.0), glowm, dome=0.6)
        for x in (7.0, 25.0):
            c.add(gear(x, 7.0, 4.0, 3.0, 8, hole=1.2), trim, bevel=1.0)
        for y in (9, 13):
            c.add(circle(16, y, 0.9), trim, bevel=0.5, tone=0.2)
        if tier == 2:
            c.add(diamond(16, 25, 1.4, 2.0), BLUEG, flat=True, tone=0.1)
        c.sparkle(29, 3, glowm)
    elif slot == "leggings":
        c.add(poly([(8, 4), (24, 4), (25, 28), (18.5, 28), (16, 12), (13.5, 28), (7, 28)]), cloth, bevel=1.8)
        c.add(rect(7.6, 4, 24.4, 7.4), LEA if tier == 1 else cloth, bevel=0.8, tone=-0.15)
        c.add(gear(16, 5.7, 2.2, 1.6, 6), trim, bevel=0.7)
        for x0 in (8.4, 19.0):
            c.add(rect(x0, 15, x0 + 4.6, 17), trim, bevel=0.6)
            c.add(rect(x0 + 0.4, 21, x0 + 4.4, 22.6), light, flat=True, tone=0.05)
        c.add(rect(9.4, 9, 11.4, 12), light, flat=True, tone=-0.05)
        c.add(rect(20.4, 9, 22.4, 12), light, flat=True, tone=-0.05)
    else:
        for (x0, flip) in ((3.5, 0), (17.5, 1)):
            c.add(poly([(x0 + 1, 6), (x0 + 9, 6), (x0 + 9.5, 20), (x0 + 12.5, 23), (x0 + 12.5, 27), (x0, 27), (x0 + 0.5, 20)]), cloth, bevel=1.6)
            c.add(rect(x0 + 0.6, 6, x0 + 9.4, 8.6), light, bevel=0.6, tone=0.05)
            c.add(rect(x0 + 0.4, 14, x0 + 9.6, 16), trim, bevel=0.6)
            c.add(rect(x0 + 3.6, 13.6, x0 + 6.4, 16.4), trim, bevel=0.6, tone=0.2)
            c.add(rect(x0 - 0.2, 25.6, x0 + 12.8, 27.4), trim, bevel=0.6, tone=-0.1)
        if tier == 2:
            c.add(diamond(8.5, 15, 1.0, 1.0), BLUEG, flat=True)
            c.add(diamond(22.5, 15, 1.0, 1.0), BLUEG, flat=True)
    return c


SLOTS = ("helmet", "chestplate", "leggings", "boots")


def write_all(out, write_json):
    strip, meta = arcane_cog_strip()
    strip.save(out("textures/item/arcane_cog.png"))
    write_json("textures/item/arcane_cog.png.mcmeta", meta)
    strip, meta = dragon_core_strip()
    strip.save(out("textures/item/tech_dragon_core.png"))
    write_json("textures/item/tech_dragon_core.png.mcmeta", meta)
    dynamo_core().save(out("textures/item/overcharged_dynamo_core.png"))
    clockwork_scepter().render().save(out("textures/item/clockwork_scepter.png"))
    hextech_scepter().render().save(out("textures/item/hextech_scepter.png"))
    for slot in SLOTS:
        armor(slot, 1).render().save(out("textures/item/clockwork_engineer_%s.png" % slot))
        armor(slot, 2).render().save(out("textures/item/hextech_engineer_%s.png" % slot))


def sheet(path, scale=4):
    ims = [arcane_cog_frame(0), arcane_cog_frame(1.0, 3), dragon_core_frame(0), dragon_core_frame(1), dynamo_core(), clockwork_scepter().render(),
           hextech_scepter().render()] + [armor(s, 1).render() for s in SLOTS] + [armor(s, 2).render() for s in SLOTS]
    cols = 8
    W = Image.new("RGBA", (cols * 36 * scale, ((len(ims) + cols - 1) // cols) * 36 * scale), (139, 139, 139, 255))
    for k, im in enumerate(ims):
        W.alpha_composite(im.resize((32 * scale, 32 * scale), Image.NEAREST), ((k % cols) * 36 * scale + 2 * scale, (k // cols) * 36 * scale + 2 * scale))
    W.save(path)
