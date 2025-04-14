from manimlib import *
from manimgl_3d import *

material_red = PBRMaterial(albedo=color_to_rgb(RED), roughness=0.5)
material_yellow = PBRMaterial(albedo=color_to_rgb(YELLOW), roughness=0.1, metallic=0.2)
material_blue = PBRMaterial(albedo=color_to_rgb(BLUE), roughness=.5)
material_brick = load_material('./assets/brick-wall', height_scale = 1.2)
material_space_ship = load_material('./assets/spaceship-panels', height_scale = 0.5)
material_gold = load_material('./assets/pirate-gold', height_scale = 0.5)


class TestPBR(PBRScene):
    def construct(self):

        cube = CubePBR(material=material_red).shift(IN * 2)
        sphere = SpherePBR(material=material_yellow)
        surface = SurfacePBR(
            material = material_blue,
            uv_func = lambda u, v : np.array([u, v, (np.sin(u) + np.sin(v))/2]),
            u_range = (-20, 20),
            v_range = (-20, 20),
            resolution = (100, 100)
        ).shift(IN*3).scale(0.5)

        # arrow = Arrow(2 * LEFT, 2 * RIGHT, color = WHITE, depth_test = True)

        self.camera.light_source.set_light_color(np.array([500., 500., 500.]))
        self.add(surface, cube) #, arrow)

        self.play(GrowFromCenter(sphere), self.camera.frame.set_phi, 70*DEGREES, run_time = 1)
        self.play(self.camera.frame.set_theta, (90+45)*DEGREES, run_time = 3)
        self.play(self.camera.frame.shift, UP * 8 + RIGHT * 8, run_time = 1)


class TestPBR2(PBRScene):
    def construct(self):
        cube = CubePBR(material=material_red)
        sphere = SpherePBR(material=material_yellow).shift(IN * 2)
        surface = SurfacePBR(
            material = material_blue,
            uv_func = lambda u, v : np.array([u, v, 0]),
            u_range = (-20, 20),
            v_range = (-20, 20),
            resolution = (10, 10)
        ).shift(IN*3).scale(0.5)

        self.add(surface, cube)

        self.play(GrowFromCenter(sphere), self.camera.frame.set_phi, 70*DEGREES, run_time = 1)
        self.play(self.camera.frame.set_phi, (90+70)*DEGREES, run_time = 3)
        self.wait()


class TestPBRTexture(PBRScene):
    def construct(self):
        light = PointLight(light_color = np.array([2000.0, 2000.0, 2000.0]))

        brick_wall = SquarePBR(material = material_brick, resolution = (1024, 1024)).scale(5)
        text = Text("Manim3D", weight=BOLD).scale(5).shift(OUT * 1.0).rotate(180*DEGREES,axis=IN).apply_depth_test()
        theta = ValueTracker(0.)

        def light_updater(mob: Mobject):
            mob.move_to(np.array([
                10 * np.cos(theta.get_value()),
                10 * np.sin(theta.get_value()),
                5
            ]))
        light.add_updater(light_updater)
        self.add(brick_wall, theta, light)

        self.play(self.camera.frame.set_phi, 50*DEGREES, run_time = 1)
        self.play(self.camera.frame.set_theta, 180*DEGREES, run_time = 3)
        self.play(theta.increment_value, 360*DEGREES, run_time = 6, rate_func = linear)
        self.play(Write(text), self.camera.frame.animate.set_phi(0), run_time = 2)
        self.wait()

class TestPBRTexture2(PBRScene):
    def construct(self):
        light1 = PointLight(light_color = np.array([2000.0, 2000.0, 2000.0]))
        light2 = PointLight(light_color = np.array([2000.0, 2000.0, 2000.0]))

        brick_wall = SquarePBR(material = material_space_ship, resolution = (1024, 1024)).scale(5)
        text = Text("Manim3D", color = RED, weight=BOLD).scale(5).shift(OUT * 1.0).rotate(180*DEGREES,axis=IN).apply_depth_test()
        theta = ValueTracker(0.)

        def light1_updater(mob: Mobject):
            mob.move_to(np.array([
                10 * np.cos(theta.get_value()),
                10 * np.sin(theta.get_value()),
                5
            ]))
        def light2_updater(mob: Mobject):
            mob.move_to(np.array([
                10 * np.cos(theta.get_value() + 180 * DEGREES),
                10 * np.sin(theta.get_value() + 180 * DEGREES),
                5
            ]))
        
        light1.add_updater(light1_updater)
        light2.add_updater(light2_updater)
        self.add(brick_wall, theta, light1, light2)

        self.play(self.camera.frame.set_phi, 50*DEGREES, run_time = 1)
        self.play(self.camera.frame.set_theta, 180*DEGREES, run_time = 3)
        self.play(theta.increment_value, 360*DEGREES, run_time = 6, rate_func = linear)
        self.play(Write(text), self.camera.frame.animate.set_phi(0), run_time = 2)
        self.wait()

class TestPBRTexture3(PBRScene):
    def construct(self):
        light = PointLight(light_color = np.array([5000.0, 5000.0, 5000.0]))

        brick_wall = SquarePBR(material = material_gold, resolution = (1024, 1024)).scale(5)
        text = Text("Manim3D", color = BLUE_A, weight=BOLD).scale(5).shift(OUT * 1.0).apply_depth_test()
        theta = ValueTracker(0.)

        def light_updater(mob: Mobject):
            mob.move_to(np.array([
                5 * np.cos(theta.get_value()),
                5 * np.sin(theta.get_value()),
                8
            ]))
        light.add_updater(light_updater)
        self.add(brick_wall, theta, light)

        self.play(self.camera.frame.set_phi, 40*DEGREES, run_time = 2)
        self.play(self.camera.frame.set_theta, 180*DEGREES, run_time = 4, rate_func = rush_into)
        self.play(self.camera.frame.set_theta, 360*DEGREES, run_time = 4, rate_func = rush_from)
        self.play(theta.increment_value, 360*DEGREES, run_time = 6, rate_func = linear)
        self.play(Write(text), self.camera.frame.animate.set_phi(360*DEGREES), run_time = 2)
        self.wait()