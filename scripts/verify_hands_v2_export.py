import bpy,os,json
ROOT=r'C:\Abdul Kalam';main=bpy.context.scene;qa=bpy.data.scenes.new('Hand v2 Export QA')
bpy.context.window.scene=qa;before=set(bpy.data.objects)
try:
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT,'exports','apj_hands_v2.glb'))
    added=set(bpy.data.objects)-before;r=next(o for o in added if o.type=='ARMATURE')
    hands={s:next(o for o in added if o.name.startswith('APJ_Hand_'+s)) for s in ['Left','Right']}
    nails=[o for o in added if o.name.startswith('APJ_Nail_')]
    def co(o):
        bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        result=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();return result
    base={s:co(o) for s,o in hands.items()};checks=[]
    for side in hands:
        for finger in ['Thumb','Index','Middle','Ring','Pinky']:
            nail=next(o for o in nails if o.name.startswith('APJ_Nail_'+side+'_'+finger));nb=co(nail)
            for j in range(1,4):
                b=r.pose.bones[f'{side}Hand{finger}{j}'];b.rotation_mode='XYZ';b.rotation_euler.z=.4
                d=max((a-c).length for a,c in zip(base[side],co(hands[side])))
                nd=max((a-c).length for a,c in zip(nb,co(nail)));b.matrix_basis.identity()
                checks.append({'bone':b.name,'skin_displacement_m':d,'nail_displacement_m':nd,'pass':d>1e-5 and nd>1e-5})
    report={'bones':len(r.data.bones),'hands':len(hands),'nails':len(nails),'joint_tests':checks,
      'pass':len(r.data.bones)==59 and len(nails)==10 and all(c['pass'] for c in checks),
      'textures':{s:[n.image.name for n in hands[s].data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image] for s in hands},
      'export_mode':'neutral rigged mesh; subdivision disabled in GLB, no animation clips'}
    with open(os.path.join(ROOT,'tests','hands_v2_export_roundtrip.json'),'w') as f:json.dump(report,f,indent=2)
    print('Hand export verified',report['pass'],'joints',len(checks),'nails',len(nails),'maps',report['textures'])
finally:
    bpy.context.window.scene=main
    for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.scenes.remove(qa)
