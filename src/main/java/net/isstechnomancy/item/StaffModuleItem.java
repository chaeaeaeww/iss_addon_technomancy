package net.isstechnomancy.item;

import net.isstechnomancy.module.ModuleType;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * A module for the Clockwork Staff's sockets. Tier adds that many levels to its family.
 */
public class StaffModuleItem extends Item {
    private final ModuleType type;
    private final int tier;

    public StaffModuleItem(ModuleType type, int tier) {
        super(new Properties().stacksTo(16).rarity(tier == 3 ? Rarity.EPIC : tier == 2 ? Rarity.RARE : Rarity.UNCOMMON));
        this.type = type;
        this.tier = tier;
    }

    public ModuleType getModuleType() {
        return type;
    }

    public int getTier() {
        return tier;
    }

    @Override
    public void appendHoverText(@NotNull ItemStack stack, @Nullable Level level, @NotNull List<Component> tooltip, @NotNull TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.iss_technomancy.module_tier", tier).withStyle(type.color()));
        tooltip.add(Component.translatable(type.translationKey() + ".desc", tier).withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.translatable("tooltip.iss_technomancy.module_hint").withStyle(ChatFormatting.DARK_GRAY, ChatFormatting.ITALIC));
    }
}
