package net.isstechnomancy.entity;

import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.entity.boss.TechDragon;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.UUID;

/**
 * Magnetic Field: a dome centered where it was cast. Everything inside except the caster is slowed, dragged to the
 * ground (flyers, levitating and jumping creatures are pulled down hard) and stripped of upward momentum. It deals no
 * damage. Only the upper hemisphere above the cast point is affected. Projectiles from others are bent down and slowed.
 * Rendered as a spinning ground sigil under a shimmering dome (see MagneticFieldRenderer).
 */
public class MagneticField extends Entity {
    private static final EntityDataAccessor<Float> DATA_RADIUS = SynchedEntityData.defineId(MagneticField.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Integer> DATA_DURATION = SynchedEntityData.defineId(MagneticField.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> DATA_OVERCHARGED = SynchedEntityData.defineId(MagneticField.class, EntityDataSerializers.BOOLEAN);

    @Nullable
    private UUID ownerUUID;
    @Nullable
    private LivingEntity cachedOwner;

    public MagneticField(EntityType<? extends MagneticField> type, Level level) {
        super(type, level);
        this.noPhysics = true;
    }

    public MagneticField(Level level, LivingEntity owner, float radius, int duration, boolean overcharged) {
        this(TechEntities.MAGNETIC_FIELD.get(), level);
        this.ownerUUID = owner.getUUID();
        this.cachedOwner = owner;
        this.entityData.set(DATA_RADIUS, radius);
        this.entityData.set(DATA_DURATION, duration);
        this.entityData.set(DATA_OVERCHARGED, overcharged);
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_RADIUS, 8f);
        this.entityData.define(DATA_DURATION, 160);
        this.entityData.define(DATA_OVERCHARGED, false);
    }

    public float getRadius() {
        return this.entityData.get(DATA_RADIUS);
    }

    public int getDuration() {
        return this.entityData.get(DATA_DURATION);
    }

    public boolean isOvercharged() {
        return this.entityData.get(DATA_OVERCHARGED);
    }

    @Nullable
    public LivingEntity getOwner() {
        if (cachedOwner != null && !cachedOwner.isRemoved()) {
            return cachedOwner;
        }
        if (ownerUUID != null && !level().isClientSide && ((net.minecraft.server.level.ServerLevel) level()).getEntity(ownerUUID) instanceof LivingEntity living) {
            cachedOwner = living;
            return living;
        }
        return null;
    }

    @Override
    public void tick() {
        super.tick();
        float radius = getRadius();
        if (level().isClientSide) {
            clientParticles(radius);
            return;
        }
        if (tickCount > getDuration()) {
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 0.5, getZ(), 30, radius * 0.4, 0.3, radius * 0.4, 0.2, false);
            discard();
            return;
        }
        LivingEntity owner = getOwner();
        if (tickCount % 30 == 1) {
            level().playSound(null, getX(), getY(), getZ(), SoundEvents.BEACON_AMBIENT, SoundSource.PLAYERS, 1.6f, 0.6f);
        }
        // upper hemisphere: centred on the cast point, nothing below the ground plane is affected
        AABB box = new AABB(getX() - radius, getY() - 1, getZ() - radius, getX() + radius, getY() + radius, getZ() + radius);
        for (Entity e : level().getEntities(this, box)) {
            if (e == owner || e.isSpectator() || !insideDome(e, radius)) {
                continue;
            }
            if (e instanceof Projectile projectile) {
                if (projectile.getOwner() != owner) {
                    Vec3 v = projectile.getDeltaMovement();
                    projectile.setDeltaMovement(v.x * 0.8, v.y - 0.08, v.z * 0.8);
                    projectile.hurtMarked = true;
                }
                continue;
            }
            if (!(e instanceof LivingEntity living) || (e instanceof Player p && (p.isCreative() || p.isSpectator()))) {
                continue;
            }
            // slowed and dragged down to the ground (no damage: the field only controls)
            living.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 15, isOvercharged() ? 3 : 2, false, false, true));
            living.removeEffect(MobEffects.LEVITATION);
            living.removeEffect(MobEffects.SLOW_FALLING);
            Vec3 v = living.getDeltaMovement();
            // the Tech Dragon cannot be pulled (it is immune to pull effects)
            double pull = living instanceof TechDragon ? 0.0 : (living.onGround() ? 0.0 : 0.45);
            living.setDeltaMovement(v.x * 0.85, Math.min(v.y, 0) - pull, v.z * 0.85);
            living.hurtMarked = true;
            if (living instanceof Player player && player.isFallFlying()) {
                player.stopFallFlying();
            }
            if (tickCount % 20 == 0) {
                MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, living.getX(), living.getY() + living.getBbHeight() * 0.5, living.getZ(), 3, 0.2, 0.3, 0.2, 0.05, false);
            }
        }
    }

    /** True when the entity's centre lies inside the dome (the upper half of a sphere of the field's radius). */
    public boolean insideDome(Entity e, float radius) {
        Vec3 c = e.getBoundingBox().getCenter();
        double dy = Math.max(0, c.y - getY() - 0.5);
        if (e.getY() < getY() - 1) {
            return false;
        }
        double dx = c.x - getX(), dz = c.z - getZ();
        return dx * dx + dy * dy + dz * dz <= radius * radius;
    }

    private void clientParticles(float radius) {
        for (int i = 0; i < 3; i++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = radius * (0.92 + random.nextDouble() * 0.08);
            level().addParticle(TechParticles.ARC_MOTE.get(), getX() + Math.cos(a) * r, getY() + 0.1 + random.nextDouble() * 0.4, getZ() + Math.sin(a) * r, 0, 0.03, 0);
        }
        if (tickCount % 2 == 0) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = random.nextDouble() * radius;
            double h = 3 + random.nextDouble() * 3;
            // motes falling inward and down: the field drags things to the ground
            level().addParticle(TechParticles.ARC_MOTE.get(), getX() + Math.cos(a) * r, getY() + h, getZ() + Math.sin(a) * r, 0, -0.35, 0);
        }
        if (isOvercharged() && random.nextInt(3) == 0) {
            level().addParticle(ParticleHelper.ELECTRICITY, getX() + (random.nextDouble() - 0.5) * radius, getY() + 0.3, getZ() + (random.nextDouble() - 0.5) * radius, 0, 0.05, 0);
        }
    }

    @Override
    public boolean shouldRenderAtSqrDistance(double distance) {
        return distance < 96 * 96;
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    protected void readAdditionalSaveData(@NotNull CompoundTag tag) {
        if (tag.hasUUID("Owner")) {
            ownerUUID = tag.getUUID("Owner");
        }
        this.entityData.set(DATA_RADIUS, tag.getFloat("Radius"));
        this.entityData.set(DATA_DURATION, tag.getInt("Duration"));
        this.entityData.set(DATA_OVERCHARGED, tag.getBoolean("Overcharged"));
    }

    @Override
    protected void addAdditionalSaveData(@NotNull CompoundTag tag) {
        if (ownerUUID != null) {
            tag.putUUID("Owner", ownerUUID);
        }
        tag.putFloat("Radius", getRadius());
        tag.putInt("Duration", getDuration());
        tag.putBoolean("Overcharged", isOvercharged());
    }

    @Override
    public @NotNull Packet<ClientGamePacketListener> getAddEntityPacket() {
        return new ClientboundAddEntityPacket(this);
    }
}
