package net.isstechnomancy.client.model;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.boss.TechDragon;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import software.bernie.geckolib.core.animatable.model.CoreGeoBone;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;

/**
 * Procedural posing on top of the baked animations (Tech Dragon v4/v5 rig): flight pitch and bank on the "flight" bone,
 * the head look spread over the neck controllers (neck1c..neck4c, headc) and tail drag on the tail controllers.
 *
 * <p>Those controller bones are never touched by any animation, and here they always get an ABSOLUTE rotation (never
 * "current + offset"), so nothing can pile up frame after frame - the cause of the old dragon spinning like a propeller
 * and standing on its tail.</p>
 */
public class TechDragonModel extends DefaultedEntityGeoModel<TechDragon> {
    private static final ResourceLocation OVERCHARGED = ISSTechnomancy.id("textures/entity/tech_dragon_overcharged.png");
    /** 1.9: overload / EMP - the glowing parts dead grey (its glowmask has only a few embers). */
    private static final ResourceLocation DRAINED = ISSTechnomancy.id("textures/entity/tech_dragon_drained.png");
    private static final String[] NECK = {"neck1c", "neck2c", "neck3c", "neck4c", "headc"};
    private static final float[] NECK_YAW = {0.12f, 0.18f, 0.22f, 0.22f, 0.26f};
    private static final float[] NECK_PITCH = {0.06f, 0.1f, 0.14f, 0.18f, 0.22f};
    private static final String[] TAIL = {"tail1c", "tail2c", "tail3c", "tail4c", "tail5c", "tail6c", "tail7c", "tail8c"};
    private static final float[] TAIL_WEIGHT = {0.15f, 0.2f, 0.25f, 0.3f, 0.35f, 0.4f, 0.45f, 0.5f};
    /** Phase-two growth: glowing crystal fins and hex scales (tools/dragon_v5.py "oc_*" bones), in growth order from the
     * shoulders out along the neck and the tail. */
    private static final String[] GROWTH = {"oc_ribs", "oc_chest", "oc_neck1c", "oc_hips", "oc_neck2c", "oc_tail1c", "oc_neck3c", "oc_tail2c",
            "oc_neck4c", "oc_tail3c", "oc_tail4c", "oc_tail5c", "oc_tail6c"};

    public TechDragonModel() {
        super(ISSTechnomancy.id("tech_dragon"));
    }

    @Override
    public ResourceLocation getTextureResource(TechDragon animatable) {
        return animatable.isDrained() ? DRAINED : animatable.isPhaseTwo() ? OVERCHARGED : super.getTextureResource(animatable);
    }

    @Override
    public void setCustomAnimations(TechDragon dragon, long instanceId, AnimationState<TechDragon> state) {
        super.setCustomAnimations(dragon, instanceId, state);
        float pt = state.getPartialTick();
        TechDragon.State s = dragon.getState();
        boolean alive = s != TechDragon.State.DEATH && s != TechDragon.State.SPAWN;
        // flight attitude
        set("flight", alive ? -dragon.getFlightPitch(pt) : 0, 0, alive ? -dragon.getBank(pt) : 0);
        // the head tracks its target only while idle / moving / hovering; attacks own the neck
        boolean free = alive && switch (s) {
            case GROUND, PERCH, HOVER, LANDING, RIDDEN, PYLON_CHARGE, BREATH, GBREATH, COG_SPIT, ARC_BARRAGE, SUMMON -> true;
            default -> false;
        };
        if (s == TechDragon.State.PERCH && dragon.getIdleVariant() == 2) {
            free = false;
        }
        float yaw = 0f, look = 0f;
        if (free) {
            float bodyYaw = Mth.rotLerp(pt, dragon.yBodyRotO, dragon.yBodyRot);
            float headYaw = Mth.rotLerp(pt, dragon.yHeadRotO, dragon.yHeadRot);
            yaw = Mth.clamp(Mth.wrapDegrees(headYaw - bodyYaw), -70, 70);
            look = Mth.clamp(dragon.getViewXRot(pt), -35, 30);
        }
        for (int i = 0; i < NECK.length; i++) {
            set(NECK[i], look * NECK_PITCH[i], yaw * NECK_YAW[i], 0);
        }
        float drag = alive ? dragon.getTailDrag(pt) : 0f;
        for (int i = 0; i < TAIL.length; i++) {
            set(TAIL[i], 0, drag * TAIL_WEIGHT[i], 0);
        }
        // phase two: the fins burst out during the overcharge roar (from 0.7 s), front to back, with a little overshoot
        float grow = !dragon.isPhaseTwo() ? 0f : s == TechDragon.State.PHASE_TWO ? (dragon.getStateTicks() + pt - 14f) / 30f : 99f;
        for (int i = 0; i < GROWTH.length; i++) {
            float k = Mth.clamp(grow - i * 0.06f, 0f, 1f);
            float scale = k >= 1f ? 1f : k * (1f + 0.25f * Mth.sin(k * Mth.PI));
            CoreGeoBone bone = getAnimationProcessor().getBone(GROWTH[i]);
            if (bone != null) {
                bone.setHidden(scale < 0.02f);
                float v = Math.max(0.02f, scale);
                bone.setScaleX(v);
                bone.setScaleY(v);
                bone.setScaleZ(v);
            }
        }
    }

    /** Absolute rotation in Bedrock degrees (GeckoLib stores x and y negated). */
    private void set(String name, float x, float y, float z) {
        CoreGeoBone bone = getAnimationProcessor().getBone(name);
        if (bone != null) {
            bone.setRotX(-x * Mth.DEG_TO_RAD);
            bone.setRotY(-y * Mth.DEG_TO_RAD);
            bone.setRotZ(z * Mth.DEG_TO_RAD);
        }
    }
}
