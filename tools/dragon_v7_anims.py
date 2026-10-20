"""
Tech Dragon 1.9: EMP stun, the pin-and-gnaw, carrying prey into the sky, and the hextech core beam (charge, the beam
itself, the overload that follows).

- emp_stunned: the EMP hits like a seizure - a jolt (head thrown back, wings flung), a collapse onto the belly, then
  electric spasms (twitches in bursts, not a steady shake) and a groggy head shake getting up;
- pin_gnaw: the left forefoot slams down on the prey (0.4 s) and holds it while the head drops to it and gnaws four
  times, worrying side to side, then a kick sends it away (2.8 s); the server keeps the prey under that forefoot;
- carry: flying with the prey clamped in the jaws, head low, hard wingbeats (loop);
- core_charge: rears, chest thrust out, wings wide, the chest core swelling and flickering (1.5 s);
- core_beam: braced, chest aimed, head thrown back roaring, the core blazing (loop) - the beam is drawn by the client;
- overload: slumps forward spent, wings collapsing, head down, the glow gone (the drained texture), slow heaves, up.
"""
import math

import anim_v4 as A
from anim_v4 import Anim, wave
from dragon_v4_anims import DISPLAY, DRAPE, LEGS, NECK, STAND, TAIL, add, breathe, merge, path, plant_all, rest_pose, smooth_window, tail_sway
from dragon_v4_anims2 import (AIR, LEGS_HANG, LOW_SPREAD, UP_V, WIDE, flap_layer, glow_pulse, jitter, rear, tail_wave_air)


def spasms(start, end, strength=1.0):
    """Electric seizure: short violent bursts every ~0.45 s with a weak tremor in between."""
    def fn(t):
        if not start <= t <= end:
            return {}
        k = (1.0 if (t % 0.45) < 0.1 else 0.22) * strength
        return {"head": [k * 7 * math.sin(t * 57), k * 6 * math.sin(t * 43), 0], "neck3": [k * 4 * math.sin(t * 49), 0, 0],
                "wing_l2": [0, 0, k * 9 * math.sin(t * 66)], "wing_l3": [0, k * 6 * math.sin(t * 51), k * 10 * math.sin(t * 71)],
                "claws_l": [k * 26 * math.sin(t * 40), 0, 0], "foot_l": [k * 14 * math.sin(t * 35), 0, 0],
                "tail6": [0, k * 9 * math.sin(t * 37), 0], "tail8": [0, k * 14 * math.sin(t * 29), 0], "jaw": [abs(k * 10 * math.sin(t * 61)), 0, 0],
                "body@pos": [0, k * 0.6 * math.sin(t * 64), 0]}
    return fn


def emp_stunned():
    a = Anim("emp_stunned", 3.0, False)
    jolt = merge(add(STAND, merge(rear(-10, 1.5), {"neck1": [-12, 0, 0], "neck3": [10, 0, 0], "head": [-28, 0, 0], "jaw": [40, 0, 0],
                                                   "tail2": [4, 0, 0], "crest@scale": [1.2, 1.2, 1.2]})), UP_V)
    down = merge(rest_pose(), {"wing_l": [0, -14, 6], "wing_l2": [0, 12, -2], "wing_l3": [0, -12, 0], "finger_l2": [0, 2, 0], "finger_l3": [0, 4, 0]}, {"body@pos": [0, -12.0, 0], "body": [0, 0, 5], "neck1": [-2, -4, 0], "neck2": [-2, -6, 4], "neck3": [0, -6, 4],
                                      "neck4": [2, -4, 6], "head": [4, -4, 14], "jaw": [12, 0, 0], "lid_l@pos": [0, -1.8, 0],
                                      "tail1": [-14, 4, 0], "tail2": [4, 6, 0], "tail3": [4, 4, 0], "core@scale": [0.8, 0.8, 0.8]})
    groggy = add(STAND, {"body@pos": [0, -3.0, 0], "chest": [6, 0, 0], "neck1": [10, 0, 0], "neck2": [4, 0, 0], "head": [4, 8, 0], "jaw": [8, 0, 0]})
    a.seq([(0.0, STAND, "smooth"), (0.12, jolt, "out"), (0.42, down, "in2"), (2.45, down, "smooth"),
           (2.75, merge(groggy, LOW_SPREAD), "out2"), (3.0, STAND, "smooth")])
    a.lag(NECK, 0.04).lag(TAIL, 0.07)
    a.layer(spasms(0.45, 2.45)).layer(breathe(1.1, 1.0))
    a.layer(lambda t: {"head": [0, 12 * smooth_window(t, 2.45, 2.55, 2.8, 2.95) * math.sin(t * 30), 0]})
    w = lambda t: 1.0 - smooth_window(t, 0.05, 0.12, 0.3, 0.42)
    a.plant("fl", lambda t: (5.0 * smooth_window(t, 0.3, 0.45, 2.45, 2.8), 0.0, -10.0 * smooth_window(t, 0.3, 0.45, 2.45, 2.8)), weight=w)
    a.plant("fr", lambda t: (-5.0 * smooth_window(t, 0.3, 0.45, 2.45, 2.8), 0.0, -8.0 * smooth_window(t, 0.3, 0.45, 2.45, 2.8)), weight=w)
    a.plant("hl", lambda t: (6.0 * smooth_window(t, 0.3, 0.45, 2.45, 2.8), 0.0, 4.0 * smooth_window(t, 0.3, 0.45, 2.45, 2.8)))
    a.plant("hr", lambda t: (-6.0 * smooth_window(t, 0.3, 0.45, 2.45, 2.8), 0.0, 3.0 * smooth_window(t, 0.3, 0.45, 2.45, 2.8)))
    a.events = {"jolt": 0.1, "collapse": 0.42, "up": 2.45}
    return a


GNAW_BITES = (0.85, 1.3, 1.75, 2.2)


def pin_gnaw():
    a = Anim("pin_gnaw", 3.2, False)
    lift = add(STAND, {"body@pos": [0, 1.0, 0.5], "chest": [-6, -6, 3], "neck1": [-4, -6, 0], "head": [-6, 0, 0], "jaw": [16, 0, 0]})
    pin = add(STAND, {"body@pos": [0, -3.0, -2.0], "chest": [7, 4, -2], "neck1": [10, 6, 0], "neck2": [8, 4, 0], "neck3": [6, 2, 0],
                      "neck4": [6, 0, 0], "head": [10, 4, 0], "jaw": [10, 0, 0]})
    keys = [(0.0, STAND, "smooth"), (0.28, merge(lift, LOW_SPREAD), "out2"), (0.42, merge(pin, LOW_SPREAD), "in")]  # noqa
    for k, t0 in enumerate(GNAW_BITES):
        side = 12 if k % 2 == 0 else -12
        keys.append((t0 - 0.16, merge(pin, LOW_SPREAD, {"head": [2, 4 + side, 0], "neck4": [2, side * 0.4, 0], "jaw": [38, 0, 0]}), "out2"))
        keys.append((t0, merge(pin, LOW_SPREAD, {"head": [10, 4 - side * 0.5, side * 0.6], "neck4": [6, 0, 0], "jaw": [-2, 0, 0]}), "snap"))
    keys += [(2.55, merge(add(STAND, {"body@pos": [0, -1.5, -1], "chest": [3, 0, 0], "neck1": [-6, 0, 0], "head": [-16, 0, 0], "jaw": [30, 0, 0]}),
                          DISPLAY), "out2"),
             (2.8, merge(add(STAND, {"body@pos": [0, -1.0, 0], "chest": [-4, -10, 4], "neck1": [2, 0, 0], "head": [-4, -8, 0]}), LOW_SPREAD), "in"),
             (3.2, STAND, "smooth")]
    a.seq(keys)
    a.lag(NECK, 0.02).lag(TAIL, 0.06)
    a.layer(tail_sway(1.6, 3.0, 0.6))
    paw = path([(0.0, (0, 0, 0), "smooth"), (0.28, (2, 14, -12), "out2"), (0.42, (1, 0, -20), "in"), (2.6, (1, 0, -20), "smooth"),
                (2.8, (-6, 6, -26), "in"), (3.1, (0, 0, 0), "smooth")])
    a.plant("fl", paw, foot=path([(0.0, 0, "smooth"), (0.3, -50, "out2"), (0.42, 20, "in"), (2.6, 20, "smooth"), (3.0, 0, "smooth")]))
    for leg in ("fr", "hl", "hr"):
        a.plant(leg)
    a.layer(lambda t: {"claws_l!": [path([(0.0, 0, "smooth"), (0.3, -35, "out2"), (0.42, 40, "in"), (2.6, 40, "smooth"), (2.9, 0, "smooth")])(t), 0, 0]})
    a.events = {"pin": 0.42, "bites": list(GNAW_BITES), "kick": 2.8}
    return a


def carry():
    L = 1.0
    a = Anim("carry", L, True)
    pose = merge(AIR, LEGS_HANG, {"body": [-20, 0, 0], "neck1": [14, 0, 0], "neck2": [10, 0, 0], "neck3": [6, 0, 0], "neck4": [4, 0, 0],
                                  "head": [10, 0, 0], "jaw": [8, 0, 0], "tail1": [8, 0, 0], "tail2": [4, 0, 0]})
    a.key(0, pose).key(L, pose)
    a.layer(flap_layer(L, 58, 1.0, 2.6)).layer(tail_wave_air(L, 2.5))
    a.layer(lambda t: {"head": [0, 8 * math.sin(2 * math.pi * t / (L / 2)), 0], "neck4": [0, 4 * math.sin(2 * math.pi * t / (L / 2) - 0.6), 0]})
    a.lag(NECK, 0.04)
    return a


CHARGE_POSE = merge(rear(-20, 1.5), {"chest": [-8, 0, 0], "neck1": [-14, 0, 0], "neck2": [-6, 0, 0], "neck3": [8, 0, 0], "head": [-24, 0, 0],
                                     "jaw": [26, 0, 0], "tail2": [6, 0, 0], "tail3": [4, 0, 0], "crest@scale": [1.2, 1.2, 1.2], "ribs@scale": [1.06, 1.04, 1.0]})


def core_charge():
    a = Anim("core_charge", 1.5, False)
    a.seq([(0.0, STAND, "smooth"),
           (0.35, merge(add(STAND, {"body@pos": [0, -2.5, 1.5], "chest": [6, 0, 0], "neck1": [12, 0, 0], "head": [-8, 0, 0]}), LOW_SPREAD), "out2"),
           (1.1, merge(add(STAND, CHARGE_POSE), DISPLAY), "out2"),
           (1.5, merge(add(STAND, CHARGE_POSE), WIDE, {"chest": [-12, 0, 0]}), "smooth")])
    a.lag(NECK, 0.04).lag(TAIL, 0.07)
    a.layer(lambda t: {"core@scale": [1.0 + 0.8 * smooth_window(t, 0.2, 1.3, 9, 10)] * 3})
    a.layer(glow_pulse(0.1, 1.0, 1.15, 0.6, 1.5)).layer(jitter(1.2, ("chest", "neck3", "head", "wing_l3"), 0.7, 1.5))
    front = lambda t: 1.0 - smooth_window(t, 0.7, 1.0, 9, 10)
    a.plant("fl", weight=front)
    a.plant("fr", weight=front)
    a.plant("hl")
    a.plant("hr")
    a.events = {"charge": 0.1}
    return a


def core_beam():
    L = 0.8
    a = Anim("core_beam", L, True)
    pose = merge(add(STAND, CHARGE_POSE), WIDE, {"chest": [-12, 0, 0], "head": [-30, 0, 0], "jaw": [40, 0, 0], "core@scale": [1.9, 1.9, 1.9]})
    a.key(0, pose).key(L, pose)
    a.layer(jitter(1.6, ("chest", "ribs", "neck2", "head", "wing_l2", "wing_l3")))
    a.layer(lambda t: {"core@scale": [1.9 + 0.25 * math.sin(2 * math.pi * t / 0.2)] * 3, "body@pos": [0, 0.4 * math.sin(2 * math.pi * t / 0.1), 0]})
    a.layer(tail_sway(L, 3.0, 0.6))
    a.plant("hl")
    a.plant("hr")
    a.plant("fl", weight=lambda t: 0.0)
    a.plant("fr", weight=lambda t: 0.0)
    return a


def overload():
    a = Anim("overload", 2.4, False)
    slump = merge(add(STAND, {"body@pos": [0, -6.0, -1.0], "chest": [8, 0, 0], "hips": [-2, 0, 0], "neck1": [8, 0, 0], "neck2": [6, 0, 0],
                              "neck3": [4, 0, 0], "neck4": [2, 0, 0], "head": [2, 0, 6], "tail2": [4, 0, 0], "jaw": [10, 0, 0], "lid_l@pos": [0, -1.4, 0],
                              "tail1": [10, 0, 0], "tail2": [6, 0, 0], "core@scale": [0.7, 0.7, 0.7], "crest@scale": [0.9, 0.9, 0.9]}), DRAPE)
    a.seq([(0.0, merge(add(STAND, CHARGE_POSE), WIDE), "smooth"), (0.45, slump, "in2"), (1.9, slump, "smooth"),
           (2.4, STAND, "smooth")])
    a.lag(NECK, 0.05).lag(TAIL, 0.08)
    a.layer(lambda t: {"ribs@scale": [1 + 0.05 * math.sin(2 * math.pi * t / 0.9) * smooth_window(t, 0.4, 0.6, 1.8, 2.1)] * 2 + [1]})
    a.layer(spasms(0.5, 1.9, 0.35))
    return plant_all(a)


ANIMS7 = [emp_stunned, pin_gnaw, carry, core_charge, core_beam, overload]


def add_to(anims, events, rig):
    for fn in ANIMS7:
        a = fn()
        anims[a.name] = A.bake(rig, a)
        events[a.name] = dict(a.events, length=a.length, loop=a.loop)
