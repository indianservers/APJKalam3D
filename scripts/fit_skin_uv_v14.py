"""Fit texture coordinates to the new photograph; no image pixels are warped."""
from pathlib import Path
import numpy as np,json
from PIL import Image
import mediapipe as mp
ROOT=Path(__file__).resolve().parents[1]
options=mp.tasks.vision.FaceLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(ROOT/'mocap/models/face_landmarker.task')),running_mode=mp.tasks.vision.RunningMode.IMAGE,num_faces=1,min_face_detection_confidence=.3,min_face_presence_confidence=.3)
landmarks=[]
with mp.tasks.vision.FaceLandmarker.create_from_options(options) as detector:
 for filename in ['textures/appearance_v3/apj_face_projection_generated.png','textures/skin_v14/face_photographic_source.png']:
  pixels=np.array(Image.open(ROOT/filename).convert('RGB'));result=detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=pixels))
  if not result.face_landmarks:raise RuntimeError('Could not detect texture landmarks: '+filename)
  landmarks.append(np.array([[p.x,1-p.y] for p in result.face_landmarks[0][:468]]))
source,target=landmarks
# Regularized radial basis interpolation provides smooth anatomy-aligned UVs.
sigma=.10;kernel=np.exp(-np.sum((source[:,None]-source[None,:])**2,axis=2)/(2*sigma*sigma))
weights=np.linalg.solve(kernel+np.eye(len(source))*.002,target-source)
field={'centers':source.tolist(),'weights':weights.tolist(),'sigma':sigma,'source':'textures/appearance_v3/apj_face_projection_generated.png','target':'textures/skin_v14/face_photographic_source.png','source_landmarks':source.tolist(),'target_landmarks':target.tolist(),'mean_landmark_fit_error_uv':float(np.linalg.norm(source+kernel@weights-target,axis=1).mean())}
(ROOT/'tests/skin_uv_v14.json').write_text(json.dumps(field),encoding='utf-8')
print('UV landmark fit mean error:',field['mean_landmark_fit_error_uv'])
