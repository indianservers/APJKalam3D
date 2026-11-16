"""Refit closure/contact and jaw masks after the reference sculpt."""
import bpy,json,math
from mathutils import Vector,Matrix
face=bpy.data.objects['APJ_Face'];keys=face.data.shape_keys;ctrl=bpy.data.objects['APJ_Face_Controls'];eyes=json.loads(face['eye_info']);tags={n:set(ids) for n,ids in json.loads(face['boundary_tags']).items()}
pose=json.loads(face['reference_pose_v5'])
for prop in json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']:ctrl[prop]=0.
ctrl.update_tag();keys.update_tag();bpy.context.scene.frame_set(1)
base=[p.co.copy() for p in keys.key_blocks['Basis'].data];mz=face['mouth_center_z']
def width(z):
    import numpy as np
    return float(np.interp(z,[1.407,1.425,1.45,1.49,1.525,1.555,1.595],[.039,.058,.077,.085,.081,.071,.061]))
def g(x,c,w):return math.exp(-((x-c)/w)**2)
for side,h in eyes.items():
    for kind,name in [('blink','eyeBlink'+side),('wide','eyeWide'+side),('squint','eyeSquint'+side)]:
        for i,(p,dst) in enumerate(zip(base,keys.key_blocks[name].data)):
            dx=p.x-h['x'];dz=p.z-h['z'];r=math.sqrt((dx/h['rx'])**2+(dz/.0045)**2);delta=Vector()
            if r<3.5:
                margin=i in tags[side];w=1 if margin else min(.86,math.exp(-(max(0,r-1)/.72)**2))
                z=p.z+(.0019 if dz>=0 else -.0009)*w if kind=='wide' else p.z+(h['z']+.00025*(dx/h['rx'])*(1 if side=='Left' else -1)-p.z)*w
                disc=(h['radius']+.00014)**2-dx*dx-(z-h['z'])**2;y=p.y
                if disc>0:
                    contact=h['cy']-math.sqrt(disc)-.0012;y=contact if margin else min(p.y,contact)
                delta=Vector((0,y-p.y,z-p.z))*(.42 if kind=='squint' else 1)
            dst.co=p+delta
hinge=Vector((0,.005,1.471));rot=Matrix.Rotation(.20,3,'X')
for i,p in enumerate(base):
    w=max(0,min(1,(mz+.00025-p.z)/.0008))*max(0,min(1,(p.z-1.416)/.018))*max(0,min(1,(1-abs(p.x)/width(p.z))/.12))
    delta=(hinge+rot@(p-hinge)-p)*w
    keys.key_blocks['jawOpen'].data[i].co=p+delta
    keys.key_blocks['jawLeft'].data[i].co=p+Vector((.003*w,0,0));keys.key_blocks['jawRight'].data[i].co=p+Vector((-.003*w,0,0));keys.key_blocks['jawForward'].data[i].co=p+Vector((0,-.003*w,0))
    keys.key_blocks['mouthClose'].data[i].co=p-delta*g(p.z,mz-.002,.010)*g(p.x,0,.037)
    keys.key_blocks['CORR_NeutralLipSeal'].data[i].co=p+Vector((0,0,(mz-p.z)*g(p.x,0,.032)*g(p.z,mz,.0025)*.9))
underlay=bpy.data.objects.get('APJ_v5_Skin_Transition_Underlay')
if underlay:
    b=underlay.data.shape_keys.key_blocks['Basis']
    for source in list(keys.key_blocks)[1:]:
        target=underlay.data.shape_keys.key_blocks[source.name]
        for i,p in enumerate(b.data):target.data[i].co=p.co+source.data[i].co-base[i]
    underlay.data.shape_keys.update_tag()
for prop,value in pose.items():ctrl[prop]=float(value)
ctrl.update_tag();keys.update_tag();bpy.context.scene.frame_set(1)
print('Post-sculpt facial rig refitted')
