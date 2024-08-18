from manimlib import *
from .pbr_scene import *
from .material import *
from manimgl_3d.shader_compatibility import *

class PointLight(Point):
    #NOTE: this is only a container, and should never be rendered as a mobject
    CONFIG = {
        "light_color": np.array([1000.0, 1000.0, 1000.0]),
    }
    def set_light_color(self, light_color: np.ndarray) -> None:
        self.light_color = light_color

    def get_light_color(self) -> np.ndarray:
        return self.light_color

default_material = PBRMaterial(
    albedo=color_to_rgb(BLUE),
    roughness=0.3,
    metallic=0.0
)

class SurfacePBR(PBRMobjectShaderCompatibilityMixin, Surface): # MobjectShaderCompatibilityMixin must appear before Mobject in the MRO chain in order to replace its init_shader_data method
    
    # 决定所有PBR物体的渲染属性
    # shader data 会随着vao和ShaderWrapper传到Camera中，进入顶点着色器
    
    CONFIG = {
        "shader_folder": "pbr",
        "shader_dtype": [
            ('point', np.float32, (3,)),
            # ('normal', np.float32, (3,)),
            # ('tangent', np.float32, (3,)),
            ('du_point', np.float32, (3,)),
            ('dv_point', np.float32, (3,)),
            ('tex_coords', np.float32, (2,)),
        ],
        "material": default_material,
        "tex_coords_scale": (1.0, 1.0), # u, v  # should remain constant
    }

    def init_data(self):
        self.data: dict[str, np.ndarray] = {
            "points": np.zeros((0, 3)),
            "bounding_box": np.zeros((3, 3)),
            "rgbas": np.zeros((1, 4)),
            "tex_coords": np.zeros((0, 2))
        }
    
    # Handle uniform data
    def init_uniforms(self):
        self.uniforms= {
            "is_fixed_in_frame": float(self.is_fixed_in_frame),
        }

    def get_normal_and_tangent(self):
        s_points, du_points, dv_points = self.get_surface_points_and_nudged_points()
        normal = np.cross((du_points - s_points) / self.epsilon, (dv_points - s_points) / self.epsilon)
        tangent = du_points
        return s_points, normal, tangent

    # Handle vertex data
    def get_tex_coords(self):
        nu, nv = self.resolution
        su, sv = self.tex_coords_scale
        return np.array([
                [u, v]
                for u in np.linspace(0, su, nu)
                for v in np.linspace(sv, 0, nv)  # Reverse y-direction
            ])

    def get_shader_data(self):
        s_points, du_points, dv_points = self.get_surface_points_and_nudged_points()
        shader_data = self.get_resized_shader_data_array(len(s_points))
        
        if "points" not in self.locked_data_keys:
            shader_data["point"] = s_points
            shader_data["du_point"] = du_points
            shader_data["dv_point"] = dv_points

            # TODO: Is it good to calculate normal and tangent in cpu?
            # shader_data["normal"] = 
            # shader_data["tangent"] = 

        if "tex_coords" not in self.locked_data_keys:
            shader_data["tex_coords"] = self.get_tex_coords()
        
        return shader_data


class SpherePBR(SurfacePBR):
    CONFIG = {
        "resolution": (101, 51),
        "radius": 1,
        "u_range": (0, TAU),
        "v_range": (0, PI),
    }

    def uv_func(self, u: float, v: float):
        return self.radius * np.array([
            np.cos(u) * np.sin(v),
            np.sin(u) * np.sin(v),
            -np.cos(v)
        ])


class SquarePBR(SurfacePBR):
    CONFIG = {
        "side_length": 2,
        "u_range": (-1, 1),
        "v_range": (-1, 1),
        "resolution": (2, 2)
    }

    def init_points(self) -> None:
        super().init_points()
        self.scale(self.side_length / 2)

    def uv_func(self, u: float, v: float) -> np.ndarray:
        return np.array([u, v, 0])


class CubePBR(SGroup): # not a SurfacePBR, but with SurfacePBR submobjects
    CONFIG = {
        "square_resolution": (2, 2),
        "side_length": 2,
        "square_class": SquarePBR,
        "material": default_material
    }

    def init_points(self) -> None:
        face = SquarePBR(
            material=self.material,
            resolution=self.square_resolution,
            side_length=self.side_length,
        )
        self.add(*self.square_to_cube_faces(face))

    @staticmethod
    def square_to_cube_faces(square: SquarePBR) -> list[SquarePBR]:
        radius = square.get_height() / 2
        square.move_to(radius * OUT)
        result = [square]
        result.extend([
            square.copy().rotate(PI / 2, axis=vect, about_point=ORIGIN)
            for vect in compass_directions(4)
        ])
        result.append(square.copy().rotate(PI, RIGHT, about_point=ORIGIN))
        return result

# TODO
class ArrowPBR(VMobjectShaderCompatibilityMixin, Arrow):
    '''Basically the vanilla manim Arrow but compatible with PBR surface objects. '''