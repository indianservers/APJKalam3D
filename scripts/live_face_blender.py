"""Start a nonblocking localhost facial receiver in the active Blender session."""
import bpy,socket,json,time
exec(compile(open(r'C:\Abdul Kalam\scripts\facial_v4_mediapipe.py').read(),'facial_v4_mediapipe.py','exec'))
ns=bpy.app.driver_namespace
old=ns.get('apj_live_face')
if old:
    if bpy.app.timers.is_registered(old['timer']):bpy.app.timers.unregister(old['timer'])
    old['socket'].close()
adapter=FaceCoefficientAdapter(response=22.)
receiver=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);receiver.bind(('127.0.0.1',9877));receiver.setblocking(False)
state={'socket':receiver,'adapter':adapter,'last':time.monotonic(),'tick':time.monotonic(),'packets':0,'tracked':False}
def apj_live_tick():
    now=time.monotonic();latest=None
    for _ in range(100):
        try:latest=json.loads(receiver.recv(65535).decode())
        except BlockingIOError:break
        except (ValueError,UnicodeError):continue
    if latest is not None:
        state['last']=now;state['packets']+=1;state['tracked']=bool(latest.get('tracked'))
        state['scores']=latest.get('scores',{})
    adapter.update(state.get('scores',{}) if now-state['last']<.7 else {},dt=now-state['tick'])
    state['tick']=now
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.tag_redraw()
    return 1/30
state['timer']=apj_live_tick;ns['apj_live_face']=state
bpy.app.timers.register(apj_live_tick,first_interval=.03)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
print('Live facial receiver listening on localhost:9877')
