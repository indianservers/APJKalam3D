"""Use baked UV maps for deformation-stable detail; retain driven wrinkle overlay."""
import bpy,math
m=bpy.data.objects['char1'];uvname=m.data.uv_layers[0].name
color=bpy.data.images['APJ_v3_Baked_Albedo_4K'];normal=bpy.data.images['APJ_v3_Baked_Normal_4K'];rough=bpy.data.images['APJ_v3_Baked_Roughness_4K']
attribute=m.data.color_attributes.get('ForeheadMask') or m.data.color_attributes.new(name='ForeheadMask',type='FLOAT_COLOR',domain='CORNER')
for poly in m.data.polygons:
    for li in poly.loop_indices:
        co=m.data.vertices[m.data.loops[li].vertex_index].co
        w=math.exp(-(co.x/.047)**2-((co.z-1.568)/.020)**2)*max(0,min(1,(-co.y-.055)/.025))
        attribute.data[li].color=(w,w,w,1)
for mat in m.data.materials:
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map=uvname
    def tex(im):
        n=nodes.new('ShaderNodeTexImage');n.image=im;links.new(uv.outputs['UV'],n.inputs['Vector']);return n
    c=tex(color);roughtex=tex(rough);normtex=tex(normal)
    nm=nodes.new('ShaderNodeNormalMap');links.new(normtex.outputs['Color'],nm.inputs['Color'])
    for bs in [n for n in nodes if n.type=='BSDF_PRINCIPLED']:
        links.new(c.outputs['Color'],bs.inputs['Base Color']);links.new(roughtex.outputs['Color'],bs.inputs['Roughness'])
        if bs.label.startswith('Aged skin'):
            wrinkle=next(n for n in nodes if n.type=='BUMP' and n.label=='Animated fine forehead detail')
            links.new(nm.outputs['Normal'],wrinkle.inputs['Normal'])
            coord=nodes.new('ShaderNodeUVMap');coord.uv_map='FaceProjection';sep=nodes.new('ShaderNodeSeparateXYZ');links.new(coord.outputs[0],sep.inputs[0])
            mul=nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=210;links.new(sep.outputs['Y'],mul.inputs[0])
            sine=nodes.new('ShaderNodeMath');sine.operation='SINE';links.new(mul.outputs[0],sine.inputs[0])
            att=nodes.new('ShaderNodeVertexColor');att.layer_name='ForeheadMask'
            mask=nodes.new('ShaderNodeMath');mask.operation='MULTIPLY';links.new(sine.outputs[0],mask.inputs[0]);links.new(att.outputs['Color'],mask.inputs[1]);links.new(mask.outputs[0],wrinkle.inputs['Height'])
            wrinkle.inputs['Strength'].driver_add('default_value').driver.expression='.18*max(a,b,c)'
            links.new(wrinkle.outputs['Normal'],bs.inputs['Normal'])
        else:links.new(nm.outputs['Normal'],bs.inputs['Normal'])
print('Appearance maps now use stable mesh UVs; wrinkle mask follows deformation')
