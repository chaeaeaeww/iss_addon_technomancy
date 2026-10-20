package net.isstechnomancy.client.particle;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;
import org.jetbrains.annotations.NotNull;

/**
 * Soft steam cloud: drifts upward, grows to ~2.5x its size and fades out. Animates through its sprite set by age.
 */
public class SteamPuffParticle extends TextureSheetParticle {
    private final SpriteSet sprites;
    private final float startSize;

    protected SteamPuffParticle(ClientLevel level, double x, double y, double z, double xd, double yd, double zd, SpriteSet sprites) {
        super(level, x, y, z, xd, yd, zd);
        this.sprites = sprites;
        this.xd = xd;
        this.yd = yd + 0.02;
        this.zd = zd;
        this.gravity = -0.02f;
        this.friction = 0.9f;
        this.lifetime = 30 + random.nextInt(12);
        this.startSize = this.quadSize * (1.2f + random.nextFloat() * 0.6f);
        this.quadSize = startSize;
        float grey = 0.82f + random.nextFloat() * 0.12f;
        this.setColor(grey, grey, grey);
        this.alpha = 0.7f;
        this.setSpriteFromAge(sprites);
    }

    @Override
    public void tick() {
        super.tick();
        if (!removed) {
            setSpriteFromAge(sprites);
            float progress = age / (float) lifetime;
            this.quadSize = startSize * (1.0f + progress * 1.5f);
            this.alpha = 0.7f * (1.0f - progress);
        }
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
            return new SteamPuffParticle(level, x, y, z, xd, yd, zd, sprites);
        }
    }
}
