"""
Tech Dragon 1.10: the spin discharge, the spacing hops, the sky breath and the strafing run.

- spin_discharge: braced low, wings half open, it whirls a full turn on the spot (0.4-1.2 s) with the tail flung out
  wide, the crest and core flaring at the height of the turn (the discharge at 0.8 s is the server's);
- hop_forward / hop_back: a short crouch-and-spring forward or back (hop 0.18 s, land 0.52 s like the side dodges,
  which the sideways hops reuse), wings flicked open for balance, landing already braced to strike;
- breath_down: hovering on strong beats, neck arched down, jaws wide - the lightning breath poured down on the target
  from above (loop);
- strafe: the low fast pass, wings swept half back, head low and forward, the jaws snapping open now and then (loop).
"""
import math

import anim_v4 as A
from anim_v4 import Anim, wave
from dragon_v4_anims import LEGS, NECK, STAND, TAIL, add, merge, smooth_window
from dragon_v4_anims2 import AIR, HOVER_BASE, LEGS_HANG, LOW_SPREAD, SWEPT, WIDE, flap_layer, glow_pulse, jitter, tail_wave_air
from dragon_v5_anims import LEGS_TUCK_SOFT, window
from dragon_v4_anims import FOLD_LOOSE


def spin_discharge():
    a = Anim("spin_discharge", 1.7, False)
    brace = merge(add(STAND, {"body@pos": [0, -3.5, 0], "chest": [5, 0, 0], "neck1": [8, 0, 0], "neck3": [4, 0, 0], "head": [-6, 0, 0], "jaw": [14, 0, 0],
                              **{TAIL[k]: [3, -3 - k * 0.6, 0] for k in range(8)}}), LOW_SPREAD)
    whirl = merge(add(STAND, {"body@pos": [0, -2.0, 0], "chest": [2, 0, 0], "neck1": [4, 12, 0], "neck3": [2, 8, 0], "head": [-10, 10, 0], "jaw": [34, 0, 0],
                              **{TAIL[k]: [6, 6 + k * 1.6, 0] for k in range(8)}, "crest@scale": [1.3, 1.3, 1.3], "core@scale": [1.6, 1.6, 1.6]}), WIDE)
    a.seq([(0.0, STAND, "smooth"), (0.32, brace, "out2"), (0.55, whirl, "out2"), (1.15, whirl, "smooth"),
           (1.4, merge(brace, {"jaw": [8, 0, 0]}), "in2"), (1.7, STAND, "smooth")])
    # the turn itself: a full revolution of the body, fast in the middle
    a.layer(lambda t: {"body": [0, 360.0 * smooth_window(t, 0.4, 1.2, 9, 10) if t < 1.2 else 360.0, 0]})
    a.layer(lambda t: {"body@pos": [0, 1.2 * math.sin(math.pi * min(1, max(0, (t - 0.4) / 0.8))), 0]})
    a.layer(glow_pulse(0.12, 1.0, 1.35, 0.6, 1.0)).layer(jitter(0.8, ("head", "neck3", "wing_l3"), 0.7, 0.95))
    a.lag(TAIL, 0.035).lag(NECK, 0.03)
    w = lambda t: 1.0 - smooth_window(t, 0.35, 0.42, 1.2, 1.35)
    for leg in LEGS:
        a.plant(leg, weight=w)
    a.events = {"spin": 0.4, "discharge": 0.8}
    return a


def _hop(name, back):
    """A short spring forward (back=False) or backwards; same timing as dodge_left."""
    a = Anim(name, 0.85, False)
    lean = -1 if back else 1
    crouch = add(STAND, {"body@pos": [0, -4.0, -1.5 * lean], "chest": [6 * lean, 0, 0], "neck1": [8, 0, 0], "head": [-6, 0, 0]})
    air = merge(add(STAND, {"body@pos": [0, 1.5, 1.0 * lean], "chest": [-6 * lean, 0, 0], "neck1": [-4, 0, 0], "neck3": [4, 0, 0], "head": [-2, 0, 0],
                            "jaw": [12, 0, 0], "tail1": [8, 0, 0], "tail2": [5, 0, 0]}), LEGS_TUCK_SOFT, WIDE)
    land = merge(add(STAND, {"body@pos": [0, -3.0, 0], "chest": [5, 0, 0], "neck1": [8, 0, 0], "head": [-6, 0, 0], "jaw": [10, 0, 0]}), LOW_SPREAD)
    a.seq([(0.0, STAND, "smooth"), (0.14, merge(crouch, FOLD_LOOSE), "out2"), (0.32, air, "out2"), (0.52, land, "in2"), (0.85, STAND, "smooth")])
    a.lag(NECK, 0.03).lag(TAIL, 0.05)
    a.lag(["wing_l", "wing_l2", "wing_l3"], 0.025).lag(["wing_r", "wing_r2", "wing_r3"], 0.025)
    wgt = window(0.17, 0.26, 0.46, 0.54)
    for leg in LEGS:
        a.plant(leg, weight=wgt)
    a.events = {"hop": 0.18, "land": 0.52}
    return a


def hop_forward():
    return _hop("hop_forward", False)


def hop_back():
    return _hop("hop_back", True)


def breath_down():
    L = 1.6
    a = Anim("breath_down", L, True)
    pose = merge(HOVER_BASE, {"body": [-4, 0, 0], "neck1": [26, 0, 0], "neck2": [18, 0, 0], "neck3": [10, 0, 0], "neck4": [4, 0, 0], "head": [2, 0, 0],
                              "jaw": [46, 0, 0], "core@scale": [1.4, 1.4, 1.4], "crest@scale": [1.15, 1.15, 1.15]})
    a.key(0, pose).key(L, pose)
    a.layer(flap_layer(L, 46, 1.0, 2.0)).layer(jitter(1.1, ("head", "neck4"))).layer(glow_pulse(0.2, 1.3, 1.5)).layer(tail_wave_air(L, 2.5))
    a.lag(NECK, 0.03)
    return a


def strafe():
    L = 1.0
    a = Anim("strafe", L, True)
    pose = merge(AIR, SWEPT, {"body": [8, 0, 0], "neck1": [6, 0, 0], "neck2": [4, 0, 0], "neck3": [2, 0, 0], "head": [6, 0, 0], "jaw": [10, 0, 0]})
    a.key(0, pose).key(L, pose)
    a.layer(lambda t: {"wing_l": [wave(t, 0.5, 2.0), 0, wave(t, 0.5, 6.0)], "wing_l3": [0, 0, wave(t, 0.25, 3.0)],
                       "jaw": [24 * max(0.0, math.sin(2 * math.pi * t / L)) ** 4, 0, 0], "head": [wave(t, 0.5, 2.0), 0, 0]})
    a.layer(glow_pulse(0.25, 1.0, 1.25)).layer(tail_wave_air(0.5, 1.2))
    return a


ANIMS8 = [spin_discharge, hop_forward, hop_back, breath_down, strafe]


def add_to(anims, events, rig):
    for fn in ANIMS8:
        a = fn()
        anims[a.name] = A.bake(rig, a)
        events[a.name] = dict(a.events, length=a.length, loop=a.loop)
