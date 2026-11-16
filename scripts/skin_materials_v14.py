"""Photographic skin sources with anatomy-aligned UVs and complete PBR bakes."""
import bpy,json,math,os,numpy as np
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;face=bpy.data.objects['APJ_Face'];rig=bpy.data.objects['Armature']
if face.get('skin_v14'):raise RuntimeError('Skin v14 is already applied')
bridge=bpy.app.driver_namespace.get('apj_capture')
if bridge:
 if bpy.app.timers.is_registered(bridge['timer']):bpy.app.timers.unregister(bridge['timer'])
 bridge['tracker'].reset();bridge['mode']='idle';bridge['packet']={}
field=json.load(open(ROOT+'/tests/skin_uv_v14.json'));centers=np.array(field['centers']);weights=np.array(field['weights']);sigma=field['sigma']
for name in ['APJ_Face','APJ_v5_Skin_Transition_Underlay','char1']:
 obj=bpy.data.objects[name];uv=obj.data.uv_layers.get('Skin14Projection') or obj.data.uv_layers.new(name='Skin14Projection');old=obj.data.uv_layers['FaceProjection'];points=np.array([tuple(p.uv) for p in old.data]);result=points.copy()
 for start in range(0,len(points),1200):
  p=points[start:start+1200];d=np.sum((p[:,None,:]-centers[None,:,:])**2,axis=2);result[start:start+len(p)]+=np.exp(-d/(2*sigma*sigma))@weights
 for p,v in zip(uv.data,result):p.uv=v
photo=bpy.data.images.load(ROOT+'/textures/skin_v14/face_photographic_source.png',check_existing=True);tile=bpy.data.images.load(ROOT+'/textures/skin_v14/aged_hand_microcolor.png',check_existing=True)
photo.pack();tile.pack()
def node(mat,kind):return mat.node_tree.nodes.new(kind)
def scalar(mat,operation,a,b=None):
 n=node(mat,'ShaderNodeMath');n.operation=operation
 for i,v in enumerate([a,b]):
  if v is None:continue
  if isinstance(v,(int,float)):n.inputs[i].default_value=v
  else:mat.node_tree.links.new(v,n.inputs[i])
 return n.outputs[0]
def texture(mat,image,uvname,scale=None):
 links=mat.node_tree.links;uv=node(mat,'ShaderNodeUVMap');uv.uv_map=uvname;coord=uv.outputs[0]
 if scale:
  mapping=node(mat,'ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=scale;links.new(coord,mapping.inputs[0]);coord=mapping.outputs[0]
 tex=node(mat,'ShaderNodeTexImage');tex.image=image;tex.extension='REPEAT';links.new(coord,tex.inputs['Vector']);return tex.outputs['Color']
def saturation(mat,source,sat=.82,value=.95):
 n=node(mat,'ShaderNodeHueSaturation');n.label='V14 restrained natural skin pigmentation';n.inputs['Saturation'].default_value=sat;n.inputs['Value'].default_value=value;mat.node_tree.links.new(source,n.inputs['Color']);return n.outputs[0]
def pores(mat,bs,hand=False):
 links=mat.node_tree.links;coord=node(mat,'ShaderNodeTexCoord');voro=node(mat,'ShaderNodeTexVoronoi');voro.inputs['Scale'].default_value=2900 if not hand else 2300;links.new(coord.outputs['Object'],voro.inputs['Vector'])
 grain=node(mat,'ShaderNodeTexNoise');grain.inputs['Scale'].default_value=6800;grain.inputs['Detail'].default_value=2.;links.new(coord.outputs['Object'],grain.inputs['Vector'])
 h=scalar(mat,'ADD',scalar(mat,'MULTIPLY',voro.outputs['Distance'],.65),scalar(mat,'MULTIPLY',grain.outputs['Fac'],.35))
 old=bs.inputs['Normal'].links[0].from_socket if bs.inputs['Normal'].is_linked else None
 bump=node(mat,'ShaderNodeBump');bump.label='V14 physical micrometer pore relief';bump.inputs['Strength'].default_value=.32;bump.inputs['Distance'].default_value=.000045 if hand else .000035;links.new(h,bump.inputs['Height'])
 if old:links.new(old,bump.inputs['Normal'])
 links.new(bump.outputs[0],bs.inputs['Normal'])
 if not hand:
  rough=node(mat,'ShaderNodeMapRange');rough.inputs['From Min'].default_value=0.;rough.inputs['From Max'].default_value=1.;rough.inputs['To Min'].default_value=.40;rough.inputs['To Max'].default_value=.58;links.new(grain.outputs['Fac'],rough.inputs['Value']);links.new(rough.outputs[0],bs.inputs['Roughness'])
 bs.inputs['IOR'].default_value=1.4;bs.inputs['Specular IOR Level'].default_value=.35;bs.inputs['Subsurface Weight'].default_value=.12;bs.inputs['Subsurface Scale'].default_value=.0012;bs.inputs['Subsurface Radius'].default_value=(1.,.48,.24)
# Face: new photograph directly replaces the orange, multiply-tinted source chain.
mat=face.data.materials[0].copy();mat.name='APJ_v14_Photographic_Facial_Skin';face.data.materials[0]=mat;bpy.data.objects['APJ_v5_Skin_Transition_Underlay'].data.materials[0]=mat
bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');links=mat.node_tree.links
color=saturation(mat,texture(mat,photo,'Skin14Projection'),.82,.95)
attr=node(mat,'ShaderNodeVertexColor');attr.layer_name='BrowUpperLipV10';sep=node(mat,'ShaderNodeSeparateColor');links.new(attr.outputs['Color'],sep.inputs[0]);mix=node(mat,'ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[2].default_value=(.65,.65,.65,1);links.new(scalar(mat,'MULTIPLY',sep.outputs['Red'],.4),mix.inputs[0]);links.new(color,mix.inputs[1]);links.new(mix.outputs[0],bs.inputs['Base Color']);pores(mat,bs)
# Hands: fresh photographic microcolor over the existing anatomical crease normals.
old=bpy.data.objects['APJ_Hand_Left'].data.materials[0];handmat=old.copy();handmat.name='APJ_v14_Photographic_Hand_Skin'
for name in ['APJ_Hand_Left','APJ_Hand_Right']:bpy.data.objects[name].data.materials[0]=handmat
bs=next(n for n in handmat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');links=handmat.node_tree.links;color=saturation(handmat,texture(handmat,tile,'Hand_Atlas',(1.8,12,1)),.70,.82)
links.new(color,bs.inputs['Base Color']);pores(handmat,bs,True)
# Make palmar skin gently lighter, without washing out the whole hand.
for name in ['APJ_Hand_Left','APJ_Hand_Right']:
 obj=bpy.data.objects[name];at=obj.data.color_attributes.new(name='V14PalmMask',type='FLOAT_COLOR',domain='POINT')
 for i,v in enumerate(obj.data.vertices):
  w=max(0,min(1,(1.301-v.co.z)/.009));at.data[i].color=(w,w,w,1)
at=node(handmat,'ShaderNodeVertexColor');at.layer_name='V14PalmMask';palm=node(handmat,'ShaderNodeMixRGB');palm.blend_type='MULTIPLY';palm.inputs[2].default_value=(1.12,1.15,1.13,1);links.new(at.outputs['Color'],palm.inputs[0]);links.new(color,palm.inputs[1]);links.new(palm.outputs[0],bs.inputs['Base Color'])
# Transition skin on the retained neck/head uses the same aligned source near front.
body=bpy.data.objects['char1'];mat=body.data.materials[0].copy();mat.name='APJ_v14_Head_And_Silver_Hair';body.data.materials[0]=mat;bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED' and n.label.startswith('Aged skin'));links=mat.node_tree.links;oldcolor=bs.inputs['Base Color'].links[0].from_socket
mask=body.data.color_attributes.new(name='V14FrontSkin',type='FLOAT_COLOR',domain='POINT')
for i,p in enumerate(body.data.shape_keys.key_blocks['Basis'].data):
 x,y,z=p.co;w=max(0,min(1,(.045-y)/.06))*max(0,min(1,(z-1.395)/.035))*max(0,min(1,(1.63-z)/.025))*max(0,min(1,(.125-abs(x))/.025));mask.data[i].color=(w,w,w,1)
at=node(mat,'ShaderNodeVertexColor');at.layer_name='V14FrontSkin';mix=node(mat,'ShaderNodeMixRGB');links.new(at.outputs['Color'],mix.inputs[0]);links.new(oldcolor,mix.inputs[1]);links.new(saturation(mat,texture(mat,photo,'Skin14Projection'),.82,.95),mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color']);pores(mat,bs)
face['skin_v14']=True
# Bake the complete color, roughness and tangent normal for real-time rendering.
s.render.engine='CYCLES';s.cycles.samples=8;s.render.bake.margin=12;s.render.bake.use_selected_to_active=False;s.render.bake.normal_space='TANGENT'
report={'source_resolution':list(photo.size),'generated_sources':['textures/skin_v14/face_photographic_source.png','textures/skin_v14/aged_hand_microcolor.png'],'uv_fit_error':field['mean_landmark_fit_error_uv'],'bakes':{},'geometry_changed':False,'notes':['Generated reconstruction, not a measured skin scan','Normal and roughness are included in the browser asset','Subsurface scattering is available in Blender; browser uses standard PBR']}
for name in ['APJ_Face','APJ_Hand_Left','APJ_Hand_Right','char1']:
 obj=bpy.data.objects[name];resolution=2048;bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;obj.data.uv_layers.active_index=0
 for i,uv in enumerate(obj.data.uv_layers):uv.active_render=i==0
 report['bakes'][name]={}
 for kind in ['Color','Roughness','Normal']:
  image=bpy.data.images.new('APJ14_'+name+'_'+kind,width=resolution,height=resolution,alpha=False)
  if kind!='Color':image.colorspace_settings.name='Non-Color'
  records=[]
  for material in obj.data.materials:
   nodes=material.node_tree.nodes;links=material.node_tree.links;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');oldout=out.inputs['Surface'].links[0].from_socket;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');target=nodes.new('ShaderNodeTexImage');target.image=image;nodes.active=target
   for n in nodes:n.select=n==target
   em=None
   if kind!='Normal':
    em=nodes.new('ShaderNodeEmission');source=bs.inputs['Base Color' if kind=='Color' else 'Roughness']
    if source.is_linked:links.new(source.links[0].from_socket,em.inputs['Color'])
    elif kind=='Color':em.inputs['Color'].default_value=source.default_value
    else:em.inputs['Color'].default_value=(source.default_value,)*3+(1,)
    links.new(em.outputs[0],out.inputs['Surface'])
   records.append((material,out,oldout,target,em))
  try:bpy.ops.object.bake(type='NORMAL' if kind=='Normal' else 'EMIT')
  finally:
   for material,out,oldout,target,em in records:
    material.node_tree.links.new(oldout,out.inputs['Surface']);material.node_tree.nodes.remove(target)
    if em:material.node_tree.nodes.remove(em)
  image.filepath_raw=ROOT+'/textures/skin_v14/'+image.name+'.png';image.file_format='PNG';image.save();image.pack();report['bakes'][name][kind]={'path':image.filepath_raw,'resolution':resolution}
json.dump(report,open(ROOT+'/tests/skin_v14.json','w'),indent=2)
bpy.data.texts.load(ROOT+'/scripts/skin_materials_v14.py');bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/blender/apj_skin_v14_master.blend')
if bridge:bpy.app.timers.register(bridge['timer'],first_interval=.03)
print(json.dumps(report))
