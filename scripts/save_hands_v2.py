import bpy,os
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;r=bpy.data.objects['Armature'];m=bpy.data.objects['char1']
for b in r.pose.bones:b.matrix_basis.identity()
for k in m.data.shape_keys.key_blocks:k.value=0
s.frame_set(1)
cam=s.camera;cam.location=(2,-4,1.85);cam.rotation_euler=(Vector((0,0,.85))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.05
s.render.resolution_x=1000;s.render.resolution_y=1100
for filename in ['rebuild_hands.py','finish_hand_albedo.py','validate_hands_v2.py','save_hands_v2.py']:
    text=bpy.data.texts.get(filename)
    if text:bpy.data.texts.remove(text)
    bpy.data.texts.load(os.path.join(ROOT,'scripts',filename))
bpy.ops.object.select_all(action='DESELECT')
for o in [r,m]+[o for o in s.objects if o.name.startswith('APJ_Hand_') or o.name.startswith('APJ_Nail_')]:
    o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'exports','apj_hands_v2.glb'),use_selection=True,export_apply=False,export_animations=False,export_all_influences=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','apj_hands_v2_master.blend'))
print('Saved hands v2 master and neutral rigged GLB')
