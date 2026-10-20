package net.isstechnomancy.client.model;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.item.ClockworkEngineerArmorItem;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.model.GeoModel;

public class ClockworkEngineerArmorModel extends GeoModel<ClockworkEngineerArmorItem> {
    private static final ResourceLocation MODEL = ISSTechnomancy.id("geo/clockwork_engineer_armor.geo.json");
    private static final ResourceLocation TEXTURE = ISSTechnomancy.id("textures/models/armor/clockwork_engineer.png");
    private static final ResourceLocation ANIMATION = ISSTechnomancy.id("animations/clockwork_engineer_armor.animation.json");

    @Override
    public ResourceLocation getModelResource(ClockworkEngineerArmorItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(ClockworkEngineerArmorItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(ClockworkEngineerArmorItem animatable) {
        return ANIMATION;
    }
}
