from manimlib import *
from manimlib.shader_wrapper import filename_to_code_map
from .utils.directories_utils import get_manimgl_3d_shader_dir

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
            directories=[get_manimgl_3d_shader_dir(), get_shader_dir(), "/"], # note the searching priority
            
            extensions=[],
        )
    except IOError:
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