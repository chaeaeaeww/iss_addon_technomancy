package net.isstechnomancy.item;

import io.redspace.ironsspellbooks.entity.armor.GenericCustomArmorRenderer;
import io.redspace.ironsspellbooks.item.armor.ImbuableChestplateArmorItem;
import net.isstechnomancy.client.model.HextechArmorModel;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.renderer.GeoArmorRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

import java.util.List;

/**
 * Hextech Engineer armor (1.9): the Clockwork Engineer set upgraded in a smithing table with the Hextech upgrade
 * template and a Tech Dragon Core. Navy hextech plating on brass, glowing cyan seams. Full set: Glorious Evolution
 * (see HextechArmorEvents).
 */
public class HextechArmorItem extends ImbuableChestplateArmorItem {
    public HextechArmorItem(Type type, Properties properties) {
        super(TechArmorMaterials.HEXTECH_ENGINEER, type, properties);
    }

    public static boolean wearsFullSet(LivingEntity entity) {
        for (EquipmentSlot slot : new EquipmentSlot[]{EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
            if (!(entity.getItemBySlot(slot).getItem() instanceof HextechArmorItem)) {
                return false;
            }
        }
        return true;
    }

    @Override
    public void appendHoverText(@NotNull ItemStack stack, @Nullable Level level, @NotNull List<Component> tooltip, @NotNull TooltipFlag flag) {
        super.appendHoverText(stack, level, tooltip, flag);
        tooltip.add(Component.translatable("tooltip.iss_technomancy.evolution.title").withStyle(ChatFormatting.GREEN));
        tooltip.add(Component.translatable("tooltip.iss_technomancy.evolution.desc", HextechArmorEvents.COOLDOWN_SECONDS).withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.translatable("tooltip.iss_technomancy.evolution.pool").withStyle(ChatFormatting.DARK_AQUA));
    }

    @Override
    @OnlyIn(Dist.CLIENT)
    public GeoArmorRenderer<?> supplyRenderer() {
        GenericCustomArmorRenderer<HextechArmorItem> renderer = new GenericCustomArmorRenderer<>(new HextechArmorModel());
        renderer.addRenderLayer(new AutoGlowingGeoLayer<>(renderer));
        return renderer;
    }
}
