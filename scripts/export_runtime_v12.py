"""Bake actual latest color shaders and export the complete skinned character."""
import bpy,os,json
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;r=bpy.data.objects['Armature'];bpy.data.objects['APJ_Face_Controls'].animation_data.action=None
for b in r.pose.bones:
 if b.name not in ['Jaw','Eye.L','Eye.R']:b.matrix_basis.identity()
s.frame_set(1);bpy.context.view_layer.update()
state=bpy.app.driver_namespace.get('apj_capture')
if state:
 if bpy.app.timers.is_registered(state['timer']):bpy.app.timers.unregister(state['timer'])
 state['socket'].close();bpy.app.driver_namespace.pop('apj_capture',None)
visible=[o for o in s.objects if o.type=='MESH' and not o.hide_get() and not o.hide_render and not o.name.startswith('SOURCE')]
copies=[];materials={};textures={};s.render.engine='CYCLES';s.cycles.samples=1;s.render.bake.margin=8;s.render.bake.use_selected_to_active=False
def bake_color(o,res):
 im=bpy.data.images.new('RuntimeColor_'+o.name,width=res,height=res,alpha=False)
 restore=[]
 for mat in o.data.materials:
  nodes=mat.node_tree.nodes;links=mat.node_tree.links;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');old=out.inputs['Surface'].links[0].from_socket
  bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');em=nodes.new('ShaderNodeEmission')
  if bs.inputs['Base Color'].is_linked:links.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color'])
  else:em.inputs['Color'].default_value=bs.inputs['Base Color'].default_value
  links.new(em.outputs[0],out.inputs['Surface']);target=nodes.new('ShaderNodeTexImage');target.image=im;nodes.active=target
  for n in nodes:n.select=n==target
  restore.append((mat,out,old,em,target))
 oldactive=o.data.uv_layers.active_index;o.data.uv_layers.active_index=0
 for i,uv in enumerate(o.data.uv_layers):uv.active_render=i==0
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 try:bpy.ops.object.bake(type='EMIT')
 finally:
  for mat,out,old,em,target in restore:mat.node_tree.links.new(old,out.inputs['Surface']);mat.node_tree.nodes.remove(em);mat.node_tree.nodes.remove(target)
  o.data.uv_layers.active_index=oldactive
 im.filepath_raw=ROOT+'/webapp/assets/'+im.name+'.png';im.file_format='PNG';im.save();im.pack();return im
for name,res in [('char1',2048),('APJ_Face',2048),('APJ_Hand_Left',1024),('APJ_Hand_Right',1024),('APJ_Eye_Left_Globe',512),('APJ_Eye_Right_Globe',512)]:
 textures[name]=bake_color(bpy.data.objects[name],res)
for o in visible:
 copy=o.copy();copy.data=o.data.copy();copy.name='EXPORT_'+o.name;s.collection.objects.link(copy);copies.append(copy)
 for a in list(copy.data.color_attributes):copy.data.color_attributes.remove(a)
 inds=[p.material_index for p in copy.data.polygons];oldmats=list(copy.data.materials);copy.data.materials.clear()
 tex=textures.get(o.name) or (textures['APJ_Face'] if o.name=='APJ_v5_Skin_Transition_Underlay' else None)
 for j,orig in enumerate(oldmats):
  key=(o.name,j)
  mat=bpy.data.materials.new('Runtime_'+o.name+str(j));mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
  originalbs=next(n for n in orig.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
  bs.inputs['Roughness'].default_value=.50 if j==0 else .65
  if tex:
   uv=nodes.new('ShaderNodeUVMap');uv.uv_map=copy.data.uv_layers[0].name;n=nodes.new('ShaderNodeTexImage');n.image=tex;links.new(uv.outputs[0],n.inputs['Vector']);links.new(n.outputs[0],bs.inputs['Base Color'])
  else:bs.inputs['Base Color'].default_value=originalbs.inputs['Base Color'].default_value
  if 'Cornea' in o.name:
   bs.inputs['Base Color'].default_value=(1,1,1,1);bs.inputs['Transmission Weight'].default_value=1.;bs.inputs['Roughness'].default_value=.03;bs.inputs['IOR'].default_value=1.38
  if o.name=='char1' and j==2:bs.inputs['Roughness'].default_value=.25
  copy.data.materials.append(mat)
 for p,i in zip(copy.data.polygons,inds):p.material_index=i
 # Keep skinning and all morph targets. Runtime uses pre-subdivision topology.
 for mod in list(copy.modifiers):
  if mod.type!='ARMATURE':copy.modifiers.remove(mod)
 if copy.data.shape_keys:
  for k in copy.data.shape_keys.key_blocks:k.value=0.
bpy.ops.object.select_all(action='DESELECT');r.select_set(True)
for o in copies:o.select_set(True)
bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=ROOT+'/webapp/assets/apj_runtime_v12.glb',use_selection=True,export_apply=False,export_animations=False,export_all_influences=True,export_morph=True)
for o in copies:bpy.data.objects.remove(o,do_unlink=True)
# Export object names retain their source identity for the browser's morph mapper.
print('Runtime exported',os.path.getsize(ROOT+'/webapp/assets/apj_runtime_v12.glb'),'bytes')
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/blender/apj_fullbody_v12_master.blend')
