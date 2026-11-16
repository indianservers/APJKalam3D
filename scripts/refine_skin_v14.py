"""Final skin color calibration and stronger anatomical hand crease relief."""
import bpy
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;bridge=bpy.app.driver_namespace['apj_capture'];was=bpy.app.timers.is_registered(bridge['timer'])
if was:bpy.app.timers.unregister(bridge['timer'])
bridge['tracker'].reset()
for mat in [bpy.data.objects['APJ_Face'].data.materials[0],bpy.data.objects['APJ_Hand_Left'].data.materials[0],bpy.data.objects['char1'].data.materials[0]]:
 hand='Hand' in mat.name
 for n in mat.node_tree.nodes:
  if n.type=='HUE_SAT' and n.label.startswith('V14'):
   n.inputs['Saturation'].default_value=1.;n.inputs['Value'].default_value=.78 if hand else .80
  if n.type=='BSDF_PRINCIPLED' and (not n.label or n.label.startswith('Aged')):n.inputs['Subsurface Weight'].default_value=.08
mat=bpy.data.objects['APJ_Hand_Left'].data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
if not any(n.label=='V14 anatomical joint and palm creases' for n in nodes):
 uv=nodes.new('ShaderNodeUVMap');uv.uv_map='Hand_Atlas';height=nodes.new('ShaderNodeTexImage');height.image=bpy.data.images.get('APJ_Hands_Height_2K') or bpy.data.images.load(ROOT+'/textures/hands/APJ_Hands_Height_2K.png');height.image.colorspace_settings.name='Non-Color';links.new(uv.outputs[0],height.inputs['Vector'])
 remap=nodes.new('ShaderNodeMapRange');remap.clamp=True;remap.inputs['From Min'].default_value=.47;remap.inputs['From Max'].default_value=.505;links.new(height.outputs[0],remap.inputs['Value']);bump=nodes.new('ShaderNodeBump');bump.label='V14 anatomical joint and palm creases';bump.inputs['Strength'].default_value=.80;bump.inputs['Distance'].default_value=.00050
 links.new(bs.inputs['Normal'].links[0].from_socket,bump.inputs['Normal']);links.new(remap.outputs[0],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal'])
nail=bpy.data.objects['APJ_Nail_Left_Index'].data.materials[0];nb=next(n for n in nail.node_tree.nodes if n.type=='BSDF_PRINCIPLED');nb.inputs['Base Color'].default_value=(.34,.22,.16,1);nb.inputs['Roughness'].default_value=.38;nb.inputs['Coat Weight'].default_value=.12
s.cycles.samples=8;s.render.bake.margin=12;s.render.bake.normal_space='TANGENT'
for name,kinds in [('APJ_Face',['Color']),('char1',['Color']),('APJ_Hand_Left',['Color','Normal']),('APJ_Hand_Right',['Color','Normal'])]:
 obj=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;records=[]
 for kind in kinds:
  records=[];image=bpy.data.images['APJ14_'+name+'_'+kind]
  for mat in obj.data.materials:
   nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');old=out.inputs['Surface'].links[0].from_socket;target=nodes.new('ShaderNodeTexImage');target.image=image;nodes.active=target
   for n in nodes:n.select=n==target
   em=None
   if kind=='Color':
    em=nodes.new('ShaderNodeEmission');links.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color']);links.new(em.outputs[0],out.inputs['Surface'])
   records.append((mat,out,old,target,em))
  try:bpy.ops.object.bake(type='NORMAL' if kind=='Normal' else 'EMIT')
  finally:
   for mat,out,old,target,em in records:
    mat.node_tree.links.new(old,out.inputs['Surface']);mat.node_tree.nodes.remove(target)
    if em:mat.node_tree.nodes.remove(em)
  image.save();image.pack()
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/blender/apj_skin_v14_master.blend')
if was:bpy.app.timers.register(bridge['timer'],first_interval=.03)
print('Warm skin pigmentation calibrated; anatomical hand crease normals rebaked')
