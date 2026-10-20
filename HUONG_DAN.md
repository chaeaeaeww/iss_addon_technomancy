# Iron's Technomancy — Addon hệ Cơ Khí Phép cho Iron's Spells 'n Spellbooks

**Nền tảng:** Minecraft 1.20.1 · Forge 47.4.0+ · Iron's Spells 'n Spellbooks **1.20.1-3.16.3** · GeckoLib 4.8.2 · PlayerAnimator 1.0.2-rc1 · Curios 5.14.1
**Mod ID:** `iss_technomancy` · **Package:** `net.isstechnomancy`

---

## 1. Cấu trúc thư mục

```
iss_technomancy/
├── build.gradle, settings.gradle, gradle.properties, gradlew(.bat), gradle/wrapper/
├── libs/irons_spellbooks-1.20.1-3.16.3.jar      ← ISS 1.20.1 không có trên maven công khai
├── tools/generate_assets.py                    ← sinh model/animation GeckoLib, animation người chơi, mọi texture
├── tools/generate_data.py                      ← sinh sounds.json, lang, recipe, loot, tag, ngọc, Patchouli
├── tools/pixelart.py, sprites.py, armor.py, models.py ← bảng màu steampunk + code vẽ item/icon/giáp/entity
└── src/main/
    ├── java/net/isstechnomancy/
    │   ├── ISSTechnomancy.java                 ← @Mod, đăng ký mọi DeferredRegister
    │   ├── registry/
    │   │   ├── TechSchools.java                ← SchoolType "iss_technomancy:technomancy" (màu #C8913A)
    │   │   ├── TechAttributes.java             ← technomancy_spell_power / technomancy_magic_resist
    │   │   ├── TechSpells.java                 ← 3 phép, đăng ký vào SpellRegistry.SPELL_REGISTRY_KEY
    │   │   ├── TechEntities.java, TechItems.java, TechSounds.java, TechParticles.java
    │   │   ├── TechTags.java (focus tag + damage type), TechAnimations.java, TechCreativeTabs.java
    │   ├── spells/   GearBarrageSpell, ArcWelderSpell, DeployBrassSentrySpell
    │   ├── entity/   GearProjectile, ArcWelderBeam, BrassSentry, SentryBolt
    │   ├── item/     TechArmorMaterials, ClockworkEngineerArmorItem
    │   └── client/   ClientSetup, renderer/*, model/*, particle/*
    └── resources/
        ├── META-INF/mods.toml, pack.mcmeta
        ├── assets/iss_technomancy/
        │   ├── geo/ (giáp + entity/*.geo.json)      animations/ (giáp + entity/*.animation.json)
        │   ├── player_animation/technomancy_animations.json   ← PlayerAnimator
        │   ├── particles/*.json  textures/{particle,item,entity,models/armor,gui/spell_icons}
        │   ├── models/item/*.json  sounds.json  lang/en_us.json  lang/vi_vn.json
        ├── assets/apotheosis/ (model + texture ngọc)
        ├── assets/irons_spellbooks/patchouli_books/iss_guide_book/{en_us,vi_vn}/entries/technomancy.json
        └── data/
            ├── iss_technomancy/{damage_type, tags, recipes, loot_tables, loot_modifiers, gems,
            │                    irons_spellbooks/upgrade_orb_type/technomancy_power.json}
            ├── irons_spellbooks/tags/items/{school_focus, inscribed_rune, staff, armors/*}.json
            └── forge/loot_modifiers/global_loot_modifiers.json
```

---

## 2. Build

### Yêu cầu
- **JDK 17** (ví dụ Eclipse Temurin 17). Java 8 sẽ không chạy được ForgeGradle 6.
- Lần build đầu cần Internet (tải Minecraft, Forge, mapping Parchment, GeckoLib, Curios, PlayerAnimator, irons_lib) — khoảng 1–2 GB vào `~/.gradle`.

### Lệnh
```bash
./gradlew build
```
Kết quả: `build/libs/iss_technomancy-1.20.1-1.0.0.jar` (đã reobf, chạy được trong game thật).

Chạy thử trong môi trường dev (client có sẵn ISS + phụ thuộc):
```bash
./gradlew runClient
```

### Cài vào game
Thả vào thư mục `mods/`: `iss_technomancy-1.20.1-1.0.0.jar` + `irons_spellbooks-1.20.1-3.16.3.jar` + `irons_lib`, `geckolib`, `curios`, `playeranimator` đúng phiên bản ở đầu file. Patchouli và Apotheosis là tùy chọn — nếu có, entry sách và ngọc tự xuất hiện.

### Lỗi thường gặp
| Lỗi | Cách xử lý |
|---|---|
| `Unsupported class file major version` / Gradle báo cần Java 17 | Đặt `JAVA_HOME` trỏ tới JDK 17. |
| `java.io.IOException: Unable to establish loopback connection` | JDK 17 trên Windows tạo Unix socket trong `%TEMP%`; nếu đường dẫn TEMP là dạng rút gọn có `~` (vd. `C:\Users\QUOCBA~1\...`) thì socket lỗi. Chạy trước khi build: `set JAVA_TOOL_OPTIONS=-Djdk.net.unixdomain.tmpdir=C:\Users\Public` (PowerShell: `$env:JAVA_TOOL_OPTIONS='-Djdk.net.unixdomain.tmpdir=C:\Users\Public'`). |
| `Could not find blank:irons_spellbooks` | Thiếu file `libs/irons_spellbooks-1.20.1-3.16.3.jar`. |
| Đường dẫn dự án quá dài (Windows) | Đặt dự án ở thư mục ngắn, vd. `D:\Mods\iss_technomancy`. |

---

## 3. Bảng chỉ số đã cài đặt (khớp bản thiết kế đã duyệt)

| Phép | Loại · Độ hiếm · Max | Sức mạnh (spell power) | Công thức | Mana | CD | Cast |
|---|---|---|---|---|---|---|
| Gear Barrage | Instant · Common · 10 | 8 + 1/lv | 3 bánh răng × (power × 0.35), nảy 1 lần | 15 + 2/lv | 2s | 0 |
| Arc Welder | Continuous · Uncommon · 8 | 2 + 1/lv | 1 + power × 0.6 mỗi 10 tick, Slowness I 1.25s, tầm 6 | 4 + 1/lv **mỗi nhịp** | 10s | 80 tick |
| Deploy Brass Sentry | Long · Rare · 5 | 10 + 3/lv | bolt = power × 0.25 / 1s (Overclock: 13 tick) | 60 + 15/lv | 45s | 30 tick |
| Steam Vent | Instant · Uncommon · 8 | 4 + 1/lv | nón 60°, tầm 5: power × 0.5, đẩy lùi 0.9 + 0.08/lv, Blindness 2s | 25 + 3/lv | 8s | 0 |
| Overdrive Protocol | Instant · Epic · 3 | — | buff Overdrive 15s + 5s/lv, cường hoá phép Technomancy kế tiếp | 80 + 20/lv | 60s | 0 |
| Assemble Automaton | Long · Rare · 5 | 6 + 2/lv | đấm = power × 0.6, loạt 3 bánh răng × power × 0.3 / 5s | 70 + 15/lv | 90s | 40 tick |

> `baseSpellPower` của ISS là kiểu `int`, nên Brass Sentry dùng **10 + 3/lv × 0.25** thay cho "5 + 1.5/lv × 0.5" — kết quả giống hệt (2.5 / 4.0 / 5.5).

Brass Sentry: HP `20 + 6/lv`, giáp 6, tồn tại `15s + 3s/lv`, tầm bắn 16, 1 tháp/người (niệm lại thì tháp cũ gập lại và biến mất), tự huỷ khi chủ chết/out/cách > 48 khối. Arc Welder bắn trúng tháp của mình: +2 HP, +1s (không vượt thời lượng gốc), Overclock 3s.

Assemble Automaton: HP `30 + 8/lv`, tồn tại `60s + 15s/lv`, 1 con/người, đi theo chủ, đánh kẻ đánh chủ / kẻ chủ vừa đánh.

**Overdrive — bản cường hoá của phép kế tiếp** (buff bị tiêu hao khi niệm):

| Phép gốc | Bản Overdrive |
|---|---|
| Gear Barrage | 5 bánh răng, nảy 2 lần, xuyên 1 mục tiêu, +25% sát thương |
| Arc Welder | tia hồ quang nảy sang 2 kẻ địch trong 4 khối (50% sát thương) suốt lần kênh |
| Steam Vent | hơi siêu nóng: tầm 7, nón 80°, đốt cháy 4s, lực đẩy ×1.6 |
| Deploy Brass Sentry | **Siege Sentry**: nòng đôi bắn luân phiên đạn nổ (sát thương ×1.5, nổ bán kính 2), HP ×1.8, tồn tại ×1.25, tầm 20, giáp 10 |
| Assemble Automaton | **Automaton Mk.II**: to ×1.35, HP ×1.6, sát thương ×1.5, loạt 5 bánh răng, hồi loạt nhanh hơn; màu vàng–đỏ thẫm, mắt cam |

**Clockwork Automaton (mob, có spawn egg):** bản hoang dã thù địch với người chơi — 40 HP, 8 giáp, đấm 6, mỗi 5s phun 3 bánh răng (3 sát thương) ở tầm 3–14 khối. Rơi 1–3 Arcane Cog, 1–4 thỏi đồng, 8% Technomancy Rune, 5% scroll Technomancy (khi người chơi giết). Hiện chỉ xuất hiện qua spawn egg (chưa spawn tự nhiên).

Mọi số đều chỉnh được không cần build lại qua hệ thống spell config của ISS (thư mục `config/irons_spellbooks_spell_config/` hoặc datapack `data/<ns>/irons_spellbooks_spell_config/`: power/mana multiplier, cooldown, max level, rarity, bật/tắt phép) vì addon dùng `DefaultConfig` chuẩn.

Trang bị:
- **Clockwork Engineer** (4 món): +125 Max Mana, +10% Technomancy Power, +5% Spell Power mỗi món; giáp 3/8/6/3 như bộ Pyromancer. Chế: giáp Wizard + Technomancy Rune + Arcane Essence (bàn chế tạo hoặc bàn rèn).
- **Clockwork Scepter**: 4 sát thương, +15% Technomancy Power, +10% Cooldown Reduction, +5% Spell Power.
- **Technomancy Upgrade Orb**: +5% Technomancy Power (orb type datapack `technomancy_power`).
- **Ngọc Apotheosis "Clockwork Gem"**: 1% → 15% Technomancy Power theo bậc, như ngọc Fire của ISS.
- Scroll và Affinity Ring dùng item chung của ISS; texture riêng `scroll_technomancy` / `affinity_ring_technomancy` được ISS tự nạp. Loot thêm vào rương dungeon, mineshaft, thợ rèn làng, ancient city, thư viện stronghold, trail ruins.

---

## 4. Thay asset placeholder bằng asset thật

Texture/model được **vẽ bằng code** (`tools/generate_assets.py` + `pixelart.py`, `sprites.py`, `armor.py`, `models.py`) theo phong cách steampunk kiểu Create: đồng thau có viền nâu đậm, đồng đỏ, da thuộc, thép đen và lõi cyan; đúng UV và tên bone. Họa sĩ có thể vẽ lại trên nền này.

1. **Model/animation GeckoLib** (`geo/…`, `animations/…`): mở trong Blockbench (plugin GeckoLib). **Giữ nguyên tên bone**:
   - Brass Sentry: `root, base, leg_mount_1..3, leg_1..3, head (bắt buộc — đầu quay theo mục tiêu), barrel, muzzle, coil, gear_l, gear_r, vent`; animation `spawn, idle, overclock, shoot, despawn`.
   - Siege Sentry: `root, base, leg_mount_1..4, leg_1..4, head, armor_l/r, barrel_l/r, muzzle_l/r, coil, gear_back, drum, exhaust`; animation `spawn, idle, overclock, shoot_left, shoot_right, despawn`.
   - Clockwork Automaton: `root, body, boiler, chimney, gear_back, head, arm_r, arm_l, leg_r, leg_l`; animation `assemble, idle, walk, attack, volley`. Bản Mk.II dùng `clockwork_automaton_mk2.png`.
   - Gear: bone `gear`, animation `spin`.
   - Giáp (texture 96×96, UV từng mặt như giáp ISS): `bipedHead/armorHead` (+ `hat_gear`), `armorBody`, `armorLeggingTorsoLayer`, `armorRightArm/LeftArm`, `armorRightLeg/LeftLeg`, `armorRightBoot/LeftBoot`; animation `idle`.
   - Phần phát sáng: các file `*_glowmask.png` (GeckoLib `AutoGlowingGeoLayer`).
2. **Animation người chơi** (`player_animation/technomancy_animations.json`): `gear_flick`, `welder_channel`, `deploy_sentry`, `deploy_sentry_finish`, `steam_push` — có thể sửa bằng Blockbench (mẫu "player" của PlayerAnimator) hoặc chỉnh keyframe trực tiếp.
3. **Âm thanh**: `sounds.json` hiện trỏ tới sound event vanilla (`"type": "event"`). Để dùng file riêng, đặt `.ogg` (mono, 44.1 kHz) vào `assets/iss_technomancy/sounds/…` rồi đổi từng mục, ví dụ:
   ```json
   "entity.brass_sentry.shoot": { "sounds": ["iss_technomancy:sentry/shoot_1", "iss_technomancy:sentry/shoot_2"], "subtitle": "subtitles.iss_technomancy.entity.brass_sentry.shoot" }
   ```
4. Sau khi thay asset thủ công, **đừng chạy lại** `generate_assets.py` (nó sẽ ghi đè) — hoặc xoá phần tương ứng trong script.

---

## 5. Ghi chú kỹ thuật (QA)

- Các API đã đối chiếu với mã nguồn tag `v1.20.1-3.16.3`: `AbstractSpell`, `DefaultConfig`, `SchoolType` (constructor không deprecated), `SchoolRegistry.SCHOOL_REGISTRY_KEY`, `SpellRegistry.SPELL_REGISTRY_KEY`, `AnimationHolder(ResourceLocation, boolean[, boolean])`, `AbstractMagicProjectile`, `DamageSources.applyDamage`, `SpellDamageSource#setIFrames`, `EntityCastData`, `MagicManager.spawnParticles`, `Utils.raycastForEntity / moveToRelativeGroundLevel`, `ImbuableChestplateArmorItem`, `GenericCustomArmorRenderer`, `IronsExtendedArmorMaterial`, `StaffItem(Properties, StaffTier)`, `UpgradeOrbItem(Properties, ResourceKey)`, `UpgradeOrbTypeRegistry.UPGRADE_ORB_REGISTRY_KEY`, loot function `randomize_spell` / `randomize_ring_enhancement` với `spell_filter.school`, GLM `irons_spellbooks:append_loot`.
- Brass Sentry **không** dùng `SummonManager` của ISS (hệ đó gắn hạn sử dụng cố định với recast), mà tự quản lý chủ (`OwnableEntity`) + thời gian sống để Arc Welder kéo dài được. Nó vẫn được ISS coi là đồng minh qua `OwnableEntity`, và Counterspell (`AntiMagicSusceptible`) sẽ thu hồi tháp.
- Tia hàn được vẽ bằng `RenderType.lightning()` (cộng màu), không cần texture; server và client dùng cùng hàm `ArcWelderBeam.trace` nên điểm chạm khớp nhau.
- Phép Continuous của ISS gọi `onCast` ở tick đầu và mỗi 10 tick; mana trừ mỗi nhịp, hết mana hoặc hết 80 tick thì kết thúc và `EntityCastData` tự xoá thực thể tia.

---

## 6. Bản cập nhật 1.1 — Robot, Trượng mô-đun, Rồng Công Nghệ

Model/texture mới được sinh bằng `tools/models_v2.py` (model GeckoLib) và `tools/sprites_v2.py` (icon, GUI, block); data mới ở `tools/data_v2.py`. Chạy lại `python tools/generate_assets.py` và `python tools/generate_data.py` sau khi sửa. `tools/preview_geo.py` render file `.geo.json` (có thể kèm tư thế của một animation) ra PNG để xem nhanh mà không cần vào game.

### Clockwork Automaton (robot)
- Model mới: robot đồng thau có cửa sổ ngực đầy bánh răng xoay liên tục (controller `gears` riêng), đầu có mắt phát sáng + ăng-ten nhấp nháy, vai có bánh răng, tay kẹp piston, ống khói đôi và bệ phóng bánh răng trên vai.
- Animation kiểu servo: dùng easing `step` của GeckoLib + giữ tư thế rồi giật nhanh (`idle`, `walk`, `attack`, `volley`, `assemble`). Thân xoay theo nấc 15° (renderer) nên quay người như máy.
- Hơi nước: ống khói phun khi đứng/đi (dày hơn khi đi/đánh nhau), chân xả hơi mỗi bước, khuỷu tay xả khi đấm, xả khi phóng bánh răng và khi trúng đòn.
- **Mk.II (Overdrive)** đổi hẳn model: golem hơi nước thân tròn (kiểu Blitzcrank) — nắm đấm khổng lồ, turbine phát sáng trên đỉnh, huy hiệu tia sét ở ngực, chân khẳng khiu có gai. Chiêu riêng:
  - **Rocket Grab** (8s, tầm 4–15): phóng nắm đấm kéo mục tiêu về, làm chậm mạnh.
  - **Power Fist**: đòn đánh thường hất tung mục tiêu.
  - **Static Field** (mỗi 3s): giật sét tối đa 3 kẻ địch trong 4.5 khối.

### Siege Sentry (tháp Overdrive)
To hơn ×1.35 (hitbox 1.9 × 2.15), bắn mỗi 9 tick (overclock 6 tick), tầm 24, nổ bán kính 2.25.

### Trượng Động Cơ Đồng Hồ (`clockwork_scepter`, giữ ID cũ)
- Model 3D GeckoLib: thân gỗ tím xoắn có đai đồng, vòng bánh răng xoay quanh lõi cyan, kim đồng hồ hình tia sét màu cam nhảy từng nấc, 2 quả cầu tím bay quanh. Trong GUI hiện icon 2D (model `forge:separate_transforms`).
- Chỉ số: 5 sát thương, +20% sức mạnh Cơ Khí, +10% giảm hồi chiêu, +5% sức mạnh phép.
- **3 ô mô-đun** — Shift + chuột phải để mở. Mô-đun chỉ tác dụng lên phép Cơ Khí niệm khi đang cầm trượng (tay chính hoặc tay phụ). Cấp các mô-đun cùng loại cộng dồn, tối đa 5:

| Mô-đun | Mỗi cấp |
|---|---|
| Đa Nòng (Splitter) | +1 bánh răng (Gear Barrage), +1 tia nảy (Arc Welder), +6° nón (Steam Vent), +1 bolt/đạn mỗi loạt (tháp pháo), +1 bánh răng mỗi loạt (automaton) |
| Cỡ Nòng (Caliber) | +10% sát thương, đạn to hơn 20%, tầm Steam Vent dài hơn |
| Lắp Ráp (Assembler) | Tháp pháo: +1 tháp mỗi cấp (tối đa 4); Automaton: +1 con mỗi 2 cấp (tối đa 3); +10% máu công trình |
| Tụ Điện (Capacitor) | +4% giảm hồi chiêu, +5% tốc độ niệm, +3% sức mạnh Cơ Khí (thuộc tính của trượng) |
| Cuộn Tesla (Tesla) | Đòn Cơ Khí phóng sét nảy sang thêm 1 kẻ địch (26–50% sát thương đòn gốc) |

Chế: cấp I = sắt + đồng + Bánh Răng Bí Thuật + đá đỏ + vật phẩm đặc trưng (máy phân phát / khối sắt / piston / khối đá đỏ / cột thu lôi); cấp II = cấp I + Rune Cơ Khí + kim cương + vàng; cấp III = cấp II + **Lõi Rồng Công Nghệ** + Energized Core + Arcane Ingot.

### Boss: Rồng Công Nghệ Lôi Đình (`tech_dragon`)
- 650 máu, giáp 12, thanh máu boss tím (đỏ ở phase 2), dài ~12 khối, sải cánh ~12 khối. Bất tử khi xuất hiện / chuyển phase / chết; mỗi đòn tối đa 60 sát thương; miễn sét, lửa, rơi.
- Đòn: **Phun bánh răng** (3 loạt bánh răng khổng lồ), **Hơi thở sét** (tụ điện rồi quét tia sét liên tục), **Gọi sấm** (12–18 sét ISS có cảnh báo), **Bổ nhào** (lao xuống tạo sóng chấn động, rung màn hình, rồi đánh dưới đất bằng **Quét đuôi** 360° và **Cào**), **Gọi drone** (2–3 Clockwork Automaton).
- **Phase 2** (≤50% máu): biến hình quá tải (pha lê chuyển cam), nổ EMP, đánh nhanh hơn, thêm **EM Pulse** và **Arc Barrage**. Nếu có **T.O Magic 'n Extras** thì rồng dùng luôn phép `traveloptics:em_pulse` và `traveloptics:rapid_laser`; không có thì dùng bản dựng sẵn (EMP + Chain Lightning của ISS).
- Rơi: 2–4 Lõi Rồng Công Nghệ, rune, bánh răng, Energized Core, 1 mô-đun cấp II (35% thêm 1 mô-đun cấp III), 2 scroll Cơ Khí chất lượng cao + 1 scroll Lightning, 500 XP.

### Triệu hồi
- **Tế Đàn Đồng Hồ** (`clockwork_altar`): chế từ Bánh Răng Bí Thuật, Rune Cơ Khí, Arcane Ingot, cột thu lôi, đá đen mài; hoặc tìm trong **Đền Đồng Hồ** (structure tự sinh ở đồng bằng, sa mạc, đồi gió, savanna, badlands…; khoảng cách 42 chunk). Đền có rương loot (35% có sẵn Lõi Dynamo, mô-đun cấp I/II, scroll).
- **Lõi Dynamo Quá Tải**: lightning bottle ×4, netherite ingot, Rune Cơ Khí ×2, Energized Core, Arcane Ingot. Dùng lên tế đàn → rồng thức dậy (mỗi lúc 1 con trong 96 khối).

### Mật Điển Đồng Hồ (`clockwork_codex`)
Sách phép 12 ô: +15% sức mạnh Cơ Khí, +5% sức mạnh phép, +200 mana. Chế: Netherite Spell Book + Lõi Rồng + Rune Cơ Khí ×4 + Bánh Răng ×2 + Energized Core.

---

## 7. Bản cập nhật 1.2 — Rồng làm lại, 4 spell mới, Pháp Sư Cơ Khí

### Rồng Công Nghệ làm lại từ đầu (`tools/dragon_v2.py`, học theo Saint's Dragons / Raevyx)
- Model mới, texture 1024×1024 (2 texel mỗi pixel model): giáp đồng-vàng viền vàng có rãnh phát sáng xanh, da chàm vảy, mào và gai pha lê phát sáng, cổ 3 khúc, đuôi 6 khúc có lưỡi pha lê, chân móng vuốt.
- **Cánh thật**: xương cánh tay → cẳng → bàn tay → 3 ngón dài; màng cánh là mặt phẳng cắt hình bằng alpha (mép vỏ sò, viền sáng, gân phát quang), vẽ một mặt, renderer không cull.
- **Animation bằng Molang** (`math.sin(query.anim_time*…)`): vỗ cánh có độ trễ vai → cẳng → bàn tay, đuôi uốn sóng, thân nhấp nhô; các đòn đánh dùng keyframe.
- **Tạo dáng trong code** (`TechDragonModel`): nghiêng thân khi rẽ (bank), ngóc/chúi theo hướng bay, đuôi bị kéo lệch khi quay, cổ và đầu nhìn theo mục tiêu trong khi thân bay theo hướng di chuyển.
- **Cơ chế mới**: Thunder Roar (vòng sét + sóng xung kích), Ground Rend (lướt trên mặt đất xé đất để lại vệt sét), Talon Snatch (lấy từ Ice and Fire: quắp người chơi bay lên rồi thả, không tự thoát ra được), Dive Bomb mạnh và rộng hơn theo tốc độ/độ cao bổ nhào, bão sét liên tục ở phase 2, bị choáng khi trúng EMP Screech (rơi xuống, nhận thêm 30% sát thương, sau đó kháng choáng 15 giây).
- **Rơi thêm**: scroll **Triệu Hồi Rồng Con Công Nghệ** (chắc chắn rơi; spell này không xuất hiện trong loot ngẫu nhiên).

### Spell mới
| Spell | Loại · Độ hiếm · Max | Hiệu ứng | Overdrive |
|---|---|---|---|
| **Kéo Tay Tên Lửa** (Rocket Grab) | Instant · Uncommon · 5 | phóng nắm đấm có dây cáp (16 + 2/lv khối), móc mục tiêu đầu tiên rồi kéo về trước mặt, Đoản Mạch 1s + 0.25s/lv; boss và quái to chỉ bị đánh và giật | nắm đấm to hơn, tầm ×1.5, choáng lâu hơn |
| **Từ Trường** (Magnetic Field) | Long 1s · Epic · 5 | vùng bán kính 7 + 0.6/lv (7–9.4) trong 7–11 giây: mọi thứ trừ người niệm bị chậm và ghì xuống đất, kẻ bay bị kéo xuống, elytra tắt, đạn bị bẻ cong; kẻ địch nhận spell power × 0.25 mỗi giây | +3 bán kính, chậm mạnh hơn, sát thương ×1.6 |
| **Sóng Nhiễu Điện** (EMP Screech) | Instant · Rare · 5 | sóng âm 18 khối: ngắt phép đang niệm, xoá công trình phép của địch (như Counterspell); máy móc/sinh vật điện (tag `iss_technomancy:mechanical`: automaton, tháp pháo, golem sắt, Harbinger và Watcher/Prowler, Magnetron/Notor/Teletor/Ferrouslime, Rồng Công Nghệ…) bị choáng 2s + 0.5s/lv và nhận power × 0.8 | nổ 360° bán kính 10 |
| **Triệu Hồi Rồng Con** (Call the Tech Drake) | Long 1.5s · Legendary · 3 | rồng con 60 + 30/lv máu, 60s + 30s/lv, phun bánh răng, hơi thở sét, gọi sấm vào kẻ chủ nhân đang đánh | rồng quá tải to hơn, pha lê cam, sát thương ×1.4, có Thunder Roar |

Hiệu ứng mới **Đoản Mạch** (Short Circuit): đứng yên tại chỗ, không gây sát thương cận chiến.

### Blitz Mk.II
- Rocket Grab giờ phóng bàn tay tên lửa thật có dây cáp, kéo quái về để đấm.
- **Quá tải trước khi chết**: thay vì chết, nó ngừng hoạt động, nháy điện 2 giây rồi phát nổ điện bán kính 5 (gây sát thương ×3 so với bánh răng, choáng, hất văng). Hết thời gian tồn tại cũng tự nổ như vậy.
- Power Fist hất tung lên trời và choáng ngắn. Overdrive kiểu Blitz: thỉnh thoảng tăng tốc 3 giây khi mục tiêu ở xa, sau đó chậm lại để xả hơi.

### Pháp Sư Cơ Khí (`technomancer`)
- Mob trung lập như các pháp sư buôn bán của ISS: đeo kính bảo hộ, áo đỏ viền vàng, tay máy, cầm Trượng Động Cơ; dùng model người niệm phép của ISS nên có đủ animation niệm phép.
- Đi lang thang (hiếm) ở đồng bằng, đồng cỏ, savanna, đồi gió, rừng, sa mạc; luôn có một người đứng ở Đền Đồng Hồ.
- Giao dịch: scroll Cơ Khí (3 bậc chất lượng), Bánh Răng, Rune, mô-đun cấp I (40% thêm cấp II), 30% bán Lõi Dynamo Quá Tải, bản đồ tới Đền Đồng Hồ.
- Khi bị đánh sẽ dùng Loạt Bánh Răng, Kéo Tay, Phun Hơi, Sóng Nhiễu Điện, dựng Tháp Pháo và lắp một Automaton.

### Kiểm tra trước khi xuất jar
- `./gradlew validateAnimations`: đọc mọi file animation/geo bằng chính GeckoLib và tính thử mọi keyframe (bắt được lỗi `step` gây crash ở bản trước). Kết quả: 9 model, 55 animation, 4212 keyframe, 0 lỗi.
- `./gradlew runGameTestServer`: 5 GameTest trên server không giao diện, tất cả đều qua. Nội dung: cho mob niệm cả 10 spell (kể cả bản Overdrive); Mk.II quá tải rồi nổ; rồng chạy hết phần mở màn và các đòn đánh, bị choáng, nhận sát thương; mọi thực thể mới đều tick được; nạp được template Đền Đồng Hồ (có tế đàn và Pháp Sư).
- Code test nằm trong `devtest/`, không đóng gói vào jar.

---

## 8. Bản cập nhật 1.3 — Rồng làm lại lần 2, Blitz, Pháp Sư kiểu Viktor, Tháp Đồng Hồ

Generator mới: `tools/dragon_v3.py` (rồng), `tools/blitz_v3.py` (Blitz), `tools/technomancer_v2.py` (Pháp Sư),
`tools/data_v3.py` (Tháp Đồng Hồ + loot), `tools/v4_assets.py` (texture vòm Từ Trường), `tools/surf.py` (vẽ texture
theo toạ độ model để các khối nối liền nhau), `tools/check_geo.py` (kiểm tra / tự sửa mặt trùng nhau gây nhấp nháy).

### Rồng Công Nghệ
- Model mới theo concept (`idea/tech_dragon.png` + bản vẽ Volta): da chàm, giáp đồng hồng viền vàng, ngọc vuông xanh
  trên giáp lưng, vương miện pha lê, cánh dơi có "mắt" đồng tròn ở cổ tay và mép cánh, đuôi 7 khúc kết thúc bằng đĩa
  đồng + lưỡi pha lê. Màng cánh là tấm mỏng vẽ **cả hai mặt** (bản 1.2 chỉ vẽ mặt trên nên nhìn từ dưới cánh biến mất).
- **Boss to ×2** (~24 khối, sải cánh ~27 khối, hitbox 6.8×5.8); rồng con ×1.5 (~7.5 khối), rồng con quá tải ~10 khối.
- **Sửa lỗi xoay như chong chóng**: ở client `yBodyRot` không bao giờ được cập nhật (BodyRotationControl bị ghi đè
  rỗng) nên thân đứng yên còn góc đầu so với thân bị kẹp/lật liên tục. Giờ thân luôn theo `yRot` ở cả hai phía và góc
  đầu được tính lại có wrap. Bay dùng hệ lái mới: rồng luôn bay theo hướng mũi, quay đầu có giới hạn tốc độ, bay vòng
  quanh mục tiêu bằng điểm nhắm phía trước nên không còn giật quay ngược.
- **Đậu / nghỉ**: không có mục tiêu thì boss bay tuần quanh hang, tìm chỗ đất trống đáp xuống, đứng nghỉ với các
  animation idle / nhìn quanh / ngồi / rỉa cánh, lâu thì nằm ngủ (hồi máu). Người chơi lại gần (≤10 khối khi ngủ, hoặc
  đánh nó) → thức dậy, gầm, cất cánh. Rồng con không có mục tiêu thì đáp xuống cạnh chủ, đi bộ theo chủ, cất cánh khi
  chủ bay/đi xa/bị tấn công.
- Animation mới: fly_fast, takeoff, land, idle_look, sit, groom, sleep, wake, run, bite, roar_ground (tổng 31).

### Blitz (Automaton Mk.II)
- Model mới theo concept Blitzcrank: thân cầu đồng thau tán đinh liền mạch, turbine xanh trên đỉnh, đầu hộp nhỏ hai mắt
  tròn phát sáng, huy hiệu tia sét tròn, ống cao su, cẳng tay khổng lồ, chân piston có gai. Cao ~3.4 khối (hitbox 1.66×3.6).
- Đánh thường: đấm thẳng luân phiên trái/phải; **1/3 cú đấm là Uppercut** (thu người, kéo nắm đấm ra sau hông, vung
  bật lên qua đầu; sát thương ×1.5, hất tung, choáng). Sát thương rơi đúng khung hình chạm của animation.
- **Chạy nước rút**: khi mục tiêu ở xa, chạy nhanh 2.5s (hai tay vung lấy đà liên tục kiểu robot), rồi chậm lại 1s xả hơi.
- **Nổ khi chết**: sóng điện (shockwave của ISS) bán kính 4 khối.
- Cú kéo Rocket Grab: dây cáp giờ là ống vuông 4 mặt và được cull theo cả đoạn dây (trước đây dây biến mất khi nắm đấm
  ra khỏi màn hình); nắm đấm trên tay Blitz ẩn đi khi đang bay.
- Đã gỡ toàn bộ mặt trùng nhau (z-fighting) trên mọi model bằng `check_geo.fix_geo`.

### Pháp Sư Cơ Khí (kiểu Viktor "Prototype")
Model riêng giữ nguyên toàn bộ bone của ISS (animation niệm phép, cầm đồ, giáp vẫn chạy) và thêm nhiều lớp: tóc bạc
dựng ngược, kính bảo hộ mắt xanh, cổ áo vàng, giáp vai 2 tầng (có ngọc), áo đỏ viền vàng có huy hiệu xoắn xanh, vạt áo,
thắt lưng, tay trái cơ khí bằng đồng, găng đen, nẹp gối, ủng; giá đỡ sau lưng với cánh tay cơ khí thứ ba có móng kẹp và
vòng hào quang xanh xoay; khăn đỏ 3 khúc bay theo chuyển động. Texture 512×512 (4 texel/pixel) + glowmask.

### Clockwork Tower
Công trình mới (`clockwork_tower`, 15×46×15) phong cách Piltover: tường kem/thạch anh, viền đồng, cửa sổ kính lam, mái
đồng xanh ngọc hình chóp, mặt đồng hồ 4 phía, ban công tầng trên. Tầng trệt là xưởng (đe, lò luyện, piston, xích, đèn)
có **một Blitz gác xưởng** (trung lập, chỉ đánh kẻ tấn công nó hoặc Pháp Sư; 150 máu; chết rơi loot `blitz_guard`).
Tầng trên cùng có **Pháp Sư Cơ Khí** và rương loot tốt. Thang leo xuyên các tầng. Sinh ở đồng bằng, đồng cỏ, savanna,
rừng, sa mạc, badlands (khoảng cách 48 chunk). Khối vanilla — sau này có thể thay bằng khối Create.

### Phép
- **Từ Trường**: bỏ toàn bộ sát thương; chỉ tác dụng trong **vòm bán cầu** phía trên điểm niệm (có vòm phát sáng hiển thị).
- **Sóng Nhiễu Điện**: bỏ sát thương, chỉ làm choáng máy móc/sinh vật điện 3s (không ngắt phép, không xoá công trình,
  không ảnh hưởng thứ khác); chỉ còn **1 cấp, độ hiếm Rare**. Pháp Sư dùng Từ Trường thay cho phép này khi phòng thủ.
- **Siege Sentry** (ụ súng Overdrive): cao ~3.2 khối (hitbox 2.6×3.2), nòng bắn từ đúng đầu nòng.

> ISS 3.16 chỉ dùng file cấu hình phép khi bạn đã tự tạo (`config/irons_spellbooks_spell_config/iss_technomancy/emp_screech.json`
> hoặc datapack). Nếu có file đó từ bản cũ, xoá nó (hoặc đặt max level = 1, rarity = rare) để nhận giá trị mới.
> Scroll/sách cũ đang chứa EMP Screech cấp 2–5 sẽ được ISS tính như cấp tối đa 1.

---

## 9. Bản cập nhật 1.4 — sửa tận gốc lỗi xoay, cân bằng, Pháp Sư kiểu skin 3D

- **Nguyên nhân thật của lỗi rồng xoay như chong chóng / đứng chổng lên trời / tay sau lưng Pháp Sư quay loạn:** code
  tạo dáng thủ tục cộng thêm góc vào bone (`bone.setRotX(bone.getRotX() + x)`). Trong GeckoLib 4.8, `GeoBone.setRotX`
  đánh dấu bone "đã thay đổi", nên khung hình sau GeckoLib **không** đưa bone (mà animation hiện tại không điều khiển)
  về tư thế gốc → góc cộng dồn mỗi khung hình. Không liên quan model hay mod Saint's Dragons / Ice and Fire.
- Sửa: `client/model/ProceduralPose` (ghi nhớ giá trị đã ghi và offset đã cộng, gỡ offset cũ trước khi cộng offset
  mới; bone không ai điều khiển thì đặt từ tư thế gốc). Mọi animation của rồng đều có kênh xoay cho các bone được tạo
  dáng thủ tục. Kiểm tra: `./gradlew checkProceduralPose` mô phỏng đúng thứ tự xử lý của GeckoLib trên GeoBone thật
  (code cũ trôi tới 200 rad sau 2000 khung hình, code mới đúng tuyệt đối).
- **Cân bằng −25%** sát thương: Gear Barrage, Arc Welder, Brass/Siege Sentry, Steam Vent, Automaton/Blitz (đấm,
  uppercut, Static Field, nổ quá tải, kéo của Blitz đều tính từ sát thương này), rồng con; Blitz gác tháp 12→9 đấm.
- **Kéo Tay Tên Lửa (phép của người chơi):** không còn sát thương, chỉ kéo + choáng. Cú kéo của Blitz vẫn gây sát thương.
- **Pháp Sư Cơ Khí làm lại** (`tools/technomancer_v3.py`): kiểu skin Minecraft 1 texel/pixel, tóc nâu đen, lớp ngoài dựng
  thành voxel như mod 3D Skin Layers (tóc, kính mắt xanh, cổ áo vàng, viền áo, thắt lưng, huy hiệu ngực, vạt áo, nẹp chân),
  giáp vai vàng có đèn xanh, áo choàng 2 vạt, giá lưng + cánh tay cơ khí có đèn xanh và 2 móng. Cánh tay và áo choàng chỉ
  lắc nhẹ quanh tư thế gốc, nâng lên/mở móng khi niệm phép.

---

## 10. Bản cập nhật 1.5 — Rồng: nghỉ kiểu Ice and Fire, hitbox nhiều phần, nhiều đòn mới

Chi tiết kỹ năng: xem `README_TECH_DRAGON.md`.
- Tư thế cánh khi đứng mới (hé, quét ra sau, rủ dọc hông) thay cho kiểu gập dựng tấm màng thẳng đứng như bản cũ.
- Nằm nghỉ kiểu Ice and Fire (cánh trải trên đất, đuôi cuộn), nằm ngóc đầu nhìn quanh, đứng dậy; 44 animation.
- Hitbox nhiều phần (`TechDragonPart`, Forge PartEntity): đầu ×1.3 sát thương, cánh ×0.7.
- Đòn mới: Cào trái/phải, 3 kiểu Cắn, Quất Đuôi, Dậm Đất, Quạt Cánh (hất văng mọi thứ, đánh bật đạn), Gầm Từ Trường
  (tạo vòm Từ Trường), Lướt Cào trên không.
- Thù dai: đuổi kẻ tấn công tới 160 khối, ra ngoài hang (Wither không thoát được nữa). Mục tiêu bay phía trên → cất cánh ngay.
- Pháp Sư Cơ Khí mạnh hơn: 110 máu, giáp 8, niệm nhanh hơn, cấp phép cao hơn, thêm Arc Welder.
- Crash `The_Harbinger_Model ... root()` là do Cataclysm 3.16 + LionfishAPI 3.0 lệch bản: dùng Cataclysm 3.31.

## 11. Bản cập nhật 1.6 — Rồng Công Nghệ làm lại hoàn toàn (v4)

Chi tiết kỹ năng, chỉ số, điều khiển: xem `README_TECH_DRAGON.md`.
- Model mới 4 chân + 2 cánh kiểu Saint's Dragons (chỉ tham khảo tỉ lệ; art của Saint's Dragons là All Rights Reserved,
  không copy). Boss dài ~26 khối, 1000 máu; rồng triệu hồi ~11 khối, cưỡi được.
- Công cụ mới trong `tools/`:
  - `dragon_v4.py`: khung xương + khối + vẽ texture theo toạ độ thật (vảy, giáp hextech, pha lê, màng cánh).
  - `anim_v4.py`: bộ bake animation: tư thế khoá + easing nội suy quaternion, độ trễ cổ/đuôi (follow-through), lớp
    chồng (thở, vỗ cánh, rung), **IK bốn chân** (chân bám đất không trượt), **màng cánh hình quạt** tự khép/mở theo
    ngón (`memb_*a/b/c/d`).
  - `dragon_v4_anims.py`, `dragon_v4_anims2.py`: 45 animation; `export_parts` bake vị trí đầu/cổ/ngực/đuôi/cánh/miệng/
    yên/lõi/chân trước/đầu đuôi mỗi tick → `data/iss_technomancy/tech_dragon/parts.json` (server dùng cho hitbox,
    đòn đánh, hơi thở, con mồi bị ngậm, người cưỡi). `tools/tech_dragon_events.json`: mốc ra đòn của từng animation.
  - `pylon_v4.py`: Tháp Hextech, Vỏ Cầu Hextech, texture khiên.
  - `rig_v4.py` (FK chuẩn GeckoLib), `render_v4.py` (render preview có z-buffer, bóng, GIF).
  - Đã xoá `dragon_v2.py`, `dragon_v3.py`, `dragon_anims_v4.py`.
- Java: `TechDragon` viết lại (máy trạng thái mới), `TechDrake` (cưỡi được: phím trong `client/RiderControls`,
  packet `network/TechNetwork`), `HextechPylon`, `HextechShell`, `DragonTracks`, renderer khiên + tia điện tháp.
- Xương điều khiển thủ tục (`flight`, `neck1c..headc`, `tail1c..tail8c`) luôn được gán góc TUYỆT ĐỐI, animation không
  bao giờ chạm vào chúng → không thể tái phát lỗi xoay chong chóng.
- Tháp/rồng miễn sát thương ngạt trong khối; tháp và sét đặt theo tia dò nền gần độ cao của rồng (không theo
  heightmap, tránh dựng trên ngọn cây/trần hang).
- 20/20 GameTest (thêm: mọi đòn mới, ngậm cắn, vỡ khiên khi phá hết tháp, hồi máu khi bỏ mặc tháp, vỏ cầu nổ + rơi đồ,
  cưỡi rồng triệu hồi).

## 12. Bản cập nhật 1.7 — Rồng v5: model dựng lại, lối đánh mới, hitbox khít, cưỡi mượt

Chi tiết: `README_TECH_DRAGON.md`.
- **Model dựng lại từ đầu** (`tools/dragon_v5.py`, cùng khung xương v4 nên IK/màng cánh/animation dùng lại được):
  cổ/thân/đuôi là ít khối lớn chồng nhau, vây lưng / mào / diềm má / răng là mặt phẳng texture trong suốt, giáp mỏng,
  mắt to lộ rõ (bỏ bánh răng vai). Hàng vây chừa khoảng trống ở ghế ngồi.
- **Phase 2 không nhuộm đỏ nữa:** generator vẽ thêm kênh "glow2" → `tech_dragon_overcharged.png` + glowmask có vân hextech
  sáng trên vảy và vây sáng; các xương `oc_*` (vây pha lê to, vảy lục giác) được `TechDragonModel` cho mọc từ 0 → 1 trong
  lúc gầm quá tải.
- **Animation mới** (`tools/dragon_v5_anims.py`): pounce, dash_claw_left/right, dodge_left/right, ram, storm, dive_bounce.
- **Hitbox 17 phần** theo vùng thân: `export_boxes` bake khung (tâm + nửa kích thước) của từng vùng mỗi tick vào
  `parts.json` ("regions", "boxes"); `TechDragon.tickParts` đặt/co giãn từng `TechDragonPart` theo đó (xoay theo yaw và
  góc bay). Phần thân là khối rắn (`canBeCollidedWith`), rồng không va vào chính nó (`canCollideWith`), ai bị đè thì bị
  đẩy ra (`pushOutOverlapping`). Click vào phần nào cũng là click vào rồng (cưỡi được).
- **AI mới:** đuổi nhanh, vồ, lướt cào, húc (đâm tường thì choáng), né + phản đòn, combo; bay ngắn: chuỗi bổ nhào, gọi bão,
  Skyfall; đuổi mục tiêu bay bằng cách bay thẳng theo, mục tiêu xuống đất thì đáp trước mặt nó.
- **Mặt đất bằng tia dò** (`floorBelow`) thay heightmap ở mọi chỗ định vị bay/đáp/bổ nhào: heightmap lấy cả mái nhà,
  ngọn cây, trần arena nên trước đây rồng có thể bay vọt lên trên mái.
- **Cưỡi:** ghế cố định (`TechDragon.SEAT`) chỉ nghiêng theo góc bay → hết giật; `client/DrakeCamera` tự chuyển góc 3 và
  kéo camera xa thêm ~7 khối (gọi `Camera.move` SRG `m_90568_` bằng reflection, có dò tường).
- 25/25 GameTest (thêm: đẩy ra khỏi thân, vồ/lướt cào/húc áp sát, né ngang, chuỗi bổ nhào + mưa sét, ghế không nhún).

## 13. Bản cập nhật 1.8 — Mắt sửa tận gốc, rồng hung hăng, thả diều + khạc sét, tiếp đất nổ, bão sét

Chi tiết: `README_TECH_DRAGON.md`.
- **Lỗi mắt (nguyên nhân thật):** trong GeckoLib/Bedrock mặt `east` của geo nằm ở **phía x nhỏ** của khối (và chiều u như
  `west` của generator). Generator ghi ngược nên tròng mắt vẽ ở mặt `east` bị đặt vào **mặt trong**, lún trong mõm; mặt
  ngoài (`west`) không có trong danh sách mặt nên không vẽ → nhìn từ ngoài thấy da, chỉ còn viền xanh. Sửa ở
  `dragon_v5.geo_json` (đổi nhãn east/west cho khối thường; khối mirror giữ nguyên). Lỗi này lật cả vây/răng/mào theo
  chiều trước-sau ở mọi bản trước. Kiểm bằng `uv_check` (scratchpad): 1045/1045 mặt GeckoLib vẽ đúng chỗ generator vẽ.
- Lỗi phụ tìm thấy cùng lúc: cẳng chân trước phải mượn UV của **xương cánh** (hai khối cùng tên `forearm`); đổi tên
  `foreleg` và `pack()` giờ báo lỗi nếu tên khối dùng chung bị trùng.
- **Mắt mới:** khe dọc phát sáng, to hơn, hốc tối, đầu trước xoay ra 8° (`EYE_YAW`), mí dày hơn mặt mắt để chớp che kín.
- **Hai cánh:** `merge()` giờ nhân đôi khóa `_l` của tư thế đè lên sang `_r` (trừ khi `_r` được cho rõ hoặc khóa `!`).
  14 animation trước chỉ giương một cánh (stomp, pylon_charge, wing_gust, land, slam, roar, field_roar, pounce, takeoff,
  dodge, dive_bounce, phase_two, death) giờ đối xứng; 39 animation còn lại không đổi (đã so từng bone).
- **Animation mới** (`tools/dragon_v6_anims.py`): backstep, wing_push, spit, crash_land (57 tổng).
- **AI:** hung hăng (`isPrey`, `findTarget` theo ưu tiên), quất/quét đuôi chỉ khi có prey trong vùng đuôi (`preyAtTail`)
  + cooldown, thả diều (BACKSTEP / WING_PUSH / KITE_HOP → SPIT), tiếp đất nổ (`crash` / `crashBlast` / `tickRings`,
  entity `DragonDebris` chỉ để hiển thị), bão sét khắp vùng (`stormLightning`). State mới thêm ở cuối enum.
- 32/32 GameTest (thêm 7: thả diều ×2, đuôi ×2, chọn mục tiêu, tiếp đất không đổi block nào, bão trúng mọi sinh vật).
  Mỗi test rồng chạy batch riêng và dọn mob sót lại trước khi chạy (rồng hung hăng sẽ đi đánh mob của test khác).

## 14. Bản cập nhật 1.9 — Rồng phá đường, beam lõi, gặm; giáp/trượng/sách Hextech; art "Premium Fantasy"

**Rồng** (chi tiết `README_TECH_DRAGON.md`): phá block theo độ cứng (mobGriefing), choáng EMP riêng 3 s / hồi 30 s,
đè & gặm, ngậm tha lên trời rồi thả, beam lõi hextech + quá tải (texture `tech_dragon_drained`), vòng sóng điện
(`ArcRing`), nổ khi chết giết trong 20 khối (damage type `iss_technomancy:hextech_blast`, bỏ qua giáp và phù phép).
Animation mới ở `tools/dragon_v7_anims.py`. Sửa luôn tư thế `stunned` cũ (đầu cắm xuống đất ~27 px).

**Item**
- **Khuôn Rèn Nâng cấp Hextech**: Netherite Upgrade Template + Lõi Rồng Công Nghệ + 4 Arcane Cog + 3 thỏi đồng → 2 khuôn.
- **Bàn rèn** (khuôn + món + Lõi Rồng): Giáp Kỹ Sư Đồng Hồ → **Giáp Kỹ Sư Hextech** (4/10/7/4 giáp, 3.5 cứng, mỗi món +150 mana,
  +15% Technomancy, +10% Lightning, +5% sức mạnh phép, +3% giảm hồi chiêu; đủ bộ: **Tiến Hóa Vinh Quang** — máu tụt
  dưới 50% thì ngẫu nhiên 1 buff 10 s: Tốc độ II, Quá Tải, Tập Trung (hồi chiêu -40% + 25% giảm hồi chiêu), +15% sức
  mạnh phép, hồi 30% mana, Hấp thụ II, Hồi máu II; hồi 30 s, không trùng lần trước).
- Trượng Đồng Hồ (bậc 1, không có sao) → **Trượng Hextech** → ★ → ★★ → ★★★ (mỗi bậc một lần rèn).
- **Sách Phép Đồng Hồ** (7 ô, bàn chế tạo) → **Mật Điển Hextech** (12 ô, bàn rèn; giữ nguyên phép, tự nới lên 12 ô).
  Mật Điển cũ (12 ô) trong thế giới giữ nguyên.

**Art "Premium Fantasy"** (`tools/ART_STYLE_PREMIUM_FANTASY.md`, bộ công cụ `tools/premium.py`): icon 32x32 (scroll
kiểu các hệ ISS, cog, rune, quả cầu nâng cấp động, lõi rồng, dynamo, khuôn, 2 sách, 5 trượng, 8 giáp), icon 10 phép +
4 hiệu ứng; model 3D trượng bậc 1 (vòng bánh răng ngang xoay) và Hextech 4 cấp, giáp bậc 1 (kiểu Create) và Hextech,
texture sách 3D, altar triệu hồi mới.

**Sửa hạ tầng**: mặt `east`/`west` trong GeckoLib là phía x nhỏ/lớn ngược với generator cũ — `render_v4` (preview) giờ
đúng như GeckoLib; model mới (trượng, giáp) ghi đúng nhãn (`models.build(bedrock_sides=True)`); model cũ (automaton,
sentry, pháp sư...) giữ nhãn cũ để không đổi hình đang có trong game.

**Kiểm tra**: build, validateAnimations (17 model, 111 animation, 0 lỗi), 39/39 GameTest (2 lần liên tiếp, mỗi lần thế
giới test mới — xoá `run/world` trước khi chạy vì rồng phá địa hình), geckoDump khớp 0.000 px cho 5 trượng, 2 bộ giáp,
rồng (9 khung, 1045 mặt).

## 15. Bản cập nhật 1.10 — Rồng thông minh hơn, cưỡi rồng, ụ súng, Blitz, Lò Rèn Sấm, art 16x16

**Rồng boss** (chi tiết `README_TECH_DRAGON.md`, bảng "Bản 1.10"): bay khạc điện xuống, lượn bắn, khạc lâu hơn, gầm
nửa cầu, xoay 360° xả điện, rũ mob khỏi lưng, nhảy giữ tầm 4 hướng, beam 10, chỉ sét từ miệng phá block, chớp điện tức
thì thay vòng sóng, gặm tới cỡ Warden (con mồi ở trong hàm), giáp lưng hextech. Animation mới: `tools/dragon_v8_anims.py`.
Hiệu ứng điện dùng chung: `entity/boss/ElectricFx.java`.

**Rồng cưỡi**: Z cắn, X cào, C (giữ) khạc điện, V gọi trời sét quanh rồng 5 s (hồi 30 s), R gầm, G ngậm (đổi được trong
Controls). Đang bay thấp gần đất, bấm Space để hạ cánh (animation đáp). Nhìn chúc xuống mà bay tới thì rồng chúc đầu tới
~85° và tăng tốc dần (tới x2.6), kéo lên vẫn giữ đà một lúc.

**Ụ súng** (`tools/turrets_v7.py`): ụ thường = tháp pháo đồng nhỏ 3 chân có bánh răng hai bên/sau lưng và ống khói xả hơi
nước. Ụ Overdrive = **Đại Pháo Hextech**: một nòng dài to có vòng hextech phát sáng, bệ bát giác, màu navy-vàng-xanh; đạn
x1.8 sát thương, nổ 3.5 khối, bắn chậm hơn (14 tick), tầm 28. Cả hai có animation lắp ráp khi triệu hồi (bệ trồi lên, chân
bung, thân rơi xuống khớp, nòng trượt ra, xả hơi) và tháo rời khi hết giờ.

**Blitz MkII**: tay kéo bay ra đúng từ bàn tay phải, bay thẳng và có thể hụt (vùng bắt nhỏ hơn); 1/4 cú đấm thường gọi
sét từ trời đánh xuống mục tiêu; uppercut 1/8 và chỉ hất tung thứ nhỏ hơn/bằng nó (rơi xuống ăn sát thương); nổ chết phóng
sóng điện tức thì. Model: bàn tay mở 3 ngón + ngón cái, 2 ống khói lớn, vai tròn, lưới miệng.

**Lò Rèn Sấm Hextech** (block `clockwork_altar`, giữ ID): block GeckoLib có kim đồng hồ chạy, bánh răng quay, 4 trụ pha lê,
vòng răng trên đỉnh. Cầm Lõi Dynamo Quá Tải bấm chuột phải: lõi đặt vào giá, 6 giây sấm rền, sét đánh xung quanh, quả cầu
sét phình dần quanh lõi, rồi nổ ra con rồng. Đặt block xuống thì mặt đồng hồ quay về phía người đặt.

**Item / art**: icon 16x16 đúng khổ ISS cho 10 phép, rune, orb nâng cấp (bánh răng quay quanh), khuôn rèn (mũi tên),
2 sách, scroll (`tools/icons_v7.py`); 32x32 cho Arcane Cog (mắt vàng mở ra ngọc xanh, giật điện, đóng lại — động), Lõi
Rồng (xanh hextech, ngọc giống ngực rồng, sét động), Lõi Dynamo (xanh hextech + model 3D khi cầm/đặt), 2 trượng dáng ISS,
8 icon giáp (`tools/icons_v8.py`, `tools/dynamo_v7.py`). Sách 3D có texture động (`tools/books_v7.py`). Giáp T1/T2 làm lại
theo ảnh concept (`tools/armor_v7.py`): mũ phù thủy vành rộng có bánh răng (T1 có kính, T2 có ngọc và đèn pha lê), áo choàng
dài có ve kem và tà, cầu vai, cổ tay kem, quần, ủng; T1 thêm vòng bánh răng ma thuật xoay sau lưng và charm bánh răng.

**Trượng Hextech kiểu Evolution (TravelOptics)**: một model/icon cho mọi cấp; tooltip ☆☆☆ → ★★★. Evo 1: phép trúng đích nạp
điện, lần thứ 5 gọi sét trời. Evo 2: +10% giảm hồi chiêu, +15% hồi mana, chỉ cần 4 lần nạp. Evo 3: mỗi 20 s phép Technomancy
hoặc Lightning kế tiếp +1 cấp (`item/ScepterEvolutionEvents.java`).

**EMF/ETF**: hai mod này chỉ đổi model/texture của các entity dùng hệ ModelPart của vanilla (qua resource pack); mob của mod
này đều dùng GeckoLib nên EMF/ETF không làm chúng ổn định hơn và không cần thêm vào.
