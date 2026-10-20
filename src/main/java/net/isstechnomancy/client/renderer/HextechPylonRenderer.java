package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.boss.HextechPylon;
import net.isstechnomancy.entity.boss.TechDragon;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;
import org.joml.Matrix4f;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * Hextech Pylon at 2x, plus the crackling power stream from its eye into the dragon's chest core while charging.
 */
public class HextechPylonRenderer extends GeoEntityRenderer<HextechPylon> {
    public HextechPylonRenderer(EntityRendererProvider.Context context) {
        super(context, new DefaultedEntityGeoModel<>(ISSTechnomancy.id("hextech_pylon")));
        this.shadowRadius = 2.5f;
        addRenderLayer(new AutoGlowingGeoLayer<>(this));
    }

    @Override
    public boolean shouldRender(HextechPylon entity, Frustum frustum, double x, double y, double z) {
        return entity.distanceToSqr(x, y, z) < 256 * 256;
    }

    @Override
    public void render(HextechPylon entity, float entityYaw, float partialTick, PoseStack poseStack, MultiBufferSource buffers, int packedLight) {
        poseStack.pushPose();
        poseStack.scale(HextechPylon.SCALE, HextechPylon.SCALE, HextechPylon.SCALE);
        super.render(entity, entityYaw, partialTick, poseStack, buffers, packedLight);
        poseStack.popPose();
        TechDragon dragon = entity.getDragon();
        if (dragon != null && entity.isCharging()) {
            Vec3 origin = new Vec3(Mth.lerp(partialTick, entity.xo, entity.getX()), Mth.lerp(partialTick, entity.yo, entity.getY()), Mth.lerp(partialTick, entity.zo, entity.getZ()));
            Vec3 start = entity.eyePosition().subtract(entity.position()).add(origin);
            Vec3 end = dragon.corePosition().subtract(dragon.position())
                    .add(Mth.lerp(partialTick, dragon.xo, dragon.getX()), Mth.lerp(partialTick, dragon.yo, dragon.getY()), Mth.lerp(partialTick, dragon.zo, dragon.getZ()));
            VertexConsumer vc = buffers.getBuffer(RenderType.lightning());
            Matrix4f m = poseStack.last().pose();
            int segments = Math.max(8, (int) (start.distanceTo(end) / 2.5));
            RandomSource random = RandomSource.create(entity.getId() * 31L + entity.tickCount / 2);
            for (int k = 0; k < 3; k++) {
                Vec3[] pts = ArcDraw.arc(start, end, segments, 1.4f, random);
                ArcDraw.strip(vc, m, pts, origin, 0.55f, 0.3f, 0.65f, 1f, 0.35f);
                ArcDraw.strip(vc, m, pts, origin, 0.18f, 0.85f, 0.95f, 1f, 0.9f);
            }
        }
    }

    @Override
    public RenderType getRenderType(HextechPylon animatable, ResourceLocation texture, @Nullable MultiBufferSource bufferSource, float partialTick) {
        return RenderType.entityCutoutNoCull(texture);
    }

    @Override
    protected float getDeathMaxRotation(HextechPylon animatable) {
        return 0f;
    }
}
