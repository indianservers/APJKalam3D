"""Reference-driven smile calibration and relaxed lip closure."""
import bpy,json,math,os
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';face=bpy.data.objects['APJ_Face'];ctrl=bpy.data.objects['APJ_Face_Controls'];keys=face.data.shape_keys;mz=face['mouth_center_z']
def g(x,c,w):return math.exp(-((x-c)/w)**2)
smile=face.shape_key_add(name='CORR_ReferenceSmileLips',from_mix=False)
seal=face.shape_key_add(name='CORR_NeutralLipSeal',from_mix=False)
for i,point in enumerate(keys.key_blocks['Basis'].data):
    p=point.co;x,y,z=p;central=g(x,0,.030);upper=max(0,min(1,(z-mz+.00025)/.0010));lower=max(0,min(1,(mz-z+.00025)/.0010))
    rise=.0023*g(z,mz+.002,.005)*upper;drop=.0025*g(z,mz-.002,.005)*lower
    smile.data[i].co=p+Vector((0,-.0005*central*g(z,mz,.008),(rise-drop)*central))
    close=(mz-z)*g(x,0,.032)*g(z,mz,.0025)*.90
    seal.data[i].co=p+Vector((0,0,close))
def driver(key,variables,expr):
    d=key.driver_add('value').driver
    for name,prop in variables.items():
        v=d.variables.new();v.name=name;v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["'+prop+'"]'
    d.expression=expr
driver(smile,{'l':'mouthSmileLeft','r':'mouthSmileRight'},'(l+r)*.5')
driver(seal,{'j':'jawOpen','l':'mouthSmileLeft','r':'mouthSmileRight','p':'mouthPucker','f':'mouthFunnel','u':'mouthUpperUpLeft','v':'mouthUpperUpRight','d':'mouthLowerDownLeft','e':'mouthLowerDownRight'},'max(0,1-max(4*j,l,r,p,f,u,v,d,e))')
underlay=bpy.data.objects.get('APJ_v5_Skin_Transition_Underlay')
if underlay:
    for source in [smile,seal]:
        key=underlay.shape_key_add(name=source.name,from_mix=False)
        for i,p in enumerate(underlay.data.shape_keys.key_blocks['Basis'].data):key.data[i].co=p.co+source.data[i].co-keys.key_blocks['Basis'].data[i].co
        d=key.driver_add('value').driver;v=d.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=keys;v.targets[0].data_path='key_blocks["'+source.name+'"].value';d.expression='v'
for o in bpy.data.objects:
    if o.name.startswith('APJ_Teeth_Upper_') or o.name=='APJ_Gum_Upper':o.location.z+=.0010
with open(os.path.join(ROOT,'tests','sculpt_v5_landmarks.json')) as f:data=json.load(f)
scores=data['reference']['coefficients'];channels=json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']
pose={name:float(scores.get(name,0.)) for name in channels}
face['reference_pose_v5']=json.dumps(pose);face['sculpt_correctives_v5']=json.dumps([smile.name,seal.name])
for name in channels:ctrl[name]=pose[name]
ctrl.update_tag();keys.update_tag();bpy.context.scene.frame_set(1)
print('Reference expression inferred from image; smile lip opening calibrated')
