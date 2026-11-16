# Kalam v15 OBJ

Open `apj_reference_v15.obj` with `apj_reference_v15.mtl` and all `texture_*.png` files in this folder.

This is a static, textured export of the v15 runtime character in its neutral pose. OBJ does not preserve bones, skin weights, facial shape keys, or animation. Use `blender/apj_reference_v15_master.blend` for the editable rig or `webapp/assets/apj_runtime_v15.glb` for the rigged runtime asset.

Generated with `scripts/export_obj_v15.py` in Blender background mode. The exporter verifies mesh data, the material library, and all referenced texture paths. OBJ material support varies between applications and does not reproduce every glTF PBR shader feature.
