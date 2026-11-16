"""Reimport exported GLB in an isolated scene; verify deformation survives."""
import bpy,json,os
ROOT=r'C:\Abdul Kalam'
main=bpy.context.scene;qa=bpy.data.scenes.new('APJ Export QA');bpy.context.window.scene=qa
before=set(bpy.data.objects)
try:
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT,'exports','apj_development.glb'))
    imported=set(bpy.data.objects)-before
    m=next(o for o in imported if o.type=='MESH' and o.data.shape_keys)
    r=next(o for o in imported if o.type=='ARMATURE')
    def coordinates():
        bpy.context.view_layer.update()
        ev=m.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        result=[v.co.copy() for v in mesh.vertices];ev.to_mesh_clear();return result
    qa.frame_set(1);base=coordinates();qa.frame_set(5)
    animation_delta=max((a-b).length for a,b in zip(base,coordinates()))
    if r.animation_data:r.animation_data_clear()
    if m.data.shape_keys.animation_data:m.data.shape_keys.animation_data_clear()
    for b in r.pose.bones:b.matrix_basis.identity()
    for k in m.data.shape_keys.key_blocks:k.value=0
    base=coordinates();checks=[]
    for k in list(m.data.shape_keys.key_blocks)[1:]:
        k.value=1;delta=max((a-b).length for a,b in zip(base,coordinates()));k.value=0
        checks.append({'morph':k.name,'displacement_m':delta,'pass':delta>1e-5})
    for b in r.pose.bones:
        if not any(f in b.name for f in ['HandThumb','HandIndex','HandMiddle','HandRing','HandPinky']):continue
        b.rotation_mode='XYZ';b.rotation_euler.z=.35
        delta=max((a-c).length for a,c in zip(base,coordinates()));b.matrix_basis.identity()
        checks.append({'joint':b.name,'displacement_m':delta,'pass':delta>1e-5})
    report={'bones':len(r.data.bones),'morph_targets':len(m.data.shape_keys.key_blocks)-1,'animation_displacement_m':animation_delta,
            'checks':checks,'pass':len(r.data.bones)==59 and len(checks)==37 and all(c['pass'] for c in checks) and animation_delta>1e-5,
            'wrinkle_shader_exported':False,'production_quality_certified':False}
    with open(os.path.join(ROOT,'tests','export_roundtrip.json'),'w') as f:json.dump(report,f,indent=2)
    print('GLB roundtrip:',report['pass'],'individual deformation checks:',len(checks))
finally:
    bpy.context.window.scene=main
    for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.scenes.remove(qa)
