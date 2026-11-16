"""Conservative reference-guided nose, lips and midface refinement."""
import bpy,math,json,os
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';scene=bpy.context.scene;face=bpy.data.objects['APJ_Face'];ctrl=bpy.data.objects['APJ_Face_Controls']
if face.get('micro_likeness_v9'):raise RuntimeError('Already applied')
live=bpy.app.driver_namespace.pop('apj_live_face',None)
if live:
    if bpy.app.timers.is_registered(live['timer']):bpy.app.timers.unregister(live['timer'])
    live['socket'].close()
if ctrl.animation_data:ctrl.animation_data.action=None
for p in json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']:ctrl[p]=0.
ctrl.update_tag();scene.frame_set(1);bpy.context.view_layer.update()
backup=face.copy();backup.data=face.data.copy();backup.name='SOURCE_Pre_Micro_Likeness_v9';scene.collection.objects.link(backup);backup.hide_set(True);backup.hide_render=True
def g(a,c,w):return math.exp(-((a-c)/w)**2)
mz=float(face['mouth_center_z'])
def sculpt(p):
    x,y,z=p
    if z<1.412 or z>1.504 or abs(x)>.09 or y>-.015:return Vector()
    tip=g(x,0,.014)*g(z,1.477,.010)
    wing=g(abs(x),.017,.009)*g(z,1.475,.009)
    corners=g(abs(x),.026,.009)*g(z,mz,.009)
    lower=g(x,0,.023)*g(z,mz-.009,.006)
    chin=g(x,0,.027)*g(z,mz-.021,.010)
    fold=g(abs(x),.033,.010)*g(z,mz+.009,.015)
    return Vector((-.032*x*tip-math.copysign(.00032*wing,x),.00065*tip+.00032*wing+.00035*lower-.00045*fold-.00028*chin,.00075*corners+.00030*lower))
stats={}
for name in ['APJ_Face','char1','APJ_v5_Skin_Transition_Underlay']:
    obj=bpy.data.objects.get(name)
    if not obj or not obj.data.shape_keys:continue
    delta=[sculpt(p.co) for p in obj.data.shape_keys.key_blocks['Basis'].data]
    for key in obj.data.shape_keys.key_blocks:
        for p,d in zip(key.data,delta):p.co+=d
    obj.data.shape_keys.update_tag()
    stats[name]={'moved_vertices':sum(d.length>.00001 for d in delta),'max_displacement_m':max(d.length for d in delta)}
face['micro_likeness_v9']=True
report={'changes':stats,'regions':['nose tip projection and alar fullness','relaxed mouth corner lift','lower lip and chin transition','softened nasolabial relief'],'targets_preserved':len(face.data.shape_keys.key_blocks)-1,'limitations':'Reference-guided approximation; no numerical likeness score. Existing unwelded head join retained.'}
json.dump(report,open(ROOT+'/tests/micro_likeness_v9.json','w'),indent=2)
scene.frame_set(1);bpy.context.view_layer.update()
bpy.data.texts.load(ROOT+'/scripts/micro_likeness_v9.py')
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/blender/apj_micro_likeness_v9_master.blend')
scene.render.filepath=ROOT+'/renders/micro_likeness_v9_front.png';bpy.ops.render.render(write_still=True)
print(json.dumps(report))
