"""Subtle salt-and-pepper brow darkening and clean upper-lip color cleanup."""
import bpy,math,json
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;f=bpy.data.objects['APJ_Face'];c=bpy.data.objects['APJ_Face_Controls']
if f.get('brows_upperlip_v10'):raise RuntimeError('Already applied')
c.animation_data.action=None
for p in json.loads(f['expression_channels'])+[p for p in c.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']:c[p]=0.
c.update_tag();s.frame_set(1);bpy.context.view_layer.update()
def g(x,mid,width):return math.exp(-((x-mid)/width)**2)
mesh=f.data;attr=mesh.color_attributes.new(name='BrowUpperLipV10',type='FLOAT_COLOR',domain='POINT');mz=float(f['mouth_center_z'])
for i,p in enumerate(mesh.shape_keys.key_blocks['Basis'].data):
 x,y,z=p.co
 brow=g(abs(x),.036,.022)*g(z,1.535+.035*(abs(x)-.034),.0055) if y<0 else 0
 lip=g(x,0,.025)*g(z,mz+.0045,.0038) if y<0 else 0
 attr.data[i].color=(brow,lip,0,1)
mat=f.data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');old=bs.inputs['Base Color'].links[0].from_socket
vc=nodes.new('ShaderNodeVertexColor');vc.layer_name=attr.name
split=nodes.new('ShaderNodeSeparateColor');links.new(vc.outputs['Color'],split.inputs[0])
fac=nodes.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.62;links.new(split.outputs['Red'],fac.inputs[0])
mul=nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.label='V10 subtle dark salt-and-pepper brows';links.new(fac.outputs[0],mul.inputs[0]);links.new(old,mul.inputs[1]);mul.inputs[2].default_value=(.43,.39,.35,1)
lipfac=nodes.new('ShaderNodeMath');lipfac.operation='MULTIPLY';lipfac.inputs[1].default_value=.26;links.new(split.outputs['Green'],lipfac.inputs[0])
mix=nodes.new('ShaderNodeMixRGB');mix.label='V10 clean warm upper lip, no moustache added';links.new(lipfac.outputs[0],mix.inputs[0]);links.new(mul.outputs[0],mix.inputs[1]);mix.inputs[2].default_value=(.23,.103,.047,1);links.new(mix.outputs[0],bs.inputs['Base Color'])
f['brows_upperlip_v10']=True
s.frame_end=60
bpy.data.texts.load(ROOT+'/scripts/brows_upperlip_v10.py')
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/blender/apj_brows_upperlip_v10_master.blend')
s.render.filepath=ROOT+'/renders/brows_upperlip_v10_front.png';bpy.ops.render.render(write_still=True)
print('Brow and upper-lip localized material masks saved; topology and all speech actions retained.')
