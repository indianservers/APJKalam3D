"""Rebuild runtime with subdivided deformation targets and interpolated weights.
Uses existing v12 shader bakes. Does not change the source character topology.
"""
import bpy,json,os,numpy as np
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;r=bpy.data.objects['Armature'];ctrl=bpy.data.objects['APJ_Face_Controls'];f=bpy.data.objects['APJ_Face']
state=bpy.app.driver_namespace.pop('apj_capture',None)
if state:
 if bpy.app.timers.is_registered(state['timer']):bpy.app.timers.unregister(state['timer'])
 state['socket'].close();state['tracker'].reset()
visible=[o for o in s.objects if o.type=='MESH' and not o.hide_get() and not o.hide_render and not o.name.startswith('SOURCE') and o.name!='APJ_v5_Skin_Transition_Underlay']
copies=[];stats={}
def smooth(o):
 contacts=[{'target':m.target,'vertex_group':m.vertex_group,'offset':m.offset,'wrap_method':m.wrap_method,'wrap_mode':m.wrap_mode} for m in o.modifiers if m.type=='SHRINKWRAP']
 mods=list(o.modifiers)
 for m in mods:o.modifiers.remove(m)
 sub=o.modifiers.new('Runtime smooth deformation','SUBSURF');sub.levels=1;sub.render_levels=1
 for info in contacts:
  contact=o.modifiers.new('Baked eyelid contact','SHRINKWRAP')
  for k,v in info.items():setattr(contact,k,v)
 keynames=[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else []
 if o.data.shape_keys:
  o.data.shape_keys.animation_data_clear()
  for k in o.data.shape_keys.key_blocks:k.value=0.
 def evaluated():
  o.data.update();o.update_tag();bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(deps);mesh=ev.to_mesh(preserve_all_data_layers=True,depsgraph=deps);return ev,mesh
 ev,mesh=evaluated();newmesh=mesh.copy();ev.to_mesh_clear();count=len(newmesh.vertices);coords={}
 for name in keynames[1:]:
  key=o.data.shape_keys.key_blocks[name];key.value=1.;o.data.shape_keys.update_tag()
  ev,mesh=evaluated();a=np.empty(count*3,dtype=np.float32);mesh.vertices.foreach_get('co',a);coords[name]=a;ev.to_mesh_clear();key.value=0.
 for mod in list(o.modifiers):o.modifiers.remove(mod)
 o.data=newmesh
 if keynames:
  o.shape_key_add(name='Basis',from_mix=False)
  for name,values in coords.items():o.shape_key_add(name=name,from_mix=False).data.foreach_set('co',values)
 ar=o.modifiers.new('Runtime skin','ARMATURE');ar.object=r
 for p in o.data.polygons:p.use_smooth=True
 return count
for original in visible:
 o=original.copy();o.data=original.data.copy();o.name='EXPORT_'+original.name;s.collection.objects.link(o);copies.append(o)
 # Clear projection/mask colors so glTF cannot use them as base-color tint.
 for a in list(o.data.color_attributes):o.data.color_attributes.remove(a)
 ids=[p.material_index for p in o.data.polygons];mats=list(o.data.materials);o.data.materials.clear()
 bake=bpy.data.images.get('RuntimeColor_'+original.name)
 for j,old in enumerate(mats):
  mat=bpy.data.materials.new('Runtime13_'+original.name+str(j));mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');src=next(n for n in old.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
  bs.inputs['Base Color'].default_value=src.inputs['Base Color'].default_value;bs.inputs['Roughness'].default_value=.53
  if original.name in ['APJ_Face','APJ_Hand_Left','APJ_Hand_Right'] or (original.name=='char1' and j==0):
   bs.inputs['Specular IOR Level'].default_value=.20;bs.inputs['IOR'].default_value=1.4
  if bake:
   uv=nodes.new('ShaderNodeUVMap');uv.uv_map=o.data.uv_layers[0].name;tex=nodes.new('ShaderNodeTexImage');tex.image=bake;links.new(uv.outputs[0],tex.inputs['Vector']);links.new(tex.outputs[0],bs.inputs['Base Color'])
  if 'Cornea' in original.name:bs.inputs['Transmission Weight'].default_value=1.;bs.inputs['Roughness'].default_value=.025;bs.inputs['IOR'].default_value=1.38
  if 'Globe' in original.name:bs.inputs['Roughness'].default_value=.22
  if original.name=='char1' and j==2:bs.inputs['Roughness'].default_value=.25
  o.data.materials.append(mat)
 for p,i in zip(o.data.polygons,ids):p.material_index=i
 if original.name in ['APJ_Face','char1','APJ_Hand_Left','APJ_Hand_Right']:
  stats[original.name]={'vertices':smooth(o),'targets':len(o.data.shape_keys.key_blocks)-1 if o.data.shape_keys else 0}
 else:
  for mod in list(o.modifiers):
   if mod.type!='ARMATURE':o.modifiers.remove(mod)
bpy.ops.object.select_all(action='DESELECT');r.select_set(True)
for o in copies:
 # Three.js skinning uses four influences. Normalize explicitly before export.
 for vertex in o.data.vertices:
  weights=sorted([(g.group,g.weight) for g in vertex.groups],key=lambda x:x[1],reverse=True)
  if not weights:continue
  kept=weights[:4];total=sum(w for _,w in kept)
  for index,_ in weights[4:]:o.vertex_groups[index].remove([vertex.index])
  if total>0:
   for index,w in kept:o.vertex_groups[index].add([vertex.index],w/total,'REPLACE')
 o.select_set(True)
bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=ROOT+'/webapp/assets/apj_runtime_v13.glb',use_selection=True,export_apply=False,export_animations=False,export_all_influences=False,export_morph=True)
for o in copies:bpy.data.objects.remove(o,do_unlink=True)
json.dump({'meshes':stats,'bytes':os.path.getsize(ROOT+'/webapp/assets/apj_runtime_v13.glb'),'note':'Subdivided skin and targets; source unwelded facial seam remains.'},open(ROOT+'/tests/runtime_v13.json','w'),indent=2)
print(json.dumps(stats))
exec(compile(open(ROOT+'/scripts/fullbody_bridge.py').read(),'fullbody_bridge.py','exec'))
