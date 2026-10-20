package net.isstechnomancy.client.model;

import software.bernie.geckolib.core.animatable.model.CoreGeoBone;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Applies procedural rotation offsets on top of GeckoLib animations without ever accumulating them.
 *
 * <p>Why this exists: GeckoLib 4's {@code GeoBone.setRotX/Y/Z} marks the bone as changed. The animation processor only
 * resets a bone to its rest pose when it is <i>not</i> marked, so the naive {@code bone.setRotX(bone.getRotX() + x)}
 * in {@code setCustomAnimations} made every bone the current animation does not drive (the dragon's root, part of its
 * neck, the Technomancer's back arm...) keep last frame's value and add the offset again, every frame: the dragon spun
 * like a propeller while climbing/diving and froze at a random angle (standing on its tail) once it landed.</p>
 *
 * <p>Here we remember, per entity and bone, the value we wrote and the offset we added. If the bone still holds exactly
 * what we wrote, nothing animated it since, so our previous offset is removed before the new one is added; otherwise
 * the animation set a fresh value this frame and the offset goes on top of that.</p>
 */
public final class ProceduralPose {
    private static final int MAX_ENTITIES = 256;

    private final Map<Long, Map<String, float[]>> applied = new LinkedHashMap<>(64, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<Long, Map<String, float[]>> eldest) {
            return size() > MAX_ENTITIES;
        }
    };

    /** Adds a rotation offset (radians, GeckoLib bone space) to the bone for this frame. */
    public void rotate(long instanceId, CoreGeoBone bone, float x, float y, float z) {
        if (bone == null) {
            return;
        }
        Map<String, float[]> bones = applied.computeIfAbsent(instanceId, k -> new HashMap<>());
        float[] last = bones.get(bone.getName());
        float bx = bone.getRotX();
        float by = bone.getRotY();
        float bz = bone.getRotZ();
        if (last != null) {
            if (bx == last[0]) {
                bx -= last[3];
            }
            if (by == last[1]) {
                by -= last[4];
            }
            if (bz == last[2]) {
                bz -= last[5];
            }
        } else {
            last = new float[6];
            bones.put(bone.getName(), last);
        }
        float nx = bx + x;
        float ny = by + y;
        float nz = bz + z;
        bone.setRotX(nx);
        bone.setRotY(ny);
        bone.setRotZ(nz);
        last[0] = nx;
        last[1] = ny;
        last[2] = nz;
        last[3] = x;
        last[4] = y;
        last[5] = z;
    }

    /** Sets a rotation relative to the bone's rest pose (for bones no animation drives). */
    public static void setFromRest(CoreGeoBone bone, float x, float y, float z) {
        if (bone == null) {
            return;
        }
        bone.setRotX(bone.getInitialSnapshot().getRotX() + x);
        bone.setRotY(bone.getInitialSnapshot().getRotY() + y);
        bone.setRotZ(bone.getInitialSnapshot().getRotZ() + z);
    }
}
