import bpy,os,json,math,sys
from mathutils import Vector
ROOT=r'C:\Abdul Kalam'
r=bpy.data.objects['Armature'];m=bpy.data.objects['char1'];scene=bpy.context.scene
for b in r.pose.bones:b.matrix_basis.identity()
for key in m.data.shape_keys.key_blocks:key.value=0

# Reproducible independent-joint demonstration, one pulse per joint.
r.animation_data_create();action=bpy.data.actions.new('APJ_Independent_Joint_And_Body_Test');r.animation_data.action=action
fingerbones=[b for b in r.pose.bones if any(f in b.name for f in ['HandThumb','HandIndex','HandMiddle','HandRing','HandPinky'])]
for i,b in enumerate(fingerbones):
    b.rotation_mode='XYZ'
    for frame,value in [(1,0),(2+i*8,0),(5+i*8,.55 if b.name.startswith('Left') else -.55),(9+i*8,0),(360,0)]:
        b.rotation_euler.z=value;b.keyframe_insert(data_path='rotation_euler',frame=frame,group=b.name)
for i,name in enumerate(['LeftArm','RightArm','Head','LeftForeArm','RightForeArm','LeftLeg','RightLeg']):
    b=r.pose.bones[name];b.rotation_mode='XYZ';axis=1 if name=='Head' else 2
    for frame,value in [(1,0),(245+i*14,0),(251+i*14,.40),(258+i*14,0),(360,0)]:
        b.rotation_euler[axis]=value;b.keyframe_insert(data_path='rotation_euler',frame=frame,group=name)
keys=m.data.shape_keys;keys.animation_data_create();fa=bpy.data.actions.new('APJ_Prototype_Face_Test');keys.animation_data.action=fa
for i,k in enumerate(list(keys.key_blocks)[1:]):
    for frame,value in [(1,0),(2+i*45,0),(20+i*45,1),(42+i*45,0),(360,0)]:
        k.value=value;k.keyframe_insert(data_path='value',frame=frame)
scene.frame_start=1;scene.frame_end=360;scene.render.fps=30;scene.frame_set(1)

# Export material keeps original base color and roughness. Node wrinkles remain
# Blender-only; dynamic bump is deliberately not represented as a glTF feature.
mapping={'status':'partial development mapping; not full Face Landmarker compatibility',
 'coefficients':{k.name:{'shape_key':k.name,'status':'prototype, visual approval required'} for k in list(keys.key_blocks)[1:]},
 'unsupported':'All other coefficients, including blink, gaze, jaw and lip speech controls',
 'body':'motion_retargeting.BODY','hands':'motion_retargeting.HAND',
 'limitations':['calibration required','swing-only landmarks cannot infer twist','no tested camera input','wrinkle shader does not export']}
with open(os.path.join(ROOT,'mocap','mediapipe_mapping.json'),'w') as f:json.dump(mapping,f,indent=2)

sys.path.insert(0,os.path.join(ROOT,'scripts'))
from motion_retargeting import Retargeter
# Synthetic direction calibration and recovery, independent of any webcam.
ret=Retargeter(r,m)
body=[(0,0,0)]*33
body[11]=(0,0,0);body[13]=(1,0,0);body[15]=(2,0,0)
body[12]=(0,0,0);body[14]=(-1,0,0);body[16]=(-2,0,0)
body[23]=(.2,1,0);body[25]=(.2,2,0);body[27]=(.2,3,0)
body[24]=(-.2,1,0);body[26]=(-.2,2,0);body[28]=(-.2,3,0)
calibrated=ret.calibrate(body=body)
sample=list(body);sample[13]=(.6,-.8,0);sample[15]=(1.2,-1.6,0)
for _ in range(30):ret.update(1/30,body=sample,coefficients={'browInnerUp':1})
angle=r.pose.bones['LeftArm'].rotation_quaternion.angle
face=keys.key_blocks['browInnerUp'].value
for _ in range(60):ret.update(1/30,confidence=0)
recovery=r.pose.bones['LeftArm'].rotation_quaternion.angle
with open(os.path.join(ROOT,'tests','retargeting.json'),'w') as f:json.dump({'source':'synthetic landmarks, no webcam','calibrated_bones':calibrated,'arm_rotation_radians':angle,'face_response':face,'loss_recovery_radians':recovery,'pass':angle>.1 and face>.9 and recovery<.01},f,indent=2)
ret.reset();scene.frame_set(1)

# Restore XYZ modes used by the authored demo after quaternion retarget tests.
for b in r.pose.bones:b.rotation_mode='XYZ'
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');r.select_set(True);m.select_set(True);bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'exports','apj_development.glb'),use_selection=True,export_apply=False,export_animations=True,export_animation_mode='ACTIVE_ACTIONS',export_all_influences=True)

# Studio: soft area lights, dark blue background, metres.
scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.055,.07,.10,1);bg.inputs['Strength'].default_value=.3
def area(name,location,power,size,color):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=location;o.rotation_euler=(Vector((0,0,1.1))-o.location).to_track_quat('-Z','Y').to_euler()
area('Studio_Key',(-2,-3,3.5),350,2.3,(1,.86,.74))
area('Studio_Fill',(2,-1.5,2.0),180,2,(.75,.85,1))
area('Studio_Rim',(0,1.7,2.8),400,1.5,(.88,.93,1))
cam=bpy.data.objects['QC_Camera'];cam.location=(2,-4,1.85);cam.rotation_euler=(Vector((0,0,.85))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.05
scene.camera=cam;scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(ROOT,'renders','development_full_body.png')
for i in bpy.data.images:
    if i.source=='FILE' and i.has_data and not i.packed_file:i.pack()
for filename in ['upgrade_character.py','validate_character.py','motion_retargeting.py','prepare_delivery.py']:
    bpy.data.texts.load(os.path.join(ROOT,'scripts',filename))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','apj_development_master.blend'))
print('Saved development master, animated GLB, mappings and synthetic retargeting test')
