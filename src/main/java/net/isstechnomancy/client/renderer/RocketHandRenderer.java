package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.RocketHand;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * Model: geo/entity/rocket_hand.geo.json (big brass fist, animations "open"/"closed"). The cable back to the owner is a
 * square textured tube (textures/entity/rocket_hand_cable.png), culled against its whole span.
 */
public class RocketHandRenderer extends GeoEntityRenderer<RocketHand> {
    private static final ResourceLocation CABLE = ISSTechnomancy.id("textures/entity/rocket_hand_cable.png");

    public RocketHandRenderer(EntityRendererProvider.Context context) {
        super(context, new DefaultedEntityGeoModel<>(ISSTechnomancy.id("rocket_hand")));
        this.shadowRadius = 0.2f;
        addRenderLayer(new AutoGlowingGeoLayer<>(this));
    }

    @Override
    public void render(RocketHand hand, float entityYaw, float partialTick, PoseStack poseStack, MultiBufferSource buffers, int packedLight) {
        LivingEntity owner = hand.getOwner();
        if (owner != null) {
            Vec3 from = hand.getPosition(partialTick);
            Vec3 to = RocketHand.anchor(owner, partialTick);
            renderCable(poseStack, buffers, to.subtract(from), packedLight, 0.07f * Math.max(1f, hand.getScale()));
        }
        poseStack.pushPose();
        float yaw = Mth.rotLerp(partialTick, hand.yRotO, hand.getYRot());
        float pitch = Mth.lerp(partialTick, hand.xRotO, hand.getXRot());
        poseStack.mulPose(Axis.YP.rotationDegrees(yaw));
        poseStack.mulPose(Axis.XP.rotationDegrees(-pitch));
        float s = hand.getScale();
        poseStack.scale(s, s, s);
        super.render(hand, 0, partialTick, poseStack, buffers, packedLight);
        poseStack.popPose();
    }

    /**
     * Vanilla culls an entity by its own tiny hitbox, which made the cable vanish whenever the fist itself was off
     * screen; test the whole span from the fist back to the owner instead (like a leash).
     */
    @Override
    public boolean shouldRender(RocketHand hand, Frustum frustum, double camX, double camY, double camZ) {
        if (super.shouldRender(hand, frustum, camX, camY, camZ)) {
            return true;
        }
        LivingEntity owner = hand.getOwner();
        if (owner == null) {
            return false;
        }
        Vec3 a = hand.position();
        Vec3 b = RocketHand.anchor(owner, 1f);
        return frustum.isVisible(new AABB(a, b).inflate(0.5));
    }

    @Override
    protected void applyRotations(RocketHand animatable, PoseStack poseStack, float ageInTicks, float rotationYaw, float partialTick) {
        // orientation is applied in render()
    }

    /**
     * The cable is a square tube (four quads) so it has width from every viewing angle; it is lit at least like a dim
     * torch so it never turns into a black line in the dark.
     */
    private static void renderCable(PoseStack poseStack, MultiBufferSource buffers, Vec3 delta, int light, float thickness) {
        double length = delta.length();
        if (length < 0.05) {
            return;
        }
        VertexConsumer vc = buffers.getBuffer(RenderType.entityCutoutNoCull(CABLE));
        poseStack.pushPose();
        float yaw = (float) Mth.atan2(delta.x, delta.z);
        float pitch = (float) Mth.atan2(delta.y, delta.horizontalDistance());
        poseStack.mulPose(Axis.YP.rotation(yaw));
        poseStack.mulPose(Axis.XP.rotation(-pitch));
        Matrix4f m = poseStack.last().pose();
        Matrix3f n = poseStack.last().normal();
        float w = thickness;
        float len = (float) length;
        float v = len * 2f;
        int lit = LightTexture.pack(Math.max(LightTexture.block(light), 8), LightTexture.sky(light));
        // top, bottom, left, right sides of the tube
        side(vc, m, n, -w, w, w, w, len, v, lit, 0, 1, 0);
        side(vc, m, n, w, -w, -w, -w, len, v, lit, 0, -1, 0);
        side(vc, m, n, -w, -w, -w, w, len, v, lit, -1, 0, 0);
        side(vc, m, n, w, w, w, -w, len, v, lit, 1, 0, 0);
        poseStack.popPose();
    }

    private static void side(VertexConsumer vc, Matrix4f m, Matrix3f n, float x0, float y0, float x1, float y1, float len, float v, int light,
                             float nx, float ny, float nz) {
        vertex(vc, m, n, x0, y0, 0, 0, 0, light, nx, ny, nz);
        vertex(vc, m, n, x1, y1, 0, 1, 0, light, nx, ny, nz);
        vertex(vc, m, n, x1, y1, len, 1, v, light, nx, ny, nz);
        vertex(vc, m, n, x0, y0, len, 0, v, light, nx, ny, nz);
    }

    private static void vertex(VertexConsumer vc, Matrix4f m, Matrix3f n, float x, float y, float z, float u, float v, int light, float nx, float ny, float nz) {
        vc.vertex(m, x, y, z).color(255, 255, 255, 255).uv(u, v).overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, nx, ny, nz).endVertex();
    }
}
