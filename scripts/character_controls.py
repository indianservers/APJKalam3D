"""Run in Blender Text Editor to install the APJ Development sidebar panel."""
import bpy

class APJ_OT_neutral(bpy.types.Operator):
    bl_idname='apj.neutral';bl_label='Reset to neutral'
    def execute(self,context):
        r=bpy.data.objects.get('Armature');m=bpy.data.objects.get('char1')
        if r:
            if r.animation_data:r.animation_data.action=None
            for b in r.pose.bones:b.matrix_basis.identity()
        if m and m.data.shape_keys:
            keys=m.data.shape_keys
            if keys.animation_data:keys.animation_data.action=None
            for k in keys.key_blocks:k.value=0
        return {'FINISHED'}

class APJ_OT_demo(bpy.types.Operator):
    bl_idname='apj.demo';bl_label='Load joint and face test animation'
    def execute(self,context):
        r=bpy.data.objects['Armature'];m=bpy.data.objects['char1']
        r.animation_data_create();r.animation_data.action=bpy.data.actions['APJ_Independent_Joint_And_Body_Test']
        for b in r.pose.bones:b.rotation_mode='XYZ'
        m.data.shape_keys.animation_data_create();m.data.shape_keys.animation_data.action=bpy.data.actions['APJ_Prototype_Face_Test']
        context.scene.frame_set(1)
        return {'FINISHED'}

class APJ_PT_controls(bpy.types.Panel):
    bl_label='APJ Development Controls';bl_idname='APJ_PT_controls'
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='APJ'
    def draw(self,context):
        layout=self.layout;r=bpy.data.objects.get('Armature');m=bpy.data.objects.get('char1')
        layout.label(text='Development mesh: facial rebuild required',icon='INFO')
        layout.operator('apj.neutral');layout.operator('apj.demo')
        layout.label(text='Demo: frames 1–360, 30 fps')
        if m and m.data.shape_keys:
            box=layout.box();box.label(text='Limited facial prototypes')
            for k in list(m.data.shape_keys.key_blocks)[1:]:box.prop(k,'value',text=k.name,slider=True)
        if r:
            layout.label(text='Reset neutral before manual posing')
            for side in ['Left','Right']:
                box=layout.box();box.label(text=side+' fingers: joint flexion')
                for f in ['Thumb','Index','Middle','Ring','Pinky']:
                    row=box.row();row.label(text=f)
                    for j in range(1,4):
                        b=r.pose.bones.get(f'{side}Hand{f}{j}')
                        if b:row.prop(b,'rotation_euler',index=2,text=str(j))

CLASSES=[APJ_OT_neutral,APJ_OT_demo,APJ_PT_controls]
for cls in CLASSES:
    previous=getattr(bpy.types,cls.__name__,None)
    if previous:bpy.utils.unregister_class(previous)
    bpy.utils.register_class(cls)
print('APJ panel registered in 3D View sidebar; N > APJ')
