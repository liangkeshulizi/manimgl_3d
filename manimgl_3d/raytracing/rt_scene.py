from manimlib import *
# from manimlib.shader_wrapper import get_shader_code_from_file
from typing import List, Union
import OpenGL.GL as gl 

from .mobject_rt import *
from manimgl_3d.shader_compatibility import get_shader_code_from_file_extended
from manimgl_3d.camera_frame import MyCameraFrame

class RTCamera(Camera):
    CONFIG = {
        "rtshader_folder" : "ray_tracing" # the folder containing vert/frag shaders for ray tracing
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._init_rtshader_program()
        self._init_quad()
    
    def init_frame(self) -> None:
        self.frame = MyCameraFrame(**self.frame_config)

    def _init_rtshader_program(self):
        def get_code(name):
            return get_shader_code_from_file_extended(os.path.join(self.rtshader_folder, f"{name}.glsl"))
        self.rtprogram =  self.ctx.program(
                vertex_shader = get_code("vert"),
                geometry_shader = get_code("geom"),
                fragment_shader = get_code("frag"),
        ) # compile and link the shader program
    
    def _init_quad(self):
        """
        With contrast to the rasterization approach, raytracing is done directly on a quad on the screen.
        This method creates the vao/vbo needed for raytracing.
        """
        coords = np.array([
            1.0, 1.0,
            1.0, -1.0,
            -1.0, 1.0,
            -1.0, 1.0,
            1.0, -1.0,
            -1.0, -1.0,
        ], dtype = 'f4')
        vbo = self.ctx.buffer(coords.tobytes())

        self.quad_vao = self.ctx.vertex_array(
            self.rtprogram ,
            [(vbo, "2f", "coords")] # attributes of vertex shader
        )
        # FIX: these vao and vbo are never released from memory, will it cause issue? 

    def set_rt_shader_uniforms(self, mobjects_rt: List[MobjectRT]) :
        shader: moderngl.Program = self.rtprogram

        # uniforms of camera perspectives
        for name, value in self.perspective_uniforms.items():
            try:
                if isinstance(value, np.ndarray) and value.ndim > 0:
                    value = tuple(value)
                shader[name].value = value
            except KeyError:
                pass # the uniform isn't declared in the shader program
        
        # uniforms of rt mobjects
        
        # uniforms of textures, lights, etc

    def capture(self, mobjects: List[Mobject], mobjects_rt: List[MobjectRT]) -> None:
        self.refresh_perspective_uniforms()
        
        # draw the RayTracing quad
        self.set_ctx_depth_test(False)
        self.set_rt_shader_uniforms(mobjects_rt)
        self.quad_vao.render(moderngl.TRIANGLE_STRIP)
        
        # draw depth masks (of the RTMobject)
        self.set_ctx_depth_test(True)
        gl.glColorMask(False, False, False, False)
        
        for mobject_rt in mobjects_rt:
            depth_mask: Mobject = mobject_rt.depth_mask
            # TODO, lock the static RTmobjects to avoid creating 
            # a new group of vao/vbo any single frame.
            get_render_group_list = map(self.get_render_group, depth_mask.get_shader_wrapper_list())
            for render_group in get_render_group_list:
                self.render_mask(render_group)
        
        # draw the non-rt mobjects
        gl.glColorMask(True, True, True, True)
        for mobject in mobjects:
            for render_group in self.get_render_group_list(mobject):
                self.render(render_group)

    def render_mask(self, render_group: dict[str]) -> None:
        shader_wrapper = render_group["shader_wrapper"]
        shader_program = render_group["prog"]
        self.set_shader_uniforms(shader_program, shader_wrapper)
        render_group["vao"].render(int(shader_wrapper.render_primitive))
        self.release_render_group(render_group) # TODO, only release the single-used ones


class RTScene(Scene):
    CONFIG = {
        "camera_class": RTCamera
    }
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mobjects_rt: list[MobjectRT] = []
    
    def remove_rt(self, *mobjects_rt_to_remove: MobjectRT):
        self.mobjects_rt = [m for m in self.mobjects_rt if m not in mobjects_rt_to_remove]

    def add_rt(self, *new_mobjects_rt: MobjectRT):
        self.remove_rt(*new_mobjects_rt) # remove the objects in case they already exist in the list
        self.mobjects_rt += new_mobjects_rt

    def add(self, *new_objects: Union[Mobject, MobjectRT]):
        """
        both Mobject and MobjectRT are supported
        """
        new_mobjects = (m for m in new_objects if isinstance(m, Mobject))
        new_mobjects_rt = (m for m in new_objects if isinstance(m, MobjectRT))

        super().add(*new_mobjects)
        self.add_rt(*new_mobjects_rt)

        return self

    def remove(self, *objects_to_remove: Union[Mobject, MobjectRT]):
        """
        both Mobject and MobjectRT are supported
        """
        mobjects_to_remove = (m for m in objects_to_remove if isinstance(m, Mobject))
        mobjects_rt_to_remove = (m for m in objects_to_remove if isinstance(m, MobjectRT))

        super().remove(*mobjects_to_remove)
        self.remove_rt(*mobjects_rt_to_remove)

        return self

    def update_frame(self, dt: float = 0, ignore_skipping: bool = False) -> None:
        self.increment_time(dt)
        self.update_mobjects(dt)
        if self.skip_animations and not ignore_skipping:
            return

        if self.window:
            self.window.clear()
        self.camera.clear()
        self.camera.capture(self.mobjects, self.mobjects_rt) ##

        if self.window:
            self.window.swap_buffers()
            vt = self.time - self.virtual_animation_start_time
            rt = time.time() - self.real_animation_start_time
            if rt < vt:
                self.update_frame(0)
    
    def unlock_mobject_data(self) -> None:
        """
        whenever a piece of animation finishes or interactive mode ends,
        manim will release all the vao/vbo/... OpenGL objects from the memory.
        """
        self.camera.release_static_mobjects()
        
        # FIX, I dont think it appropriate to release the quad vao for rt here
        # since they are still needed till the end of the scene.