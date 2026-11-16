import bpy,json,math,os
import numpy as np
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';data=json.load(open(os.path.join(ROOT,'tests','sculpt_v5_fit_field.json')))
C=np.array(data['centres']);W=np.array(data['weights']);sigma=data['sigma']
def field(points):
    p=np.array([(v.x,v.z) for v in points],dtype=np.float64);outputs=[]
    for start in range(0,len(p),2048):
        part=p[start:start+2048];d=((part[:,None,:]-C[None,:,:])**2).sum(2);result=np.exp(-d/(2*sigma*sigma))@W
        length=np.linalg.norm(result,axis=1);result*=np.minimum(1,.004/np.maximum(length,1e-9))[:,None]
        mask=np.ones(len(part))
        for x in [-.0345,.0347]:mask*=1-.98*np.exp(-((part[:,0]-x)/.014)**2-((part[:,1]-1.5148)/.014)**2)
        mask*=np.clip((part[:,1]-1.390)/.020,0,1)
        result*=mask[:,None];outputs.extend([Vector((x,0,z)) for x,z in result])
    return outputs
face=bpy.data.objects['APJ_Face'];ctrl=bpy.data.objects['APJ_Face_Controls'];pose=json.loads(face['reference_pose_v5'])
if ctrl.animation_data:ctrl.animation_data.action=None
for prop in json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']:ctrl[prop]=0.
ctrl.update_tag();face.data.shape_keys.update_tag();bpy.context.scene.frame_set(1)
mouth_delta=field([Vector((0,0,face['mouth_center_z']))])[0]
stats={}
for name in ['APJ_Face','char1','APJ_v5_Skin_Transition_Underlay']:
    obj=bpy.data.objects.get(name)
    if not obj:continue
    base=obj.data.shape_keys.key_blocks['Basis'];delta=field([p.co.copy() for p in base.data])
    for key in obj.data.shape_keys.key_blocks:
        for p,d in zip(key.data,delta):p.co+=d
    obj.data.shape_keys.update_tag();stats[name]=max(d.length for d in delta)
face['mouth_center_z']+=mouth_delta.z
# Transport visible mouth structures through the same field at neutral pose.
for obj in bpy.data.objects:
    if not (obj.type=='MESH' and (obj.name.startswith('APJ_Teeth_') or obj.name.startswith('APJ_Gum_') or obj.name in ['APJ_Tongue','APJ_Mouth_Interior'])):continue
    matrix=obj.matrix_world.copy();inv=matrix.inverted().to_3x3();world=[matrix@v.co for v in obj.data.vertices];delta=field(world)
    for v,d in zip(obj.data.vertices,delta):v.co+=inv@d
    obj.data.update()
hair=bpy.data.objects.get('APJ_v3_Fine_Hair_Strands')
if hair:
    matrix=hair.matrix_world.copy();inverse=matrix.inverted().to_3x3()
    for spline in hair.data.splines:
        points=[matrix@Vector(p.co[:3]) for p in spline.points];delta=field(points)
        for point,d in zip(spline.points,delta):
            q=Vector(point.co[:3])+inverse@d;point.co=(*q,1)
face['landmark_sculpt_v5']=True
for prop,value in pose.items():ctrl[prop]=float(value)
# Blendshape predictor amplitudes are calibrated to this reconstructed rig.
for prop in ['eyeBlinkLeft','eyeBlinkRight']:ctrl[prop]*=.45
for prop in ['eyeSquintLeft','eyeSquintRight']:ctrl[prop]*=.50
for prop in ['browDownLeft','browDownRight']:ctrl[prop]*=.35
pose={prop:float(ctrl[prop]) for prop in pose};face['reference_pose_v5']=json.dumps(pose)
ctrl.update_tag();face.data.shape_keys.update_tag();bpy.context.scene.frame_set(1)
print('Landmark-guided sculpt transported to face, retained head, hair and mouth:',stats)
