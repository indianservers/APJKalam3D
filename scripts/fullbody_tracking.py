"""Local landmark-to-rig solver. Metric world landmarks drive limb directions.
Thoracic motion is inferred, not individual-rib measurement. No input code executes.
"""
import bpy,math,json,time
from mathutils import Vector,Quaternion,Matrix
BODY={'LeftArm':(11,13),'LeftForeArm':(13,15),'RightArm':(12,14),'RightForeArm':(14,16),'LeftUpLeg':(23,25),'LeftLeg':(25,27),'RightUpLeg':(24,26),'RightLeg':(26,28),'LeftFoot':(27,31),'RightFoot':(28,32)}
FINGERS={'Thumb':(1,2,3,4),'Index':(5,6,7,8),'Middle':(9,10,11,12),'Ring':(13,14,15,16),'Pinky':(17,18,19,20)}
def vec(p):return Vector((p['x'],p['z'],-p['y']))
def frame(x,z):
 if x.length<1e-5 or z.length<1e-5:return Quaternion()
 x=x.normalized();z=(z-x*z.dot(x)).normalized();y=z.cross(x).normalized()
 if y.length<.1:return Quaternion()
 return Matrix((x,y,z)).transposed().to_quaternion()
def limited(q,degrees):
 axis,angle=q.to_axis_angle()
 if angle>math.pi:angle-=2*math.pi
 return Quaternion(axis,max(-math.radians(degrees),min(math.radians(degrees),angle)))
class FullBodyTracker:
 def __init__(self):
  self.rig=bpy.data.objects['Armature'];self.face=bpy.data.objects['APJ_Face'];self.ctrl=bpy.data.objects['APJ_Face_Controls']
  self.names=json.loads(self.face['expression_channels'])+[n for n in self.ctrl.keys() if n.startswith('eyeLook')]
  self.rest={b.name:b.matrix_local.to_quaternion() for b in self.rig.data.bones};self.directions={b.name:(b.tail_local-b.head_local).normalized() for b in self.rig.data.bones}
  self.calibration=None;self.faceNeutral={};self.headNeutral=Quaternion();self.last={};self.reset()
 def reset(self):
  if self.rig.animation_data:self.rig.animation_data.action=None
  if self.ctrl.animation_data:self.ctrl.animation_data.action=None
  for b in self.rig.pose.bones:
   if b.name not in ['Jaw','Eye.L','Eye.R']:b.matrix_basis.identity()
  for n in self.names:self.ctrl[n]=0.
  self.ctrl['gazeHorizontal']=0.;self.ctrl['gazeVertical']=0.;self.rig['breathing']=0.
  self.ctrl.update_tag();self.face.data.shape_keys.update_tag();bpy.context.view_layer.update()
 def calibrate(self,packet):
  p=packet.get('pose',[]);im=packet.get('poseImage',[])
  if len(p)!=33 or min(p[i].get('visibility',0) for i in [11,12,23,24,25,26,27,28])<.55:return False
  v=list(map(vec,p));z=(v[11]+v[12]-v[23]-v[24])*.5;x=v[11]-v[12]
  self.calibration={'torso':frame(x,z),'hipY':(im[23]['y']+im[24]['y'])/2 if len(im)==33 else .5,'torsoPixels':abs((im[11]['y']+im[12]['y']-im[23]['y']-im[24]['y'])/2) if len(im)==33 else .25}
  return True
 def calibrate_face(self,packet):
  if not packet.get('face'):return False
  self.faceNeutral=dict(packet['face']);fp=packet.get('facePoints',[])
  if len(fp)>=468:
   v=list(map(vec,fp));self.headNeutral=frame(v[263]-v[33],v[10]-v[152])
  return True
 def update(self,packet,dt=.033,settings=None):
  settings=settings or {};alpha=1-math.exp(-float(settings.get('response',14))*min(.15,max(.001,dt)))
  p=packet.get('pose',[]) if settings.get('body',True) else [];h=packet.get('hands',[]) if settings.get('hands',True) else []
  deltas={};visibility=float(settings.get('confidence',.5))
  base=self.calibration['torso'].inverted() if self.calibration else Quaternion()
  def good(indices):return len(p)==33 and min(p[i].get('visibility',0) for i in indices)>=visibility
  if good([11,12,23,24]):
   v=list(map(vec,p));hips=(v[23]+v[24])*.5;shoulders=(v[11]+v[12])*.5
   torso=frame(v[11]-v[12],shoulders-hips);pelvis=frame(v[23]-v[24],shoulders-hips)
   # Calibration removes camera yaw/roll while preserving actual limb articulation.
   base=self.calibration['torso'].inverted() if self.calibration else Quaternion()
   pelvis=limited(base@pelvis,65);torso=limited(base@torso,75)
   deltas['Hips']=pelvis
   deltas['Spine02']=pelvis.slerp(torso,.33);deltas['Spine01']=pelvis.slerp(torso,.66);deltas['Spine']=torso
   for side in ['Left','Right']:deltas[side+'Shoulder']=torso
   for n,(a,b) in BODY.items():
    if good([a,b]):
     d=base@(v[b]-v[a])
     if d.length>1e-5:deltas[n]=self.directions[n].rotation_difference(d.normalized())
   im=packet.get('poseImage',[])
   if len(im)==33 and self.calibration and settings.get('root',True):
    drop=(self.calibration['hipY']-(im[23]['y']+im[24]['y'])/2)*.39/max(.1,self.calibration['torsoPixels'])
    target=max(-.48,min(.20,drop));root=self.rig.pose.bones['Root'];root.location.y+=(target-root.location.y)*alpha
  else:
   self.rig.pose.bones['Root'].location*=1-alpha
  # Arms must remain available in seated/upper-body framing without visible hips.
  if len(p)==33:
   v=list(map(vec,p))
   for n,(a,b) in BODY.items():
    if not ('Arm' in n):continue
    if good([a,b]):
     d=base@(v[b]-v[a])
     if d.length>1e-5:deltas[n]=self.directions[n].rotation_difference(d.normalized())
  # Face frame from landmarks; aspect-corrected by the browser before delivery.
  fp=packet.get('facePoints',[]) if settings.get('face',True) else []
  if len(fp)>=468:
   fv=list(map(vec,fp));head=limited(frame(fv[263]-fv[33],fv[10]-fv[152])@self.headNeutral.inverted(),55)
   base=self.calibration['torso'].inverted() if self.calibration else Quaternion()
   head=base@head@(base.inverted() if self.faceNeutral else Quaternion());torso=deltas.get('Spine',Quaternion());deltas['neck']=torso.slerp(head,.3);deltas['Head']=head
  # Palm orientation and finger segment directions in the same camera frame.
  for hand in h:
   side=hand.get('side');pts=hand.get('world',[])
   if side not in ['Left','Right'] or len(pts)!=21 or hand.get('confidence',0)<visibility:continue
   v=list(map(vec,pts));base=self.calibration['torso'].inverted() if self.calibration else Quaternion()
   n=side+'Hand';restside=1 if side=='Left' else -1
   # Two vectors constrain wrist roll, unlike a single forearm direction.
   long=(v[9]-v[0]).normalized();across=(v[5]-v[17]).normalized()
   restlong=self.directions[n];restacross=Vector((0,-1,0))
   observed=frame(base@long,base@across);reference=frame(restlong,restacross)
   deltas[n]=observed@reference.inverted()
   for finger,ids in FINGERS.items():
    for j in range(3):
     name=f'{side}Hand{finger}{j+1}';direction=base@(v[ids[j+1]]-v[ids[j]])
     if direction.length>1e-6:deltas[name]=self.directions[name].rotation_difference(direction.normalized())
  # Solve desired world orientation to local basis, parent first. No compounded swing.
  actual={}
  for b in sorted(self.rig.pose.bones,key=lambda b:len(b.parent_recursive)):
   n=b.name
   if n in ['Jaw','Eye.L','Eye.R','Root'] or n.startswith('Rib.') or n=='Sternum' or n.endswith(('_IK','_Pole')):continue
   parent=actual.get(b.parent.name,Quaternion()) if b.parent else Quaternion()
   desired=deltas.get(n,parent)
   local=self.rest[n].inverted()@parent.inverted()@desired@self.rest[n]
   b.rotation_mode='QUATERNION';b.rotation_quaternion=b.rotation_quaternion.slerp(local,alpha)
   actual[n]=parent@self.rest[n]@b.rotation_quaternion@self.rest[n].inverted()
  scores=packet.get('face',{}) if settings.get('face',True) else {}
  for n in self.names:
   raw=scores.get(n,0);raw=float(raw) if isinstance(raw,(float,int)) and math.isfinite(raw) else 0
   if n.startswith('eyeLook'):
    raw=max(0,raw-self.faceNeutral.get(n,0))*.55
   else:
    neutral=self.faceNeutral.get(n,0)
    # Compensate resting-expression bias without erasing deliberate expression.
    bias=min(neutral,.35) if n.startswith(('mouthFrown','mouthShrug','mouthStretch','eyeSquint')) else .03
    raw=max(0,raw-bias)
    gain=2.0 if n.startswith('mouthSmile') else 1.45 if n.startswith(('jawOpen','eyeBlink')) else 1.15
    raw*=gain
   self.ctrl[n]=float(self.ctrl[n])+(max(0,min(1,raw))-float(self.ctrl[n]))*alpha
  self.ctrl.update_tag();self.face.data.shape_keys.update_tag();bpy.context.view_layer.update()
  return {'body':good([11,12]),'legs':good([23,24,25,26,27,28]),'hands':len(h),'face':bool(scores),'calibrated':self.calibration is not None}
 def snapshot(self):
  return {'bones':{b.name:{'q':list(b.rotation_quaternion)[1:]+[b.rotation_quaternion.w] if b.rotation_mode=='QUATERNION' else list(b.rotation_euler.to_quaternion())[1:]+[b.rotation_euler.to_quaternion().w], 'p':list(b.location)} for b in self.rig.pose.bones},'face':{n:float(self.ctrl[n]) for n in self.names},'morphs':{k.name:float(k.value) for k in self.face.data.shape_keys.key_blocks[1:]}}
