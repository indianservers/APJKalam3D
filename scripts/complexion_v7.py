"""Deeper golden-brown reference complexion, without cool/ashy fill light."""
import bpy,json,os
ROOT=r'C:\Abdul Kalam';done=set();changes=[]
for name in ['APJ_Face','APJ_v5_Skin_Transition_Underlay','APJ_Hand_Left','APJ_Hand_Right','char1']:
    obj=bpy.data.objects.get(name)
    if not obj:continue
    for mat in obj.data.materials[:1]:
        if mat in done:continue
        done.add(mat)
        for node in mat.node_tree.nodes:
            if node.type=='MIX_RGB' and node.label=='V6 warm medium-brown reference complexion':
                node.inputs[2].default_value=(.46,.37,.26,1);node.label='V7 deeper golden-brown reference complexion'
            elif node.type=='HUE_SAT' and node.label=='V6 restrained skin saturation':node.inputs['Saturation'].default_value=1.02
            elif node.type=='BSDF_PRINCIPLED' and (name!='char1' or node.label.startswith('Aged skin')):
                node.inputs['Specular IOR Level'].default_value=.20;node.inputs['Subsurface Weight'].default_value=.055
                if not node.inputs['Roughness'].is_linked:node.inputs['Roughness'].default_value=.54
        nodes=mat.node_tree.nodes;links=mat.node_tree.links
        tone=next((n for n in nodes if n.type=='MIX_RGB' and n.label=='V7 deeper golden-brown reference complexion'),None)
        if tone:
            sat=tone.inputs[1].links[0].from_node;original=sat.inputs['Color'].links[0].from_socket
            split=nodes.new('ShaderNodeSeparateColor');links.new(original,split.inputs[0])
            difference=nodes.new('ShaderNodeMath');difference.operation='SUBTRACT';links.new(split.outputs['Red'],difference.inputs[0]);links.new(split.outputs['Blue'],difference.inputs[1])
            mask=nodes.new('ShaderNodeMapRange');mask.clamp=True;mask.inputs['From Min'].default_value=.06;mask.inputs['From Max'].default_value=.20;links.new(difference.outputs[0],mask.inputs['Value'])
            mix=nodes.new('ShaderNodeMixRGB');mix.label='V7 skin-only complexion mask';links.new(mask.outputs[0],mix.inputs[0]);links.new(original,mix.inputs[1]);links.new(tone.outputs[0],mix.inputs[2])
            for link in list(tone.outputs[0].links):
                if link.to_node!=mix:links.new(mix.outputs[0],link.to_socket)
        changes.append(mat.name)
for name,color,power in [('Studio_Key',(1,.93,.84),190),('Studio_Fill',(.95,.90,.83),60),('Studio_Rim',(.94,.94,.92),130)]:
    obj=bpy.data.objects.get(name)
    if obj:obj.data.color=color;obj.data.energy=power
report={'appearance_target':'Deeper golden-brown complexion from the supplied individual reference','linear_skin_multiplier':[.46,.37,.26],
 'skin_saturation':1.02,'specular_level':.20,'subsurface_weight':.055,'materials':changes,
 'lighting':'Warm-neutral fill replacing blue fill; softer rim','eye_color':'Dark brown, retained from v6','geometry_and_controls_changed':False}
json.dump(report,open(os.path.join(ROOT,'tests','complexion_v7.json'),'w'),indent=2)
bpy.data.texts.load(os.path.join(ROOT,'scripts','complexion_v7.py'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','apj_complexion_v7_master.blend'))
print('Deeper golden-brown materials and warm-neutral lighting saved')
