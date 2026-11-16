"""Functional expression, jaw, gaze, wrinkle and eyelid-contact verification."""
import bpy,bmesh,json,os,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=r'C:\Abdul Kalam';face=bpy.data.objects['APJ_Face'];rig=bpy.data.objects['Armature'];c=bpy.data.objects['APJ_Face_Controls'];keys=face.data.shape_keys;s=bpy.context.scene
names=json.loads(face['expression_channels']);gaze=[p for p in c.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical'];allchannels=names+gaze
if c.animation_data:c.animation_data.action=None
def apply(values={}):
    for name in allchannels:c[name]=float(values.get(name,0.))
    c.update_tag();keys.update_tag();rig.update_tag();s.frame_set(s.frame_current+1);bpy.context.view_layer.update()
def vertices(o):
    bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();values=np.array([tuple(o.matrix_world@v.co) for v in me.vertices],dtype=np.float64);ev.to_mesh_clear();return values
def delta(a,b):return float(np.linalg.norm(a-b,axis=1).max())
apply();neutral=vertices(face);tests=[]
for name in names:
    dependency={'jawOpen':.7} if name=='mouthClose' else {}
    apply(dependency);base=vertices(face);apply({**dependency,name:1.});result=vertices(face);d=delta(base,result)
    tests.append({'control':name,'max_evaluated_displacement_m':d,'shape_value':keys.key_blocks[name].value,'pass':bool(d>1e-5 and np.isfinite(result).all())})

# Eyeballs rotate about a fixed centre, independently or together.
for name in gaze:
    apply();before={side:bpy.data.objects['APJ_Eye_'+side+'_Globe'].matrix_world.copy() for side in ['Left','Right']}
    apply({name:.8});angles={};centre_errors={}
    for side in ['Left','Right']:
        matrix=bpy.data.objects['APJ_Eye_'+side+'_Globe'].matrix_world
        angles[side]=before[side].to_quaternion().rotation_difference(matrix.to_quaternion()).angle
        centre_errors[side]=(matrix.translation-before[side].translation).length
    intended=['Left','Right'] if name.startswith('gaze') else ['Left'] if name.endswith('Left') else ['Right']
    passed=all(angles[side]>.02 and centre_errors[side]<1e-5 for side in intended) and all(angles[side]<1e-5 for side in angles if side not in intended)
    tests.append({'control':name,'rotation_radians':angles,'centre_errors_m':centre_errors,'pass':passed})

# Jaw moves the lower dentition and tongue; maxillary teeth remain on the head.
apply();upper=bpy.data.objects['APJ_Teeth_Upper_07'];lower=bpy.data.objects['APJ_Teeth_Lower_07'];tongue=bpy.data.objects['APJ_Tongue']
u0=vertices(upper);l0=vertices(lower);t0=vertices(tongue);apply({'jawOpen':.8})
jaw={'rotation_radians':rig.pose.bones['Jaw'].rotation_euler.x,'upper_teeth_displacement_m':delta(u0,vertices(upper)),'lower_teeth_displacement_m':delta(l0,vertices(lower)),'tongue_displacement_m':delta(t0,vertices(tongue))}
jaw['pass']=jaw['upper_teeth_displacement_m']<1e-6 and jaw['lower_teeth_displacement_m']>.005 and jaw['tongue_displacement_m']>.005

# Occlusion is measured against the actual evaluated facial surface.
eyes=json.loads(face['eye_info'])
def occlusion(side):
    h=eyes[side];bv=BVHTree.FromObject(face,bpy.context.evaluated_depsgraph_get());covered=0;total=0
    for x in np.linspace(-.0065,.0065,15):
      for z in np.linspace(-.0021,.0021,9):
        if (x/.007)**2+(z/.0025)**2>1:continue
        xx=h['x']+float(x);zz=h['z']+float(z);hit=bv.ray_cast(Vector((xx,-.5,zz)),Vector((0,1,0)))[0]
        front=h['cy']-math.sqrt((h['radius']+.00014)**2-x*x-z*z);covered+=int(hit is not None and hit.y<=front+.00005);total+=1
    return covered/total
blink=[]
for side in eyes:
    apply();open_cover=occlusion(side);apply({'eyeBlink'+side:1.});closed_cover=occlusion(side)
    other='Right' if side=='Left' else 'Left';other_cover=occlusion(other)
    blink.append({'side':side,'neutral_covered_fraction':open_cover,'blink_covered_fraction':closed_cover,'other_eye_covered_fraction':other_cover,'pass':closed_cover>.95 and open_cover<.25 and other_cover<.25})

# Geometric wrinkle deformation is isolated from the larger brow raise.
apply({'browInnerUp':1.});wrinkle_key=keys.key_blocks['WRINKLE_BrowRaise'];driver=next(fc for fc in keys.animation_data.drivers if 'WRINKLE_BrowRaise' in fc.data_path)
driven_value=wrinkle_key.value;driver.mute=True;wrinkle_key.value=0.;keys.update_tag();bpy.context.view_layer.update();without=vertices(face)
driver.mute=False;keys.update_tag();s.frame_set(s.frame_current+1);bpy.context.view_layer.update();with_wrinkle=vertices(face)
wrinkle={'driven_value':driven_value,'isolated_geometry_displacement_m':delta(without,with_wrinkle)};wrinkle['pass']=driven_value>.9 and wrinkle['isolated_geometry_displacement_m']>3e-5

combinations=[]
for label,values in [('smile_jaw',{'jawOpen':.6,'mouthSmileLeft':.6,'mouthSmileRight':.6}),('blink_wide',{'eyeBlinkLeft':1.,'eyeWideLeft':1.}),('blink_squint',{'eyeBlinkLeft':1.,'eyeSquintLeft':1.}),('frown',{'browDownLeft':.8,'browDownRight':.8}),('funnel_jaw',{'jawOpen':.4,'mouthFunnel':.6}),('pucker',{'mouthPucker':.7})]:
    apply(values);v=vertices(face);item={'label':label,'max_displacement_m':delta(neutral,v),'finite':bool(np.isfinite(v).all())}
    if label.startswith('blink'):item['closed_eye_covered_fraction']=occlusion('Left')
    item['pass']=item['finite'] and item.get('closed_eye_covered_fraction',1)>.95;combinations.append(item)
apply();reset_error=delta(neutral,vertices(face))
bm=bmesh.new();bm.from_mesh(face.data);topology={'vertices':len(bm.verts),'quads':sum(len(f.verts)==4 for f in bm.faces),'faces':len(bm.faces),'junction_edges':sum(len(e.link_faces)>2 for e in bm.edges),'boundary_edges':sum(e.is_boundary for e in bm.edges),'rest_degenerate_faces':sum(f.calc_area()<1e-13 for f in bm.faces)};bm.free()
report={'production_ready':False,'expression_tests':tests,'jaw':jaw,'blink_occlusion':blink,'geometric_wrinkle':wrinkle,'combinations':combinations,'reset_error_m':reset_error,'topology':topology,
 'all_functional_checks_pass':bool(all(t['pass'] for t in tests) and jaw['pass'] and all(t['pass'] for t in blink) and wrinkle['pass'] and all(t['pass'] for t in combinations) and reset_error<1e-7),
 'limitations':['Reconstructed face overlaps the original head; not a welded full-head retopology','Skin contact uses Blender shrinkwrap correction','Artistic expression shapes require production review','No live capture or automated audio synchronization tested','Extreme expressions and broad phoneme coverage remain limited']}
output=globals().get('FACIAL_VALIDATION_OUTPUT',os.path.join(ROOT,'tests','facial_v4_validation.json'))
with open(output,'w') as f:json.dump(report,f,indent=2)
s.frame_set(1)
print(json.dumps({k:v for k,v in report.items() if k not in ['expression_tests','limitations']},default=str))
print('FAILED CONTROLS',[t['control'] for t in tests if not t['pass']])
