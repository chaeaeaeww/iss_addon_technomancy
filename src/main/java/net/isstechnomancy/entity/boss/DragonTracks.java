package net.isstechnomancy.entity.boss;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.isstechnomancy.ISSTechnomancy;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/**
 * Baked positions of reference points on the Tech Dragon (head, neck, chest, tail sections, wings, jaws, saddle, chest
 * core, forefeet, tail tip) for every animation, one sample per tick, exported by tools/dragon_v4_anims.py from the
 * same animation file the client plays. The server uses them so hitboxes, bites, claw swipes, tail lashes, the breath
 * origin, the grabbed victim and the rider all follow the animation exactly, without running GeckoLib on the server.
 *
 * <p>Model space is Bedrock pixels: +x is the dragon's left, +y up, -z forward (see {@link #toWorld}).</p>
 */
public final class DragonTracks {
    public static final int HEAD = 0, NECK = 1, CHEST = 2, HIPS = 3, TAIL1 = 4, TAIL2 = 5, TAIL3 = 6, WING_L = 7, WING_R = 8,
            WINGTIP_L = 9, WINGTIP_R = 10, MOUTH = 11, SADDLE = 12, CORE = 13, HAND_L = 14, HAND_R = 15, TAIL_TIP = 16;
    private static final String PATH = "/data/" + ISSTechnomancy.MODID + "/tech_dragon/parts.json";

    /** Hitbox regions (order of the "regions" list in parts.json and of the dragon's parts). */
    public static final int R_HEAD = 0, R_NECK_A = 1, R_NECK_B = 2, R_CHEST = 3, R_HIPS = 4, R_LEG_FL = 5, R_LEG_FR = 6, R_LEG_HL = 7, R_LEG_HR = 8,
            R_TAIL_A = 9, R_TAIL_B = 10, R_TAIL_C = 11, R_TAIL_D = 12, R_WING_L_IN = 13, R_WING_L_OUT = 14, R_WING_R_IN = 15, R_WING_R_OUT = 16;
    public static final int REGIONS = 17;

    private record Track(float length, boolean loop, float[][] frames, float[][] boxes) {
    }

    private static Map<String, Track> tracks;
    private static int points;
    private static int regions;

    private DragonTracks() {
    }

    private static synchronized void load() {
        if (tracks != null) {
            return;
        }
        tracks = new HashMap<>();
        try (InputStream in = DragonTracks.class.getResourceAsStream(PATH)) {
            if (in == null) {
                ISSTechnomancy.LOGGER.error("Missing {}", PATH);
                return;
            }
            JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            points = root.getAsJsonArray("points").size();
            regions = root.has("regions") ? root.getAsJsonArray("regions").size() : 0;
            for (Map.Entry<String, com.google.gson.JsonElement> e : root.getAsJsonObject("animations").entrySet()) {
                JsonObject a = e.getValue().getAsJsonObject();
                JsonArray frames = a.getAsJsonArray("frames");
                float[][] data = new float[frames.size()][];
                for (int i = 0; i < frames.size(); i++) {
                    JsonArray row = frames.get(i).getAsJsonArray();
                    float[] f = new float[row.size()];
                    for (int k = 0; k < f.length; k++) {
                        f[k] = row.get(k).getAsFloat();
                    }
                    data[i] = f;
                }
                float[][] boxes = a.has("boxes") ? floats(a.getAsJsonArray("boxes")) : new float[0][];
                tracks.put(e.getKey(), new Track(a.get("length").getAsFloat(), a.get("loop").getAsBoolean(), data, boxes));
            }
        } catch (Exception ex) {
            ISSTechnomancy.LOGGER.error("Could not read {}", PATH, ex);
        }
    }

    private static float[][] floats(JsonArray frames) {
        float[][] data = new float[frames.size()][];
        for (int i = 0; i < frames.size(); i++) {
            JsonArray row = frames.get(i).getAsJsonArray();
            float[] f = new float[row.size()];
            for (int k = 0; k < f.length; k++) {
                f[k] = row.get(k).getAsFloat();
            }
            data[i] = f;
        }
        return data;
    }

    public static int regionCount() {
        load();
        return regions;
    }

    /**
     * Model-space box of a body region at a time of an animation: {centre x, y, z, half x, y, z} in px, the bounds of
     * that region's cubes as the client draws them (baked by tools/dragon_v5_anims.export_boxes).
     */
    public static float[] box(String animation, double seconds, int region, float[] out) {
        load();
        Track t = tracks.get(animation);
        if (t == null || t.boxes.length == 0) {
            t = tracks.get("ground_idle");
        }
        if (t == null || t.boxes.length == 0 || region >= regions) {
            java.util.Arrays.fill(out, 0f);
            return out;
        }
        double s = t.loop && t.length > 0 ? seconds % t.length : Mth.clamp(seconds, 0, t.length);
        double f = s * 20.0;
        int i0 = Mth.clamp((int) Math.floor(f), 0, t.boxes.length - 1);
        int i1 = Math.min(t.boxes.length - 1, i0 + 1);
        float k = (float) Mth.clamp(f - i0, 0, 1);
        float[] a = t.boxes[i0];
        float[] b = t.boxes[i1];
        int o = region * 6;
        for (int j = 0; j < 6; j++) {
            out[j] = Mth.lerp(k, a[o + j], b[o + j]);
        }
        return out;
    }

    public static boolean has(String animation) {
        load();
        return tracks.containsKey(animation);
    }

    /** Length of an animation in seconds (0 if unknown). */
    public static float length(String animation) {
        load();
        Track t = tracks.get(animation);
        return t == null ? 0 : t.length;
    }

    /** Model-space position (px) of a point at a time (seconds) of an animation; loops wrap, others clamp. */
    public static Vec3 point(String animation, double seconds, int index) {
        load();
        Track t = tracks.get(animation);
        if (t == null || index >= points) {
            t = tracks.get("ground_idle");
            if (t == null) {
                return Vec3.ZERO;
            }
        }
        double s = t.loop && t.length > 0 ? seconds % t.length : Mth.clamp(seconds, 0, t.length);
        double f = s * 20.0;
        int i0 = Mth.clamp((int) Math.floor(f), 0, t.frames.length - 1);
        int i1 = Math.min(t.frames.length - 1, i0 + 1);
        double k = Mth.clamp(f - i0, 0, 1);
        float[] a = t.frames[i0];
        float[] b = t.frames[i1];
        int o = index * 3;
        return new Vec3(Mth.lerp(k, a[o], b[o]), Mth.lerp(k, a[o + 1], b[o + 1]), Mth.lerp(k, a[o + 2], b[o + 2]));
    }

    /**
     * Model point (px) to world, for a dragon at {@code origin} facing {@code yawDeg} (body yaw), drawn at
     * {@code scale}, pitched by {@code pitchDeg} (positive = nose up) about the flight pivot.
     * GeckoLib bakes Bedrock +x as -x and turns the model by 180 - yaw, so +x lands on the dragon's left.
     */
    public static Vec3 toWorld(Vec3 model, Vec3 origin, float yawDeg, float pitchDeg, float scale) {
        double x = model.x, y = model.y, z = model.z;
        if (pitchDeg != 0) {
            double py = 27, pz = -10;
            double t = Math.toRadians(pitchDeg);
            double dy = y - py, dz = z - pz;
            y = py + Math.cos(t) * dy - Math.sin(t) * dz;
            z = pz + Math.sin(t) * dy + Math.cos(t) * dz;
        }
        double yaw = Math.toRadians(yawDeg);
        double lx = Math.cos(yaw), lz = Math.sin(yaw);       // dragon's left
        double fx = -Math.sin(yaw), fz = Math.cos(yaw);      // forward
        double s = scale / 16.0;
        return origin.add((x * lx - z * fx) * s, y * s, (x * lz - z * fz) * s);
    }
}
