"""Deterministic full-body, seated, digit and confidence/recovery tests."""
import bpy,json,math
from mathutils import Vector,Quaternion
ROOT=r'C:\Abdul Kalam';state=bpy.app.driver_namespace.get('apj_capture');tracker=state['tracker'];r=tracker.rig
exec(compile(open(ROOT+'/scripts/capture_presets.py').read(),'capture_presets.py','exec'))
BODY=tracker.update.__globals__['BODY'];FINGERS=tracker.update.__globals__['FINGERS']
report={'production_ready':False,'live_camera_tested':False,'tests':{}}
def worldpoint(v):return {'x':float(v.x),'y':float(-v.z),'z':float(v.y),'visibility':1.}
def run(packet,n=35):
 for _ in range(n):tracker.update(packet,1/30)
def evaluated_bounds(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());pts=[ev.matrix_world@v.co for v in ev.data.vertices];return [[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)]
tracker.reset();neutral=evaluated_bounds(bpy.data.objects['char1']);run(pose_packet('standing'))
standing={'left_arm_down':list(r.pose.bones['LeftArm'].matrix.to_3x3()@Vector((0,1,0))),'right_arm_down':list(r.pose.bones['RightArm'].matrix.to_3x3()@Vector((0,1,0)))}
standing['pass']=standing['left_arm_down'][2]<-.85 and standing['right_arm_down'][2]<-.85;report['tests']['standing']=standing
tracker.reset();run(pose_packet('seated'));r.pose.bones['Root'].location.y=-.30;bpy.context.view_layer.update()
thigh=(r.pose.bones['LeftUpLeg'].tail-r.pose.bones['LeftUpLeg'].head).normalized();shin=(r.pose.bones['LeftLeg'].tail-r.pose.bones['LeftLeg'].head).normalized()
report['tests']['seated']={'thigh_direction':list(thigh),'shin_direction':list(shin),'hip_knee_angle_degrees':math.degrees(thigh.angle(shin)),'body_bounds':evaluated_bounds(bpy.data.objects['char1']),'pass':thigh.y<-.9 and shin.z<-.9}
for mode in ['open','fist']:
 tracker.reset();packet=pose_packet('standing');packet['hands']=[]
 for side,sign in [('Left',1),('Right',-1)]:
  points=[None]*21;points[0]=r.data.bones[side+'Hand'].head_local.copy()
  for finger,indices in FINGERS.items():
   current=r.data.bones[side+'Hand'+finger+'1'].head_local.copy();points[indices[0]]=current.copy()
   for j in range(3):
    b=r.data.bones[f'{side}Hand{finger}{j+1}'];d=b.tail_local-b.head_local
    if mode=='fist':d=Quaternion(Vector((0,sign,0)),math.radians(45+35*j))@d
    current=current+d;points[indices[j+1]]=current.copy()
  packet['hands'].append({'side':side,'confidence':1.,'world':[worldpoint(p) for p in points]})
 run(packet)
 moved={b.name:float(b.rotation_quaternion.angle) for b in r.pose.bones if 'Hand' in b.name and any(f in b.name for f in FINGERS)}
 report['tests']['digits_'+mode]={'joint_count':len(moved),'nonzero_joint_count':sum(abs(v)>.02 for v in moved.values()),'finite':all(math.isfinite(v) for v in moved.values()),'pass':len(moved)==30 and all(math.isfinite(v) for v in moved.values()) and (mode=='open' or all(abs(v)>.02 for v in moved.values()))}
report['tests']['confidence_recovery']={};run({},120)
maximum=max(r.pose.bones[n].rotation_quaternion.angle for n in BODY)
report['tests']['confidence_recovery']={'maximum_limb_rotation_radians':maximum,'pass':maximum<.002}
tracker.reset();report['tests']['neutral_reset']={'max_limb_angle':max(r.pose.bones[n].rotation_quaternion.angle for n in BODY),'pass':max(r.pose.bones[n].rotation_quaternion.angle for n in BODY)<1e-5}
packet=pose_packet('standing')
for i in [23,24,25,26,27,28]:packet['pose'][i]['visibility']=0.
for i,v in [(13,Vector((.30,-.02,1.32))),(15,Vector((.30,-.02,1.57))),(14,Vector((-.30,-.02,1.32))),(16,Vector((-.30,-.02,1.57)))]:packet['pose'][i]=worldpoint(v)
run(packet);bpy.context.view_layer.update();dots={}
for name in ['LeftArm','LeftForeArm','RightArm','RightForeArm']:
 a,b=BODY[name];expected=tracker.update.__globals__['vec'](packet['pose'][b])-tracker.update.__globals__['vec'](packet['pose'][a]);actual=r.pose.bones[name].tail-r.pose.bones[name].head;dots[name]=float(expected.normalized().dot(actual.normalized()))
report['tests']['arms_without_visible_hips']={'direction_dots':dots,'pass':min(dots.values())>.995}
tracker.reset()
report['all_pass']=all(t['pass'] for t in report['tests'].values())
json.dump(report,open(ROOT+'/tests/fullbody_v12_validation.json','w'),indent=2);print(json.dumps(report))
