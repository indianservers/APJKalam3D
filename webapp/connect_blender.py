"""Bootstrap this project's fixed capture bridge through Blender MCP port 9876."""
import socket,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def connect():
 code="import bpy\nif 'APJ_Face' not in bpy.data.objects or not bpy.data.objects['APJ_Face'].get('reference_v15'):\n bpy.ops.wm.open_mainfile(filepath="+repr(str(ROOT/'blender/apj_reference_v15_master.blend'))+")\nexec(compile(open("+repr(str(ROOT/'scripts/fullbody_bridge.py'))+").read(),'fullbody_bridge.py','exec'))\n"
 with socket.create_connection(('127.0.0.1',9876),timeout=30) as client:
  client.sendall(json.dumps({'type':'execute_code','params':{'code':code}}).encode());buf=b''
  while len(buf)<2000000:
   chunk=client.recv(65536)
   if not chunk:break
   buf+=chunk
   try:
    result=json.loads(buf)
    if result.get('status')=='error':raise RuntimeError(str(result.get('message',result)))
    return result
   except json.JSONDecodeError:continue
 raise RuntimeError('No complete response from Blender MCP')
if __name__=='__main__':print(json.dumps(connect()))
