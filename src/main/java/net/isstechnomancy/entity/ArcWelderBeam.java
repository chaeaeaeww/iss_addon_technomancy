package net.isstechnomancy.entity;

import io.redspace.ironsspellbooks.api.util.Utils;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.damage.DamageSources;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSpells;
import net.isstechnomancy.spells.ArcWelderSpell;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

/**
 * Invisible anchor entity for the Arc Welder channel. It follows its caster, is drawn by
 * {@link net.isstechnomancy.client.renderer.ArcWelderBeamRenderer} and applies the damage pulses.
 * The spell discards it through EntityCastData when the cast ends.
 */
public class ArcWelderBeam extends Entity {
    private static final EntityDataAccessor<Integer> DATA_OWNER_ID = SynchedEntityData.defineId(ArcWelderBeam.class, EntityDataSerializers.INT);
    /** Hard cap in case the cast is interrupted without the cast data being reset. */
    private static final int MAX_LIFETIME = 120;

    private float damage;
    private int forks;
    private int teslaLevel;

    public ArcWelderBeam(EntityType<? extends ArcWelderBeam> entityType, Level level) {
        super(entityType, level);
        this.noPhysics = true;
    }

    public ArcWelderBeam(Level level, LivingEntity owner) {
        this(TechEntities.ARC_WELDER_BEAM.get(), level);
        this.entityData.set(DATA_OWNER_ID, owner.getId());
        followOwner(owner);
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_OWNER_ID, -1);
    }

    @Nullable
    public LivingEntity getOwner() {
        return level().getEntity(this.entityData.get(DATA_OWNER_ID)) instanceof LivingEntity living ? living : null;
    }

    public void setDamage(float damage) {
        this.damage = damage;
    }

    /**
     * Overdrive: number of extra enemies the arc jumps to from its primary target.
     */
    public void setForks(int forks) {
        this.forks = forks;
    }

    public void setTeslaLevel(int teslaLevel) {
        this.teslaLevel = teslaLevel;
    }

    @Override
    public void tick() {
        super.tick();
        LivingEntity owner = getOwner();
        if (owner == null || !owner.isAlive()) {
            if (!level().isClientSide) {
                discard();
            }
            return;
        }
        followOwner(owner);
        if (level().isClientSide) {
            if (tickCount % 2 == 0) {
                Vec3 end = trace(level(), owner, 1f).getLocation();
                Vec3 jitter = Utils.getRandomVec3(0.08);
                level().addParticle(TechParticles.ARC_MOTE.get(), end.x, end.y, end.z, jitter.x, jitter.y + 0.02, jitter.z);
                level().addParticle(TechParticles.BRASS_SPARK.get(), end.x, end.y, end.z, jitter.x * 2, 0.1 + Math.abs(jitter.y), jitter.z * 2);
            }
        } else if (tickCount > MAX_LIFETIME) {
            discard();
        }
    }

    private void followOwner(LivingEntity owner) {
        setPos(owner.getX(), owner.getEyeY() - 0.3, owner.getZ());
    }

    /**
     * Shared by server damage and client rendering so both agree on where the arc lands.
     */
    public static HitResult trace(Level level, LivingEntity owner, float partialTick) {
        Vec3 start = owner.getEyePosition(partialTick);
        Vec3 end = start.add(owner.getViewVector(partialTick).scale(ArcWelderSpell.RANGE));
        return Utils.raycastForEntity(level, owner, start, end, true, 0.35f,
                entity -> entity != owner && entity.isPickable() && !entity.isSpectator());
    }

    /**
     * One damage tick. Called by {@link ArcWelderSpell#onCast} every 10 ticks of the channel.
     */
    public void pulse() {
        if (level().isClientSide) {
            return;
        }
        LivingEntity owner = getOwner();
        if (owner == null) {
            return;
        }
        HitResult hit = trace(level(), owner, 1f);
        Vec3 location = hit.getLocation();
        if (hit instanceof EntityHitResult entityHit) {
            Entity target = entityHit.getEntity();
            if (target instanceof BrassSentry sentry && sentry.isOwnedBy(owner)) {
                sentry.applyWeld();
                MagicManager.spawnParticles(level(), TechParticles.ARC_MOTE.get(), location.x, location.y, location.z, 10, 0.2, 0.2, 0.2, 0.05, false);
                return;
            }
            if (!DamageSources.isFriendlyFireBetween(owner, target)) {
                DamageSources.applyDamage(target, damage, TechSpells.ARC_WELDER.get().getDamageSource(this, owner).setIFrames(0));
                if (teslaLevel > 0 && tickCount % 20 < 10) {
                    net.isstechnomancy.module.TeslaHelper.arc(this, owner, target, damage, teslaLevel);
                }
                if (target instanceof LivingEntity livingTarget) {
                    livingTarget.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, ArcWelderSpell.SLOW_DURATION_TICKS, 0), owner);
                    if (forks > 0) {
                        fork(owner, livingTarget);
                    }
                }
            }
        }
        MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), location.x, location.y, location.z, 8, 0.08, 0.08, 0.08, 0.25, false);
        MagicManager.spawnParticles(level(), TechParticles.ARC_MOTE.get(), location.x, location.y, location.z, 4, 0.1, 0.1, 0.1, 0.03, false);
    }

    private void fork(LivingEntity owner, LivingEntity origin) {
        Vec3 from = origin.getBoundingBox().getCenter();
        level().getEntitiesOfClass(LivingEntity.class, origin.getBoundingBox().inflate(ArcWelderSpell.FORK_RANGE),
                        candidate -> candidate != origin && candidate != owner && candidate.isAlive()
                                && !DamageSources.isFriendlyFireBetween(owner, candidate) && candidate.hasLineOfSight(origin))
                .stream()
                .sorted(java.util.Comparator.comparingDouble(candidate -> candidate.distanceToSqr(origin)))
                .limit(forks)
                .forEach(candidate -> {
                    DamageSources.applyDamage(candidate, damage * ArcWelderSpell.FORK_DAMAGE, TechSpells.ARC_WELDER.get().getDamageSource(this, owner).setIFrames(0));
                    candidate.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, ArcWelderSpell.SLOW_DURATION_TICKS, 0), owner);
                    Vec3 to = candidate.getBoundingBox().getCenter();
                    int steps = (int) Math.ceil(from.distanceTo(to) / 0.35);
                    for (int i = 0; i <= steps; i++) {
                        Vec3 point = from.lerp(to, i / (double) steps).add(Utils.getRandomVec3(0.12));
                        MagicManager.spawnParticles(level(), TechParticles.ARC_MOTE.get(), point.x, point.y, point.z, 1, 0, 0, 0, 0, false);
                    }
                    MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), to.x, to.y, to.z, 5, 0.1, 0.1, 0.1, 0.2, false);
                });
    }

    @Override
    public boolean shouldRenderAtSqrDistance(double distance) {
        return distance < 64 * 64;
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        // Transient entity (registered with noSave); nothing to persist.
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        // Transient entity (registered with noSave); nothing to persist.
    }

    @Override
    public Packet<ClientGamePacketListener> getAddEntityPacket() {
        return new ClientboundAddEntityPacket(this);
    }
}
