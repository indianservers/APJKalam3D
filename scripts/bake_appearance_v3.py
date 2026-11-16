"""Bake procedural appearance and front projection into the original UV atlas."""
import bpy,os
ROOT=r'C:\Abdul Kalam';OUT=os.path.join(ROOT,'textures','appearance_v3');m=bpy.data.objects['char1'];s=bpy.context.scene
bpy.ops.object.select_all(action='DESELECT');m.select_set(True);bpy.context.view_layer.objects.active=m
m.data.uv_layers.active_index=0
for i,uv in enumerate(m.data.uv_layers):uv.active_render=(i==0)
s.render.bake.use_selected_to_active=False;s.render.bake.use_cage=False;s.render.bake.margin=16
def target(name,color):
    im=bpy.data.images.new(name,width=4096,height=4096,alpha=False)
    if not color:im.colorspace_settings.name='Non-Color'
    for mat in m.data.materials:
        n=mat.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;mat.node_tree.nodes.active=n
        for node in mat.node_tree.nodes:node.select=(node==n)
    return im
def save(im):
    im.filepath_raw=os.path.join(OUT,im.name+'.png');im.file_format='PNG';im.save();im.pack()
    print('Saved',im.filepath_raw)
color=target('APJ_v3_Baked_Albedo_4K',True);restore=[]
for mat in m.data.materials:
    n=mat.node_tree.nodes;l=mat.node_tree.links;out=next(x for x in n if x.type=='OUTPUT_MATERIAL');old=out.inputs['Surface'].links[0].from_socket
    bs=next(x for x in n if x.type=='BSDF_PRINCIPLED')
    socket=bs.inputs['Base Color'].links[0].from_socket
    em=n.new('ShaderNodeEmission');l.new(socket,em.inputs['Color']);l.new(em.outputs[0],out.inputs['Surface']);restore.append((mat,out,old,em))
bpy.ops.object.bake(type='EMIT');save(color)
for mat,out,old,em in restore:mat.node_tree.links.new(old,out.inputs['Surface']);mat.node_tree.nodes.remove(em)
rough=target('APJ_v3_Baked_Roughness_4K',False);bpy.ops.object.bake(type='ROUGHNESS');save(rough)
normal=target('APJ_v3_Baked_Normal_4K',False);s.render.bake.normal_space='TANGENT';bpy.ops.object.bake(type='NORMAL');save(normal)
# Use the baked albedo in the cinematic material, so facial texture registration
# follows the UVs for all future deformations rather than object-space projection.
head=m.data.materials[0];n=head.node_tree.nodes;l=head.node_tree.links
uv=n.new('ShaderNodeUVMap');uv.uv_map=m.data.uv_layers[0].name
tex=n.new('ShaderNodeTexImage');tex.image=color;l.new(uv.outputs['UV'],tex.inputs['Vector'])
for bs in [x for x in n if x.type=='BSDF_PRINCIPLED']:l.new(tex.outputs['Color'],bs.inputs['Base Color'])
# Tone the original hand atlas toward the new face complexion.
handmat=bpy.data.objects['APJ_Hand_Left'].data.materials[0]
nodes=handmat.node_tree.nodes;links=handmat.node_tree.links;bs=next(x for x in nodes if x.type=='BSDF_PRINCIPLED')
old=bs.inputs['Base Color'].links[0].from_socket
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(.88,.79,.70,1);links.new(old,mix.inputs[1]);links.new(mix.outputs[0],bs.inputs['Base Color'])
print('Three 4K UV maps baked; generated source projection is 1254px, not native 4K detail')
