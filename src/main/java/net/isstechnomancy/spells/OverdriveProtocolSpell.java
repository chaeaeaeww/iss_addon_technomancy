package net.isstechnomancy.spells;

import io.redspace.ironsspellbooks.api.config.DefaultConfig;
import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.CastSource;
import io.redspace.ironsspellbooks.api.spells.CastType;
import io.redspace.ironsspellbooks.api.spells.SpellAnimations;
import io.redspace.ironsspellbooks.api.spells.SpellRarity;
import io.redspace.ironsspellbooks.api.util.AnimationHolder;
import io.redspace.ironsspellbooks.api.util.Utils;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.registry.TechEffects;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSchools;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.Level;

import java.util.List;
import java.util.Optional;

/**
 * Instant · Epic · max level 3.
 * Grants Overdrive for 15s + 5s per level. The next Technomancy spell is cast in its upgraded form
 * (see {@link net.isstechnomancy.effect.OverdriveEffect}) and consumes the buff.
 */
public class OverdriveProtocolSpell extends AbstractSpell {
    private final ResourceLocation spellId = ISSTechnomancy.id("overdrive_protocol");

    private final DefaultConfig defaultConfig = new DefaultConfig()
            .setMinRarity(SpellRarity.EPIC)
            .setSchoolResource(TechSchools.TECHNOMANCY_RESOURCE)
            .setMaxLevel(3)
            .setCooldownSeconds(60)
            .build();

    public OverdriveProtocolSpell() {
        this.manaCostPerLevel = 20;
        this.baseSpellPower = 1;
        this.spellPowerPerLevel = 0;
        this.castTime = 0;
        this.baseManaCost = 80;
    }

    @Override
    public List<MutableComponent> getUniqueInfo(int spellLevel, LivingEntity caster) {
        return List.of(Component.translatable("ui.irons_spellbooks.effect_length", Utils.timeFromTicks(getDurationTicks(spellLevel), 1)));
    }

    @Override
    public CastType getCastType() {
        return CastType.INSTANT;
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
        return Optional.empty();
    }

    @Override
    public Optional<SoundEvent> getCastFinishSound() {
        return Optional.of(TechSounds.OVERDRIVE_CAST.get());
    }

    @Override
    public AnimationHolder getCastStartAnimation() {
        return SpellAnimations.SELF_CAST_ANIMATION;
    }

    @Override
    public AnimationHolder getCastFinishAnimation() {
        return AnimationHolder.pass();
    }

    @Override
    public void onCast(Level level, int spellLevel, LivingEntity entity, CastSource castSource, MagicData playerMagicData) {
        entity.addEffect(new MobEffectInstance(TechEffects.OVERDRIVE.get(), getDurationTicks(spellLevel), 0, false, true, true));
        MagicManager.spawnParticles(level, TechParticles.COG_SIGIL.get(), entity.getX(), entity.getY() + 0.05, entity.getZ(), 1, 0, 0, 0, 0, true);
        MagicManager.spawnParticles(level, TechParticles.ARC_MOTE.get(), entity.getX(), entity.getY() + 1, entity.getZ(), 24, 0.5, 0.8, 0.5, 0.08, false);
        MagicManager.spawnParticles(level, TechParticles.BRASS_SPARK.get(), entity.getX(), entity.getY() + 1.2, entity.getZ(), 30, 0.3, 0.3, 0.3, 0.35, false);
        MagicManager.spawnParticles(level, TechParticles.STEAM_PUFF.get(), entity.getX(), entity.getY() + 0.1, entity.getZ(), 14, 0.7, 0.05, 0.7, 0.02, false);
        super.onCast(level, spellLevel, entity, castSource, playerMagicData);
    }

    public int getDurationTicks(int spellLevel) {
        return (15 + 5 * (spellLevel - 1)) * 20;
    }

    @Override
    public boolean shouldAIStopCasting(int spellLevel, Mob mob, LivingEntity target) {
        return false;
    }
}
