"""Save cinematic master and a standard-PBR export using baked UV textures."""
import bpy,os,json
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;body=bpy.data.objects['char1'];rig=bpy.data.objects['Armature']
images={name:bpy.data.images['APJ_v3_Baked_'+name+'_4K'] for name in ['Albedo','Roughness','Normal']}
for image in bpy.data.images:
    if image.source=='FILE' and image.has_data and not image.packed_file:image.pack()
for filename in ['appearance_v3.py','bake_appearance_v3.py','stabilize_appearance_v3.py','render_appearance_v3_review.py','deliver_appearance_v3.py']:
    text=bpy.data.texts.get(filename)
    if text:bpy.data.texts.remove(text)
    bpy.data.texts.load(os.path.join(ROOT,'scripts',filename))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','apj_appearance_v3_master.blend'))

copy=body.copy();copy.data=body.data.copy();copy.name='APJ_Appearance_v3_Body';s.collection.objects.link(copy)
# The master uses this attribute as a wrinkle mask; it must not become glTF
# base-color vertex tint, which would black out the rest of the body.
for attribute in list(copy.data.color_attributes):copy.data.color_attributes.remove(attribute)
material_indices=[p.material_index for p in copy.data.polygons]
copy.data.materials.clear()
for kind in ['Head','Fabric','Leather']:
    mat=bpy.data.materials.new('APJ_v3_Export_'+kind);mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map=copy.data.uv_layers[0].name
    for mapname,inputname in [('Albedo','Base Color'),('Roughness','Roughness')]:
        n=nodes.new('ShaderNodeTexImage');n.image=images[mapname];links.new(uv.outputs[0],n.inputs['Vector']);links.new(n.outputs['Color'],bs.inputs[inputname])
    n=nodes.new('ShaderNodeTexImage');n.image=images['Normal'];links.new(uv.outputs[0],n.inputs['Vector'])
    normal=nodes.new('ShaderNodeNormalMap');links.new(n.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs[0],bs.inputs['Normal'])
    if kind=='Fabric':bs.inputs['Sheen Weight'].default_value=.12
    if kind=='Leather':bs.inputs['Coat Weight'].default_value=.24;bs.inputs['Coat Roughness'].default_value=.20
    copy.data.materials.append(mat)
for poly,index in zip(copy.data.polygons,material_indices):poly.material_index=index
bpy.ops.object.select_all(action='DESELECT')
selected=[rig,copy]+[o for o in s.objects if o.name.startswith('APJ_Hand_') or o.name.startswith('APJ_Nail_')]
for o in selected:o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'exports','apj_appearance_v3.glb'),use_selection=True,export_apply=False,export_animations=False,export_all_influences=True)
bpy.data.objects.remove(copy,do_unlink=True)
report={'blend':'blender/apj_appearance_v3_master.blend','glb':'exports/apj_appearance_v3.glb',
 'baked_maps':{key:{'size':list(im.size),'path':im.filepath} for key,im in images.items()},
 'generated_source_resolution':[1254,1254],'generator':'built-in image_gen',
 'hair_strands':len(bpy.data.objects['APJ_v3_Fine_Hair_Strands'].data.splines),
 'bones':len(rig.data.bones),'facial_prototype_targets':len(body.data.shape_keys.key_blocks)-1,
 'missing_textures':[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath))],
 'export_exclusions':['Cinematic fine hair curves','Transparent corneal reflection overlays','Procedural dynamic wrinkle driver'],
 'limitations':['Generated appearance reconstruction, not measured scan data','Single frontal source; side/back retain original atlas detail','Coarse existing facial geometry limits likeness','Corneal layers do not implement separate eye rotation or eyelid rig','No claim of native 4K generated detail','Neutral rigged export has no animation clips']}
with open(os.path.join(ROOT,'tests','appearance_v3.json'),'w') as f:json.dump(report,f,indent=2)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','apj_appearance_v3_master.blend'))
print('Appearance v3 master and standard-PBR GLB saved')
