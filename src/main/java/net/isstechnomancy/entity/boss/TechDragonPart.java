package net.isstechnomancy.entity.boss;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.entity.PartEntity;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * One hitbox of the Tech Dragon's body (head, two neck sections, chest, hips, four legs, four tail sections, inner and
 * outer half of each wing). Every tick {@link TechDragon#tickParts()} sizes and places it on the bounds of that body
 * region in the animation frame being played, so the boxes cover the model and move with it.
 *
 * <p>Body parts (not the wings) are solid: other entities collide with them like with a boat and the dragon pushes
 * anything that ends up inside them back out, so nothing can stand or get stuck inside the dragon. Hits are forwarded to
 * the dragon with a per-part multiplier (the head is a weak spot, the wings are tough).</p>
 */
public class TechDragonPart extends PartEntity<TechDragon> {
    public final String partName;
    public final float damageMultiplier;
    public final boolean solid;
    private EntityDimensions size = EntityDimensions.scalable(1f, 1f);

    public TechDragonPart(TechDragon parent, String partName, float damageMultiplier, boolean solid) {
        super(parent);
        this.partName = partName;
        this.damageMultiplier = damageMultiplier;
        this.solid = solid;
        this.refreshDimensions();
    }

    /** Places the part on a world-space box (the dragon calls this every tick on both sides). */
    public void place(AABB box) {
        double cx = (box.minX + box.maxX) * 0.5, cz = (box.minZ + box.maxZ) * 0.5;
        float w = (float) Math.max(box.getXsize(), box.getZsize());
        float h = (float) box.getYsize();
        if (Math.abs(size.width - w) > 1e-3 || Math.abs(size.height - h) > 1e-3) {
            size = EntityDimensions.scalable(w, h);
        }
        double ox = getX(), oy = getY(), oz = getZ();
        setPos(cx, box.minY, cz);
        setBoundingBox(box);
        xo = ox;
        yo = oy;
        zo = oz;
        xOld = ox;
        yOld = oy;
        zOld = oz;
    }

    @Override
    protected void defineSynchedData() {
    }

    @Override
    protected void readAdditionalSaveData(@NotNull CompoundTag tag) {
    }

    @Override
    protected void addAdditionalSaveData(@NotNull CompoundTag tag) {
    }

    @Override
    public boolean isPickable() {
        return true;
    }

    @Override
    public boolean canBeCollidedWith() {
        return solid && getParent().isAlive();
    }

    @Nullable
    @Override
    public ItemStack getPickResult() {
        return getParent().getPickResult();
    }

    @Override
    public boolean hurt(@NotNull DamageSource source, float amount) {
        return !isInvulnerableTo(source) && getParent().hurtFromPart(this, source, amount);
    }

    /** Right-clicking any part of the dragon is right-clicking the dragon (mounting the summoned one). */
    @Override
    public @NotNull InteractionResult interact(@NotNull Player player, @NotNull InteractionHand hand) {
        return getParent().interact(player, hand);
    }

    @Override
    public boolean is(@NotNull Entity entity) {
        return this == entity || getParent() == entity;
    }

    @Override
    public @NotNull EntityDimensions getDimensions(@NotNull Pose pose) {
        return size;
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    public @NotNull Packet<ClientGamePacketListener> getAddEntityPacket() {
        throw new UnsupportedOperationException();
    }
}
