"""Reduce false cut-edge shadows from the deliberately overlapping head surfaces.
This is a render join correction, not a welded-topology repair.
"""
import bpy,bmesh,math
from mathutils.kdtree import KDTree
body=bpy.data.objects['char1'];mesh=body.data
bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();ids=set()
for e in bm.edges:
    if len(e.link_faces)!=1:continue
    for v in e.verts:
        if .043<abs(v.co.x)<.12 and 1.418<v.co.z<1.502 and v.co.y<.01:ids.add(v.index)
kd=KDTree(len(ids))
for i,index in enumerate(ids):kd.insert(mesh.vertices[index].co,i)
kd.balance();values=[]
for v in mesh.vertices:
    _,_,distance=kd.find(v.co) if ids else (None,None,1.)
    t=max(0,min(1,1-distance/.004));t=t*t*(3-2*t)
    if not (1.415<v.co.z<1.505 and abs(v.co.x)>.040 and v.co.y<.015):t=0.
    values.append(t)
bm.free();attr=mesh.color_attributes.new(name='JawJoinShadowMask',type='FLOAT_COLOR',domain='CORNER')
for poly in mesh.polygons:
    for li in poly.loop_indices:
        w=values[mesh.loops[li].vertex_index];attr.data[li].color=(w,w,w,1)
mat=mesh.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');old=out.inputs['Surface'].links[0].from_socket
attribute=nodes.new('ShaderNodeVertexColor');attribute.layer_name='JawJoinShadowMask';light=nodes.new('ShaderNodeLightPath')
mul=nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';links.new(attribute.outputs['Color'],mul.inputs[0]);links.new(light.outputs['Is Shadow Ray'],mul.inputs[1])
transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');links.new(mul.outputs[0],mix.inputs[0]);links.new(old,mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
under=bpy.data.objects.get('APJ_v5_Skin_Transition_Underlay')
if under:under.visible_shadow=False
print('Overlap-only shadow correction applied at',len(ids),'boundary vertices')
