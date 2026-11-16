"""Blender development retargeter. Input landmarks must be 3D metric points.
Image-normalized x/y and relative z are not interchangeable with world landmarks.
Calibration stores observed rest directions; single-vector tracking cannot solve twist.
No webcam is opened by this module.
"""
import math
from mathutils import Vector, Quaternion

BODY = {'LeftArm':(11,13),'LeftForeArm':(13,15),
        'RightArm':(12,14),'RightForeArm':(14,16),
        'LeftUpLeg':(23,25),'LeftLeg':(25,27),
        'RightUpLeg':(24,26),'RightLeg':(26,28)}
HAND = {'Thumb':(1,2,3,4),'Index':(5,6,7,8),
        'Middle':(9,10,11,12),'Ring':(13,14,15,16),'Pinky':(17,18,19,20)}
FACE = ['browInnerUp','browOuterUpLeft','browOuterUpRight',
        'browDownLeft','browDownRight','mouthSmileLeft','mouthSmileRight']

class Retargeter:
    def __init__(self, rig, mesh, response=14., confidence=.65, mirrored=False):
        self.rig=rig; self.mesh=mesh; self.response=response
        self.confidence=confidence; self.mirrored=mirrored
        self.rest={}; self.current={}; self.face={}

    def convert(self,p):
        # MediaPipe camera: x right, y down, z away; Blender: x right, z up.
        x,y,z=p
        return Vector((-x if self.mirrored else x,z,-y))

    def directions(self,body=None,hands=None):
        result={}
        def add(name,points,a,b):
            if len(points)<=max(a,b):return
            d=self.convert(points[b])-self.convert(points[a])
            if d.length>1e-6:result[name]=d.normalized()
        if body:
            for name,(a,b) in BODY.items():add(name,body,a,b)
        for side,points in (hands or {}).items():
            if side not in ('Left','Right'):continue
            for finger,indices in HAND.items():
                for j in range(3):add(f'{side}Hand{finger}{j+1}',points,indices[j],indices[j+1])
        return result

    def calibrate(self,body=None,hands=None):
        self.reset(); self.rest=self.directions(body,hands)
        return sorted(self.rest)

    def reset(self):
        for b in self.rig.pose.bones:b.matrix_basis.identity()
        for k in self.mesh.data.shape_keys.key_blocks:k.value=0
        self.current.clear();self.face.clear()

    def update(self,dt,body=None,hands=None,coefficients=None,confidence=1.):
        # Exponential smoothing remains stable as frame rate varies. Tracking loss
        # returns to neutral; confidence can also be supplied per bone.
        alpha=1-math.exp(-self.response*max(0,min(dt,.25)))
        observed=self.directions(body,hands)
        desired={}
        ordered=sorted(self.rig.pose.bones,key=lambda b:len(b.parent_recursive))
        for b in ordered:
            if b.name not in self.rest:continue
            conf=confidence.get(b.name,0) if isinstance(confidence,dict) else confidence
            q=Quaternion()
            if conf>=self.confidence and b.name in observed:
                q=self.rest[b.name].rotation_difference(observed[b.name])
                # Conservative swing limit; artist-authored twist is not inferred.
                axis,angle=q.to_axis_angle()
                q=Quaternion(axis,min(angle,math.radians(120)))
            desired[b.name]=q
            parent_delta=Quaternion()
            for ancestor in b.parent_recursive:
                if ancestor.name in desired:
                    parent_delta=desired[ancestor.name];break
            restq=b.bone.matrix_local.to_quaternion()
            local=restq.inverted() @ parent_delta.inverted() @ q @ restq
            prev=self.current.get(b.name,Quaternion())
            value=prev.slerp(local,alpha);self.current[b.name]=value
            b.rotation_mode='QUATERNION';b.rotation_quaternion=value
        for name in FACE:
            raw=(coefficients or {}).get(name,0.)
            if not math.isfinite(raw):raw=0.
            conf=confidence if isinstance(confidence,(int,float)) else 1.
            target=max(0.,min(1.,raw)) if conf>=self.confidence else 0.
            value=self.face.get(name,0.)+(target-self.face.get(name,0.))*alpha
            self.face[name]=value
            self.mesh.data.shape_keys.key_blocks[name].value=value
