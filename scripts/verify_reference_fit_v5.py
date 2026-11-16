import json,numpy as np
from pathlib import Path
ROOT=Path(r'C:\Abdul Kalam');data=json.load(open(ROOT/'tests/sculpt_v5_landmarks.json'));fit=json.load(open(ROOT/'tests/sculpt_v5_fit_field.json'))
def points(record):return np.array(record['landmarks'])[:,:2]*np.array(record['size'])
def frame(p):
    a=p[[33,133]].mean(0);b=p[[263,362]].mean(0);e=(b-a)/np.linalg.norm(b-a);return (a+b)/2,e,np.array([-e[1],e[0]]),np.linalg.norm(b-a)
ref=points(data['reference']);p=points(data['render']);rc,re,rp,rd=frame(ref);mc,me,mp,md=frame(p)
canonical=np.stack(((ref-rc)@re/rd,-(ref-rc)@rp/rd),1);target=mc+canonical[:,:1]*md*me-canonical[:,1:]*md*mp
w,h=data['render']['size'];delta=(target-p)*np.array([.30/w,.30/h]);error=np.linalg.norm(delta[fit['selected_indices']],axis=1)
report={'before_mean_eye_aligned_image_plane_error_m':fit['before_mean_eye_aligned_landmark_error_m'],
 'measured_after_mean_error_m':float(error.mean()),'improvement_fraction':float(1-error.mean()/fit['before_mean_eye_aligned_landmark_error_m']),
 'scope':'Detector-estimated 2D landmarks aligned at the eyes. This is a fitting guide, not a biometric similarity score or an exact 3D match.',
 'reference':'Dr. Kalam’s Welcoming Wave.png','render':'renders/sculpt_v5_reference_pose_front.png'}
json.dump(report,open(ROOT/'tests/sculpt_v5_fit_verification.json','w'),indent=2);print(report)
