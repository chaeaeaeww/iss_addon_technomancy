package net.isstechnomancy.item;

import io.redspace.ironsspellbooks.entity.armor.GenericCustomArmorRenderer;
import io.redspace.ironsspellbooks.item.armor.ImbuableChestplateArmorItem;
import net.isstechnomancy.client.model.ClockworkEngineerArmorModel;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;
import software.bernie.geckolib.renderer.GeoArmorRenderer;

public class ClockworkEngineerArmorItem extends ImbuableChestplateArmorItem {
    public ClockworkEngineerArmorItem(Type type, Properties properties) {
        super(TechArmorMaterials.CLOCKWORK_ENGINEER, type, properties);
    }

    @Override
    @OnlyIn(Dist.CLIENT)
    public GeoArmorRenderer<?> supplyRenderer() {
        GenericCustomArmorRenderer<ClockworkEngineerArmorItem> renderer = new GenericCustomArmorRenderer<>(new ClockworkEngineerArmorModel());
        renderer.addRenderLayer(new software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer<>(renderer));
        return renderer;
    }
}
