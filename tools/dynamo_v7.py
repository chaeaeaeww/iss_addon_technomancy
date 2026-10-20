"""
Iron's Technomancy 1.10: the Overcharged Dynamo Core as a 3D item (a block-model of elements, so it is solid in the
hand, on the ground, in item frames and set in the Hextech Thunderforge's cradle; the inventory keeps the flat icon
through forge:separate_transforms). Hextech colours: navy body, brass end caps and a coil cage, glowing cyan coil
bands and core window (forge_data full-bright on the glowing faces).
"""
import math

from PIL import Image

from premium import MAT, Canvas, Mat, circle, gear, hue_ramp, rect

NS = "iss_technomancy:"
NAVY2 = Mat(hue_ramp("#1A2550", 8, 0.02, 0.5, shift=0.05), base=0.5, spread=0.5, gloss=0.2, dither=True)
B, BD, CYA = MAT["brass"], MAT["brass_dark"], MAT["cyan_glow"]


def tex(fn):
    c = Canvas(16)
    fn(c)
    return c.render(outline=False, shadow=False)


def textures():
    def body(c):
        c.add(rect(0, 0, 16, 16), NAVY2, bevel=3, tone=0.05)
        for y in (3, 12):
            c.add(rect(0, y, 16, y + 1.6), CYA, flat=True, tone=0.05)
        for x in (0, 15):
            c.add(rect(x, 0, x + 1, 16), BD, flat=True)

    def cap(c):
        c.add(rect(0, 0, 16, 16), B, bevel=4)
        c.add(gear(8, 8, 6.5, 5, 8, hole=2.5), BD, flat=True, tone=0.1)
        c.add(circle(8, 8, 2.4), CYA, dome=0.8)

    def window(c):
        c.add(rect(0, 0, 16, 16), CYA, bevel=4, tone=-0.1)
        for k in range(3):
            y = 4 + k * 4
            c.line(1, y, 5, y - 2, CYA.ramp[-1])
            c.line(5, y - 2, 9, y + 1, CYA.ramp[-1])
            c.line(9, y + 1, 14, y - 1, CYA.ramp[-1])

    def cage(c):
        c.add(rect(0, 0, 16, 16), B, bevel=2.5, tone=0.05)
    return {"dynamo_body": tex(body), "dynamo_cap": tex(cap), "dynamo_window": tex(window), "dynamo_cage": tex(cage)}


def el(f, t, tx, glow=False, rot=None, faces=None):
    faces = faces or ("north", "south", "east", "west", "up", "down")
    out = {}
    for face in faces:
        if face in ("north", "south"):
            uv = [f[0], 16 - t[1], t[0], 16 - f[1]]
        elif face in ("east", "west"):
            uv = [f[2], 16 - t[1], t[2], 16 - f[1]]
        else:
            uv = [f[0], f[2], t[0], t[2]]
        d = {"uv": [max(0, min(16, v)) for v in uv], "texture": tx}
        if glow:
            d["forge_data"] = {"block_light": 15, "sky_light": 15}
        out[face] = d
    e = {"from": f, "to": t, "faces": out}
    if rot:
        e["rotation"] = rot
    return e


def model():
    """A squat cylinder of coil (two squares turned 45 degrees), brass end caps, four brass cage posts, a cyan core
    window front and back, cyan coil bands."""
    E = [
        el([4, 3, 4], [12, 13, 12], "#body"),
        el([4, 3, 4], [12, 13, 12], "#body", rot={"angle": 45, "axis": "y", "origin": [8, 8, 8]}),
        el([3.4, 1.5, 3.4], [12.6, 3, 12.6], "#cap"),
        el([3.4, 13, 3.4], [12.6, 14.5, 12.6], "#cap"),
        el([5.5, 14.5, 5.5], [10.5, 15.5, 10.5], "#cap"),
        el([5.5, 0.5, 5.5], [10.5, 1.5, 10.5], "#cap"),
        el([6, 6, 3.6], [10, 10, 12.4], "#window", glow=True),
    ]
    for (x, z) in ((3.2, 3.2), (11.8, 3.2), (3.2, 11.8), (11.8, 11.8)):
        E.append(el([x - 0.5, 3, z - 0.5], [x + 0.5, 13, z + 0.5], "#cage", rot={"angle": 45, "axis": "y", "origin": [8, 8, 8]}))
    for y in (5, 10.4):
        E.append(el([3.7, y, 3.7], [12.3, y + 0.8, 12.3], "#window", glow=True))
    display = {
        "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.45, 0.45, 0.45]},
        "thirdperson_lefthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.45, 0.45, 0.45]},
        "firstperson_righthand": {"rotation": [0, 45, 0], "translation": [1, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "firstperson_lefthand": {"rotation": [0, 225, 0], "translation": [1, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.4, 0.4, 0.4]},
        "fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.85, 0.85, 0.85]},
        "head": {"rotation": [0, 0, 0], "translation": [0, 8, 0], "scale": [0.8, 0.8, 0.8]},
    }
    base = {"parent": "block/block", "textures": {"body": NS + "item/dynamo_body", "cap": NS + "item/dynamo_cap", "window": NS + "item/dynamo_window",
                                                  "cage": NS + "item/dynamo_cage", "particle": NS + "item/dynamo_body"},
            "elements": E, "display": display}
    return {"loader": "forge:separate_transforms", "gui_light": "front",
            "base": base,
            "perspectives": {"gui": {"parent": "item/generated", "textures": {"layer0": NS + "item/overcharged_dynamo_core"}}}}


def write_all(out, write_json):
    for name, im in textures().items():
        im.save(out("textures/item/%s.png" % name))
    write_json("models/item/overcharged_dynamo_core.json", model())
