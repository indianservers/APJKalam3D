import * as THREE from 'three';

import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

export class CharacterViewer{

 constructor(container){

  this.container=container;this.scene=new THREE.Scene();this.scene.background=null;

  this.camera=new THREE.PerspectiveCamera(32,1,.01,50);this.camera.position.set(2.2,1.7,-3.7);

  this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});this.renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=.90;container.append(this.renderer.domElement);

  this.controls=new OrbitControls(this.camera,this.renderer.domElement);this.controls.target.set(0,.85,0);this.controls.enableDamping=true;this.controls.minDistance=.16;this.controls.maxDistance=7;
  const pmrem=new THREE.PMREMGenerator(this.renderer);this.scene.environment=pmrem.fromScene(new RoomEnvironment(),.04).texture;this.scene.environmentIntensity=.25;pmrem.dispose();

  this.scene.add(new THREE.HemisphereLight(0xf5efdf,0x48503e,1.2));

  const key=new THREE.DirectionalLight(0xfff2e4,1.6);key.position.set(-2,3,3);this.scene.add(key);const fill=new THREE.DirectionalLight(0xf5f4ee,.8);fill.position.set(2,2,2);this.scene.add(fill);

  const rim=new THREE.DirectionalLight(0xffe8c4,.7);rim.position.set(0,2,-2);this.scene.add(rim);

  const floor=new THREE.Mesh(new THREE.CircleGeometry(1.3,80),new THREE.MeshStandardMaterial({color:0x283328,roughness:1}));floor.rotation.x=-Math.PI/2;floor.position.y=-.015;this.scene.add(floor);

  const grid=new THREE.GridHelper(2.5,20,0x4d5c45,0x354432);grid.position.y=-.012;grid.material.transparent=true;grid.material.opacity=.35;this.scene.add(grid);

  this.bones={};this.morphs=[];new ResizeObserver(()=>this.resize()).observe(container);this.resize();this.animate();

 }

 resize(){const w=this.container.clientWidth,h=this.container.clientHeight;this.camera.aspect=w/h;this.camera.updateProjectionMatrix();this.renderer.setSize(w,h);}

 async load(){

  const gltf=await new GLTFLoader().loadAsync('/assets/apj_runtime_v14.glb');this.model=gltf.scene;this.scene.add(this.model);

  this.model.traverse(o=>{

   if(o.isBone)this.bones[o.name]={object:o,quaternion:o.quaternion.clone(),position:o.position.clone(),targetQuaternion:o.quaternion.clone(),targetPosition:o.position.clone()};

   const sourceName=o.name.replace(/^EXPORT_/,'');

   if(o.morphTargetDictionary&&(sourceName.startsWith('APJ_Face')||sourceName.startsWith('APJ_v5_Skin_Transition')))this.morphs.push(o);

   if(o.isMesh){o.frustumCulled=false;const mats=Array.isArray(o.material)?o.material:[o.material];for(const m of mats){m.side=THREE.DoubleSide;if(sourceName.startsWith('APJ_Teeth')){m.color.setRGB(.62,.57,.46);m.roughness=.38;}}}

  });document.querySelector('#model-loading').style.display='none';document.querySelector('#model-status').textContent='Kalam skin / v14 / local';this.view(this.viewMode||'body');

 }

 apply(state){

  for(const [name,pose]of Object.entries(state.bones||{})){

   const b=this.bones[name]||this.bones[name.replaceAll('.','_')]||this.bones[name.replace(/[.\[\]:/]/g,'')];if(!b)continue;

   const delta=new THREE.Quaternion(...pose.q);b.targetQuaternion.copy(b.quaternion).multiply(delta);

   b.targetPosition.copy(b.position).add(new THREE.Vector3(...pose.p).applyQuaternion(b.quaternion));

  }

  for(const o of this.morphs)for(const [name,index]of Object.entries(o.morphTargetDictionary))o.morphTargetInfluences[index]=state.morphs?.[name]||0;

 }

 view(mode){

  this.viewMode=mode;

  const views={body:[[0, .88,0],[1.6,1.45,3.4]],face:[[0,1.51,.02],[.04,1.54,.62]],hands:[[.63,1.30,0],[.70,1.56,.30]]};

  const [target,position]=views[mode]||views.body;this.controls.target.set(...target);this.camera.position.set(...position);this.controls.update();

 }

 animate(){requestAnimationFrame(()=>this.animate());

  for(const b of Object.values(this.bones)){b.object.quaternion.slerp(b.targetQuaternion,.45);b.object.position.lerp(b.targetPosition,.45);}

  if(this.viewMode==='face'&&this.bones.Head){

   this.model.updateMatrixWorld(true);const target=this.bones.Head.object.localToWorld(new THREE.Vector3(0,.075,0));const delta=target.clone().sub(this.controls.target);this.camera.position.add(delta);this.controls.target.copy(target);

  }

  if(this.viewMode==='hands'&&this.bones.LeftHand){this.model.updateMatrixWorld(true);const target=this.bones.LeftHand.object.localToWorld(new THREE.Vector3(0,.08,0));const delta=target.clone().sub(this.controls.target);this.camera.position.add(delta);this.controls.target.copy(target);}
  this.controls.update();this.renderer.render(this.scene,this.camera);}

}

