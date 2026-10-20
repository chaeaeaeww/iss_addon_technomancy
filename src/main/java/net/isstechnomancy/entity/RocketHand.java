package net.isstechnomancy.entity;

import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.damage.DamageSources;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.entity.boss.TechDragon;
import net.isstechnomancy.registry.TechEffects;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSpells;
import net.isstechnomancy.registry.TechTags;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * Rocket Grab's mechanical hand. Flies out on a cable; the first living entity it touches is latched and reeled back to
 * the owner (players and mob-sized creatures; larger creatures and bosses are only hit and jolted), then stunned.
 * Used by the Rocket Grab spell and by the Mk.II automaton.
 */
public class RocketHand extends Entity implements GeoEntity {
    private static final EntityDataAccessor<Integer> DATA_OWNER = SynchedEntityData.defineId(RocketHand.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_GRABBED = SynchedEntityData.defineId(RocketHand.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> DATA_RETURNING = SynchedEntityData.defineId(RocketHand.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Float> DATA_SCALE = SynchedEntityData.defineId(RocketHand.class, EntityDataSerializers.FLOAT);
    private static final RawAnimation OPEN = RawAnimation.begin().thenLoop("open");
    private static final RawAnimation CLOSED = RawAnimation.begin().thenLoop("closed");
    public static final double SPEED = 1.9;
    public static final double RETURN_SPEED = 1.4;

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private double range = 16;
    private float damage = 4;
    private int stunTicks = 30;
    private int teslaLevel;
    private Vec3 start = Vec3.ZERO;
    private int life;

    public RocketHand(EntityType<? extends RocketHand> type, Level level) {
        super(type, level);
        this.noPhysics = true;
    }

    public RocketHand(Level level, LivingEntity owner, Vec3 from, Vec3 direction, double range, float damage, int stunTicks, float scale) {
        this(TechEntities.ROCKET_HAND.get(), level);
        this.entityData.set(DATA_OWNER, owner.getId());
        this.entityData.set(DATA_SCALE, scale);
        this.range = range;
        this.damage = damage;
        this.stunTicks = stunTicks;
        this.start = from;
        setPos(from.x, from.y, from.z);
        Vec3 velocity = direction.normalize().scale(SPEED);
        setDeltaMovement(velocity);
        faceAlong(velocity);
    }

    public void setTeslaLevel(int teslaLevel) {
        this.teslaLevel = teslaLevel;
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_OWNER, -1);
        this.entityData.define(DATA_GRABBED, -1);
        this.entityData.define(DATA_RETURNING, false);
        this.entityData.define(DATA_SCALE, 1f);
    }

    @Nullable
    public LivingEntity getOwner() {
        return level().getEntity(this.entityData.get(DATA_OWNER)) instanceof LivingEntity living ? living : null;
    }

    @Nullable
    public Entity getGrabbed() {
        int id = this.entityData.get(DATA_GRABBED);
        return id < 0 ? null : level().getEntity(id);
    }

    public boolean isReturning() {
        return this.entityData.get(DATA_RETURNING);
    }

    public float getScale() {
        return this.entityData.get(DATA_SCALE);
    }

    /** Where the cable attaches on the owner. */
    public static Vec3 anchor(LivingEntity owner, float partialTick) {
        return owner.getPosition(partialTick).add(0, owner.getBbHeight() * 0.62, 0);
    }

    private void faceAlong(Vec3 v) {
        double h = v.horizontalDistance();
        setYRot((float) (Mth.atan2(v.x, v.z) * Mth.RAD_TO_DEG));
        setXRot((float) (Mth.atan2(v.y, h) * Mth.RAD_TO_DEG));
        yRotO = getYRot();
        xRotO = getXRot();
    }

    @Override
    public void tick() {
        super.tick();
        LivingEntity owner = getOwner();
        if (owner == null || !owner.isAlive() || owner.level() != level()) {
            if (!level().isClientSide) {
                discard();
            }
            return;
        }
        life++;
        Vec3 pos = position();
        if (!isReturning()) {
            Vec3 next = pos.add(getDeltaMovement());
            if (!level().isClientSide) {
                BlockHitResult blockHit = level().clip(new ClipContext(pos, next, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
                if (blockHit.getType() != HitResult.Type.MISS) {
                    next = blockHit.getLocation();
                }
                EntityHitResult entityHit = ProjectileUtil.getEntityHitResult(level(), this, pos, next,
                        new AABB(pos, next).inflate(0.45 * getScale()), e -> canLatch(owner, e));
                if (entityHit != null) {
                    latch(owner, entityHit.getEntity());
                } else if (blockHit.getType() != HitResult.Type.MISS || next.distanceTo(start) >= range) {
                    startReturn();
                    level().playSound(null, getX(), getY(), getZ(), SoundEvents.CHAIN_HIT, SoundSource.NEUTRAL, 1f, 0.8f);
                }
            }
            setPos(next.x, next.y, next.z);
            if (level().isClientSide && life % 2 == 0) {
                level().addParticle(TechParticles.STEAM_PUFF.get(), getX(), getY(), getZ(), 0, 0.02, 0);
            }
        } else {
            Vec3 home = anchor(owner, 1f);
            Vec3 delta = home.subtract(pos);
            double dist = delta.length();
            Vec3 move = dist < RETURN_SPEED ? delta : delta.scale(RETURN_SPEED / dist);
            setDeltaMovement(move);
            faceAlong(move.scale(-1));
            setPos(pos.x + move.x, pos.y + move.y, pos.z + move.z);
            Entity grabbed = getGrabbed();
            if (!level().isClientSide && grabbed != null && grabbed.isAlive()) {
                grabbed.setPos(getX(), getY() - grabbed.getBbHeight() * 0.5, getZ());
                grabbed.setDeltaMovement(move);
                grabbed.hurtMarked = true;
                grabbed.fallDistance = 0;
            }
            if (!level().isClientSide && (dist < 1.6 + owner.getBbWidth() || life > 80)) {
                release(owner);
            }
        }
        if (!level().isClientSide && life > 120) {
            discard();
        }
    }

    private boolean canLatch(LivingEntity owner, Entity e) {
        return e instanceof LivingEntity living && living.isAlive() && e != owner && !e.isSpectator() && !owner.isAlliedTo(e)
                && !DamageSources.isFriendlyFireBetween(owner, e) && !(e instanceof Player p && p.isCreative());
    }

    /** Players and mob-sized creatures are reeled in; big creatures and bosses are only hit. */
    public static boolean canPull(Entity e) {
        return !(e instanceof TechDragon) && !e.getType().is(TechTags.BOSSES) && e.getBbWidth() <= 1.6 && e.getBbHeight() <= 2.8;
    }

    private void latch(LivingEntity owner, Entity target) {
        if (damage > 0) {
            // the Blitz's own grab still hurts; the player spell passes 0 and only pulls/stuns
            DamageSources.applyDamage(target, damage, TechSpells.ROCKET_GRAB.get().getDamageSource(this, owner));
            net.isstechnomancy.module.TeslaHelper.arc(this, owner, target, damage, teslaLevel);
        }
        level().playSound(null, target.getX(), target.getY(), target.getZ(), SoundEvents.ANVIL_PLACE, SoundSource.NEUTRAL, 0.8f, 1.6f);
        MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, target.getX(), target.getY() + target.getBbHeight() * 0.5, target.getZ(), 12, 0.3, 0.3, 0.3, 0.25, false);
        if (target instanceof LivingEntity living) {
            living.addEffect(new MobEffectInstance(TechEffects.STUNNED.get(), canPull(target) ? stunTicks + 20 : stunTicks / 2, 0), owner);
        }
        if (canPull(target)) {
            this.entityData.set(DATA_GRABBED, target.getId());
        }
        startReturn();
    }

    private void startReturn() {
        this.entityData.set(DATA_RETURNING, true);
    }

    private void release(LivingEntity owner) {
        Entity grabbed = getGrabbed();
        if (grabbed instanceof LivingEntity living && living.isAlive()) {
            Vec3 front = owner.position().add(owner.getLookAngle().multiply(1, 0, 1).normalize().scale(1.4 + owner.getBbWidth() * 0.5));
            living.teleportTo(front.x, owner.getY() + 0.1, front.z);
            living.setDeltaMovement(Vec3.ZERO);
            living.hurtMarked = true;
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, living.getX(), living.getY() + 1, living.getZ(), 10, 0.3, 0.4, 0.3, 0.2, false);
        }
        level().playSound(null, owner.getX(), owner.getY(), owner.getZ(), SoundEvents.PISTON_CONTRACT, SoundSource.NEUTRAL, 1f, 1.2f);
        discard();
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
    }

    @Override
    protected void addAdditionalSaveData(@NotNull CompoundTag tag) {
    }

    @Override
    public @NotNull Packet<ClientGamePacketListener> getAddEntityPacket() {
        return new ClientboundAddEntityPacket(this);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "hand", 2, state -> state.setAndContinue(getGrabbed() != null ? CLOSED : OPEN)));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
