package net.isstechnomancy.module;

import net.isstechnomancy.item.ClockworkStaffItem;
import net.isstechnomancy.item.StaffModuleItem;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.items.ItemStackHandler;

import java.util.EnumMap;
import java.util.Map;

/**
 * Reads and writes the three module sockets stored on a Clockwork Staff stack (tag "TechModules", an ItemStackHandler).
 */
public final class StaffModules {
    public static final int SLOTS = 3;
    public static final String TAG = "TechModules";

    private StaffModules() {
    }

    public static ItemStackHandler read(ItemStack staff) {
        ItemStackHandler handler = new ItemStackHandler(SLOTS);
        CompoundTag tag = staff.getTag();
        if (tag != null && tag.contains(TAG, Tag.TAG_COMPOUND)) {
            handler.deserializeNBT(tag.getCompound(TAG));
            if (handler.getSlots() != SLOTS) {
                ItemStackHandler resized = new ItemStackHandler(SLOTS);
                for (int i = 0; i < Math.min(SLOTS, handler.getSlots()); i++) {
                    resized.setStackInSlot(i, handler.getStackInSlot(i));
                }
                handler = resized;
            }
        }
        return handler;
    }

    public static void write(ItemStack staff, ItemStackHandler handler) {
        staff.getOrCreateTag().put(TAG, handler.serializeNBT());
    }

    /**
     * Module levels without allocating a handler (used every cast and for attribute modifiers).
     */
    public static ModuleStats stats(ItemStack staff) {
        CompoundTag tag = staff.getTag();
        if (tag == null || !tag.contains(TAG, Tag.TAG_COMPOUND)) {
            return ModuleStats.NONE;
        }
        ListTag items = tag.getCompound(TAG).getList("Items", Tag.TAG_COMPOUND);
        if (items.isEmpty()) {
            return ModuleStats.NONE;
        }
        Map<ModuleType, Integer> levels = new EnumMap<>(ModuleType.class);
        for (int i = 0; i < items.size(); i++) {
            ItemStack module = ItemStack.of(items.getCompound(i));
            if (module.getItem() instanceof StaffModuleItem item) {
                levels.merge(item.getModuleType(), item.getTier(), Integer::sum);
            }
        }
        return new ModuleStats(levels);
    }

    /**
     * Module stats of the Clockwork Staff the caster is holding (main hand first), or {@link ModuleStats#NONE}.
     */
    public static ModuleStats of(LivingEntity caster) {
        if (caster == null) {
            return ModuleStats.NONE;
        }
        for (InteractionHand hand : InteractionHand.values()) {
            ItemStack stack = caster.getItemInHand(hand);
            if (stack.getItem() instanceof ClockworkStaffItem) {
                return stats(stack);
            }
        }
        return ModuleStats.NONE;
    }
}
