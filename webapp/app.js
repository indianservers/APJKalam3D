import {CharacterViewer} from './viewer.js';
const $=id=>document.getElementById(id);const viewer=new CharacterViewer($('stage'));viewer.load().catch(e=>{$('model-loading').textContent='Character preview unavailable: '+e.message;});
let stream=null,worker=null,busy=false,running=false,ready=false,lastFrame=0,lastVideo=-1,lastResult=null,recording=false,modelPromise=null;
const settings=()=>({body:$('track-body').checked,hands:$('track-hands').checked,face:$('track-face').checked,root:$('root-motion').checked,response:+$('smooth').value});
function notice(text,error=false){$('notice').textContent=text;$('notice').classList.toggle('error',error);}
async function command(name,data={}){const r=await fetch('/api/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,data})});const j=await r.json();if(!r.ok)throw Error(j.error);return j;}
async function cameras(){
 try{const selected=$('camera').value;const devices=(await navigator.mediaDevices.enumerateDevices()).filter(d=>d.kind==='videoinput');$('camera').replaceChildren(new Option('Default camera',''),...devices.map((d,i)=>new Option(d.label||`Camera ${i+1}`,d.deviceId)));$('camera').value=selected;return devices;}catch(e){notice('Camera device list unavailable. '+e.message,true);return [];}
}
function loadModels(){
 if(ready)return Promise.resolve();
 if(modelPromise)return modelPromise;
 if(worker)worker.terminate();worker=new Worker('/tracking-worker.js');
 modelPromise=new Promise((resolve,reject)=>{worker.onmessage=async({data})=>{
  if(data.type==='ready'){ready=true;worker.postMessage({type:'settings',settings:settings()});resolve();}
  if(data.type==='error'){busy=false;notice('Tracking error: '+data.error,true);reject(Error(data.error));}
  if(data.type==='result'){
   busy=false;lastResult=data.result;draw(data.result);$('fps').textContent=(1000/Math.max(1,data.ms)).toFixed(0)+' inference FPS';
   const f=data.result.face,pct=v=>Math.round((v||0)*100)+'%';$('expression-levels').textContent='Smile '+pct(Math.max(f.mouthSmileLeft||0,f.mouthSmileRight||0))+' · Jaw '+pct(f.jawOpen)+' · Blink '+pct(Math.max(f.eyeBlinkLeft||0,f.eyeBlinkRight||0));
   const h=data.result.hands;const gestures=h.map(hand=>hand.side+': '+gesture(hand));$('gesture').textContent='Hand gesture: '+(gestures.join(' · ')||'—');
   const packet={...data.result,hands:h.map(({image,...rest})=>rest)};delete packet.overlayFace;
   try{const r=await fetch('/api/frame',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(packet)});if(!r.ok)notice('Motion relay rejected a frame: '+(await r.json()).error,true);}catch(e){notice('Local relay unavailable. '+e.message,true);}
  }
 };worker.onerror=e=>{busy=false;modelPromise=null;reject(Error(e.message));};worker.postMessage({type:'init'});});return modelPromise;
}
function gesture(hand){
 const p=hand.world,d=(a,b)=>Math.hypot(p[a].x-p[b].x,p[a].y-p[b].y,p[a].z-p[b].z);if(d(4,8)<.025)return 'Pinch';
 let extended=0;for(const [tip,pip]of [[8,6],[12,10],[16,14],[20,18]])if(d(tip,0)>d(pip,0)*1.15)extended++;
 return extended===0?'Fist':extended===4?'Open palm':extended===2?'Two fingers':'Articulating';
}
async function start(){
 $('start').disabled=true;notice('Loading local tracking models…');
 try{
  const deviceId=$('camera').value;stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480},frameRate:{ideal:24,max:30},...(deviceId?{deviceId:{exact:deviceId}}:{})},audio:false});
  $('video').srcObject=stream;await $('video').play();await cameras();$('camera-empty').style.display='none';$('camera-label').textContent='CAMERA LIVE';
  await loadModels();running=true;$('stop').disabled=false;$('start').textContent='Camera running';notice('Stand fully in frame, then calibrate. Keep the camera still during capture.');requestAnimationFrame(loop);
 }catch(e){stop();notice(e.name==='NotFoundError'?'No camera found. Connect or switch on your camera, then refresh the device list.':e.name==='NotAllowedError'?'Camera permission is needed. Allow camera access for this local page, then try again.':e.message,true);}
}
function stop(){running=false;stream?.getTracks().forEach(t=>t.stop());stream=null;$('video').srcObject=null;$('camera-empty').style.display='flex';$('camera-label').textContent='CAMERA OFF';$('start').disabled=false;$('start').innerHTML='Start camera <span>↗</span>';$('stop').disabled=true;$('fps').textContent='— FPS';$('overlay').getContext('2d').clearRect(0,0,$('overlay').width,$('overlay').height);command('reset').catch(()=>{});}
async function loop(now){
 if(!running)return;
 if(!busy&&now-lastFrame>33&&$('video').currentTime!==lastVideo){busy=true;lastFrame=now;lastVideo=$('video').currentTime;try{const image=await createImageBitmap($('video'));worker.postMessage({type:'frame',image,timestamp:now},[image]);}catch(e){busy=false;}}
 requestAnimationFrame(loop);
}
const bodyEdges=[[11,12],[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24],[23,25],[25,27],[24,26],[26,28],[27,31],[28,32]];
const handEdges=[[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]];
function draw(data){const c=$('overlay');c.width=$('video').videoWidth;c.height=$('video').videoHeight;const ctx=c.getContext('2d');ctx.clearRect(0,0,c.width,c.height);ctx.lineWidth=2;function lines(p,edges,color){ctx.strokeStyle=color;for(const[a,b]of edges){if(!p[a]||!p[b])continue;ctx.beginPath();ctx.moveTo(p[a].x*c.width,p[a].y*c.height);ctx.lineTo(p[b].x*c.width,p[b].y*c.height);ctx.stroke();}ctx.fillStyle=color;for(const v of p){ctx.beginPath();ctx.arc(v.x*c.width,v.y*c.height,2,0,Math.PI*2);ctx.fill();}}
 lines(data.poseImage,bodyEdges,'#d5e8ac');for(const h of data.hands)lines(h.image,handEdges,'#edc37e');const p=data.overlayFace;ctx.fillStyle='#f3e6c5';for(const i of [33,133,263,362,61,291,13,14,1])if(p[i]){ctx.beginPath();ctx.arc(p[i].x*c.width,p[i].y*c.height,2,0,Math.PI*2);ctx.fill();}}
async function poll(){
 try{const s=await(await fetch('/api/state')).json();$('bridge').textContent=s.connected?'Blender connected':'Blender bridge offline';$('bridge').classList.toggle('connected',s.connected);if(s.connected){viewer.apply(s);$('bone-count').textContent=s.rigBones||87;$('mode-label').textContent=({idle:'Ready for movement',live:'Following your performance',seated:'Seated deformation check',standing:'Standing deformation check',recorded:'Motion recorded'})[s.mode]||s.mode;
 const labels=[['body-status',s.tracking?.body],['hand-status',s.tracking?.hands>0],['face-status',s.tracking?.face]];for(const[id,on]of labels){$(id).textContent=s.mode==='live'?(on?'Tracking':'Not visible'):'Waiting';$(id).classList.toggle('tracked',s.mode==='live'&&on);}
 recording=!!s.recording;$('record').classList.toggle('recording',recording);$('record').innerHTML='<span class="record-dot"></span>'+(recording?'Stop recording · '+s.recordedFrames+'f':'Record motion');if(s.error)notice(s.error,true);
 }}catch(e){$('bridge').textContent='Local server offline';}setTimeout(poll,50);
}
$('start').onclick=start;$('stop').onclick=stop;$('refresh-camera').onclick=cameras;
$('reconnect').onclick=async()=>{notice('Connecting to Blender on this computer…');try{const r=await fetch('/api/connect',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});const j=await r.json();if(!r.ok)throw Error(j.error);notice('Blender connected. Start the camera when ready.');}catch(e){notice('Open Blender and start MCP on port 9876. '+e.message,true);}};
$('smile-test').onclick=async()=>{await command('smile');notice('Showing a five-second smile on the character. Live expression tracking then resumes.');};
$('face-calibrate').onclick=async()=>{if(!running||!lastResult?.facePoints.length)return notice('Start the camera and face it with a relaxed expression first.',true);await command('calibrate_face');notice('Neutral face and head angle calibrated. Now smile, blink, and open your mouth.');};
$('reference-test').onclick=async()=>{if(running)stop();notice('Loading local models for reference-image tracking…');$('reference-test').disabled=true;try{await loadModels();const image=await createImageBitmap(await(await fetch('/assets/reference.png')).blob());worker.postMessage({type:'frame',image,timestamp:performance.now()},[image]);notice('Tracking test uses the supplied still reference, not a live camera. The pose will return to neutral after the test.');}catch(e){notice(e.message,true);}finally{$('reference-test').disabled=false;}};
$('calibrate').onclick=async()=>{if(!running||!lastResult?.pose.length)return notice('Start the camera and stand fully in frame before calibration.',true);await command('calibrate');await new Promise(resolve=>setTimeout(resolve,250));const s=await(await fetch('/api/state')).json();notice(s.calibration_ok?'Standing baseline captured. You can now move or sit; keep the camera still.':'Standing calibration needs shoulders, hips, knees, and ankles clearly in frame. Step back and try again.',!s.calibration_ok);};
$('record').onclick=async()=>{if(!recording&&!running)return notice('Start the camera before recording motion.',true);await command(recording?'record_stop':'record_start');};
$('save').onclick=async()=>{await command('save');notice('Saving to blender/apj_reference_v15_session.blend on this computer.');};
for(const b of document.querySelectorAll('[data-command]'))b.onclick=async()=>{if(running)stop();await command(b.dataset.command);notice(b.dataset.command==='seated'?'Seated test pose. Inspect hips, knees and garment folds from the side.':'Pose loaded. Drag to inspect the character.');};
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>{document.querySelectorAll('[data-view]').forEach(e=>e.classList.toggle('active',e===b));viewer.view(b.dataset.view);};
for(const id of ['track-body','track-hands','track-face','root-motion','smooth'])$(id).oninput=()=>{const value=settings();$('smooth-value').value=value.response;worker?.postMessage({type:'settings',settings:value});command('settings',value);};
$('mirror').onchange=()=>$('video').parentElement.classList.toggle('mirrored',$('mirror').checked);$('video').parentElement.classList.add('mirrored');window.addEventListener('beforeunload',()=>stream?.getTracks().forEach(t=>t.stop()));cameras();poll();
