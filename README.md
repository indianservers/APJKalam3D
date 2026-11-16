# APJ Abdul Kalam — development character

## Current appearance target — v15

Open `blender/apj_reference_v15_master.blend` or the local motion app. The user's exact attached portrait is preserved in `textures/reference_v15/exact_appearance_target.png` and used directly as the face/front-head color source. A bounded reference-space fit refines the face, and eyelid aperture and soft frontal lighting are adjusted for this portrait. The browser face view uses an orthographic portrait camera to avoid exaggerated perspective. 2,640 fine strand ribbons (120,480 vertices) are weighted to Head and included in the web asset, replacing the color-only hair-shell appearance. Existing 87 bones and 51 face targets are retained. Source-space photo matching does not determine hidden anatomy or certify exact likeness from other angles. Facial functional checks: `tests/reference_v15_facial_validation.json`.


## Current skin revision — v14

Open `blender/apj_skin_v14_master.blend` or http://127.0.0.1:8080. New generated face and hand color sources are applied with 2K roughness and normal bakes, including the browser runtime. The prior color-only export did not carry the skin normal/roughness detail. The new face source is aligned by UV landmark fitting, and hand creases plus small dorsal tendon/MCP relief preserve existing finger topology and weights. Generated sources, exact generation prompts and map limitations: `textures/skin_v14/GENERATION.md`. Actual Blender close-ups: `renders/skin_v14_face.png` and `renders/skin_v14_hand.png`. Previous masters remain preserved. Face/hand forms and the head join still need geometry refinement for production photorealism.


## Live motion studio — v13, 16 November 2026

Open **http://127.0.0.1:8080** for local webcam body, hands, fingers, facial expressions and eye tracking. The current master is `blender/apj_capture_v13_master.blend`. Startup and calibration instructions, validation evidence and remaining limitations are in `webapp/README.md`. Start again with `Start Motion Studio.ps1` after enabling Blender MCP on port 9876.

The rig now has 87 bones, including 30 finger joints, 24 weighted rib controls and a sternum control. Standing/seated and hidden-hips arm tests pass; individual ribs follow the torso rather than being directly camera-tracked. The exposed neck remains compact. A new smoothed, skinned browser GLB includes all 51 face targets, actual baked appearance colors, eyelid-contact corrections, normalized runtime weights and corrected front lighting. Neutral-face calibration, a gentle smile test, expression-level readouts, motion recording and session save controls are included. Live webcam coefficient delivery was verified; exact full-body seated cloning and production-level cloth/face joins are not claimed.

This project is **not yet a production-quality digital human**. It develops the supplied Meshy character and records what was actually verified. Original files in the project root are preserved.

## Latest revision: facial micro refinement v9

Open `blender/apj_micro_likeness_v9_master.blend`. Conservative sculpt adjustments reduce nose-tip projection and alar fullness, gently lift relaxed mouth corners, and soften the lower-lip/chin and nasolabial transitions. Maximum vertex movement is 0.781 mm. All 51 targets are preserved; facial functional checks pass in `tests/micro_likeness_v9_rig_validation.json`. Cycles reviews: `renders/micro_likeness_v9_front.png` and `renders/micro_likeness_v9_three_quarter.png`. The v8 master remains preserved. This is a reference-guided approximation, not a measured likeness percentage; the unwelded head join remains.

## Previous revision: jaw and posterior cheeks v8

Open `blender/apj_jaw_cheeks_v8_master.blend`. The new portrait is preserved as `references/apj_jaw_reference_v8.png`. This localized sculpt rounds the jaw/chin transition and adds modest volume around the jaw corners and posterior cheeks near the ears. The same field was transferred through the face, retained source head and concealed backing, preserving all 51 existing shape targets. The rest of the facial proportions, dark brown eyes and v7 complexion are retained. The file opens in neutral for comparison with the new portrait.

A separate Cycles overlap-shadow correction softens the artificial cut line where the facial patch meets retained head skin. This changes shadow handling only near that join, plus the concealed backing; it does not weld the topology. A future real-time export needs its own join/material review. Actual reviews are `renders/jaw_cheeks_v8_front.png`, `jaw_cheeks_v8_left_three_quarter.png`, and `jaw_cheeks_v8_right_three_quarter.png`. Sculpt parameters are recorded in `tests/jaw_cheeks_v8.json`; `tests/jaw_cheeks_v8_rig_validation.json` confirms that the expression, jaw/dentition, gaze, blink, wrinkle, combination and neutral-reset checks passed after the change. Earlier masters remain unchanged. The single portrait still does not determine an exact hidden rear-cheek profile.

## Previous revision: deeper reference complexion v7

Open `blender/apj_complexion_v7_master.blend`. This pass makes the face, retained neck/head skin and hands more distinctly golden-brown, reduces the pale/ashy skin sheen, and replaces the blue fill light with warm-neutral illumination. A skin-pigment mask prevents the stronger adjustment from tinting silver hair-edge pixels. The dark brown eyes from v6 are retained. Actual Cycles review: `renders/complexion_v7_face.png`. Parameters and construction are in `tests/complexion_v7.json` and `scripts/complexion_v7.py`. Geometry and facial controls were not changed. The previously documented likeness and seam issues remain.

## Previous revision: skin and eye materials v6

Open `blender/apj_skin_eyes_v6_master.blend`. Skin on the face, retained neck/head skin and hands uses a deeper, less orange warm-brown material response. Saturation was restrained, skin specular/SSS reduced slightly, and the irises changed from lighter amber fibers to deep brown with a dark limbal edge and near-black pupil. Sclera is warm off-white. The user's supplied appearance reference guided these adjustments; nationality alone does not define one complexion or eye color.

This is a material pass. The v5 geometry, facial controls and reference pose are preserved; the documented cheek/neck seam and likeness limitations remain. Actual Cycles reviews are `renders/skin_eyes_v6_face.png` and `renders/skin_eyes_v6_eye_closeup.png`. Parameters are recorded in `tests/skin_eyes_v6.json`, and the construction script is `scripts/skin_eyes_v6.py`. Earlier masters remain unchanged.

## Previous revision: reference-guided likeness sculpt v5

Open `blender/apj_likeness_v5_master.blend`. It opens with the fitted reference-smile pose. The previous v4 master remains unchanged. The face was geometrically sculpted around the cheeks, jaw taper, chin pad, nose tip/alar forms, bridge/glabella, brows, lips and mature eyelid opening. The eyes were recessed 1.1 mm into the sockets. The sculpt field was transported through the 49 existing facial targets, into retained head skin, and through the hair/mouth geometry where the landmark fit affected it. Two additional sculpt correctives calibrate smile lip opening and relaxed lip closure.

The supplied `Dr. Kalam’s Welcoming Wave.png` and actual Blender renders were measured with MediaPipe Face Landmarker in an isolated project environment (`.venv-facefit`). A bounded smooth field fit the eye-aligned image-plane forehead, cheek, nose and lip proportions. The measured landmark mismatch fell by about 22% in the final rendered view. This is a detector-based proportion guide, **not a likeness score or proof of an exact reconstruction**. The single view does not determine unseen depth. It is a closer development approximation; an exact likeness and production sculpt are still unfinished.

The source head/facial-patch overlap was retained. A finer-cut/ribbon transition experiment failed visual/bounds checks and was rejected. Shared sculpt transport and a concealed skin backing are used in the saved version. Visible cheek/neck transition lines and residual contour artifacts still need manual sculpt/retopology cleanup; the head is not a welded production surface. Those limitations are visible in the saved clay review and are not treated as completed work.

`tests/sculpt_v5.json` records the sculpt, preserved targets, reference pose and remaining issues. `tests/sculpt_v5_fit_verification.json` records the front-view fitting diagnostic. `tests/sculpt_v5_rig_validation.json` confirms that the existing expressions, independent gaze, jaw/dentition, blink occlusion, geometric wrinkles, combinations and neutral reset still pass after the sculpt. The 62-bone rig and v4 demonstration are retained. This turn does not create a new real-time export.

Run `facial_v4_demo_ui.py` and `likeness_v5_controls.py` from the embedded texts if the sidebar is absent after reopening. Under **N → APJ Face**, **Show reference smile** restores the fitted pose, **Reset face to neutral** allows manual work, and **Load 20-second facial demo** restores the existing demonstration. Actual review renders are `renders/sculpt_v5_reference_pose_front.png`, `sculpt_v5_reference_pose_three_quarter.png`, `sculpt_v5_neutral_front.png`, and `sculpt_v5_clay_front.png`. The pre-sculpt comparison is `renders/sculpt_v5_before_reference_pose.png`. `scripts/rebuild_likeness_v5.py` recreates a separate rebuilt file from v4 and the frozen fit field. The isolated landmark environment uses `scripts/facefit-requirements.txt`.

## Previous revision: facial animation v4

Open `blender/apj_facial_v4_master.blend`. Play frames **1–600 at 30 fps** for the saved 20-second facial demonstration. Timeline markers identify brows, frown, smile, squint, independent/both-eye blinks, jaw opening, pucker/funnel, horizontal/vertical gaze, combined smile/jaw and a speech-shape test. This is an actual driven Blender animation, not a sequence of altered portraits.

The new `APJ_Face` surface has 9,204 vertices and 8,948 quad faces, with real eye and mouth apertures. It uses 43 expression shape keys and six additional geometric wrinkle correctives. The full skeleton now has 62 bones, including `Jaw`, `Eye.L` and `Eye.R`. Separate eyeballs and clear corneas rotate independently. A mouth cavity, 28 teeth, gum arches and tongue are attached to the upper head or jaw as appropriate. Lower dentition and tongue move with the jaw while upper teeth remain on the head. Eye contact corrections keep facial skin outside the corneas during combinations.

Run the embedded `facial_v4_demo_ui.py` in Blender's Text Editor if the panel is absent after reopening. Open the **N sidebar → APJ Face**. **Reset face to neutral** detaches the demonstration for manual controls. The panel provides individual sliders, jaw controls, gaze, expression presets and A/E/O/M speech-shape tests. **Load 20-second facial demo** restores playback. The sidebar is registered in the current session; automatic execution preferences were not changed. Use `APJ_Face_Controls` for animation, rather than the legacy shape keys still retained on `char1`.

Wrinkles include real geometry deformation driven by brow raising, frown, smile and squint, plus shader detail. Permanent age texture remains visible at neutral. A validation test isolated about 0.167 mm of evaluated geometric wrinkle movement from the larger brow raise. Jaw range is deliberately limited to 11.46 degrees, with eye yaw limited to about 17.2 degrees and pitch to 16 degrees. This is a functional development rig, not production FACS sculpt certification.

`tests/facial_v4_validation.json` records independent checks for all 43 expression controls and ten gaze inputs (eight coefficient controls plus two combined-gaze sliders), jaw/upper/lower-teeth/tongue behavior, independently tested blink occlusion, isolated wrinkle deformation, combined expressions and exact return to neutral. Blink tests measure the evaluated facial mesh covering sampled iris-region rays rather than merely checking a shape-key value. `tests/facial_v4_demo_adapter.json` checks the saved demo and synthetic coefficient smoothing, invalid inputs and tracking-loss return to neutral. `renders/facial_v4_*.png` contains the Cycles expression review images.

`mocap/facial_v4_mapping.json` maps 43 non-gaze coefficients to shapes, eight gaze coefficients to eye bones, and neutral to the implicit zero pose. Names were checked against the [official Face Landmarker enum](https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/mediapipe/tasks/python/vision/face_landmarker.py). `scripts/facial_v4_mediapipe.py` accepts supplied dictionaries or category objects and applies confidence filtering and smoothing. It does not open a webcam or run MediaPipe inference. Subject left/right conventions must be preserved, and mirrored detector data normalized upstream. The older retargeter's seven-key face path is superseded by this adapter for v4.

Limitations remain: the reconstructed front surface overlaps the original head and is not a welded full-head retopology; neck/cheek transitions and extreme expressions still need sculpt and weight cleanup. The eye and mouth systems are reconstructed rather than scan-derived. A/E/O/M presets do not constitute automatic audio lip synchronization. Live tracking and runtime performance have not been tested. The previous v3 GLB is preserved and **does not contain this v4 facial reconstruction**. Drivers, contact corrections and procedural eye materials require a separate bake/export pass for a real-time engine. The requested work here is delivered in the Blender master and saved facial demonstration.

## Previous revision: appearance v3

Open `blender/apj_appearance_v3_master.blend` for the latest appearance work. This preserves the hands-v2 rig and geometry while adding aged skin coloration and fine detail, separate skin/hair/fabric/leather surface responses, fine hair curves following the original envelope, and two thin corneal reflection layers. The solid hair envelope remains underneath; this is not a complete strand groom. Corneal overlays improve reflections but do not add eye rotation or a blink rig.

The built-in `image_gen` tool enhanced a frontal albedo view matched to the existing mesh, using the supplied welcoming-wave image as the appearance reference. The 1254×1254 generated source was projected onto the actual model and baked into its original UV layout. Three reusable 4096×4096 atlases are saved under `textures/appearance_v3/`: `APJ_v3_Baked_Albedo_4K.png`, `APJ_v3_Baked_Roughness_4K.png`, and `APJ_v3_Baked_Normal_4K.png`. Atlas size does not imply native 4K generated detail. A first generated fragmented atlas was rejected for island drift and is not used. Exact prompts and disposition are in `textures/appearance_v3/generation_prompts.json`.

The master uses subsurface skin shading, varying roughness, UV normal detail and a driven forehead overlay whose mask follows mesh deformation. The generated skin is artistic reconstruction, not measured scan data. Side and back detail blend into the original atlas, and coarse facial geometry still limits likeness and close-up realism. `exports/apj_appearance_v3.glb` uses standard PBR materials with the baked maps and preserves the rig, facial prototype shapes, hands and nails. Cinematic hair curves, corneal overlays and the Blender wrinkle driver are excluded. This is a neutral rigged export without animation clips.

Actual Cycles review renders use the `renders/appearance_v3_` prefix: face front, three-quarter face, eye detail, hair detail, fabric detail, shoe detail and full body. These are renders of the modified 3D model, not the generated source image. Construction, bake, stable UV material, render and delivery scripts are stored under `scripts/` and embedded in the master. Appearance metadata and export checks are recorded in `tests/appearance_v3*.json`.

## Previous revision: rebuilt hands v2

Open `blender/apj_hands_v2_master.blend` for the previous hand reconstruction. The previous development master is preserved. This revision replaces both coarse hands with connected, predominantly quad meshes: five distinct fingers per hand, rounded pads, knuckle relief and dense bend loops. Each hand has 2,403 base vertices and 2,440 faces (2,362 quads, with triangle closures at the fingertips). Each has zero non-manifold edges, degenerate faces or unweighted vertices. The wrist connection is concealed within the cuff and is not welded to the body. The pre-replacement geometry is kept as the hidden `SOURCE_Before_Hand_Rebuild` object.

Ten separate curved nail plates follow the distal finger joints. The hands have dedicated 2K UV atlases for source-transferred albedo, roughness and tangent normal detail, plus a separate height source. Projection misses on the reconstructed thumb were replaced with corresponding source-finger skin texels. The original atlas contains baked shading; the transfer does not turn it into a scan-quality skin texture. Procedural crease and pore maps supplement it. Nail color variation uses vertex colors, with a narrow lighter free edge. The appearance and reconstructed anatomy still need artist review before production acceptance.

`exports/apj_hands_v2.glb` contains the neutral rigged character with both new hands, ten nail meshes and skin textures. It has no animation clips; the 59-bone skeleton remains independently poseable. `tests/hands_v2_validation.json` records all 30 joint movement tests, nail attachment, opposite-hand isolation, normalized weights and topology. `tests/hands_v2_export_roundtrip.json` records another 30 deformation checks after GLB reimport and confirms the skin texture maps survived. Both reports passed. Review images are `renders/hands_v2_left_open.png`, `hands_v2_right_open.png`, and `hands_v2_left_curl.png`.

Use `character_controls.py` and **Reset to neutral** before manual posing. Finger flexion is exposed as each phalanx's local Z rotation; negative Z curls the right hand. The v2 rig rest positions have been fitted to the new fingers. Full thumb opposition, extreme fists and self-contact remain areas for further anatomical correction and captured-motion validation.

## Open and use

Open `blender/apj_development_master.blend`. The character is in its source rest pose at frame 1. Play frames 1–360 to see independent finger-joint pulses, body movement, and separate brow/smile prototype tests. This is a test sequence, not a finished performance.

Run the embedded `character_controls.py` text in Blender's Text Editor to add the **N sidebar → APJ** panel. **Reset to neutral** detaches the test actions for manual posing. The panel exposes all 30 individual finger flexion joints and seven facial prototype sliders. **Load joint and face test animation** restores the demo. The panel registration lasts for the current Blender session; this file does not silently enable automatic script execution.

`blender/apj_working.blend` is the imported pre-upgrade checkpoint. The original walking animation remains recoverable from the unchanged root FBX. Its original action is retained as source data in the development file but is not certified after transform normalization; the exported animation is the new test sequence.

## Implemented and checked

- Reused the supplied textured 3D mesh, initially 13,663 vertices and 10,372 triangles. Welding coincident vertices reduced it to 5,188 vertices while retaining loop UVs. All faces remain triangular; this is not facial retopology.
- Topology inspection found 12 boundary edges and 20 non-manifold edges (including boundaries). These remain unresolved; the mesh is not certified clean for production deformation.
- 59-bone development armature: original body rig, root, 30 finger phalanges, and optional foot IK/pole helpers. Foot IK constraints default to zero influence and need pole calibration before use.
- Finger skin weights fitted from hand-space guides, normalized; all 30 individual joints moved evaluated mesh vertices. Tight curls show pinching and need hand topology and weight correction.
- Seven **closed-mouth prototypes**: `browInnerUp`, `browOuterUpLeft`, `browOuterUpRight`, `browDownLeft`, `browDownRight`, `mouthSmileLeft`, `mouthSmileRight`. These are spatially masked deformations, not anatomically validated FACS shapes.
- Blender forehead bump response driven by brow shape values. Strength was measured at 0.12 neutral and 0.77 raised. This is a simple procedural development effect; it does not implement a full permanent/dynamic wrinkle-map workflow.
- Packed original 4K base-color, metallic and roughness atlases; smooth shading and optional master subdivision. The source appearance has photographic lighting and detail baked into its color map.
- Cycles studio lighting and review renders. Review resolution is 800px; the three-quarter body render is 1000×1100. These are development inspections, not final 4K renders.
- Animated GLB reimported in an isolated Blender scene: 59 bones, seven morph targets, skinning, animation movement, all 30 finger joints and all seven morphs passed vertex-displacement checks. Tests do not certify anatomical quality or engine-specific performance.
- Partial calibrated retargeting module with coordinate conversion, confidence filtering, frame-rate independent smoothing, rotation limits, and return to neutral. Synthetic body directions and facial coefficients passed response/recovery testing. **No live camera, MediaPipe runtime, or real-time FPS was tested.**

## Files and validation

- `exports/apj_development.glb`: development skin, seven morphs, test animation, PBR atlas material. Blender procedural wrinkle shader, live drivers and IK controls are not exported. The base triangle mesh is used; this is not an independently optimized LOD asset.
- `mocap/mediapipe_mapping.json`: exact names for the seven implemented prototype coefficients; all other coefficients are explicitly unsupported.
- `scripts/upgrade_character.py`: rebuild from the pre-upgrade working checkpoint; refuses to run twice.
- `scripts/validate_character.py`: body/finger/shape movement, weights, texture paths and wrinkle driver.
- `scripts/verify_export.py`: isolated GLB reimport and independent morph/finger tests.
- `scripts/motion_retargeting.py`: Blender module for already supplied metric 3D landmarks and coefficients. Calibrate in a known neutral pose before updates. Handedness must be supplied anatomically as Left/Right; normalize any mirrored detector labels upstream. Normalized image coordinates cannot be substituted for metric world coordinates. Single-vector tracking does not solve twist or wrist orientation, and occlusions remain ambiguous.
- `tests/*.json`: machine-readable build, deformation, retargeting and roundtrip results.
- `renders/`: body views, face/brow and hand/curl review images.

Official interface references checked during implementation: [Face Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker), [Hand Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker). This project does not claim all 52 facial coefficients.

## Required work before production acceptance

The supplied mesh is one exterior shell containing face, painted eyes, closed mouth, hair, jacket and trousers. Missing components cannot be recovered reliably by adding control names. A reliable facial rig requires artist-reviewed reconstruction and retopology around the eyes, lips, jaw and forehead, separate eyeballs and eyelids with correct contact, a mouth cavity, teeth and tongue, and sculpted expression/corrective targets. The current prototypes do not blink, articulate speech, or track gaze.

Also outstanding: likeness approval against multi-view photographic references; anatomical hands and thumb opposition; tested full-body deformation corrections; separate deformable garments and seated-pose tests; strand hair and real-time cards; dedicated skin albedo/normal/displacement/micro-detail maps; expression wrinkle masks and exportable replacements; complete facial coefficient coverage; calibrated head/neck and wrist tracking; actual MediaPipe/webcam integration, recording and playback harness; performance measurement; optimized LODs and independent runtime review. Source arm alignment remains slightly below horizontal and needs review before declaring a strict T-pose.

Do not treat passing displacement tests as production sign-off. The next priority is replacing the facial shell with a deformation-ready reconstruction while preserving UV/material references and the working rig.
