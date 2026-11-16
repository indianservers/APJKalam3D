"""Reference-space fit for the exact appearance requested by the user."""
from pathlib import Path
import json,numpy as np
from PIL import Image
import mediapipe as mp
ROOT=Path(__file__).resolve().parents[1]
options=mp.tasks.vision.FaceLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(ROOT/'mocap/models/face_landmarker.task')),running_mode=mp.tasks.vision.RunningMode.IMAGE,num_faces=1,min_face_detection_confidence=.3,min_face_presence_confidence=.3)
data={}
with mp.tasks.vision.FaceLandmarker.create_from_options(options) as detector:
 for name,file in [('target','textures/reference_v15/exact_appearance_target.png'),('current','renders/skin_v14_face.png'),('old_projection','textures/appearance_v3/apj_face_projection_generated.png')]:
  pixels=np.array(Image.open(ROOT/file).convert('RGB'));r=detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=pixels))
  if not r.face_landmarks:raise RuntimeError('Face missing: '+name)
  p=np.array([[v.x,v.y] for v in r.face_landmarks[0][:468]]);data[name]={'points':p.tolist(),'size':[pixels.shape[1],pixels.shape[0]],'file':file}
def frame(p):
 a=p[[33,133]].mean(0);b=p[[263,362]].mean(0);v=b-a;dist=np.linalg.norm(v);e=v/dist;return (a+b)/2,e,np.array([-e[1],e[0]]),dist
ref=np.array(data['target']['points']);cur=np.array(data['current']['points']);rc,re,rp,rd=frame(ref);cc,ce,cp,cd=frame(cur)
target=cc+((ref-rc)@re/rd)[:,None]*cd*ce+((ref-rc)@rp/rd)[:,None]*cd*cp
def world(p):return np.stack(((p[:,0]-.5)*.30,1.52+(.5-p[:,1])*.30),axis=1)
indices=[1,2,4,5,6,98,327,49,279,64,294,97,326,61,291,13,14,0,17,37,267,39,269,40,270,181,405,84,314,87,317,70,63,105,66,107,336,296,334,293,300,10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109]
centers=world(cur[indices]);delta=world(target[indices])-centers
# Keep the eye centers fixed so eyeballs, gaze and contact systems stay registered.
mirror=centers.copy();mirror[:,0]*=-1;md=delta.copy();md[:,0]*=-1;centers=np.r_[centers,mirror];delta=np.r_[delta,md]
length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.006/np.maximum(length,1e-9))[:,None]
sigma=.021;kernel=np.exp(-np.sum((centers[:,None]-centers[None,:])**2,axis=2)/(2*sigma*sigma));weights=np.linalg.solve(kernel+np.eye(len(centers))*.08,delta)
# Texture UV fit from original projection to the exact supplied image.
source=np.array(data['old_projection']['points']);source[:,1]=1-source[:,1];uvtarget=ref.copy();uvtarget[:,1]=1-uvtarget[:,1];uvsigma=.10;k=np.exp(-np.sum((source[:,None]-source[None,:])**2,axis=2)/(2*uvsigma*uvsigma));uvw=np.linalg.solve(k+np.eye(468)*.002,uvtarget-source)
result={'measurements':data,'sculpt':{'centers':centers.tolist(),'weights':weights.tolist(),'sigma':sigma,'max_delta_m':.006},'uv':{'centers':source.tolist(),'weights':uvw.tolist(),'sigma':uvsigma},'mean_requested_landmark_delta_m':float(np.linalg.norm(world(target[indices])-world(cur[indices]),axis=1).mean()),'note':'Single-image eye-aligned proportion guidance, not an exact likeness score or hidden-depth reconstruction'}
(ROOT/'tests/reference_v15_fit.json').write_text(json.dumps(result),encoding='utf-8');print('Requested mean landmark displacement mm',result['mean_requested_landmark_delta_m']*1000)
