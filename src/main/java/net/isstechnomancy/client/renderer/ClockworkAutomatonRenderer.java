package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.ClockworkAutomaton;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * Normal form: geo/entity/clockwork_automaton.geo.json (servo robot). Mk.II: geo/entity/clockwork_automaton_mk2.geo.json
 * (the "Blitz" steam golem, authored at full size) with its own texture and animation file. While its Rocket Grab is
 * out the fist_r bone is hidden.
 * The body turns in 15 degree clicks so it pivots like a machine.
 */
public class ClockworkAutomatonRenderer extends GeoEntityRenderer<ClockworkAutomaton> {
    private static final ResourceLocation MK2_MODEL = ISSTechnomancy.id("geo/entity/clockwork_automaton_mk2.geo.json");
    private static final ResourceLocation MK2_TEXTURE = ISSTechnomancy.id("textures/entity/clockwork_automaton_mk2.png");
    private static final ResourceLocation MK2_ANIMATION = ISSTechnomancy.id("animations/entity/clockwork_automaton_mk2.animation.json");
    private static final float TURN_STEP = 15f;

    public ClockworkAutomatonRenderer(EntityRendererProvider.Context context) {
        super(context, new DefaultedEntityGeoModel<>(ISSTechnomancy.id("clockwork_automaton"), true) {
            @Override
            public ResourceLocation getModelResource(ClockworkAutomaton animatable) {
                return animatable.isMk2() ? MK2_MODEL : super.getModelResource(animatable);
            }

            @Override
            public ResourceLocation getTextureResource(ClockworkAutomaton animatable) {
                return animatable.isMk2() ? MK2_TEXTURE : super.getTextureResource(animatable);
            }

            @Override
            public ResourceLocation getAnimationResource(ClockworkAutomaton animatable) {
                return animatable.isMk2() ? MK2_ANIMATION : super.getAnimationResource(animatable);
            }

            @Override
            public void setCustomAnimations(ClockworkAutomaton animatable, long instanceId, AnimationState<ClockworkAutomaton> animationState) {
                super.setCustomAnimations(animatable, instanceId, animationState);
                if (animatable.isMk2()) {
                    // the right fist is flying on its cable during Rocket Grab
                    var fist = getAnimationProcessor().getBone("fist_r");
                    if (fist != null) {
                        fist.setHidden(animatable.isHandOut());
                    }
                }
            }
        });
        this.shadowRadius = 0.6f;
        addRenderLayer(new AutoGlowingGeoLayer<>(this));
    }

    @Override
    protected void applyRotations(ClockworkAutomaton animatable, PoseStack poseStack, float ageInTicks, float rotationYaw, float partialTick) {
        super.applyRotations(animatable, poseStack, ageInTicks, Math.round(rotationYaw / TURN_STEP) * TURN_STEP, partialTick);
    }

    @Override
    public void render(ClockworkAutomaton entity, float entityYaw, float partialTick, PoseStack poseStack, MultiBufferSource bufferSource, int packedLight) {
        // the Blitz model is authored at full size; only the hitbox is scaled
        this.shadowRadius = entity.isMk2() ? 1.3f : 0.6f;
        super.render(entity, entityYaw, partialTick, poseStack, bufferSource, packedLight);
    }
}
