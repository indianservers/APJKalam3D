"""Subtle soft-tissue fullness, carried through existing expression targets."""
import bpy,math,json
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';s=bpy.context.scene;f=bpy.data.objects['APJ_Face'];c=bpy.data.objects['APJ_Face_Controls']
if f.get('cheek_fullness_v11'):raise RuntimeError('Already applied')
if c.animation_data:c.animation_data.action=None
for p in json.loads(f['expression_channels'])+[p for p in c.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']:c[p]=0.
c.update_tag();s.frame_set(1);bpy.context.view_layer.update()
def g(x,m,w):return math.exp(-((x-m)/w)**2)
def sculpt(p):
 x,y,z=p
 if y>-.005 or abs(x)>.115 or z<1.415 or z>1.510:return Vector()
 cheek=g(abs(x),.049,.022)*g(z,1.482,.020)
 lower=g(abs(x),.052,.021)*g(z,1.451,.018)
 protect=1-.94*g(x,0,.029)*g(z,1.454,.030)
 edge=min(1,max(0,(1.510-z)/.010))*min(1,max(0,(z-1.415)/.012))
 return Vector((math.copysign(.00085*cheek+.00060*lower,x),-.00115*cheek-.00060*lower,.00020*cheek))*protect*edge
stats={}
for name in ['APJ_Face','char1','APJ_v5_Skin_Transition_Underlay']:
 o=bpy.data.objects.get(name)
 if not o or not o.data.shape_keys:continue
 ds=[sculpt(p.co) for p in o.data.shape_keys.key_blocks['Basis'].data]
 for k in o.data.shape_keys.key_blocks:
  for p,d in zip(k.data,ds):p.co+=d
 o.data.shape_keys.update_tag();stats[name]={'max_displacement_m':max(d.length for d in ds)}
f['cheek_fullness_v11']=True;s.frame_set(1);bpy.context.view_layer.update()
json.dump({'changes':stats,'targets_preserved':len(f.data.shape_keys.key_blocks)-1,'note':'Subtle cheek and lower-face fullness. Existing overlapping head join retained.'},open(ROOT+'/tests/cheek_fullness_v11.json','w'),indent=2)
bpy.data.texts.load(ROOT+'/scripts/cheek_fullness_v11.py')
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/blender/apj_cheek_fullness_v11_master.blend')
s.render.filepath=ROOT+'/renders/cheek_fullness_v11_front.png';bpy.ops.render.render(write_still=True)
print(stats)
