import bpy,os,json,sys
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;face=bpy.data.objects['APJ_Face'];ctrl=bpy.data.objects['APJ_Face_Controls'];rig=bpy.data.objects['Armature']
script_names=['facial_v4_geometry.py','facial_v4_finish_topology.py','facial_v4_assets.py','facial_v4_controls.py','facial_v4_boundary_color.py','facial_v4_lip_extensions.py','facial_v4_contact.py','facial_v4_demo_ui.py','facial_v4_mediapipe.py','validate_facial_v4.py','validate_facial_v4_demo_adapter.py','render_facial_v4.py','save_facial_v4.py']
for name in script_names:
    text=bpy.data.texts.get(name)
    if text:bpy.data.texts.remove(text)
    bpy.data.texts.load(os.path.join(ROOT,'scripts',name))
ctrl.animation_data_create();ctrl.animation_data.action=bpy.data.actions['APJ_Facial_v4_Demonstration']
for p in json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']:ctrl[p]=0.
s.frame_start=1;s.frame_end=600;s.render.fps=30;s.frame_set(1)
ctrl.update_tag();face.data.shape_keys.update_tag();bpy.context.view_layer.update()
for im in bpy.data.images:
    if im.source=='FILE' and im.has_data and not im.packed_file:im.pack()
bpy.ops.object.select_all(action='DESELECT');face.select_set(True);ctrl.select_set(True);bpy.context.view_layer.objects.active=ctrl
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
summary={'master':'blender/apj_facial_v4_master.blend','face_mesh':face.name,'quad_faces':len(face.data.polygons),'vertices':len(face.data.vertices),
 'expression_shapes':len(json.loads(face['expression_channels'])),'wrinkle_correctives':len(json.loads(face['wrinkle_correctives'])),
 'gaze_coefficients':8,'implicit_neutral':True,'rig_bones':len(rig.data.bones),'jaw_bone':'Jaw','eye_bones':['Eye.L','Eye.R'],
 'demo':{'action':'APJ_Facial_v4_Demonstration','start':1,'end':600,'fps':30},
 'validation_report':'tests/facial_v4_validation.json','mapping':'mocap/facial_v4_mapping.json',
 'export_note':'Previous v3 GLB is preserved and does not include v4 facial reconstruction. Blender contact corrections and drivers need a separate export bake.',
 'production_ready':False}
with open(os.path.join(ROOT,'tests','facial_v4_delivery.json'),'w') as f:json.dump(summary,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','apj_facial_v4_master.blend'))
print(json.dumps(summary))
