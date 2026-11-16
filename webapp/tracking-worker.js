importScripts('/node_modules/@mediapipe/tasks-vision/vision_bundle.js');
const {FilesetResolver,PoseLandmarker,HandLandmarker,FaceLandmarker}=Vision;
let pose,hand,face,settings={body:true,hands:true,face:true},ready=false;
async function init(){
 const files=await FilesetResolver.forVisionTasks('/node_modules/@mediapipe/tasks-vision/wasm');
 const base={runningMode:'VIDEO'};
 async function create(Task,options){try{return await Task.createFromOptions(files,options);}catch(error){options.baseOptions.delegate='CPU';return await Task.createFromOptions(files,options);}}
 pose=await create(PoseLandmarker,{...base,baseOptions:{modelAssetPath:'/models/pose_landmarker_lite.task',delegate:'GPU'},numPoses:1,minPoseDetectionConfidence:.5,minPosePresenceConfidence:.5,minTrackingConfidence:.5});
 hand=await create(HandLandmarker,{...base,baseOptions:{modelAssetPath:'/models/hand_landmarker.task',delegate:'GPU'},numHands:2,minHandDetectionConfidence:.5,minHandPresenceConfidence:.5,minTrackingConfidence:.5});
 face=await create(FaceLandmarker,{...base,baseOptions:{modelAssetPath:'/models/face_landmarker.task',delegate:'GPU'},numFaces:1,outputFaceBlendshapes:true,minFaceDetectionConfidence:.5,minFacePresenceConfidence:.5});
 ready=true;postMessage({type:'ready'});
}
self.onmessage=async({data})=>{
 try{
  if(data.type==='init'){await init();return;}
  if(data.type==='settings'){settings=data.settings;return;}
  if(data.type!=='frame'||!ready){data.image?.close();return;}
  const image=data.image,t=data.timestamp,begin=performance.now();
  const p=settings.body?pose.detectForVideo(image,t):{};
  const h=settings.hands?hand.detectForVideo(image,t):{};
  const f=settings.face?face.detectForVideo(image,t):{};
  const scores=Object.fromEntries((f.faceBlendshapes?.[0]?.categories||[]).map(c=>[c.categoryName,c.score]));
  const hands=(h.worldLandmarks||[]).map((world,i)=>{
   const image=h.landmarks[i],body=p.landmarks?.[0];let side=h.handedness[i][0].categoryName;
   if(body){const d=j=>body[j].visibility>.5?Math.hypot(body[j].x-image[0].x,body[j].y-image[0].y):Infinity;if(Math.min(d(15),d(16))<.20)side=d(15)<d(16)?'Left':'Right';}
   return {world,side,confidence:h.handedness[i][0].score,image};
  });
  const aspect=image.width/image.height;
  const result={pose:p.worldLandmarks?.[0]||[],poseImage:p.landmarks?.[0]||[],hands,face:scores,facePoints:(f.faceLandmarks?.[0]||[]).map(v=>({...v,x:v.x*aspect,z:v.z*aspect})),overlayFace:f.faceLandmarks?.[0]||[]};
  image.close();postMessage({type:'result',result,ms:performance.now()-begin});
 }catch(error){data.image?.close();postMessage({type:'error',error:error.message||String(error)});}
};
