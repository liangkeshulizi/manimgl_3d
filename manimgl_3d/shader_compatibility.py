from manimlib import *
from .utils.directories_utils import get_manimgl_3d_shader_dir

__all__ = [
    "get_shader_code_from_file_extended",
    "MyShaderWrapper",
    "MobjectShaderCompatibilityMixin",
    "VMobjectShaderCompatibilityMixin",
]

filename_to_code_map = {} # caching seperately, avoiding fetching wrong files

# exactly copied expect one line
def get_shader_code_from_file_extended(filename: str) -> str | None:
    if not filename:
        return None
    if filename in filename_to_code_map:
        return filename_to_code_map[filename]

    try:
        filepath = find_file(
            filename,

            ########## Incorporates manimgl_3d/shader folder to the searching list ##########
            directories=[
                get_manimgl_3d_shader_dir(),
                get_shader_dir(),
                "/"
            ],
            
            extensions=[],
        )
    except IOError:
        if 'vert' in filename or 'frag' in filename:
            print(f'shader {filename} not found.')  # as a warning
        return None

    with open(filepath, "r") as f:
        result = f.read()

    insertions = re.findall(r"^#INSERT .*\.glsl$", result, flags=re.MULTILINE)
    for line in insertions:
        inserted_code = get_shader_code_from_file_extended(
            os.path.join("inserts", line.replace("#INSERT ", ""))
        )
        result = result.replace(line, inserted_code)
    filename_to_code_map[filename] = result
    return result


# This will search the manimgl_3d/shader folder while fetching shader code file
class MyShaderWrapper(ShaderWrapper):
    def init_program_code(self) -> None:
        def get_code(name: str) -> str | None:
            return get_shader_code_from_file_extended(
                os.path.join(self.shader_folder, f"{name}.glsl")
            )

        self.program_code: dict[str, str | None] = {
            "vertex_shader": get_code("vert"),
            "geometry_shader": get_code("geom"),
            "fragment_shader": get_code("frag"),
        }


class MobjectShaderCompatibilityMixin:
    def init_shader_data(self):
        self.shader_data = np.zeros(len(self.get_points()), dtype=self.shader_dtype)
        self.shader_indices = None
        self.shader_wrapper = MyShaderWrapper( # involving the manimgl_3d/sahder folder
            vert_data=self.shader_data,
            shader_folder=self.shader_folder,
            texture_paths=self.texture_paths,
            depth_test=self.depth_test,
            render_primitive=self.render_primitive,
        )

class VMobjectShaderCompatibilityMixin:
    def init_shader_data(self):
        self.fill_data = np.zeros(0, dtype=self.fill_dtype)
        self.stroke_data = np.zeros(0, dtype=self.stroke_dtype)
        self.fill_shader_wrapper = MyShaderWrapper(   # involving the manimgl_3d/sahder folder
            vert_data=self.fill_data,
            vert_indices=np.zeros(0, dtype='i4'),
            shader_folder=self.fill_shader_folder,
            render_primitive=self.render_primitive,
        )
        self.stroke_shader_wrapper = MyShaderWrapper( # involving the manimgl_3d/sahder folder
            vert_data=self.stroke_data,
            shader_folder=self.stroke_shader_folder,
            render_primitive=self.render_primitive,
        )