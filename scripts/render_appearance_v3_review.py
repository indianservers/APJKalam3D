import bpy,os
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;cam=s.camera
s.cycles.samples=48;s.render.resolution_x=1200;s.render.resolution_y=1200;s.render.resolution_percentage=100
def render(name,position,target,scale):
    selection=globals().get('APJ_REVIEW_SELECTION')
    if selection and name not in selection:return
    cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    s.render.filepath=os.path.join(ROOT,'renders','appearance_v3_'+name+'.png');bpy.ops.render.render(write_still=True);print(name,'saved')
render('face_front',(0,-.65,1.52),(0,-.02,1.52),.30)
render('face_three_quarter',(.32,-.60,1.54),(0,0,1.52),.31)
render('eye_detail',(.015,-.45,1.52),(.015,-.06,1.515),.112)
render('hair_detail',(.25,-.35,1.68),(0,.005,1.58),.25)
render('fabric_detail',(.18,-.7,1.14),(0,-.04,1.12),.40)
render('shoe_detail',(.40,-.65,.25),(0,-.05,.08),.46)
s.render.resolution_x=1200;s.render.resolution_y=1600
render('full_body',(2,-4,1.85),(0,0,.85),2.05)
cam.location=(0,-.65,1.52);cam.rotation_euler=(Vector((0,-.02,1.52))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30
s.render.resolution_x=1200;s.render.resolution_y=1200
