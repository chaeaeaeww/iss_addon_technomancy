package net.isstechnomancy.effect;

import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import net.isstechnomancy.registry.TechEffects;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;

/**
 * Granted by Overdrive Protocol. The next Technomancy spell its holder casts is upgraded and consumes the effect:
 * <ul>
 *     <li>Gear Barrage: 5 gears, 2 bounces, +25% damage, pierce 1</li>
 *     <li>Arc Welder: the arc forks to 2 extra enemies for 50% damage</li>
 *     <li>Deploy Brass Sentry: deploys a Siege Sentry instead</li>
 *     <li>Steam Vent: superheated (longer, wider, ignites, stronger knockback)</li>
 *     <li>Assemble Automaton: assembles a Mk.II Automaton</li>
 * </ul>
 */
public class OverdriveEffect extends MobEffect {
    public static final int COLOR = 0xFF8A3A;

    public OverdriveEffect() {
        super(MobEffectCategory.BENEFICIAL, COLOR);
    }

    /**
     * Server side. Removes Overdrive from the caster if present and plays the trigger feedback.
     *
     * @return true when the current cast should use its upgraded version
     */
    public static boolean consume(LivingEntity caster) {
        if (caster.level().isClientSide || !caster.hasEffect(TechEffects.OVERDRIVE.get())) {
            return false;
        }
        caster.removeEffect(TechEffects.OVERDRIVE.get());
        caster.level().playSound(null, caster.getX(), caster.getY(), caster.getZ(), TechSounds.OVERDRIVE_TRIGGER.get(), SoundSource.PLAYERS, 1.0f, 1.0f);
        MagicManager.spawnParticles(caster.level(), TechParticles.BRASS_SPARK.get(), caster.getX(), caster.getY() + 1.0, caster.getZ(), 30, 0.4, 0.6, 0.4, 0.3, false);
        MagicManager.spawnParticles(caster.level(), TechParticles.STEAM_PUFF.get(), caster.getX(), caster.getY() + 0.2, caster.getZ(), 12, 0.6, 0.1, 0.6, 0.03, false);
        return true;
    }
}
