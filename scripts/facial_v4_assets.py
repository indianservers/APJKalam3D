"""Actual eye globes, corneas and mouth interior bound to facial bones."""
import bpy,math,json
from mathutils import Vector
face=bpy.data.objects['APJ_Face'];rig=bpy.data.objects['Armature'];s=bpy.context.scene
eyes=json.loads(face['eye_info']);mz=face['mouth_center_z']
def mat(name,color,rough=.5):
    m=bpy.data.materials.new(name);m.use_nodes=True;b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;return m,b
def bind(o,bone):
    o.data.materials.clear()
    o.parent=rig
    g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE')
    mod=o.modifiers.new('Facial bone binding','ARMATURE');mod.object=rig
def bone_parent(o,bone):
    world=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;o.matrix_world=world
def mathnode(n,l,op,a,b=None):
    node=n.new('ShaderNodeMath');node.operation=op
    for i,x in enumerate([a,b]):
        if x is None:continue
        if isinstance(x,(int,float)):node.inputs[i].default_value=x
        else:l.new(x,node.inputs[i])
    return node.outputs[0]
eye_mat,bs=mat('APJ_v4_Sclera_Brown_Iris',(.68,.66,.59),.32);n=eye_mat.node_tree.nodes;l=eye_mat.node_tree.links
tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Object'],sep.inputs[0])
x=sep.outputs['X'];y=sep.outputs['Y'];z=sep.outputs['Z']
rad=mathnode(n,l,'SQRT',mathnode(n,l,'ADD',mathnode(n,l,'MULTIPLY',x,x),mathnode(n,l,'MULTIPLY',z,z)))
angle=mathnode(n,l,'ARCTAN2',z,x);fiber=mathnode(n,l,'SINE',mathnode(n,l,'MULTIPLY',angle,139))
fiber=mathnode(n,l,'MULTIPLY_ADD',fiber,.35);fiber.node.inputs[2].default_value=.5
colors=n.new('ShaderNodeMixRGB');colors.inputs[1].default_value=(.045,.014,.004,1);colors.inputs[2].default_value=(.19,.085,.024,1);l.new(fiber,colors.inputs[0])
front=mathnode(n,l,'LESS_THAN',y,0);iris=mathnode(n,l,'MULTIPLY',mathnode(n,l,'LESS_THAN',rad,.0056),front)
mix=n.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.68,.66,.59,1);l.new(colors.outputs[0],mix.inputs[2]);l.new(iris,mix.inputs[0])
limbus=mathnode(n,l,'MULTIPLY',mathnode(n,l,'GREATER_THAN',rad,.0051),iris)
edge=n.new('ShaderNodeMixRGB');l.new(mix.outputs[0],edge.inputs[1]);edge.inputs[2].default_value=(.018,.010,.005,1);l.new(limbus,edge.inputs[0])
pupil=mathnode(n,l,'MULTIPLY',mathnode(n,l,'LESS_THAN',rad,.0019),front)
pm=n.new('ShaderNodeMixRGB');l.new(edge.outputs[0],pm.inputs[1]);pm.inputs[2].default_value=(.001,.0007,.0004,1);l.new(pupil,pm.inputs[0]);l.new(pm.outputs[0],bs.inputs['Base Color'])
bs.inputs['Specular IOR Level'].default_value=.25
cornea,cb=mat('APJ_v4_Clear_Cornea',(1,1,1),.025);cb.inputs['IOR'].default_value=1.376;cb.inputs['Transmission Weight'].default_value=1
for side,h in eyes.items():
    center=(h['x'],h['cy'],h['z']);bone='Eye.'+side[0]
    for suffix,radius,material in [('Globe',h['radius'],eye_mat),('Cornea',h['radius']+.00014,cornea)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=radius,location=center)
        o=bpy.context.object;o.name='APJ_Eye_'+side+'_'+suffix;o.data.materials.append(material)
        for p in o.data.polygons:p.use_smooth=True
        bone_parent(o,bone)

cavity,cb=mat('APJ_v4_Mouth_Cavity',(.018,.0025,.003),.70)
gum,gb=mat('APJ_v4_Gingiva',(.20,.025,.022),.46);gb.inputs['Subsurface Weight'].default_value=.12;gb.inputs['Subsurface Scale'].default_value=.001;gb.inputs['Coat Weight'].default_value=.1
teeth,tb=mat('APJ_v4_Tooth_Enamel',(.62,.55,.42),.28);tb.inputs['IOR'].default_value=1.5;tb.inputs['Coat Weight'].default_value=.15
tongue,tb=mat('APJ_v4_Tongue',(.27,.040,.038),.43);tb.inputs['Subsurface Weight'].default_value=.1;tb.inputs['Subsurface Scale'].default_value=.001;tb.inputs['Coat Weight'].default_value=.12
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=1,location=(0,-.05,mz-.006))
o=bpy.context.object;o.name='APJ_Mouth_Interior';o.scale=(.038,.035,.030);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
o.parent=rig;o.data.materials.append(cavity);head=o.vertex_groups.new(name='Head');jaw=o.vertex_groups.new(name='Jaw')
for v in o.data.vertices:
    worldz=v.co.z+o.location.z;w=max(0,min(1,(mz-worldz)/.014));head.add([v.index],1-w,'REPLACE');jaw.add([v.index],w,'REPLACE')
for p in o.data.polygons:p.use_smooth=True
mod=o.modifiers.new('Mouth cavity deformation','ARMATURE');mod.object=rig
for arch,bone,zcenter,yradius in [('Upper','Head',mz-.0035,.020),('Lower','Jaw',mz-.0085,.017)]:
    for i in range(14):
        theta=(i-6.5)/6.5*1.37;x=.025*math.sin(theta);y=-.069-yradius*math.cos(theta)
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,zcenter))
        tooth=bpy.context.object;tooth.name=f'APJ_Teeth_{arch}_{i+1:02d}';tooth.scale=(.0059 if abs(theta)<.5 else .0050,.0040,.0072 if arch=='Upper' else .0063);tooth.rotation_euler.z=-theta
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        bind(tooth,bone);tooth.data.materials.append(teeth)
        bevel=tooth.modifiers.new('Rounded enamel edges','BEVEL');bevel.width=.0008;bevel.segments=3
        for p in tooth.data.polygons:p.use_smooth=True
    # A shallow gum arch behind the enamel roots.
    curve=bpy.data.curves.new('Gum_Arch_'+arch,'CURVE');curve.dimensions='3D';curve.bevel_depth=.0024;curve.bevel_resolution=3
    spline=curve.splines.new('POLY');spline.points.add(39)
    for i,p in enumerate(spline.points):
        theta=-1.43+2.86*i/39;p.co=(.025*math.sin(theta),-.069-yradius*math.cos(theta),zcenter+(.004 if arch=='Upper' else -.0036),1)
    o=bpy.data.objects.new('APJ_Gum_'+arch,curve);s.collection.objects.link(o)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
    bind(o,bone);o.data.materials.append(gum)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=1,location=(0,-.057,mz-.016))
o=bpy.context.object;o.name='APJ_Tongue';o.scale=(.017,.021,.0045);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bind(o,'Jaw');o.data.materials.append(tongue)
for p in o.data.polygons:p.use_smooth=True
print('Created real eye globes/corneas, mouth cavity, 28 teeth, gums and tongue')
