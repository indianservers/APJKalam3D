"""Remove projected pale/tooth-colored pixels from the lip skin, not dental meshes."""
import bpy,math
ROOT=r'C:\Abdul Kalam';f=bpy.data.objects['APJ_Face'];s=bpy.context.scene
if not f.get('lip_texture_cleanup_v13'):
 mesh=f.data;attribute=mesh.color_attributes.new(name='LipColorCleanupV13',type='FLOAT_COLOR',domain='POINT');mz=float(f['mouth_center_z'])
 for i,p in enumerate(mesh.shape_keys.key_blocks['Basis'].data):
  x,y,z=p.co;mask=max(0,min(1,(.036-abs(x))/.008))*math.exp(-((z-mz)/.006)**4) if y<-.02 else 0
  attribute.data[i].color=(mask,mask,mask,1)
 mat=f.data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');old=bs.inputs['Base Color'].links[0].from_socket
 split=nodes.new('ShaderNodeSeparateColor');links.new(old,split.inputs[0]);minimum=nodes.new('ShaderNodeMath');minimum.operation='MINIMUM';links.new(split.outputs['Red'],minimum.inputs[0]);links.new(split.outputs['Green'],minimum.inputs[1]);minimum2=nodes.new('ShaderNodeMath');minimum2.operation='MINIMUM';links.new(minimum.outputs[0],minimum2.inputs[0]);links.new(split.outputs['Blue'],minimum2.inputs[1])
 bright=nodes.new('ShaderNodeMapRange');bright.clamp=True;bright.inputs['From Min'].default_value=.16;bright.inputs['From Max'].default_value=.32;links.new(minimum2.outputs[0],bright.inputs['Value'])
 attr=nodes.new('ShaderNodeVertexColor');attr.layer_name=attribute.name;factor=nodes.new('ShaderNodeMath');factor.operation='MULTIPLY';links.new(attr.outputs['Color'],factor.inputs[0]);links.new(bright.outputs[0],factor.inputs[1])
 clean=nodes.new('ShaderNodeMixRGB');clean.label='V13 remove projected white strip from lip skin';links.new(factor.outputs[0],clean.inputs[0]);links.new(old,clean.inputs[1]);clean.inputs[2].default_value=(.24,.105,.060,1);links.new(clean.outputs[0],bs.inputs['Base Color']);f['lip_texture_cleanup_v13']=True
# Update the face's standard-PBR color bake used by the browser.
state=bpy.app.driver_namespace['apj_capture'];was=bpy.app.timers.is_registered(state['timer'])
if was:bpy.app.timers.unregister(state['timer'])
state['tracker'].reset();mat=f.data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');old=out.inputs['Surface'].links[0].from_socket
em=nodes.new('ShaderNodeEmission');links.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color']);links.new(em.outputs[0],out.inputs['Surface']);target=nodes.new('ShaderNodeTexImage');target.image=bpy.data.images['RuntimeColor_APJ_Face'];nodes.active=target
for n in nodes:n.select=n==target
f.data.uv_layers.active_index=0
for i,uv in enumerate(f.data.uv_layers):uv.active_render=i==0
bpy.ops.object.select_all(action='DESELECT');f.select_set(True);bpy.context.view_layer.objects.active=f;s.render.engine='CYCLES';s.cycles.samples=1;s.render.bake.use_selected_to_active=False
try:
 bpy.ops.object.bake(type='EMIT');target.image.filepath_raw=ROOT+'/webapp/assets/RuntimeColor_APJ_Face.png';target.image.save();target.image.pack()
finally:
 links.new(old,out.inputs['Surface']);nodes.remove(em);nodes.remove(target)
 if was:bpy.app.timers.register(state['timer'],first_interval=.03)
print('Lip color cleanup baked; real dental meshes retained')
