package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.isstechnomancy.entity.boss.DragonDebris;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;
import org.jetbrains.annotations.NotNull;

/** A tumbling copy of the torn-up block (its normal block model), a little smaller than a full block. */
public class DragonDebrisRenderer extends EntityRenderer<DragonDebris> {
    public DragonDebrisRenderer(EntityRendererProvider.Context context) {
        super(context);
        this.shadowRadius = 0.3f;
    }

    @Override
    public void render(@NotNull DragonDebris debris, float yaw, float partialTick, @NotNull PoseStack pose, @NotNull MultiBufferSource buffers, int light) {
        BlockState block = debris.getBlock();
        if (block.getRenderShape() != RenderShape.MODEL) {
            return;
        }
        float size = 0.55f + (debris.getId() % 5) * 0.09f;
        float spin = debris.spin(partialTick);
        pose.pushPose();
        pose.translate(0, size * 0.5, 0);
        pose.mulPose(Axis.YP.rotationDegrees(spin * 0.6f));
        pose.mulPose(Axis.XP.rotationDegrees(spin));
        pose.scale(size, size, size);
        pose.translate(-0.5, -0.5, -0.5);
        Minecraft.getInstance().getBlockRenderer().renderSingleBlock(block, pose, buffers, light, OverlayTexture.NO_OVERLAY);
        pose.popPose();
        super.render(debris, yaw, partialTick, pose, buffers, light);
    }

    @Override
    public @NotNull ResourceLocation getTextureLocation(@NotNull DragonDebris debris) {
        return TextureAtlas.LOCATION_BLOCKS;
    }
}
