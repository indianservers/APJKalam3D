"""Measure reference/render landmarks for an eye-aligned geometric likeness fit."""
import json,sys,os
from pathlib import Path
import numpy as np
from PIL import Image
import mediapipe as mp
ROOT=Path(r'C:\Abdul Kalam')
options=mp.tasks.vision.FaceLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(ROOT/'mocap/models/face_landmarker.task')),
    running_mode=mp.tasks.vision.RunningMode.IMAGE,num_faces=1,output_face_blendshapes=True,output_facial_transformation_matrixes=True,min_face_detection_confidence=.3,min_face_presence_confidence=.3)
inputs={'reference':ROOT/'Dr. Kalam’s Welcoming Wave.png','render':ROOT/'renders/sculpt_v5_reference_pose_front.png'}
result={}
with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
    for name,path in inputs.items():
        pil=Image.open(path).convert('RGB');crop=None
        image=mp.Image(image_format=mp.ImageFormat.SRGB,data=np.array(pil));data=landmarker.detect(image)
        if not data.face_landmarks and name=='reference':
            ww,hh=pil.size;crop=[int(ww*.25),0,int(ww*.68),int(hh*.26)];pil=pil.crop(crop)
            image=mp.Image(image_format=mp.ImageFormat.SRGB,data=np.array(pil));data=landmarker.detect(image)
        if not data.face_landmarks:raise RuntimeError('No face detected: '+name)
        result[name]={'landmarks':[[p.x,p.y,p.z] for p in data.face_landmarks[0]],'size':[image.width,image.height],
            'coefficients':{c.category_name:c.score for c in data.face_blendshapes[0]},
            'matrix':data.facial_transformation_matrixes[0].tolist(),'analysis_crop':crop}
with open(ROOT/'tests/sculpt_v5_landmarks.json','w') as f:json.dump(result,f,indent=2)
print('Detected reference and rendered face:',{k:len(v['landmarks']) for k,v in result.items()})
print('Reference expression',{k:round(v,3) for k,v in result['reference']['coefficients'].items() if v>.2})
