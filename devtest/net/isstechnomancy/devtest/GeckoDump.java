package net.isstechnomancy.devtest;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.cache.object.GeoBone;
import software.bernie.geckolib.cache.object.GeoCube;
import software.bernie.geckolib.cache.object.GeoQuad;
import software.bernie.geckolib.cache.object.GeoVertex;
import software.bernie.geckolib.core.animation.Animation;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.EasingType;
import software.bernie.geckolib.core.keyframe.AnimationPoint;
import software.bernie.geckolib.core.keyframe.BoneAnimation;
import software.bernie.geckolib.core.keyframe.KeyframeStack;
import software.bernie.geckolib.core.object.Axis;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.core.state.BoneSnapshot;
import software.bernie.geckolib.loading.json.raw.Model;
import software.bernie.geckolib.loading.object.BakedAnimations;
import software.bernie.geckolib.loading.object.BakedModelFactory;
import software.bernie.geckolib.loading.object.GeometryTree;
import software.bernie.geckolib.util.JsonUtil;
import software.bernie.geckolib.util.RenderUtils;
import org.joml.Vector4f;

import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Dev-only: poses a model exactly the way GeckoLib does in game (its own geo baking, its own keyframe evaluation via
 * AnimationController, its own bone/cube matrix code from RenderUtils) and writes every textured quad to JSON, so
 * tools/render_v4.py can draw what the game draws and compare it with the Python preview.
 *
 * <p>Args: geo.json animation.json out.json [animation time]... (time in seconds; "-" = no animation).</p>
 */
public final class GeckoDump {
    public static void main(String[] args) throws Exception {
        Model model = JsonUtil.GEO_GSON.fromJson(Files.readString(Path.of(args[0])), Model.class);
        BakedGeoModel baked = BakedModelFactory.DEFAULT_FACTORY.constructGeoModel(GeometryTree.fromModel(model));
        JsonObject animRoot = JsonParser.parseString(Files.readString(Path.of(args[1]))).getAsJsonObject();
        BakedAnimations anims = JsonUtil.GEO_GSON.fromJson(animRoot.getAsJsonObject("animations"), BakedAnimations.class);
        Map<String, GeoBone> bones = new HashMap<>();
        for (GeoBone b : baked.topLevelBones()) {
            collect(b, bones);
        }
        Map<String, BoneSnapshot> initial = new HashMap<>();
        for (GeoBone b : bones.values()) {
            b.saveInitialSnapshot();
            initial.put(b.getName(), b.getInitialSnapshot());
        }
        AnimationController<?> ctrl = new AnimationController<>(null, s -> PlayState.STOP);
        Method point = AnimationController.class.getDeclaredMethod("getAnimationPointAtTick", List.class, double.class, boolean.class, Axis.class);
        point.setAccessible(true);
        JsonArray frames = new JsonArray();
        for (int i = 3; i + 1 < args.length; i += 2) {
            for (GeoBone b : bones.values()) {
                BoneSnapshot s = initial.get(b.getName());
                b.setRotX(s.getRotX());
                b.setRotY(s.getRotY());
                b.setRotZ(s.getRotZ());
                b.setPosX(0);
                b.setPosY(0);
                b.setPosZ(0);
                b.setScaleX(1);
                b.setScaleY(1);
                b.setScaleZ(1);
            }
            if (!args[i].equals("-")) {
                Animation anim = anims.getAnimation(args[i]);
                if (anim == null) {
                    throw new IllegalArgumentException("no animation " + args[i]);
                }
                double tick = Double.parseDouble(args[i + 1]) * 20.0;
                for (BoneAnimation ba : anim.boneAnimations()) {
                    GeoBone b = bones.get(ba.boneName());
                    if (b == null) {
                        continue;
                    }
                    BoneSnapshot s = initial.get(b.getName());
                    KeyframeStack<?> rot = ba.rotationKeyFrames();
                    if (!rot.xKeyframes().isEmpty()) {
                        b.setRotX((float) value(point, ctrl, rot.xKeyframes(), tick, true, Axis.X) + s.getRotX());
                        b.setRotY((float) value(point, ctrl, rot.yKeyframes(), tick, true, Axis.Y) + s.getRotY());
                        b.setRotZ((float) value(point, ctrl, rot.zKeyframes(), tick, true, Axis.Z) + s.getRotZ());
                    }
                    KeyframeStack<?> pos = ba.positionKeyFrames();
                    if (!pos.xKeyframes().isEmpty()) {
                        b.setPosX((float) value(point, ctrl, pos.xKeyframes(), tick, false, Axis.X));
                        b.setPosY((float) value(point, ctrl, pos.yKeyframes(), tick, false, Axis.Y));
                        b.setPosZ((float) value(point, ctrl, pos.zKeyframes(), tick, false, Axis.Z));
                    }
                    KeyframeStack<?> sc = ba.scaleKeyFrames();
                    if (!sc.xKeyframes().isEmpty()) {
                        b.setScaleX((float) value(point, ctrl, sc.xKeyframes(), tick, false, Axis.X));
                        b.setScaleY((float) value(point, ctrl, sc.yKeyframes(), tick, false, Axis.Y));
                        b.setScaleZ((float) value(point, ctrl, sc.zKeyframes(), tick, false, Axis.Z));
                    }
                }
            }
            JsonArray quads = new JsonArray();
            PoseStack stack = new PoseStack();
            for (GeoBone b : baked.topLevelBones()) {
                render(stack, b, quads);
            }
            JsonObject frame = new JsonObject();
            frame.addProperty("animation", args[i]);
            frame.addProperty("time", args[i + 1]);
            frame.add("quads", quads);
            frames.add(frame);
        }
        Files.writeString(Path.of(args[2]), frames.toString());
        System.out.println("GeckoDump: wrote " + frames.size() + " frames to " + args[2]);
    }

    private static double value(Method point, AnimationController<?> ctrl, List<?> frames, double tick, boolean rotation, Axis axis) throws Exception {
        AnimationPoint p = (AnimationPoint) point.invoke(ctrl, frames, tick, rotation, axis);
        return EasingType.lerpWithOverride(p, null);
    }

    private static void collect(GeoBone b, Map<String, GeoBone> out) {
        out.put(b.getName(), b);
        for (GeoBone c : b.getChildBones()) {
            collect(c, out);
        }
    }

    /** GeoRenderer.renderRecursively / renderCube matrix order. */
    private static void render(PoseStack stack, GeoBone bone, JsonArray out) {
        stack.pushPose();
        RenderUtils.prepMatrixForBone(stack, bone);
        if (!bone.isHidden()) {
            for (GeoCube cube : bone.getCubes()) {
                stack.pushPose();
                RenderUtils.translateToPivotPoint(stack, cube);
                RenderUtils.rotateMatrixAroundCube(stack, cube);
                RenderUtils.translateAwayFromPivotPoint(stack, cube);
                for (GeoQuad quad : cube.quads()) {
                    if (quad == null) {
                        continue;
                    }
                    JsonArray q = new JsonArray();
                    for (GeoVertex v : quad.vertices()) {
                        Vector4f p = stack.last().pose().transform(new Vector4f(v.position().x(), v.position().y(), v.position().z(), 1f));
                        JsonArray vv = new JsonArray();
                        vv.add(p.x());
                        vv.add(p.y());
                        vv.add(p.z());
                        vv.add(v.texU());
                        vv.add(v.texV());
                        q.add(vv);
                    }
                    out.add(q);
                }
                stack.popPose();
            }
        }
        if (!bone.isHidingChildren()) {
            for (GeoBone child : bone.getChildBones()) {
                render(stack, child, out);
            }
        }
        stack.popPose();
    }
}
