"""Rigged transition ribbons close source-head/facial-patch gaps.
Ribbons overlap the facial surface; this is not a welded full-head retopology.
"""
import bpy,bmesh,math,json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
face=bpy.data.objects['APJ_Face'];body=bpy.data.objects['char1'];rig=bpy.data.objects['Armature'];ctrl=bpy.data.objects['APJ_Face_Controls'];s=bpy.context.scene
if bpy.data.objects.get('APJ_v5_Facial_Transition'):raise RuntimeError('Transition already built')
for prop in json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']:ctrl[prop]=0.
ctrl.update_tag();face.data.shape_keys.update_tag();s.frame_set(1);bpy.context.view_layer.update()
sub=next(m for m in body.modifiers if m.type=='SUBSURF');old=sub.show_viewport;sub.show_viewport=True;sub.levels=2;bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
edges=[]
for edge in bm.edges:
    if len(edge.link_faces)!=1:continue
    mid=(edge.verts[0].co+edge.verts[1].co)*.5
    if 1.411<mid.z<1.604 and mid.y<.005 and abs(mid.x)<.125:
        loop=next(l for l in edge.link_faces[0].loops if l.edge==edge)
        edges.append((loop.vert.index,loop.link_loop_next.vert.index))
source_indices=sorted({i for pair in edges for i in pair})
bv=BVHTree.FromObject(face,dg);kd=KDTree(len(face.data.vertices))
for i,v in enumerate(face.data.shape_keys.key_blocks['Basis'].data):kd.insert(v.co,i)
kd.balance()
image=bpy.data.images['APJ_v3_Baked_Albedo_4K'];w,h=image.size;pixels=np.array(image.pixels[:],dtype=np.float32).reshape(h,w,4)
uvdata=me.uv_layers[0].data;uvbyvert={me.loops[li].vertex_index:uvdata[li].uv.copy() for p in me.polygons for li in p.loop_indices}
verts=[];uvs=[];colors=[];weights=[];inner_source=[];outermap={};innermap={}
groupnames={g.index:g.name for g in body.vertex_groups};bone_names={b.name for b in rig.data.bones}
for index in source_indices:
    p=me.vertices[index].co.copy();uv=uvbyvert.get(index,Vector((.5,.5)))
    px=max(0,min(w-1,int(uv.x*(w-1))));py=max(0,min(h-1,int(uv.y*(h-1))));rgb=pixels[py,px,:3]
    linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    outermap[index]=len(verts);verts.append(p);uvs.append((p.x/.30+.5,(p.z-1.52)/.30+.5));colors.append((*linear,1.));inner_source.append(None)
    weight={groupnames[g.group]:g.weight for g in me.vertices[index].groups if groupnames.get(g.group) in bone_names and g.weight>1e-6}
    total=sum(weight.values());weights.append({n:v/total for n,v in weight.items()} if total else {'Head':1.})
    x=p.x*.955;z=max(1.425,min(1.589,p.z));hit=bv.ray_cast(Vector((x,-.6,z)),Vector((0,1,0)))[0]
    if hit is None:hit=bv.find_nearest(Vector((x,p.y,z)))[0]
    if hit is None:hit=p.copy()
    hit=hit.copy();hit.y+=.0003
    _,near,distance=kd.find(hit)
    innermap[index]=len(verts);verts.append(hit);uvs.append((hit.x/.30+.5,(hit.z-1.52)/.30+.5));colors.append((*linear,1.));weights.append({'Head':1.});inner_source.append(near)
polys=[]
for a,b in edges:polys.append((outermap[b],outermap[a],innermap[a],innermap[b]))
mesh=bpy.data.meshes.new('Facial_Transition_Ribbons');mesh.from_pydata(verts,[],polys);mesh.update();obj=bpy.data.objects.new('APJ_v5_Facial_Transition',mesh);s.collection.objects.link(obj)
mat=face.data.materials[0].copy();mat.name='APJ_v5_Facial_Transition_Skin';nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
color=nodes.new('ShaderNodeVertexColor');color.layer_name='TransitionColor';links.new(color.outputs['Color'],bs.inputs['Base Color']);mesh.materials.append(mat)
for name in ['UVMap','FaceProjection']:
    uv=mesh.uv_layers.new(name=name)
    for p in mesh.polygons:
        p.use_smooth=True
        for li in p.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
for name in ['TransitionColor','FacialEdgeBlend','FacialWrinkleMask']:
    attr=mesh.color_attributes.new(name=name,type='FLOAT_COLOR',domain='CORNER')
    for p in mesh.polygons:
        for li in p.loop_indices:attr.data[li].color=colors[mesh.loops[li].vertex_index] if name!='FacialWrinkleMask' else (0,0,0,0)
groups={name:obj.vertex_groups.new(name=name) for name in sorted({n for value in weights for n in value})}
for i,value in enumerate(weights):
    for name,weight in value.items():groups[name].add([i],weight,'REPLACE')
obj.shape_key_add(name='Basis')
base=face.data.shape_keys.key_blocks['Basis']
for source in list(face.data.shape_keys.key_blocks)[1:]:
    key=obj.shape_key_add(name=source.name,from_mix=False)
    for i,near in enumerate(inner_source):
        key.data[i].co=Vector(verts[i])+(source.data[near].co-base.data[near].co if near is not None else Vector())
    driver=key.driver_add('value').driver;var=driver.variables.new();var.name='v';var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=face.data.shape_keys;var.targets[0].data_path='key_blocks["'+source.name+'"].value';driver.expression='v'
mod=obj.modifiers.new('Transition skeletal binding','ARMATURE');mod.object=rig;obj.parent=rig
bm.free();ev.to_mesh_clear();sub.show_viewport=old
print('Built',len(polys),'transition quads with',len(obj.data.shape_keys.key_blocks)-1,'driven expression targets')
