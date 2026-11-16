"""Transport the sculpt field to the retained source-head skin underneath it."""
import bpy,math
from mathutils import Vector
from mathutils.kdtree import KDTree
face=bpy.data.objects['APJ_Face'];source=bpy.data.objects['SOURCE_Facial_v4_PreSculpt'];body=bpy.data.objects['char1']
old=source.data.shape_keys.key_blocks['Basis'];new=face.data.shape_keys.key_blocks['Basis'];kd=KDTree(len(old.data))
for i,p in enumerate(old.data):kd.insert(p.co,i)
kd.balance();deltas=[]
for point in body.data.shape_keys.key_blocks['Basis'].data:
    p=point.co;d=Vector()
    if 1.414<p.z<1.597 and p.y<.005 and abs(p.x)<.115:
        near=kd.find_n(p,4)
        if near and near[0][2]<.014:
            weights=[1/max(.0003,t[2])**2 for t in near];total=sum(weights)
            for (_,index,distance),weight in zip(near,weights):d+=(new.data[index].co-old.data[index].co)*(weight/total)
    deltas.append(d)
for key in body.data.shape_keys.key_blocks:
    for point,d in zip(key.data,deltas):point.co+=d
body.data.shape_keys.update_tag();body['v5_overlap_sculpt_matched']=True
print('Shared sculpt applied to retained head overlap:',sum(d.length>1e-5 for d in deltas),'vertices')
