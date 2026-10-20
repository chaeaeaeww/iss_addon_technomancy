package net.isstechnomancy.client.particle;

import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Camera;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;

/**
 * A flat cog rune lying on the ground (not camera-facing). Spins at ~90°/s, fades in, holds, then fades out.
 */
public class CogSigilParticle extends TextureSheetParticle {
    private static final float RADIUS = 1.1f;
    private static final float SPIN_PER_TICK = 4.5f * Mth.DEG_TO_RAD;

    private float angle;
    private float angleO;

    protected CogSigilParticle(ClientLevel level, double x, double y, double z, SpriteSet sprites) {
        super(level, x, y, z, 0, 0, 0);
        this.xd = 0;
        this.yd = 0;
        this.zd = 0;
        this.gravity = 0;
        this.hasPhysics = false;
        this.lifetime = 30;
        this.angle = random.nextFloat() * Mth.TWO_PI;
        this.angleO = angle;
        this.pickSprite(sprites);
        // Brass #C8913A
        this.setColor(0xC8 / 255f, 0x91 / 255f, 0x3A / 255f);
        this.alpha = 0;
    }

    @Override
    public void tick() {
        super.tick();
        angleO = angle;
        angle += SPIN_PER_TICK;
        float progress = age / (float) lifetime;
        if (progress < 0.2f) {
            alpha = progress / 0.2f;
        } else if (progress > 0.7f) {
            alpha = (1.0f - progress) / 0.3f;
        } else {
            alpha = 1.0f;
        }
        alpha *= 0.85f;
    }

    @Override
    public void render(@NotNull VertexConsumer consumer, Camera camera, float partialTick) {
        Vec3 cameraPos = camera.getPosition();
        float x = (float) (Mth.lerp(partialTick, xo, this.x) - cameraPos.x());
        float y = (float) (Mth.lerp(partialTick, yo, this.y) - cameraPos.y());
        float z = (float) (Mth.lerp(partialTick, zo, this.z) - cameraPos.z());
        float rotation = Mth.lerp(partialTick, angleO, angle);
        float cos = Mth.cos(rotation) * RADIUS;
        float sin = Mth.sin(rotation) * RADIUS;
        // Corners of a square rotated around the Y axis, lying flat on the XZ plane.
        float[][] corners = {
                {-cos + sin, -sin - cos},
                {-cos - sin, -sin + cos},
                {cos - sin, sin + cos},
                {cos + sin, sin - cos}
        };
        float u0 = getU0(), u1 = getU1(), v0 = getV0(), v1 = getV1();
        float[][] uvs = {{u1, v1}, {u1, v0}, {u0, v0}, {u0, v1}};
        int light = getLightColor(partialTick);
        // Upward-facing side
        for (int i = 0; i < 4; i++) {
            consumer.vertex(x + corners[i][0], y, z + corners[i][1]).uv(uvs[i][0], uvs[i][1]).color(rCol, gCol, bCol, alpha).uv2(light).endVertex();
        }
        // Downward-facing side, so the sigil is visible when cast on a ledge above the viewer
        for (int i = 3; i >= 0; i--) {
            consumer.vertex(x + corners[i][0], y, z + corners[i][1]).uv(uvs[i][0], uvs[i][1]).color(rCol, gCol, bCol, alpha).uv2(light).endVertex();
        }
    }

    @Override
    protected int getLightColor(float partialTick) {
        return 0xF000F0;
    }

    @Override
    public @NotNull ParticleRenderType getRenderType() {
        return ParticleRenderType.PARTICLE_SHEET_TRANSLUCENT;
    }

    public static class Provider implements ParticleProvider<SimpleParticleType> {
        private final SpriteSet sprites;

        public Provider(SpriteSet sprites) {
            this.sprites = sprites;
        }

        @Override
        public Particle createParticle(@NotNull SimpleParticleType type, @NotNull ClientLevel level, double x, double y, double z, double xd, double yd, double zd) {
            return new CogSigilParticle(level, x, y, z, sprites);
        }
    }
}
