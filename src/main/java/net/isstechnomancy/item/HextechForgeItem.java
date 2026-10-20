package net.isstechnomancy.item;

import net.isstechnomancy.ISSTechnomancy;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.level.block.Block;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.model.GeoModel;
import software.bernie.geckolib.renderer.GeoItemRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.function.Consumer;

/** 1.10: the Hextech Thunderforge as an item shows the block's own animated model (inventory, hand, item frame). */
public class HextechForgeItem extends BlockItem implements GeoItem {
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("idle");
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    public HextechForgeItem(Block block, Properties properties) {
        super(block, properties);
    }

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
            public BlockEntityWithoutLevelRenderer getCustomRenderer() {
                if (renderer == null) {
                    GeoItemRenderer<HextechForgeItem> r = new GeoItemRenderer<>(new GeoModel<>() {
                        @Override
                        public ResourceLocation getModelResource(HextechForgeItem item) {
                            return ISSTechnomancy.id("geo/block/hextech_thunderforge.geo.json");
                        }

                        @Override
                        public ResourceLocation getTextureResource(HextechForgeItem item) {
                            return ISSTechnomancy.id("textures/block/hextech_thunderforge.png");
                        }

                        @Override
                        public ResourceLocation getAnimationResource(HextechForgeItem item) {
                            return ISSTechnomancy.id("animations/block/hextech_thunderforge.animation.json");
                        }
                    });
                    r.addRenderLayer(new AutoGlowingGeoLayer<>(r));
                    renderer = r;
                }
                return renderer;
            }
        });
    }
}
