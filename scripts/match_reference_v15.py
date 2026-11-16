"""Fit the existing animated character to the exact user-supplied portrait."""
import bpy,json,math,random,numpy as np
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';scene=bpy.context.scene;face=bpy.data.objects['APJ_Face'];body=bpy.data.objects['char1'];rig=bpy.data.objects['Armature'];ctrl=bpy.data.objects['APJ_Face_Controls']
if face.get('reference_v15'):raise RuntimeError('Already applied')
state=bpy.app.driver_namespace.get('apj_capture')
if state:
 if bpy.app.timers.is_registered(state['timer']):bpy.app.timers.unregister(state['timer'])
 state['tracker'].reset();state['mode']='idle';state['packet']={}
fit=json.load(open(ROOT+'/tests/reference_v15_fit.json'));field=fit['sculpt'];C=np.array(field['centers']);W=np.array(field['weights']);sigma=field['sigma']
def sculpt(points):
 p=np.array([tuple(v) for v in points]);xz=p[:,[0,2]];out=[]
 for start in range(0,len(p),1800):
  a=p[start:start+1800];q=xz[start:start+1800];d=np.sum((q[:,None]-C[None,:])**2,axis=2);delta=np.exp(-d/(2*sigma*sigma))@W
  length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.006/np.maximum(length,1e-9))[:,None]
  mask=np.clip((a[:,2]-1.397)/.018,0,1)*np.clip((1.622-a[:,2])/.014,0,1)*np.clip((.09-a[:,1])/.035,0,1)
  for x in [-.0345,.0347]:mask*=1-.99*np.exp(-((a[:,0]-x)/.018)**2-((a[:,2]-1.5148)/.014)**2)
  delta*=mask[:,None];out.extend(Vector((x,0,z)) for x,z in delta)
 return out
stats={}
for name in ['APJ_Face','char1','APJ_v5_Skin_Transition_Underlay']:
 obj=bpy.data.objects[name];base=obj.data.shape_keys.key_blocks['Basis'];delta=sculpt([v.co for v in base.data])
 for key in obj.data.shape_keys.key_blocks:
  for p,d in zip(key.data,delta):p.co+=d
 obj.data.shape_keys.update_tag();stats[name]={'max_displacement_m':max(d.length for d in delta),'moved_vertices':sum(d.length>.00001 for d in delta)}
mouth_delta=sculpt([Vector((0,-.09,face['mouth_center_z']))])[0];face['mouth_center_z']+=mouth_delta.z
for obj in scene.objects:
 if obj.type=='MESH' and (obj.name.startswith(('APJ_Teeth_','APJ_Gum_')) or obj.name in ['APJ_Tongue','APJ_Mouth_Interior']):
  matrix=obj.matrix_world.copy();inv=matrix.inverted().to_3x3();delta=sculpt([matrix@v.co for v in obj.data.vertices])
  for p,d in zip(obj.data.vertices,delta):p.co+=inv@d
hair=bpy.data.objects['APJ_v3_Fine_Hair_Strands'];matrix=hair.matrix_world.copy();inv=matrix.inverted().to_3x3()
for spline in hair.data.splines:
 delta=sculpt([matrix@Vector(p.co[:3]) for p in spline.points])
 for p,d in zip(spline.points,delta):p.co=(*(Vector(p.co[:3])+inv@d),1)
# Refit eyelid/jaw closure after changing the neutral surface.
exec(compile(open(ROOT+'/scripts/refresh_likeness_v5_rig.py').read(),'refresh_likeness_v5_rig.py','exec'))
for prop in json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']:ctrl[prop]=0.
ctrl.update_tag();face.data.shape_keys.update_tag();scene.frame_set(1);bpy.context.view_layer.update()
# New texture coordinates point at the exact requested image, not an interpretation.
uvfit=fit['uv'];UC=np.array(uvfit['centers']);UW=np.array(uvfit['weights']);us=uvfit['sigma']
for name in ['APJ_Face','APJ_v5_Skin_Transition_Underlay','char1']:
 obj=bpy.data.objects[name];old=obj.data.uv_layers['FaceProjection'];uv=obj.data.uv_layers.new(name='Reference15Projection');p=np.array([tuple(v.uv) for v in old.data]);result=p.copy()
 for start in range(0,len(p),1800):
  a=p[start:start+1800];d=np.sum((a[:,None]-UC[None,:])**2,axis=2);result[start:start+len(a)]+=np.exp(-d/(2*us*us))@UW
 for v,co in zip(uv.data,result):v.uv=co
image=bpy.data.images.load(ROOT+'/textures/reference_v15/exact_appearance_target.png',check_existing=True);image.pack()
mat=face.data.materials[0].copy();mat.name='APJ_v15_Exact_Reference_Skin';face.data.materials[0]=mat;bpy.data.objects['APJ_v5_Skin_Transition_Underlay'].data.materials[0]=mat
head=body.data.materials[0].copy();head.name='APJ_v15_Reference_Head_And_Hair';body.data.materials[0]=head
for material in [mat,head]:
 for node in material.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image and node.image.name.startswith('face_photographic_source'):node.image=image
  if node.type=='UVMAP' and node.uv_map=='Skin14Projection':node.uv_map='Reference15Projection'
  if node.type=='HUE_SAT' and node.label.startswith('V14'):
   node.inputs['Saturation'].default_value=1.;node.inputs['Value'].default_value=.80
# Dense, fine strand ribbons export to the browser and move with Head.
rng=random.Random(1515);vertices=[];faces=[];material_ids=[]
for spline in hair.data.splines:
 points=[hair.matrix_world@Vector(p.co[:3]) for p in spline.points]
 if len(points)<4:continue
 for copy in range(4):
  offset=rng.uniform(-.00035,.00035);start=len(vertices);base_mat=rng.choices([0,1,2,3],[.12,.35,.40,.13])[0]
  for j,p in enumerate(points):
   tangent=(points[min(j+1,len(points)-1)]-points[max(0,j-1)]).normalized();normal=(p-Vector((0,.025,1.54))).normalized();across=tangent.cross(normal).normalized()
   if across.length<.1:across=Vector((1,0,0))
   t=j/max(1,len(points)-1);width=.000095*(.25+.75*math.sin(math.pi*(t*.94+.03))**.35);center=p+normal*(.00010+copy*.000025)+across*offset
   vertices.extend([center-across*width,center+across*width])
   if j:
    a=start+(j-1)*2;b=start+j*2;faces.append((a,a+1,b+1,b));material_ids.append(0 if t<.08 else base_mat)
mesh=bpy.data.meshes.new('APJ_v15_Exportable_Silver_Fibers');mesh.from_pydata(vertices,[],faces);mesh.update();obj=bpy.data.objects.new('APJ_v15_Silver_Hair_Strands',mesh);scene.collection.objects.link(obj)
for i,color in enumerate([(.18,.19,.20,1),(.38,.39,.40,1),(.58,.59,.60,1),(.72,.73,.74,1)]):
 m=bpy.data.materials.new('APJ_v15_Silver_Fiber_'+str(i));m.use_nodes=True;bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=color;bs.inputs['Roughness'].default_value=.40;bs.inputs['Anisotropic'].default_value=.65;mesh.materials.append(m)
for poly,i in zip(mesh.polygons,material_ids):poly.material_index=i;poly.use_smooth=True
group=obj.vertex_groups.new(name='Head');group.add(list(range(len(mesh.vertices))),1.,'REPLACE');mod=obj.modifiers.new('Rigid head attachment','ARMATURE');mod.object=rig;obj.parent=rig
hair.hide_render=True;hair.hide_set(True)
face['reference_v15']=True;face['exact_appearance_reference']='textures/reference_v15/exact_appearance_target.png'
report={'sculpt':stats,'strand_ribbons':len(hair.data.splines)*4,'hair_vertices':len(mesh.vertices),'hair_faces':len(mesh.polygons),'mouth_delta_m':list(mouth_delta),'face_targets':len(face.data.shape_keys.key_blocks)-1,'bone_count':len(rig.data.bones),'source':'Exact user-supplied appearance image','limitations':['Single portrait cannot specify hidden depth','Existing head join still needs topology cleanup','No exact multiview likeness score claimed']}
json.dump(report,open(ROOT+'/tests/reference_v15.json','w'),indent=2)
bpy.data.texts.load(ROOT+'/scripts/match_reference_v15.py');bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/blender/apj_reference_v15_master.blend')
if state:bpy.app.timers.register(state['timer'],first_interval=.03)
print(json.dumps(report))
