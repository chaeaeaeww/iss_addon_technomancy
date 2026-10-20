package net.isstechnomancy.entity.boss;

import java.util.List;

/**
 * Animation keys the Java code plays for the Tech Dragon, the Hextech Pylon and the Hextech Shell. GeckoLib looks them
 * up by this exact key, so devtest ValidateAnimations checks each one exists in its animation file (plain class: the
 * check runs without bootstrapping Minecraft).
 */
public final class DragonAnimationNames {
    public static final List<String> DRAGON = List.of("roar_air", "hover", "fly", "fly_fast", "glide", "land", "takeoff", "walk",
            "sit", "rest", "ground_idle", "lie_down", "rest_up", "sleep", "wake", "run", "bite", "bite_sweep", "claw_left", "claw_right", "grab",
            "grab_shake", "grab_toss", "tail_whip", "tail_whip_right", "tail_sweep", "stomp", "wing_gust", "field_roar", "rend",
            "breath_charge_ground", "breath_ground", "roar", "slam", "cog_spit", "breath_charge", "breath", "thunder", "swoop", "dive", "air_bite",
            "phase_two", "pylon_charge", "stunned", "death", "pounce", "dash_claw_left", "dash_claw_right", "dodge_left", "dodge_right", "ram",
            "storm", "dive_bounce", "backstep", "wing_push", "spit", "crash_land",
            "emp_stunned", "pin_gnaw", "carry", "core_charge", "core_beam", "overload",
            "spin_discharge", "hop_forward", "hop_back", "breath_down", "strafe");
    public static final List<String> PYLON = List.of("rise", "charge", "collapse");
    public static final List<String> SHELL = List.of("assemble", "charge", "burst");

    private DragonAnimationNames() {
    }
}
