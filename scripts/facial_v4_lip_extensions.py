"""Eight additional lip controls complete the non-gaze coefficient conversion."""
import bpy,math,json,os
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';face=bpy.data.objects['APJ_Face'];ctrl=bpy.data.objects['APJ_Face_Controls'];keys=face.data.shape_keys;mz=face['mouth_center_z']
extra=['mouthDimpleLeft','mouthDimpleRight','mouthLeft','mouthRight','mouthRollLower','mouthRollUpper','mouthShrugLower','mouthShrugUpper']
def g(x,c,w):return math.exp(-((x-c)/w)**2)
for name in extra:
    ctrl[name]=0.;ctrl.id_properties_ui(name).update(min=0.,max=1.,soft_min=0.,soft_max=1.)
    key=face.shape_key_add(name=name)
    for i,(v,dst) in enumerate(zip(keys.key_blocks['Basis'].data,key.data)):
        p=v.co;x,y,z=p;lip=g(x,0,.037)*g(z,mz,.010);delta=Vector()
        if name.startswith('mouthDimple'):
            side=1 if name.endswith('Left') else -1;w=g(x,side*.027,.013)*g(z,mz,.011);delta=Vector((-side*.0020*w,.0025*w,.0008*w))
        elif name in ['mouthLeft','mouthRight']:delta.x=(.004 if name=='mouthLeft' else -.004)*lip
        elif name=='mouthRollLower':
            w=lip*max(0,min(1,(mz-z+.0005)/.003));delta=Vector((0,.0025*w,.0011*w))
        elif name=='mouthRollUpper':
            w=lip*max(0,min(1,(z-mz+.0005)/.003));delta=Vector((0,.0025*w,-.0010*w))
        elif name=='mouthShrugLower':
            w=g(x,0,.029)*g(z,mz-.006,.009);delta=Vector((0,-.0011*w,.0032*w))
        elif name=='mouthShrugUpper':
            w=g(x,0,.029)*g(z,mz+.005,.008);delta=Vector((0,-.0008*w,.0027*w))
        dst.co=p+delta
    d=key.driver_add('value').driver;var=d.variables.new();var.name='v';var.type='SINGLE_PROP';var.targets[0].id=ctrl;var.targets[0].data_path='["'+name+'"]';d.expression='v'
names=json.loads(face['expression_channels'])+extra;face['expression_channels']=json.dumps(names)
gaze=[name for name in ctrl.keys() if name.startswith('eyeLook')]
mapping={'mesh':face.name,'controller':ctrl.name,'coefficients':{name:{'type':'shape_key','target':name,'property':name} for name in names},
 'joint_controls':{name:{'type':'eye_bone','property':name,'bone':'Eye.L' if name.endswith('Left') else 'Eye.R'} for name in gaze},
 'neutral':{'_neutral':{'type':'implicit_zero_pose','note':'No deformation target. Zero expression scores are the neutral pose; neutral score does not override simultaneous coefficients.'}},
 'official_source':'https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/mediapipe/tasks/python/vision/face_landmarker.py',
 'supported_non_neutral_coefficients':len(names)+len(gaze),'conversion_coverage_including_neutral':len(names)+len(gaze)+1,
 'status':'Conversion coverage tested synthetically; not live-capture or FACS anatomical certification',
 'left_right':'Subject anatomical sides; unmirror detector output upstream',
 'wrinkle_correctives':json.loads(face['wrinkle_correctives'])}
with open(os.path.join(ROOT,'mocap','facial_v4_mapping.json'),'w') as f:json.dump(mapping,f,indent=2)
counts={k.name:sum((a.co-b.co).length>1e-5 for a,b in zip(k.data,keys.key_blocks['Basis'].data)) for k in list(keys.key_blocks)[1:]}
with open(os.path.join(ROOT,'tests','facial_v4_build.json'),'w') as f:json.dump({'affected_vertices':counts,'expression_targets':len(names),'geometric_wrinkle_correctives':6,'total_shape_targets':len(keys.key_blocks)-1,'gaze_coefficients':len(gaze),'bones':len(bpy.data.objects['Armature'].data.bones)},f,indent=2)
print('Lip controls complete:',len(names),'expression shapes plus',len(gaze),'gaze coefficients and implicit neutral')
