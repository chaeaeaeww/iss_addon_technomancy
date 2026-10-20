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
import net.isstechnomancy.entity.GearProjectile;
import net.isstechnomancy.module.ModuleStats;
import net.isstechnomancy.module.StaffModules;
import net.isstechnomancy.registry.TechAnimations;
import net.isstechnomancy.registry.TechSchools;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.Optional;

/**
 * Instant · Common · max level 10.
 * Fires a fan of brass gears (±6° spread) that each ricochet off one block surface.
 * Damage per gear = spell power × 0.35, spell power = 8 + 1 per level.
 */
public class GearBarrageSpell extends AbstractSpell {
    public static final int GEAR_COUNT = 3;
    public static final float SPREAD_DEGREES = 6f;
    public static final int BLOCK_BOUNCES = 1;
    public static final int OVERDRIVE_GEAR_COUNT = 5;
    public static final int OVERDRIVE_BLOCK_BOUNCES = 2;
    public static final float OVERDRIVE_DAMAGE = 1.25f;

    private final ResourceLocation spellId = ISSTechnomancy.id("gear_barrage");

    private final DefaultConfig defaultConfig = new DefaultConfig()
            .setMinRarity(SpellRarity.COMMON)
            .setSchoolResource(TechSchools.TECHNOMANCY_RESOURCE)
            .setMaxLevel(10)
            .setCooldownSeconds(2)
            .build();

    public GearBarrageSpell() {
        this.manaCostPerLevel = 2;
        this.baseSpellPower = 8;
        this.spellPowerPerLevel = 1;
        this.castTime = 0;
        this.baseManaCost = 15;
    }

    @Override
    public List<MutableComponent> getUniqueInfo(int spellLevel, LivingEntity caster) {
        return List.of(
                Component.translatable("ui.iss_technomancy.damage_per_gear", Utils.stringTruncation(getDamage(spellLevel, caster), 2)),
                Component.translatable("ui.irons_spellbooks.projectile_count", GEAR_COUNT)
        );
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
        return Optional.of(TechSounds.GEAR_BARRAGE_CAST.get());
    }

    @Override
    public AnimationHolder getCastStartAnimation() {
        return TechAnimations.GEAR_FLICK;
    }

    @Override
    public AnimationHolder getCastFinishAnimation() {
        return AnimationHolder.pass();
    }

    @Override
    public void onCast(Level level, int spellLevel, LivingEntity entity, CastSource castSource, MagicData playerMagicData) {
        Vec3 look = entity.getLookAngle();
        Vec3 origin = entity.getEyePosition().add(0, -0.15, 0).add(look.scale(0.4));
        boolean overdrive = OverdriveEffect.consume(entity);
        ModuleStats modules = StaffModules.of(entity);
        int count = (overdrive ? OVERDRIVE_GEAR_COUNT : GEAR_COUNT) + modules.extraProjectiles();
        float damage = getDamage(spellLevel, entity) * (overdrive ? OVERDRIVE_DAMAGE : 1f) * modules.damageMultiplier();
        float spread = Math.min(SPREAD_DEGREES, 48f / Math.max(1, count - 1));
        for (int i = 0; i < count; i++) {
            float yawOffset = (i - (count - 1) / 2f) * spread * Mth.DEG_TO_RAD;
            Vec3 direction = look.yRot(yawOffset);
            GearProjectile gear = new GearProjectile(level, entity);
            gear.setPos(origin.x, origin.y - gear.getBbHeight() * 0.5, origin.z);
            gear.shoot(direction);
            gear.setDamage(damage);
            gear.setScale(modules.sizeMultiplier());
            gear.setTeslaLevel(modules.teslaJumps());
            gear.setBlockBounces(overdrive ? OVERDRIVE_BLOCK_BOUNCES : BLOCK_BOUNCES);
            if (overdrive) {
                gear.setPierceLevel(1);
            }
            level.addFreshEntity(gear);
        }
        super.onCast(level, spellLevel, entity, castSource, playerMagicData);
    }

    public float getDamage(int spellLevel, LivingEntity caster) {
        return getSpellPower(spellLevel, caster) * 0.2625f; // 1.4: -25%
    }

    @Override
    public boolean shouldAIStopCasting(int spellLevel, Mob mob, LivingEntity target) {
        return mob.distanceToSqr(target) > 14 * 14;
    }
}
