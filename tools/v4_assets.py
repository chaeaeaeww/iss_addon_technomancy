"""
Update 1.3 assets: Magnetic Field dome texture and the rest of the 1.3 art (see the other modules imported by
generate_assets.py). Only small textures live here; the big models have their own modules (blitz_v3.py,
dragon_v3.py, technomancer_v2.py, sentry_v3.py).
"""
import math

from pixelart import CYAN, new, put


def magnetic_dome(w=128, h=64):
    """Tileable dome shell: faint hexagonal lattice, brighter meridian field lines and a glowing rim at the bottom
    (v = 1 is the ground ring, v = 0 the top of the dome)."""
    img = new(w, h)
    for y in range(h):
        for x in range(w):
            v = y / (h - 1)
            # hex lattice (two sets of slanted lines + horizontals)
            hx = x / 8.0
            hy = y / (8.0 * 0.866)
            a = abs(((hx + hy * 0.5) % 1) - 0.5)
            b = abs(((hx - hy * 0.5) % 1) - 0.5)
            c = abs((hy % 1) - 0.5)
            lattice = min(a, b, c * 1.1)
            alpha = 0
            col = CYAN[2]
            if lattice < 0.06:
                alpha = 70
                col = CYAN[2]
            # meridian field lines
            if x % 16 in (0, 1):
                alpha = max(alpha, 120)
                col = CYAN[3]
            # glowing ground rim and a soft gradient towards it
            if v > 0.9:
                alpha = max(alpha, int(150 + 100 * (v - 0.9) / 0.1))
                col = CYAN[3] if v < 0.97 else CYAN[4]
            alpha = max(alpha, int(18 + 40 * v))
            if alpha:
                put(img, x, y, (col[0], col[1], col[2], min(255, alpha)))
    return img
