"""Bake the exact reference image alignment and revised surface for runtime."""
import bpy,json
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;state=bpy.app.driver_namespace['apj_capture'];was=bpy.app.timers.is_registered(state['timer'])
if was:bpy.app.timers.unregister(state['timer'])
state['tracker'].reset();hair=bpy.data.objects['APJ_v15_Silver_Hair_Strands'];uv=hair.data.uv_layers.get('FiberDirection') or hair.data.uv_layers.new(name='FiberDirection')
for loop in hair.data.loops:
 p=hair.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(loop.vertex_index%2,max(0,min(1,(1.64-p.z)/.23)))
for m in hair.data.materials:
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Anisotropic Rotation'].default_value=.25
s.render.engine='CYCLES';s.cycles.samples=8;s.render.bake.margin=12;s.render.bake.use_selected_to_active=False;s.render.bake.normal_space='TANGENT'
report={}
for name in ['APJ_Face','char1']:
 obj=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;obj.data.uv_layers.active_index=0
 for i,uv in enumerate(obj.data.uv_layers):uv.active_render=i==0
 report[name]={}
 for kind in ['Color','Roughness','Normal']:
  image=bpy.data.images.new('APJ15_'+name+'_'+kind,width=2048,height=2048,alpha=False)
  if kind!='Color':image.colorspace_settings.name='Non-Color'
  records=[]
  for material in obj.data.materials:
   nodes=material.node_tree.nodes;links=material.node_tree.links;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');old=out.inputs['Surface'].links[0].from_socket;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');target=nodes.new('ShaderNodeTexImage');target.image=image;nodes.active=target
   for n in nodes:n.select=n==target
   em=None
   if kind!='Normal':
    em=nodes.new('ShaderNodeEmission');source=bs.inputs['Base Color' if kind=='Color' else 'Roughness']
    if source.is_linked:links.new(source.links[0].from_socket,em.inputs['Color'])
    elif kind=='Color':em.inputs['Color'].default_value=source.default_value
    else:em.inputs['Color'].default_value=(source.default_value,)*3+(1,)
    links.new(em.outputs[0],out.inputs['Surface'])
   records.append((material,out,old,target,em))
  try:bpy.ops.object.bake(type='NORMAL' if kind=='Normal' else 'EMIT')
  finally:
   for material,out,old,target,em in records:
    material.node_tree.links.new(old,out.inputs['Surface']);material.node_tree.nodes.remove(target)
    if em:material.node_tree.nodes.remove(em)
  image.filepath_raw=ROOT+'/textures/reference_v15/'+image.name+'.png';image.file_format='PNG';image.save();image.pack();report[name][kind]=image.filepath_raw
json.dump(report,open(ROOT+'/tests/reference_v15_maps.json','w'),indent=2)
if was:bpy.app.timers.register(state['timer'],first_interval=.03)
print('Reference v15 color, roughness and normal bakes complete')
