package net.isstechnomancy.client.renderer;

import io.redspace.ironsspellbooks.entity.mobs.abstract_spell_casting_mob.AbstractSpellCastingMob;
import io.redspace.ironsspellbooks.entity.mobs.abstract_spell_casting_mob.AbstractSpellCastingMobModel;
import io.redspace.ironsspellbooks.entity.mobs.abstract_spell_casting_mob.AbstractSpellCastingMobRenderer;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.client.model.ProceduralPose;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * Technomancer ("Hextech" engineer, Minecraft-skin style with a voxel outer layer like the 3D Skin Layers mod):
 * geo/entity/technomancer.geo.json keeps every bone of Iron's Spells' casting mob model, so ISS casting animations,
 * held items and armor work, and adds pauldrons, a back rig with a third mechanical arm and two cape panels.
 *
 * <p>The extra bones are never keyframed. They are set every frame <b>from their rest pose</b> (never added to their
 * current rotation: GeckoLib does not reset bones it does not animate, so adding made the back arm spin): the cape
 * hangs and swings back with walking speed, the third arm sways slowly around its rest pose, rises while casting and
 * opens its claws.</p>
 */
public class TechnomancerRenderer extends AbstractSpellCastingMobRenderer {
    private static final ResourceLocation MODEL = ISSTechnomancy.id("geo/entity/technomancer.geo.json");
    private static final ResourceLocation TEXTURE = ISSTechnomancy.id("textures/entity/technomancer.png");

    public TechnomancerRenderer(EntityRendererProvider.Context context) {
        super(context, new AbstractSpellCastingMobModel() {
            @Override
            public ResourceLocation getModelResource(AbstractSpellCastingMob mob) {
                return MODEL;
            }

            @Override
            public ResourceLocation getTextureResource(AbstractSpellCastingMob mob) {
                return TEXTURE;
            }

            @Override
            public void setCustomAnimations(AbstractSpellCastingMob mob, long instanceId, AnimationState<AbstractSpellCastingMob> state) {
                super.setCustomAnimations(mob, instanceId, state);
                float t = mob.tickCount + state.getPartialTick();
                float walk = Mth.clamp(state.getLimbSwingAmount() * 1.5f, 0f, 1f);
                float cast = mob.isCasting() ? 1f : 0f;
                // cape: hangs straight, swings back when walking, small flutter (GeckoLib radians from rest; GeckoLib's
                // X axis is the Bedrock one negated, so a negative value lifts the hem backwards)
                float swing = 0.45f * walk;
                ProceduralPose.setFromRest(getAnimationProcessor().getBone("cape_l"), -(swing + 0.04f + 0.04f * Mth.sin(t * 0.12f)), 0, 0);
                ProceduralPose.setFromRest(getAnimationProcessor().getBone("cape_r"), -(swing + 0.04f + 0.04f * Mth.sin(t * 0.12f + 1.3f)), 0, 0);
                ProceduralPose.setFromRest(getAnimationProcessor().getBone("cape_l2"), -(0.25f * walk + 0.05f + 0.05f * Mth.sin(t * 0.17f + 0.6f)), 0, 0);
                ProceduralPose.setFromRest(getAnimationProcessor().getBone("cape_r2"), -(0.25f * walk + 0.05f + 0.05f * Mth.sin(t * 0.17f + 2.0f)), 0, 0);
                // third arm: slow sway (a few degrees), lifts while casting; claws open while casting
                float sway = 0.07f * Mth.sin(t * 0.05f);
                ProceduralPose.setFromRest(getAnimationProcessor().getBone("back_arm"), 0.05f * Mth.sin(t * 0.07f) + 0.2f * cast, 0, sway);
                ProceduralPose.setFromRest(getAnimationProcessor().getBone("back_arm2"), 0.06f * Mth.sin(t * 0.07f + 1f) + 0.3f * cast, 0, 0);
                float open = 0.12f + 0.35f * cast;
                ProceduralPose.setFromRest(getAnimationProcessor().getBone("claw_l"), 0, 0, -open);
                ProceduralPose.setFromRest(getAnimationProcessor().getBone("claw_r"), 0, 0, open);
            }
        });
        addRenderLayer(new AutoGlowingGeoLayer<>(this));
    }
}
