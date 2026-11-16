"""Fit a bounded smooth 2D sculpt field to eye-aligned reference landmarks.
Only image-plane proportions are constrained; this does not infer scanned depth.
"""
import json,math
from pathlib import Path
import numpy as np
ROOT=Path(r'C:\Abdul Kalam');data=json.load(open(ROOT/'tests/sculpt_v5_landmarks.json'))
def points(record):return np.array(record['landmarks'])[:,:2]*np.array(record['size'])
ref=points(data['reference']);model=points(data['render'])
def frame(p):
    a=p[[33,133]].mean(0);b=p[[263,362]].mean(0);v=b-a;dist=np.linalg.norm(v);e=v/dist;perp=np.array([-e[1],e[0]]);return (a+b)/2,e,perp,dist
rc,re,rp,rd=frame(ref);mc,me,mp,md=frame(model)
canonical=np.stack(((ref-rc)@re/rd,-(ref-rc)@rp/rd),axis=1)
target=mc+canonical[:,:1]*md*me-canonical[:,1:]*md*mp
w,h=data['render']['size']
def world(p):return np.stack(((p[:,0]/w-.5)*.30,1.52+(.5-p[:,1]/h)*.30),axis=1)
sourceworld=world(model);targetworld=world(target)
selected=[1,2,4,5,6,98,327,49,279,64,294,97,326,61,291,13,14,0,17,37,267,39,269,40,270,181,405,84,314,87,317,
 70,63,105,66,107,336,296,334,293,300,10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109]
centres=sourceworld[selected];raw=targetworld[selected]-centres
length=np.linalg.norm(raw,axis=1);bounded=raw*np.minimum(1,.004/np.maximum(length,1e-9))[:,None]
# Mild bilateral averaging prevents camera yaw being sculpted into facial asymmetry.
mid=world(mc[None,:])[0,0]
mirrored=centres.copy();mirrored[:,0]=2*mid-mirrored[:,0];mirror_delta=bounded.copy();mirror_delta[:,0]*=-1
centres=np.concatenate([centres,mirrored]);delta=np.concatenate([bounded,mirror_delta])
anchors=np.array([[.0347,1.5148],[-.0345,1.5148],[.0455,1.5148],[.0239,1.5148],[-.0453,1.5148],[-.0237,1.5148]])
centres=np.concatenate([centres,anchors]);delta=np.concatenate([delta,np.zeros_like(anchors)])
sigma=.023;dist=((centres[:,None,:]-centres[None,:,:])**2).sum(2);kernel=np.exp(-dist/(2*sigma*sigma));regularizer=np.ones(len(centres))*.055;regularizer[-len(anchors):]=.0005
weights=np.linalg.solve(kernel+np.diag(regularizer),delta)
def evaluate(p):
    d=((p[:,None,:]-centres[None,:,:])**2).sum(2);result=np.exp(-d/(2*sigma*sigma))@weights
    lens=np.linalg.norm(result,axis=1);result*=np.minimum(1,.004/np.maximum(lens,1e-9))[:,None]
    mask=np.ones(len(p))
    for x in [-.0345,.0347]:mask*=1-.98*np.exp(-((p[:,0]-x)/.014)**2-((p[:,1]-1.5148)/.014)**2)
    return result*mask[:,None]
pred=evaluate(sourceworld[selected]);before=np.linalg.norm(raw,axis=1);after=np.linalg.norm(raw-pred,axis=1)
result={'centres':centres.tolist(),'weights':weights.tolist(),'sigma':sigma,'max_displacement_m':.004,'selected_indices':selected,
 'before_mean_eye_aligned_landmark_error_m':float(before.mean()),'predicted_mean_error_m':float(after.mean()),
 'coordinate_plane':'world X/Z from the 0.30 m orthographic frontal camera','limits':'Single-view, detector-estimated landmarks; not a metric 3D scan or likeness certification'}
json.dump(result,open(ROOT/'tests/sculpt_v5_fit_field.json','w'),indent=2)
print('Mean eye-aligned image-plane error mm:',before.mean()*1000,'predicted',after.mean()*1000)
