"""
Position-aware materials: a Surface painter is bound to its cube and paints every texel from the model-space point it
covers, so neighbouring cubes (stacked hull bands, emblem pieces, wing plates...) share one continuous gradient,
seam layout or decal instead of each face being shaded on its own.

UV orientation follows GeckoLib/preview_geo: north u = +x, v = -y; south u = -x; east u = +z; west u = -z;
up u = +x, v = -z (row 0 at the back); down u = +x, v = +z after the flipped down UV written by models.build.
"""
from models import C


class Surface:
    """fn(face, x, y, z, i, j, w, h) -> color, (color, glow_color) or None (skip). Bound to a cube via cube()."""

    def __init__(self, fn, density=2.0):
        self.fn = fn
        self.density = density
        self.cube_ref = None

    def __call__(self, img, x, y, w, h, face):
        import models
        c = self.cube_ref
        ox, oy, oz = c.origin
        sw, sh, sd = c.size
        for j in range(h):
            for i in range(w):
                fu = (i + 0.5) / w
                fv = (j + 0.5) / h
                if face == "north":
                    p = (ox + fu * sw, oy + sh - fv * sh, oz)
                elif face == "south":
                    p = (ox + sw - fu * sw, oy + sh - fv * sh, oz + sd)
                elif face == "east":
                    p = (ox + sw, oy + sh - fv * sh, oz + fu * sd)
                elif face == "west":
                    p = (ox, oy + sh - fv * sh, oz + sd - fu * sd)
                elif face == "up":
                    p = (ox + fu * sw, oy + sh, oz + sd - fv * sd)
                else:  # down (row 0 = back after the flipped UV)
                    p = (ox + fu * sw, oy, oz + sd - fv * sd)
                r = self.fn(face, p[0], p[1], p[2], i, j, w, h)
                if r is None:
                    continue
                if isinstance(r, tuple) and len(r) == 2 and isinstance(r[0], tuple):
                    col, glow = r
                else:
                    col, glow = r, None
                img.putpixel((x + i, y + j), col)
                if glow is not None:
                    models.glow_put(x + i, y + j, glow)


def surf_cube(bone, origin, size, fn, name=None, **kw):
    s = Surface(fn)
    c = C(bone, list(origin), list(size), s, name=name, **kw)
    s.cube_ref = c
    return c
