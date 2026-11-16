import bpy,json,os,math
ROOT=r'C:\Abdul Kalam';scene=bpy.context.scene;face=bpy.data.objects['APJ_Face'];ctrl=bpy.data.objects['APJ_Face_Controls'];rig=bpy.data.objects['Armature']
scripts=['sculpt_likeness_v5.py','match_sculpt_v5_head_overlap.py','finish_likeness_v5.py','reference_expression_v5.py','measure_reference_v5.py','fit_reference_landmarks_v5.py','apply_landmark_sculpt_v5.py','refresh_likeness_v5_rig.py','verify_reference_fit_v5.py','likeness_v5_controls.py','render_likeness_v5.py','save_likeness_v5.py']
for name in scripts:
    existing=bpy.data.texts.get(name)
    if existing:bpy.data.texts.remove(existing)
    bpy.data.texts.load(os.path.join(ROOT,'scripts',name))
if ctrl.animation_data:ctrl.animation_data.action=None
pose=json.loads(face['reference_pose_v5']);channels=json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']
for p in channels:ctrl[p]=float(pose.get(p,0.))
ctrl.update_tag();face.data.shape_keys.update_tag();scene.frame_set(1)
for image in bpy.data.images:
    if image.source=='FILE' and image.has_data and not image.packed_file:image.pack()
original=bpy.data.objects['SOURCE_Facial_v4_PreSculpt'].data.shape_keys.key_blocks['Basis'];current=face.data.shape_keys.key_blocks['Basis']
deltas=[(a.co-b.co).length for a,b in zip(current.data,original.data)]
report=json.load(open(os.path.join(ROOT,'tests','sculpt_v5.json'),encoding='utf-8'))
report.update({'master':'blender/apj_likeness_v5_master.blend','maximum_displacement_from_v4_m':max(deltas),'changed_vertices_from_v4':sum(d>1e-5 for d in deltas),
 'original_shape_targets_preserved':49,'current_shape_targets':len(face.data.shape_keys.key_blocks)-1,'rig_bones':len(rig.data.bones),
 'reference_pose':pose,'source_reference':'Dr. Kalam’s Welcoming Wave.png','reference_fit_report':'tests/sculpt_v5_fit_verification.json','rig_validation':'tests/sculpt_v5_rig_validation.json',
 'transition_strategy':'V4 overlap retained and transported through the sculpt; concealed skin backing. Finer-cut/ribbon experiment rejected.',
 'remaining':['Cheek and neck surface transitions still need artist cleanup','Single-view reconstruction cannot define the exact unseen profile','No production or exact-likeness certification'],
 'missing_textures':[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file and not os.path.exists(bpy.path.abspath(i.filepath))]})
json.dump(report,open(os.path.join(ROOT,'tests','sculpt_v5.json'),'w',encoding='utf-8'),indent=2,ensure_ascii=False)
bpy.ops.object.select_all(action='DESELECT');face.select_set(True);bpy.context.view_layer.objects.active=face
path=globals().get('LIKENESS_OUTPUT',os.path.join(ROOT,'blender','apj_likeness_v5_master.blend'))
bpy.ops.wm.save_as_mainfile(filepath=path)
print('Saved reference-guided sculpt',path,'max basis change',max(deltas),'targets',len(face.data.shape_keys.key_blocks)-1)
