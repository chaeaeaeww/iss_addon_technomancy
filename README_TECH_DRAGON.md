# Rồng Công Nghệ Lôi Đình (Tech Dragon, the Thunderforged) — bản 1.10.0

Boss của trường phép Cơ Khí (Iron's Technomancy). Bản 1.7.0 (v5) **dựng lại model từ đầu** và **viết lại lối đánh**:
rồng 4 chân + 2 cánh, thân thon, cổ và đuôi gồm các khối lớn chồng lên nhau nên uốn liền mạch. Vây lưng, mào pha lê,
diềm má và răng là các mặt phẳng có texture trong suốt (cách Saint's Dragons dựng rồng, chỉ học cách làm, không chép
gì). Giáp đồng mỏng sát thân. **Mắt (1.8):** mắt rắn khe dọc phát sáng, to, đặt trong hốc tối, đầu trước hơi xoay ra
ngoài nên nhìn thẳng, chéo hay nghiêng đều thấy; mí nằm trên mắt khi mở và che kín khi chớp; phase 2 mắt xanh lơ rực. Màu theo concept: vảy chàm, bụng tím oải hương, đồng hồng viền vàng, pha lê
xanh, lõi hextech ở ngực.

> Không sao chép gì từ Saint's Dragons: mã nguồn của mod đó là MIT nhưng **model/texture/animation là All Rights
> Reserved**. Toàn bộ model, texture và 53 animation đều sinh bằng code (`tools/dragon_v5*.py`, `dragon_v4_anims*.py`).

## Chỉ số

| | Boss | Rồng triệu hồi (cuộn phép, chỉ boss rơi) |
|---|---|---|
| Kích thước | dài ~26 khối, sải cánh ~36 khối ("Stage 5") | dài ~11 khối ("Stage 3"); quá tải ~13 khối |
| Máu / giáp | **1000** / 16 (giáp cứng 8) | 120 / 170 / 220 theo cấp phép, giáp 10 |
| Sát thương | cắn 22, vồ 22, cào 18, húc 20, quất đuôi 16; phase 2 ×1.25 | ~40% của boss × sức mạnh phép (quá tải ×1.3) |
| Tồn tại | — | 3 / 4 / 5 phút theo cấp, mỗi người 1 con |
| Sát thương tối đa mỗi đòn nhận vào | 50 | — |
| Miễn | sét, rơi, ngạt trong khối; mọi hiệu ứng **kéo** (Rocket Grab, kéo từ trường...) | như boss |

So với Ender Dragon (200 máu): to hơn, trâu gấp 5, đánh đau hơn, có nhiều cơ chế hơn, và đánh như thú săn mồi dưới đất
chứ không lượn vòng tròn.

**Hitbox 17 phần, khít theo model và animation:** đầu (×1.3 sát thương), 2 khúc cổ, ngực, hông, 4 chân, 4 khúc đuôi,
nửa trong và nửa ngoài mỗi cánh (×0.7). Mỗi tick, từng hộp được **đặt và co giãn theo đúng khung của vùng thân đó** trong
khung hình animation đang chạy (bake sẵn từ chính model). Thân, chân, đuôi là **khối rắn**: người, quái và boss khác
(kể cả Wither) va vào như va vào thuyền, không đi xuyên được; ai bị thân rồng đè lên thì bị **đẩy ra ngoài**, không còn
bị kẹt bên trong rồng. Cánh chỉ nhận đòn, không chặn đường. Mọi đòn cận chiến trúng tại **vị trí thật** của hàm / móng /
đầu / đuôi ở khung hình ra đòn.

## Hung hăng (1.8)

Rồng boss **chủ động tấn công mọi thứ trong khu vực**: người chơi, quái thù địch (vanilla và mod khác), **boss khác**
(Wither, boss Cataclysm, rồng Ice and Fire...), mob trung lập, golem (sắt và tuyết), thú cưng / sinh vật triệu hồi của
người khác. **Không chủ động đánh**: động vật thụ động, ngựa/lừa/lạc đà không bướu (kể cả đã thuần), dân làng, thương
nhân lang thang, Pháp Sư Cơ Khí và mọi NPC buôn bán. Đòn diện rộng vẫn trúng bất kỳ ai đứng trong vùng.

Thứ tự ưu tiên: kẻ vừa đánh nó → người chơi → boss khác → mob nguy hiểm gần nhất. Đã chọn mục tiêu thì bám tới khi
mục tiêu chết / ra khỏi tầm, không đổi lung tung (chỉ đổi khi có người chơi xuất hiện). Rồng triệu hồi vẫn theo chủ.

## Hành vi khi không có địch

Đáp xuống gần hang, luân phiên đứng nhìn quanh (thở, chớp mắt), **ngồi**, **nằm** kiểu sphinx, nằm lâu thì **ngủ**
và hồi máu nhanh. Bị đánh hoặc có người tới gần thì thức dậy, đứng lên, gầm, rồi lao vào trận.

**Thù dai:** kẻ tấn công bị đuổi tới cùng (tới 160 khối). Mục tiêu bay lượn thì rồng bay **đuổi thẳng theo** nó (không
lượn vòng); mục tiêu xuống đất thì rồng đáp ngay trước mặt nó.

## Lối đánh: thú săn mồi dưới đất

Rồng chạy đuổi nhanh (~9 khối/s, phase 2 nhanh hơn), quay người gắt, áp sát liên tục:

| Kỹ năng | Mô tả |
|---|---|
| **Vồ** *(mới)* | Hạ thấp người lấy đà, bật nhảy theo đường vòng cung (tới ~22 khối), chân trước vươn ra, hàm há, đáp xuống ngay trước mục tiêu: hàm và móng cùng bổ xuống kèm sóng xung kích nhỏ. |
| **Lướt Cào trái / phải** *(mới)* | Lao vụt hai sải chân (tới ~20 khối), dừng ngay tầm vuốt rồi cào chéo. |
| **Húc** *(mới)* | Cúi đầu, sừng và mào chĩa tới, phi nước đại thẳng (tới ~18 khối/s, hơi bám theo mục tiêu). Đâm vào tường thì **choáng 1.5 s**. |
| **Né trái / phải** *(mới)* | Bị đánh cận chiến dồn dập hoặc có kẻ nép sát hông/dưới ngực: nhảy ngang tránh, xoè cánh giữ thăng bằng, đáp xuống là **phản đòn ngay** (cắn / cào / lướt cào / vồ tuỳ khoảng cách). |
| **Combo** | Sau cắn, cào, lướt cào, vồ: nếu mục tiêu còn trong tầm thì nối ngay đòn khác (35%, phase 2 55%). |
| **Cắn / Cắn Quét** | Mổ đớp; quét ngang cả vòng cung phía trước. |
| **Cào trái / phải** | Vung chân trước lên cao rồi bổ chéo xuống theo phía của mục tiêu. |
| **Ngậm Cắn** | Đớp con mồi nhỏ (≤150% cỡ người chơi): ngậm trong miệng, lắc xé 2.4 s rồi quăng đi. Không lén thoát được. |
| **Quất Đuôi trái / phải** | Chỉ khi có thứ nó sẽ tấn công đứng **đúng tầm đuôi** (sau lưng, trong vùng hitbox nửa sau của đuôi), 65% mỗi lần xét, hồi 5–7.5 s. Đứng cạnh vai hay trước mặt thì không bị quất. |
| **Quét Đuôi / Quạt Cánh** | Bị vây (≥3 kẻ): giương cánh đập hất văng mọi thứ, đánh bật đạn; chỉ quét đuôi khi có kẻ ở đuôi. |
| **Bật Lùi** *(1.8)* | Bị áp sát: vỗ cánh một nhịp lớn bật lùi ~14 khối (vẫn nhìn mục tiêu), luồng gió hất kẻ trước mặt. |
| **Vỗ Cánh Đẩy** *(1.8)* | Hai nhịp vỗ cánh về phía trước: thổi bay mọi thứ trong hình nón phía trước, đánh bật đạn. |
| **Nhảy Qua Lại** *(1.8)* | 2–3 cú nhảy chéo trái/phải lùi dần (kiểu Zinogre). |
| **Khạc Sét** *(1.8)* | Cổ co lại, lõi và mào tích điện, rồi vươn cổ khạc một tia sét gấp khúc tới chỗ mục tiêu đang chạy tới (tầm ~64 khối, nổ tại chỗ trúng). Sau mỗi đòn thả diều, nếu đã có khoảng cách thì khạc luôn. Phase 2 khạc 2 tia. Tường chặn được, không phá block. |
| **Dậm Đất** | Chồm lên rồi dậm xuống: sóng xung kích điện, hất tung, làm chậm (kẻ đứng sát dưới ngực). |
| **Gầm Từ Trường** | Vòm từ trường làm chậm, ghì xuống, kéo kẻ bay rơi. |
| **Hơi Thở Sét** | Tia sét liên tục quét theo mục tiêu. |
| **Xé Đất** (phase 2) | Phi nước đại hàm mở, để lại vệt sét. |

## Kỹ năng bay (chỉ bay ngắn, khoảng 20–30 giây một lần)

| Kỹ năng | Mô tả |
|---|---|
| **Chuỗi Bổ Nhào** *(mới)* | Cất cánh, vút lên trên mục tiêu rồi lao thẳng xuống đập đất, **bật lên lại và bổ tiếp**: 3 lần (phase 2: 4 lần), lần cuối đập mạnh rồi đánh tiếp dưới đất. |
| **Gọi Bão** | Bay lên cao ~25 khối trên mục tiêu, treo mình giữa mây đen, ngửa cổ gầm: **8 giây sét đánh tùm lum** khắp vùng bán kính ~24 khối (phase 2: ~30, dày hơn), và cứ ~1.2 s **mỗi sinh vật nó sẽ tấn công trong vùng** lãnh một tia (mục tiêu chính bị đón đầu); rồi lao xuống đáp nổ trước mặt mục tiêu. |
| **Skyfall** (phase 2) | Vút lên rất cao rồi lao thẳng xuống: vụ nổ lớn + vòng sét, rồi gầm làm chậm và yếu mọi kẻ xung quanh. |

Khi đuổi mục tiêu đang bay: Phun Bánh Răng, Hơi Thở Sét, Lướt Cào trên không, Gầm Sấm, Gọi Sấm, EMP / Arc Barrage
(phase 2), gọi drone.

**Tiếp đất (1.8):** mọi lần đáp từ trên không trong trận (sau khi đuổi trên không, sau Gọi Bão, kết Chuỗi Bổ Nhào,
Skyfall, đáp xuống giữa sân khi gọi Tháp) đều là **lao xuống đập đất nổ điện**: sát thương quanh điểm đập, **5–6 vòng
sóng điện lan ra liên tiếp** (ai đứng trên đất khi vòng đi qua bị hất nhẹ và làm chậm), tia điện chạy trên mặt đất, sét
giáng quanh, **đất đá văng lên** (khối giả chỉ để nhìn, rơi xuống thì vỡ thành bụi), rung màn hình mạnh, tiếng nổ +
sấm. **Không phá địa hình.** Rồi gầm (Skyfall: gầm làm chậm và yếu).

## Bản 1.9

| Kỹ năng / cơ chế | Mô tả |
|---|---|
| **Phá đường** | Như rồng Ice and Fire: đầu, cổ, thân, chân húc vỡ block cứng tới mức đá/gạch/gỗ (≤ 2.0) trên đường tới mục tiêu (không đào nền dưới chân). Sét phá block yếu (đất, cát, sỏi, kính, lá; ≤ 0.6). Beam lõi khoan tới đá/gạch đá/deepslate (≤ 3.0). Theo gamerule `mobGriefing`, không rơi đồ, không phá block có dữ liệu (rương, lò, spawner...), obsidian, bedrock. |
| **Choáng EMP** | Sóng Nhiễu Điện làm nó co giật ngã gục 3 giây (animation riêng, vân sáng tắt xám), nhận thêm 30% sát thương; 30 giây sau mới bị choáng lại. |
| **Đè & Gặm** | Bổ chân trước đè con mồi (≤ ~2x người chơi), cúi đầu gặm 4 nhát, rồi đá văng. |
| **Ngậm & Thả** | Ngậm Cắn ra thường hơn; sau khi lắc xé có thể tha con mồi vút lên cao ~18 khối rồi thả rơi, sau đó lao xuống đáp nổ. |
| **Beam Lõi Hextech** | Chồm lên, viên ngọc giữa ngực phình sáng (1.5 s), rồi bắn beam tím-xanh dày (2.8 s) quét theo mục tiêu: sát thương rất cao mỗi 0.2 s, đốt cháy, khoan xuyên tường. Xong thì **quá tải**: gục xuống xả khói, toàn bộ phần phát sáng tắt xám 2.4 s, nhận thêm 30% sát thương. Hồi ~25 s (phase 2 nhanh hơn). |
| **Vòng sóng điện** | Gầm, dậm, khạc sét, EMP, gồng lõi, tiếp đất... đều phát các vòng sóng điện gấp khúc lan ra. |
| **Nổ khi chết** | Trong **20 khối là chết** (xuyên giáp, xuyên Blast Protection, tính theo máu tối đa nên boss khác cũng chết); 20–40 khối vẫn rất đau. Giơ khiên đúng hướng thì sống (khiên vỡ). |

## Bản 1.10

| Thay đổi | Mô tả |
|---|---|
| **Bay khạc điện xuống** | Bay lên lượn vòng quanh mục tiêu ở độ cao ~12 khối (x scale), quay mặt về nó, gồng 1.2 s rồi khạc điện chéo xuống ~4.8 s; xong thì lao xuống đáp vào trận. |
| **Lượn bắn** | Vòng ra một bên, lượn thấp và nhanh cắt ngang qua mục tiêu, khạc 3 tia sét (phase 2: 4) khi đi qua đầu nó. |
| **Khạc điện lâu hơn** | Hơi thở sét 3 s → 4.5 s (mặt đất và trên không). |
| **Gầm nửa cầu** | Gầm thổi bay mọi thứ trong nửa quả cầu quanh nó (cả trên không, cả đạn bay), không chỉ trên mặt đất. Bị vây đông cũng gầm. |
| **Quẩy đuôi đúng lúc** | Đuôi chỉ quất khi thật sự có địch ở đuôi. Bị vây hoặc mục tiêu chui dưới bụng mà đuôi trống: **xoay 360° xả điện** (đuôi + cánh quét quanh, cơ thể phóng điện ra xung quanh). |
| **Không cho mob đứng trên lưng** | Thứ gì đứng/được dịch chuyển lên lưng bị trượt khỏi sườn (không còn bị nâng lên trên), bị chích điện; nếu cứ bám, rồng xoay 360° hất văng. |
| **Nhảy giữ tầm (4 hướng)** | Quá gần thì nhảy lùi, hơi xa thì nhảy tới, lệch sang bên thì nhảy ngang — đưa mục tiêu vào đúng tầm hàm rồi đánh ngay. |
| **Beam mạnh hơn** | Beam lõi 7 → 10 sát thương mỗi nhát. |
| **Chỉ sét từ miệng phá block** | Hơi thở và tia khạc vẫn phá block yếu; sét trời (bão, sấm, gầm) không phá gì. |
| **Sóng điện tức thì** | Bỏ các vòng sóng xanh lan chậm dưới chân; thay bằng chớp điện lan ra trong 1 tick. |
| **Gặm to hơn** | Gặm/ngậm được tới cỡ Warden; con mồi nằm trong hàm (không còn bị kéo lên thân). Không ra đòn nếu mục tiêu quá to hay là boss. |
| **Giáp lưng hextech** | Dọc sống lưng: vảy giáp đồng nâu viền vàng, hàng vảy xanh hextech trên sống (sáng ở phase 2); vây lưng thêm dải vảy xanh. |

## Phase 2 (≤ 50% máu): Hextech quá tải

Gồng lên quá tải (chồm, giương cánh, điện chạy khắp người, nổ EMP). **Không đổi màu đỏ nữa:** vảy hiện lên các **đường
vân hextech phát sáng**, cả hàng vây lưng sáng rực, và **mọc thêm vây pha lê phát sáng** lớn dọc cổ, lưng, đuôi cùng các
mảng vảy lục giác sáng ở hai bên sườn (kiểu Godzilla), mọc dần từ vai ra đầu và đuôi trong lúc gầm. Thanh boss chuyển
xanh. Đánh nhanh hơn ~1/3, đau hơn 25%, nối combo nhiều hơn, né nhiều hơn, bão sét đánh liên tục vào mục tiêu, thêm
Skyfall và Xé Đất.

## Tháp Hextech (≤ 30% máu, một lần mỗi trận)

1. Rồng bật **khiên xanh trắng** (miễn mọi sát thương), bay về giữa hang và đáp xuống.
2. **4 Tháp Hextech** cao ~18 khối mọc lên quanh nó (bán kính ~28 khối), mỗi tháp **120 máu**; tia điện từ tháp vào
   lõi ngực rồng. Thanh boss xanh hiện số tháp còn lại và thời gian.
3. Có **25 giây**: phá hết 4 tháp thì **khiên vỡ**, rồng choáng 4 giây (nhận thêm 30% sát thương); không kịp thì rồng
   **hồi 8% máu tối đa cho mỗi tháp còn đứng** và **nổ điện** quanh mình.

## Khắc chế

- **Sóng Nhiễu Điện (EMP Screech)** làm rồng choáng: đang bay thì rơi xuống, nhận thêm 30% sát thương; sau đó kháng
  choáng 15 giây.
- Dụ nó **Húc vào tường** để nó choáng.
- Nó vỗ cánh lùi / nhảy qua lại là sắp khạc sét: nấp sau vật cản hoặc chạy ngang.
- Đánh vào **đầu** (×1.3). Khi nó hạ thấp người lấy đà là sắp **Vồ**: chạy ngang. Đừng đứng sau đuôi, đừng nép dưới ngực.

## Cái chết

Rồng gục xuống, cuộn tròn. Các **tấm hextech** khóa thành **một quả cầu** quanh nó, ánh sáng tích tụ rồi **nổ**: bán
kính **40 khối**, tới **80 sát thương** gần tâm. **Giơ khiên về phía vụ nổ thì sống (chỉ nhận 10%) nhưng khiên chắc chắn
vỡ.** Không phá địa hình. Đồ rơi ra sau vụ nổ.

## Rồng triệu hồi (cưỡi được)

Triệu hồi bằng cuộn **Triệu Hồi Rồng Công Nghệ** (chỉ boss rơi). Chủ nhân chuột phải vào rồng (bất kỳ phần nào) để cưỡi.

- **Camera tự chuyển sang góc nhìn thứ 3, kéo xa** (~7 khối thêm so với mặc định, tự né tường). Xuống rồng thì trả lại góc
  nhìn cũ.
- **Ghế ngồi cố định** trên lưng giữa hai gốc cánh (chừa khoảng trống ở hàng vây), chỉ nghiêng theo hướng bay, không nhún
  nhảy theo animation, nên không còn giật.

| Điều khiển | Tác dụng |
|---|---|
| W A S D | đi / bay theo hướng nhìn; giữ W một lúc thì tăng tốc |
| Space | cất cánh, bay lên |
| **Hạ xuống** (Ctrl trái, đổi được trong Controls) | hạ độ cao, đáp |
| Chuột trái | cắn / cào luân phiên (trên không: cắn) |
| Giữ chuột phải | hơi thở sét theo hướng nhìn |
| **R** | Gầm Sấm |
| **G** | Ngậm Cắn (dưới đất) |

Không ai cưỡi: bay theo chủ, đánh kẻ chủ đang đánh / bị đánh (dưới đất dùng cả bộ đòn mới: vồ, lướt cào, húc, né...),
không có việc gì thì đáp cạnh chủ, ngồi/nằm nghỉ.

## Rơi đồ

2–4 Lõi Rồng Công Nghệ, rune, bánh răng, Energized Core, 1 mô-đun cấp II (35% thêm cấp III), 2 scroll Cơ Khí chất
lượng cao + 1 scroll Lightning, scroll **Triệu Hồi Rồng Công Nghệ** (chắc chắn rơi), 600 XP.

## Animation (68 của rồng)

Đất: ground_idle, walk, run, sit, lie_down, rest, rest_up, sleep, wake. Đòn đất: bite, bite_sweep, claw_left,
claw_right, grab, grab_shake, grab_toss, tail_whip, tail_whip_right, tail_sweep, stomp, wing_gust, field_roar, rend,
breath_charge_ground, breath_ground, roar, **pounce, dash_claw_left, dash_claw_right, dodge_left, dodge_right, ram**.
Trên không: fly, fly_fast, glide, hover, dive, **dive_bounce**, takeoff, land, swoop, cog_spit, thunder, roar_air,
**storm**, breath_charge, breath, air_bite, slam.
Thả diều / tiếp đất (1.8): **backstep, wing_push, spit, crash_land** (nhảy qua lại dùng dodge_left/right).
1.9: **emp_stunned, pin_gnaw, carry, core_charge, core_beam, overload**.
1.10: **spin_discharge, hop_forward, hop_back, breath_down, strafe**. Đặc biệt: phase_two, pylon_charge, stunned, death.
Tháp: rise, charge, collapse. Vỏ cầu: assemble, charge, burst.
