package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.block.HextechForgeBlockEntity;
import net.isstechnomancy.registry.TechItems;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import software.bernie.geckolib.model.DefaultedBlockGeoModel;
import software.bernie.geckolib.renderer.GeoBlockRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * The Hextech Thunderforge: the animated clockwork (GeckoLib), the Overcharged Dynamo Core turning in its cradle and,
 * during the summoning, the core rising into a swelling ball of lightning fed by arcs from the four crystals.
 */
public class HextechForgeRenderer implements net.minecraft.client.renderer.blockentity.BlockEntityRenderer<HextechForgeBlockEntity> {
    private static final ResourceLocation ORB = ISSTechnomancy.id("textures/entity/dragon_shield.png");
    private static final int RINGS = 12, SEGMENTS = 20;
    private final RandomSource random = RandomSource.create();
    /** The clockwork itself (wrapped rather than extended: GeoBlockRenderer's render() clashes with a typed override). */
    private final GeoBlockRenderer<HextechForgeBlockEntity> geo;

    public HextechForgeRenderer(BlockEntityRendererProvider.Context context) {
        geo = new GeoBlockRenderer<>(new DefaultedBlockGeoModel<>(ISSTechnomancy.id("hextech_thunderforge")));
        geo.addRenderLayer(new AutoGlowingGeoLayer<>(geo));
    }

    @Override
    public void render(HextechForgeBlockEntity forge, float partialTick, PoseStack poseStack, MultiBufferSource buffers, int light, int overlay) {
        geo.render(forge, partialTick, poseStack, buffers, light, overlay);
        float time = (forge.getLevel() != null ? forge.getLevel().getGameTime() : 0) + partialTick;
        boolean summoning = forge.isSummoning();
        float t = summoning ? forge.getSummonTicks() + partialTick : 0;
        poseStack.pushPose();
        poseStack.translate(0.5, 0, 0.5);
        if (forge.hasCore()) {
            // the core sits in the cradle; summoning lifts it into the heart of the ball
            float rise = summoning ? Mth.clamp(t / 40f, 0f, 1f) : 0f;
            double y = Mth.lerp(rise, 14.6 / 16.0 + 0.04 * Mth.sin(time * 0.1f), HextechForgeBlockEntity.ORB_HEIGHT);
            poseStack.pushPose();
            poseStack.translate(0, y, 0);
            poseStack.mulPose(Axis.YP.rotationDegrees(time * (summoning ? 12f : 2f)));
            float s = summoning ? Mth.lerp(rise, 0.55f, 0.8f) : 0.55f;
            poseStack.scale(s, s, s);
            Minecraft.getInstance().getItemRenderer().renderStatic(new ItemStack(TechItems.OVERCHARGED_DYNAMO_CORE.get()), ItemDisplayContext.FIXED,
                    summoning ? LightTexture.FULL_BRIGHT : light, OverlayTexture.NO_OVERLAY, poseStack, buffers, forge.getLevel(), 0);
            poseStack.popPose();
        }
        if (summoning) {
            float r = HextechForgeBlockEntity.orbRadius(t);
            renderOrb(poseStack, buffers, time, r);
            renderArcs(poseStack, buffers, r, t);
        }
        poseStack.popPose();
    }

    private void renderOrb(PoseStack poseStack, MultiBufferSource buffers, float time, float radius) {
        VertexConsumer vc = buffers.getBuffer(RenderType.energySwirl(ORB, time * 0.01f % 1f, time * 0.006f % 1f));
        poseStack.pushPose();
        poseStack.translate(0, HextechForgeBlockEntity.ORB_HEIGHT, 0);
        Matrix4f m = poseStack.last().pose();
        Matrix3f n = poseStack.last().normal();
        float pulse = 0.65f + 0.25f * Mth.sin(time * 0.6f);
        float r = radius * (1f + 0.04f * Mth.sin(time * 1.3f));
        for (int i = 0; i < RINGS; i++) {
            float v0 = i / (float) RINGS, v1 = (i + 1) / (float) RINGS;
            float th0 = v0 * Mth.PI, th1 = v1 * Mth.PI;
            for (int j = 0; j < SEGMENTS; j++) {
                float u0 = j / (float) SEGMENTS, u1 = (j + 1) / (float) SEGMENTS;
                float ph0 = u0 * Mth.TWO_PI, ph1 = u1 * Mth.TWO_PI;
                vertex(vc, m, n, r, th0, ph0, u0 * 4, v0 * 2, pulse);
                vertex(vc, m, n, r, th1, ph0, u0 * 4, v1 * 2, pulse);
                vertex(vc, m, n, r, th1, ph1, u1 * 4, v1 * 2, pulse);
                vertex(vc, m, n, r, th0, ph1, u1 * 4, v0 * 2, pulse);
            }
        }
        poseStack.popPose();
    }

    private static void vertex(VertexConsumer vc, Matrix4f m, Matrix3f n, float r, float theta, float phi, float u, float v, float a) {
        float sx = Mth.sin(theta) * Mth.cos(phi), sy = Mth.cos(theta), sz = Mth.sin(theta) * Mth.sin(phi);
        vc.vertex(m, sx * r, sy * r, sz * r).color(0.55f * a, 0.75f * a, 1.0f * a, 1f).uv(u, v).overlayCoords(OverlayTexture.NO_OVERLAY)
                .uv2(LightTexture.FULL_BRIGHT).normal(n, sx, sy, sz).endVertex();
    }

    /** Arcs from the four crystal crowns into the ball, and a few crawling over it. */
    private void renderArcs(PoseStack poseStack, MultiBufferSource buffers, float radius, float t) {
        VertexConsumer vc = buffers.getBuffer(RenderType.lightning());
        Matrix4f m = poseStack.last().pose();
        random.setSeed((long) (t * 0.5f) * 31L);
        Vec3 orb = new Vec3(0, HextechForgeBlockEntity.ORB_HEIGHT, 0);
        for (double[] c : HextechForgeBlockEntity.CRYSTALS) {
            Vec3 tip = new Vec3(c[0], c[1], c[2]);
            Vec3 to = orb.add(tip.subtract(orb).normalize().scale(radius * 0.9));
            ArcDraw.strip(vc, m, ArcDraw.arc(tip, to, 6, 0.25f + radius * 0.1f, random), Vec3.ZERO, 0.06f, 0.6f, 0.85f, 1.0f, 0.85f);
        }
        for (int k = 0; k < 3; k++) {
            Vec3 a = orb.add(new Vec3(random.nextFloat() - 0.5, random.nextFloat() - 0.5, random.nextFloat() - 0.5).normalize().scale(radius));
            Vec3 b = orb.add(new Vec3(random.nextFloat() - 0.5, random.nextFloat() - 0.5, random.nextFloat() - 0.5).normalize().scale(radius));
            ArcDraw.strip(vc, m, ArcDraw.arc(a, b, 5, radius * 0.3f, random), Vec3.ZERO, 0.05f, 0.85f, 0.7f, 1.0f, 0.8f);
        }
    }

    @Override
    public boolean shouldRenderOffScreen(HextechForgeBlockEntity forge) {
        return true;
    }

    @Override
    public int getViewDistance() {
        return 96;
    }
}
