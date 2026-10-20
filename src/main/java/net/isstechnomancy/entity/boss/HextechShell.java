package net.isstechnomancy.entity.boss;

import io.redspace.ironsspellbooks.api.registry.SchoolRegistry;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.particle.ShockwaveParticleOptions;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.core.particles.ParticleTypes;
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
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Explosion;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.ToolActions;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import org.joml.Vector3f;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * The Tech Dragon's last act: hextech plates fly in from all around and lock into a sphere around its curled-up body
 * (3 s), the light inside builds and leaks through the seams (3 s), then it bursts.
 *
 * <p>The blast reaches {@value #BLAST_RADIUS} blocks. 1.9: within {@value #KILL_RADIUS} blocks it kills anything (its
 * own damage type ignores armour and protection enchantments, and it is sized on the victim's max health, so other
 * bosses die too); from there to the edge it falls off but still hurts badly. Raising a shield toward it saves its
 * holder (a small hit) but the shield is destroyed. Terrain is not damaged. The dragon's loot drops once the shell is gone.</p>
 */
public class HextechShell extends Entity implements GeoEntity {
    public static final float SCALE = 2.0f;
    /** Sphere radius in blocks (model 72 px at scale 2). */
    public static final double RADIUS = 9.0;
    public static final int ASSEMBLE = 60;
    public static final int BURST = 120;
    public static final int LIFETIME = 140;
    public static final double BLAST_RADIUS = 40;
    public static final float BLAST_DAMAGE = 80f;
    public static final double KILL_RADIUS = 20;
    public static final net.minecraft.resources.ResourceKey<net.minecraft.world.damagesource.DamageType> HEXTECH_BLAST =
            net.minecraft.resources.ResourceKey.create(net.minecraft.core.registries.Registries.DAMAGE_TYPE, net.isstechnomancy.ISSTechnomancy.id("hextech_blast"));

    private static final EntityDataAccessor<Integer> DATA_AGE = SynchedEntityData.defineId(HextechShell.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_DRAGON = SynchedEntityData.defineId(HextechShell.class, EntityDataSerializers.INT);
    public static final java.util.List<String> ANIMATION_NAMES = DragonAnimationNames.SHELL;
    private static final RawAnimation ANIM_ASSEMBLE = RawAnimation.begin().thenPlayAndHold("assemble");
    private static final RawAnimation ANIM_CHARGE = RawAnimation.begin().thenLoop("charge");
    private static final RawAnimation ANIM_BURST = RawAnimation.begin().thenPlayAndHold("burst");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    public HextechShell(EntityType<? extends HextechShell> type, Level level) {
        super(type, level);
        this.noCulling = true;
        this.noPhysics = true;
        setNoGravity(true);
    }

    public HextechShell(Level level, TechDragon dragon) {
        this(TechEntities.HEXTECH_SHELL.get(), level);
        this.entityData.set(DATA_DRAGON, dragon.getId());
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_AGE, 0);
        this.entityData.define(DATA_DRAGON, -1);
    }

    public int getAge() {
        return this.entityData.get(DATA_AGE);
    }

    public Vec3 centre() {
        return position().add(0, RADIUS, 0);
    }

    /** Camera shake for players nearby (read by CameraShakeHandler). */
    public int getShake() {
        int age = getAge();
        if (age >= BURST && age < BURST + 20) {
            return 40;
        }
        return age > ASSEMBLE ? 6 + (age - ASSEMBLE) / 6 : 0;
    }

    @Nullable
    private TechDragon dragon() {
        Entity e = level().getEntity(this.entityData.get(DATA_DRAGON));
        return e instanceof TechDragon d ? d : null;
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide) {
            clientTick();
            return;
        }
        int age = getAge() + 1;
        this.entityData.set(DATA_AGE, age);
        Vec3 c = centre();
        if (age < ASSEMBLE && age % 4 == 0) {
            level().playSound(null, c.x, c.y, c.z, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 3f, 0.6f + random.nextFloat() * 0.4f);
        }
        if (age == ASSEMBLE) {
            level().playSound(null, c.x, c.y, c.z, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 6f, 0.5f);
        }
        if (age > ASSEMBLE && age < BURST && age % 10 == 0) {
            level().playSound(null, c.x, c.y, c.z, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 6f, 0.6f + (age - ASSEMBLE) / 60f);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRICITY, c.x, c.y, c.z, 20, RADIUS * 0.7, RADIUS * 0.7, RADIUS * 0.7, 0.3, true);
        }
        if (age == BURST - 16) {
            level().playSound(null, c.x, c.y, c.z, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 8f, 0.5f);
        }
        if (age == BURST) {
            explode();
        }
        if (age >= LIFETIME) {
            discard();
        }
    }

    private void clientTick() {
        int age = getAge();
        Vec3 c = centre();
        if (age > ASSEMBLE && age < BURST) {
            for (int i = 0; i < 3; i++) {
                double a = random.nextDouble() * Math.PI * 2, b = random.nextDouble() * Math.PI;
                double r = RADIUS * 1.02;
                level().addParticle(ParticleTypes.END_ROD, c.x + Math.cos(a) * Math.sin(b) * r, c.y + Math.cos(b) * r, c.z + Math.sin(a) * Math.sin(b) * r,
                        Math.cos(a) * Math.sin(b) * 0.2, Math.cos(b) * 0.2, Math.sin(a) * Math.sin(b) * 0.2);
            }
        }
    }

    private void explode() {
        Vec3 c = centre();
        TechDragon dragon = dragon();
        Entity cause = dragon != null ? dragon : this;
        level().playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE, SoundSource.HOSTILE, 10f, 0.5f);
        level().playSound(null, c.x, c.y, c.z, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 10f, 0.6f);
        level().playSound(null, c.x, c.y, c.z, TechSounds.TECH_DRAGON_DEATH.get(), SoundSource.HOSTILE, 8f, 0.6f);
        Vector3f color = SchoolRegistry.LIGHTNING.get().getTargetingColor();
        for (int k = 1; k <= 3; k++) {
            MagicManager.spawnParticles(level(), new ShockwaveParticleOptions(color, (float) -(BLAST_RADIUS * k / 3.0), true), c.x, c.y - RADIUS + 0.5, c.z, 1, 0, 0, 0, 0, true);
        }
        MagicManager.spawnParticles(level(), ParticleTypes.EXPLOSION_EMITTER, c.x, c.y, c.z, 8, RADIUS, RADIUS * 0.6, RADIUS, 0, true);
        MagicManager.spawnParticles(level(), ParticleTypes.FLASH, c.x, c.y, c.z, 6, 2, 2, 2, 0, true);
        MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, c.x, c.y, c.z, 300, RADIUS, RADIUS, RADIUS, 1.2, true);
        MagicManager.spawnParticles(level(), ParticleTypes.END_ROD, c.x, c.y, c.z, 200, RADIUS * 0.5, RADIUS * 0.5, RADIUS * 0.5, 1.0, true);
        for (int i = 0; i < 12; i++) {
            double a = i * Math.PI / 6;
            double r = 12 + random.nextDouble() * 20;
            LightningBolt bolt = EntityType.LIGHTNING_BOLT.create(level());
            if (bolt != null) {
                double x = c.x + Math.cos(a) * r, z = c.z + Math.sin(a) * r;
                bolt.moveTo(x, level().getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, Mth.floor(x), Mth.floor(z)), z);
                bolt.setVisualOnly(true);
                level().addFreshEntity(bolt);
            }
        }
        DamageSource source = new DamageSource(level().registryAccess().registryOrThrow(net.minecraft.core.registries.Registries.DAMAGE_TYPE)
                .getHolderOrThrow(HEXTECH_BLAST), this, cause instanceof LivingEntity l ? l : null);
        for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(BLAST_RADIUS), e -> e != dragon && e.isAlive())) {
            if (victim instanceof Player p && (p.isCreative() || p.isSpectator())) {
                continue;
            }
            double d = victim.getBoundingBox().getCenter().distanceTo(c);
            if (d > BLAST_RADIUS) {
                continue;
            }
            float damage;
            if (d <= KILL_RADIUS) {
                // lethal: more than it can take whatever its armour, absorption or size
                damage = victim.getMaxHealth() * 4f + victim.getAbsorptionAmount() + 200f;
            } else {
                double k = (d - KILL_RADIUS) / (BLAST_RADIUS - KILL_RADIUS);
                float seen = Math.max(0.5f, Explosion.getSeenPercent(c, victim));
                damage = (float) Mth.lerp(k, 60, 14) * seen;
            }
            if (blocksWithShield(victim, c)) {
                breakShield(victim);
                damage = Math.min(damage, 6f);
            }
            victim.invulnerableTime = 0;
            if (damage > 0.5f) {
                victim.hurt(source, damage);
            }
            Vec3 push = victim.position().subtract(c).normalize().scale(2.6 * (1 - d / BLAST_RADIUS) + 0.4);
            victim.setDeltaMovement(victim.getDeltaMovement().add(push.x, Math.max(0.4, push.y + 0.5), push.z));
            victim.hurtMarked = true;
        }
        if (dragon != null) {
            dragon.releaseLoot();
            dragon.discard();
        }
    }

    /** Facing the blast with a raised shield. */
    private static boolean blocksWithShield(LivingEntity victim, Vec3 c) {
        if (!victim.isBlocking()) {
            return false;
        }
        ItemStack use = victim.getUseItem();
        if (use.isEmpty() || !use.canPerformAction(ToolActions.SHIELD_BLOCK)) {
            return false;
        }
        Vec3 look = victim.getViewVector(1f).multiply(1, 0, 1).normalize();
        Vec3 to = c.subtract(victim.position()).multiply(1, 0, 1).normalize();
        return look.dot(to) > 0.0;
    }

    private static void breakShield(LivingEntity victim) {
        ItemStack use = victim.getUseItem();
        net.minecraft.world.InteractionHand hand = victim.getUsedItemHand();
        victim.stopUsingItem();
        victim.broadcastBreakEvent(hand);
        if (victim instanceof Player p) {
            p.getCooldowns().addCooldown(use.getItem(), 100);
        }
        use.shrink(use.getCount());
        victim.level().playSound(null, victim.getX(), victim.getY(), victim.getZ(), SoundEvents.SHIELD_BREAK, SoundSource.PLAYERS, 1.5f, 0.8f);
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public boolean hurt(@NotNull DamageSource source, float amount) {
        return false;
    }

    @Override
    public boolean shouldRenderAtSqrDistance(double distance) {
        return distance < 256 * 256;
    }

    @Override
    protected void readAdditionalSaveData(@NotNull CompoundTag tag) {
    }

    @Override
    protected void addAdditionalSaveData(@NotNull CompoundTag tag) {
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    public @NotNull Packet<ClientGamePacketListener> getAddEntityPacket() {
        return new ClientboundAddEntityPacket(this);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 0, state -> {
            int age = getAge();
            return state.setAndContinue(age < ASSEMBLE ? ANIM_ASSEMBLE : age < BURST ? ANIM_CHARGE : ANIM_BURST);
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
