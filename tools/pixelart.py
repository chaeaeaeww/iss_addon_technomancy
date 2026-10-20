"""
Small pixel-art toolkit used by generate_assets.py.

Style target: Create-mod-like steampunk. Warm brass ramps with a dark brown outline, copper accents,
leather and blackened iron, plus a cyan "arcane" core. Light comes from the top-left.
"""
import math

from PIL import Image

CLEAR = (0, 0, 0, 0)


def rgb(hex_color, alpha=255):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


# ------------------------------------------------------------------------------------------- palette ramps (dark -> light)
OUTLINE = rgb("2B1A0C")
BRASS = [rgb("5C3A12"), rgb("8A5A1E"), rgb("B97D2A"), rgb("DDA341"), rgb("F2C766"), rgb("FFE9A8")]
COPPER = [rgb("4A2214"), rgb("7A3A22"), rgb("A8553A"), rgb("CF7650"), rgb("EA9C72")]
LEATHER = [rgb("2A1A10"), rgb("3E2617"), rgb("573521"), rgb("71472C"), rgb("8C5C3A")]
IRON = [rgb("1E2026"), rgb("2F323A"), rgb("454953"), rgb("62676F"), rgb("8C929C"), rgb("BAC0C8")]
CLOTH = [rgb("1C1A1E"), rgb("2A272E"), rgb("3A3640"), rgb("4D4854")]
STONE = [rgb("232328"), rgb("34343B"), rgb("46464E"), rgb("5A5A63"), rgb("70707A")]
CYAN = [rgb("0E4C57"), rgb("1E8FA0"), rgb("4FE3F0"), rgb("A6F6FB"), rgb("E6FFFF")]
PAPER = [rgb("8C6A3E"), rgb("B99566"), rgb("DCC093"), rgb("F0DDB4")]
STEAM = [rgb("8F959C"), rgb("B9BEC4"), rgb("E1E4E7")]


def ramp(colors, t):
    """t in [0,1] -> color from a ramp."""
    t = max(0.0, min(0.999, t))
    return colors[int(t * len(colors))]


def new(w, h=None):
    return Image.new("RGBA", (w, h if h is not None else w), CLEAR)


def put(img, x, y, color):
    if 0 <= x < img.width and 0 <= y < img.height and color is not None:
        img.putpixel((int(x), int(y)), color)


def filled(img, x, y):
    return 0 <= x < img.width and 0 <= y < img.height and img.getpixel((x, y))[3] > 0


def inner_outline(img, color=OUTLINE):
    """Repaint every opaque pixel that touches transparency (4-neighbourhood) with the outline color."""
    w, h = img.size
    edge = [(x, y) for y in range(h) for x in range(w)
            if filled(img, x, y) and not all(filled(img, x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        img.putpixel((x, y), color)
    return img


def stamp(img, x0, y0, rows, palette):
    """Draw an ASCII grid; '.' and ' ' are skipped, other chars are looked up in palette."""
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in ". ":
                continue
            put(img, x0 + x, y0 + y, palette[ch])
    return img


def lit(nx, ny):
    """Lambert-ish factor for a 2D normal with light from the top-left. Returns 0..1."""
    length = math.hypot(nx, ny) or 1.0
    return 0.5 + 0.5 * ((-nx - ny) / length) / math.sqrt(2) * math.sqrt(2) * 0.7071


# ------------------------------------------------------------------------------------------- shapes

def gear(img, cx, cy, r_outer, r_root, teeth, colors=BRASS, angle=0.0, hole=0.0, hub=None, spokes=0, tooth_width=0.5, outline=True):
    """
    Draws a cogwheel. Each pixel is classified by polar coordinates (supersampled 3x3), then shaded with
    the light coming from the top-left: brighter on the upper-left rim, darker bottom-right.
    """
    layer = new(img.width, img.height)
    for py in range(img.height):
        for px in range(img.width):
            hits = 0
            for sy in (-0.33, 0, 0.33):
                for sx in (-0.33, 0, 0.33):
                    dx, dy = px + 0.5 + sx - cx, py + 0.5 + sy - cy
                    r = math.hypot(dx, dy)
                    a = (math.atan2(dy, dx) - angle) % (2 * math.pi)
                    phase = (a * teeth / (2 * math.pi)) % 1.0
                    limit = r_outer if phase < tooth_width else r_root
                    if r <= limit and r >= hole:
                        hits += 1
            if hits < 5:
                continue
            dx, dy = px + 0.5 - cx, py + 0.5 - cy
            r = math.hypot(dx, dy)
            # rim lighting
            t = 0.55 + 0.45 * ((-dx - dy) / (r or 1)) * min(1.0, r / max(1.0, r_root))
            # recessed groove between hub and rim
            if hub and hub[0] <= r <= hub[1]:
                t -= 0.35
            if spokes and hub and r < hub[0]:
                a = (math.atan2(dy, dx) - angle) % (2 * math.pi)
                if (a * spokes / (2 * math.pi)) % 1.0 > 0.35 and r > hole + 1.2:
                    t -= 0.45
            put(layer, px, py, ramp(colors, t))
    if outline:
        inner_outline(layer)
    img.alpha_composite(layer)
    return img


def disc(img, cx, cy, r, colors, outline=True, highlight=True):
    layer = new(img.width, img.height)
    for py in range(img.height):
        for px in range(img.width):
            dx, dy = px + 0.5 - cx, py + 0.5 - cy
            d = math.hypot(dx, dy)
            if d <= r:
                t = 0.55 + 0.45 * ((-dx - dy) / (r or 1))
                put(layer, px, py, ramp(colors, t))
    if outline:
        inner_outline(layer)
    if highlight and r >= 1.5:
        put(layer, int(cx - r * 0.35), int(cy - r * 0.35), colors[-1])
    img.alpha_composite(layer)
    return img


def line(img, x0, y0, x1, y1, color):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(steps):
        t = i / max(1, steps - 1)
        put(img, round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), color)


def rect(img, x0, y0, x1, y1, color):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(img, x, y, color)


def bevel_rect(img, x0, y0, x1, y1, colors, outline=OUTLINE):
    """Filled rectangle with a light top-left edge and dark bottom-right edge."""
    rect(img, x0, y0, x1, y1, colors[len(colors) // 2])
    line(img, x0, y0, x1, y0, colors[-1])
    line(img, x0, y0, x0, y1, colors[-2])
    line(img, x0, y1, x1, y1, colors[1])
    line(img, x1, y0, x1, y1, colors[1])
    if outline:
        line(img, x0 - 1, y0 - 1, x1 + 1, y0 - 1, outline)
        line(img, x0 - 1, y1 + 1, x1 + 1, y1 + 1, outline)
        line(img, x0 - 1, y0, x0 - 1, y1, outline)
        line(img, x1 + 1, y0, x1 + 1, y1, outline)


def noise(img, x0, y0, x1, y1, amount, seed):
    """Deterministic per-pixel brightness jitter for material texture (leather grain, cast iron)."""
    import random
    rnd = random.Random(seed)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if not filled(img, x, y):
                continue
            r, g, b, a = img.getpixel((x, y))
            f = 1.0 + rnd.uniform(-amount, amount)
            img.putpixel((x, y), (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)), a))


def gradient_bg(img, top, bottom, vignette=0.35):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            t = y / max(1, h - 1)
            c = [int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)]
            dx, dy = (x + 0.5) / w - 0.5, (y + 0.5) / h - 0.5
            v = 1.0 - vignette * min(1.0, (dx * dx + dy * dy) * 3.2)
            img.putpixel((x, y), (int(c[0] * v), int(c[1] * v), int(c[2] * v), 255))
    return img


def upscale(img, factor):
    return img.resize((img.width * factor, img.height * factor), Image.NEAREST)
