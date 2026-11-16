"""Local-only static app and validated landmark relay. No camera images stored."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import socket,json,time,math,threading
from urllib.parse import unquote,urlsplit
from connect_blender import connect
ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parent
UDP=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
COMMANDS={'reset','calibrate','calibrate_face','smile','seated','standing','settings','record_start','record_stop','save'}
def validate_points(value,max_count):
 if not isinstance(value,list) or len(value)>max_count:raise ValueError('Invalid landmark count')
 out=[]
 for p in value:
  if not isinstance(p,dict):raise ValueError('Invalid point')
  point={}
  for k in ['x','y','z','visibility']:
   v=p.get(k,1 if k=='visibility' else 0)
   if not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>20:raise ValueError('Invalid coordinate')
   point[k]=round(v,5)
  out.append(point)
 return out
def validate_frame(data):
 face=data.get('face',{})
 if not isinstance(face,dict) or len(face)>64:raise ValueError('Invalid face coefficients')
 clean={k:max(0,min(1,float(v))) for k,v in face.items() if isinstance(k,str) and len(k)<64 and isinstance(v,(int,float)) and math.isfinite(v)}
 hands=[]
 for h in data.get('hands',[])[:2]:
  if h.get('side') not in ['Left','Right']:continue
  conf=h.get('confidence',0)
  if not isinstance(conf,(int,float)) or not math.isfinite(conf):continue
  hands.append({'side':h['side'],'confidence':max(0,min(1,conf)),'world':validate_points(h.get('world',[]),21)})
 return {'type':'frame','pose':validate_points(data.get('pose',[]),33),'poseImage':validate_points(data.get('poseImage',[]),33),'facePoints':validate_points(data.get('facePoints',[]),478),'hands':hands,'face':clean}
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def log_message(self,*args):pass
 def end_headers(self):
  self.send_header('Cache-Control','no-cache');self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
 def respond(self,status,data):
  raw=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  if '..' in Path(unquote(urlsplit(self.path).path)).parts:return self.send_error(403)
  if self.path=='/api/state':
   try:
    data=json.loads((PROJECT/'mocap/capture_state.json').read_text());data['connected']=time.time()-data['time']<2
   except (OSError,ValueError):data={'connected':False,'mode':'offline','error':'Start Blender bridge'}
   return self.respond(200,data)
  if self.path.startswith('/node_modules/') or self.path.startswith('/models/') or self.path.startswith('/assets/') or self.path.split('?')[0] in ['/','/index.html','/style.css','/app.js','/tracking-worker.js','/viewer.js']:
   return super().do_GET()
  self.send_error(404)
 def do_POST(self):
  # Only the served local app may submit to the loopback relay.
  origin=self.headers.get('Origin')
  if origin and origin not in ['http://127.0.0.1:8080','http://localhost:8080']:return self.respond(403,{'error':'Local app origin required'})
  if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.respond(415,{'error':'JSON required'})
  try:
   length=int(self.headers.get('Content-Length','0'))
   if length<1 or length>120000:raise ValueError('Invalid payload size')
   data=json.loads(self.rfile.read(length))
   if self.path=='/api/connect':return self.respond(200,{'ok':True,'result':connect()})
   if self.path=='/api/frame':packet=validate_frame(data)
   elif self.path=='/api/command' and data.get('name') in COMMANDS:packet={'type':'command','name':data['name'],'data':data.get('data',{})}
   else:return self.respond(400,{'error':'Unsupported command'})
   raw=json.dumps(packet,separators=(',',':')).encode()
   if len(raw)>65000:raise ValueError('Frame is too large')
   UDP.sendto(raw,('127.0.0.1',9877));self.respond(200,{'ok':True})
  except (ValueError,TypeError,AttributeError,OverflowError) as exc:self.respond(400,{'error':str(exc)})
  except (OSError,RuntimeError) as exc:self.respond(503,{'error':str(exc)})
if __name__=='__main__':
 print('APJ Motion Studio http://127.0.0.1:8080',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8080),Handler).serve_forever()
