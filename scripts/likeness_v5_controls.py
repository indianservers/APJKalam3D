import bpy,json
class APJLIKE_OT_reference(bpy.types.Operator):
    bl_idname='apjlike.reference';bl_label='Show reference smile'
    def execute(self,context):
        face=bpy.data.objects['APJ_Face'];ctrl=bpy.data.objects['APJ_Face_Controls']
        if ctrl.animation_data:ctrl.animation_data.action=None
        channels=json.loads(face['expression_channels'])+[p for p in ctrl.keys() if p.startswith('eyeLook')]+['gazeHorizontal','gazeVertical']
        pose=json.loads(face['reference_pose_v5'])
        for prop in channels:ctrl[prop]=float(pose.get(prop,0.))
        ctrl.update_tag();face.data.shape_keys.update_tag();context.scene.frame_set(context.scene.frame_current);return {'FINISHED'}
class APJLIKE_PT_reference(bpy.types.Panel):
    bl_label='APJ Reference Sculpt v5';bl_idname='APJLIKE_PT_reference';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='APJ Face'
    def draw(self,context):
        layout=self.layout;layout.operator('apjlike.reference');layout.operator('apjface.reset');layout.operator('apjface.demo');layout.label(text='Single-view likeness approximation',icon='INFO')
for cls in [APJLIKE_OT_reference,APJLIKE_PT_reference]:
    previous=getattr(bpy.types,cls.__name__,None)
    if previous:bpy.utils.unregister_class(previous)
    bpy.utils.register_class(cls)
