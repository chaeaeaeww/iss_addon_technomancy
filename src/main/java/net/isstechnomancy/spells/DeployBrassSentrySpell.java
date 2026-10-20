package net.isstechnomancy.spells;

import io.redspace.ironsspellbooks.api.config.DefaultConfig;
import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.CastSource;
import io.redspace.ironsspellbooks.api.spells.CastType;
import io.redspace.ironsspellbooks.api.spells.SpellRarity;
import io.redspace.ironsspellbooks.api.util.AnimationHolder;
import io.redspace.ironsspellbooks.api.util.Utils;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.effect.OverdriveEffect;
import net.isstechnomancy.entity.SiegeSentry;
import net.isstechnomancy.entity.BrassSentry;
import net.isstechnomancy.module.ModuleStats;
import net.isstechnomancy.module.StaffModules;
import net.isstechnomancy.registry.TechAnimations;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSchools;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.Optional;

/**
 * Long Cast (1.5s) · Rare · max level 5.
 * Deploys a stationary Brass Sentry up to 8 blocks away that fires arcane bolts at hostiles within 16 blocks.
 * Bolt damage = spell power × 0.1875 with spell power = 10 + 3 per level (1.9 / 3.0 / 4.1 at levels 1 / 3 / 5).
 * HP = 20 + 6 per level, lifetime = 15s + 3s per level. One sentry per caster; recasting replaces it.
 */
public class DeployBrassSentrySpell extends AbstractSpell {
    public static final float PLACE_RANGE = 8f;
    public static final float SIEGE_DAMAGE = 1.5f;
    public static final float SIEGE_HEALTH = 1.8f;
    public static final float SIEGE_LIFETIME = 1.25f;
    /** Assembler modules add up to this many extra sentries. */
    public static final int MAX_EXTRA_SENTRIES = 3;

    private final ResourceLocation spellId = ISSTechnomancy.id("deploy_brass_sentry");

    private final DefaultConfig defaultConfig = new DefaultConfig()
            .setMinRarity(SpellRarity.RARE)
            .setSchoolResource(TechSchools.TECHNOMANCY_RESOURCE)
            .setMaxLevel(5)
            .setCooldownSeconds(45)
            .build();

    public DeployBrassSentrySpell() {
        this.manaCostPerLevel = 15;
        this.baseSpellPower = 10;
        this.spellPowerPerLevel = 3;
        this.castTime = 30;
        this.baseManaCost = 60;
    }

    @Override
    public List<MutableComponent> getUniqueInfo(int spellLevel, LivingEntity caster) {
        return List.of(
                Component.translatable("ui.iss_technomancy.bolt_damage", Utils.stringTruncation(getBoltDamage(spellLevel, caster), 2)),
                Component.translatable("ui.irons_spellbooks.hp", getSentryHealth(spellLevel)),
                Component.translatable("ui.iss_technomancy.sentry_lifetime", Utils.stringTruncation(getLifetimeTicks(spellLevel) / 20f, 1))
        );
    }

    @Override
    public CastType getCastType() {
        return CastType.LONG;
    }

    @Override
    public DefaultConfig getDefaultConfig() {
        return defaultConfig;
    }

    @Override
    public ResourceLocation getSpellResource() {
        return spellId;
    }

    @Override
    public Optional<SoundEvent> getCastStartSound() {
        return Optional.of(TechSounds.SENTRY_WINDUP.get());
    }

    @Override
    public Optional<SoundEvent> getCastFinishSound() {
        return Optional.of(TechSounds.SENTRY_DEPLOY.get());
    }

    @Override
    public AnimationHolder getCastStartAnimation() {
        return TechAnimations.DEPLOY_SENTRY;
    }

    @Override
    public AnimationHolder getCastFinishAnimation() {
        return TechAnimations.DEPLOY_SENTRY_FINISH;
    }

    /**
     * Draws the spinning cog sigil under the caster and at the deploy point while the long cast charges.
     */
    @Override
    public void onServerCastTick(Level level, int spellLevel, LivingEntity entity, @Nullable MagicData playerMagicData) {
        super.onServerCastTick(level, spellLevel, entity, playerMagicData);
        if (entity.tickCount % 10 == 0) {
            MagicManager.spawnParticles(level, TechParticles.COG_SIGIL.get(), entity.getX(), entity.getY() + 0.05, entity.getZ(), 1, 0, 0, 0, 0, true);
            Vec3 spot = findDeployPosition(level, entity);
            MagicManager.spawnParticles(level, TechParticles.COG_SIGIL.get(), spot.x, spot.y + 0.05, spot.z, 1, 0, 0, 0, 0, true);
        }
        if (entity.tickCount % 4 == 0) {
            MagicManager.spawnParticles(level, TechParticles.BRASS_SPARK.get(), entity.getX(), entity.getY() + 0.2, entity.getZ(), 2, 0.4, 0.05, 0.4, 0.05, false);
        }
    }

    @Override
    public void onCast(Level level, int spellLevel, LivingEntity entity, CastSource castSource, MagicData playerMagicData) {
        // One sentry per caster: retire the previous one before deploying a new one.
        level.getEntitiesOfClass(BrassSentry.class, entity.getBoundingBox().inflate(BrassSentry.MAX_OWNER_DISTANCE),
                        sentry -> entity.getUUID().equals(sentry.getOwnerUUID()))
                .forEach(BrassSentry::beginDespawn);

        boolean siege = OverdriveEffect.consume(entity);
        ModuleStats modules = StaffModules.of(entity);
        int count = 1 + Math.min(MAX_EXTRA_SENTRIES, modules.extraConstructs());
        Vec3 primary = findDeployPosition(level, entity);
        Vec3 side = new Vec3(-entity.getLookAngle().z, 0, entity.getLookAngle().x).normalize().scale(siege ? 3.6 : 2.2);
        float damage = getBoltDamage(spellLevel, entity) * modules.damageMultiplier();
        int health = (int) (getSentryHealth(spellLevel) * modules.constructHealthMultiplier());
        for (int i = 0; i < count; i++) {
            // primary, right, left, behind
            Vec3 offset = switch (i) {
                case 1 -> side;
                case 2 -> side.scale(-1);
                case 3 -> entity.getLookAngle().multiply(1, 0, 1).normalize().scale(siege ? -3.6 : -2.5);
                default -> Vec3.ZERO;
            };
            Vec3 spot = i == 0 ? primary : Utils.moveToRelativeGroundLevel(level, primary.add(offset), 3, 6);
            BrassSentry sentry = siege
                    ? new SiegeSentry(level, entity, damage * SIEGE_DAMAGE, (int) (health * SIEGE_HEALTH), (int) (getLifetimeTicks(spellLevel) * SIEGE_LIFETIME))
                    : new BrassSentry(level, entity, damage, health, getLifetimeTicks(spellLevel));
            sentry.setModules(modules.extraProjectiles(), modules.teslaJumps());
            sentry.moveTo(spot.x, spot.y, spot.z, entity.getYRot(), 0);
            sentry.setYBodyRot(entity.getYRot());
            sentry.setYHeadRot(entity.getYRot());
            level.addFreshEntity(sentry);
            MagicManager.spawnParticles(level, TechParticles.STEAM_PUFF.get(), spot.x, spot.y + 0.3, spot.z, 12, 0.4, 0.2, 0.4, 0.02, false);
            MagicManager.spawnParticles(level, TechParticles.BRASS_SPARK.get(), spot.x, spot.y + 0.5, spot.z, 20, 0.3, 0.3, 0.3, 0.2, false);
        }
        super.onCast(level, spellLevel, entity, castSource, playerMagicData);
    }

    /**
     * Raycasts up to {@link #PLACE_RANGE} blocks along the caster's view and settles the result onto the ground.
     */
    public static Vec3 findDeployPosition(Level level, LivingEntity caster) {
        Vec3 look = caster.getLookAngle();
        Vec3 start = caster.getEyePosition();
        Vec3 end = start.add(look.scale(PLACE_RANGE));
        BlockHitResult hit = level.clip(new ClipContext(start, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, caster));
        Vec3 spot;
        if (hit.getType() == HitResult.Type.MISS) {
            spot = end;
        } else if (hit.getDirection() == Direction.UP) {
            spot = hit.getLocation();
        } else {
            // Hit a wall or ceiling: back off so the sentry does not clip into it.
            spot = hit.getLocation().subtract(look.scale(0.6));
        }
        return Utils.moveToRelativeGroundLevel(level, spot, 3, 6);
    }

    public float getBoltDamage(int spellLevel, @Nullable LivingEntity caster) {
        return getSpellPower(spellLevel, caster) * 0.1875f; // 1.4: -25%
    }

    public int getSentryHealth(int spellLevel) {
        return 20 + 6 * (spellLevel - 1);
    }

    public int getLifetimeTicks(int spellLevel) {
        return (15 + 3 * (spellLevel - 1)) * 20;
    }

    @Override
    public boolean shouldAIStopCasting(int spellLevel, Mob mob, LivingEntity target) {
        return false;
    }
}
