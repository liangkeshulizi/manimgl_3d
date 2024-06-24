from manimlib import *

from .pbr_scene import *

# __all__ = ["SurfacePBR", "SpherePBR", "SquarePBR", "CubePBR",]


class SurfacePBR(Surface): 
    # 决定所有PBR物体的渲染属性
    # shader data 会随着vao和ShaderWrapper传到Camera中，进入顶点着色器
    
    CONFIG = {
        "shader_folder": "pbr",
        "color": BLUE,
        "albedo": np.array([0.04, 0.04, 0.04]),
        "metallic": 0.0,
        "roughness": 0.3,
        "ao": 0.3,
        "shader_dtype": [
            ('point', np.float32, (3,)),
            ('du_point', np.float32, (3,)),
            ('dv_point', np.float32, (3,)),
            ('color', np.float32, (4,)),
        ]
    }

    def init_uniforms(self):
        self.uniforms= {
            "is_fixed_in_frame": float(self.is_fixed_in_frame),
            "shadow": self.shadow,
            "albedo": self.albedo,
            "metallic": self.metallic,
            "roughness": self.roughness,
            "ao": self.ao,
        }
    
    def get_shader_data(self):
        s_points, du_points, dv_points = self.get_surface_points_and_nudged_points()
        shader_data = self.get_resized_shader_data_array(len(s_points))
        if "points" not in self.locked_data_keys:
            shader_data["point"] = s_points
            shader_data["du_point"] = du_points
            shader_data["dv_point"] = dv_points
        self.fill_in_shader_color_info(shader_data)
        return shader_data


class SpherePBR(SurfacePBR):
    CONFIG = {
        "resolution": (65, 65),
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
        "resolution": (2, 2),
    }

    def init_points(self) -> None:
        super().init_points()
        self.scale(self.side_length / 2)

    def uv_func(self, u: float, v: float) -> np.ndarray:
        return np.array([u, v, 0])


class CubePBR(SGroup): # not a SurfacePBR, but with SurfacePBR submobjects
    CONFIG = {
        "color": RED,
        "opacity": 1,
        "gloss": 0.5,
        "square_resolution": (2, 2),
        "side_length": 2,
        "square_class": SquarePBR,
    }

    def init_points(self) -> None:
        face = SquarePBR(
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

    def _get_face(self) -> SquarePBR:
        return SquarePBR(resolution=self.square_resolution)
    