"""Facial performance test and Blender sidebar. Safe to rerun to register UI."""
import bpy,json,os
ROOT=r'C:\Abdul Kalam'
def controller():return bpy.data.objects['APJ_Face_Controls']
def channels():
    c=controller();return json.loads(bpy.data.objects['APJ_Face']['expression_channels'])+[p for p in c.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']
def reset_face(detach=True):
    c=controller()
    if detach and c.animation_data:c.animation_data.action=None
    for name in channels():c[name]=0.
    c.update_tag();bpy.data.objects['APJ_Face'].data.shape_keys.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update()
PRESETS={
 'Brows':{'browInnerUp':.9,'browOuterUpLeft':.55,'browOuterUpRight':.55},
 'Frown':{'browDownLeft':.8,'browDownRight':.8},
 'Smile':{'mouthSmileLeft':.75,'mouthSmileRight':.75,'cheekSquintLeft':.20,'cheekSquintRight':.20},
 'Blink':{'eyeBlinkLeft':1.,'eyeBlinkRight':1.},
 'Jaw':{'jawOpen':.70},
 'A':{'jawOpen':.65},'E':{'jawOpen':.20,'mouthStretchLeft':.55,'mouthStretchRight':.55},
 'O':{'jawOpen':.40,'mouthFunnel':.60,'mouthPucker':.20},
 'M':{'jawOpen':.10,'mouthClose':1.,'mouthPressLeft':.55,'mouthPressRight':.55}}
def preset(name):
    reset_face();c=controller()
    for prop,value in PRESETS[name].items():c[prop]=float(value)
    c.update_tag();bpy.data.objects['APJ_Face'].data.shape_keys.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current)

POSES=[(30,'BROWS',PRESETS['Brows']),(75,'FROWN',PRESETS['Frown']),(120,'SMILE',PRESETS['Smile']),
 (165,'SQUINT',{'eyeSquintLeft':.7,'eyeSquintRight':.7}),
 (210,'BLINK_BOTH',PRESETS['Blink']),(240,'BLINK_LEFT',{'eyeBlinkLeft':1.}),(270,'BLINK_RIGHT',{'eyeBlinkRight':1.}),
 (315,'JAW_OPEN',PRESETS['Jaw']),(360,'PUCKER',{'mouthPucker':.7}),(405,'FUNNEL',{'jawOpen':.3,'mouthFunnel':.6}),
 (450,'GAZE_LEFT',{'gazeHorizontal':.8}),(480,'GAZE_UP',{'gazeVertical':.7}),
 (525,'SMILE_AND_JAW',{'jawOpen':.45,'mouthSmileLeft':.55,'mouthSmileRight':.55}),
 (570,'SPEECH_E',PRESETS['E'])]
if not bpy.data.actions.get('APJ_Facial_v4_Demonstration'):
    reset_face();c=controller();c.animation_data_create();action=bpy.data.actions.new('APJ_Facial_v4_Demonstration');action.use_fake_user=True;c.animation_data.action=action
    values={1:{},600:{}}
    for frame,label,pose in POSES:values[frame-10]={};values[frame]=pose;values[frame+10]={}
    for frame,pose in sorted(values.items()):
        for name in channels():c[name]=float(pose.get(name,0.));c.keyframe_insert(data_path='["'+name+'"]',frame=frame,group='Facial Controls')
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag=strip.channelbag(slot)
                if bag:
                    for fc in bag.fcurves:
                        for kp in fc.keyframe_points:kp.interpolation='LINEAR'
    s=bpy.context.scene;s.frame_start=1;s.frame_end=600;s.render.fps=30
    for frame,label,pose in POSES:s.timeline_markers.new('FACE_'+label,frame=frame)
    s.timeline_markers.new('FACE_NEUTRAL',frame=1);s.timeline_markers.new('FACE_NEUTRAL_END',frame=600)
    c.animation_data.action=action;s.frame_set(1)
    with open(os.path.join(ROOT,'tests','facial_v4_demo_poses.json'),'w') as f:json.dump([{'frame':fr,'label':label,'controls':p} for fr,label,p in POSES],f,indent=2)

class APJFACE_OT_reset(bpy.types.Operator):
    bl_idname='apjface.reset';bl_label='Reset face to neutral'
    def execute(self,context):reset_face();return {'FINISHED'}
class APJFACE_OT_demo(bpy.types.Operator):
    bl_idname='apjface.demo';bl_label='Load 20-second facial demo'
    def execute(self,context):
        reset_face()
        c=controller();c.animation_data_create();c.animation_data.action=bpy.data.actions['APJ_Facial_v4_Demonstration'];context.scene.frame_set(1);return {'FINISHED'}
class APJFACE_OT_preset(bpy.types.Operator):
    bl_idname='apjface.preset';bl_label='Expression preset';expression:bpy.props.StringProperty()
    def execute(self,context):preset(self.expression);return {'FINISHED'}
class APJFACE_PT_controls(bpy.types.Panel):
    bl_label='APJ Facial Animation v4';bl_idname='APJFACE_PT_controls';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='APJ Face'
    def draw(self,context):
        layout=self.layout;c=bpy.data.objects.get('APJ_Face_Controls')
        if not c:layout.label(text='Open facial v4 master');return
        layout.operator('apjface.reset');layout.operator('apjface.demo');layout.label(text='Demo frames 1–600 at 30 fps')
        row=layout.row()
        for name in ['Brows','Frown','Smile','Blink','Jaw']:
            op=row.operator('apjface.preset',text=name);op.expression=name
        row=layout.row();row.label(text='Speech shape tests')
        for name in ['A','E','O','M']:
            op=row.operator('apjface.preset',text=name);op.expression=name
        groups=[('Brow',['brow']),('Eyes and gaze',['eye']),('Cheeks and nose',['cheek','nose']),('Jaw',['jaw']),('Mouth',['mouth'])]
        available=channels()
        for label,prefixes in groups:
            box=layout.box();box.label(text=label)
            for name in available:
                if any(name.startswith(p) for p in prefixes):box.prop(c,'["'+name+'"]',text=name,slider=True)
        box=layout.box();box.label(text='Combined gaze')
        for name in ['gazeHorizontal','gazeVertical']:box.prop(c,'["'+name+'"]',text=name,slider=True)
        layout.label(text='Reset detaches demo for manual controls',icon='INFO')
CLASSES=[APJFACE_OT_reset,APJFACE_OT_demo,APJFACE_OT_preset,APJFACE_PT_controls]
for cls in CLASSES:
    old=getattr(bpy.types,cls.__name__,None)
    if old:bpy.utils.unregister_class(old)
    bpy.utils.register_class(cls)
print('Facial demo and N sidebar > APJ Face ready')
