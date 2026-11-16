"""Blend reconstructed facial edges into the v3 source using sampled vertex color."""
import bpy,numpy as np,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
face=bpy.data.objects['APJ_Face'];source=bpy.data.objects['SOURCE_Before_Facial_v4']
source.hide_set(False);sub=next(m for m in source.modifiers if m.type=='SUBSURF');was=sub.show_viewport;sub.show_viewport=True;sub.levels=2;bpy.context.view_layer.update()
ev=source.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());me.calc_loop_triangles()
vertices=[v.co.copy() for v in me.vertices];tris=list(me.loop_triangles);bv=BVHTree.FromPolygons(vertices,[t.vertices[:] for t in tris],all_triangles=True)
uv=me.uv_layers[0].data;image=bpy.data.images['APJ_v3_Baked_Albedo_4K'];w,h=image.size
pixels=np.array(image.pixels[:],dtype=np.float32).reshape(h,w,4)
values=[]
for v in face.data.vertices:
    p=v.co;width=float(np.interp(p.z,[1.407,1.425,1.45,1.49,1.525,1.555,1.595],[.039,.058,.077,.085,.081,.071,.061]))
    edge=max(max(0,min(1,(abs(p.x)/width-.76)/.16)),max(0,min(1,(1.423-p.z)/.013)),max(0,min(1,(p.z-1.581)/.012)))
    hit,normal,index,distance=bv.ray_cast(Vector((p.x,-.6,p.z)),Vector((0,1,0)))
    color=(.42,.24,.14)
    if hit is not None:
        t=tris[index];a,b,c=[vertices[i] for i in t.vertices];coords=[Vector((*uv[i].uv,0)) for i in t.loops]
        q=barycentric_transform(hit,a,b,c,*coords);ix=max(0,min(w-1,int(q.x*(w-1))));iy=max(0,min(h-1,int(q.y*(h-1))));rgb=pixels[iy,ix,:3]
        color=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    values.append((*color,edge))
ev.to_mesh_clear();sub.show_viewport=was;source.hide_set(True)
attr=face.data.color_attributes.new(name='FacialEdgeBlend',type='FLOAT_COLOR',domain='CORNER')
for p in face.data.polygons:
    for li in p.loop_indices:attr.data[li].color=values[face.data.loops[li].vertex_index]
mat=face.data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');old=bs.inputs['Base Color'].links[0].from_socket
vertex=nodes.new('ShaderNodeVertexColor');vertex.layer_name='FacialEdgeBlend'
mix=nodes.new('ShaderNodeMixRGB');links.new(vertex.outputs['Alpha'],mix.inputs[0]);links.new(old,mix.inputs[1]);links.new(vertex.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color'])
print('Face overlap color matched to original UV texture')
