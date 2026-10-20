"""
"Premium Fantasy" pixel-art toolkit (see ART_STYLE_PREMIUM_FANTASY.md).

    c = Canvas(32)
    c.add(shape, MAT["brass"], bevel=2.5)          # bevelled, lit, hue-shifted ramp
    c.add(shape2, MAT["cyan_glow"], glow=True)     # emissive accent
    c.sparkle(25, 6, MAT["cyan_glow"])
    img = c.render()

Shapes are predicates on pixel-centre coordinates (x, y) in canvas pixels. Later shapes sit on top of earlier ones and
cast a 1-px shadow down-right onto them (ambient occlusion), every silhouette gets a dark outline in the colour of its
own material, and every material is drawn from a 6-8 step hue-shifted ramp.
"""
import colorsys
import math

import numpy as np
from PIL import Image

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.47
KEY = np.array([-0.55, -0.62, 0.56])          # light from the top-left, a little in front
KEY = KEY / np.linalg.norm(KEY)
RIM = np.array([0.7, 0.6, 0.38])
RIM = RIM / np.linalg.norm(RIM)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def hue_ramp(base, n=8, lo=0.05, hi=0.95, shadow_hue=0.66, light_hue=0.14, shift=0.09, sat_curve=0.25):
    """n colours dark -> light around `base` (hex). Shadows slide toward shadow_hue (cool), highlights toward light_hue
    (warm) by up to `shift` of the hue circle; saturation peaks in the mid tones."""
    r, g, b = hexrgb(base)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    out = []
    for i in range(n):
        t = i / (n - 1)
        L = lo + (hi - lo) * t
        target = shadow_hue if t < 0.5 else light_hue
        k = abs(t - 0.5) * 2 * shift
        dh = ((target - h + 0.5) % 1.0) - 0.5
        hh = (h + max(-k, min(k, dh))) % 1.0
        ss = max(0.0, min(1.0, s * (1 - sat_curve * abs(t - 0.55) * 1.6)))
        rr, gg, bb = colorsys.hls_to_rgb(hh, L, ss)
        out.append((int(rr * 255), int(gg * 255), int(bb * 255), 255))
    return out


class Mat:
    def __init__(self, ramp, glow=False, base=0.5, spread=0.55, gloss=0.25, dither=False):
        self.ramp, self.glow, self.base, self.spread, self.gloss, self.dither = ramp, glow, base, spread, gloss, dither

    @property
    def dark(self):
        return self.ramp[0]

    def color(self, t):
        return self.ramp[max(0, min(len(self.ramp) - 1, int(round(t * (len(self.ramp) - 1)))))]


MAT = {
    "brass": Mat(hue_ramp("#C99A3A", 8, 0.06, 0.93), base=0.55, spread=0.6, gloss=0.35),
    "brass_dark": Mat(hue_ramp("#8E6424", 7, 0.05, 0.75), base=0.45, spread=0.45),
    "copper": Mat(hue_ramp("#B8603A", 8, 0.06, 0.88), base=0.5, spread=0.55, gloss=0.3),
    "walnut": Mat(hue_ramp("#6A4026", 7, 0.05, 0.6), base=0.5, spread=0.45, gloss=0.1, dither=True),
    "leather": Mat(hue_ramp("#7A4A2A", 7, 0.05, 0.62), base=0.5, spread=0.5, gloss=0.08, dither=True),
    "cream": Mat(hue_ramp("#E2CC9C", 7, 0.25, 0.97, shift=0.05), base=0.6, spread=0.4, gloss=0.05, dither=True),
    "andesite": Mat(hue_ramp("#7E8576", 7, 0.08, 0.78, shift=0.05), base=0.5, spread=0.5, gloss=0.1, dither=True),
    "iron": Mat(hue_ramp("#5E6470", 7, 0.05, 0.85, shift=0.04), base=0.45, spread=0.55, gloss=0.4),
    "navy": Mat(hue_ramp("#1E2F66", 8, 0.03, 0.6, shift=0.05), base=0.5, spread=0.55, gloss=0.25, dither=True),
    "amber_glow": Mat(hue_ramp("#FF9A1E", 7, 0.22, 0.97, shadow_hue=0.0, light_hue=0.15, sat_curve=0.0), glow=True, base=0.72, spread=0.4, gloss=0.5),
    "wine": Mat(hue_ramp("#9A2244", 7, 0.08, 0.85, shadow_hue=0.75, light_hue=0.98), base=0.55, spread=0.55, gloss=0.45),
    "cyan_glow": Mat(hue_ramp("#38B4FF", 7, 0.22, 0.98, shadow_hue=0.66, light_hue=0.5, sat_curve=0.0), glow=True, base=0.72, spread=0.4, gloss=0.5),
    "violet_glow": Mat(hue_ramp("#8A4CFF", 7, 0.15, 0.95, shadow_hue=0.72, light_hue=0.8, sat_curve=0.0), glow=True, base=0.68, spread=0.45, gloss=0.5),
    "steel_blade": Mat(hue_ramp("#9AA6C0", 8, 0.08, 0.98, shift=0.06), base=0.55, spread=0.6, gloss=0.6),
}


class Canvas:
    def __init__(self, n=32):
        self.n = n
        self.color = [[None] * n for _ in range(n)]
        self.mat = [[None] * n for _ in range(n)]
        self.layer = np.full((n, n), -1)
        self.k = 0
        self.extra = []

    def mask(self, inside):
        m = np.zeros((self.n, self.n), dtype=bool)
        for y in range(self.n):
            for x in range(self.n):
                m[y, x] = bool(inside(x + 0.5, y + 0.5))
        return m

    @staticmethod
    def distance(m):
        """Chamfer distance (px) from each inside pixel to the outside."""
        n = m.shape[0]
        d = np.where(m, 99.0, 0.0)
        for _ in range(2):
            for y in range(n):
                for x in range(n):
                    if not m[y, x]:
                        continue
                    for dy, dx, w in ((-1, 0, 1), (0, -1, 1), (-1, -1, 1.41), (-1, 1, 1.41)):
                        yy, xx = y + dy, x + dx
                        v = d[yy, xx] if 0 <= yy < n and 0 <= xx < n else 0.0
                        d[y, x] = min(d[y, x], v + w)
            for y in range(n - 1, -1, -1):
                for x in range(n - 1, -1, -1):
                    if not m[y, x]:
                        continue
                    for dy, dx, w in ((1, 0, 1), (0, 1, 1), (1, 1, 1.41), (1, -1, 1.41)):
                        yy, xx = y + dy, x + dx
                        v = d[yy, xx] if 0 <= yy < n and 0 <= xx < n else 0.0
                        d[y, x] = min(d[y, x], v + w)
        return d

    def add(self, inside, mat, bevel=2.0, dome=0.0, flat=False, tone=0.0, glow=None):
        """Paint a shape. bevel: rounded edge width (px); dome: extra overall roundness (0 flat .. 1 sphere); tone:
        shift along the ramp (+lighter)."""
        m = self.mask(inside) if callable(inside) else inside
        if not m.any():
            return m
        d = self.distance(m)
        h = np.sqrt(np.clip(d / max(0.5, bevel), 0, 1))
        if dome > 0:
            ys, xs = np.nonzero(m)
            cy, cx = ys.mean(), xs.mean()
            r = max(1.0, max(np.ptp(ys), np.ptp(xs)) / 2 + 0.5)
            yy, xx = np.mgrid[0:self.n, 0:self.n]
            sph = np.sqrt(np.clip(1 - ((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r), 0, 1))
            h = h * (1 - dome) + sph * dome
        gy, gx = np.gradient(h)
        self.k += 1
        for y in range(self.n):
            for x in range(self.n):
                if not m[y, x]:
                    continue
                if flat:
                    v = mat.base + tone
                else:
                    nrm = np.array([-gx[y, x] * 2.2, -gy[y, x] * 2.2, 1.0])
                    nrm /= np.linalg.norm(nrm)
                    key = float(nrm @ KEY)
                    rim = max(0.0, float(nrm @ RIM) - 0.75) * 1.6
                    grad = -((x - self.n / 2) + (y - self.n / 2)) / self.n * 0.25
                    v = mat.base + tone + mat.spread * (key - 0.62) * 1.25 + rim * 0.25 + grad
                    if mat.gloss and key > 0.93:
                        v += mat.gloss
                if mat.dither:
                    v += BAYER4[y % 4, x % 4] * 0.13
                self.color[y][x] = mat.color(v)
                self.mat[y][x] = mat
                self.layer[y, x] = self.k
        return m

    def px(self, x, y, color, mat=None):
        if 0 <= x < self.n and 0 <= y < self.n:
            self.color[y][x] = color
            if mat is not None:
                self.mat[y][x] = mat
            if self.layer[y, x] < 0:
                self.layer[y, x] = self.k

    def line(self, x0, y0, x1, y1, color, mat=None):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / max(1, steps)
            self.px(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), color, mat)

    def spike(self, x0, y0, x1, y1, mat, width=1.6):
        """A tapering spike from a base at (x0, y0) to a 1-px point at (x1, y1)."""
        L = math.hypot(x1 - x0, y1 - y0)

        def inside(x, y):
            dx, dy = x1 - x0, y1 - y0
            t = ((x - x0) * dx + (y - y0) * dy) / max(1e-6, L * L)
            if t < 0 or t > 1:
                return False
            px, py = x0 + dx * t, y0 + dy * t
            return math.hypot(x - px, y - py) <= width * (1 - t) * 0.5 + 0.35
        return self.add(inside, mat, bevel=1.0)

    def sparkle(self, x, y, mat, big=False):
        """A magic particle: bright centre, dimmer arms (plus shape) - drawn after render() on top of everything."""
        self.extra.append((x, y, mat, big))

    def rune(self, x, y, glyph, color):
        for j, row in enumerate(RUNES[glyph]):
            for i, ch in enumerate(row):
                if ch == "#":
                    self.px(x + i, y + j, color)

    def render(self, outline=True, shadow=True):
        n = self.n
        out = [row[:] for row in self.color]
        if shadow:
            # 1-px contact shadow / ambient occlusion where a higher layer overlaps a lower one (light from top-left)
            for y in range(n):
                for x in range(n):
                    if out[y][x] is None or x == 0 or y == 0:
                        continue
                    up = self.layer[y - 1, x - 1]
                    if up > self.layer[y, x] and self.mat[y][x] is not None and not self.mat[y][x].glow:
                        r = self.mat[y][x].ramp
                        i = max(0, r.index(out[y][x]) - 2) if out[y][x] in r else 0
                        out[y][x] = r[i]
        if outline:
            res = [row[:] for row in out]
            for y in range(n):
                for x in range(n):
                    if out[y][x] is None:
                        continue
                    nb = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                    if any(not (0 <= a < n and 0 <= b < n) or out[b][a] is None for a, b in nb):
                        m = self.mat[y][x]
                        if m is None:
                            continue
                        # selective outline: the lit top-left edge one step lighter than the shaded bottom-right
                        lit_edge = (x - 1 < 0 or out[y][x - 1] is None or y - 1 < 0 or out[y - 1][x] is None) and \
                                   not (x + 1 >= n or out[y][x + 1] is None or y + 1 >= n or out[y + 1][x] is None)
                        res[y][x] = m.ramp[1] if (lit_edge and m.glow) else (m.ramp[1] if lit_edge and len(m.ramp) > 6 and m.base > 0.5 else m.ramp[0])
            out = res
        img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        for y in range(n):
            for x in range(n):
                if out[y][x] is not None:
                    img.putpixel((x, y), out[y][x])
        for x, y, mat, big in self.extra:
            for dx, dy, k in ((0, 0, -1), (1, 0, -3), (-1, 0, -3), (0, 1, -3), (0, -1, -3)) + (((2, 0, -5), (-2, 0, -5), (0, 2, -5), (0, -2, -5)) if big else ()):
                xx, yy = int(x + dx), int(y + dy)
                if 0 <= xx < n and 0 <= yy < n:
                    img.putpixel((xx, yy), mat.ramp[k])
        return img

    def glowmask(self, img):
        """Emissive pixels only (for GeckoLib glowmasks / reference)."""
        g = Image.new("RGBA", img.size, (0, 0, 0, 0))
        for y in range(self.n):
            for x in range(self.n):
                if self.mat[y][x] is not None and self.mat[y][x].glow:
                    g.putpixel((x, y), img.getpixel((x, y)))
        return g


RUNES = {
    "a": ["#.#", ".#.", "#.#"], "b": ["##.", "#.#", "##."], "c": [".#.", "###", ".#."], "d": ["#..", "###", "..#"],
    "e": ["###", "#..", "##."], "f": ["#.#", "###", "#.#"], "g": [".#", "##", ".#"], "h": ["#.", "##", "#."],
}


# ---- shapes (pixel-centre predicates, canvas pixels)

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
        return (x - ax - dx * t) ** 2 + (y - ay - dy * t) ** 2 <= r * r
    return inside


def gear(cx, cy, r_out, r_root, teeth, hole=0.0, phase=0.0, tooth=0.5):
    def inside(x, y):
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        if d < hole or d > r_out:
            return False
        if d <= r_root:
            return True
        a = (math.atan2(dy, dx) / (2 * math.pi) * teeth + phase) % 1.0
        return abs(a - 0.5) < tooth / 2
    return inside


def rect(x0, y0, x1, y1):
    return lambda x, y: x0 <= x <= x1 and y0 <= y <= y1


def union(*fs):
    return lambda x, y: any(f(x, y) for f in fs)


def minus(a, b):
    return lambda x, y: a(x, y) and not b(x, y)


def diamond(cx, cy, rx, ry):
    return poly([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)])
