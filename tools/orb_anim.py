"""
Technomancy Upgrade Orb, animated (32x32 frames, a strip + mcmeta with per-frame times).

The body is Iron's Spells' own empty upgrade orb, studied pixel by pixel (the user put its 16x16 texture in
Techno/assets/description; copy in tools/art_src): an octagonal dark stone, a 1-px near-black outline, lavender-grey
highlights on the top-left rim, teal-grey on the right, a black pit in the middle and reddish cracks at the top and
bottom. It is redrawn at 2x (every source pixel is a 2x2 block) so the stone's look is exactly ISS's. On it go the
Technomancy parts: a gold band round the pit with four hextech-cyan gems, gold plates on the rim, and in the pit a gold
sphere that holds a hextech energy stone.

The loop: the orb rests (3.5 s) -> the gold sphere splits in two and the stone pops out and crackles -> the orb breaks
into four stones of unequal size that drift apart UNEVENLY (different distances, directions and timing), float and bob,
tied by little arcs and glowing along their cut edges -> they drift back together, the stone sinks, the sphere closes.
"""
import math
import random

from PIL import Image

from premium import MAT, Mat, hue_ramp

import os

C = 15.5
CYA = MAT["cyan_glow"]
# brown gold, in step with the hextech gear (the dragon's bronze and gold): less yellow, more brown
BRASS = Mat(hue_ramp("#A87530", 8, 0.07, 0.8, shadow_hue=0.04, light_hue=0.11), base=0.55, spread=0.55, gloss=0.25)
OUTLINE = (12, 12, 18, 255)
PIT_R = 5.2
SRC_ORB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art_src", "iss_empty_upgrade_orb.png")


def iss_orb():
    """The ISS empty orb's 16x16 pixels, from the 128x128 image the user supplied."""
    return Image.open(SRC_ORB).convert("RGBA").resize((16, 16), Image.NEAREST)


def stone():
    """The ISS orb at 2x, squeezed to 22x22 and centred in 32x32 (spans 5..26). The orb's own near-black outline becomes
    the thin outer GOLD frame; the dark outline is added again outside it by with_outline."""
    src = iss_orb()
    big = Image.new("RGBA", (26, 26), (0, 0, 0, 0))
    for y in range(13):
        for x in range(13):
            p = src.getpixel((x + 2, y + 2))
            if p[3]:
                for dy in (0, 1):
                    for dx in (0, 1):
                        big.putpixel((2 * x + dx, 2 * y + dy), p)
    small = big.resize((22, 22), Image.NEAREST)
    out = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    out.paste(small, (5, 5))
    px = out.load()
    for y in range(32):
        for x in range(32):
            if px[x, y][3] and any(not (0 <= x + dx < 32 and 0 <= y + dy < 32) or px[x + dx, y + dy][3] == 0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = BRASS.color(0.7 + 0.3 * lit(x, y) + (0.05 if (x + y) % 2 else 0))
    # redden: ISS's red cracks stronger, and two more red patches (right/top and left/bottom) in the same palette
    for y in range(32):
        for x in range(32):
            r, g, b, a = px[x, y]
            if a and r > g + 18 and r > b + 18 and r < 200 and not (r > 180 and g > 120):
                px[x, y] = (min(255, int(r * 1.45) + 6), int(g * 1.05), int(b * 1.0), 255)
    for (cx, cy) in ((22, 10), (9, 22)):
        for (dx, dy, c) in ((0, 0, (125, 68, 64)), (1, 0, (92, 44, 40)), (-1, 0, (116, 61, 57)), (0, 1, (83, 39, 34)), (0, -1, (125, 68, 64)), (1, 1, (92, 44, 40))):
            xx, yy = cx + dx, cy + dy
            if 0 <= xx < 32 and 0 <= yy < 32 and px[xx, yy][3] and PIT_R + 1.5 < r_of(xx, yy) < 11.2:
                px[xx, yy] = (min(255, c[0] + 28), c[1] + 6, c[2] + 4, 255)
    return out


def r_of(x, y):
    return math.hypot(x - C, y - C)


def lit(x, y):
    """Light from the top-left: +1 lit .. -1 shaded."""
    return -((x - C) + (y - C)) / (2 * 14.0)


def body():
    """The orb with the Technomancy parts on it, WITHOUT the gold sphere (that is drawn on its own)."""
    img = stone()
    px = img.load()
    for y in range(32):
        for x in range(32):
            if px[x, y][3] == 0:
                continue
            d = r_of(x, y)
            if 5.5 <= d < 7.4:
                px[x, y] = BRASS.color(0.62 + 0.3 * lit(x, y) - (0.06 if d > 6.8 else 0))
            elif 7.4 <= d < 8.0:
                px[x, y] = BRASS.color(0.14 + 0.1 * lit(x, y))
    for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cx, cy = C + ax * 6.4, C + ay * 6.4
        for y in range(32):
            for x in range(32):
                dd = abs(x - cx) + abs(y - cy)
                if px[x, y][3] and dd <= 2.2:
                    px[x, y] = BRASS.ramp[-3] if dd > 1.6 else CYA.color(0.85 - 0.25 * dd + 0.2 * lit(x, y))
    return img


def dome():
    """The gold sphere in the pit."""
    out = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for y in range(32):
        for x in range(32):
            d = r_of(x, y)
            if d <= 3.4:
                out.putpixel((x, y), BRASS.color(0.7 - 0.55 * (d / 3.4) ** 1.6 + 0.35 * lit(x, y)))
    out.putpixel((13, 13), BRASS.ramp[-1])
    out.putpixel((14, 13), BRASS.ramp[-2])
    return out


def piece_of(x, y):
    """Which of the four stones a pixel belongs to: cut lines at uneven angles, jagged (a block-hash wobble)."""
    a = (math.atan2(y - C, x - C) + math.pi) % math.tau
    wob = (((x // 3) * 73856093 ^ (y // 3) * 19349663) % 1000) / 1000.0 - 0.5
    a = (a + wob * 0.55) % math.tau
    k = 0
    for i, c in enumerate((0.5, 1.95, 3.5, 4.95)):
        if a >= c:
            k = i
    return k


# how far each stone drifts at full spread (px), in different directions and by different amounts
DRIFT = ((4.0, -2.0), (-2.0, -4.0), (-4.0, 2.0), (2.0, 4.0))


MAG = (5.0, 4.0, 4.6, 4.8)                      # how far each stone drifts at full spread (uneven)
SKEW = ((1.0, 0.8), (-0.9, 1.1), (-1.1, -0.7), (0.9, -1.0))   # and a little sideways, so none moves straight out


def centres(body_img):
    sums = [[0.0, 0.0, 0] for _ in range(4)]
    for y in range(32):
        for x in range(32):
            if body_img.getpixel((x, y))[3] and r_of(x, y) > PIT_R:
                k = piece_of(x, y)
                sums[k][0] += x
                sums[k][1] += y
                sums[k][2] += 1
    return [(sx / n, sy / n) for sx, sy, n in sums]


def split_pieces(body_img, spread, phase):
    """Four stones; spread 0..1 (each follows it at its own pace), phase drives the floating bob. Each stone moves away
    from the middle (so none overlaps another) by its own distance, with its own sideways drift."""
    cs = centres(body_img)
    offs = []
    for i, (cx, cy) in enumerate(cs):
        t = max(0.0, min(1.0, spread * (1.0 + 0.3 * math.sin(i * 2.1 + 0.7)) - 0.08 * i))
        vx, vy = cx - C, cy - C
        n = math.hypot(vx, vy) or 1.0
        dx = vx / n * MAG[i] + SKEW[i][0]
        dy = vy / n * MAG[i] + SKEW[i][1]
        bob = math.sin(phase * 2.2 + i * 1.7) * 0.9 * (1 if t > 0.5 else t * 2)
        offs.append((round(dx * t), round(dy * t + bob)))
    ids = {}
    for y in range(32):
        for x in range(32):
            if body_img.getpixel((x, y))[3] and r_of(x, y) > PIT_R:
                ids[(x, y)] = piece_of(x, y)
    layers = [Image.new("RGBA", (32, 32), (0, 0, 0, 0)) for _ in range(4)]
    for (x, y), k in ids.items():
        p = body_img.getpixel((x, y))
        edge = any(ids.get((x + dx, y + dy), k) != k for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge and spread > 0.3:
            continue            # the cut edge crumbles away: the gap widens
        if edge and spread > 0.1:
            p = CYA.color(0.55 + 0.25 * lit(x, y))
        nx, ny = x + offs[k][0], y + offs[k][1]
        if 0 <= nx < 32 and 0 <= ny < 32:
            layers[k].putpixel((nx, ny), p)
    return layers, offs, ids


def with_outline(img, color=OUTLINE):
    out = img.copy()
    px, op = img.load(), out.load()
    for y in range(32):
        for x in range(32):
            if px[x, y][3] == 0 and any(0 <= x + dx < 32 and 0 <= y + dy < 32 and px[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                op[x, y] = color
    return out


def gem(radius, glow=1.0):
    """The hextech energy stone: a lit cyan crystal, blocky (a diamond with a brighter heart)."""
    img = Image.new("RGBA", (32, 32))
    for y in range(32):
        for x in range(32):
            d = (abs(x - C) + abs(y - C)) / max(1.0, radius)
            if d <= 1.0:
                img.putpixel((x, y), CYA.color(min(1.0, 1.05 - d * 0.85 + (0.1 if (x < C and y < C) else 0) + 0.1 * (glow - 1))))
    return img


def bolt_line(img, p0, p1, rnd, jitter=1.2):
    steps = max(2, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * 1.2))
    px = img.load()
    for s in range(steps + 1):
        t = s / steps
        x = p0[0] + (p1[0] - p0[0]) * t + (rnd.random() - 0.5) * jitter * math.sin(math.pi * t) * 2
        y = p0[1] + (p1[1] - p0[1]) * t + (rnd.random() - 0.5) * jitter * math.sin(math.pi * t) * 2
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < 32 and 0 <= yi < 32:
            px[xi, yi] = CYA.ramp[-2] if s % 2 else CYA.ramp[4]


def links(img, offs, ids, seed):
    """Little arcs tying neighbouring stones together across the gaps."""
    rnd = random.Random(seed)
    for a in range(4):
        b = (a + 1) % 4
        nb = ((1, 0), (-1, 0), (0, 1), (0, -1))
        pairs = [(x, y) for (x, y), k in ids.items() if k == a and any(ids.get((x + dx, y + dy)) == b for dx, dy in nb)]
        if not pairs:
            continue
        pairs.sort(key=lambda p: r_of(*p))
        for pick in (pairs[len(pairs) // 4], pairs[len(pairs) * 3 // 4]):
            q = next(((pick[0] + dx, pick[1] + dy) for dx, dy in nb if ids.get((pick[0] + dx, pick[1] + dy)) == b), pick)
            bolt_line(img, (pick[0] + offs[a][0], pick[1] + offs[a][1]), (q[0] + offs[b][0], q[1] + offs[b][1]), rnd, 1.0)


def halves(dome_img, split, lift):
    """The gold sphere cut in two (left/right), the halves `split` px apart, the left one a pixel higher."""
    out = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for y in range(32):
        for x in range(32):
            p = dome_img.getpixel((x, y))
            if p[3]:
                sx = -1 if x <= C else 1
                nx, ny = x + sx * split, y - (lift if sx < 0 else 0)
                if 0 <= nx < 32 and 0 <= ny < 32:
                    out.putpixel((nx, ny), p)
    return out


def sparks(img, n, seed, r0=7, r1=14):
    rnd = random.Random(seed)
    for _ in range(n):
        a, r = rnd.random() * math.tau, r0 + rnd.random() * (r1 - r0)
        x, y = int(C + math.cos(a) * r), int(C + math.sin(a) * r)
        if 0 <= x < 32 and 0 <= y < 32:
            img.putpixel((x, y), CYA.ramp[-1] if rnd.random() < 0.5 else CYA.ramp[3])


def pull_streams(img, offs, cs, gem_r, rnd, strength):
    """Streams of electricity from the energy stone out along the cracks between the stones (the stones are held by
    them and pulled back in): one jagged line per crack, from the stone's edge to the rim."""
    for c in (0.5, 1.95, 3.5, 4.95):
        a = c - math.pi
        dx, dy = math.cos(a), math.sin(a)
        # the crack drifts with its two neighbours: aim between them
        k = (0.5, 1.95, 3.5, 4.95).index(c)
        ox = (offs[k - 1][0] + offs[k][0]) / 2.0
        oy = (offs[k - 1][1] + offs[k][1]) / 2.0
        p0 = (C + dx * (gem_r * 0.6 + 1.5), C + dy * (gem_r * 0.6 + 1.5))
        p1 = (C + dx * 12.5 + ox, C + dy * 12.5 + oy)
        bolt_line(img, p0, p1, rnd, 1.5 + 0.4 * (strength > 1))


def compose(b, d, spread, split, gem_r, phase=0.0, bolts=0, seed=0, link=False, spark_n=0):
    """b: the orb body; d: the gold sphere; spread 0 = whole, 1 = fully drifted; split: halves' gap; gem_r: stone size;
    bolts: 0 none, 1 streams, 2 strong streams."""
    out = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    rnd = random.Random(seed)
    layers, offs, ids = split_pieces(b, spread, phase)
    # no overlaps: every pixel belongs to at most one stone
    seen = set()
    for L in layers:
        cur = {(x, y) for y in range(32) for x in range(32) if L.getpixel((x, y))[3]}
        assert not (seen & cur), "stones overlap (spread %.2f)" % spread
        seen |= cur
    if spark_n:
        sparks(out, spark_n, seed + 5)
    pit = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for y in range(32):
        for x in range(32):
            p = b.getpixel((x, y))
            if p[3] and r_of(x, y) <= PIT_R:
                pit.putpixel((x, y), p)
    out.alpha_composite(with_outline(pit) if spread > 0 else pit)
    for L in layers:
        out.alpha_composite(with_outline(L))
    if split:
        out.alpha_composite(halves(d, split, 1 if split > 1 else 0))
        if gem_r > 0:
            out.alpha_composite(gem(gem_r, 1.0 + 0.1 * split))
        else:
            for y in range(int(C) - 3, int(C) + 4):
                out.putpixel((15, y), CYA.ramp[-2])
                out.putpixel((16, y), CYA.ramp[4])
    else:
        out.alpha_composite(d)
    if bolts and spread > 0.15:
        # streams of electricity from the middle out to each floating stone: only in the gaps (never over a stone)
        st = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        pull_streams(st, offs, centres(b), gem_r, rnd, bolts)
        sp, op = st.load(), out.load()
        for y in range(32):
            for x in range(32):
                if sp[x, y][3] and op[x, y][3] == 0:
                    op[x, y] = sp[x, y]
                    for dx, dy in ((1, 0), (0, 1)):
                        if 0 <= x + dx < 32 and 0 <= y + dy < 32 and op[x + dx, y + dy][3] == 0 and (x * 3 + y) % 2:
                            op[x + dx, y + dy] = CYA.ramp[2]
    return out


def frames():
    b, d = body(), dome()
    return [
        (compose(b, d, 0, 0, 0), 70),                                              # rests, closed
        (compose(b, d, 0, 1, 0), 3),                                               # the sphere cracks, a bright seam
        (compose(b, d, 0, 2, 2.4, spark_n=2, seed=1), 3),                          # it splits, the stone peeks out
        (compose(b, d, 0.35, 3, 4.2, 0.0, 1, 2, True), 3),                         # the stone pops out, the orb loosens
        (compose(b, d, 0.7, 3, 5.4, 0.5, 1, 3, True), 4),                          # the stones drift apart unevenly
        (compose(b, d, 1.0, 3, 5.8, 1.0, 2, 4, True), 4),                          # fully apart, floating
        (compose(b, d, 1.0, 3, 5.6, 1.7, 1, 5, True), 4),
        (compose(b, d, 0.85, 3, 5.4, 2.4, 2, 6, True), 3),
        (compose(b, d, 0.5, 3, 4.6, 3.0, 2, 7, True), 3),                          # drifting back together
        (compose(b, d, 0.15, 2, 3.4, 3.5, 1, 8, True), 3),
        (compose(b, d, 0, 1, 0), 3),                                               # whole, the sphere closes
    ]


def strip_and_meta():
    seq = frames()
    strip = Image.new("RGBA", (32, 32 * len(seq)), (0, 0, 0, 0))
    for k, (im, _) in enumerate(seq):
        strip.paste(im, (0, 32 * k))
    meta = {"animation": {"interpolate": False, "frames": [{"index": k, "time": t} for k, (_, t) in enumerate(seq)]}}
    return strip, meta


def preview(path, scale=10):
    seq = frames()
    cols = 4
    W = Image.new("RGB", (cols * (32 * scale + 6), ((len(seq) + cols - 1) // cols) * (32 * scale + 6)), (60, 60, 66))
    for k, (im, t) in enumerate(seq):
        big = im.resize((32 * scale, 32 * scale), Image.NEAREST)
        W.paste(big, ((k % cols) * (32 * scale + 6) + 3, (k // cols) * (32 * scale + 6) + 3), big)
    W.save(path)
