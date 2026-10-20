"""
Tech Dragon v4: every animation besides the first review set (dragon_v4_anims.py). Same tools: key poses, lag,
layers (flapping, breathing, shaking), leg IK and membrane fitting.

Hit frames / events are in each animation's `events` (seconds) and copied into tech_dragon_events.json for reference.
"""
import math

import anim_v4 as A
from anim_v4 import Anim, wave
from dragon_v4_anims import (DISPLAY, DRAPE, FOLD, FOLD_LOOSE, LEGS, LEGS_TUCKED, NECK, NECK_LOW, STAND, TAIL, add, blink,
                             breathe, merge, path, plant_all, rest_legs, rest_pose, smooth_window, tail_sway, wing_pose)

# --------------------------------------------------------------------------------------------- extra poses

SWEPT = wing_pose(dh=(0.80, 0.12, 0.58), df=(0.70, 0.02, 0.70), d1=(0.45, -0.02, 0.89), n_hand=(0.0, 1.0, 0.0), fan=(10, 22))
LOW_SPREAD = {"wing_l": [0, -14, 32], "wing_l2": [0, 12, -12], "wing_l3": [0, -12, -8], "finger_l2": [0, 2, 0], "finger_l3": [0, 4, 0]}
UP_V = {"wing_l": [4, 18, -58], "wing_l2": [0, -12, 12], "wing_l3": [0, 14, 16], "finger_l2": [0, -2, 0], "finger_l3": [0, -4, 0]}
WIDE = {"wing_l": [0, 6, -22], "wing_l2": [0, -4, 4], "wing_l3": [0, 4, 6], "finger_l2": [0, -2, 0], "finger_l3": [0, -3, 0]}
WRAP = wing_pose(dh=(0.30, 0.80, 0.52), df=(-0.30, 0.15, -0.94), d1=(-0.20, -0.25, 0.95), n_hand=(0.15, 1.0, 0.0), fan=(10, 22))
NECK_AIR = {"neck1": [-6, 0, 0], "neck2": [-2, 0, 0], "neck3": [2, 0, 0], "neck4": [3, 0, 0], "head": [5, 0, 0]}
TAIL_AIR = {"tail1": [2, 0, 0], "tail2": [1, 0, 0]}
LEGS_HANG = {"arm_l": [30, 0, -4], "forearm_l": [-40, 0, 0], "hand_l": [30, 0, 0], "claws_l": [20, 0, 0],
             "thigh_l": [24, 0, -3], "shin_l": [10, 0, 0], "meta_l": [12, 0, 0], "foot_l": [30, 0, 0]}
LEGS_REACH = {"arm_l": [-10, 0, -6], "forearm_l": [-10, 0, 0], "hand_l": [-10, 0, 0], "claws_l": [-20, 0, 0],
              "thigh_l": [-12, 0, -4], "shin_l": [8, 0, 0], "meta_l": [-6, 0, 0], "foot_l": [-12, 0, 0]}
LEGS_RAKE = {"arm_l": [-50, 0, -10], "forearm_l": [-20, 0, 0], "hand_l": [-30, 0, 0], "claws_l": [-40, 0, 0],
             "thigh_l": [-35, 0, -6], "shin_l": [-10, 0, 0], "meta_l": [-20, 0, 0], "foot_l": [-40, 0, 0]}
AIR = merge(NECK_AIR, TAIL_AIR, LEGS_TUCKED)


def rear(angle, height=0.0, pivot_z=8.0):
    """Body rotation about the hind hips (rear up / sit) instead of about the body pivot: rotation + compensating
    position for the 'body' bone (pivot z = -10)."""
    a = math.radians(angle)
    d = pivot_z + 10.0
    # rot3([x]) = Rx(-x): a vector (0, 0, d) becomes (0, sin(x) * d, cos(x) * d)
    y = math.sin(a) * d
    z = math.cos(a) * d
    # the tail would swing into the ground: tilt it back up by most of the body angle
    return {"body": [angle, 0, 0], "body@pos": [0, -y + height, d - z], "tail1": [-angle * 0.75, 0, 0], "tail2": [-angle * 0.15, 0, 0]}


def flap_layer(period, amp=40.0, fold=1.0, bob=1.6, phase=0.0, weight=None):
    """Additive wing beat (left side, mirrored): up/down at the shoulder with the forearm and hand lagging, the hand
    folding in on the upstroke; the body bobs against the beat."""
    def fn(t):
        w = weight(t) if weight else 1.0
        if w <= 0:
            return {}
        th = 2 * math.pi * t / period + math.radians(phase)
        s = math.sin(th)
        up = max(0.0, math.cos(th)) * fold
        return {"wing_l": [6 * math.cos(th) * w, 4 * up * w, -amp * s * w],
                "wing_l2": [0, 22 * up * w, -amp * 0.25 * math.sin(th - math.radians(25)) * w],
                "wing_l3": [0, -30 * up * w, -amp * 0.4 * math.sin(th - math.radians(50)) * w],
                "finger_l2": [0, 10 * up * w, 0], "finger_l3": [0, 18 * up * w, 0],
                "body@pos": [0, bob * math.sin(th - math.radians(160)) * w, 0]}
    return fn


def tail_wave_air(period, amp=2.0):
    return lambda t: {TAIL[k]: [wave(t, period, amp + 0.4 * k, -100 - k * 40), wave(t, 2 * period, 2 + 0.3 * k, -k * 35), 0] for k in range(8)}


def gait(a, L, stride, duty, phases, lift=4.0, hind_lift=3.4, toe=28.0):
    for leg in LEGS:
        lf = lift if leg[0] == "f" else hind_lift

        def off(t, leg=leg, lf=lf):
            ph = (t / L + phases[leg]) % 1.0
            if ph < duty:
                return (0.0, 0.0, -stride / 2 + stride * ph / duty)
            u = (ph - duty) / (1 - duty)
            return (0.0, lf * math.sin(math.pi * u), stride / 2 - stride * A.ease("smooth", u))

        def pitch(t, leg=leg):
            ph = (t / L + phases[leg]) % 1.0
            return 0.0 if ph < duty else toe * math.sin(math.pi * (ph - duty) / (1 - duty))
        a.plant(leg, off, foot=pitch)


def jitter(amount, bones=("neck2", "head", "body"), start=0.0, end=1e9):
    def fn(t):
        if not start <= t <= end:
            return {}
        out = {}
        for k, b in enumerate(bones):
            out[b] = [amount * math.sin(t * 61 + k * 1.7) * math.sin(t * 13 + k), amount * 0.8 * math.sin(t * 47 + k * 2.3), 0]
        return out
    return fn


def glow_pulse(period, lo=1.0, hi=1.3, start=0.0, end=1e9):
    def fn(t):
        if not start <= t <= end:
            return {}
        k = lo + (hi - lo) * (0.5 + 0.5 * math.sin(2 * math.pi * t / period))
        return {"core@scale": [k, k, k], "crest@scale": [1 + (k - 1) * 0.5] * 3}
    return fn


# --------------------------------------------------------------------------------------------- ground: idle family

def sit():
    a = Anim("sit", 6.0, True)
    pose = merge(STAND, rear(-24, -11), {"hips": [16, 0, 0], "neck1": [-14, 0, 0], "neck2": [-6, 0, 0], "neck3": [8, 0, 0], "neck4": [12, 0, 0],
                                         "head": [20, 0, 0], "tail1": [6, 14, 0], "tail2": [-3, 16, 0], "tail3": [-3, 18, 0], "tail4": [-1, 20, 0],
                                         "tail5": [0, 20, 0], "tail6": [0, 18, 0], "tail7": [0, 16, 0], "tail8": [0, 12, 0]})
    look = [(0.0, {}), (1.5, {"neck4": [0, -10, 0], "head": [-3, -18, 0]}), (2.6, {"neck4": [0, -10, 0], "head": [-3, -18, 0]}), (3.4, {}),
            (4.6, {"neck4": [0, 8, 0], "head": [4, 15, 5]}), (5.4, {"neck4": [0, 8, 0], "head": [4, 15, 5]}), (6.0, {})]
    for t, p in look:
        a.key(t, add(pose, p), "smooth")
    a.lag(NECK, 0.08)
    a.layer(breathe(3.2)).layer(blink([0.9, 3.9])).layer(tail_sway(6.0, 1.2, 0.3, 30))
    a.plant("fl", lambda t: (0.5, 0.0, -2.0))
    a.plant("fr", lambda t: (-0.5, 0.0, -2.0))
    a.plant("hl", lambda t: (1.5, 0.0, -5.0), foot=lambda t: -12.0)
    a.plant("hr", lambda t: (-1.5, 0.0, -5.0), foot=lambda t: -12.0)
    return a


REST_FL, REST_HL = (1.5, 0.0, -13.0), (2.5, 0.0, 2.0)


def lie_transition(name, length, down=True):
    a = Anim(name, length, "hold" if down else False)
    s, e = (STAND, rest_pose()) if down else (rest_pose(), STAND)
    mid = add(s if down else e, {"body@pos": [0, -4, 0], "neck1": [6, 0, 0], "head": [-4, 0, 0]})
    if down:
        a.seq([(0.0, s, "smooth"), (length * 0.45, mid, "smooth"), (length, e, "smooth")])
    else:
        a.seq([(0.0, s, "smooth"), (length * 0.4, add(s, {"body@pos": [0, 2, 0], "chest": [-6, 0, 0], "neck1": [-6, 0, 0]}), "out2"),
               (length * 0.75, mid, "smooth"), (length, e, "smooth")])
    a.lag(NECK, 0.07).lag(TAIL, 0.09)
    k0, k1 = (0.0, 1.0) if down else (1.0, 0.0)

    def blend(v, t0, t1):
        def fn(t):
            u = A.ease("smooth", max(0.0, min(1.0, (t / length - t0) / (t1 - t0))))
            f = k0 + (k1 - k0) * u
            return tuple(c * f for c in v)
        return fn
    # front legs fold first when lying down (last when getting up), the hind legs follow
    fa, fb = (0.15, 0.75) if down else (0.25, 0.85)
    ha, hb = (0.35, 0.95) if down else (0.05, 0.65)
    a.plant("fl", blend(REST_FL, fa, fb))
    a.plant("fr", blend((-REST_FL[0], 0.0, REST_FL[2]), fa, fb))
    a.plant("hl", blend(REST_HL, ha, hb), foot=lambda t: -30.0 * (blend((1.0,), ha, hb)(t)[0]))
    a.plant("hr", blend((-REST_HL[0], 0.0, REST_HL[2]), ha, hb), foot=lambda t: -30.0 * (blend((1.0,), ha, hb)(t)[0]))
    a.layer(tail_sway(3.0, 1.5, 0.3))
    return a


def sleep_pose():
    return merge(rest_pose(), DRAPE, {
        "body@pos": [0, -13.6, 0], "neck1": [14, 16, 0], "neck2": [6, 18, 0], "neck3": [-2, 16, 0], "neck4": [-6, 12, 0], "head": [-6, 8, 6],
        "tail1": [-14, -12, 0], "tail2": [4, -16, 0], "tail3": [4, -20, 0], "tail4": [3, -22, 0], "tail5": [2, -24, 0], "tail6": [1, -24, 0],
        "tail7": [0, -22, 0], "tail8": [0, -18, 0], "lid_l@pos": [0, -3.2, 0]})


WRAP_LIGHT = wing_pose(dh=(0.62, 0.30, 0.72), df=(0.35, -0.25, -0.90), d1=(0.42, -0.30, 0.86), n_hand=(-0.45, 1.0, 0.0), fan=(10, 22))


def sleep():
    a = Anim("sleep", 8.0, True)
    a.key(0, sleep_pose()).key(8.0, sleep_pose())
    a.layer(breathe(5.0, 1.6)).layer(tail_sway(8.0, 0.8, 0.2, 25))
    a.layer(lambda t: {"wing_l": [0, 0, wave(t, 8.0, 1.2, 30)]})
    rest_legs(a)
    return a


def wake():
    a = Anim("wake", 2.4, False)
    s = sleep_pose()
    lifted = add(rest_pose(), {"neck1": [-12, 0, 0], "neck2": [-6, 0, 0], "head": [-6, 0, 0], "jaw": [24, 0, 0]})
    a.seq([(0.0, s, "smooth"), (0.6, add(rest_pose(), {"lid_l@pos": [0, -1.2, 0]}), "smooth"), (1.1, lifted, "out2"),
           (1.5, add(rest_pose(), {"neck1": [-4, 0, 0]}), "smooth"), (2.4, STAND, "smooth")])
    a.lag(NECK, 0.06).lag(TAIL, 0.09)
    a.layer(lambda t: {"head": [0, smooth_window(t, 1.5, 1.6, 1.8, 1.95) * wave(t, 0.18, 9), smooth_window(t, 1.5, 1.6, 1.8, 1.95) * wave(t, 0.18, 6)]})

    def w(t0, t1):
        return lambda t: 1.0 - A.ease("smooth", max(0.0, min(1.0, (t - t0) / (t1 - t0))))
    a.plant("fl", lambda t: tuple(c * w(1.5, 2.2)(t) for c in REST_FL))
    a.plant("fr", lambda t: tuple(c * w(1.5, 2.2)(t) for c in (-REST_FL[0], 0.0, REST_FL[2])))
    a.plant("hl", lambda t: tuple(c * w(1.7, 2.4)(t) for c in REST_HL), foot=lambda t: -30.0 * w(1.7, 2.4)(t))
    a.plant("hr", lambda t: tuple(c * w(1.7, 2.4)(t) for c in (-REST_HL[0], 0.0, REST_HL[2])), foot=lambda t: -30.0 * w(1.7, 2.4)(t))
    return a


def run():
    L = 0.8
    a = Anim("run", L, True)
    pose = merge(STAND, FOLD_LOOSE, {"neck1": [-6, 0, 0], "neck2": [-2, 0, 0], "neck3": [4, 0, 0], "neck4": [4, 0, 0], "head": [6, 0, 0],
                                     "tail1": [-4, 0, 0], "tail2": [-2, 0, 0], "tail3": [0, 0, 0]})
    a.key(0, pose).key(L, pose)
    gait(a, L, 34.0, 0.42, {"hl": 0.0, "hr": 0.08, "fl": 0.5, "fr": 0.58}, lift=7.0, hind_lift=6.0, toe=40.0)
    a.layer(lambda t: {"body@pos": [0, 1.4 * math.sin(4 * math.pi * t / L - 1.0), 0], "body": [wave(t, L, 4.0, 90), 0, 0],
                       "chest": [wave(t, L, -5.0, 60), 0, 0], "hips": [wave(t, L, 5.0, 60), 0, 0],
                       "neck1": [wave(t, L, 4.0, 150), 0, 0], "head": [wave(t, L, -5.0, 180), 0, 0],
                       "wing_l": [0, 0, wave(t, L, 3.0, 30)]})
    a.layer(tail_sway(L, 2.0, 0.5, 40, 180))
    a.lag(TAIL, 0.05)
    return a


# --------------------------------------------------------------------------------------------- ground attacks

def bite_sweep():
    """Head swings across low with the jaw open: hits a wide arc in front (hit 0.55 s)."""
    a = Anim("bite_sweep", 1.15, False)
    a.seq([(0.0, STAND, "smooth"),
           (0.35, add(STAND, {"body@pos": [0, 0.5, 1], "chest": [-2, -10, 0], "neck1": [4, -22, 0], "neck2": [2, -16, 0], "neck3": [0, -10, 0],
                              "head": [-4, -14, -10], "jaw": [30, 0, 0]}), "out2"),
           (0.55, add(STAND, {"body@pos": [0, -0.8, -2.5], "chest": [5, 6, 0], "neck1": [12, 10, 0], "neck2": [8, 12, 0], "neck3": [2, 8, 0],
                              "head": [-4, 10, 8], "jaw": [10, 0, 0]}), "in2"),
           (0.68, add(STAND, {"body@pos": [0, -0.6, -2], "chest": [4, 12, 0], "neck1": [10, 20, 0], "neck2": [6, 16, 0], "neck3": [2, 10, 0],
                              "head": [-2, 12, 10], "jaw": [-2, 0, 0]}), "out2"),
           (1.15, STAND, "smooth")])
    a.lag(NECK, 0.03).lag(TAIL, 0.07)
    a.layer(tail_sway(3.0, 3.0, 0.5))
    a.events = {"hit": 0.55}
    return plant_all(a)


def grab():
    """Lunge and seize something small in the jaws (catch frame 0.5 s); continues into grab_shake."""
    a = Anim("grab", 1.0, "hold")
    hold = add(STAND, {"body@pos": [0, -0.4, -2], "chest": [3, 0, 0], "neck1": [6, 0, 0], "neck2": [4, 0, 0], "neck3": [0, 0, 0],
                       "head": [-6, 0, 0], "jaw": [8, 0, 0]})
    a.seq([(0.0, STAND, "smooth"),
           (0.3, add(STAND, {"body@pos": [0, 1.2, 2.5], "chest": [-5, 0, 0], "neck1": [-10, 0, 0], "neck2": [-6, 0, 0], "head": [-10, 0, 0],
                             "jaw": [20, 0, 0]}), "out2"),
           (0.44, add(STAND, {"body@pos": [0, -1.0, -6], "chest": [6, 0, 0], "neck1": [16, 0, 0], "neck2": [12, 0, 0], "neck3": [4, 0, 0],
                              "head": [-8, 0, 0], "jaw": [46, 0, 0]}), "in2"),
           (0.5, add(STAND, {"body@pos": [0, -1.0, -6], "chest": [6, 0, 0], "neck1": [16, 0, 0], "neck2": [12, 0, 0], "neck3": [4, 0, 0],
                             "head": [-6, 0, 0], "jaw": [6, 0, 0]}), "snap"),
           (1.0, hold, "smooth")])
    a.lag(NECK, 0.02).lag(TAIL, 0.06)
    a.events = {"catch": 0.5}
    return plant_all(a)


GRAB_HOLD = add(STAND, {"body@pos": [0, -0.4, -2], "chest": [3, 0, 0], "neck1": [6, 0, 0], "neck2": [4, 0, 0], "head": [-6, 0, 0], "jaw": [8, 0, 0]})


def grab_shake():
    """Holding the prey, thrash the head side to side (bite pulses at every swing: 0.2 s and 0.6 s of each loop)."""
    L = 0.8
    a = Anim("grab_shake", L, True)
    a.key(0, GRAB_HOLD).key(L, GRAB_HOLD)
    a.layer(lambda t: {"neck1": [wave(t, L / 2, 2.0), wave(t, L, 16), 0], "neck2": [0, wave(t, L, 14, -30), 0],
                       "neck3": [0, wave(t, L, 12, -60), 0], "neck4": [0, wave(t, L, 10, -80), wave(t, L, 6, -80)],
                       "head": [wave(t, L / 2, 4.0, 40), wave(t, L, 16, -100), wave(t, L, 14, -100)],
                       "jaw": [wave(t, L / 2, 3.0), 0, 0], "chest": [0, wave(t, L, 5, 20), wave(t, L, 3, 20)],
                       "body@pos": [wave(t, L, 0.8, 20), 0, 0]})
    a.layer(tail_sway(L, 4.0, 0.8, 40, 200))
    a.events = {"pulse": [0.2, 0.6]}
    return plant_all(a)


def grab_toss():
    """Whip the head to the side and let go (release 0.42 s)."""
    a = Anim("grab_toss", 1.0, False)
    a.seq([(0.0, GRAB_HOLD, "smooth"),
           (0.28, add(STAND, {"chest": [-2, 10, 0], "neck1": [0, 22, 0], "neck2": [-4, 16, 0], "neck3": [-4, 10, 0], "head": [-6, 14, 10],
                              "jaw": [8, 0, 0]}), "out2"),
           (0.42, add(STAND, {"chest": [-6, -12, 0], "neck1": [-14, -24, 0], "neck2": [-10, -16, 0], "neck3": [-4, -10, 0], "head": [-16, -14, -12],
                              "jaw": [38, 0, 0]}), "in"),
           (0.6, add(STAND, {"chest": [-4, -8, 0], "neck1": [-10, -16, 0], "neck2": [-6, -10, 0], "head": [-10, -8, -6], "jaw": [12, 0, 0]}), "out2"),
           (1.0, STAND, "smooth")])
    a.lag(NECK, 0.025).lag(TAIL, 0.06)
    a.events = {"release": 0.42}
    return plant_all(a)


def tail_whip():
    """Whip the tail at something behind on the left side (hit 0.55 s)."""
    a = Anim("tail_whip", 1.1, False)
    wind = {"hips": [0, -14, 0], "chest": [0, 6, 0], "neck1": [0, 10, 0], "head": [0, 14, 0],
            **{TAIL[k]: [2, -6 - k * 1.5, 0] for k in range(8)}}
    lash = {"hips": [0, 18, 0], "chest": [0, -8, 0], "neck1": [0, -14, 0], "neck3": [0, -10, 0], "head": [0, -16, 0], "jaw": [10, 0, 0],
            **{TAIL[k]: [4, 9 + k * 2.6, 0] for k in range(8)}}
    a.seq([(0.0, STAND, "smooth"), (0.35, add(STAND, wind), "out2"), (0.6, add(STAND, lash), "in2"),
           (0.75, add(STAND, merge(lash, {"hips": [0, 14, 0]})), "out2"), (1.1, STAND, "smooth")])
    a.lag(TAIL, 0.035).lag(NECK, 0.05)
    a.events = {"hit": 0.55}
    return plant_all(a)


def tail_sweep():
    """Surrounded: the tail sweeps a huge arc around one side and back across the other (hits 0.5 s and 1.0 s)."""
    a = Anim("tail_sweep", 1.6, False)
    left = {"hips": [0, 20, 0], "chest": [0, -10, 0], "body": [0, 6, 0], "neck1": [0, -12, 0], "head": [0, -12, 0],
            **{TAIL[k]: [4, 10 + k * 2.5, 0] for k in range(8)}}
    right = {"hips": [0, -20, 0], "chest": [0, 10, 0], "body": [0, -6, 0], "neck1": [0, 12, 0], "head": [0, 12, 0],
             **{TAIL[k]: [4, -10 - k * 2.5, 0] for k in range(8)}}
    a.seq([(0.0, STAND, "smooth"), (0.25, add(STAND, {"body@pos": [0, -1.5, 0], **{TAIL[k]: [2, -4 - k, 0] for k in range(8)}}), "out2"),
           (0.55, add(STAND, left), "in2"), (1.0, add(STAND, right), "smooth"), (1.6, STAND, "smooth")])
    a.lag(TAIL, 0.04).lag(NECK, 0.05)
    a.events = {"hits": [0.5, 1.0]}
    return plant_all(a)


def stomp():
    """Rear up onto the hind legs, forefeet clawing the air, then slam them down (impact 1.0 s): shock wave."""
    a = Anim("stomp", 1.8, False)
    up = merge(rear(-32, 1.0), {"hips": [6, 0, 0], "neck1": [-2, 0, 0], "neck2": [2, 0, 0], "neck3": [6, 0, 0], "head": [-10, 0, 0], "jaw": [34, 0, 0],
                                "crest@scale": [1.12, 1.12, 1.12]})
    a.seq([(0.0, STAND, "smooth"),
           (0.25, add(STAND, {"body@pos": [0, -2, 1], "chest": [4, 0, 0], "neck1": [6, 0, 0]}), "smooth"),
           (0.7, merge(add(STAND, up), WIDE), "out2"),
           (0.85, merge(add(STAND, up), WIDE, {"body": [-34, 0, 0]}), "smooth"),
           (1.0, merge(add(STAND, {"body@pos": [0, -3.5, -2], "chest": [6, 0, 0], "neck1": [18, 0, 0], "neck2": [8, 0, 0], "head": [-12, 0, 0],
                                   "jaw": [30, 0, 0]}), LOW_SPREAD), "in"),
           (1.25, merge(add(STAND, {"body@pos": [0, -2.2, -1], "chest": [3, 0, 0], "neck1": [10, 0, 0], "head": [-6, 0, 0], "jaw": [14, 0, 0]}), LOW_SPREAD), "out2"),
           (1.8, STAND, "smooth")])
    a.lag(NECK, 0.04).lag(TAIL, 0.07)
    front_w = lambda t: 1.0 - smooth_window(t, 0.3, 0.55, 0.88, 1.0)
    paw = path([(0.0, (0, 0, 0), "smooth"), (0.35, (0, 6, -2), "out2"), (0.7, (2, 26, -14), "out2"), (0.88, (2, 22, -18), "smooth"),
                (1.0, (1.5, 0, -8), "in"), (1.6, (0, 0, 0), "smooth")])
    a.plant("fl", paw, weight=lambda t: 1.0, foot=path([(0.0, 0, "smooth"), (0.7, -60, "out2"), (1.0, 0, "in")]))
    a.plant("fr", lambda t: (-paw(t)[0], paw(t)[1], paw(t)[2] - 2 * smooth_window(t, 0.6, 0.75, 0.85, 0.95)),
            foot=path([(0.0, 0, "smooth"), (0.75, -60, "out2"), (1.0, 0, "in")]))
    a.plant("hl")
    a.plant("hr")
    a.layer(lambda t: {"claws_l": [-30 * smooth_window(t, 0.4, 0.6, 0.85, 1.0), 0, 0]})
    a.events = {"roar": 0.55, "impact": 1.0}
    return a


def wing_gust():
    """Wings thrown wide and high with a roar, then one huge downbeat that blasts everything away (1.05 s)."""
    a = Anim("wing_gust", 1.9, False)
    a.seq([(0.0, STAND, "smooth"),
           (0.55, merge(add(STAND, {"body@pos": [0, 1.0, 1.0], "chest": [-10, 0, 0], "neck1": [-8, 0, 0], "head": [-14, 0, 0], "jaw": [36, 0, 0]}), UP_V), "out2"),
           (0.9, merge(add(STAND, {"body@pos": [0, 1.4, 1.2], "chest": [-12, 0, 0], "neck1": [-10, 0, 0], "head": [-12, 0, 0], "jaw": [30, 0, 0]}),
                       {"wing_l": [6, 26, -66], "wing_l2": [0, -14, 14], "wing_l3": [0, 16, 18]}), "smooth"),
           (1.05, merge(add(STAND, {"body@pos": [0, 2.4, -1.0], "chest": [4, 0, 0], "neck1": [8, 0, 0], "head": [2, 0, 0], "jaw": [16, 0, 0]}),
                        {"wing_l": [-8, -30, 22], "wing_l2": [0, 6, -10], "wing_l3": [0, -6, -12]}), "in"),
           (1.3, merge(add(STAND, {"body@pos": [0, 0.5, 0], "neck1": [4, 0, 0]}), LOW_SPREAD), "out2"),
           (1.9, STAND, "smooth")])
    a.lag(["wing_l", "wing_l2", "wing_l3"], 0.03).lag(["wing_r", "wing_r2", "wing_r3"], 0.03).lag(NECK, 0.05).lag(TAIL, 0.07)
    a.layer(tail_sway(2.0, 3.0, 0.6))
    a.events = {"roar": 0.35, "gust": 1.05}
    return plant_all(a)


def field_roar():
    """Head bowed, a roar into the ground with the chest core flaring: the magnetic dome goes up at 0.7 s."""
    a = Anim("field_roar", 2.0, False)
    bow = add(STAND, {"body@pos": [0, -2, 0], "chest": [6, 0, 0], "neck1": [20, 0, 0], "neck2": [10, 0, 0], "neck3": [0, 0, 0], "head": [-18, 0, 0],
                      "jaw": [40, 0, 0], "crest@scale": [1.15, 1.15, 1.15], "core@scale": [1.5, 1.5, 1.5], "ribs@scale": [1.05, 1.04, 1]})
    a.seq([(0.0, STAND, "smooth"), (0.35, add(STAND, {"chest": [-4, 0, 0], "neck1": [-8, 0, 0], "head": [-8, 0, 0], "jaw": [10, 0, 0],
                                                       "ribs@scale": [1.06, 1.05, 1]}), "out2"),
           (0.7, merge(bow, LOW_SPREAD), "in2"), (1.4, merge(bow, LOW_SPREAD, {"jaw": [34, 0, 0]}), "smooth"), (2.0, STAND, "smooth")])
    a.lag(NECK, 0.04).lag(TAIL, 0.08)
    a.layer(jitter(1.5, ("neck3", "head"), 0.7, 1.4)).layer(glow_pulse(0.25, 1.4, 1.6, 0.7, 1.4))
    a.events = {"field": 0.7}
    return plant_all(a)


def rend():
    """Ground Rend charge: low galloping surge, head down, jaws open, claws tearing the ground (loop)."""
    L = 0.7
    a = Anim("rend", L, True)
    pose = merge(STAND, FOLD_LOOSE, {"neck1": [4, 0, 0], "neck2": [4, 0, 0], "neck3": [2, 0, 0], "neck4": [-2, 0, 0], "head": [-8, 0, 0],
                                     "jaw": [26, 0, 0], "body@pos": [0, -2, 0], "chest": [4, 0, 0]})
    a.key(0, pose).key(L, pose)
    gait(a, L, 32.0, 0.42, {"hl": 0.0, "hr": 0.1, "fl": 0.5, "fr": 0.6}, lift=6.0, hind_lift=5.0, toe=35.0)
    a.layer(lambda t: {"body@pos": [0, 1.2 * math.sin(4 * math.pi * t / L - 1.0), 0], "body": [wave(t, L, 3.0, 90), 0, 0],
                       "chest": [wave(t, L, -4.0, 60), 0, 0], "hips": [wave(t, L, 4.0, 60), 0, 0], "head": [wave(t, L / 2, 3.0), wave(t, L, 4.0), 0]})
    a.layer(tail_sway(L, 2.5, 0.5, 40, 180))
    return a


def breath_charge_ground():
    a = Anim("breath_charge_ground", 1.0, "hold")
    a.seq([(0.0, STAND, "smooth"),
           (1.0, add(STAND, {"body@pos": [0, 0.8, 1.5], "chest": [-6, 0, 0], "neck1": [-14, 0, 0], "neck2": [-8, 0, 0], "neck3": [-2, 0, 0],
                             "head": [-12, 0, 0], "jaw": [14, 0, 0], "ribs@scale": [1.07, 1.06, 1], "core@scale": [1.5, 1.5, 1.5],
                             "crest@scale": [1.15, 1.15, 1.15]}), "out2")])
    a.lag(NECK, 0.05)
    a.layer(jitter(0.8, ("head", "neck3"), 0.5, 1.0))
    return plant_all(a)


BREATH_GROUND = add(STAND, {"body@pos": [0, -0.6, -2], "chest": [5, 0, 0], "neck1": [12, 0, 0], "neck2": [8, 0, 0], "neck3": [2, 0, 0], "neck4": [-4, 0, 0],
                            "head": [-14, 0, 0], "jaw": [44, 0, 0], "ribs@scale": [0.98, 0.98, 1], "core@scale": [1.35, 1.35, 1.35]})


def breath_ground():
    L = 1.0
    a = Anim("breath_ground", L, True)
    a.key(0, BREATH_GROUND).key(L, BREATH_GROUND)
    a.layer(jitter(1.2, ("head", "neck4", "jaw"))).layer(glow_pulse(0.2, 1.3, 1.5)).layer(tail_sway(L, 2.0, 0.4))
    return plant_all(a)


def phase_two():
    """Overcharge: rears, wings flung up, roars while lightning surges through the body (EMP burst at 2.6 s)."""
    a = Anim("phase_two", 3.4, False)
    up = merge(rear(-18, 0.5), {"neck1": [-6, 0, 0], "neck2": [-2, 0, 0], "neck3": [10, 0, 0], "head": [-24, 0, 0], "jaw": [44, 0, 0],
                                "crest@scale": [1.25, 1.25, 1.25], "core@scale": [1.7, 1.7, 1.7]})
    a.seq([(0.0, STAND, "smooth"), (0.6, add(STAND, {"body@pos": [0, -2.5, 1], "chest": [6, 0, 0], "neck1": [14, 0, 0], "head": [-6, 0, 0]}), "smooth"),
           (1.1, merge(add(STAND, up), UP_V), "out"), (2.4, merge(add(STAND, up), UP_V, {"head": [-30, 0, 0]}), "smooth"),
           (2.65, merge(add(STAND, {"body@pos": [0, -2.5, -1], "chest": [6, 0, 0], "neck1": [18, 0, 0], "head": [-10, 0, 0], "jaw": [36, 0, 0]}),
                        LOW_SPREAD), "in"),
           (3.4, STAND, "smooth")])
    a.lag(NECK, 0.05).lag(TAIL, 0.08)
    a.layer(jitter(2.0, ("neck2", "neck4", "head", "chest", "wing_l3"), 1.1, 2.4)).layer(glow_pulse(0.15, 1.4, 1.8, 1.0, 2.6))
    a.layer(tail_sway(1.0, 4.0, 0.8))
    front_w = lambda t: 1.0 - smooth_window(t, 0.75, 1.0, 2.45, 2.65)
    a.plant("fl", lambda t: (0.0, 0.0, -4.0 * smooth_window(t, 2.4, 2.65, 3.0, 3.4)), weight=front_w)
    a.plant("fr", lambda t: (0.0, 0.0, -4.0 * smooth_window(t, 2.4, 2.65, 3.0, 3.4)), weight=front_w)
    a.plant("hl")
    a.plant("hr")
    a.events = {"roar": 1.0, "burst": 2.6}
    return a


def pylon_charge():
    """Pylon phase: crouched low behind the shield, wings raised in a V, head up, the chest core drinking power."""
    L = 3.0
    a = Anim("pylon_charge", L, True)
    pose = merge(add(STAND, {"body@pos": [0, -4.5, 0], "chest": [-4, 0, 0], "neck1": [-10, 0, 0], "neck2": [-6, 0, 0], "neck3": [4, 0, 0],
                             "neck4": [0, 0, 0], "head": [-22, 0, 0], "jaw": [16, 0, 0], "crest@scale": [1.2, 1.2, 1.2]}), UP_V)
    a.key(0, pose).key(L, pose)
    a.layer(glow_pulse(0.5, 1.4, 1.9)).layer(jitter(0.9, ("chest", "neck3", "head", "wing_l3")))
    a.layer(lambda t: {"wing_l": [0, 0, wave(t, L, 4.0)], "ribs@scale": [1 + 0.03 * math.sin(2 * math.pi * t / 1.5)] * 2 + [1]})
    a.layer(tail_sway(L, 3.0, 0.5))
    return plant_all(a)


def stunned():
    """EMP stun: collapsed on the belly, legs splayed, head on the ground, twitching, eyes half shut."""
    L = 2.0
    a = Anim("stunned", L, True)
    # 1.9: chin on the ground (the 1.7 pose buried the head ~27 px under it)
    pose = merge(rest_pose(), {"wing_l": [0, -14, 6], "wing_l2": [0, 12, -2], "wing_l3": [0, -12, 0], "finger_l2": [0, 2, 0], "finger_l3": [0, 4, 0]}, {"body@pos": [0, -12.0, 0], "body": [0, 0, 6], "neck1": [-2, -4, 0], "neck2": [-2, -6, 4], "neck3": [0, -6, 4],
                                           "neck4": [2, -4, 6], "head": [4, -4, 14], "jaw": [14, 0, 0], "lid_l@pos": [0, -1.6, 0],
                                           "tail1": [-14, 4, 0], "tail2": [4, 6, 0], "tail3": [4, 4, 0]})
    a.key(0, pose).key(L, pose)

    def twitch(t):
        k = 1.0 if (t % 1.0) < 0.12 else 0.25
        return {"wing_l3": [0, 0, 4 * k * math.sin(t * 70)], "head": [k * 3 * math.sin(t * 53), 0, 0], "claws_l": [k * 20 * math.sin(t * 40), 0, 0],
                "tail8": [0, k * 8 * math.sin(t * 37), 0], "jaw": [k * 4 * math.sin(t * 61), 0, 0]}
    a.layer(twitch).layer(breathe(1.0, 1.0))
    a.plant("fl", lambda t: (5.0, 0.0, -10.0))
    a.plant("fr", lambda t: (-5.0, 0.0, -8.0))
    a.plant("hl", lambda t: (6.0, 0.0, 4.0), foot=lambda t: -40.0)
    a.plant("hr", lambda t: (-6.0, 0.0, 3.0), foot=lambda t: -40.0)
    return a


def death():
    """Staggers, a last weak roar, collapses, then curls up tight (tail around, wings wrapped) for the hextech shell."""
    a = Anim("death", 5.0, "hold")
    curl = merge(FOLD, {"body@pos": [0, -13.6, 0], "chest": [2, 14, 0], "hips": [-1, -14, 0],
                        "neck1": [10, 28, 0], "neck2": [4, 30, 0], "neck3": [-2, 28, 0], "neck4": [-6, 22, 0], "head": [-4, 16, 8], "lid_l@pos": [0, -3.2, 0],
                        "tail1": [-14, -24, 0], "tail2": [4, -28, 0], "tail3": [4, -30, 0], "tail4": [3, -30, 0], "tail5": [2, -30, 0],
                        "tail6": [1, -28, 0], "tail7": [0, -26, 0], "tail8": [0, -22, 0], "core@scale": [1.6, 1.6, 1.6]})
    a.seq([(0.0, STAND, "smooth"),
           (0.5, add(STAND, {"body@pos": [0, -1.5, 0], "body": [0, 0, 8], "neck1": [10, 8, 0], "head": [6, 0, 10], "jaw": [10, 0, 0]}), "smooth"),
           (1.2, merge(add(STAND, {"chest": [-8, 0, 0], "neck1": [-14, 0, 0], "neck2": [-6, 0, 0], "head": [-24, 0, 0], "jaw": [40, 0, 0]}), DISPLAY), "out2"),
           (2.0, merge(add(rest_pose(), {"body": [0, 0, 10], "neck1": [16, -6, 0], "head": [0, 0, 18], "jaw": [20, 0, 0]}), LOW_SPREAD), "in2"),
           (2.3, merge(add(rest_pose(), {"body@pos": [0, 0.8, 0], "body": [0, 0, 6], "neck1": [12, -4, 0], "head": [-2, 0, 12], "jaw": [10, 0, 0]}),
                       LOW_SPREAD), "out2"),
           (4.2, curl, "smooth"), (5.0, curl, "smooth")])
    a.lag(NECK, 0.07).lag(TAIL, 0.1)
    a.layer(jitter(1.5, ("head", "wing_l3", "claws_l"), 2.0, 3.2))

    def legs_w(t):
        return 1.0
    a.plant("fl", path([(0.0, (0, 0, 0), "smooth"), (2.0, REST_FL, "in2"), (4.2, (4.0, 0.0, -10.0), "smooth")]))
    a.plant("fr", path([(0.0, (0, 0, 0), "smooth"), (2.0, (-REST_FL[0], 0, REST_FL[2]), "in2"), (4.2, (-2.0, 0.0, -9.0), "smooth")]))
    a.plant("hl", path([(0.0, (0, 0, 0), "smooth"), (2.0, REST_HL, "in2"), (4.2, (4.0, 0.0, -2.0), "smooth")]),
            foot=path([(0.0, 0, "smooth"), (2.0, -30, "smooth")]))
    a.plant("hr", path([(0.0, (0, 0, 0), "smooth"), (2.0, (-REST_HL[0], 0, REST_HL[2]), "in2"), (4.2, (-4.0, 0.0, 0.0), "smooth")]),
            foot=path([(0.0, 0, "smooth"), (2.0, -30, "smooth")]))
    a.events = {"roar": 1.0, "collapse": 2.0, "curled": 4.2}
    return a


# --------------------------------------------------------------------------------------------- flight

def hover():
    L = 1.9
    a = Anim("hover", L, True)
    pose = merge(AIR, LEGS_HANG, {"body": [-22, 0, 0], "neck1": [8, 0, 0], "neck2": [4, 0, 0], "neck3": [6, 0, 0], "neck4": [4, 0, 0], "head": [10, 0, 0],
                                  "tail1": [8, 0, 0], "tail2": [4, 0, 0], "tail3": [0, 0, 0]})
    a.key(0, pose).key(L, pose)
    a.layer(flap_layer(L, 50, 1.0, 2.2)).layer(tail_wave_air(L, 3.0))
    a.layer(lambda t: {"neck1": [wave(t, L, -2.5, -40), 0, 0], "head": [wave(t, L, 3.0, -20), 0, 0],
                       "arm_l": [wave(t, L, 5, -60), 0, 0], "thigh_l": [wave(t, L, 4, -80), 0, 0]})
    a.lag(NECK, 0.05)
    return a


def fly_fast():
    L = 1.25
    a = Anim("fly_fast", L, True)
    pose = merge(AIR, {"body": [6, 0, 0], "neck1": [-8, 0, 0], "head": [8, 0, 0], "wing_l": [0, -8, 0], "wing_l2": [0, 6, 0], "wing_l3": [0, 10, 0]})
    a.key(0, pose).key(L, pose)
    a.layer(flap_layer(L, 38, 1.0, 1.6)).layer(tail_wave_air(L, 1.5))
    a.lag(NECK, 0.04)
    return a


def glide():
    L = 4.0
    a = Anim("glide", L, True)
    pose = merge(AIR, {"wing_l": [-4, -4, -6], "wing_l2": [0, 0, 4], "wing_l3": [0, 0, 6]})
    a.key(0, pose).key(L, pose)
    a.layer(lambda t: {"wing_l": [wave(t, L, 2.0), 0, wave(t, L / 2, 2.5)], "wing_l3": [0, 0, wave(t, L / 2, 3.5, -40)],
                       "body@pos": [0, wave(t, L / 2, 0.8, 180), 0], "neck1": [wave(t, L, 2.0, 30), 0, 0], "head": [wave(t, L, -2.0, 60), 0, 0]})
    a.layer(tail_wave_air(L, 1.5))
    return a


def dive():
    L = 1.0
    a = Anim("dive", L, True)
    pose = merge(AIR, SWEPT, {"neck1": [10, 0, 0], "neck2": [6, 0, 0], "neck3": [2, 0, 0], "head": [-10, 0, 0], "jaw": [8, 0, 0]})
    a.key(0, pose).key(L, pose)
    a.layer(lambda t: {"wing_l": [wave(t, 0.25, 1.5), 0, wave(t, 0.3, 2.0)], "wing_l3": [0, 0, wave(t, 0.2, 3.0)], "head": [wave(t, 0.5, 1.5), 0, 0]})
    a.layer(tail_wave_air(0.5, 1.0))
    return a


def takeoff():
    a = Anim("takeoff", 1.4, False)
    crouch = add(STAND, {"body@pos": [0, -4, 0], "chest": [6, 0, 0], "neck1": [8, 0, 0], "head": [-6, 0, 0]})
    a.seq([(0.0, STAND, "smooth"),
           (0.35, merge(crouch, {"wing_l": [0, 10, -60], "wing_l2": [0, -6, 10], "wing_l3": [0, 6, 16]}), "out2"),
           (0.6, merge(add(AIR, {"body": [-24, 0, 0], "body@pos": [0, 4, 0], "neck1": [-10, 0, 0], "head": [6, 0, 0]}), LEGS_HANG,
                       {"wing_l": [-6, -8, 36], "wing_l2": [0, -4, -8], "wing_l3": [0, 6, -12]}), "in2"),
           (0.95, merge(add(AIR, {"body": [-12, 0, 0], "body@pos": [0, 2, 0]}), {"wing_l": [6, 10, -42], "wing_l2": [0, 22, 14], "wing_l3": [0, -30, 18],
                                                                              "finger_l2": [0, 10, 0], "finger_l3": [0, 20, 0]}), "smooth"),
           (1.25, merge(add(AIR, {"body": [-6, 0, 0]}), {"wing_l": [-4, -6, 30], "wing_l2": [0, -4, -6], "wing_l3": [0, 6, -10]}), "in2"),
           (1.4, merge(AIR, {"wing_l": [-4, -2, 10]}), "out2")])
    a.lag(NECK, 0.05).lag(TAIL, 0.07)
    a.lag(["wing_l", "wing_l2", "wing_l3"], 0.03).lag(["wing_r", "wing_r2", "wing_r3"], 0.03)
    w = lambda t: 1.0 - smooth_window(t, 0.42, 0.62, 9, 10)
    for leg in LEGS:
        a.plant(leg, weight=w)
    a.events = {"leap": 0.45}
    return a


def land():
    a = Anim("land", 1.4, "hold")
    flare = merge(AIR, LEGS_REACH, {"body": [-28, 0, 0], "body@pos": [0, 4, 0], "neck1": [10, 0, 0], "neck2": [6, 0, 0], "head": [8, 0, 0],
                                    "tail1": [12, 0, 0], "tail2": [6, 0, 0]})
    a.seq([(0.0, merge(AIR, {"wing_l": [0, 0, -20]}), "smooth"),
           (0.35, merge(flare, {"wing_l": [-10, -24, 40], "wing_l2": [0, 8, -6], "wing_l3": [0, -6, -10]}), "out2"),
           (0.65, merge(flare, {"wing_l": [8, -10, -30], "wing_l2": [0, 18, 10], "wing_l3": [0, -20, 14]}), "smooth"),
           (0.9, merge(add(STAND, {"body@pos": [0, -3, 0], "chest": [5, 0, 0], "neck1": [8, 0, 0]}), LOW_SPREAD), "in2"),
           (1.4, STAND, "smooth")])
    a.lag(NECK, 0.05).lag(TAIL, 0.08)
    w = lambda t: smooth_window(t, 0.72, 0.9, 9, 10)
    for leg in LEGS:
        a.plant(leg, weight=w)
    a.events = {"touchdown": 0.9}
    return a


def swoop():
    """Dives through the target with all four feet thrown forward, claws open (rake 0.75 s), then climbs away."""
    a = Anim("swoop", 1.6, False)
    a.seq([(0.0, merge(AIR, SWEPT, {"neck1": [8, 0, 0], "head": [-8, 0, 0]}), "smooth"),
           (0.55, merge(AIR, LEGS_RAKE, LOW_SPREAD, {"body": [-16, 0, 0], "neck1": [-6, 0, 0], "head": [10, 0, 0], "jaw": [30, 0, 0],
                                                    "claws_l": [-50, 0, 0]}), "out2"),
           (0.8, merge(AIR, LEGS_RAKE, {"body": [-6, 0, 0], "arm_l": [30, 0, -8], "thigh_l": [30, 0, -4], "claws_l": [40, 0, 0], "jaw": [10, 0, 0],
                                        "wing_l": [-6, -10, 34], "wing_l2": [0, -4, -6], "wing_l3": [0, 6, -10]}), "in"),
           (1.1, merge(AIR, {"body": [-14, 0, 0], "wing_l": [6, 10, -42], "wing_l2": [0, 22, 14], "wing_l3": [0, -30, 18], "finger_l2": [0, 10, 0],
                             "finger_l3": [0, 20, 0]}), "smooth"),
           (1.35, merge(AIR, {"body": [-8, 0, 0], "wing_l": [-4, -6, 30], "wing_l2": [0, -4, -6], "wing_l3": [0, 6, -10]}), "in2"),
           (1.6, merge(AIR, {"wing_l": [0, 0, 0]}), "smooth")])
    a.lag(NECK, 0.04).lag(TAIL, 0.06).lag(["arm_l", "forearm_l", "hand_l"], 0.02).lag(["arm_r", "forearm_r", "hand_r"], 0.02)
    a.layer(tail_wave_air(0.8, 2.0))
    a.events = {"rake": 0.75}
    return a


HOVER_BASE = merge(AIR, LEGS_HANG, {"body": [-16, 0, 0], "neck1": [4, 0, 0], "neck3": [4, 0, 0], "head": [8, 0, 0], "tail1": [6, 0, 0], "tail2": [3, 0, 0]})


def air_attack(name, length, keys, events, flap=1.9, amp=44):
    a = Anim(name, length, False)
    a.seq([(t, merge(HOVER_BASE, p), e) for t, p, e in keys])
    a.layer(flap_layer(flap, amp, 1.0, 2.0)).layer(tail_wave_air(flap, 2.5))
    a.lag(NECK, 0.03)
    a.events = events
    return a


def cog_spit():
    spit = {"neck1": [10, 0, 0], "neck2": [6, 0, 0], "head": [2, 0, 0], "jaw": [36, 0, 0]}
    back = {"neck1": [-6, 0, 0], "neck2": [-4, 0, 0], "head": [-8, 0, 0], "jaw": [8, 0, 0]}
    keys = [(0.0, {}, "smooth"), (0.06, back, "out2"), (0.12, spit, "in"), (0.34, back, "smooth"), (0.42, spit, "in"), (0.64, back, "smooth"),
            (0.72, spit, "in"), (1.2, {}, "smooth")]
    return air_attack("cog_spit", 1.2, keys, {"spits": [0.1, 0.4, 0.7]})


def thunder():
    up = merge({"body": [-30, 0, 0], "tail1": [18, 0, 0], "tail2": [6, 0, 0], "neck1": [-8, 0, 0], "neck2": [-4, 0, 0], "neck3": [8, 0, 0], "head": [-28, 0, 0], "jaw": [44, 0, 0],
                "crest@scale": [1.25, 1.25, 1.25], "core@scale": [1.6, 1.6, 1.6]})
    keys = [(0.0, {}, "smooth"), (0.4, {"body": [-6, 0, 0], "neck1": [12, 0, 0], "head": [4, 0, 0]}, "smooth"), (0.8, up, "out"),
            (2.6, merge(up, {"head": [-32, 0, 0]}), "smooth"), (3.2, {}, "smooth")]
    a = air_attack("thunder", 3.2, keys, {"roar": 0.5, "storm": 0.8}, flap=1.6, amp=50)
    a.layer(jitter(1.2, ("head", "neck3"), 0.8, 2.6))
    return a


def roar_air():
    up = {"body": [-26, 0, 0], "tail1": [16, 0, 0], "tail2": [6, 0, 0], "neck1": [-6, 0, 0], "neck2": [-2, 0, 0], "neck3": [10, 0, 0], "head": [-26, 0, 0], "jaw": [42, 0, 0],
          "crest@scale": [1.18, 1.18, 1.18], "core@scale": [1.4, 1.4, 1.4]}
    keys = [(0.0, {}, "smooth"), (0.35, {"body": [-8, 0, 0], "neck1": [10, 0, 0], "head": [4, 0, 0]}, "smooth"), (0.7, up, "out"),
            (1.7, merge(up, {"head": [-30, 0, 0]}), "smooth"), (2.2, {}, "smooth")]
    a = air_attack("roar_air", 2.2, keys, {"roar": 0.6}, flap=1.6, amp=48)
    a.layer(lambda t: {"jaw": [smooth_window(t, 0.7, 0.8, 1.6, 1.8) * wave(t, 0.09, 2.5), 0, 0]})
    return a


def breath_charge_air():
    keys = [(0.0, {}, "smooth"), (1.0, {"body": [-8, 0, 0], "neck1": [-12, 0, 0], "neck2": [-6, 0, 0], "head": [-12, 0, 0], "jaw": [14, 0, 0],
                                        "ribs@scale": [1.07, 1.06, 1], "core@scale": [1.5, 1.5, 1.5], "crest@scale": [1.15, 1.15, 1.15]}, "out2")]
    a = air_attack("breath_charge", 1.0, keys, {})
    a.loop = "hold"
    return a


def breath_air():
    L = 1.9
    a = Anim("breath", L, True)
    pose = merge(HOVER_BASE, {"body": [-10, 0, 0], "neck1": [14, 0, 0], "neck2": [8, 0, 0], "neck3": [2, 0, 0], "neck4": [-4, 0, 0], "head": [-10, 0, 0],
                              "jaw": [44, 0, 0], "core@scale": [1.35, 1.35, 1.35]})
    a.key(0, pose).key(L, pose)
    a.layer(flap_layer(L, 40, 1.0, 1.6)).layer(jitter(1.2, ("head", "neck4"))).layer(glow_pulse(0.2, 1.3, 1.5)).layer(tail_wave_air(L, 2.0))
    return a


def slam():
    """Dive impact: crouched deep, wings flung out low, head down with a roar, then back up to a stance (1.2 s)."""
    a = Anim("slam", 1.2, False)
    impact = merge(add(STAND, {"body@pos": [0, -6, 0], "chest": [8, 0, 0], "neck1": [20, 0, 0], "neck2": [8, 0, 0], "head": [-16, 0, 0], "jaw": [36, 0, 0]}),
                   LOW_SPREAD)
    a.seq([(0.0, merge(impact, SWEPT), "smooth"), (0.12, impact, "out2"), (0.6, merge(impact, {"body@pos": [0, -4, 0]}), "smooth"), (1.2, STAND, "smooth")])
    a.lag(NECK, 0.05).lag(TAIL, 0.06)
    a.plant("fl", lambda t: (3.0, 0.0, -4.0))
    a.plant("fr", lambda t: (-3.0, 0.0, -4.0))
    a.plant("hl", lambda t: (2.0, 0.0, 2.0))
    a.plant("hr", lambda t: (-2.0, 0.0, 2.0))
    a.events = {"impact": 0.0}
    return a


def air_bite():
    keys = [(0.0, {}, "smooth"), (0.2, {"neck1": [-10, 0, 0], "neck2": [-6, 0, 0], "head": [-10, 0, 0], "jaw": [16, 0, 0]}, "out2"),
            (0.32, {"neck1": [14, 0, 0], "neck2": [10, 0, 0], "neck3": [2, 0, 0], "head": [-4, 0, 0], "jaw": [40, 0, 0]}, "in2"),
            (0.38, {"neck1": [16, 0, 0], "neck2": [10, 0, 0], "head": [-2, 0, 0], "jaw": [-2, 0, 0]}, "snap"), (0.8, {}, "smooth")]
    return air_attack("air_bite", 0.8, keys, {"hit": 0.38}, flap=1.6, amp=40)


ANIMS2 = [sit, lambda: lie_transition("lie_down", 2.0, True), lambda: lie_transition("rest_up", 1.6, False), sleep, wake, run,
          bite_sweep, grab, grab_shake, grab_toss, tail_whip, tail_sweep, stomp, wing_gust, field_roar, rend, breath_charge_ground, breath_ground,
          phase_two, pylon_charge, stunned, death, hover, fly_fast, glide, dive, takeoff, land, swoop, cog_spit, thunder, roar_air,
          breath_charge_air, breath_air, slam, air_bite]
MIRRORED = {"tail_whip": "tail_whip_right"}
