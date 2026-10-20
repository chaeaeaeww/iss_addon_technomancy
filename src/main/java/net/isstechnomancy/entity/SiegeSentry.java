package net.isstechnomancy.entity;

import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;

/**
 * Overdriven Brass Sentry, 1.10 "Hextech Grand Cannon": a heavy fixed emplacement with one long hextech-ringed barrel
 * that fires slow, heavy explosive shells (x1.8 damage, a 3.5 block blast, 28 block reach). Shares ownership,
 * lifetime, Arc Welder synergy and targeting with {@link BrassSentry}.
 */
public class SiegeSentry extends BrassSentry {
    public static final double SIEGE_TARGET_RANGE = 28;
    public static final int SIEGE_FIRE_INTERVAL = 14;
    public static final int SIEGE_OVERCLOCK_FIRE_INTERVAL = 10;
    public static final float SHELL_RADIUS = 3.5f;
    public static final float SHELL_DAMAGE_MULTIPLIER = 1.8f;
    /** Barrel length from the turret axis (model px). */
    private static final double BARREL_PX = 24;
    public static final int SIEGE_SPAWN_TICKS = 32;
    /** Render scale (model is 18 px tall, so ~3.2 blocks); the entity type hitbox is sized to match. */
    public static final float RENDER_SCALE = 2.85f;
    /** Barrel axis height as a fraction of the hitbox height (barrels sit 10 px up the 18 px model). */
    private static final float EYE_FRACTION = 0.56f;

    private static final RawAnimation ANIM_SHOOT = RawAnimation.begin().thenPlay("shoot");

    public SiegeSentry(EntityType<? extends SiegeSentry> entityType, Level level) {
        super(entityType, level);
    }

    public SiegeSentry(Level level, LivingEntity owner, float shellDamage, int maxHealth, int lifetimeTicks) {
        super(TechEntities.SIEGE_SENTRY.get(), level, owner, shellDamage, maxHealth, lifetimeTicks);
    }

    public static AttributeSupplier.Builder createSiegeAttributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 36)
                .add(Attributes.ARMOR, 10)
                .add(Attributes.ARMOR_TOUGHNESS, 2)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1)
                .add(Attributes.MOVEMENT_SPEED, 0)
                .add(Attributes.FOLLOW_RANGE, SIEGE_TARGET_RANGE);
    }

    @Override
    protected float getStandingEyeHeight(@NotNull Pose pose, @NotNull EntityDimensions dimensions) {
        return dimensions.height * EYE_FRACTION;
    }

    @Override
    protected double getTargetRange() {
        return SIEGE_TARGET_RANGE;
    }

    @Override
    protected int getFireInterval() {
        return isOverclocked() ? SIEGE_OVERCLOCK_FIRE_INTERVAL : SIEGE_FIRE_INTERVAL;
    }

    @Override
    protected void fireAt(LivingEntity target, LivingEntity owner) {
        Vec3 look = getViewVector(1f);
        // the one barrel runs along the axis and ends 24 px in front of it (model space)
        Vec3 muzzle = getEyePosition().add(look.scale(BARREL_PX / 16.0 * RENDER_SCALE));
        Vec3 aim = target.getBoundingBox().getCenter().add(0, target.getBbHeight() * 0.15, 0);
        Vec3 direction = aim.subtract(muzzle).normalize();

        int count = 1 + getExtraBolts();
        for (int i = 0; i < count; i++) {
            float yaw = (i - (count - 1) / 2f) * 6f * net.minecraft.util.Mth.DEG_TO_RAD;
            SiegeShell shell = new SiegeShell(level(), owner);
            shell.setPos(muzzle.x, muzzle.y - shell.getBbHeight() * 0.5, muzzle.z);
            shell.shoot(direction.yRot(yaw));
            shell.setDamage(getBoltDamage() * SHELL_DAMAGE_MULTIPLIER);
            shell.setExplosionRadius(SHELL_RADIUS);
            shell.setTeslaLevel(getTeslaLevel());
            level().addFreshEntity(shell);
        }

        triggerAnim("action", "shoot");
        level().playSound(null, getX(), getY(), getZ(), TechSounds.SIEGE_SENTRY_SHOOT.get(), SoundSource.NEUTRAL, 1.6f, isOverclocked() ? 0.85f : 0.7f);
        level().playSound(null, getX(), getY(), getZ(), net.minecraft.sounds.SoundEvents.GENERIC_EXPLODE, SoundSource.NEUTRAL, 0.6f, 1.4f);
        MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), muzzle.x, muzzle.y, muzzle.z, 10, 0.2, 0.2, 0.2, 0.05, false);
        MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), muzzle.x, muzzle.y, muzzle.z, 12, 0.15, 0.15, 0.15, 0.3, false);
        MagicManager.spawnParticles(level(), net.minecraft.core.particles.ParticleTypes.EXPLOSION, muzzle.x, muzzle.y, muzzle.z, 1, 0, 0, 0, 0, false);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 4, state -> {
            if (isDespawning()) {
                return state.setAndContinue(ANIM_DESPAWN);
            }
            if (tickCount < SIEGE_SPAWN_TICKS) {
                return state.setAndContinue(ANIM_SPAWN);
            }
            return state.setAndContinue(isOverclocked() ? ANIM_OVERCLOCK : ANIM_IDLE);
        }));
        controllers.add(new AnimationController<>(this, "action", 0, state -> PlayState.STOP)
                .triggerableAnim("shoot", ANIM_SHOOT));
    }

    @Override
    protected int assembleLockTick() {
        return 20;
    }

    @Override
    protected Vec3 ventPosition() {
        return position().add(0, 16.5 / 16.0 * RENDER_SCALE, 0);
    }
}
