package net.isstechnomancy.client.screen;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.item.StaffModuleItem;
import net.isstechnomancy.menu.StaffModuleMenu;
import net.isstechnomancy.module.ModuleType;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.NotNull;

import java.util.EnumMap;
import java.util.Map;

public class StaffModuleScreen extends AbstractContainerScreen<StaffModuleMenu> {
    private static final ResourceLocation TEXTURE = ISSTechnomancy.id("textures/gui/staff_modules.png");

    public StaffModuleScreen(StaffModuleMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        this.imageWidth = 176;
        this.imageHeight = 166;
        this.inventoryLabelY = this.imageHeight - 93;
    }

    @Override
    protected void renderBg(@NotNull GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {
        graphics.blit(TEXTURE, leftPos, topPos, 0, 0, imageWidth, imageHeight);
    }

    @Override
    protected void renderLabels(@NotNull GuiGraphics graphics, int mouseX, int mouseY) {
        graphics.drawString(font, title, titleLabelX, titleLabelY, 0xF2C766, false);
        graphics.drawString(font, playerInventoryTitle, inventoryLabelX, inventoryLabelY, 0xDDA341, false);
        // summary of the module levels inside the brass panel
        Map<ModuleType, Integer> levels = new EnumMap<>(ModuleType.class);
        for (int i = 0; i < menu.getSockets().getSlots(); i++) {
            ItemStack stack = menu.getSockets().getStackInSlot(i);
            if (stack.getItem() instanceof StaffModuleItem module) {
                levels.merge(module.getModuleType(), module.getTier(), Integer::sum);
            }
        }
        int y = 19;
        for (Map.Entry<ModuleType, Integer> entry : levels.entrySet()) {
            int level = Math.min(ModuleType.MAX_LEVEL, entry.getValue());
            MutableComponent line = Component.translatable(entry.getKey().translationKey() + ".short").append(" " + level + "/" + ModuleType.MAX_LEVEL)
                    .withStyle(entry.getKey().color());
            graphics.pose().pushPose();
            graphics.pose().scale(0.75f, 0.75f, 1f);
            graphics.drawString(font, line, (int) (11 / 0.75f), (int) (y / 0.75f), 0xFFFFFF, false);
            graphics.pose().popPose();
            y += 8;
        }
    }

    @Override
    public void render(@NotNull GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        renderBackground(graphics);
        super.render(graphics, mouseX, mouseY, partialTick);
        renderTooltip(graphics, mouseX, mouseY);
    }
}
