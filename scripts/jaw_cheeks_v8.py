"""Local jaw and posterior-cheek refinement using the new portrait reference."""
import bpy,math,json,os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=r'C:\Abdul Kalam';face=bpy.data.objects['APJ_Face'];body=bpy.data.objects['char1'];ctrl=bpy.data.objects['APJ_Face_Controls'];scene=bpy.context.scene
if face.get('jaw_cheeks_v8'):raise RuntimeError('Jaw pass already applied')
if ctrl.animation_data:ctrl.animation_data.action=None
channels=json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']
saved={p:float(ctrl[p]) for p in channels}
for p in channels:ctrl[p]=0.
ctrl.update_tag();face.data.shape_keys.update_tag();scene.frame_set(1);bpy.context.view_layer.update()
backup=face.copy();backup.data=face.data.copy();backup.name='SOURCE_Pre_Jaw_Cheeks_v8';scene.collection.objects.link(backup);backup.hide_set(True);backup.hide_render=True
def g(x,c,w):return math.exp(-((x-c)/w)**2)
mz=face['mouth_center_z']
def sculpt(p):
    x,y,z=p
    if z<1.408 or z>1.503 or abs(x)>.12 or y>.07:return Vector()
    fade=min(1,max(0,(z-1.408)/.010))*min(1,max(0,(1.503-z)/.014))
    mouth=1-.90*g(x,0,.036)*g(z,mz,.015)
    jaw=g(abs(x),.056,.022)*g(z,1.443,.024)
    cheek=g(abs(x),.064,.023)*g(z,1.473,.025)
    dx=math.copysign(.0024*jaw,x)+.025*x*g(z,1.426,.012)
    dy=-.0018*cheek+.0010*g(x,0,.040)*g(z,1.415,.010)
    dz=.00065*g(x,0,.038)*g(z,1.423,.011)
    return Vector((dx,dy,dz))*fade*mouth
stats={}
for name in ['APJ_Face','char1','APJ_v5_Skin_Transition_Underlay']:
    obj=bpy.data.objects.get(name)
    if not obj or not obj.data.shape_keys:continue
    delta=[sculpt(p.co) for p in obj.data.shape_keys.key_blocks['Basis'].data]
    for key in obj.data.shape_keys.key_blocks:
        for p,d in zip(key.data,delta):p.co+=d
    obj.data.shape_keys.update_tag();stats[name]={'moved_vertices':sum(d.length>1e-5 for d in delta),'max_displacement_m':max(d.length for d in delta)}

# Match only the overlap band to the retained head surface. Avoid new topology cuts.
sub=next(mod for mod in body.modifiers if mod.type=='SUBSURF');was=sub.show_viewport;sub.show_viewport=True;sub.levels=2;bpy.context.view_layer.update()
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());base=face.data.shape_keys.key_blocks['Basis'];corrections=[]
for p in base.data:
    co=p.co;d=Vector()
    region=g(co.z,1.458,.034)*max(0,min(1,(abs(co.x)-.043)/.020))
    if region>.02 and 1.418<co.z<1.502:
        hit=bvh.ray_cast(Vector((co.x,-.40,co.z)),Vector((0,1,0)))[0]
        if hit is not None and hit.y<-.015 and abs(hit.y-co.y)<.006:
            # Keep the patch just in front of overlapping retained skin.
            target=hit.y-.00035;amount=max(-.002,min(.002,target-co.y))*region
            d.y=amount
    corrections.append(d)
for key in face.data.shape_keys.key_blocks:
    for p,d in zip(key.data,corrections):p.co+=d
under=bpy.data.objects.get('APJ_v5_Skin_Transition_Underlay')
if under:
    for key in under.data.shape_keys.key_blocks:
        for p,d in zip(key.data,corrections):p.co+=d
    under.data.shape_keys.update_tag()
sub.show_viewport=was;face.data.shape_keys.update_tag();scene.frame_set(1);bpy.context.view_layer.update()
face['jaw_cheeks_v8']=True;face['jaw_reference_v8']='references/apj_jaw_reference_v8.png'
report={'reference':'references/apj_jaw_reference_v8.png','regions':['jaw angle and jowl width','posterior cheek volume','rounded chin transition','face/head overlap band'],
 'changes':stats,'overlap_max_correction_m':max(d.length for d in corrections),'shape_targets_preserved':len(face.data.shape_keys.key_blocks)-1,
 'notes':['Localized sculpt; eyes/nose/forehead and material tone retained','Original v7 master preserved','Single portrait does not fully constrain the hidden rear cheek profile','Existing facial patch is still not a welded full-head surface']}
json.dump(report,open(os.path.join(ROOT,'tests','jaw_cheeks_v8.json'),'w'),indent=2)
bpy.data.texts.load(os.path.join(ROOT,'scripts','jaw_cheeks_v8.py'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','apj_jaw_cheeks_v8_master.blend'))
print(json.dumps(report))
