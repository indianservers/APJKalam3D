import bpy,os,json
ROOT=r'C:\Abdul Kalam';main=bpy.context.scene;qa=bpy.data.scenes.new('Appearance v3 Export QA');bpy.context.window.scene=qa;before=set(bpy.data.objects)
try:
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT,'exports','apj_appearance_v3.glb'))
    added=set(bpy.data.objects)-before;rig=next(o for o in added if o.type=='ARMATURE')
    body=next(o for o in added if o.type=='MESH' and o.data.shape_keys)
    hands=[o for o in added if o.name.startswith('APJ_Hand_')];nails=[o for o in added if o.name.startswith('APJ_Nail_')]
    maps=[]
    for mat in body.data.materials:
        images=[n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
        maps.append({'material':mat.name,'images':[{'name':im.name,'size':list(im.size)} for im in images],
          'has_normal_node':any(n.type=='NORMAL_MAP' for n in mat.node_tree.nodes)})
    def co(o):
        bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();res=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();return res
    baseline=co(body);body.data.shape_keys.key_blocks['browInnerUp'].value=1
    face_delta=max((a-b).length for a,b in zip(baseline,co(body)));body.data.shape_keys.key_blocks['browInnerUp'].value=0
    hand=next(o for o in hands if o.name.startswith('APJ_Hand_Left'));baseline=co(hand)
    rig.pose.bones['LeftHandIndex2'].rotation_mode='XYZ';rig.pose.bones['LeftHandIndex2'].rotation_euler.z=.45
    finger_delta=max((a-b).length for a,b in zip(baseline,co(hand)))
    maps_ok=len(maps)==3 and all(item['has_normal_node'] and len(item['images'])>=3 and all(im['size']==[4096,4096] for im in item['images']) for item in maps)
    report={'bones':len(rig.data.bones),'facial_shapes':list(body.data.shape_keys.key_blocks.keys()),'hands':len(hands),'nails':len(nails),
      'materials':maps,'face_deformation_m':face_delta,'finger_deformation_m':finger_delta,'body_vertex_colors':len(body.data.color_attributes),
      'pass':len(rig.data.bones)==59 and len(hands)==2 and len(nails)==10 and face_delta>1e-5 and finger_delta>1e-5 and maps_ok,
      'scope':'Blender glTF reimport, texture presence and sampled deformation. Not a photorealism or performance certification.'}
    with open(os.path.join(ROOT,'tests','appearance_v3_export_roundtrip.json'),'w') as f:json.dump(report,f,indent=2)
    print('Appearance export passed:',report['pass'],'body materials:',len(maps),'face motion:',face_delta,'finger motion:',finger_delta)
finally:
    bpy.context.window.scene=main
    for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.scenes.remove(qa)
