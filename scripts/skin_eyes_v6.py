"""Reference-guided warm brown complexion and dark brown iris material pass."""
import bpy,os,json
ROOT=r'C:\Abdul Kalam';scene=bpy.context.scene
if bpy.data.objects['APJ_Face'].get('skin_eyes_v6'):raise RuntimeError('Tone pass already applied')
def tone(mat,bs):
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;old=bs.inputs['Base Color'].links[0].from_socket
    sat=nodes.new('ShaderNodeHueSaturation');sat.label='V6 restrained skin saturation';sat.inputs['Saturation'].default_value=.90;links.new(old,sat.inputs['Color'])
    mul=nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.label='V6 warm medium-brown reference complexion';mul.inputs[0].default_value=1.;mul.inputs[2].default_value=(.72,.70,.67,1)
    links.new(sat.outputs['Color'],mul.inputs[1]);links.new(mul.outputs[0],bs.inputs['Base Color'])
    bs.inputs['Specular IOR Level'].default_value=.28
    if not bs.inputs['Roughness'].is_linked:bs.inputs['Roughness'].default_value=.51
    bs.inputs['Subsurface Weight'].default_value=.075
changed=[];done=set()
for name in ['APJ_Face','APJ_v5_Skin_Transition_Underlay','APJ_Hand_Left','APJ_Hand_Right']:
    obj=bpy.data.objects.get(name)
    if not obj:continue
    for mat in obj.data.materials:
        if mat in done:continue
        bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tone(mat,bs);done.add(mat);changed.append(mat.name)
mat=bpy.data.objects['char1'].data.materials[0]
skin=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED' and n.label.startswith('Aged skin'))
tone(mat,skin);changed.append(mat.name+' (skin branch only)')
eye=bpy.data.objects['APJ_Eye_Left_Globe'].data.materials[0]
for n in eye.node_tree.nodes:
    if n.type!='MIX_RGB':continue
    a=tuple(n.inputs[1].default_value[:3]);b=tuple(n.inputs[2].default_value[:3])
    if abs(a[0]-.045)<1e-4 and abs(b[0]-.19)<1e-4:
        n.inputs[1].default_value=(.010,.004,.0018,1);n.inputs[2].default_value=(.035,.014,.0055,1);n.label='V6 deep brown iris fibers'
    if abs(a[0]-.68)<1e-4:n.inputs[1].default_value=(.52,.49,.43,1)
    if abs(b[0]-.018)<1e-4:n.inputs[2].default_value=(.006,.003,.0015,1)
eye['appearance']='Dark brown iris, near-black pupil, warm off-white sclera'
bpy.data.objects['APJ_Face']['skin_eyes_v6']=True
report={'skin_materials':changed,'skin_linear_multiplier':[.72,.70,.67],'skin_saturation':.90,
 'iris':'deep brown','pupil':'near-black','reference':'Dr. Kalam’s Welcoming Wave.png',
 'note':'Individual appearance reference used; nationality does not prescribe one skin tone or eye color',
 'geometry_and_rig_changed':False,'source':'apj_likeness_v5_master.blend'}
json.dump(report,open(os.path.join(ROOT,'tests','skin_eyes_v6.json'),'w'),indent=2)
bpy.data.texts.load(os.path.join(ROOT,'scripts','skin_eyes_v6.py'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','apj_skin_eyes_v6_master.blend'))
print('Saved v6 complexion and iris materials',changed)
