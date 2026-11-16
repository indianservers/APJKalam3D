"""Appearance upgrade for the existing APJ hands-v2 model.
Generated projection is a texture source, not the final Blender beauty render.
"""
import bpy,math,os,random,json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=r'C:\Abdul Kalam';TEX=os.path.join(ROOT,'textures','appearance_v3')
m=bpy.data.objects['char1'];rig=bpy.data.objects['Armature'];s=bpy.context.scene
if m.get('appearance_v3'):raise RuntimeError('Appearance v3 already installed')
source=bpy.data.images['BakedMaterial_baseColor.png']
face=bpy.data.images.load(os.path.join(TEX,'apj_face_projection_generated.png'),check_existing=True);face.pack()
uv=m.data.uv_layers.get('FaceProjection') or m.data.uv_layers.new(name='FaceProjection')
for p in m.data.polygons:
    for li in p.loop_indices:
        co=m.data.vertices[m.data.loops[li].vertex_index].co
        uv.data[li].uv=(co.x/.30+.5,(co.z-1.52)/.30+.5)

def material(name):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial')
    return mat,nodes,mat.node_tree.links,out
def mathnode(nodes,links,operation,a,b=None):
    n=nodes.new('ShaderNodeMath');n.operation=operation
    for i,x in enumerate([a,b]):
        if x is None:continue
        if isinstance(x,(int,float)):n.inputs[i].default_value=x
        else:links.new(x,n.inputs[i])
    return n.outputs[0]
def texnode(nodes,links,image,uvname='UVMap'):
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map=uvname
    n=nodes.new('ShaderNodeTexImage');n.image=image;links.new(uv.outputs['UV'],n.inputs['Vector']);return n
original_uv=m.data.uv_layers[0].name

# One head material blends two different BRDFs by source skin pigmentation.
# This avoids hard triangle-boundary material changes at hair and brows.
head,n,l,out=material('APJ_v3_Head_Skin_And_Silver_Hair')
old=texnode(n,l,source,original_uv);projected=texnode(n,l,face,'FaceProjection')
projected.extension='EXTEND'
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0])
blend=mathnode(n,l,'MULTIPLY_ADD',sep.outputs['Y'],-22.)
# Front projection fades to original atlas around the sides and back.
blend.node.inputs[2].default_value=-.15
blend=mathnode(n,l,'MAXIMUM',blend,0);blend=mathnode(n,l,'MINIMUM',blend,1)
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';l.new(blend,mix.inputs[0]);l.new(old.outputs['Color'],mix.inputs[1]);l.new(projected.outputs['Color'],mix.inputs[2])
skin=n.new('ShaderNodeBsdfPrincipled');skin.label='Aged skin: SSS, variable roughness, pore normal'
l.new(mix.outputs[0],skin.inputs['Base Color']);skin.inputs['IOR'].default_value=1.40
skin.inputs['Subsurface Weight'].default_value=.10;skin.inputs['Subsurface Scale'].default_value=.0011
skin.inputs['Subsurface Radius'].default_value=(1,.46,.23);skin.inputs['Specular IOR Level'].default_value=.32
coord=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1900;noise.inputs['Detail'].default_value=2.2;noise.inputs['Roughness'].default_value=.72
l.new(coord.outputs['Object'],noise.inputs['Vector'])
rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=.2;rough.inputs['From Max'].default_value=.8;rough.inputs['To Min'].default_value=.40;rough.inputs['To Max'].default_value=.58
l.new(noise.outputs['Fac'],rough.inputs['Value']);l.new(rough.outputs[0],skin.inputs['Roughness'])
pore=n.new('ShaderNodeBump');pore.inputs['Strength'].default_value=.15;pore.inputs['Distance'].default_value=.000035;l.new(noise.outputs['Fac'],pore.inputs['Height'])

# Restrained forehead detail, smoothly masked and driven by the existing brows.
def gauss(socket,center,width):
    a=mathnode(n,l,'SUBTRACT',socket,center);a=mathnode(n,l,'DIVIDE',a,width);a=mathnode(n,l,'MULTIPLY',a,a)
    a=mathnode(n,l,'MULTIPLY',a,-1);return mathnode(n,l,'EXPONENT',a)
mask=mathnode(n,l,'MULTIPLY',gauss(sep.outputs['X'],0,.047),gauss(sep.outputs['Z'],1.568,.020))
mask=mathnode(n,l,'MULTIPLY',mask,mathnode(n,l,'LESS_THAN',sep.outputs['Y'],-.065))
line=mathnode(n,l,'MULTIPLY',sep.outputs['Z'],700);line=mathnode(n,l,'SINE',line)
height=mathnode(n,l,'MULTIPLY',mask,line)
wrinkle=n.new('ShaderNodeBump');wrinkle.label='Animated fine forehead detail';wrinkle.inputs['Distance'].default_value=.00012
l.new(height,wrinkle.inputs['Height']);l.new(pore.outputs['Normal'],wrinkle.inputs['Normal']);l.new(wrinkle.outputs['Normal'],skin.inputs['Normal'])
driver=wrinkle.inputs['Strength'].driver_add('default_value').driver
for name,key in [('a','browInnerUp'),('b','browOuterUpLeft'),('c','browOuterUpRight')]:
    var=driver.variables.new();var.name=name;var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=m.data.shape_keys;var.targets[0].data_path=f'key_blocks["{key}"].value'
driver.expression='.08+.18*max(a,b,c)'
hair=n.new('ShaderNodeBsdfPrincipled');hair.label='Silver hair surface under strand geometry'
l.new(mix.outputs[0],hair.inputs['Base Color']);hair.inputs['Roughness'].default_value=.39;hair.inputs['Anisotropic'].default_value=.50
hair.inputs['Specular IOR Level'].default_value=.38
rgb=n.new('ShaderNodeSeparateColor');l.new(old.outputs['Color'],rgb.inputs[0])
pigment=mathnode(n,l,'SUBTRACT',rgb.outputs['Red'],rgb.outputs['Green']);pigment=mathnode(n,l,'MULTIPLY',pigment,12.)
pigment=mathnode(n,l,'MAXIMUM',pigment,0);pigment=mathnode(n,l,'MINIMUM',pigment,1)
blendshader=n.new('ShaderNodeMixShader');l.new(pigment,blendshader.inputs[0]);l.new(hair.outputs[0],blendshader.inputs[1]);l.new(skin.outputs[0],blendshader.inputs[2]);l.new(blendshader.outputs[0],out.inputs['Surface'])

cloth,n,l,out=material('APJ_v3_Bandhgala_Fine_Woven_Fabric')
bs=n.new('ShaderNodeBsdfPrincipled');old=texnode(n,l,source,original_uv)
color=n.new('ShaderNodeMixRGB');color.blend_type='MULTIPLY';color.inputs[0].default_value=.35;color.inputs[2].default_value=(.79,.73,.64,1);l.new(old.outputs['Color'],color.inputs[1]);l.new(color.outputs[0],bs.inputs['Base Color'])
bs.inputs['Roughness'].default_value=.77;bs.inputs['Specular IOR Level'].default_value=.22;bs.inputs['Sheen Weight'].default_value=.22;bs.inputs['Sheen Roughness'].default_value=.6
coord=n.new('ShaderNodeTexCoord');waves=[]
for direction in ['X','Y']:
    wave=n.new('ShaderNodeTexWave');wave.bands_direction=direction;wave.inputs['Scale'].default_value=2200;wave.inputs['Distortion'].default_value=.4;l.new(coord.outputs['Object'],wave.inputs['Vector']);waves.append(wave.outputs['Color'])
weave=mathnode(n,l,'MULTIPLY',waves[0],waves[1]);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.000025;l.new(weave,bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal']);l.new(bs.outputs[0],out.inputs['Surface'])

leather,n,l,out=material('APJ_v3_Black_Polished_Leather')
bs=n.new('ShaderNodeBsdfPrincipled');old=texnode(n,l,source,original_uv);l.new(old.outputs['Color'],bs.inputs['Base Color'])
bs.inputs['Roughness'].default_value=.27;bs.inputs['Specular IOR Level'].default_value=.42;bs.inputs['Coat Weight'].default_value=.24;bs.inputs['Coat Roughness'].default_value=.20
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1500;noise.inputs['Detail'].default_value=2
coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Object'],noise.inputs['Vector'])
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.10;bump.inputs['Distance'].default_value=.000035;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal']);l.new(bs.outputs[0],out.inputs['Surface'])

m.data.materials.clear()
for mat in [head,cloth,leather]:m.data.materials.append(mat)
for p in m.data.polygons:
    p.material_index=0 if p.center.z>1.410 else 2 if p.center.z<.115 else 1
    p.use_smooth=True

# Thin transparent corneal reflection surfaces retain the painted iris layout.
# These improve shading; they do not implement separate rotating eyeballs.
cornea,n,l,out=material('APJ_v3_Corneal_Reflection_Layer')
trans=n.new('ShaderNodeBsdfTransparent');gloss=n.new('ShaderNodeBsdfAnisotropic');gloss.inputs['Roughness'].default_value=.025
fres=n.new('ShaderNodeFresnel');fres.inputs['IOR'].default_value=1.376
mix=n.new('ShaderNodeMixShader');l.new(fres.outputs[0],mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(gloss.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
deps=bpy.context.evaluated_depsgraph_get();bvh=BVHTree.FromObject(m,deps)
for side,x in [('Left',.0347),('Right',-.0345)]:
    verts=[];faces=[]
    for i in range(9):
      for j in range(13):
        a=i/8*2-1;b=j/12*2-1
        xx=x+b*.0063;zz=1.5148+a*.0036*math.sqrt(max(.04,1-b*b))
        hit,norm,_,dist=bvh.ray_cast(Vector((xx,-.5,zz)),Vector((0,1,0)))
        if hit is None:hit=Vector((xx,-.085,zz))
        verts.append((xx,hit.y-.00018-.00045*(1-a*a)*(1-b*b),zz))
    for i in range(8):
      for j in range(12):faces.append((i*13+j,i*13+j+1,(i+1)*13+j+1,(i+1)*13+j))
    mesh=bpy.data.meshes.new('Cornea_'+side);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new('APJ_Cornea_'+side,mesh);s.collection.objects.link(o);mesh.materials.append(cornea)
    for p in mesh.polygons:p.use_smooth=True
    group=o.vertex_groups.new(name='Head');group.add(list(range(len(verts))),1,'REPLACE');mod=o.modifiers.new('Head attachment','ARMATURE');mod.object=rig;o.parent=rig

# Fine geometry strands follow the existing hair envelope, with slight flyaways.
rng=random.Random(2045)
hairmats=[]
for i,col in enumerate([(.33,.32,.30,1),(.53,.51,.48,1),(.22,.215,.21,1),(.68,.67,.64,1)]):
    mat,n,l,out=material('APJ_v3_Silver_Strand_'+str(i));bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=col;bs.inputs['Roughness'].default_value=.34;bs.inputs['Anisotropic'].default_value=.65;l.new(bs.outputs[0],out.inputs['Surface']);hairmats.append(mat)
curve=bpy.data.curves.new('APJ_Fine_Hair_Strands','CURVE');curve.dimensions='3D';curve.resolution_u=2;curve.bevel_depth=.000035;curve.bevel_resolution=1
for mat in hairmats:curve.materials.append(mat)
fw,fh=face.size;facepixels=np.array(face.pixels[:],dtype=np.float32).reshape(fh,fw,4)
for side in [-1,1]:
  for index in range(330):
    depth=rng.uniform(-.055,.080);spread=rng.uniform(.72,1.10);phase=rng.uniform(0,math.tau)
    points=[]
    for j in range(24):
        t=j/23
        x=side*(.004+.099*math.sin(t*math.pi*.70))*spread
        z=1.638-.215*t**1.14
        y=depth+.016*math.sin(t*math.pi)+.012*t
        desired=Vector((x,y,z));near,normal,faceidx,distance=bvh.find_nearest(desired)
        if near is None:continue
        # Avoid laying a strand across facial skin at the frontal centre.
        if near.y<-.065 and abs(near.x)<.068 and near.z<1.59:continue
        pu=max(0,min(fw-1,int((near.x/.30+.5)*(fw-1))));pv=max(0,min(fh-1,int(((near.z-1.52)/.30+.5)*(fh-1))))
        color=facepixels[pv,pu,:3]
        if near.y<.04 and near.z<1.61 and color[0]-color[1]>.05 and color[1]-color[2]>.025:break
        offset=.00030+.00024*math.sin(phase+t*18)+(.0012*t*t if index%16==0 else 0)
        point=near+normal*max(.0001,offset);points.append(point)
    if len(points)<5:continue
    spline=curve.splines.new('POLY');spline.points.add(len(points)-1);spline.material_index=rng.randrange(len(hairmats))
    for j,(p,co) in enumerate(zip(spline.points,points)):
        p.co=(*co,1);p.radius=.35+.65*math.sin(math.pi*(j+.5)/len(points))**.35
hair_obj=bpy.data.objects.new('APJ_v3_Fine_Hair_Strands',curve);s.collection.objects.link(hair_obj)
# Rigid head attachment preserves the existing rest transform.
hair_obj.parent=rig;hair_obj.parent_type='BONE';hair_obj.parent_bone='Head';hair_obj.matrix_world.identity()

# Use controlled lighting to expose material response without bleaching skin.
for name,power in [('Studio_Key',190),('Studio_Fill',70),('Studio_Rim',180)]:
    if bpy.data.objects.get(name):bpy.data.objects[name].data.energy=power
s.cycles.samples=64;s.cycles.use_denoising=True
m['appearance_v3']=True
print('Installed v3 projected skin, pore/wrinkle response, cloth/leather shaders, corneal reflections and',len(curve.splines),'fine hair strands')
