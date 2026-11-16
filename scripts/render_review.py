"""Small Cycles review renders, not final 4K acceptance renders."""
import bpy,os
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;cam=s.camera
r=bpy.data.objects['Armature'];m=bpy.data.objects['char1']
rig_action=r.animation_data.action;face_action=m.data.shape_keys.animation_data.action
r.animation_data.action=None;m.data.shape_keys.animation_data.action=None
def reset():
    for b in r.pose.bones:b.matrix_basis.identity()
    for k in m.data.shape_keys.key_blocks:k.value=0
def render(name,position,target,scale):
    cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    s.render.filepath=os.path.join(ROOT,'renders',name+'.png');bpy.ops.render.render(write_still=True)
s.render.resolution_x=800;s.render.resolution_y=800;s.cycles.samples=24
reset();render('face_neutral',(0,-.65,1.52),(0,-.02,1.52),.30)
m.data.shape_keys.key_blocks['browInnerUp'].value=1
m.data.shape_keys.key_blocks['browOuterUpLeft'].value=.7;m.data.shape_keys.key_blocks['browOuterUpRight'].value=.7
render('face_brow_prototype',(0,-.65,1.52),(0,-.02,1.52),.30)
reset();render('hand_neutral',(.64,.01,2),(.64,.01,1.30),.23)
for b in r.pose.bones:
    if b.name.startswith('LeftHand') and any(f in b.name for f in ['Thumb','Index','Middle','Ring','Pinky']):b.rotation_mode='XYZ';b.rotation_euler.z=.5
render('hand_curl_prototype',(.64,.01,2),(.64,.01,1.30),.23)
reset()
for name,pos in [('front',(0,-4,.85)),('back',(0,4,.85)),('left_profile',(4,0,.85)),('right_profile',(-4,0,.85))]:
    render('body_'+name,pos,(0,0,.85),1.95)
r.animation_data.action=rig_action;m.data.shape_keys.animation_data.action=face_action;s.frame_set(1)
cam.location=(2,-4,1.85);cam.rotation_euler=(Vector((0,0,.85))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.05
s.render.resolution_x=1000;s.render.resolution_y=1100;s.cycles.samples=32
print('Saved 8 review renders')
