package net.isstechnomancy.entity;

import io.redspace.ironsspellbooks.api.util.Utils;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.damage.DamageSources;
import io.redspace.ironsspellbooks.entity.spells.AbstractMagicProjectile;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSounds;
import net.isstechnomancy.registry.TechSpells;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;

import java.util.Optional;
import java.util.function.Supplier;

/**
 * Explosive shell fired by a Siege Sentry. Detonates on any impact: full damage at the center,
 * falling to 60% at the edge of {@link #getExplosionRadius()}. Never breaks blocks. Drawn by its smoke trail.
 */
public class SiegeShell extends AbstractMagicProjectile {
    private static final int MAX_FLIGHT_TICKS = 50;
    private boolean detonated;
    private int teslaLevel;

    public SiegeShell(EntityType<? extends SiegeShell> entityType, Level level) {
        super(entityType, level);
        this.setNoGravity(false);
    }

    public SiegeShell(Level level, LivingEntity owner) {
        this(TechEntities.SIEGE_SHELL.get(), level);
        setOwner(owner);
    }

    public void setTeslaLevel(int teslaLevel) {
        this.teslaLevel = teslaLevel;
    }

    @Override
    public void tick() {
        super.tick();
        if (!level().isClientSide && !isRemoved() && tickCount > MAX_FLIGHT_TICKS) {
            detonate(position());
        }
    }

    @Override
    protected double getDefaultGravity() {
        return 0.012;
    }

    @Override
    public float getSpeed() {
        return 1.3f;
    }

    @Override
    public void trailParticles() {
        Vec3 jitter = Utils.getRandomVec3(0.03);
        level().addParticle(ParticleTypes.SMOKE, getX(), getY() + getBbHeight() * 0.5, getZ(), jitter.x, jitter.y, jitter.z);
        level().addParticle(TechParticles.BRASS_SPARK.get(), getX(), getY() + getBbHeight() * 0.5, getZ(), jitter.x, jitter.y, jitter.z);
        if (tickCount % 2 == 0) {
            level().addParticle(TechParticles.ARC_MOTE.get(), getX(), getY() + getBbHeight() * 0.5, getZ(), 0, 0, 0);
        }
    }

    @Override
    public void impactParticles(double x, double y, double z) {
        // Detonation draws its own burst in detonate().
    }

    @Override
    public Optional<Supplier<SoundEvent>> getImpactSound() {
        return Optional.empty();
    }

    @Override
    protected void onHitBlock(@NotNull BlockHitResult result) {
        super.onHitBlock(result);
        if (!level().isClientSide) {
            detonate(result.getLocation());
        } else {
            discard();
        }
    }

    @Override
    protected void onHitEntity(@NotNull EntityHitResult hitResult) {
        super.onHitEntity(hitResult);
        if (!level().isClientSide) {
            detonate(hitResult.getLocation());
        } else {
            discard();
        }
    }

    private void detonate(Vec3 center) {
        if (detonated) {
            return;
        }
        detonated = true;
        Entity owner = getOwner();
        Entity attacker = owner == null ? this : owner;
        float radius = getExplosionRadius();
        LivingEntity closest = null;
        for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(radius).move(center.subtract(position())))) {
            if (victim == owner || DamageSources.isFriendlyFireBetween(attacker, victim)) {
                continue;
            }
            double distance = victim.getBoundingBox().getCenter().distanceTo(center);
            if (distance > radius + victim.getBbWidth() * 0.5) {
                continue;
            }
            float falloff = (float) (1.0 - 0.4 * Math.min(1.0, distance / radius));
            DamageSources.applyDamage(victim, damage * falloff, TechSpells.DEPLOY_BRASS_SENTRY.get().getDamageSource(this, attacker).setIFrames(0));
            if (closest == null || victim.distanceToSqr(center) < closest.distanceToSqr(center)) {
                closest = victim;
            }
        }
        if (closest != null) {
            net.isstechnomancy.module.TeslaHelper.arc(this, owner, closest, damage, teslaLevel);
        }
        MagicManager.spawnParticles(level(), ParticleTypes.EXPLOSION, center.x, center.y, center.z, 1, 0, 0, 0, 0, true);
        MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), center.x, center.y, center.z, 10, radius * 0.4, 0.3, radius * 0.4, 0.04, false);
        MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), center.x, center.y, center.z, 24, 0.2, 0.2, 0.2, 0.35, false);
        MagicManager.spawnParticles(level(), TechParticles.ARC_MOTE.get(), center.x, center.y, center.z, 10, radius * 0.4, 0.3, radius * 0.4, 0.05, false);
        level().playSound(null, center.x, center.y, center.z, TechSounds.SIEGE_SHELL_EXPLODE.get(), SoundSource.NEUTRAL, 1.4f, 0.9f + random.nextFloat() * 0.2f);
        discard();
    }
}
