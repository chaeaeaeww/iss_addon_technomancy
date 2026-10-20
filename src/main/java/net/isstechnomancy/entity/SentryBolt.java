package net.isstechnomancy.entity;

import io.redspace.ironsspellbooks.api.util.Utils;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.damage.DamageSources;
import io.redspace.ironsspellbooks.entity.spells.AbstractMagicProjectile;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSounds;
import net.isstechnomancy.registry.TechSpells;
import net.minecraft.sounds.SoundEvent;
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
 * Arcane bolt fired by a Brass Sentry. Owned by the sentry's caster so kills, resistances and
 * friendly-fire rules resolve against the player. Rendered purely through its arc-mote trail.
 */
public class SentryBolt extends AbstractMagicProjectile {
    private static final int MAX_FLIGHT_TICKS = 40;
    private int teslaLevel;

    public SentryBolt(EntityType<? extends SentryBolt> entityType, Level level) {
        super(entityType, level);
        this.setNoGravity(true);
    }

    public SentryBolt(Level level, LivingEntity owner) {
        this(TechEntities.SENTRY_BOLT.get(), level);
        setOwner(owner);
    }

    public void setTeslaLevel(int teslaLevel) {
        this.teslaLevel = teslaLevel;
    }

    @Override
    public void tick() {
        super.tick();
        if (!level().isClientSide && tickCount > MAX_FLIGHT_TICKS) {
            discard();
        }
    }

    @Override
    public float getSpeed() {
        return 1.4f;
    }

    @Override
    public void trailParticles() {
        Vec3 motion = getDeltaMovement();
        int steps = 3;
        for (int i = 0; i < steps; i++) {
            Vec3 offset = motion.scale(i / (float) steps);
            Vec3 jitter = Utils.getRandomVec3(0.02);
            level().addParticle(TechParticles.ARC_MOTE.get(), getX() - offset.x, getY() + getBbHeight() * 0.5 - offset.y, getZ() - offset.z, jitter.x, jitter.y, jitter.z);
        }
    }

    @Override
    public void impactParticles(double x, double y, double z) {
        MagicManager.spawnParticles(level(), TechParticles.ARC_MOTE.get(), x, y, z, 10, 0.1, 0.1, 0.1, 0.08, false);
        MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), x, y, z, 5, 0.05, 0.05, 0.05, 0.15, false);
    }

    @Override
    public Optional<Supplier<SoundEvent>> getImpactSound() {
        return Optional.of(TechSounds.SENTRY_BOLT_IMPACT);
    }

    @Override
    protected void onHitBlock(@NotNull BlockHitResult result) {
        super.onHitBlock(result);
        discard();
    }

    @Override
    protected void onHitEntity(@NotNull EntityHitResult hitResult) {
        super.onHitEntity(hitResult);
        if (!level().isClientSide) {
            Entity owner = getOwner();
            Entity attacker = owner == null ? this : owner;
            DamageSources.applyDamage(hitResult.getEntity(), damage, TechSpells.DEPLOY_BRASS_SENTRY.get().getDamageSource(this, attacker));
            net.isstechnomancy.module.TeslaHelper.arc(this, owner, hitResult.getEntity(), damage, teslaLevel);
        }
        consumeEntityImpact(hitResult, true);
    }
}
