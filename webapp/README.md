# Kalam Motion Studio — local capture

The current reference appearance is **v15**. It uses the exact portrait requested by the user, refines face proportions and eyelid aperture, adds 2,640 Head-weighted fine hair ribbons, and uses soft neutral portrait lighting. Face mode now uses an orthographic camera aligned to the reference; other views retain perspective. The original 87 bones and 51 face targets remain. The v14 hand maps and anatomical detail are retained.

The current skin revision is **v14**. It replaces the earlier tinted projection with a generated photographic-style facial source aligned through 468 UV landmarks, and a generated aged-hand color tile. Color, variable roughness and tangent normal maps are baked at 2048 square for the face, both hands and retained body/head. The browser now includes these normal and roughness maps; the earlier export omitted them. Fine pore relief, anatomical hand creases and soft environment reflections are present. The original generated sources are 1254 square, not 2K scans. Small dorsal tendon/knuckle relief was added to the hands without changing topology, weights or bone names. Generation prompts and source assets are in `../textures/skin_v14/GENERATION.md`.


Open **http://127.0.0.1:8080**. This is a local application; model files, camera processing, and the motion relay remain on this computer. The app uses pinned MediaPipe Tasks Vision 1.2.3 and Three.js 0.180.0. Models and dependencies are installed locally; no CDN is needed at runtime.

## Starting again

1. Open Blender and start its MCP server on port **9876**.
2. Run `Start Motion Studio.ps1` from the project root. It loads `blender/apj_reference_v15_master.blend` when needed, installs the fixed local capture bridge, starts the local HTTP server, and opens the app. It preserves the current v12/v13 project when already loaded.
3. Alternatively run `.venv-facefit/Scripts/python.exe webapp/connect_blender.py`, then `.venv-facefit/Scripts/python.exe webapp/server.py`, then open the URL. **Connect Blender** in the page can reconnect after a Blender restart while the HTTP server remains running.

## Capture

- Click **Start camera** and allow this local page to use your camera. Microphone access is not requested.
- For facial motion, relax your face, face the camera, and click **Calibrate neutral face**. Then smile, blink, look around, or open your mouth. Measured smile, jaw, and blink levels appear below the controls. The five-second **Smile** button is a rig preview, not a camera-cloning demonstration.
- Arms and elbows work with upper-body framing, even if hips are hidden. Each arm segment still needs its own visible landmarks.
- For seated height, stand so shoulders, hips, knees, and ankles are visible, then click **Calibrate standing pose**. Keep the camera still afterward. The app estimates root-height changes from the calibrated image-plane hip position; this is approximate, not a floor-calibrated multi-camera solution.
- Keep hands in view for individual finger and wrist tracking. Landmark wrist positions associate handedness with the anatomical body side. Mirroring affects only the camera display.
- Use **Standing**, **Seated**, and **Neutral** to inspect deformation without a camera. Seated is a preset test, separate from live capture.
- **Record motion** writes rig and facial coefficient keyframes to Blender actions. Stop recording before playback. **Save Blender session** saves `blender/apj_reference_v15_session.blend`. Camera images and audio are not recorded.

## Rig and preview

The source rig has **87 bones**, including 30 finger joints, existing arms/legs/feet/toes/spine/neck/head/jaw/eyes, plus 24 independently poseable weighted rib controls and a sternum control. Rib motion follows the torso: individual ribs are not directly detected by MediaPipe. This is not a rig of all 206 anatomical human bones.

The runtime asset is `assets/apj_runtime_v15.glb`, with the latest complexion and brow/upper-lip shader colors baked from Blender. Face geometry and all 51 existing targets are subdivided together; the suit and hands are also smoothed. Eyelid contact is evaluated into the face targets, and runtime skin weights are normalized to four influences for Three.js. Eye/rib bone names are matched through Three.js name sanitization. The renderer uses front-facing studio lights and smooths incoming joint rotations.

The neck bone is not lengthened. The collar was raised by at most 6 mm for a compact exposed neck.

## What was verified

- Live Lenovo FHD webcam stream reached Blender. Body, hand, facial coefficients and gestures were observed. GPU detector throughput varied around 18–27 inference FPS during checks; this number is not a guaranteed end-to-end render rate.
- All 30 digit joints respond in synthetic open/fist tests. Standing, seated hips/knees (~88 degrees), tracking-loss recovery, and neutral reset pass. A regression specifically verifies both arm chains with invisible hips, with target-direction dot products greater than 0.995.
- Facial jaw/dentition, gaze, blink occlusion, geometric wrinkles, expression combinations and neutral reset checks pass.
- HTTP checks verify the local relay, payload bounds, origin restrictions, command allowlist, and actual GLB morph data. The GLB contains 51 nonempty face targets, rather than merely a static face.

Evidence: `../tests/fullbody_v12_validation.json`, `../tests/capture_v13_facial_validation.json`, `../tests/runtime_v13.json`, and `../tests/test_motion_webapp.py`.

## Remaining limitations

The face remains a reference-guided reconstruction, not an exact scan or certified likeness. Its head/face join remains unwelded and needs sculpt/retopology cleanup. Extreme facial expressions and garment intersections need artist review. A single camera cannot recover hidden joints, exact finger twist, individual rib motion, cloth dynamics, or exact seated floor contact. The existing coat is skinned geometry, not a separate cloth simulation. Actual full-body seated webcam performance still needs review with the complete person visible.

The Blender master retains procedural detail and fine hair that are approximated in the standard-PBR browser preview. No exact image-to-image color equivalence is claimed across different lighting/renderers.

## Implementation

`tracking-worker.js` runs face, hand and pose inference in a worker, tries GPU and falls back to CPU. `server.py` serves only the app assets and validates JSON. UDP packets stay on `127.0.0.1:9877`; `scripts/fullbody_bridge.py` applies them on Blender's main-thread timer. `scripts/fullbody_tracking.py` solves global limb directions into bone-local rotations in parent order. The app does not accept arbitrary executable code; the reconnect endpoint runs only the project's fixed bootstrap script through the existing MCP server.
