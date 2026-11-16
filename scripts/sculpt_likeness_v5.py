"""Reference-guided geometric likeness pass, transferred through existing keys.
Single-image reconstruction; no claim of scan-accurate unseen depth.
"""
import bpy,math,json,os
import numpy as np
from mathutils import Vector,Matrix
ROOT=r'C:\Abdul Kalam';face=bpy.data.objects['APJ_Face'];body=bpy.data.objects['char1'];rig=bpy.data.objects['Armature'];ctrl=bpy.data.objects['APJ_Face_Controls'];scene=bpy.context.scene
if face.get('likeness_v5'):raise RuntimeError('Likeness sculpt already applied')
if ctrl.animation_data:ctrl.animation_data.action=None
channels=json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']
for name in channels:ctrl[name]=0.
ctrl.update_tag();face.data.shape_keys.update_tag();scene.frame_set(1);bpy.context.view_layer.update()
copy=face.copy();copy.data=face.data.copy();copy.name='SOURCE_Facial_v4_PreSculpt';scene.collection.objects.link(copy);copy.hide_set(True);copy.hide_render=True
keys=face.data.shape_keys;base=[v.co.copy() for v in keys.key_blocks['Basis'].data]
def g(x,c,w):return math.exp(-((x-c)/w)**2)
def width(z):return float(np.interp(z,[1.407,1.425,1.45,1.49,1.525,1.555,1.595],[.039,.058,.077,.085,.081,.071,.061]))
def edge(p):return max(0,min(1,(1-abs(p.x)/width(p.z))/.18))*max(0,min(1,(p.z-1.415)/.012))*max(0,min(1,(1.595-p.z)/.009))
eyes=json.loads(face['eye_info']);tags={name:set(ids) for name,ids in json.loads(face['boundary_tags']).items()}
deltas=[]
for index,p in enumerate(base):
    x,y,z=p;w=edge(p);d=Vector()
    # Taper the lower jaw/chin while retaining high cheek volume.
    d.x-=x*(.055*g(z,1.448,.024)+.040*g(z,1.428,.014))*g(abs(x),.052,.040)
    d.y-=.0026*g(abs(x),.050,.021)*g(z,1.487,.022)
    d.z+=.0008*g(abs(x),.046,.024)*g(z,1.481,.024)
    # Round the chin pad, soften the long lower-face appearance and labiomental crease.
    d.y-=.0011*g(x,0,.027)*g(z,1.430,.010)
    d.z+=.0012*g(x,0,.038)*g(z,1.429,.010)
    d.y+=.00045*g(x,0,.025)*g(z,1.438,.0018)
    # More rounded nasal tip, broader alar forms and a less sharp bridge.
    d.y-=.0016*g(x,0,.014)*g(z,1.476,.010)
    d.z+=.00045*g(x,0,.016)*g(z,1.476,.009)
    d.x+=math.copysign(.0010,x)*g(abs(x),.016,.010)*g(z,1.478,.011)
    d.y+=.00075*g(x,0,.010)*g(z,1.505,.016)
    # Relax the glabella and soften the inner brow ridge.
    d.y+=.0010*g(abs(x),.020,.018)*g(z,1.539,.014)
    d.z+=.0008*g(abs(x),.026,.021)*g(z,1.540,.014)
    d.y-=.0007*g(x,0,.046)*g(z,1.568,.020)
    # Subtle lip volume; smiling remains an expression rather than a baked statue.
    d.y-=.0008*g(x,0,.029)*g(z,1.449,.0030)
    d.y-=.0010*g(x,0,.027)*g(z,1.443,.0030)
    for side,h in eyes.items():
        dx=x-h['x'];dz=z-h['z'];mask=g(dx,0,.015)*g(dz,0,.010)
        d.x-=.025*dx*mask
        # Smaller mature aperture and softer under-eye bag volume.
        if index in tags[side]:d.z+=-.00060 if dz>=0 else .00035
        else:d.z+=(-.00035 if dz>=0 else .00022)*mask
        d.y+=.00055*g(dx,0,.014)*g(dz,-.008,.005)
    deltas.append(d*w)
# Transfer the same sculpt field into every existing target, preserving their deltas.
for key in keys.key_blocks:
    for point,delta in zip(key.data,deltas):point.co+=delta
face.data.update()

# Recess the eye globes slightly into the sculpted orbits.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for side,h in eyes.items():
    h['cy']+=.0011;bone=rig.data.edit_bones['Eye.'+side[0]];bone.head.y+=.0011;bone.tail.y+=.0011
bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
for side,h in eyes.items():
    for suffix in ['Globe','Cornea']:
        o=bpy.data.objects['APJ_Eye_'+side+'_'+suffix];matrix=o.matrix_world.copy();matrix.translation=Vector((h['x'],h['cy'],h['z']));o.matrix_world=matrix
face['eye_info']=json.dumps(eyes)

# Rebuild closure and jaw targets from the new neutral surface.
newbase=[v.co.copy() for v in keys.key_blocks['Basis'].data];mz=face['mouth_center_z']
for side,h in eyes.items():
    for kind,name in [('blink','eyeBlink'+side),('wide','eyeWide'+side),('squint','eyeSquint'+side)]:
        for i,(p,dst) in enumerate(zip(newbase,keys.key_blocks[name].data)):
            dx=p.x-h['x'];dz=p.z-h['z'];r=math.sqrt((dx/h['rx'])**2+(dz/.0045)**2);d=Vector()
            if r<3.5:
                margin=i in tags[side];w=1. if margin else min(.86,math.exp(-(max(0,r-1)/.72)**2))
                z=p.z+(.0019 if dz>=0 else -.0009)*w if kind=='wide' else p.z+(h['z']+.00025*(dx/h['rx'])*(1 if side=='Left' else -1)-p.z)*w
                disc=(h['radius']+.00014)**2-dx*dx-(z-h['z'])**2;y=p.y
                if disc>0:
                    contact=h['cy']-math.sqrt(disc)-.0012;y=contact if margin else min(p.y,contact)
                d=Vector((0,y-p.y,z-p.z))*(.42 if kind=='squint' else 1)
            dst.co=p+d
hinge=Vector((0,.005,1.471));rot=Matrix.Rotation(.20,3,'X')
for i,p in enumerate(newbase):
    w=max(0,min(1,(mz+.00025-p.z)/.0008))*max(0,min(1,(p.z-1.416)/.018))*max(0,min(1,(1-abs(p.x)/width(p.z))/.12))
    delta=(hinge+rot@(p-hinge)-p)*w
    keys.key_blocks['jawOpen'].data[i].co=p+delta
    keys.key_blocks['jawLeft'].data[i].co=p+Vector((.003*w,0,0));keys.key_blocks['jawRight'].data[i].co=p+Vector((-.003*w,0,0));keys.key_blocks['jawForward'].data[i].co=p+Vector((0,-.003*w,0))
    keys.key_blocks['mouthClose'].data[i].co=p-delta*g(p.z,mz-.002,.010)*g(p.x,0,.037)

# Retain the v4 overlap topology. A finer source cut was rejected in visual QA.

face['likeness_v5']=True
reference_pose={'jawOpen':.20,'mouthSmileLeft':.65,'mouthSmileRight':.70,'cheekSquintLeft':.18,'cheekSquintRight':.18,'mouthUpperUpLeft':.18,'mouthUpperUpRight':.18}
face['reference_pose_v5']=json.dumps(reference_pose)
report={'source':'Dr. Kalam’s Welcoming Wave.png','mode':'Reference-guided geometric sculpt; depth is artistic reconstruction',
 'sculpted_regions':['cheek volume','lower cheek and jaw taper','chin pad and labiomental form','nasal tip and alar width','bridge and glabella','brow ridge','lip volume','mature eyelid aperture','neck and cheek overlap transitions'],
 'maximum_basis_displacement_m':max(d.length for d in deltas),'vertices_changed':sum(d.length>1e-5 for d in deltas),
 'shape_targets_preserved':len(keys.key_blocks)-1,'eye_recess_m':.0011,'reference_pose':reference_pose,
 'limitations':['Single reference does not constrain unseen profile exactly','Not a scan-based likeness','Overlapping facial surface still needs production seam review']}
with open(os.path.join(ROOT,'tests','sculpt_v5.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2,ensure_ascii=False)
print(json.dumps(report,ensure_ascii=False))
