"""Meaningful expression targets, geometric wrinkle correctives, jaw and gaze."""
import bpy,math,json,os
from mathutils import Vector,Matrix
face=bpy.data.objects['APJ_Face'];rig=bpy.data.objects['Armature'];eyes=json.loads(face['eye_info']);tags=json.loads(face['boundary_tags']);mz=face['mouth_center_z']
ctrl=bpy.data.objects.new('APJ_Face_Controls',None);bpy.context.scene.collection.objects.link(ctrl);ctrl.empty_display_size=.08;ctrl.location=(0,-.27,1.52);ctrl.hide_render=True
names=['browInnerUp','browOuterUpLeft','browOuterUpRight','browDownLeft','browDownRight',
 'eyeBlinkLeft','eyeBlinkRight','eyeWideLeft','eyeWideRight','eyeSquintLeft','eyeSquintRight','cheekSquintLeft','cheekSquintRight',
 'jawOpen','jawLeft','jawRight','jawForward','mouthSmileLeft','mouthSmileRight','mouthFrownLeft','mouthFrownRight',
 'mouthStretchLeft','mouthStretchRight','mouthPucker','mouthFunnel','mouthClose','mouthPressLeft','mouthPressRight',
 'mouthUpperUpLeft','mouthUpperUpRight','mouthLowerDownLeft','mouthLowerDownRight','cheekPuff','noseSneerLeft','noseSneerRight']
gazenames=['eyeLookUpLeft','eyeLookDownLeft','eyeLookInLeft','eyeLookOutLeft','eyeLookUpRight','eyeLookDownRight','eyeLookInRight','eyeLookOutRight']
for name in names+gazenames:
    ctrl[name]=0.;ctrl.id_properties_ui(name).update(min=0.,max=1.,soft_min=0.,soft_max=1.)
for name in ['gazeHorizontal','gazeVertical']:
    ctrl[name]=0.;ctrl.id_properties_ui(name).update(min=-1.,max=1.,soft_min=-1.,soft_max=1.)
ctrl['jaw_angle_max_degrees']=math.degrees(.20)
def g(x,c,w):return math.exp(-((x-c)/w)**2)
def sideweight(x,side):return .5*(1+math.tanh(side*x/.005))
def border(p):
    width=float(__import__('numpy').interp(p.z,[1.407,1.425,1.45,1.49,1.525,1.555,1.595],[.039,.058,.077,.085,.081,.071,.061]))
    return max(0,min(1,(1-abs(p.x)/width)/.12))*max(0,min(1,(p.z-1.409)/.010))*max(0,min(1,(1.595-p.z)/.006))
def jawweight(p):
    lower=max(0,min(1,(mz+.00025-p.z)/.0008));neck=max(0,min(1,(p.z-1.416)/.018));return lower*neck*border(p)
hinge=Vector((0,.005,1.471));rotation=Matrix.Rotation(.20,3,'X')
base=[v.co.copy() for v in face.data.vertices];borders=[border(p) for p in base]
jawdelta=[(hinge+rotation@(p-hinge)-p)*jawweight(p) for p in base]
tagsets={name:set(ids) for name,ids in tags.items()}
face.shape_key_add(name='Basis')
def eyelid(p,side,kind,index):
    h=eyes[side];dx=p.x-h['x'];dz=p.z-h['z'];r=math.sqrt((dx/h['rx'])**2+(dz/.0045)**2)
    w=math.exp(-(max(0,r-1)/.72)**2)
    if r>3.5:return Vector()
    margin=index in tagsets[side]
    if not margin:w=min(w,.86)
    if kind=='wide':z=p.z+(.0019 if dz>=0 else -.0009)*w
    else:
        target=h['z']+.00025*(dx/h['rx'])*(1 if side=='Left' else -1)
        z=p.z+(target-p.z)*w
    disc=(h['radius']+.00014)**2-dx*dx-(z-h['z'])**2
    y=p.y
    if disc>0:
        contact=h['cy']-math.sqrt(disc)-.0012
        y=contact if margin else min(p.y,contact)
    return Vector((0,y-p.y,z-p.z))
counts={}
for name in names:
    key=face.shape_key_add(name=name);count=0
    side=1 if name.endswith('Left') else -1 if name.endswith('Right') else 0
    for i,(p,dst) in enumerate(zip(base,key.data)):
        x,y,z=p;delta=Vector();sw=sideweight(x,side) if side else 1
        lip=g(x,0,.037)*g(z,mz,.010);corner=g(x,side*.026,.016)*g(z,mz,.012) if side else 0
        if name=='browInnerUp':delta.z=.0065*g(x,0,.028)*g(z,1.542,.023);delta.y=-.0005*g(x,0,.035)*g(z,1.55,.025)
        elif name.startswith('browOuterUp'):delta.z=.006*g(x,side*.042,.026)*g(z,1.541,.020)
        elif name.startswith('browDown'):
            w=g(x,side*.032,.027)*g(z,1.539,.020);delta=Vector((-side*.003*w,.0005*w,-.0045*w))
        elif name.startswith('eyeBlink'):delta=eyelid(p,'Left' if side==1 else 'Right','blink',i)
        elif name.startswith('eyeWide'):delta=eyelid(p,'Left' if side==1 else 'Right','wide',i)
        elif name.startswith('eyeSquint'):delta=eyelid(p,'Left' if side==1 else 'Right','blink',i)*.42
        elif name.startswith('cheekSquint'):
            w=g(x,side*.042,.023)*g(z,1.495,.018);delta=Vector((0,-.0014*w,.0032*w))
        elif name=='jawOpen':delta=jawdelta[i]
        elif name in ('jawLeft','jawRight'):delta.x=(.003 if name=='jawLeft' else -.003)*jawweight(p)
        elif name=='jawForward':delta.y=-.003*jawweight(p)
        elif name.startswith('mouthSmile'):
            cheek=g(x,side*.045,.026)*g(z,1.479,.023);delta=Vector((side*.0045*corner,-.0014*corner-.0008*cheek,.006*corner+.0022*cheek))
        elif name.startswith('mouthFrown'):delta=Vector((-side*.001*corner,.0004*corner,-.0045*corner))
        elif name.startswith('mouthStretch'):delta=Vector((side*.006*corner,0,.0008*corner))
        elif name=='mouthPucker':delta=Vector((-x*.26*lip,-.0045*lip,(mz-z)*.12*lip))
        elif name=='mouthFunnel':delta=Vector((-x*.13*lip,-.0035*lip,(.003 if z>=mz else -.0035)*lip))
        elif name=='mouthClose':delta=-jawdelta[i]*g(z,mz-.002,.010)*g(x,0,.037)
        elif name.startswith('mouthPress'):delta=Vector((0,.0012*lip*sw,(mz-z)*.25*lip*sw))
        elif name.startswith('mouthUpperUp'):
            w=lip*sw*max(0,min(1,(z-mz+.001)/.003));delta=Vector((0,-.0006*w,.0034*w))
        elif name.startswith('mouthLowerDown'):
            w=lip*sw*max(0,min(1,(mz-z+.001)/.003));delta=Vector((0,-.0003*w,-.0038*w))
        elif name=='cheekPuff':delta=Vector((math.copysign(.0015,x)*g(abs(x),.048,.024)*g(z,1.478,.024),-.0032*g(abs(x),.048,.024)*g(z,1.478,.024),0))
        elif name.startswith('noseSneer'):
            w=g(x,side*.020,.014)*g(z,1.477,.017);delta=Vector((side*.0008*w,-.0008*w,.0033*w))
        if name!='jawOpen':delta*=borders[i]
        dst.co=p+delta
        if delta.length>1e-5:count+=1
    counts[name]=count

# Correctives move real skin vertices; the permanent texture remains visible at neutral.
correctives=['WRINKLE_BrowRaise','WRINKLE_Frown','WRINKLE_SmileLeft','WRINKLE_SmileRight','WRINKLE_SquintLeft','WRINKLE_SquintRight']
for name in correctives:
    key=face.shape_key_add(name=name);count=0;side=1 if name.endswith('Left') else -1
    for i,(p,dst) in enumerate(zip(base,key.data)):
        x,y,z=p;dy=0.
        if name=='WRINKLE_BrowRaise':
            for line in [1.551,1.560,1.569,1.578]:
                curve=line+.0014*math.cos(x*45);dy+=(.00034*g(z,curve,.00065)-.00016*g(z,curve+.0011,.0008))*g(x,0,.049)
        elif name=='WRINKLE_Frown':
            for line in [-.007,.007]:dy+=(.00035*g(x,line,.0007)-.00015*g(x,line+.001,.0008))*g(z,1.543,.014)
        else:
            cx=side*.046;cz=1.513
            for slope in [-.45,0,.45]:
                line=cz+slope*(side*x-.047)
                dy+=.00025*g(z,line,.00065)*g(x,side*.057,.014)
            if 'Smile' in name:dy+=.00025*g(x,side*(.026+.35*(1.475-z)),.0012)*g(z,1.472,.016)
        delta=Vector((0,dy*borders[i],0));dst.co=p+delta
        if delta.length>1e-6:count+=1
    counts[name]=count

def driver(target,path,variables,expression,index=None):
    fc=target.driver_add(path) if index is None else target.driver_add(path,index)
    d=fc.driver;d.type='SCRIPTED'
    for varname,prop in variables.items():
        var=d.variables.new();var.name=varname;var.type='SINGLE_PROP';var.targets[0].id=ctrl;var.targets[0].data_path='["'+prop+'"]'
    d.expression=expression;return d
for name in names:
    variables={'v':name};expr='v'
    if name.startswith('eyeSquint') or name.startswith('eyeWide'):
        variables['b']='eyeBlinkLeft' if name.endswith('Left') else 'eyeBlinkRight';expr='v*(1-b)'
    if name=='mouthClose':variables['j']='jawOpen';expr='v*j'
    driver(face.data.shape_keys.key_blocks[name],'value',variables,expr)
driver(face.data.shape_keys.key_blocks['WRINKLE_BrowRaise'],'value',{'a':'browInnerUp','b':'browOuterUpLeft','c':'browOuterUpRight'},'max(a,b,c)')
driver(face.data.shape_keys.key_blocks['WRINKLE_Frown'],'value',{'a':'browDownLeft','b':'browDownRight'},'max(a,b)')
for side in ['Left','Right']:
    driver(face.data.shape_keys.key_blocks['WRINKLE_Smile'+side],'value',{'v':'mouthSmile'+side},'v')
    driver(face.data.shape_keys.key_blocks['WRINKLE_Squint'+side],'value',{'v':'eyeSquint'+side,'b':'eyeBlink'+side},'v*(1-b)')
jaw=rig.pose.bones['Jaw'];jaw.rotation_mode='XYZ'
driver(jaw,'rotation_euler',{'v':'jawOpen'},'.20*v',0)
driver(jaw,'location',{'l':'jawLeft','r':'jawRight'},'.003*(l-r)',0)
driver(jaw,'location',{'v':'jawForward'},'-.003*v',2)
for side in ['Left','Right']:
    bone=rig.pose.bones['Eye.'+side[0]];bone.rotation_mode='XYZ'
    driver(bone,'rotation_euler',{'u':'eyeLookUp'+side,'d':'eyeLookDown'+side,'g':'gazeVertical'},'max(-.28,min(.28,.24*(u-d+g)))',0)
    sign=1 if side=='Left' else -1
    driver(bone,'rotation_euler',{'o':'eyeLookOut'+side,'i':'eyeLookIn'+side,'g':'gazeHorizontal'},f'max(-.30,min(.30,.28*(g+{sign}*(o-i))))',2)

# A shader wrinkle layer responds to the same controls; UV-based mask follows skin.
mat=face.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links;bs=next(x for x in n if x.type=='BSDF_PRINCIPLED');old=bs.inputs['Normal'].links[0].from_socket
uv=n.new('ShaderNodeUVMap');uv.uv_map='FaceProjection';sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs[0],sep.inputs[0])
wave=n.new('ShaderNodeMath');wave.operation='MULTIPLY';wave.inputs[1].default_value=210;l.new(sep.outputs['Y'],wave.inputs[0])
sine=n.new('ShaderNodeMath');sine.operation='SINE';l.new(wave.outputs[0],sine.inputs[0])
attr=face.data.color_attributes.new(name='FacialWrinkleMask',type='FLOAT_COLOR',domain='CORNER')
for p in face.data.polygons:
    for li in p.loop_indices:
        v=base[face.data.loops[li].vertex_index];w=g(v.x,0,.048)*g(v.z,1.566,.026);attr.data[li].color=(w,w,w,1)
vertex=n.new('ShaderNodeVertexColor');vertex.layer_name='FacialWrinkleMask';mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(vertex.outputs['Color'],mask.inputs[0]);l.new(sine.outputs[0],mask.inputs[1])
wrinkle=n.new('ShaderNodeBump');wrinkle.label='V4 Dynamic Wrinkle Shader';wrinkle.inputs['Distance'].default_value=.00009;l.new(mask.outputs[0],wrinkle.inputs['Height']);l.new(old,wrinkle.inputs['Normal']);l.new(wrinkle.outputs[0],bs.inputs['Normal'])
driver(wrinkle.inputs['Strength'],'default_value',{'a':'browInnerUp','b':'browOuterUpLeft','c':'browOuterUpRight','d':'browDownLeft','e':'browDownRight'},'.20*max(a,b,c,d,e)')
face['expression_channels']=json.dumps(names);face['wrinkle_correctives']=json.dumps(correctives)
mapping={'mesh':face.name,'controller':ctrl.name,'coefficients':{name:{'shape_key':name,'property':name} for name in names},
 'gaze':{name:{'bone_control':True,'property':name} for name in gazenames},'global_gaze':['gazeHorizontal','gazeVertical'],
 'jaw_bone':'Jaw','eye_bones':['Eye.L','Eye.R'],'unsupported':'All remaining coefficients; no full 52-coefficient certification',
 'range_notes':'Coefficients 0..1; global gaze -1..1; jaw opening max 11.46 degrees; eye yaw 17.2 and pitch 16 degrees'}
with open(r'C:\Abdul Kalam\mocap\facial_v4_mapping.json','w') as f:json.dump(mapping,f,indent=2)
with open(r'C:\Abdul Kalam\tests\facial_v4_build.json','w') as f:json.dump({'affected_vertices':counts,'shape_targets':len(names)+len(correctives),'coefficient_properties':len(names)+len(gazenames),'bones':len(rig.data.bones)},f,indent=2)
print('Facial controls:',len(names),'expression targets,',len(correctives),'geometric wrinkle correctives, 8 gaze coefficients, jaw and two eye bones')
