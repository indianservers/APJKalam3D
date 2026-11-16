import bpy,bmesh,json,os,math
ROOT=r'C:\Abdul Kalam';r=bpy.data.objects['Armature']
hands={s:bpy.data.objects['APJ_Hand_'+s] for s in ['Left','Right']}
fingers=['Thumb','Index','Middle','Ring','Pinky']
def reset():
    for b in r.pose.bones:b.matrix_basis.identity()
    bpy.context.view_layer.update()
def co(o):
    bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    a=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();return a
reset();base={s:co(o) for s,o in hands.items()};checks=[];topology={}
for side,hand in hands.items():
    bm=bmesh.new();bm.from_mesh(hand.data)
    topology[side]={'vertices':len(bm.verts),'faces':len(bm.faces),'quads':sum(len(f.verts)==4 for f in bm.faces),
        'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
    bm.free();sums=[sum(g.weight for g in v.groups) for v in hand.data.vertices]
    topology[side]['unweighted_vertices']=sum(v<1e-6 for v in sums)
    topology[side]['max_weight_sum_error']=max(abs(s-1) for s in sums)
    for f in fingers:
        nail=bpy.data.objects[f'APJ_Nail_{side}_{f}'];nbase=co(nail)
        for j in range(1,4):
            reset();b=r.pose.bones[f'{side}Hand{f}{j}'];b.rotation_mode='XYZ';b.rotation_euler.z=.45 if side=='Left' else -.45
            moved=co(hand);delta=max((a-c).length for a,c in zip(base[side],moved))
            naildelta=max((a-c).length for a,c in zip(nbase,co(nail)))
            other='Right' if side=='Left' else 'Left';leak=max((a-c).length for a,c in zip(base[other],co(hands[other])))
            checks.append({'bone':b.name,'hand_vertex_displacement_m':delta,'nail_displacement_m':naildelta,'opposite_hand_displacement_m':leak,
                'pass':delta>1e-5 and naildelta>1e-5 and leak<1e-7})
reset()
report={'hands':2,'fingers':10,'nail_plates':len([o for o in bpy.data.objects if o.name.startswith('APJ_Nail_')]),
 'topology':topology,'joint_tests':checks,'all_pass':all(t['pass'] for t in checks) and all(t['nonmanifold_edges']==0 and t['unweighted_vertices']==0 for t in topology.values()),
 'scope':'Independent deformation, nail attachment, weights and mesh health. Not anatomical or photorealism certification.',
 'limitations':['Wrist join is concealed inside cuff, not welded to the body mesh','Reconstructed hand anatomy needs artist review for final production','No captured finger-motion validation']}
with open(os.path.join(ROOT,'tests','hands_v2_validation.json'),'w') as f:json.dump(report,f,indent=2)
print('Hands v2 validation',report['all_pass'],'joint checks',len(checks),'topology',topology)
