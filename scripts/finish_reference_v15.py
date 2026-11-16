"""Reference eyelid aperture and soft frontal portrait illumination."""
import bpy,json,math
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';f=bpy.data.objects['APJ_Face'];s=bpy.context.scene;state=bpy.app.driver_namespace['apj_capture'];was=bpy.app.timers.is_registered(state['timer'])
if was:bpy.app.timers.unregister(state['timer'])
state['tracker'].reset()
if not f.get('aperture_v15'):
 eyes=json.loads(f['eye_info'])
 for name in ['APJ_Face','APJ_v5_Skin_Transition_Underlay','char1']:
  obj=bpy.data.objects[name];base=obj.data.shape_keys.key_blocks['Basis'];ds=[]
  for p in base.data:
   x,y,z=p.co;dz=0.
   if y<0:
    for side,h in eyes.items():
     strength=.22 if side=='Right' else .055;w=math.exp(-((x-h['x'])/.016)**2-((z-h['z'])/.008)**2);dz+=(z-h['z'])*strength*w
   ds.append(dz)
  for key in obj.data.shape_keys.key_blocks:
   for p,dz in zip(key.data,ds):p.co.z+=dz
  obj.data.shape_keys.update_tag()
 exec(compile(open(ROOT+'/scripts/refresh_likeness_v5_rig.py').read(),'refresh_likeness_v5_rig.py','exec'))
 for p in json.loads(f['expression_channels'])+[p for p in bpy.data.objects['APJ_Face_Controls'].keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']:bpy.data.objects['APJ_Face_Controls'][p]=0.
 f['aperture_v15']=True
for name,loc,power,size in [('Studio_Key',(-.20,-.90,1.72),200,1.0),('Studio_Fill',(.32,-.80,1.53),100,.9),('Studio_Rim',(0,.40,1.80),100,.6)]:
 o=bpy.data.objects.get(name)
 if o:
  o.location=loc;o.rotation_euler=(Vector((0,0,1.52))-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.size=size;o.data.color=(1.,.96,.91)
for name in ['APJ_Eye_Left_Globe','APJ_Eye_Right_Globe','APJ_Eye_Left_Cornea','APJ_Eye_Right_Cornea']:
 b=next(n for n in bpy.data.objects[name].data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 b.inputs['Specular IOR Level'].default_value=0. if name.endswith('Globe') else .35
 if name.endswith('Globe'):b.inputs['Roughness'].default_value=.45
exec(compile(open(ROOT+'/scripts/calibrate_portrait_lights_v15.py').read(),'calibrate_portrait_lights_v15.py','exec'))
s.frame_set(1);bpy.context.view_layer.update()
# Bake just the revised face normal; color and UV alignment are unchanged.
obj=f;mat=f.data.materials[0];nodes=mat.node_tree.nodes;image=bpy.data.images['APJ15_APJ_Face_Normal'];target=nodes.new('ShaderNodeTexImage');target.image=image;nodes.active=target
for n in nodes:n.select=n==target
bpy.ops.object.select_all(action='DESELECT');f.select_set(True);bpy.context.view_layer.objects.active=f;s.cycles.samples=8
try:bpy.ops.object.bake(type='NORMAL');image.save();image.pack()
finally:nodes.remove(target)
if was:bpy.app.timers.register(state['timer'],first_interval=.03)
print('Eye openings and soft frontal reference lighting updated')
