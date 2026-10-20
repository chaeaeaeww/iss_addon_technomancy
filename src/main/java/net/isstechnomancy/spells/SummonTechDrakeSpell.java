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
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.effect.OverdriveEffect;
import net.isstechnomancy.entity.boss.TechDrake;
import net.isstechnomancy.module.ModuleStats;
import net.isstechnomancy.module.StaffModules;
import net.isstechnomancy.registry.TechAnimations;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSchools;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.Optional;

/**
 * Long cast (1.5s) · Legendary · max level 3. Only obtained from the Tech Dragon (never found in random loot).
 * Calls a rideable Tech Drake (~11 blocks long; the boss is 26): HP 120 + 50/level, lifetime 3 min + 1 min/level,
 * about 40% of the boss's damage scaled by spell power. Right-click it to ride (see {@link TechDrake}).
 * Overdrive: an overcharged drake, bigger, 1.3x damage, orange crystals. One drake per caster.
 */
public class SummonTechDrakeSpell extends AbstractSpell {
    private final ResourceLocation spellId = ISSTechnomancy.id("summon_tech_drake");
    private final DefaultConfig defaultConfig = new DefaultConfig()
            .setMinRarity(SpellRarity.LEGENDARY)
            .setSchoolResource(TechSchools.TECHNOMANCY_RESOURCE)
            .setMaxLevel(3)
            .setCooldownSeconds(150)
            .build();

    public SummonTechDrakeSpell() {
        this.manaCostPerLevel = 50;
        this.baseSpellPower = 10;
        this.spellPowerPerLevel = 2;
        this.castTime = 30;
        this.baseManaCost = 200;
    }

    @Override
    public boolean allowLooting() {
        return false;
    }

    @Override
    public List<MutableComponent> getUniqueInfo(int spellLevel, LivingEntity caster) {
        return List.of(
                Component.translatable("ui.irons_spellbooks.hp", getHealth(spellLevel)),
                Component.translatable("ui.iss_technomancy.sentry_lifetime", Utils.stringTruncation(getLifetime(spellLevel) / 20f, 0)),
                Component.translatable("ui.iss_technomancy.drake_power", Utils.stringTruncation(getPower(spellLevel, caster) * 100, 0)));
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
        return Optional.of(TechSounds.TECH_DRAGON_CHARGE.get());
    }

    @Override
    public Optional<SoundEvent> getCastFinishSound() {
        return Optional.of(TechSounds.TECH_DRAGON_ROAR.get());
    }

    @Override
    public AnimationHolder getCastStartAnimation() {
        return TechAnimations.FIELD_CHANNEL;
    }

    @Override
    public AnimationHolder getCastFinishAnimation() {
        return TechAnimations.DEPLOY_SENTRY_FINISH;
    }

    @Override
    public void onServerCastTick(Level level, int spellLevel, LivingEntity entity, @Nullable MagicData playerMagicData) {
        super.onServerCastTick(level, spellLevel, entity, playerMagicData);
        if (entity.tickCount % 5 == 0) {
            MagicManager.spawnParticles(level, ParticleHelper.ELECTRICITY, entity.getX(), entity.getY() + 2.5, entity.getZ(), 6, 1, 0.5, 1, 0.1, false);
        }
    }

    @Override
    public void onCast(Level level, int spellLevel, LivingEntity entity, CastSource castSource, MagicData playerMagicData) {
        boolean overcharged = OverdriveEffect.consume(entity);
        ModuleStats modules = StaffModules.of(entity);
        level.getEntitiesOfClass(TechDrake.class, entity.getBoundingBox().inflate(96), d -> entity.getUUID().equals(d.getOwnerUUID())).forEach(TechDrake::dismiss);
        int health = (int) (getHealth(spellLevel) * modules.constructHealthMultiplier());
        TechDrake drake = new TechDrake(level, entity, getPower(spellLevel, entity) * modules.damageMultiplier(), health, getLifetime(spellLevel), overcharged);
        Vec3 spot = entity.position().add(entity.getLookAngle().multiply(1, 0, 1).normalize().scale(6)).add(0, 3.5, 0);
        drake.moveTo(spot.x, spot.y, spot.z, entity.getYRot(), 0);
        drake.finalizeSpawn((net.minecraft.server.level.ServerLevel) level, level.getCurrentDifficultyAt(drake.blockPosition()),
                net.minecraft.world.entity.MobSpawnType.MOB_SUMMONED, null, null);
        level.addFreshEntity(drake);
        LightningBolt bolt = EntityType.LIGHTNING_BOLT.create(level);
        if (bolt != null) {
            bolt.moveTo(spot.x, spot.y - 2.5, spot.z);
            bolt.setVisualOnly(true);
            level.addFreshEntity(bolt);
        }
        MagicManager.spawnParticles(level, TechParticles.STEAM_PUFF.get(), spot.x, spot.y, spot.z, 20, 1, 0.6, 1, 0.05, false);
        super.onCast(level, spellLevel, entity, castSource, playerMagicData);
    }

    /** 120 / 170 / 220 health. */
    public int getHealth(int spellLevel) {
        return 120 + 50 * (spellLevel - 1);
    }

    /** 3 / 4 / 5 minutes. */
    public int getLifetime(int spellLevel) {
        return (180 + 60 * (spellLevel - 1)) * 20;
    }

    /** 1.0 at base spell power; the drake deals 40% of the boss's damage times this. */
    public float getPower(int spellLevel, @Nullable LivingEntity caster) {
        return getSpellPower(spellLevel, caster) / 10f;
    }

    @Override
    public boolean shouldAIStopCasting(int spellLevel, Mob mob, LivingEntity target) {
        return false;
    }
}
