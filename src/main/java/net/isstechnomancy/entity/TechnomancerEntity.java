package net.isstechnomancy.entity;

import io.redspace.ironsspellbooks.entity.mobs.abstract_spell_casting_mob.AbstractSpellCastingMob;
import io.redspace.ironsspellbooks.entity.mobs.abstract_spell_casting_mob.NeutralWizard;
import io.redspace.ironsspellbooks.entity.mobs.goals.FocusOnTradingPlayerGoal;
import io.redspace.ironsspellbooks.entity.mobs.goals.PatrolNearLocationGoal;
import io.redspace.ironsspellbooks.entity.mobs.goals.SpellBarrageGoal;
import io.redspace.ironsspellbooks.entity.mobs.goals.WizardAttackGoal;
import io.redspace.ironsspellbooks.entity.mobs.goals.WizardRecoverGoal;
import io.redspace.ironsspellbooks.entity.mobs.wizards.IMerchantWizard;
import io.redspace.ironsspellbooks.item.FurledMapItem;
import io.redspace.ironsspellbooks.loot.SpellFilter;
import io.redspace.ironsspellbooks.player.AdditionalWanderingTrades;
import io.redspace.ironsspellbooks.registries.SoundRegistry;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.module.ModuleType;
import net.isstechnomancy.registry.TechItems;
import net.isstechnomancy.registry.TechSchools;
import net.isstechnomancy.registry.TechSpells;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.goal.target.ResetUniversalAngerTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.Objects;

/**
 * Technomancer: a neutral wandering wizard (goggles, red-and-gold coat, clockwork staff) like Iron's Spells' merchant
 * wizards. Patrols around, trades Technomancy scrolls, cogs, runes, modules, Dynamo Cores and maps to Clockwork
 * Shrines, and defends itself with Technomancy spells (Gear Barrage, Rocket Grab, Steam Vent, Magnetic Field, Brass
 * Sentries and a one-off Clockwork Automaton).
 */
public class TechnomancerEntity extends NeutralWizard implements IMerchantWizard {
    @Nullable
    private Player tradingPlayer;
    @Nullable
    protected MerchantOffers offers;
    private long lastRestockGameTime;
    private int numberOfRestocksToday;
    private long lastRestockCheckDayTime;

    public TechnomancerEntity(EntityType<? extends AbstractSpellCastingMob> type, Level level) {
        super(type, level);
        this.xpReward = 25;
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FocusOnTradingPlayerGoal<>(this));
        this.goalSelector.addGoal(1, new FloatGoal(this));
        // 1.5 buff: casts faster, at higher spell levels, and also uses Arc Welder; sentries come more often
        this.goalSelector.addGoal(2, new SpellBarrageGoal(this, TechSpells.DEPLOY_BRASS_SENTRY.get(), 3, 5, 160, 300, 1));
        this.goalSelector.addGoal(3, new WizardAttackGoal(this, 1.25, 25, 50)
                .setSpellQuality(0.45f, 0.85f)
                .setSpells(
                        List.of(TechSpells.GEAR_BARRAGE.get(), TechSpells.GEAR_BARRAGE.get(), TechSpells.ARC_WELDER.get(), TechSpells.ROCKET_GRAB.get(),
                                TechSpells.STEAM_VENT.get()),
                        List.of(TechSpells.MAGNETIC_FIELD.get()),
                        List.of(),
                        List.of())
                .setSingleUseSpell(TechSpells.ASSEMBLE_AUTOMATON.get(), 60, 200, 3, 5)
                .setDrinksPotions());
        this.goalSelector.addGoal(4, new PatrolNearLocationGoal(this, 30f, 0.75));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8f));
        this.goalSelector.addGoal(10, new WizardRecoverGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false, this::isHostileTowards));
        this.targetSelector.addGoal(5, new ResetUniversalAngerTargetGoal<>(this, false));
    }

    public static AttributeSupplier.Builder prepareAttributes() {
        return LivingEntity.createLivingAttributes()
                .add(Attributes.ATTACK_DAMAGE, 3)
                .add(Attributes.ATTACK_KNOCKBACK, 0)
                .add(Attributes.MAX_HEALTH, 110)
                .add(Attributes.ARMOR, 8)
                .add(Attributes.ARMOR_TOUGHNESS, 2)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.3)
                .add(Attributes.FOLLOW_RANGE, 32)
                .add(Attributes.MOVEMENT_SPEED, 0.25);
    }

    @Override
    public SpawnGroupData finalizeSpawn(@NotNull ServerLevelAccessor level, @NotNull DifficultyInstance difficulty, @NotNull MobSpawnType reason,
                                        @Nullable SpawnGroupData data, @Nullable CompoundTag tag) {
        setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(TechItems.CLOCKWORK_SCEPTER.get()));
        setDropChance(EquipmentSlot.MAINHAND, 0.04f);
        return super.finalizeSpawn(level, difficulty, reason, data, tag);
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    /* ---------------------------------------------------------------- trading */

    @Override
    protected @NotNull InteractionResult mobInteract(@NotNull Player player, @NotNull InteractionHand hand) {
        boolean preventTrade = getTarget() != null || (!level().isClientSide && getOffers().isEmpty());
        if (!preventTrade) {
            if (!level().isClientSide && !getOffers().isEmpty()) {
                if (shouldRestock()) {
                    restock();
                }
                setTradingPlayer(player);
                openTradingScreen(player, getDisplayName(), 0);
            }
            return InteractionResult.sidedSuccess(level().isClientSide);
        }
        return super.mobInteract(player, hand);
    }

    @Override
    public @NotNull MerchantOffers getOffers() {
        if (offers == null) {
            offers = new MerchantOffers();
            SpellFilter technomancy = new SpellFilter(TechSchools.TECHNOMANCY.get());
            offers.add(new AdditionalWanderingTrades.RandomScrollTrade(technomancy, 0f, 0.3f).getOffer(this, random));
            if (random.nextFloat() < 0.8f) {
                offers.add(new AdditionalWanderingTrades.RandomScrollTrade(technomancy, 0.3f, 0.7f).getOffer(this, random));
            }
            if (random.nextFloat() < 0.6f) {
                offers.add(new AdditionalWanderingTrades.RandomScrollTrade(technomancy, 0.75f, 1f).getOffer(this, random));
            }
            offers.add(new MerchantOffer(new ItemStack(Items.EMERALD, 6), ItemStack.EMPTY, new ItemStack(TechItems.ARCANE_COG.get(), 2), 0, 12, 3, 0.05f));
            offers.add(new MerchantOffer(new ItemStack(Items.EMERALD, 18), new ItemStack(Items.COPPER_BLOCK, 4), new ItemStack(TechItems.TECHNOMANCY_RUNE.get()), 0, 4, 8, 0.1f));
            ModuleType type = ModuleType.values()[random.nextInt(ModuleType.values().length)];
            offers.add(new MerchantOffer(new ItemStack(Items.EMERALD, 20), new ItemStack(TechItems.ARCANE_COG.get(), 4),
                    new ItemStack(TechItems.MODULES.get(type).get(0).get()), 0, 3, 10, 0.1f));
            if (random.nextFloat() < 0.4f) {
                ModuleType rare = ModuleType.values()[random.nextInt(ModuleType.values().length)];
                offers.add(new MerchantOffer(new ItemStack(Items.EMERALD, 48), new ItemStack(TechItems.TECHNOMANCY_RUNE.get(), 2),
                        new ItemStack(TechItems.MODULES.get(rare).get(1).get()), 0, 1, 20, 0.1f));
            }
            if (random.nextFloat() < 0.3f) {
                offers.add(new MerchantOffer(new ItemStack(Items.EMERALD, 64), new ItemStack(Items.NETHERITE_SCRAP, 2),
                        new ItemStack(TechItems.OVERCHARGED_DYNAMO_CORE.get()), 0, 1, 30, 0.1f));
            }
            offers.add(new MerchantOffer(new ItemStack(Items.EMERALD, 24), ItemStack.EMPTY,
                    FurledMapItem.of(ISSTechnomancy.id("clockwork_shrine"), Component.translatable("item.iss_technomancy.clockwork_shrine_map")), 0, 1, 5, 0.1f));
            offers.removeIf(Objects::isNull);
            setLastRestockGameTime(level().getGameTime());
        }
        return offers;
    }

    @Override
    public void overrideOffers(@NotNull MerchantOffers offers) {
    }

    @Override
    public void notifyTrade(MerchantOffer offer) {
        offer.increaseUses();
        this.ambientSoundTime = -getAmbientSoundInterval();
    }

    @Override
    public void notifyTradeUpdated(@NotNull ItemStack stack) {
        if (!level().isClientSide && this.ambientSoundTime > -getAmbientSoundInterval() + 20) {
            this.ambientSoundTime = -getAmbientSoundInterval();
            playSound(stack.isEmpty() ? SoundRegistry.TRADER_NO.get() : SoundRegistry.TRADER_YES.get(), getSoundVolume(), getVoicePitch());
        }
    }

    @Override
    public @NotNull SoundEvent getNotifyTradeSound() {
        return SoundRegistry.TRADER_YES.get();
    }

    @Override
    public void setTradingPlayer(@Nullable Player player) {
        this.tradingPlayer = player;
    }

    @Nullable
    @Override
    public Player getTradingPlayer() {
        return tradingPlayer;
    }

    @Override
    public int getRestocksToday() {
        return numberOfRestocksToday;
    }

    @Override
    public void setRestocksToday(int restocks) {
        this.numberOfRestocksToday = restocks;
    }

    @Override
    public long getLastRestockGameTime() {
        return lastRestockGameTime;
    }

    @Override
    public void setLastRestockGameTime(long time) {
        this.lastRestockGameTime = time;
    }

    @Override
    public long getLastRestockCheckDayTime() {
        return lastRestockCheckDayTime;
    }

    @Override
    public void setLastRestockCheckDayTime(long time) {
        this.lastRestockCheckDayTime = time;
    }

    @Override
    public @NotNull Level level() {
        return super.level();
    }

    @Override
    public void addAdditionalSaveData(@NotNull CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        serializeMerchant(tag, offers, lastRestockGameTime, numberOfRestocksToday);
    }

    @Override
    public void readAdditionalSaveData(@NotNull CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        deserializeMerchant(tag, c -> this.offers = c);
    }
}
