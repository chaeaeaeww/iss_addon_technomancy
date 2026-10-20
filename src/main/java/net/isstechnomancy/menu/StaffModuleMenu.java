package net.isstechnomancy.menu;

import net.isstechnomancy.item.ClockworkStaffItem;
import net.isstechnomancy.item.StaffModuleItem;
import net.isstechnomancy.module.StaffModules;
import net.isstechnomancy.registry.TechMenus;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.items.ItemStackHandler;
import net.minecraftforge.items.SlotItemHandler;
import org.jetbrains.annotations.NotNull;

/**
 * Three module sockets of the Clockwork Staff held in {@link #hand}. Socket contents are written back to the staff's
 * NBT on every change, and the hotbar slot holding the staff is locked while the menu is open.
 */
public class StaffModuleMenu extends AbstractContainerMenu {
    public static final int[][] SOCKETS = {{44, 35}, {80, 53}, {116, 35}};

    private final InteractionHand hand;
    private final Player player;
    private final ItemStackHandler sockets;

    public StaffModuleMenu(int id, Inventory inventory, FriendlyByteBuf buf) {
        this(id, inventory, buf.readEnum(InteractionHand.class));
    }

    public StaffModuleMenu(int id, Inventory inventory, InteractionHand hand) {
        super(TechMenus.STAFF_MODULES.get(), id);
        this.hand = hand;
        this.player = inventory.player;
        ItemStack staff = player.getItemInHand(hand);
        ItemStackHandler stored = StaffModules.read(staff);
        this.sockets = new ItemStackHandler(StaffModules.SLOTS) {
            @Override
            protected void onContentsChanged(int slot) {
                ItemStack held = player.getItemInHand(StaffModuleMenu.this.hand);
                if (held.getItem() instanceof ClockworkStaffItem) {
                    StaffModules.write(held, this);
                }
            }

            @Override
            public boolean isItemValid(int slot, @NotNull ItemStack stack) {
                return stack.getItem() instanceof StaffModuleItem;
            }

            @Override
            public int getSlotLimit(int slot) {
                return 1;
            }
        };
        for (int i = 0; i < StaffModules.SLOTS; i++) {
            sockets.setStackInSlot(i, stored.getStackInSlot(i).copy());
        }
        for (int i = 0; i < StaffModules.SLOTS; i++) {
            addSlot(new SlotItemHandler(sockets, i, SOCKETS[i][0], SOCKETS[i][1]));
        }
        int locked = hand == InteractionHand.MAIN_HAND ? inventory.selected : -1;
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) {
                addSlot(new Slot(inventory, col + row * 9 + 9, 8 + col * 18, 84 + row * 18));
            }
        }
        for (int col = 0; col < 9; col++) {
            if (col == locked) {
                addSlot(new Slot(inventory, col, 8 + col * 18, 142) {
                    @Override
                    public boolean mayPickup(@NotNull Player p) {
                        return false;
                    }

                    @Override
                    public boolean mayPlace(@NotNull ItemStack stack) {
                        return false;
                    }
                });
            } else {
                addSlot(new Slot(inventory, col, 8 + col * 18, 142));
            }
        }
    }

    public ItemStackHandler getSockets() {
        return sockets;
    }

    @Override
    public @NotNull ItemStack quickMoveStack(@NotNull Player p, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem() || !slot.mayPickup(p)) {
            return ItemStack.EMPTY;
        }
        ItemStack stack = slot.getItem();
        ItemStack copy = stack.copy();
        int socketEnd = StaffModules.SLOTS;
        if (index < socketEnd) {
            if (!moveItemStackTo(stack, socketEnd, slots.size(), true)) {
                return ItemStack.EMPTY;
            }
        } else if (stack.getItem() instanceof StaffModuleItem) {
            boolean moved = false;
            for (int i = 0; i < socketEnd && !stack.isEmpty(); i++) {
                Slot socket = slots.get(i);
                if (!socket.hasItem()) {
                    socket.set(stack.split(1));
                    moved = true;
                }
            }
            if (!moved) {
                return ItemStack.EMPTY;
            }
        } else {
            return ItemStack.EMPTY;
        }
        if (stack.isEmpty()) {
            slot.set(ItemStack.EMPTY);
        } else {
            slot.setChanged();
        }
        return copy;
    }

    @Override
    public boolean stillValid(@NotNull Player p) {
        return p.getItemInHand(hand).getItem() instanceof ClockworkStaffItem;
    }
}
