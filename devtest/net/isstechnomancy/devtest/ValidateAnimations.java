package net.isstechnomancy.devtest;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.eliotlash.mclib.math.IValue;
import software.bernie.geckolib.core.animation.Animation;
import software.bernie.geckolib.core.animation.EasingType;
import software.bernie.geckolib.core.keyframe.AnimationPoint;
import software.bernie.geckolib.core.keyframe.BoneAnimation;
import software.bernie.geckolib.core.keyframe.Keyframe;
import software.bernie.geckolib.core.keyframe.KeyframeStack;
import software.bernie.geckolib.core.molang.MolangParser;
import software.bernie.geckolib.core.molang.MolangQueries;
import software.bernie.geckolib.loading.object.BakedAnimations;
import software.bernie.geckolib.util.JsonUtil;

import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;

/**
 * Dev-only check (not packaged): parses every animation file of the mod with GeckoLib's own deserializer and evaluates
 * every keyframe through EasingType.lerpWithOverride at several points in time (the code path that crashes the game on
 * bad easing arguments or broken Molang). Also checks the geo files parse with GeckoLib's Gson.
 */
public class ValidateAnimations {
    public static void main(String[] args) throws Exception {
        Path root = Path.of(args[0]);
        int files = 0, anims = 0, frames = 0, errors = 0;
        try (Stream<Path> walk = Files.walk(root)) {
            List<Path> paths = walk.filter(p -> p.toString().endsWith(".animation.json")).toList();
            for (Path p : paths) {
                files++;
                try (Reader r = Files.newBufferedReader(p)) {
                    JsonObject json = JsonParser.parseReader(r).getAsJsonObject();
                    BakedAnimations baked = JsonUtil.GEO_GSON.fromJson(json.getAsJsonObject("animations"), BakedAnimations.class);
                    for (Animation animation : baked.animations().values()) {
                        anims++;
                        for (BoneAnimation bone : animation.boneAnimations()) {
                            for (KeyframeStack<Keyframe<IValue>> stack : List.of(bone.rotationKeyFrames(), bone.positionKeyFrames(), bone.scaleKeyFrames())) {
                                for (List<Keyframe<IValue>> axis : List.of(stack.xKeyframes(), stack.yKeyframes(), stack.zKeyframes())) {
                                    for (Keyframe<IValue> kf : axis) {
                                        for (double time : new double[]{0, 0.13, 0.5, 1.7, 2.9}) {
                                            MolangParser.INSTANCE.setValue(MolangQueries.ANIM_TIME, () -> time);
                                            MolangParser.INSTANCE.setValue(MolangQueries.LIFE_TIME, () -> time);
                                            double start = kf.startValue().get();
                                            double end = kf.endValue().get();
                                            for (double f = 0; f <= 1.0001; f += 0.25) {
                                                AnimationPoint point = new AnimationPoint(kf, kf.length() * f, kf.length(), start, end);
                                                double v = EasingType.lerpWithOverride(point, null);
                                                if (Double.isNaN(v) || Double.isInfinite(v)) {
                                                    throw new IllegalStateException("NaN/Inf value in " + animation.name() + "/" + bone.boneName());
                                                }
                                            }
                                        }
                                        frames++;
                                    }
                                }
                            }
                        }
                    }
                } catch (Exception e) {
                    errors++;
                    System.out.println("ERROR " + root.relativize(p) + ": " + e);
                }
            }
        }
        int geos = 0;
        try (Stream<Path> walk = Files.walk(root)) {
            for (Path p : walk.filter(x -> x.toString().endsWith(".geo.json")).toList()) {
                geos++;
                try (Reader r = Files.newBufferedReader(p)) {
                    software.bernie.geckolib.loading.json.raw.Model model = JsonUtil.GEO_GSON.fromJson(r, software.bernie.geckolib.loading.json.raw.Model.class);
                    software.bernie.geckolib.cache.object.BakedGeoModel baked = software.bernie.geckolib.loading.object.BakedModelFactory.DEFAULT_FACTORY
                            .constructGeoModel(software.bernie.geckolib.loading.object.GeometryTree.fromModel(model));
                    if (baked.topLevelBones().isEmpty()) {
                        throw new IllegalStateException("no bones");
                    }
                } catch (Exception e) {
                    errors++;
                    System.out.println("ERROR " + root.relativize(p) + ": " + e);
                }
            }
        }
        // the names the Java code plays must exist in the files (1.6.0 shipped with prefixed keys: nothing played)
        java.util.Map<String, java.util.List<String>> required = java.util.Map.of(
                "entity/tech_dragon", net.isstechnomancy.entity.boss.DragonAnimationNames.DRAGON,
                "entity/hextech_pylon", net.isstechnomancy.entity.boss.DragonAnimationNames.PYLON,
                "entity/hextech_shell", net.isstechnomancy.entity.boss.DragonAnimationNames.SHELL,
                // 1.10: the turrets (one heavy barrel on the Grand Cannon) and the Hextech Thunderforge
                "entity/brass_sentry", java.util.List.of("spawn", "idle", "overclock", "shoot", "despawn"),
                "entity/siege_sentry", java.util.List.of("spawn", "idle", "overclock", "shoot", "despawn"),
                "block/hextech_thunderforge", java.util.List.of("idle", "charging"));
        for (var e : required.entrySet()) {
            Path file = root.resolve("animations/" + e.getKey() + ".animation.json");
            com.google.gson.JsonObject table = com.google.gson.JsonParser.parseString(Files.readString(file)).getAsJsonObject().getAsJsonObject("animations");
            for (String name : e.getValue()) {
                if (!table.has(name)) {
                    System.out.println("ERROR " + e.getKey() + ": the code plays '" + name + "' but the file has no such animation");
                    errors++;
                }
            }
        }
        System.out.println("Checked " + geos + " geo models");
        System.out.println("Checked " + files + " files, " + anims + " animations, " + frames + " keyframes, " + errors + " errors");
        if (errors > 0) {
            System.exit(1);
        }
    }
}
