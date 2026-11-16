import bpy,json
face=bpy.data.objects['APJ_Face']
for side,h in json.loads(face['eye_info']).items():
    group=face.vertex_groups.new(name='MASK_EyeContact_'+side)
    ids=[v.index for v in face.data.vertices if (v.co.x-h['x'])**2+(v.co.z-h['z'])**2<.017**2]
    group.add(ids,1.,'REPLACE')
    mod=face.modifiers.new('Corneal contact '+side,'SHRINKWRAP');mod.target=bpy.data.objects['APJ_Eye_'+side+'_Cornea'];mod.vertex_group=group.name
    mod.wrap_method='NEAREST_SURFACEPOINT';mod.wrap_mode='OUTSIDE';mod.offset=.0006
