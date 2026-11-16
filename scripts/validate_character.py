"""Functional deformation tests, executed in Blender; visual QA remains required."""
import bpy,json,os,math
ROOT=r'C:\Abdul Kalam'
r=bpy.data.objects['Armature'];m=bpy.data.objects['char1']
def reset():
    if r.animation_data:r.animation_data.action=None
    if m.data.shape_keys.animation_data:m.data.shape_keys.animation_data.action=None
    for b in r.pose.bones:b.matrix_basis.identity()
    for k in m.data.shape_keys.key_blocks:k.value=0
    bpy.context.view_layer.update()
def vertices():
    bpy.context.view_layer.update()
    ev=m.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=ev.to_mesh();result=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();return result
reset();base=vertices();results=[]
names=[b.name for b in r.data.bones if any(f in b.name for f in ['HandThumb','HandIndex','HandMiddle','HandRing','HandPinky'])]
names+=['Head','neck','LeftArm','RightArm','LeftForeArm','RightForeArm','LeftUpLeg','RightUpLeg','LeftLeg','RightLeg']
for name in names:
    reset();b=r.pose.bones[name];b.rotation_mode='XYZ';b.rotation_euler.z=.35
    moved=vertices();d=[(a-c).length for a,c in zip(moved,base)]
    results.append({'control':name,'max_vertex_displacement_m':max(d),'moved_vertices':sum(x>1e-5 for x in d),'pass':max(d)>1e-5})
for k in m.data.shape_keys.key_blocks:
    if k.name=='Basis':continue
    reset();k.value=1.;moved=vertices();d=[(a-c).length for a,c in zip(moved,base)]
    results.append({'control':k.name,'max_vertex_displacement_m':max(d),'moved_vertices':sum(x>1e-5 for x in d),'pass':max(d)>1e-5})
reset()
mat=m.data.materials[0];bump=next(n for n in mat.node_tree.nodes if n.type=='BUMP')
def strength():
    m.data.shape_keys.update_tag();mat.node_tree.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update()
    return bump.inputs['Strength'].default_value
neutral=strength();m.data.shape_keys.key_blocks['browInnerUp'].value=1.;raised=strength();reset()
sums=[sum(g.weight for g in v.groups) for v in m.data.vertices]
report={'production_ready':False,'tests':results,'all_deformation_tests_pass':all(t['pass'] for t in results),
        'unweighted_vertices':sum(s<1e-6 for s in sums),'max_weight_sum_error':max(abs(s-1) for s in sums),
        'wrinkle_strength_neutral':neutral,'wrinkle_strength_raised':raised,'wrinkle_driver_pass':raised>neutral,
        'missing_textures':[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file and not os.path.exists(bpy.path.abspath(i.filepath))],
        'unsupported':['independent eyeballs','eyelid contact','speech / mouth interior','52 production facial targets','hair cards','anatomical corrective deformation','live webcam test'],
        'test_scope':'Evaluated vertex movement only; does not certify anatomical or visual quality'}
with open(os.path.join(ROOT,'tests','validation.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='tests'}))
