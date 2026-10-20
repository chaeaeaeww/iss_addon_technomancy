package net.isstechnomancy.registry;

import io.redspace.ironsspellbooks.api.util.AnimationHolder;
import net.isstechnomancy.ISSTechnomancy;
import software.bernie.geckolib.core.animation.Animation;
import software.bernie.geckolib.core.animation.RawAnimation;

import java.util.Optional;

/**
 * Player casting animations. PlayerAnimator loads every file in assets/&lt;namespace&gt;/player_animation/,
 * so these resolve to the animations defined in assets/iss_technomancy/player_animation/technomancy_animations.json.
 * Spell-casting mobs (Technomancer) play the closest Iron's Spells mob animation instead (casting_animations.json).
 */
public class TechAnimations {
    public static final AnimationHolder GEAR_FLICK = holder("gear_flick", true, false, "instant_projectile");
    public static final AnimationHolder WELDER_CHANNEL = holder("welder_channel", false, false, "continuous_thrust");
    public static final AnimationHolder DEPLOY_SENTRY = holder("deploy_sentry", true, true, "long_cast");
    public static final AnimationHolder STEAM_PUSH = holder("steam_push", true, false, "charge_spit_finish");
    public static final AnimationHolder DEPLOY_SENTRY_FINISH = holder("deploy_sentry_finish", true, true, "long_cast_finish");
    public static final AnimationHolder ROCKET_GRAB = holder("gear_flick", true, false, "instant_projectile");
    public static final AnimationHolder EMP_SCREECH = holder("steam_push", true, false, "cast_t_pose");
    public static final AnimationHolder FIELD_CHANNEL = holder("deploy_sentry", true, true, "self_cast_two_hands");

    private static AnimationHolder holder(String player, boolean playOnce, boolean legs, String mob) {
        RawAnimation mobAnimation = RawAnimation.begin().then(mob, playOnce ? Animation.LoopType.PLAY_ONCE : Animation.LoopType.HOLD_ON_LAST_FRAME);
        return new AnimationHolder(ISSTechnomancy.id(player), playOnce, legs) {
            @Override
            public Optional<RawAnimation> getForMob() {
                return Optional.of(mobAnimation);
            }
        };
    }
}
