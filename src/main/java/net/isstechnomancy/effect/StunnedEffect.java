package net.isstechnomancy.effect;

import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.phys.Vec3;

/**
 * Short Circuit: the target is locked in place and can't deal melee damage. Applied by Rocket Grab, EMP Screech and
 * the Mk.II automaton.
 */
public class StunnedEffect extends MobEffect {
    public static final int COLOR = 0x6FE8FF;

    public StunnedEffect() {
        super(MobEffectCategory.HARMFUL, COLOR);
        addAttributeModifier(Attributes.MOVEMENT_SPEED, "8a3c2f0e-5b61-4d35-9a0a-6f7f6f2a1c01", -1.0, AttributeModifier.Operation.MULTIPLY_TOTAL);
        addAttributeModifier(Attributes.ATTACK_DAMAGE, "8a3c2f0e-5b61-4d35-9a0a-6f7f6f2a1c02", -1.0, AttributeModifier.Operation.MULTIPLY_TOTAL);
        addAttributeModifier(Attributes.FLYING_SPEED, "8a3c2f0e-5b61-4d35-9a0a-6f7f6f2a1c03", -1.0, AttributeModifier.Operation.MULTIPLY_TOTAL);
    }

    @Override
    public void applyEffectTick(LivingEntity entity, int amplifier) {
        Vec3 motion = entity.getDeltaMovement();
        entity.setDeltaMovement(0, Math.min(motion.y, 0), 0);
        if (entity instanceof Mob mob) {
            mob.getNavigation().stop();
            mob.setJumping(false);
        }
    }

    @Override
    public boolean isDurationEffectTick(int duration, int amplifier) {
        return true;
    }
}
