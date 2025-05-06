import trimesh
from manimlib import *
from .pbr_scene import *
from .material import *
from manimgl_3d.shader_compatibility import *
from manimgl_3d.utils.model_utils import *

class PointLight(Point):
    # NOTE: this is only a container, and should never be rendered as a mobject
    CONFIG = {
        "light_color": np.array([1000.0, 1000.0, 1000.0]),
    }
    def set_light_color(self, light_color: np.ndarray) -> None:
        assert light_color.shape == (3,)
        self.light_color[:] = light_color[:]

    def get_light_color(self) -> np.ndarray:
        return self.light_color
    
    # make sure this is not rendered
    def get_shader_wrapper_list(self):
        return []

default_material = PBRMaterial(
    albedo=color_to_rgb(BLUE),
    roughness=0.3,
    metallic=0.0
)

class SurfacePBR(PBRMobjectShaderCompatibilityMixin, Surface): # MobjectShaderCompatibilityMixin must appear before Mobject in the MRO chain in order to replace its init_shader_data method
    
    # Render Configurations affecting all PBR mobjects
    # shader_data will be passed into Camera via vao & ShaderWrapper, ending up in the vertex shader.
    
    CONFIG = {
        "shader_folder": "pbr",
        "shader_dtype": [
            ('point', np.float32, (3,)),
            ('normal', np.float32, (3,)),
            ('tangent', np.float32, (3,)),
            ('tex_coords', np.float32, (2,)),
        ],
        "material": default_material,
        "tex_coords_scale": (1.0, 1.0), # u, v  # should remain constant
    }

    def init_data(self):
        self.data: dict[str, np.ndarray] = {
            "points": np.zeros((0, 3)),
            "bounding_box": np.zeros((3, 3)),
            "tex_coords": np.zeros((0, 2))
        }

    def init_colors(self):
        pass
    
    def init_uniforms(self):
        self.uniforms= {
            "is_fixed_in_frame": float(self.is_fixed_in_frame),
        }

    def init_points(self):
        super().init_points()
        
        # init tex_coords
        nu, nv = self.resolution
        su, sv = self.tex_coords_scale
        tex_coords = np.array([
                [u, v]
                for u in np.linspace(0, su, nu)
                for v in np.linspace(sv, 0, nv)  # Reverse y-direction
            ])
        self.data["tex_coords"] = tex_coords

    def calculate_normal_and_tangent(self, s_points, du_points, dv_points):
        normal = np.cross((du_points - s_points), (dv_points - s_points))
        tangent = (du_points - s_points)
        return normal, tangent

    def get_tex_coords(self):
        return self.data["tex_coords"]

    def get_shader_data(self):
        s_points, du_points, dv_points = self.get_surface_points_and_nudged_points()
        shader_data = self.get_resized_shader_data_array(len(s_points))
        
        if "points" not in self.locked_data_keys:
            shader_data["point"] = s_points
            shader_data["normal"], shader_data["tangent"] = self.calculate_normal_and_tangent(s_points, du_points, dv_points)

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

    def init_colors(self):
        pass

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

class ModelPBR(PBRMobjectShaderCompatibilityMixin, Mobject):
    CONFIG = {
        "shader_folder": "pbr",
        "render_primitive": moderngl.TRIANGLES,
        "depth_test": True,
        "shader_dtype": [
            ('point', np.float32, (3,)),
            ('normal', np.float32, (3,)),
            ('tangent', np.float32, (3,)),
            ('tex_coords', np.float32, (2,)),
        ],
        "material": default_material,
    }

    def __init__(self, model_path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        model = trimesh.load_mesh(model_path, process=True)
        if isinstance(model, trimesh.Scene):
            model = trimesh.util.concatenate(model.dump())
        
        self.init_model(model)

    # Initializers, only run once

    def init_data(self):
        self.data: dict[str, np.ndarray] = {
            "points": np.zeros((0, 3)),
            "normal": np.zeros((0, 3)),
            "tangent": np.zeros((0, 3)),
            "bounding_box": np.zeros((3, 3)),
            "tex_coords": np.zeros((0, 2))
        }
    
    def init_colors(self):
        pass

    def init_model(self, model: trimesh.Trimesh):
        
        # Parsing the model and compute necessary data
        
        vertices = model.vertices
        face_indices = model.faces
        normals = model.vertex_normals

        if hasattr(model.visual, 'uv') and model.visual.uv is not None:
            tex_coords = model.visual.uv
        else:
            tex_coords = np.zeros((len(model.vertices), 2))

        tangents = compute_tangents(vertices, tex_coords, normals, face_indices)
        
        # Initalize mobject data
        
        self.set_points(vertices)
        self.data["normal"] = np.copy(normals)              # copy makes sure the array is editable
        self.data["tangent"] = np.copy(tangents)
        self.data["tex_coords"] = np.copy(tex_coords)
        self.shader_indices = face_indices

    # Methods directly affecting points
    
    def apply_points_function(
        self,
        func: Callable[[np.ndarray], np.ndarray],
        about_point: np.ndarray = None,
        about_edge: np.ndarray = ORIGIN,
        works_on_bounding_box: bool = False
    ):
        super().apply_points_function(func, about_point, about_edge, works_on_bounding_box)
        extra_arrs = [self.get_normal(), self.get_tangent()]        # the function also applies to normals and tangents
        for arr in extra_arrs:
            if about_point is None:
                arr[:] = func(arr)
            else:
                arr[:] = func(arr - about_point) + about_point
    
    # Getters, called during run-time

    def get_normal(self):
        return self.data["normal"]
    
    def get_tangent(self):
        return self.data["tangent"]
    
    def get_tex_coords(self):
        return self.data["tex_coords"]

    def get_shader_data(self):
        points = self.get_points()
        shader_data = self.get_resized_shader_data_array(len(points))

        if "points" not in self.locked_data_keys:
            shader_data["point"] = points
            shader_data["normal"] = self.get_normal()
            shader_data["tangent"] = self.get_tangent()

        if "tex_coords" not in self.locked_data_keys:
            shader_data["tex_coords"] = np.array([1., 1.]) - self.get_tex_coords()
        
        return shader_data
