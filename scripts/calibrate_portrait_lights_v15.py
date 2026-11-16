"""Preserve known-good irradiance while moving studio sources near the portrait."""
import bpy,json
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';names=['Studio_Key','Studio_Fill','Studio_Rim'];target=Vector((0,0,1.52))
with bpy.data.libraries.load(ROOT+'/blender/apj_skin_v14_master.blend',link=False) as (src,dst):dst.objects=[n for n in names if n in src.objects]
report={}
settings={'Studio_Key':((-.35,-.90,1.78),.4),'Studio_Fill':((.40,-.80,1.60),.35),'Studio_Rim':((0,.40,1.80),.6)}
for name,old in zip(names,dst.objects):
 obj=bpy.data.objects[name];loc,size=settings[name];old_location=old.location.copy();old_distance=(old_location-target).length;new_distance=(Vector(loc)-target).length
 ratio=(new_distance**2+(size*.5)**2)/(old_distance**2+(old.data.size*.5)**2)
 obj.location=loc;obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler();obj.data.energy=old.data.energy*ratio*.85;obj.data.size=size;obj.data.color=(1.,.96,.91)
 report[name]={'old_position':list(old_location),'new_position':list(loc),'old_power':old.data.energy,'new_power':obj.data.energy}
 data=old.data;bpy.data.objects.remove(old)
 if data.users==0:bpy.data.lights.remove(data)
json.dump(report,open(ROOT+'/tests/reference_v15_lights.json','w'),indent=2);print(json.dumps(report))
