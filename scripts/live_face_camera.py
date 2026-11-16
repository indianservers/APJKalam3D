"""Local webcam preview and facial coefficients streamed to Blender over localhost."""
import cv2, mediapipe as mp, socket, json, time, traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
status=ROOT/'mocap/live_camera_status.json'
sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
cap=None
try:
    cap=cv2.VideoCapture(0,cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release();cap=cv2.VideoCapture(0)
    if not cap.isOpened():raise RuntimeError('Camera 0 could not be opened')
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,640);cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
    options=mp.tasks.vision.FaceLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(ROOT/'mocap/models/face_landmarker.task')),running_mode=mp.tasks.vision.RunningMode.VIDEO,num_faces=1,output_face_blendshapes=True,min_face_detection_confidence=.5,min_face_presence_confidence=.5)
    start=time.monotonic();frames=0;last=0
    with mp.tasks.vision.FaceLandmarker.create_from_options(options) as detector:
        while True:
            ok,frame=cap.read()
            if not ok:raise RuntimeError('Camera frame could not be read')
            stamp=max(last+1,int((time.monotonic()-start)*1000));last=stamp
            result=detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)),stamp)
            scores={c.category_name:float(c.score) for c in result.face_blendshapes[0]} if result.face_blendshapes else {}
            sock.sendto(json.dumps({'scores':scores,'tracked':bool(scores)}).encode(),('127.0.0.1',9877))
            frames+=1;fps=frames/max(.001,time.monotonic()-start)
            view=cv2.flip(frame,1)
            cv2.putText(view,f'APJ live face | {fps:.1f} FPS | '+('TRACKING' if scores else 'Find face'),(12,26),cv2.FONT_HERSHEY_SIMPLEX,.55,(30,220,30),2)
            cv2.putText(view,'Smile, blink, open jaw | Q / Esc to stop',(12,view.shape[0]-15),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
            cv2.imshow('APJ Kalam - Live Camera',view)
            if frames%15==0:status.write_text(json.dumps({'running':True,'tracked':bool(scores),'fps':fps,'frames':frames,'time':time.time(),'jawOpen':scores.get('jawOpen',0)}))
            if cv2.waitKey(1)&255 in (27,ord('q')):break
            if cv2.getWindowProperty('APJ Kalam - Live Camera',cv2.WND_PROP_VISIBLE)<1:break
except Exception as exc:
    status.write_text(json.dumps({'running':False,'error':str(exc),'traceback':traceback.format_exc()}));raise
finally:
    sock.sendto(json.dumps({'scores':{},'tracked':False}).encode(),('127.0.0.1',9877))
    if cap:cap.release()
    cv2.destroyAllWindows();sock.close()
    if status.exists():
        data=json.loads(status.read_text());data['running']=False;status.write_text(json.dumps(data))
