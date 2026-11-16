"""HTTP boundary and actual exported-runtime checks for the local motion app."""
import unittest,json,struct,urllib.request,urllib.error
from pathlib import Path
BASE='http://127.0.0.1:8080';ROOT=Path(__file__).resolve().parents[1]
class MotionAppTests(unittest.TestCase):
 def request(self,path,data=None,origin=None,content='application/json'):
  headers={'Content-Type':content}
  if origin:headers['Origin']=origin
  req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
  try:
   with urllib.request.urlopen(req,timeout=10) as r:return r.status,r.read()
  except urllib.error.HTTPError as e:return e.code,e.read()
 def test_page(self):
  code,body=self.request('/');self.assertEqual(code,200);self.assertIn(b'Calibrate neutral face',body)
 def test_bridge_connected(self):
  code,body=self.request('/api/state');self.assertTrue(json.loads(body)['connected'])
 def test_invalid_landmark_count(self):self.assertEqual(self.request('/api/frame',{'pose':[{}]*34})[0],400)
 def test_unknown_command(self):self.assertEqual(self.request('/api/command',{'name':'execute_code'})[0],400)
 def test_cross_origin(self):self.assertEqual(self.request('/api/command',{'name':'reset'},origin='https://example.com')[0],403)
 def test_json_only(self):self.assertEqual(self.request('/api/command',{'name':'reset'},content='text/plain')[0],415)
 def test_server_not_served(self):self.assertEqual(self.request('/server.py')[0],404)
 def test_path_traversal(self):self.assertEqual(self.request('/assets/%2e%2e/server.py')[0],403)
 def test_exported_rig_and_face(self):
  with open(ROOT/'webapp/assets/apj_runtime_v15.glb','rb') as file:
   magic,version,total=struct.unpack('<III',file.read(12));self.assertEqual(version,2);length,kind=struct.unpack('<II',file.read(8));gltf=json.loads(file.read(length));blen,bkind=struct.unpack('<II',file.read(8));blob=file.read(blen)
  names={n.get('name') for n in gltf['nodes']};self.assertIn('EXPORT_APJ_v15_Silver_Hair_Strands',names);self.assertIn('Head',names);self.assertIn('LeftHandIndex3',names)
  self.assertEqual(len([n for n in names if n and n.startswith('Rib.')]),24)
  faces=[m for m in gltf['meshes'] if len(m.get('extras',{}).get('targetNames',[]))==51];self.assertEqual(len(faces),1)
  mesh=faces[0];self.assertIn('mouthSmileLeft',mesh['extras']['targetNames'])
  for channel in mesh['extras']['targetNames']:
   index=mesh['extras']['targetNames'].index(channel);accessor=gltf['accessors'][mesh['primitives'][0]['targets'][index]['POSITION']]
   valueinfo=accessor.get('sparse',{}).get('values',accessor);count=accessor.get('sparse',{}).get('count',accessor['count']);view=gltf['bufferViews'][valueinfo['bufferView']];offset=view.get('byteOffset',0)+valueinfo.get('byteOffset',0)
   values=struct.unpack_from('<'+'f'*(count*3),blob,offset);self.assertGreater(max(map(abs,values)),1e-8,channel)
  self.assertGreater(gltf['accessors'][mesh['primitives'][0]['attributes']['POSITION']]['count'],30000)
  self.assertFalse(any('JOINTS_1' in p.get('attributes',{}) for m in gltf['meshes'] for p in m['primitives']))
  skin_nodes=[n for n in gltf['nodes'] if n.get('name') in ['EXPORT_APJ_Face','EXPORT_APJ_Hand_Left','EXPORT_APJ_Hand_Right','EXPORT_char1']]
  self.assertEqual(len(skin_nodes),4)
  for n in skin_nodes:
   for primitive in gltf['meshes'][n['mesh']]['primitives']:
    material=gltf['materials'][primitive['material']]
    self.assertIn('normalTexture',material,n['name'])
    self.assertIn('metallicRoughnessTexture',material['pbrMetallicRoughness'],n['name'])
if __name__=='__main__':unittest.main(verbosity=2)
