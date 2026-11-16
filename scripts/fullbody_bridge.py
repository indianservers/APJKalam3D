"""Blender localhost UDP receiver with command allowlist and visible status."""
import bpy,json,time,socket,os,traceback
ROOT=r'C:\Abdul Kalam'
exec(compile(open(ROOT+'/scripts/fullbody_tracking.py').read(),'fullbody_tracking.py','exec'))
exec(compile(open(ROOT+'/scripts/capture_presets.py').read(),'capture_presets.py','exec'))
ns=bpy.app.driver_namespace
for name in ['apj_live_face','apj_capture']:
 old=ns.pop(name,None)
 if old:
  if bpy.app.timers.is_registered(old['timer']):bpy.app.timers.unregister(old['timer'])
  old['socket'].close()
receiver=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);receiver.bind(('127.0.0.1',9877));receiver.setblocking(False)
tracker=FullBodyTracker();state={'socket':receiver,'tracker':tracker,'last':0.,'tick':time.monotonic(),'publish':0.,'packets':0,'mode':'idle','recording':False,'recorded':0,'settings':{'body':True,'hands':True,'face':True,'root':True,'response':14,'confidence':.5},'error':None}
def command(name,data):
 if name=='reset':tracker.reset();state['mode']='idle';state['packet']={}
 elif name=='calibrate':
  state['calibration_ok']=tracker.calibrate(state.get('packet',{}))
 elif name=='calibrate_face':state['face_calibration_ok']=tracker.calibrate_face(state.get('packet',{}))
 elif name=='smile':state['smile_until']=time.monotonic()+5
 elif name in ['seated','standing']:
  packet=pose_packet(name);tracker.reset()
  for _ in range(40):tracker.update(packet,.033,state['settings'])
  if name=='seated':tracker.rig.pose.bones['Root'].location.y=-.30
  state['mode']=name;state['packet']={}
 elif name=='settings':
  for k in ['body','hands','face','root']:
   if k in data:state['settings'][k]=bool(data[k])
  for k,lo,hi in [('response',3,30),('confidence',.2,.95)]:
   if isinstance(data.get(k),(int,float)):state['settings'][k]=max(lo,min(hi,float(data[k])))
 elif name=='record_start':
  state['recording']=True;state['recorded']=0;state['record_start']=time.monotonic()
  tracker.rig.animation_data_create();tracker.rig.animation_data.action=bpy.data.actions.new('APJ_Camera_Body_'+time.strftime('%H%M%S'))
  tracker.ctrl.animation_data_create();tracker.ctrl.animation_data.action=bpy.data.actions.new('APJ_Camera_Face_'+time.strftime('%H%M%S'))
 elif name=='record_stop':
  state['recording']=False;bpy.context.scene.frame_end=max(60,state['recorded']);state['mode']='recorded'
 elif name=='save':
  bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/blender/apj_reference_v15_session.blend')
def tick():
 now=time.monotonic();dt=min(.1,now-state['tick']);state['tick']=now
 try:
  for _ in range(60):
   try:packet=json.loads(receiver.recv(65535).decode())
   except BlockingIOError:break
   if packet.get('type')=='command':command(packet.get('name'),packet.get('data',{}))
   elif packet.get('type')=='frame':
    state['packet']=packet;state['last']=now;state['packets']+=1;state['mode']='live'
  if state['mode']=='live':
   state['tracking']=tracker.update(state.get('packet',{}) if now-state['last']<.7 else {},dt,state['settings'])
   if now-state['last']>2:state['mode']='idle'
  if now<state.get('smile_until',0):
   for name,value in {'mouthSmileLeft':.85,'mouthSmileRight':.85,'cheekSquintLeft':.25,'cheekSquintRight':.25,'eyeSquintLeft':.18,'eyeSquintRight':.18,'mouthUpperUpLeft':.15,'mouthUpperUpRight':.15,'jawOpen':.10,'mouthFrownLeft':0.,'mouthFrownRight':0.}.items():tracker.ctrl[name]=value
   tracker.ctrl.update_tag();tracker.face.data.shape_keys.update_tag();bpy.context.view_layer.update()
  elif 'smile_until' in state:
   state.pop('smile_until')
   if state['mode']!='live':
    for name in tracker.names:tracker.ctrl[name]=0.
    tracker.ctrl.update_tag();tracker.face.data.shape_keys.update_tag();bpy.context.view_layer.update()
  if state['recording'] and now-state['last']<.7:
   frame=int((now-state['record_start'])*30)+1;state['recorded']=frame
   for b in tracker.rig.pose.bones:
    if b.name not in ['Jaw','Eye.L','Eye.R']:
     b.keyframe_insert('rotation_quaternion',frame=frame,group=b.name);b.keyframe_insert('location',frame=frame,group=b.name)
   for n in tracker.names:tracker.ctrl.keyframe_insert(data_path='["'+n+'"]',frame=frame,group='Face')
  if now-state['publish']>.04:
   state['publish']=now
   data={'time':time.time(),'mode':state['mode'],'packets':state['packets'],'tracking':state.get('tracking',{}),'settings':state['settings'],'calibrated':tracker.calibration is not None,'calibration_ok':state.get('calibration_ok'),'face_calibration_ok':state.get('face_calibration_ok'),'recording':state['recording'],'recordedFrames':state['recorded'],'error':state['error'],'rigBones':len(tracker.rig.data.bones),**tracker.snapshot()}
   path=ROOT+'/mocap/capture_state.json';tmp=path+'.tmp'
   with open(tmp,'w') as file:json.dump(data,file)
   try:os.replace(tmp,path)
   except PermissionError:pass # Windows may briefly hold the file during an HTTP read.
   state['error']=None
  for area in bpy.context.screen.areas if bpy.context.screen else []:
   if area.type=='VIEW_3D':area.tag_redraw()
 except Exception:
  print(traceback.format_exc());state['error']='Motion update failed. See the Blender console for details.'
 return 1/30
state['timer']=tick;ns['apj_capture']=state;bpy.app.timers.register(tick,first_interval=.05)
print('APJ capture bridge listening at 127.0.0.1:9877; full body, fingers and face')
