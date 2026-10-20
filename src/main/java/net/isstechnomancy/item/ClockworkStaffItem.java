package net.isstechnomancy.item;

import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.Multimap;
import io.redspace.ironsspellbooks.api.registry.AttributeRegistry;
import io.redspace.ironsspellbooks.item.weapons.StaffItem;
import io.redspace.ironsspellbooks.item.weapons.StaffTier;
import io.redspace.ironsspellbooks.render.StaffArmPose;
import net.isstechnomancy.menu.StaffModuleMenu;
import net.isstechnomancy.module.ModuleStats;
import net.isstechnomancy.module.ModuleType;
import net.isstechnomancy.module.StaffModules;
import net.isstechnomancy.registry.TechAttributes;
import net.minecraft.ChatFormatting;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;
import net.minecraftforge.items.ItemStackHandler;
import net.minecraftforge.network.NetworkHooks;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.List;
import java.util.UUID;
import java.util.function.Consumer;

/**
 * Clockwork Staff: the Technomancy staff. 3D GeckoLib model (spinning cog ring, ticking lightning hand, orbiting orbs)
 * in hand, flat icon in GUIs. Sneak + use opens its three module sockets; modules upgrade every Technomancy spell cast
 * while it is held (see {@link ModuleStats}). Capacitor modules add attributes directly to the staff.
 */
public class ClockworkStaffItem extends StaffItem implements GeoItem {
    private static final UUID CAPACITOR_CDR = UUID.fromString("5b2f1c64-7f0e-4c4a-9a4e-3f1f2a6c7d01");
    private static final UUID CAPACITOR_CAST = UUID.fromString("5b2f1c64-7f0e-4c4a-9a4e-3f1f2a6c7d02");
    private static final UUID CAPACITOR_POWER = UUID.fromString("5b2f1c64-7f0e-4c4a-9a4e-3f1f2a6c7d03");
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("idle");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    /** GeckoLib model and texture name (geo/item/<model>.geo.json, textures/item/<model>.png). */
    private final String model;
    /** Hextech scepter star level (1.9), 0 for none. */
    private final int stars;

    public ClockworkStaffItem(Properties properties, StaffTier tier) {
        this(properties, tier, "clockwork_staff", 0);
    }

    public ClockworkStaffItem(Properties properties, StaffTier tier, String model, int stars) {
        super(properties, tier);
        this.model = model;
        this.stars = stars;
    }

    public String getModelName() {
        return model;
    }

    public int getStars() {
        return stars;
    }

    @Override
    public @NotNull InteractionResultHolder<ItemStack> use(@NotNull Level level, Player player, @NotNull InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.isShiftKeyDown()) {
            if (player instanceof ServerPlayer serverPlayer) {
                NetworkHooks.openScreen(serverPlayer, new SimpleMenuProvider(
                        (id, inventory, p) -> new StaffModuleMenu(id, inventory, hand),
                        Component.translatable("container.iss_technomancy.staff_modules")), buf -> buf.writeEnum(hand));
                level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.CHAIN_PLACE, SoundSource.PLAYERS, 0.8f, 1.4f);
            }
            return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
        }
        return super.use(level, player, hand);
    }

    @Override
    public Multimap<Attribute, AttributeModifier> getAttributeModifiers(EquipmentSlot slot, ItemStack stack) {
        Multimap<Attribute, AttributeModifier> base = super.getAttributeModifiers(slot, stack);
        if (slot != EquipmentSlot.MAINHAND) {
            return base;
        }
        int capacitor = StaffModules.stats(stack).level(ModuleType.CAPACITOR);
        if (capacitor <= 0) {
            return base;
        }
        ImmutableMultimap.Builder<Attribute, AttributeModifier> builder = ImmutableMultimap.builder();
        builder.putAll(base);
        builder.put(AttributeRegistry.COOLDOWN_REDUCTION.get(), new AttributeModifier(CAPACITOR_CDR, "Capacitor module", 0.04 * capacitor, AttributeModifier.Operation.MULTIPLY_BASE));
        builder.put(AttributeRegistry.CAST_TIME_REDUCTION.get(), new AttributeModifier(CAPACITOR_CAST, "Capacitor module", 0.05 * capacitor, AttributeModifier.Operation.MULTIPLY_BASE));
        builder.put(TechAttributes.TECHNOMANCY_SPELL_POWER.get(), new AttributeModifier(CAPACITOR_POWER, "Capacitor module", 0.03 * capacitor, AttributeModifier.Operation.MULTIPLY_BASE));
        return builder.build();
    }

    @Override
    public void appendHoverText(@NotNull ItemStack stack, @Nullable Level level, @NotNull List<Component> tooltip, @NotNull TooltipFlag flag) {
        super.appendHoverText(stack, level, tooltip, flag);
        if (model.startsWith("hextech")) {
            // 1.10: TravelOptics-style evolution: stars, then each Evo's ability (lit once unlocked)
            tooltip.add(Component.literal("★".repeat(stars)).withStyle(ChatFormatting.YELLOW)
                    .append(Component.literal("☆".repeat(3 - stars)).withStyle(ChatFormatting.GRAY))
                    .append(Component.translatable("tooltip.iss_technomancy.evolution", stars).withStyle(ChatFormatting.DARK_AQUA)));
            tooltip.add(Component.translatable("tooltip.iss_technomancy.evolution_benefits").withStyle(ChatFormatting.YELLOW));
            for (int evo = 1; evo <= 3; evo++) {
                boolean on = stars >= evo;
                tooltip.add(Component.literal(on ? " ★ " : " ☆ ").withStyle(on ? ChatFormatting.YELLOW : ChatFormatting.DARK_GRAY)
                        .append(Component.translatable("tooltip.iss_technomancy.scepter_evo" + evo).withStyle(on ? ChatFormatting.AQUA : ChatFormatting.DARK_GRAY)));
            }
            if (stars < 3) {
                tooltip.add(Component.translatable("tooltip.iss_technomancy.scepter_upgrade").withStyle(ChatFormatting.DARK_GRAY, ChatFormatting.ITALIC));
            }
        }
        ItemStackHandler modules = StaffModules.read(stack);
        tooltip.add(Component.translatable("tooltip.iss_technomancy.staff_modules").withStyle(ChatFormatting.GOLD));
        for (int i = 0; i < modules.getSlots(); i++) {
            ItemStack module = modules.getStackInSlot(i);
            if (module.getItem() instanceof StaffModuleItem item) {
                tooltip.add(Component.literal(" ◆ ").withStyle(item.getModuleType().color()).append(module.getHoverName().copy().withStyle(ChatFormatting.GRAY)));
            } else {
                tooltip.add(Component.literal(" ◇ ").withStyle(ChatFormatting.DARK_GRAY).append(Component.translatable("tooltip.iss_technomancy.empty_socket").withStyle(ChatFormatting.DARK_GRAY)));
            }
        }
        tooltip.add(Component.translatable("tooltip.iss_technomancy.staff_hint").withStyle(ChatFormatting.DARK_GRAY, ChatFormatting.ITALIC));
    }

    @Override
    public boolean shouldCauseReequipAnimation(ItemStack oldStack, ItemStack newStack, boolean slotChanged) {
        return slotChanged || oldStack.getItem() != newStack.getItem();
    }

    /* ---------------------------------------------------------------- GeckoLib */

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "idle", 0, state -> state.setAndContinue(IDLE)));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    @OnlyIn(Dist.CLIENT)
    public void initializeClient(Consumer<IClientItemExtensions> consumer) {
        consumer.accept(new IClientItemExtensions() {
            private BlockEntityWithoutLevelRenderer renderer;

            @Override
            public HumanoidModel.ArmPose getArmPose(LivingEntity entity, InteractionHand hand, ItemStack stack) {
                return StaffArmPose.STAFF_ARM_POS;
            }

            @Override
            public BlockEntityWithoutLevelRenderer getCustomRenderer() {
                if (renderer == null) {
                    renderer = net.isstechnomancy.client.renderer.ClockworkStaffRenderer.create();
                }
                return renderer;
            }
        });
    }
}
