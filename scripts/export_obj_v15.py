"""Export the v15 runtime mesh as a portable, textured static OBJ."""
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[1]
target = root / 'exports' / 'obj_v15'
target.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(root / 'webapp/assets/apj_runtime_v15.glb'))
for index, image in enumerate(bpy.data.images):
    if image.type != 'IMAGE':
        continue
    # glTF images are lazy loaded; reading pixels loads packed image data.
    assert len(image.pixels) > 0, image.name
    image.filepath_raw = str(target / f'texture_{index:02d}.png')
    image.file_format = 'PNG'
    image.save()
    if image.packed_file:
        image.unpack(method='REMOVE')
props = bpy.ops.wm.obj_export.get_rna_type().properties
print('OBJ axis values:', [i.identifier for i in props['forward_axis'].enum_items])
bpy.ops.wm.obj_export(filepath=str(target / 'apj_reference_v15.obj'),
                      export_materials=True, path_mode='RELATIVE')
obj = target / 'apj_reference_v15.obj'
assert obj.stat().st_size > 1000000
text = obj.read_text(encoding='utf-8')
assert '\nv ' in text and '\nf ' in text and 'mtllib ' in text
mtl = target / 'apj_reference_v15.mtl'
assert mtl.exists()
map_count = 0
for line in mtl.read_text(encoding='utf-8').splitlines():
    if line.startswith(('map_', 'bump ')):
        assert (target / line.split()[-1]).exists(), line
        map_count += 1
assert map_count >= 6, 'Missing skin and eye texture references'
print('Verified textured OBJ:', obj, obj.stat().st_size)
