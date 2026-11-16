"""Small dorsal tendon and MCP pad relief over the existing connected hand mesh."""
import bpy,math,json
ROOT=r'C:\Abdul Kalam';state=bpy.app.driver_namespace['apj_capture'];was=bpy.app.timers.is_registered(state['timer']);s=bpy.context.scene
if was:bpy.app.timers.unregister(state['timer'])
state['tracker'].reset();changes={}
for name in ['APJ_Hand_Left','APJ_Hand_Right']:
 obj=bpy.data.objects[name]
 if obj.get('tissue_v14'):continue
 moves=[]
 for vertex in obj.data.vertices:
  x,y,z=vertex.co;ax=abs(x)
  if .546<ax<.641 and z>1.303:
   t=max(0,min(1,(ax-.55)/.078));top=max(0,min(1,(z-1.303)/.009));window=math.sin(math.pi*t)**1.2;dz=0.
   for base in [-.020,.0035,.027,.049]:
    center=.009+(base-.009)*t
    dz+=.0011*math.exp(-((y-center)/.0035)**2)*window
    dz+=.00125*math.exp(-((ax-.624)/.008)**2-((y-base)/.007)**2)
   dz=min(.0022,dz)*top;vertex.co.z+=dz;moves.append(dz)
 obj.data.update();obj['tissue_v14']=True;changes[name]={'max_relief_m':max(moves,default=0),'vertex_count':len(obj.data.vertices)}
s.render.bake.normal_space='TANGENT';s.cycles.samples=8
for name in ['APJ_Hand_Left','APJ_Hand_Right']:
 obj=bpy.data.objects[name];mat=obj.data.materials[0];nodes=mat.node_tree.nodes;image=bpy.data.images['APJ14_'+name+'_Normal'];target=nodes.new('ShaderNodeTexImage');target.image=image;nodes.active=target
 for n in nodes:n.select=n==target
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 try:bpy.ops.object.bake(type='NORMAL');image.save();image.pack()
 finally:nodes.remove(target)
json.dump(changes,open(ROOT+'/tests/hand_tissue_v14.json','w'),indent=2)
if was:bpy.app.timers.register(state['timer'],first_interval=.03)
print(json.dumps(changes))
