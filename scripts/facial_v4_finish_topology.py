"""Concealed overlap skirt and conservative eyelid-to-cornea clearance."""
import bpy,bmesh,math,json
face=bpy.data.objects['APJ_Face'];mesh=face.data;eyes=json.loads(face['eye_info']);tags=json.loads(face['boundary_tags'])
for v in mesh.vertices:
    for h in eyes.values():
        radius=h['radius']+.00014;disc=radius*radius-(v.co.x-h['x'])**2-(v.co.z-h['z'])**2
        if disc>0:v.co.y=min(v.co.y,h['cy']-math.sqrt(disc)-.00085)
uvdata=mesh.uv_layers[0].data;uvs={mesh.loops[li].vertex_index:uvdata[li].uv.copy() for p in mesh.polygons for li in p.loop_indices}
verts=[v.co.copy() for v in mesh.vertices];faces=[list(p.vertices) for p in mesh.polygons]
sets=[set(ids) for ids in tags.values()];bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();newindices={}
def skirt(index):
    if index in newindices:return newindices[index]
    p=verts[index].copy()
    if p.z<1.410:p.z-=.003
    elif p.z>1.592:p.z+=.003
    else:p.x+=math.copysign(.0035,p.x)
    p.y+=.004
    i=len(verts);verts.append(p);uvs[i]=((p.x/.30+.5),(p.z-1.52)/.30+.5);newindices[index]=i;return i
for edge in bm.edges:
    if len(edge.link_faces)!=1:continue
    a,b=[v.index for v in edge.verts]
    if any(a in ids and b in ids for ids in sets):continue
    loop=next(loop for loop in edge.link_faces[0].loops if loop.edge==edge)
    a=loop.vert.index;b=loop.link_loop_next.vert.index
    faces.append([b,a,skirt(a),skirt(b)])
bm.free()
new=bpy.data.meshes.new('APJ_Deformation_Face_Quads_SeamSkirt');new.from_pydata(verts,[],faces);new.update()
for mat in mesh.materials:new.materials.append(mat)
for name in ['UVMap','FaceProjection']:
    uv=new.uv_layers.new(name=name)
    for p in new.polygons:
        p.use_smooth=True
        for li in p.loop_indices:uv.data[li].uv=uvs[new.loops[li].vertex_index]
new.uv_layers.active_index=0;new.uv_layers[0].active_render=True;face.data=new
face.vertex_groups.clear();group=face.vertex_groups.new(name='Head');group.add(list(range(len(verts))),1,'REPLACE')
face['overlap_skirt_vertices']=len(newindices)
print('Concealed facial edge overlap:',len(newindices),'vertices; corneal clearance adjusted')
