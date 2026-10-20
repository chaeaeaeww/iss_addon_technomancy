package net.isstechnomancy.spells;

import io.redspace.ironsspellbooks.api.config.DefaultConfig;
import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.CastSource;
import io.redspace.ironsspellbooks.api.spells.CastType;
import io.redspace.ironsspellbooks.api.spells.SpellRarity;
import io.redspace.ironsspellbooks.api.util.AnimationHolder;
import io.redspace.ironsspellbooks.api.util.Utils;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.effect.OverdriveEffect;
import net.isstechnomancy.entity.RocketHand;
import net.isstechnomancy.module.ModuleStats;
import net.isstechnomancy.module.StaffModules;
import net.isstechnomancy.registry.TechAnimations;
import net.isstechnomancy.registry.TechSchools;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.Optional;

/**
 * Instant · Uncommon · max level 5. Launches a mechanical fist on a cable (Blitzcrank's Rocket Grab): the first
 * creature it touches is yanked back in front of the caster and short-circuited (stunned). Bosses and big creatures
 * are only jolted. Range 16 + 2/level, no damage, stun 1s + 0.25s/level.
 * Overdrive: bigger fist, 1.5x range, longer stun. Splitter modules launch extra fists in a fan.
 */
public class RocketGrabSpell extends AbstractSpell {
    private final ResourceLocation spellId = ISSTechnomancy.id("rocket_grab");
    private final DefaultConfig defaultConfig = new DefaultConfig()
            .setMinRarity(SpellRarity.UNCOMMON)
            .setSchoolResource(TechSchools.TECHNOMANCY_RESOURCE)
            .setMaxLevel(5)
            .setCooldownSeconds(12)
            .build();

    public RocketGrabSpell() {
        this.manaCostPerLevel = 5;
        this.baseSpellPower = 6;
        this.spellPowerPerLevel = 1;
        this.castTime = 0;
        this.baseManaCost = 30;
    }

    @Override
    public List<MutableComponent> getUniqueInfo(int spellLevel, LivingEntity caster) {
        return List.of(
                Component.translatable("ui.irons_spellbooks.distance", Utils.stringTruncation(getRange(spellLevel), 1)),
                Component.translatable("ui.iss_technomancy.stun_duration", Utils.stringTruncation(getStunTicks(spellLevel) / 20f, 2)));
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
        return Optional.of(SoundEvents.PISTON_EXTEND);
    }

    @Override
    public AnimationHolder getCastStartAnimation() {
        return TechAnimations.ROCKET_GRAB;
    }

    @Override
    public AnimationHolder getCastFinishAnimation() {
        return AnimationHolder.pass();
    }

    @Override
    public void onCast(Level level, int spellLevel, LivingEntity entity, CastSource castSource, MagicData playerMagicData) {
        boolean overdrive = OverdriveEffect.consume(entity);
        ModuleStats modules = StaffModules.of(entity);
        int hands = 1 + Math.min(2, modules.extraProjectiles());
        double range = getRange(spellLevel) * (overdrive ? 1.5 : 1.0);
        // 1.4: the grab only pulls and stuns, it deals no damage
        float damage = 0f;
        int stun = (int) (getStunTicks(spellLevel) * (overdrive ? 1.6f : 1f));
        float scale = (overdrive ? 1.5f : 1f) * (0.6f + 0.4f * modules.sizeMultiplier());
        Vec3 look = entity.getLookAngle();
        Vec3 origin = entity.getEyePosition().add(0, -0.35, 0).add(look.scale(0.7));
        for (int i = 0; i < hands; i++) {
            float yaw = (i - (hands - 1) / 2f) * 12f * Mth.DEG_TO_RAD;
            RocketHand hand = new RocketHand(level, entity, origin, look.yRot(yaw), range, damage, stun, scale);
            hand.setTeslaLevel(modules.teslaJumps());
            level.addFreshEntity(hand);
        }
        level.playSound(null, entity.getX(), entity.getY(), entity.getZ(), SoundEvents.FIREWORK_ROCKET_LAUNCH, entity.getSoundSource(), 1f, 0.7f);
        super.onCast(level, spellLevel, entity, castSource, playerMagicData);
    }

    public double getRange(int spellLevel) {
        return 16 + 2 * (spellLevel - 1);
    }

    public int getStunTicks(int spellLevel) {
        return 20 + 5 * (spellLevel - 1);
    }

    @Override
    public boolean shouldAIStopCasting(int spellLevel, Mob mob, LivingEntity target) {
        return mob.distanceToSqr(target) > getRange(spellLevel) * getRange(spellLevel);
    }
}
