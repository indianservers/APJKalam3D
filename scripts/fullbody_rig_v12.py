"""Extend the existing human deformation rig with weighted thoracic controls."""
import bpy,json,math
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;r=bpy.data.objects['Armature'];body=bpy.data.objects['char1'];face=bpy.data.objects['APJ_Face'];ctrl=bpy.data.objects['APJ_Face_Controls']
if r.get('fullbody_v12'):raise RuntimeError('Already upgraded')
if r.animation_data:r.animation_data.action=None
if ctrl.animation_data:ctrl.animation_data.action=None
for p in json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']:ctrl[p]=0.
for b in r.pose.bones:
 b.matrix_basis.identity()
 for con in b.constraints:
  if con.type=='IK':con.influence=0
ctrl.update_tag();s.frame_set(1);bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT');r.select_set(True);bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
ribspec=[]
for j in range(1,13):
 z=1.315-(j-1)*.014
 parent='Spine' if z>=1.272 else 'Spine01' if z>=1.146 else 'Spine02'
 for side,sign in [('L',1),('R',-1)]:
  name=f'Rib.{side}.{j:02d}';b=r.data.edit_bones.new(name)
  b.head=(sign*.014,.018,z);b.tail=(sign*(.105-.0035*abs(j-6)),.002,z-.009)
  b.parent=r.data.edit_bones[parent];b.use_deform=True;b.align_roll(Vector((0,0,1)));ribspec.append((name,sign,z,parent))
b=r.data.edit_bones.new('Sternum');b.head=(0,-.055,1.19);b.tail=(0,-.055,1.30);b.parent=r.data.edit_bones['Spine01'];b.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
ribgroups={name:body.vertex_groups.new(name=name) for name,*_ in ribspec};sternum=body.vertex_groups.new(name='Sternum')
counts={n:0 for n in ribgroups};counts['Sternum']=0
for v in body.data.vertices:
 x,y,z=v.co
 if not (1.14<z<1.34 and abs(x)<.17):continue
 torso=sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in ['Spine','Spine01','Spine02'])
 if torso<.35:continue
 weights=[]
 for name,sign,rz,parent in ribspec:
  w=math.exp(-((z-rz)/.014)**2-((x-sign*.085)/.07)**2)
  if w>.08:weights.append((name,w))
 sw=math.exp(-(x/.035)**2-((z-1.25)/.075)**2-((y+.055)/.08)**2)
 if sw>.08:weights.append(('Sternum',sw))
 total=sum(w for n,w in weights)
 if total<=0:continue
 amount=.12*min(1,torso)
 for vg in list(v.groups):body.vertex_groups[vg.group].add([v.index],vg.weight*(1-amount),'REPLACE')
 for name,w in weights:
  body.vertex_groups[name].add([v.index],amount*w/total,'REPLACE');counts[name]+=1
r['breathing']=0.;r.id_properties_ui('breathing').update(min=0,max=1,description='Small inferred thoracic expansion, not camera-measured individual ribs')
for name,sign,z,parent in ribspec:
 p=r.pose.bones[name];p.rotation_mode='QUATERNION'
 # Each rib is independently poseable. The shared breathing control adds subtle lift.
 fc=p.driver_add('location',1);d=fc.driver;v=d.variables.new();v.name='breath';v.type='SINGLE_PROP';v.targets[0].id=r;v.targets[0].data_path='["breathing"]';d.expression='.0006*breath'
for o in [body,face,bpy.data.objects['APJ_Hand_Left'],bpy.data.objects['APJ_Hand_Right']]:
 for m in o.modifiers:
  if m.type=='ARMATURE':m.use_deform_preserve_volume=True
body['fullbody_deformation_note']='Weighted thorax, preserved finger skinning, volume-preserving armature. Coat remains a single garment mesh; extreme seated cloth collisions require cleanup.'
r['fullbody_v12']=True;r['status']='Full-body capture rig v12, 30 finger joints + 24 weighted ribs and sternum'
rest=[]
for b in r.data.bones:
 q=b.matrix_local.to_quaternion();lq=(b.parent.matrix_local.inverted()@b.matrix_local).to_quaternion() if b.parent else q
 rest.append({'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'restQuaternion':[q.x,q.y,q.z,q.w],'localQuaternion':[lq.x,lq.y,lq.z,lq.w],'deform':b.use_deform})
json.dump({'bones':rest,'faceChannels':json.loads(face['expression_channels']),'wrinkles':json.loads(face['wrinkle_correctives']),'coordinates':'Blender Z-up, front -Y; anatomical left +X'},open(ROOT+'/webapp/assets/rig.json','w'),indent=2)
json.dump({'bone_count':len(r.data.bones),'finger_joints':30,'rib_controls':24,'rib_weighted_vertices':counts,'production_ready':False,'limitations':['Individual ribs inferred from torso, not directly tracked','Single-view capture has occlusion/depth ambiguity','Coat is not a cloth simulation','Existing facial patch is not welded']},open(ROOT+'/tests/fullbody_rig_v12.json','w'),indent=2)
s.frame_set(1);bpy.context.view_layer.update()
bpy.data.texts.load(ROOT+'/scripts/fullbody_rig_v12.py')
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/blender/apj_fullbody_v12_master.blend')
print('Rig bones',len(r.data.bones),'weighted ribs',sum(v>0 for n,v in counts.items()))
