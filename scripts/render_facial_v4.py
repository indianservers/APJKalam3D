"""Cycles facial expression review, selected via FACIAL_RENDER_SELECTION."""
import bpy,json,os
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;c=bpy.data.objects['APJ_Face_Controls'];face=bpy.data.objects['APJ_Face']
if c.animation_data:c.animation_data.action=None
channels=json.loads(face['expression_channels'])+[p for p in c.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']
poses={
 'neutral':{},'brows_raised':{'browInnerUp':.9,'browOuterUpLeft':.55,'browOuterUpRight':.55},
 'frown':{'browDownLeft':.8,'browDownRight':.8},
 'blink':{'eyeBlinkLeft':1.,'eyeBlinkRight':1.},
 'smile':{'mouthSmileLeft':.75,'mouthSmileRight':.75,'cheekSquintLeft':.20,'cheekSquintRight':.20},
 'jaw_open':{'jawOpen':.70},'pucker':{'mouthPucker':.7},'gaze_left':{'gazeHorizontal':.8},
 'smile_jaw_three_quarter':{'jawOpen':.45,'mouthSmileLeft':.55,'mouthSmileRight':.55},
 'wrinkle_closeup':{'browInnerUp':1.,'browOuterUpLeft':.6,'browOuterUpRight':.6}}
s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100
for name,values in poses.items():
    selected=globals().get('FACIAL_RENDER_SELECTION')
    if selected and name not in selected:continue
    for prop in channels:c[prop]=float(values.get(prop,0.))
    c.update_tag();face.data.shape_keys.update_tag();s.frame_set(s.frame_current+1)
    target=Vector((0,-.02,1.52));cam=s.camera;cam.location=(0,-.65,1.52);cam.data.ortho_scale=.30
    if name.endswith('three_quarter'):cam.location=(.30,-.60,1.54)
    if name=='wrinkle_closeup':cam.location=(0,-.55,1.567);target=Vector((0,-.08,1.567));cam.data.ortho_scale=.12
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=os.path.join(ROOT,'renders','facial_v4_'+name+'.png');bpy.ops.render.render(write_still=True);print(name,'saved')
for prop in channels:c[prop]=0.
c.update_tag();face.data.shape_keys.update_tag();s.frame_set(1)
cam=s.camera;cam.location=(0,-.65,1.52);cam.rotation_euler=(Vector((0,-.02,1.52))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30
