package net.isstechnomancy.client.model;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.item.HextechArmorItem;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.model.GeoModel;

public class HextechArmorModel extends GeoModel<HextechArmorItem> {
    private static final ResourceLocation MODEL = ISSTechnomancy.id("geo/hextech_engineer_armor.geo.json");
    private static final ResourceLocation TEXTURE = ISSTechnomancy.id("textures/models/armor/hextech_engineer.png");
    private static final ResourceLocation ANIMATION = ISSTechnomancy.id("animations/hextech_engineer_armor.animation.json");

    @Override
    public ResourceLocation getModelResource(HextechArmorItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(HextechArmorItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(HextechArmorItem animatable) {
        return ANIMATION;
    }
}
