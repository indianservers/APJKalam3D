"""Facial surface reconstruction with quad loops and true eye/mouth openings.
Run on appearance-v3. Keeps a hidden source copy and never overwrites v3.
"""
import bpy,math,os,json
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=r'C:\Abdul Kalam';body=bpy.data.objects['char1'];rig=bpy.data.objects['Armature'];s=bpy.context.scene
if bpy.data.objects.get('APJ_Face'):raise RuntimeError('Facial v4 already installed')
s.frame_set(1)
if rig.animation_data:rig.animation_data.action=None
if body.data.shape_keys.animation_data:body.data.shape_keys.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for k in body.data.shape_keys.key_blocks:k.value=0
backup=body.copy();backup.data=body.data.copy();backup.name='SOURCE_Before_Facial_v4';s.collection.objects.link(backup);backup.hide_set(True);backup.hide_render=True
for o in bpy.data.objects:
    if o.name.startswith('APJ_Cornea_'):o.hide_set(True);o.hide_render=True
sub=next(mod for mod in body.modifiers if mod.type=='SUBSURF');sub.show_viewport=True;sub.levels=2;bpy.context.view_layer.update()
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
def surface(x,z):
    hit,normal,index,dist=bvh.ray_cast(Vector((x,-.60,z)),Vector((0,1,0)))
    return hit.copy() if hit is not None else Vector((x,-.07,z))
ZMIN=1.407;ZMAX=1.595;MZ=1.446
def width(z):return float(np.interp(z,[1.407,1.425,1.45,1.49,1.525,1.555,1.595],[.039,.058,.077,.085,.081,.071,.061]))
uvals=np.linspace(-1,1,81).tolist()
fixed=[1.5148+v for v in [-.007,-.0045,-.0022,0,.0022,.0045,.007]]+[MZ+v for v in [-.006,-.003,-.0015,0,.0015,.003,.006]]
zvals=sorted(set(fixed+[float(z) for z in np.linspace(ZMIN,ZMAX,103) if all(abs(z-f)>.00040 for f in fixed)]))
def nearest(values,x):return min(range(len(values)),key=lambda i:abs(values[i]-x))
holes=[]
for side,x in [('Left',.0347),('Right',-.0345)]:
    cu=x/width(1.5148);a=nearest(uvals,cu-.1375);b=nearest(uvals,cu+.1375);j0=nearest(zvals,1.5103);j1=nearest(zvals,1.5193)
    cy=surface(x,1.5148).y+.0117
    holes.append({'name':side,'x':x,'z':1.5148,'rx':.0108,'rz':.0035,'a':a,'b':b,'j0':j0,'j1':j1,'cu':(uvals[a]+uvals[b])/2,'ur':(uvals[b]-uvals[a])/2,'zr':(zvals[j1]-zvals[j0])/2,'cy':cy,'radius':.0120})
a=nearest(uvals,-.35);b=nearest(uvals,.35);j0=nearest(zvals,MZ-.0015);j1=nearest(zvals,MZ+.0015)
holes.append({'name':'Mouth','x':0,'z':MZ,'rx':.027,'rz':.00065,'a':a,'b':b,'j0':j0,'j1':j1,'cu':0,'ur':.35,'zr':.0015})
eyeinfo={h['name']:h for h in holes[:2]}

verts=[];uvs=[];tags=[];index={}
for j,z in enumerate(zvals):
 for i,u in enumerate(uvals):
    x=u*width(z);zz=z;boundary=None
    for h in holes:
        dx=(u-h['cu'])/h['ur'];dz=(z-h['z'])/h['zr'];rr=max(abs(dx),abs(dz))
        if rr<1e-6:continue
        if rr<=2.4:
            theta=math.atan2(dz,dx);bx=(h['cu']+h['ur']*dx/rr)*width(h['z']+h['zr']*dz/rr);bz=h['z']+h['zr']*dz/rr
            tx=h['x']+h['rx']*math.cos(theta);tz=h['z']+h['rz']*math.sin(theta)
            if h['name']!='Mouth':tz+=.00025*math.cos(theta)*(1 if h['name']=='Left' else -1)
            fade=max(0,min(1,(2.4-rr)/1.4))**2
            x+=(tx-bx)*fade;zz+=(tz-bz)*fade
        if (i in (h['a'],h['b']) and h['j0']<=j<=h['j1']) or (j in (h['j0'],h['j1']) and h['a']<=i<=h['b']):boundary=h['name']
    p=surface(x,zz);p.y-=.0006*min(1,max(0,(1-abs(u))/.14))
    # Eyelid margin sits on the eyeball envelope, blending into orbital skin.
    for h in holes[:2]:
        dx=x-h['x'];dz=zz-h['z'];rr=math.sqrt((dx/h['rx'])**2+(dz/.0045)**2)
        disc=h['radius']**2-dx*dx-dz*dz
        if disc>0:
            contact=h['cy']-math.sqrt(disc)-.00027
            p.y=min(p.y,contact)
    texz=zz
    # Sample adjacent skin on the lids; painted pupils belong inside the holes.
    for h in holes[:2]:
        rr=math.sqrt(((x-h['x'])/.013)**2+((zz-h['z'])/.006)**2)
        if rr<1.4:texz+=math.copysign(.0045*max(0,1-rr/1.4),zz-h['z'] if abs(zz-h['z'])>1e-7 else 1)
    index[i,j]=len(verts);verts.append(tuple(p));uvs.append((x/.30+.5,(texz-1.52)/.30+.5));tags.append(boundary)
faces=[]
for j in range(len(zvals)-1):
 for i in range(len(uvals)-1):
    if any(h['a']<=i<h['b'] and h['j0']<=j<h['j1'] for h in holes):continue
    faces.append((index[i,j],index[i+1,j],index[i+1,j+1],index[i,j+1]))
used=sorted({i for f in faces for i in f});remap={old:new for new,old in enumerate(used)}
verts=[verts[i] for i in used];uvs=[uvs[i] for i in used];tags=[tags[i] for i in used];faces=[tuple(remap[i] for i in f) for f in faces]
mesh=bpy.data.meshes.new('APJ_Deformation_Face_Quad_Surface');mesh.from_pydata(verts,[],faces);mesh.update();face=bpy.data.objects.new('APJ_Face',mesh);s.collection.objects.link(face)
for name in ['UVMap','FaceProjection']:
    uv=mesh.uv_layers.new(name=name)
    for p in mesh.polygons:
        p.use_smooth=True
        for li in p.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
mesh.uv_layers.active_index=0;mesh.uv_layers[0].active_render=True
group=face.vertex_groups.new(name='Head');group.add(list(range(len(verts))),1,'REPLACE');mod=face.modifiers.new('Head skin binding','ARMATURE');mod.object=rig
mod=face.modifiers.new('Facial surface smoothing','SUBSURF');mod.levels=1;mod.render_levels=1;face.parent=rig
face['eye_info']=json.dumps(eyeinfo);face['mouth_center_z']=MZ
face['topology_note']='Quad facial patch with eye and mouth apertures; outer seam concealed at source overlap, not welded to full head'
face['boundary_tags']=json.dumps({name:[i for i,t in enumerate(tags) if t==name] for name in ['Left','Right','Mouth']})

# Remove source front faces using edit-mode deletion, preserving legacy keys.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
selected=0
for p in body.data.polygons:
    p.select=all(ZMIN+.006<body.data.vertices[i].co.z<ZMAX-.006 and body.data.vertices[i].co.y<-.035 and abs(body.data.vertices[i].co.x)<width(body.data.vertices[i].co.z)*.84 for i in p.vertices)
    selected+=int(p.select)
bpy.ops.object.mode_set(mode='EDIT');bpy.context.tool_settings.mesh_select_mode=(False,False,True);bpy.ops.mesh.delete(type='ONLY_FACE');bpy.ops.object.mode_set(mode='OBJECT')
sub.show_viewport=False

# A face-only skin material uses the continuous frontal UV source.
mat=bpy.data.materials.new('APJ_v4_Facial_Skin');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links
bs=next(x for x in n if x.type=='BSDF_PRINCIPLED');bs.inputs['IOR'].default_value=1.40;bs.inputs['Subsurface Weight'].default_value=.09;bs.inputs['Subsurface Scale'].default_value=.0011;bs.inputs['Subsurface Radius'].default_value=(1,.46,.23);bs.inputs['Specular IOR Level'].default_value=.32;bs.inputs['Roughness'].default_value=.49
tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images['apj_face_projection_generated.png'];uv=n.new('ShaderNodeUVMap');uv.uv_map='UVMap';l.new(uv.outputs[0],tex.inputs['Vector']);l.new(tex.outputs['Color'],bs.inputs['Base Color'])
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=650;noise.inputs['Detail'].default_value=2;l.new(uv.outputs[0],noise.inputs['Vector'])
bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.000025;bump.inputs['Strength'].default_value=.13;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal']);mesh.materials.append(mat)

# Jaw and two eye bones, oriented with predictable local axes.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
jaw=rig.data.edit_bones.new('Jaw');jaw.head=(0,.005,1.471);jaw.tail=(0,.005,1.426);jaw.parent=rig.data.edit_bones['Head'];jaw.align_roll(Vector((0,1,0)))
for side,h in eyeinfo.items():
    eye=rig.data.edit_bones.new('Eye.'+side[0]);eye.head=(h['x'],h['cy'],h['z']);eye.tail=Vector(eye.head)+Vector((0,-.024,0));eye.parent=rig.data.edit_bones['Head'];eye.align_roll(Vector((0,0,1)))
bpy.ops.object.mode_set(mode='OBJECT')
print('Face reconstruction:',len(verts),'vertices,',len(faces),'quads; source faces removed:',selected)
