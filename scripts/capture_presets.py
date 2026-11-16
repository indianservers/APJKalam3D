"""Synthetic joint targets for deterministic seated and hand deformation checks."""
def point(x,y,z,visibility=1):return {'x':x,'y':-z,'z':y,'visibility':visibility}
def pose_packet(mode='standing'):
 p=[point(0,0,1.5) for _ in range(33)]
 for side,sign,sh,el,wr,hip,knee,ank,heel,toe in [('Left',1,11,13,15,23,25,27,29,31),('Right',-1,12,14,16,24,26,28,30,32)]:
  p[sh]=point(sign*.17,0,1.33);p[el]=point(sign*.22,-.015,1.12);p[wr]=point(sign*.22,-.04,.92)
  p[hip]=point(sign*.08,0,.90)
  if mode=='seated':
   p[knee]=point(sign*.11,-.34,.89);p[ank]=point(sign*.12,-.34,.53);p[heel]=point(sign*.12,-.32,.48);p[toe]=point(sign*.12,-.47,.48)
  else:
   p[knee]=point(sign*.11,-.02,.49);p[ank]=point(sign*.13,-.01,.13);p[heel]=point(sign*.13,.02,.04);p[toe]=point(sign*.15,-.18,.03)
 im=[dict(v,x=.5+v['x']*.5,y=.5-v['y']*-.5) for v in p]
 return {'pose':p,'poseImage':im,'hands':[],'face':{},'facePoints':[]}
