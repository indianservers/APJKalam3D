"""Run in Blender after importing and applying transforms to the supplied FBX.
Creates a development rig, not a production facial reconstruction.
"""
import bpy, bmesh, math, json, os
from mathutils import Vector

ROOT = r'C:\Abdul Kalam'
m = bpy.data.objects['char1']
r = bpy.data.objects['Armature']
if r.get('apj_upgrade'):
    raise RuntimeError('Upgrade already applied; reopen apj_working.blend to rebuild')
bm = bmesh.new(); bm.from_mesh(m.data)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.000001)
bm.to_mesh(m.data); bm.free(); m.data.update()
for p in m.data.polygons: p.use_smooth = True

# Landmarks fitted to the source hands in world metres. Mirrored right hand
# remains a reconstruction; both sides require close-up deformation review.
guides = {
    'Thumb': [(0.578,-.009,1.301),(.608,-.028,1.299),(.632,-.039,1.296),(.650,-.045,1.294)],
    'Index': [(.624,-.017,1.306),(.659,-.020,1.302),(.689,-.019,1.298),(.712,-.018,1.298)],
    'Middle':[(.625,.006,1.307),(.665,.005,1.302),(.695,.004,1.296),(.715,.003,1.296)],
    'Ring':[(.619,.029,1.306),(.655,.028,1.302),(.685,.027,1.296),(.707,.026,1.295)],
    'Pinky':[(.611,.049,1.305),(.642,.048,1.302),(.673,.044,1.297),(.691,.041,1.295)]}
bpy.ops.object.select_all(action='DESELECT'); r.select_set(True)
bpy.context.view_layer.objects.active=r
bpy.ops.object.mode_set(mode='EDIT')
root=r.data.edit_bones.new('Root'); root.head=(0,0,0); root.tail=(0,0,.15); root.use_deform=False
r.data.edit_bones['Hips'].parent=root
segments=[]
for side,sign in [('Left',1),('Right',-1)]:
    for finger,points in guides.items():
        points=[Vector((sign*x,y,z)) for x,y,z in points]
        parent=r.data.edit_bones[side+'Hand']
        for j in range(3):
            name=f'{side}Hand{finger}{j+1}'
            b=r.data.edit_bones.new(name); b.head=points[j]; b.tail=points[j+1]
            b.parent=parent; b.use_connect=(j>0)
            b.align_roll(Vector((0,1,0))); parent=b
            segments.append((name,side,finger,j,points[j],points[j+1]))
    # Optional leg IK: disabled by default to retain direct FK / tracking control.
    foot=r.data.edit_bones[side+'Foot']; knee=r.data.edit_bones[side+'Leg']
    ik=r.data.edit_bones.new(side+'Foot_IK'); ik.head=foot.head; ik.tail=foot.head+Vector((0,-.12,0)); ik.use_deform=False; ik.parent=root
    pole=r.data.edit_bones.new(side+'Knee_Pole'); pole.head=knee.head+Vector((0,-.45,0)); pole.tail=pole.head+Vector((0,0,.12)); pole.use_deform=False; pole.parent=root
bpy.ops.object.mode_set(mode='OBJECT')
for side in ['Left','Right']:
    con=r.pose.bones[side+'Leg'].constraints.new('IK');con.name='Optional foot IK (enable after pole calibration)'
    con.target=r;con.subtarget=side+'Foot_IK';con.pole_target=r;con.pole_subtarget=side+'Knee_Pole';con.chain_count=2;con.influence=0

def nearest(p,a,b):
    t=max(0,min(1,(p-a).dot(b-a)/(b-a).length_squared))
    return (p-(a+t*(b-a))).length,t

groups={name:m.vertex_groups.new(name=name) for name,*_ in segments}
assigned={name:0 for name in groups}
for v in m.data.vertices:
    p=v.co; x=abs(p.x)
    if not (1.26<p.z<1.34 and x>.574): continue
    side='Left' if p.x>0 else 'Right'
    options=[(nearest(p,a,b)[0],name,finger,j,a,b) for name,s,finger,j,a,b in segments if s==side]
    distance,name,finger,j,a,b=min(options,key=lambda it:it[0])
    # Preserve wrist and central palm. Blend the proximal attachment.
    start=.575 if finger=='Thumb' and p.y<-.014 else .611
    if finger=='Thumb' and p.y>=-.014: continue
    strength=max(0,min(1,(x-start)/.018))
    if strength==0 or distance>.030: continue
    # Smooth along the three phalanges, keeping neighbouring fingers separate.
    candidates=[]
    for n,s,f,k,aa,bb in segments:
        if s==side and f==finger:
            d,t=nearest(p,aa,bb)
            center=(aa+bb)*.5
            along=max(.000001, math.exp(-((p-center).length/.020)**2))
            candidates.append((n,along))
    total=sum(w for _,w in candidates)
    old=[(g.group,g.weight) for g in v.groups]
    for gi,w in old: m.vertex_groups[gi].add([v.index],w*(1-strength),'REPLACE')
    for n,w in candidates:
        weight=strength*w/total
        groups[n].add([v.index],weight,'REPLACE')
        if weight>.01: assigned[n]+=1

# Normalize all deformation weights; tiny source weights can exceed glTF's
# default four influences, so the export explicitly retains all influences.
for v in m.data.vertices:
    total=sum(g.weight for g in v.groups)
    if total>0:
        for g in list(v.groups):m.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')

# Closed-mouth facial prototypes. No empty keys pretending to support speech.
def gauss(x,c,s):return math.exp(-((x-c)/s)**2)
def front(y):return max(0,min(1,(-y-.045)/.035))
m.shape_key_add(name='Basis')
shape_counts={}
for name,side,kind in [('browInnerUp',0,'inner'),('browOuterUpLeft',1,'outer'),('browOuterUpRight',-1,'outer'),('browDownLeft',1,'down'),('browDownRight',-1,'down'),('mouthSmileLeft',1,'smile'),('mouthSmileRight',-1,'smile')]:
    key=m.shape_key_add(name=name);count=0
    for v,d in zip(m.data.vertices,key.data):
        x,y,z=v.co;mask=front(y)
        if kind=='inner':w=mask*gauss(x,0,.030)*gauss(z,1.542,.027);delta=Vector((0,-.001*w,.006*w))
        elif kind in ('outer','down'):
            w=mask*gauss(x,side*.042,.024)*gauss(z,1.54,.019)
            delta=Vector((-side*.002*w if kind=='down' else 0,0,(-.005 if kind=='down' else .006)*w))
        else:
            w=mask*gauss(x,side*.032,.020)*gauss(z,1.451,.019)
            delta=Vector((side*.003*w,-.001*w,.004*w))
        d.co=v.co+delta
        if delta.length>1e-5:count+=1
    shape_counts[name]=count

# Dynamic forehead detail is masked in object coordinates, isolated from suit.
mat=m.data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links
bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
geo=nodes.new('ShaderNodeTexCoord');geo.label='Object-space forehead mask'
sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Object'],sep.inputs[0])
def mathnode(op,a=None,b=None):
    n=nodes.new('ShaderNodeMath');n.operation=op
    for idx,value in enumerate([a,b]):
        if value is None:continue
        if isinstance(value,(int,float)):n.inputs[idx].default_value=value
        else:links.new(value,n.inputs[idx])
    return n.outputs[0]
mask=mathnode('MULTIPLY',mathnode('GREATER_THAN',sep.outputs['Z'],1.545),mathnode('LESS_THAN',sep.outputs['Z'],1.592))
mask=mathnode('MULTIPLY',mask,mathnode('LESS_THAN',sep.outputs['Y'],-.075))
mask=mathnode('MULTIPLY',mask,mathnode('LESS_THAN',mathnode('ABSOLUTE',sep.outputs['X']),.057))
wave=mathnode('SINE',mathnode('MULTIPLY',sep.outputs['Z'],580))
height=mathnode('MULTIPLY',wave,mask)
bump=nodes.new('ShaderNodeBump');bump.label='Development forehead wrinkle response';bump.inputs['Distance'].default_value=.00018
links.new(height,bump.inputs['Height']);links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
driver=bump.inputs['Strength'].driver_add('default_value').driver
for varname,keyname in [('a','browInnerUp'),('b','browOuterUpLeft'),('c','browOuterUpRight')]:
    var=driver.variables.new();var.name=varname;var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=m.data.shape_keys;var.targets[0].data_path=f'key_blocks["{keyname}"].value'
driver.expression='.12+.65*max(a,b,c)'
r.show_in_front=True;r['apj_upgrade']=True;r['status']='Development rig; facial reconstruction outstanding'
m['facial_status']='7 closed-mouth prototypes; eyes and mouth interior require reconstruction'
report={'finger_weighted_vertices':assigned,'prototype_shape_affected_vertices':shape_counts,'bones':len(r.data.bones),'vertices_after_weld':len(m.data.vertices),'triangles':len(m.data.polygons),'production_ready':False}
with open(os.path.join(ROOT,'tests','build_report.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
