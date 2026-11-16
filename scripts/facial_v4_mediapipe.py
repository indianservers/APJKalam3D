"""Applies supplied Face Landmarker coefficients. Does not open a camera."""
import bpy,json,math,os
class FaceCoefficientAdapter:
    def __init__(self,response=18.,confidence=.65):
        self.ctrl=bpy.data.objects['APJ_Face_Controls'];self.face=bpy.data.objects['APJ_Face']
        self.previous_action=self.ctrl.animation_data.action if self.ctrl.animation_data else None
        if self.ctrl.animation_data:self.ctrl.animation_data.action=None
        self.names=json.loads(self.face['expression_channels'])+[name for name in self.ctrl.keys() if name.startswith('eyeLook')]
        self.response=response;self.confidence=confidence;self.state={name:0. for name in self.names}
        self.reset()
    def reset(self):
        for name in self.names:self.state[name]=0.;self.ctrl[name]=0.
        self.ctrl['gazeHorizontal']=0.;self.ctrl['gazeVertical']=0.
        self.ctrl.update_tag();self.face.data.shape_keys.update_tag();bpy.context.view_layer.update()
    def stop(self,restore_action=True):
        self.reset()
        if restore_action and self.previous_action:
            self.ctrl.animation_data_create();self.ctrl.animation_data.action=self.previous_action
    def update(self,scores,dt=1/30,confidence=1.):
        # Convert a category list without executing input or accepting unknown properties.
        if not isinstance(scores,dict):scores={item.category_name:item.score for item in scores}
        alpha=1-math.exp(-self.response*max(0,min(dt,.25)))
        for name in self.names:
            value=scores.get(name,0.)
            try:value=float(value)
            except (TypeError,ValueError):value=0.
            if not math.isfinite(value) or confidence<self.confidence:value=0.
            value=max(0,min(1,value));self.state[name]+=alpha*(value-self.state[name]);self.ctrl[name]=float(self.state[name])
        self.ctrl.update_tag();self.face.data.shape_keys.update_tag();bpy.context.view_layer.update()
        return dict(self.state)
