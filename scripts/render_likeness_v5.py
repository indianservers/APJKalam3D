import bpy,json,os
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';scene=bpy.context.scene;face=bpy.data.objects['APJ_Face'];ctrl=bpy.data.objects['APJ_Face_Controls'];cam=scene.camera
if ctrl.animation_data:ctrl.animation_data.action=None
channels=json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical'];pose=json.loads(face['reference_pose_v5'])
def values(data):
    for p in channels:ctrl[p]=float(data.get(p,0.))
    ctrl.update_tag();face.data.shape_keys.update_tag();scene.frame_set(scene.frame_current+1)
def render(name,position):
    cam.location=position;cam.rotation_euler=(Vector((0,-.02,1.52))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30
    scene.render.filepath=os.path.join(ROOT,'renders','sculpt_v5_'+name+'.png');bpy.ops.render.render(write_still=True)
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.render.resolution_x=1100;scene.render.resolution_y=1100
values(pose);render('reference_pose_three_quarter',(.24,-.60,1.54))
values({});render('neutral_front',(0,-.65,1.52))
clay=bpy.data.materials.new('APJ_v5_Sculpt_Review_Clay');clay.use_nodes=True;bs=next(n for n in clay.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.30,.29,.27,1);bs.inputs['Roughness'].default_value=.70
scene.view_layers[0].material_override=clay;render('clay_front',(0,-.65,1.52));scene.view_layers[0].material_override=None
values(pose);scene.frame_set(1)
cam.location=(0,-.65,1.52);cam.rotation_euler=(Vector((0,-.02,1.52))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30
print('Likeness review: three-quarter, neutral and clay saved')
