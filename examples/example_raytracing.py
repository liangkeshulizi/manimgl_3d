from manimlib import *
from raytracing import *

class TestRT(RTScene):
    def construct(self):
        # surface = Sphere(radius = 10).shift(IN * 11)
        sphere1 = SphereRT(ORIGIN, 1)
        sphere2 = SphereRT(RIGHT * 2, 1)
        cube = Cube(color = RED, roughness = .4).shift(OUT * 2)
        self.add(sphere1, sphere2, cube)

        self.play(self.camera.frame.set_phi, 75 * DEGREES, run_time = 2)
        self.play(self.camera.frame.set_theta, 180 * DEGREES, run_time = 3, rate_func = there_and_back)