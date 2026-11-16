"""Concealed skin backing and fitted reference smile for sculpt review."""
import bpy,json,math
from mathutils import Vector
face=bpy.data.objects['APJ_Face'];rig=bpy.data.objects['Armature'];scene=bpy.context.scene
underlay=face.copy();underlay.data=face.data.copy();underlay.name='APJ_v5_Skin_Transition_Underlay';scene.collection.objects.link(underlay)
for modifier in list(underlay.modifiers):
    if modifier.type=='SHRINKWRAP':underlay.modifiers.remove(modifier)
def width(z):
    import numpy as np
    return float(np.interp(z,[1.407,1.425,1.45,1.49,1.525,1.555,1.595],[.039,.058,.077,.085,.081,.071,.061]))
offsets=[]
for point in underlay.data.shape_keys.key_blocks['Basis'].data:
    x,y,z=point.co;r=abs(x)/width(z);edge=max(0,min(1,(r-.72)/.24))
    dz=-.002*max(0,min(1,(1.435-z)/.015))+.0015*max(0,min(1,(z-1.580)/.015))
    offsets.append(Vector((math.copysign(.004*edge,x),.0035,dz)))
for key in underlay.data.shape_keys.key_blocks:
    for point,delta in zip(key.data,offsets):point.co+=delta
underlay['purpose']='Concealed overlap backing for transition cracks; not a welded head surface'
# Fit the upper incisor/gum position to the revised lip volume.
for o in bpy.data.objects:
    if o.name.startswith('APJ_Teeth_Upper_') or o.name=='APJ_Gum_Upper':o.location.y-=.0015;o.location.z+=.0015
pose={'jawOpen':.27,'mouthSmileLeft':.90,'mouthSmileRight':.92,'cheekSquintLeft':.28,'cheekSquintRight':.28,
      'mouthUpperUpLeft':.24,'mouthUpperUpRight':.24,'mouthStretchLeft':.12,'mouthStretchRight':.12,'mouthDimpleLeft':.12,'mouthDimpleRight':.12}
face['reference_pose_v5']=json.dumps(pose)
ctrl=bpy.data.objects['APJ_Face_Controls']
for name in json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']:ctrl[name]=float(pose.get(name,0.))
ctrl.update_tag();face.data.shape_keys.update_tag();scene.frame_set(1)
print('Reference smile fitted; concealed transition backing installed')
