from manimlib import *

class MobjectRT: # Superclass of all Raytracing Mobjects
    CONFIG = {}
    def __init__(self, **kwargs):
        pass

class SphereRT(MobjectRT):
    CONFIG = {}
    def __init__(self, center = ORIGIN, radius = 1.0, **kwargs):
        self.center = center
        self.radius = radius
        self.depth_mask = self._get_depth_mask(**kwargs) # maintain it
        super().__init__()
    
    # Time-consuming. Try not to call it repeadedly.
    def _get_depth_mask(self, **kwargs) -> Mobject:
        return Sphere(radius = self.radius, **kwargs).shift(self.center)
    
    def get_shader_data(self):
        pass