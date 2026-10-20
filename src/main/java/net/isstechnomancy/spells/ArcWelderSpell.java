package net.isstechnomancy.spells;

import io.redspace.ironsspellbooks.api.config.DefaultConfig;
import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.CastSource;
import io.redspace.ironsspellbooks.api.spells.CastType;
import io.redspace.ironsspellbooks.api.spells.SpellRarity;
import io.redspace.ironsspellbooks.api.util.AnimationHolder;
import io.redspace.ironsspellbooks.api.util.Utils;
import io.redspace.ironsspellbooks.spells.EntityCastData;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.effect.OverdriveEffect;
import net.isstechnomancy.entity.ArcWelderBeam;
import net.isstechnomancy.module.ModuleStats;
import net.isstechnomancy.module.StaffModules;
import net.isstechnomancy.registry.TechAnimations;
import net.isstechnomancy.registry.TechSchools;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.Level;

import java.util.List;
import java.util.Optional;

/**
 * Continuous · Uncommon · max level 8.
 * A 6-block welding arc. Every 10 ticks (the Iron's Spells continuous interval) it deals
 * 1 + spell power × 0.6 damage and applies Slowness I ("Fused"). Spell power = 2 + 1 per level, 80 tick channel.
 * Hitting your own Brass Sentry repairs it, extends its lifetime and overclocks it instead.
 */
public class ArcWelderSpell extends AbstractSpell {
    public static final float RANGE = 6f;
    public static final int SLOW_DURATION_TICKS = 25;
    public static final int OVERDRIVE_FORKS = 2;
    public static final float FORK_RANGE = 4f;
    public static final float FORK_DAMAGE = 0.5f;

    private final ResourceLocation spellId = ISSTechnomancy.id("arc_welder");

    private final DefaultConfig defaultConfig = new DefaultConfig()
            .setMinRarity(SpellRarity.UNCOMMON)
            .setSchoolResource(TechSchools.TECHNOMANCY_RESOURCE)
            .setMaxLevel(8)
            .setCooldownSeconds(10)
            .build();

    public ArcWelderSpell() {
        this.manaCostPerLevel = 1;
        this.baseSpellPower = 2;
        this.spellPowerPerLevel = 1;
        this.castTime = 80;
        this.baseManaCost = 4;
    }

    @Override
    public List<MutableComponent> getUniqueInfo(int spellLevel, LivingEntity caster) {
        return List.of(
                Component.translatable("ui.iss_technomancy.damage_per_pulse", Utils.stringTruncation(getDamage(spellLevel, caster), 2)),
                Component.translatable("ui.irons_spellbooks.distance", Utils.stringTruncation(RANGE, 1))
        );
    }

    @Override
    public CastType getCastType() {
        return CastType.CONTINUOUS;
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
        return Optional.of(TechSounds.ARC_WELDER_START.get());
    }

    @Override
    public Optional<SoundEvent> getCastFinishSound() {
        return Optional.empty();
    }

    @Override
    public AnimationHolder getCastStartAnimation() {
        return TechAnimations.WELDER_CHANNEL;
    }

    @Override
    public AnimationHolder getCastFinishAnimation() {
        return AnimationHolder.none();
    }

    /**
     * Called on the first tick of the cast and then every 10 ticks while channeling.
     */
    @Override
    public void onCast(Level level, int spellLevel, LivingEntity entity, CastSource castSource, MagicData playerMagicData) {
        if (playerMagicData.isCasting()
                && playerMagicData.getCastingSpellId().equals(getSpellId())
                && playerMagicData.getAdditionalCastData() instanceof EntityCastData entityCastData
                && entityCastData.getCastingEntity() instanceof ArcWelderBeam beam
                && !beam.isRemoved()) {
            beam.setDamage(getDamage(spellLevel, entity) * StaffModules.of(entity).damageMultiplier());
            beam.pulse();
        } else {
            ModuleStats modules = StaffModules.of(entity);
            ArcWelderBeam beam = new ArcWelderBeam(level, entity);
            beam.setDamage(getDamage(spellLevel, entity) * modules.damageMultiplier());
            int forks = (OverdriveEffect.consume(entity) ? OVERDRIVE_FORKS : 0) + modules.extraProjectiles();
            beam.setForks(forks);
            beam.setTeslaLevel(modules.teslaJumps());
            level.addFreshEntity(beam);
            playerMagicData.setAdditionalCastData(new EntityCastData(beam));
            beam.pulse();
        }
        level.playSound(null, entity.getX(), entity.getY(), entity.getZ(), TechSounds.ARC_WELDER_LOOP.get(), SoundSource.PLAYERS, 0.6f, 0.9f + entity.getRandom().nextFloat() * 0.2f);
        super.onCast(level, spellLevel, entity, castSource, playerMagicData);
    }

    @Override
    public void onServerCastComplete(Level level, int spellLevel, LivingEntity entity, MagicData playerMagicData, boolean cancelled) {
        level.playSound(null, entity.getX(), entity.getY(), entity.getZ(), TechSounds.ARC_WELDER_END.get(), SoundSource.PLAYERS, 0.8f, 1f);
        // Resetting the casting state resets the EntityCastData, which discards the beam entity.
        super.onServerCastComplete(level, spellLevel, entity, playerMagicData, cancelled);
    }

    public float getDamage(int spellLevel, LivingEntity caster) {
        return (1 + getSpellPower(spellLevel, caster) * 0.6f) * 0.75f; // 1.4: -25%
    }

    @Override
    public boolean shouldAIStopCasting(int spellLevel, Mob mob, LivingEntity target) {
        return mob.distanceToSqr(target) > (RANGE * RANGE) * 1.2;
    }
}
