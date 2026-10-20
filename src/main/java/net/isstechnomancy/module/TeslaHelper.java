package net.isstechnomancy.module;

import io.redspace.ironsspellbooks.api.registry.SpellRegistry;
import io.redspace.ironsspellbooks.api.util.Utils;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.damage.DamageSources;
import io.redspace.ironsspellbooks.particle.ZapParticleOption;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Tesla module: after a Technomancy hit, lightning jumps from the victim to the nearest other enemies.
 */
public final class TeslaHelper {
    public static final double JUMP_RANGE = 5.0;

    private TeslaHelper() {
    }

    public static void arc(Entity source, Entity attacker, Entity firstVictim, float hitDamage, int teslaLevel) {
        if (teslaLevel <= 0 || !(firstVictim.level() instanceof ServerLevel level) || attacker == null) {
            return;
        }
        float damage = hitDamage * ModuleStats.teslaDamageShare(teslaLevel);
        List<Entity> zapped = new ArrayList<>();
        zapped.add(firstVictim);
        Entity from = firstVictim;
        for (int jump = 0; jump < teslaLevel; jump++) {
            Entity current = from;
            List<LivingEntity> candidates = level.getEntitiesOfClass(LivingEntity.class, current.getBoundingBox().inflate(JUMP_RANGE),
                    e -> e.isAlive() && e != attacker && !zapped.contains(e) && !DamageSources.isFriendlyFireBetween(attacker, e)
                            && !attacker.isAlliedTo(e));
            if (candidates.isEmpty()) {
                break;
            }
            candidates.sort(Comparator.comparingDouble(e -> e.distanceToSqr(current)));
            LivingEntity next = candidates.get(0);
            Vec3 start = current.position().add(0, current.getBbHeight() * 0.5, 0);
            Vec3 end = next.position().add(0, next.getBbHeight() * 0.5, 0);
            if (!Utils.hasLineOfSight(level, start, end, true)) {
                zapped.add(next);
                continue;
            }
            level.sendParticles(new ZapParticleOption(end), start.x, start.y, start.z, 1, 0, 0, 0, 0);
            MagicManager.spawnParticles(level, ParticleHelper.ELECTRIC_SPARKS, end.x, end.y, end.z, 6, 0.2, 0.2, 0.2, 0.15, false);
            DamageSources.applyDamage(next, damage, SpellRegistry.CHAIN_LIGHTNING_SPELL.get().getDamageSource(source, attacker));
            level.playSound(null, end.x, end.y, end.z, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.PLAYERS, 0.35f, 1.6f + level.random.nextFloat() * 0.3f);
            zapped.add(next);
            from = next;
        }
    }
}
