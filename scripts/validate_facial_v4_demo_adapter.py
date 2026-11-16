import bpy,json,sys,os,math
ROOT=r'C:\Abdul Kalam';sys.path.insert(0,os.path.join(ROOT,'scripts'))
c=bpy.data.objects['APJ_Face_Controls'];face=bpy.data.objects['APJ_Face'];rig=bpy.data.objects['Armature'];s=bpy.context.scene
previous=c.animation_data.action if c.animation_data else None;frame=s.frame_current
c.animation_data_create();c.animation_data.action=bpy.data.actions['APJ_Facial_v4_Demonstration']
with open(os.path.join(ROOT,'tests','facial_v4_demo_poses.json')) as f:poses=json.load(f)
checks=[]
for pose in poses:
    s.frame_set(pose['frame']);bpy.context.view_layer.update()
    errors={name:abs(float(c[name])-value) for name,value in pose['controls'].items()}
    checks.append({'frame':pose['frame'],'label':pose['label'],'max_control_error':max(errors.values(),default=0),'pass':max(errors.values(),default=0)<1e-5})
from facial_v4_mediapipe import FaceCoefficientAdapter
adapter=FaceCoefficientAdapter();adapter.reset()
for _ in range(25):adapter.update({'jawOpen':.6,'browInnerUp':.5,'eyeLookOutLeft':.4},1/30)
s.frame_set(601);bpy.context.view_layer.update();response={'jawOpen':float(c['jawOpen']),'browInnerUp':float(c['browInnerUp']),'eyeLookOutLeft':float(c['eyeLookOutLeft'])}
for _ in range(50):adapter.update({},1/30,confidence=0.)
loss=max(abs(v) for v in adapter.state.values());adapter.reset();adapter.update({'jawOpen':float('nan'),'eyeBlinkLeft':float('inf'),'unknown':100},1/30)
invalid=max(abs(v) for v in adapter.state.values());adapter.stop(restore_action=False)
report={'input_source':'Synthetic coefficient dictionaries; no camera or MediaPipe inference tested','demo_frames':checks,'smoothed_response':response,'tracking_loss_max_value':loss,'nonfinite_input_max_value':invalid,
 'pass':all(p['pass'] for p in checks) and abs(response['jawOpen']-.6)<1e-4 and abs(response['browInnerUp']-.5)<1e-4 and loss<1e-6 and invalid==0.}
with open(os.path.join(ROOT,'tests','facial_v4_demo_adapter.json'),'w') as f:json.dump(report,f,indent=2)
c.animation_data.action=previous;s.frame_set(frame)
print('Demo/adapter checks passed:',report['pass'],'demo poses:',len(checks))
