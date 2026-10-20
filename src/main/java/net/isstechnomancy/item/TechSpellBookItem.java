package net.isstechnomancy.item;

import io.redspace.ironsspellbooks.api.spells.ISpellContainer;
import io.redspace.ironsspellbooks.api.spells.ISpellContainerMutable;
import io.redspace.ironsspellbooks.item.SpellBook;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.NotNull;

/**
 * Technomancy spellbooks (1.9): the 7-slot Clockwork Spellbook and the 12-slot Hextech Codex. Iron's Spells stores the
 * slot count in the book's NBT, so a book upgraded in the smithing table (which copies the NBT, spells included) would
 * keep its old size: this grows the container to the item's size whenever the book sits in an inventory.
 */
public class TechSpellBookItem extends SpellBook {
    public TechSpellBookItem(int slots, Properties properties) {
        super(slots, properties);
    }

    @Override
    public void inventoryTick(@NotNull ItemStack stack, @NotNull Level level, @NotNull Entity entity, int slot, boolean selected) {
        super.inventoryTick(stack, level, entity, slot, selected);
        if (!level.isClientSide && level.getGameTime() % 20 == 0) {
            growContainer(stack, getMaxSpellSlots());
        }
    }

    /** True if it had to grow. */
    public static boolean growContainer(ItemStack stack, int slots) {
        if (!ISpellContainer.isSpellContainer(stack)) {
            return false;
        }
        ISpellContainer container = ISpellContainer.get(stack);
        if (container.getMaxSpellCount() >= slots) {
            return false;
        }
        ISpellContainerMutable copy = container.mutableCopy();
        copy.setMaxSpellCount(slots);
        ISpellContainer.set(stack, copy.toImmutable());
        return true;
    }
}
