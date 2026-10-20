package net.isstechnomancy.devtest;

import net.isstechnomancy.client.model.ProceduralPose;
import software.bernie.geckolib.cache.object.GeoBone;

/**
 * Regression check for the 1.2/1.3 "propeller" bug. Simulates GeckoLib 4.8's per-frame order on real GeoBones
 * (AnimationProcessor.tickAnimation: animated bones get the keyframe value, bones that are NOT marked as changed are
 * reset to their rest pose, then all change markers are cleared; then the model's setCustomAnimations runs) and checks
 * that procedural offsets applied through {@link ProceduralPose} stay bounded, while the old additive code diverges.
 */
public final class ProceduralPoseCheck {
    public static void main(String[] args) {
        int errors = 0;
        errors += run("non-animated bone", false);
        errors += run("animated bone", true);
        errors += runAnimationSwitch();
        // show the old bug really happens under the same simulation
        GeoBone naive = bone("naive");
        for (int f = 0; f < 2000; f++) {
            frame(naive, false, 0f);
            naive.setRotX(naive.getRotX() + 0.1f); // 1.3 code: add to the current rotation
        }
        System.out.println("old additive code after 2000 frames: rotX = " + naive.getRotX() + " rad (should have been 0.1)");
        if (Math.abs(naive.getRotX()) < 10) {
            System.out.println("WARNING: simulation does not reproduce the old bug");
            errors++;
        }
        System.out.println("ProceduralPose checks: " + errors + " errors");
        if (errors > 0) {
            System.exit(1);
        }
    }

    private static GeoBone bone(String name) {
        GeoBone b = new GeoBone(null, name, false, null, false, false);
        b.setRotX(0.3f);
        b.saveInitialSnapshot();
        b.resetStateChanges();
        return b;
    }

    /** GeckoLib's tickAnimation for one bone. */
    private static void frame(GeoBone b, boolean animated, float animValue) {
        if (animated) {
            b.setRotX(animValue + b.getInitialSnapshot().getRotX());
        } else if (!b.hasRotationChanged()) {
            b.setRotX(b.getInitialSnapshot().getRotX());
        }
        b.resetStateChanges();
    }

    private static int run(String label, boolean animated) {
        ProceduralPose pose = new ProceduralPose();
        GeoBone b = bone(label);
        for (int f = 0; f < 2000; f++) {
            float anim = animated ? (float) Math.sin(f * 0.05) * 0.5f : 0f;
            frame(b, animated, anim);
            float offset = (float) Math.sin(f * 0.13) * 0.2f;
            pose.rotate(1L, b, offset, 0, 0);
            float expected = 0.3f + anim + offset;
            if (Math.abs(b.getRotX() - expected) > 1e-4) {
                System.out.println("FAIL " + label + " frame " + f + ": " + b.getRotX() + " expected " + expected);
                return 1;
            }
        }
        System.out.println("ok: " + label);
        return 0;
    }

    /** Animation drives the bone, then stops driving it: the offset must not stack on the stale value. */
    private static int runAnimationSwitch() {
        ProceduralPose pose = new ProceduralPose();
        GeoBone b = bone("switch");
        float lastAnimated = 0;
        for (int f = 0; f < 600; f++) {
            boolean animated = f < 300;
            float anim = 0.4f;
            frame(b, animated, anim);
            pose.rotate(2L, b, 0.1f, 0, 0);
            if (animated) {
                lastAnimated = b.getRotX();
            } else if (Math.abs(b.getRotX() - lastAnimated) > 1e-4) {
                System.out.println("FAIL switch frame " + f + ": " + b.getRotX() + " drifted from " + lastAnimated);
                return 1;
            }
        }
        System.out.println("ok: animation switch (holds, no drift)");
        return 0;
    }
}
