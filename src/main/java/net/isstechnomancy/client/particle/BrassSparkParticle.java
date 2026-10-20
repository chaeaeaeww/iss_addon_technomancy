package net.isstechnomancy.client.particle;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;
import org.jetbrains.annotations.NotNull;

/**
 * Short-lived hot spark: falls with gravity, cools from bright gold to dark orange, always full-bright.
 */
public class BrassSparkParticle extends TextureSheetParticle {
    private static final float START_R = 1.0f, START_G = 0.86f, START_B = 0.45f;
    private static final float END_R = 0.78f, END_G = 0.36f, END_B = 0.10f;

    protected BrassSparkParticle(ClientLevel level, double x, double y, double z, double xd, double yd, double zd, SpriteSet sprites) {
        super(level, x, y, z, xd, yd, zd);
        this.xd = xd;
        this.yd = yd;
        this.zd = zd;
        this.gravity = 0.6f;
        this.friction = 0.92f;
        this.lifetime = 6 + random.nextInt(5);
        this.quadSize *= 0.45f + random.nextFloat() * 0.25f;
        this.hasPhysics = true;
        this.pickSprite(sprites);
        this.setColor(START_R, START_G, START_B);
    }

    @Override
    public void tick() {
        super.tick();
        float progress = age / (float) lifetime;
        setColor(Mth.lerp(progress, START_R, END_R), Mth.lerp(progress, START_G, END_G), Mth.lerp(progress, START_B, END_B));
        this.alpha = 1.0f - progress * progress;
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
            return new BrassSparkParticle(level, x, y, z, xd, yd, zd, sprites);
        }
    }
}
