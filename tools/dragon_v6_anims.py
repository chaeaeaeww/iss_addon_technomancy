"""
Tech Dragon 1.8: the kiting moves and the crash landing.

- backstep: a wing-beat leap straight back (the entity flies the arc) to open distance;
- wing_push: two forward wing beats that blow the target away;
- spit: the neck coils back while the core and crest charge, then lunges and spits a lightning bolt (Ice and Fire's
  lightning dragons and Elden Ring's Lansseax were the reference for the idea, nothing is copied);
- crash_land: every landing from the air in a fight (after a chase, the storm, the dive chain, Skyfall, the pylons):
  the dragon comes down in a dive (the "dive" loop), hits the ground chest first with the wings flung up by the
  impact, slams them down and roars while the shock rings spread (the effects are the server's).

The kiting side-hops reuse dodge_left / dodge_right.
"""
import anim_v4 as A
from anim_v4 import Anim
from dragon_v4_anims import DISPLAY, LEGS, NECK, STAND, TAIL, add, merge, path, plant_all, smooth_window, tail_sway
from dragon_v4_anims2 import LEGS_REACH, LOW_SPREAD, UP_V, WIDE, glow_pulse, jitter, rear
from dragon_v5_anims import window

# wing beats (left side; merge() mirrors them): the left wing points +x, so +y swings it forward, -z raises it
BEAT_UP = {"wing_l": [8, -24, -52], "wing_l2": [0, -10, 14], "wing_l3": [0, 12, 18], "finger_l2": [0, -2, 0], "finger_l3": [0, -4, 0]}
BEAT_DOWN_FWD = {"wing_l": [-6, 30, 30], "wing_l2": [0, 14, -10], "wing_l3": [0, -8, -12], "finger_l2": [0, 3, 0], "finger_l3": [0, 6, 0]}
PUSH = {"wing_l": [-6, 50, 4], "wing_l2": [0, 24, -6], "wing_l3": [0, -12, -8], "finger_l2": [0, 4, 0], "finger_l3": [0, 8, 0]}
FLUNG = {"wing_l": [4, 10, -50], "wing_l2": [0, -12, 16], "wing_l3": [0, 16, 20], "finger_l2": [0, -2, 0], "finger_l3": [0, -4, 0]}
SLAMMED = {"wing_l": [0, -10, 12], "wing_l2": [0, 14, -6], "wing_l3": [0, -14, -2], "finger_l2": [0, 2, 0], "finger_l3": [0, 4, 0]}


def backstep():
    """Crouch with the wings raised, one big forward downbeat that throws it backwards (leap 0.3 s), a second beat in
    the air, forefeet reaching, land (0.85 s) facing the target the whole time."""
    a = Anim("backstep", 1.25, False)
    crouch = add(STAND, {"body@pos": [0, -4.0, 2.0], "chest": [5, 0, 0], "hips": [-2, 0, 0], "neck1": [10, 0, 0], "neck2": [4, 0, 0],
                         "head": [-8, 0, 0], "jaw": [10, 0, 0], "tail1": [8, 0, 0], "tail2": [4, 0, 0]})
    launch = add(STAND, merge(rear(-16, 2.0), {"neck1": [-8, 0, 0], "neck2": [-4, 0, 0], "neck3": [6, 0, 0], "head": [10, 0, 0], "jaw": [28, 0, 0]}))
    air = add(STAND, merge(rear(-12, 3.0), {"neck1": [-4, 0, 0], "neck3": [4, 0, 0], "head": [8, 0, 0], "jaw": [16, 0, 0],
                                            "tail1": [10, 0, 0], "tail2": [6, 0, 0]}))
    land = add(STAND, {"body@pos": [0, -3.5, -1.0], "chest": [6, 0, 0], "neck1": [10, 0, 0], "neck2": [4, 0, 0], "head": [-6, 0, 0], "jaw": [8, 0, 0]})
    a.seq([(0.0, STAND, "smooth"),
           (0.18, merge(crouch, BEAT_UP), "out2"),
           (0.32, merge(launch, BEAT_DOWN_FWD, LEGS_REACH), "in2"),
           (0.52, merge(air, BEAT_UP, LEGS_REACH), "smooth"),
           (0.68, merge(air, BEAT_DOWN_FWD, LEGS_REACH), "in2"),
           (0.86, merge(land, LOW_SPREAD), "in"),
           (1.25, STAND, "smooth")])
    a.lag(NECK, 0.03).lag(TAIL, 0.06)
    a.lag(["wing_l", "wing_l2", "wing_l3"], 0.03).lag(["wing_r", "wing_r2", "wing_r3"], 0.03)
    w = window(0.3, 0.38, 0.8, 0.88)
    for leg in LEGS:
        a.plant(leg, weight=w)
    a.events = {"leap": 0.3, "land": 0.86}
    return a


def wing_push():
    """Rears a little with the wings raised and swept back, then two beats forward at the target (0.6 s and 1.05 s):
    the wind blows it away."""
    a = Anim("wing_push", 1.6, False)
    up = add(STAND, merge(rear(-10, 1.0), {"neck1": [-6, 0, 0], "neck3": [6, 0, 0], "head": [-10, 0, 0], "jaw": [30, 0, 0],
                                           "crest@scale": [1.1, 1.1, 1.1]}))
    hit = add(STAND, {"body@pos": [0, -1.0, -1.5], "chest": [6, 0, 0], "neck1": [8, 0, 0], "neck2": [4, 0, 0], "head": [-8, 0, 0], "jaw": [22, 0, 0]})
    a.seq([(0.0, STAND, "smooth"),
           (0.36, merge(up, BEAT_UP, {"wing_l": [8, -34, -56]}), "out2"),
           (0.6, merge(hit, PUSH), "in"),
           (0.82, merge(up, BEAT_UP), "out2"),
           (1.05, merge(hit, PUSH, {"wing_l": [-4, 44, 10]}), "in"),
           (1.3, merge(add(STAND, {"body@pos": [0, -1.5, 0], "chest": [3, 0, 0], "neck1": [4, 0, 0]}), LOW_SPREAD), "out2"),
           (1.6, STAND, "smooth")])
    a.lag(["wing_l", "wing_l2", "wing_l3"], 0.03).lag(["wing_r", "wing_r2", "wing_r3"], 0.03).lag(NECK, 0.05).lag(TAIL, 0.07)
    a.layer(tail_sway(1.6, 2.5, 0.5))
    a.events = {"push": 0.6, "push2": 1.05}
    return plant_all(a)


def spit():
    """Lightning spit: neck coiled back and up while the core and crest charge (0.1-0.55 s), then a lunge with the jaws
    wide (spit 0.6 s), wings half open."""
    a = Anim("spit", 1.3, False)
    coil = add(STAND, {"body@pos": [0, 1.0, 1.5], "chest": [-6, 0, 0], "neck1": [-20, 0, 0], "neck2": [-12, 0, 0], "neck3": [8, 0, 0],
                       "neck4": [16, 0, 0], "head": [18, 0, 0], "jaw": [12, 0, 0], "crest@scale": [1.15, 1.15, 1.15], "core@scale": [1.3, 1.3, 1.3]})
    lunge = add(STAND, {"body@pos": [0, -1.5, -2.5], "chest": [6, 0, 0], "neck1": [12, 0, 0], "neck2": [10, 0, 0], "neck4": [-8, 0, 0],
                        "head": [-14, 0, 0], "jaw": [42, 0, 0], "crest@scale": [1.1, 1.1, 1.1]})
    a.seq([(0.0, STAND, "smooth"),
           (0.45, merge(coil, DISPLAY), "out2"),
           (0.55, merge(coil, DISPLAY, {"jaw": [20, 0, 0]}), "smooth"),
           (0.62, merge(lunge, WIDE), "in"),
           (0.8, merge(lunge, WIDE, {"jaw": [36, 0, 0]}), "smooth"),
           (1.3, STAND, "smooth")])
    a.lag(NECK, 0.03).lag(TAIL, 0.06)
    a.lag(["wing_l", "wing_l2", "wing_l3"], 0.03).lag(["wing_r", "wing_r2", "wing_r3"], 0.03)
    a.layer(jitter(0.8, ("head", "neck3"), 0.15, 0.55)).layer(glow_pulse(0.12, 1.15, 1.45, 0.1, 0.62))
    a.layer(tail_sway(1.3, 2.0, 0.5))
    a.events = {"charge": 0.1, "spit": 0.6}
    return plant_all(a)


def crash_land():
    """Impact from a dive (0.0 s): chest down, forefeet braced wide, the wings flung up by the blow then slammed down
    (0.18 s), then a roar with the head thrown up (0.55-1.1 s) while the shock rings spread."""
    a = Anim("crash_land", 1.6, False)
    impact = add(STAND, {"body@pos": [0, -7.0, -1.0], "chest": [10, 0, 0], "hips": [-2, 0, 0], "neck1": [10, 0, 0], "neck2": [6, 0, 0],
                         "head": [-22, 0, 0], "jaw": [24, 0, 0], "tail1": [8, 0, 0], "tail2": [4, 0, 0]})
    roar = add(STAND, {"body@pos": [0, -1.0, 0.5], "chest": [-8, 0, 0], "neck1": [-16, 0, 0], "neck2": [-8, 0, 0], "neck3": [6, 0, 0],
                       "head": [-20, 0, 0], "jaw": [44, 0, 0], "crest@scale": [1.15, 1.15, 1.15], "core@scale": [1.25, 1.25, 1.25]})
    a.seq([(0.0, merge(impact, FLUNG), "smooth"),
           (0.18, merge(impact, SLAMMED), "in"),
           (0.4, merge(impact, LOW_SPREAD, {"body@pos": [0, -5.0, -0.5], "wing_l": [0, -14, 20]}), "smooth"),
           (0.62, merge(roar, DISPLAY), "out2"),
           (1.1, merge(roar, DISPLAY, {"jaw": [40, 0, 0]}), "smooth"),
           (1.6, STAND, "smooth")])
    a.lag(NECK, 0.04).lag(TAIL, 0.07)
    a.lag(["wing_l", "wing_l2", "wing_l3"], 0.025).lag(["wing_r", "wing_r2", "wing_r3"], 0.025)
    a.layer(jitter(1.0, ("head", "neck3"), 0.6, 1.1)).layer(glow_pulse(0.2, 1.1, 1.4, 0.0, 1.2))
    brace = path([(0.0, (3.0, 0.0, -5.0), "smooth"), (0.5, (3.0, 0.0, -5.0), "smooth"), (1.4, (0, 0, 0), "smooth")])
    a.plant("fl", brace)
    a.plant("fr", lambda t: (-brace(t)[0], brace(t)[1], brace(t)[2]))
    a.plant("hl", lambda t: (2.0 * (1 - smooth_window(t, 0.5, 1.4, 9, 10)), 0.0, 2.0 * (1 - smooth_window(t, 0.5, 1.4, 9, 10))))
    a.plant("hr", lambda t: (-2.0 * (1 - smooth_window(t, 0.5, 1.4, 9, 10)), 0.0, 2.0 * (1 - smooth_window(t, 0.5, 1.4, 9, 10))))
    a.events = {"impact": 0.0, "roar": 0.55}
    return a


ANIMS6 = [backstep, wing_push, spit, crash_land]


def add_to(anims, events, rig):
    for fn in ANIMS6:
        a = fn()
        anims[a.name] = A.bake(rig, a)
        events[a.name] = dict(a.events, length=a.length, loop=a.loop)
