"""Clean source-to-target bake misses and clothing spill from reconstructed thumb.
Uses skin texels transferred from the source index finger for the new thumb UV island.
"""
import bpy,numpy as np,os
ROOT=r'C:\Abdul Kalam';im=bpy.data.images['APJ_Hands_Transferred_Albedo_2K']
w,h=im.size;rgba=np.empty(w*h*4,np.float32);im.pixels.foreach_get(rgba);rgba=rgba.reshape(h,w,4)
rgb=rgba[:,:,:3].copy();yy,xx=np.mgrid[0:h,0:w];u=xx/(w-1);v=yy/(h-1)
valid=(rgb[:,:,0]-rgb[:,:,1]>.055)&(rgb[:,:,1]-rgb[:,:,2]>.025)&(rgb[:,:,0]>.32)
refv=.015+np.mod(v-.015,.145);refy=np.clip((refv*(h-1)).astype(int),0,h-1)
ref=rgb[refy,xx].copy();refvalid=valid[refy,xx]
median=np.median(rgb[valid],axis=0)
for c in range(3):ref[:,:,c]=np.where(refvalid,ref[:,:,c],median[c])
bad=(~valid)|((v>=.595)&(v<=.723))
alpha=bad.astype(np.float32)
for _ in range(4):alpha=(alpha*4+np.roll(alpha,1,0)+np.roll(alpha,-1,0)+np.roll(alpha,1,1)+np.roll(alpha,-1,1))/8
alpha=np.maximum(alpha,bad)
rgb=rgb*(1-alpha[:,:,None])+ref*alpha[:,:,None]
rgba[:,:,:3]=rgb;im.pixels.foreach_set(rgba.ravel());im.update()
im.filepath_raw=os.path.join(ROOT,'textures','hands','APJ_Hands_Albedo_Transferred_Clean_2K.png');im.save();im.pack()
print('Cleaned projection misses; median source skin',median.tolist())
