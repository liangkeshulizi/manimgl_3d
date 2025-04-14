from manimlib import *
from manimgl_3d.camera_frame import MyCameraFrame
from manimgl_3d.pbr.surface_pbr import PointLight
from manimgl_3d.pbr.material import PBRMaterial
from manimgl_3d.shader_compatibility import *
from manimgl_3d.utils.gl_utils import render_quad, blit_fbo, gl_blit_fbo, render_texture_on_quad, get_quad_prog

from OpenGL.GL import * # FIX
from typing import List

# TODO: support multiple light sources and light types (other than point light source)
class PBRCamera(Camera):
    
    CONFIG = {
        'frame_config' : {},
        'light_source_position': [2., 2., 5.],

        'samples': 4,      # for multisampling anti-alias
        'exposure': 1.0,   # for HDR tone mapping
        
        # bloom effect related
        'bloom': True,
        'bloom_threshold': 1.0,
        'mip_depth': 6,    # You can play around with this value, should not be larger than log2(pixel_width)
        'bloom_filter_radius': 0.005,
        'bloom_strength': 0.04,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_pbr()

    def init_context(self, ctx: moderngl.Context | None = None) -> None:
        if ctx is None:
            ctx = moderngl.create_standalone_context()
            fbo = self.get_fbo(ctx, 0)
        else:
            fbo = ctx.detect_framebuffer()
        self.ctx = ctx
        self.fbo = fbo
        self.set_ctx_blending(True) # for compatiblity

    def init_pbr(self) -> None:
        pw, ph = self.pixel_width, self.pixel_height

        if self.n_channels != 4:
            raise NotImplementedError('PBRCamera currently only supports 4 components for color buffer (RGBA).')

        # HDR MSAA FBO -> hdr_color_buffer_msaa, hdr_bright_buffer_msaa
        # NOTE: for compatibility with normal Mobjects, use RGBA instead of RGB
        self.hdr_color_buffer_msaa = self.ctx.texture(
                size=(pw, ph),
                components=self.n_channels,
                samples=self.samples,
                internal_format = GL_RGBA16F # use floating point framebuffers for HDR
            )
        self.hdr_bright_buffer_msaa = self.ctx.texture(
            size=(pw, ph),
            components=self.n_channels,
            samples=self.samples,
            internal_format = GL_RGBA16F
        )
        self.fbo_hdr_msaa = self.ctx.framebuffer(
            color_attachments = (self.hdr_color_buffer_msaa, self.hdr_bright_buffer_msaa),
            depth_attachment = self.ctx.depth_renderbuffer((pw, ph), samples=self.samples)
        )

        # HDR FBO -> hdr_color_buffer, hdr_bright_buffer (for resolution)
        self.hdr_color_buffer = self.ctx.texture(
                size=(pw, ph),
                components=self.n_channels,
                internal_format = GL_RGBA16F
            )
        self.hdr_color_buffer.repeat_x, self.hdr_color_buffer.repeat_y = False, False
        self.hdr_bright_buffer = self.ctx.texture(  # TODO: Abandoned
            size=(pw, ph),
            components=self.n_channels,
            internal_format = GL_RGBA16F
        )
        self.hdr_bright_buffer.repeat_x, self.hdr_bright_buffer.repeat_y = False, False
        self.fbo_hdr = self.ctx.framebuffer(
            color_attachments = (self.hdr_color_buffer, self.hdr_bright_buffer),
            depth_attachment = self.ctx.depth_renderbuffer((pw, ph))
        )

        # # FBO for bloom effect (legacy)
        # self.fbos_pingpong: List[moderngl.Framebuffer] = []
        # for _ in range(2):
        #     pingpang_color_buffer = self.ctx.texture(
        #         size=(pw, ph),
        #         components=self.n_channels,
        #         internal_format = GL_RGBA16F
        #     )
        #     pingpang_color_buffer.repeat_x, pingpang_color_buffer.repeat_y = False, False
        #     fbo_pingpang = self.ctx.framebuffer(color_attachments=(pingpang_color_buffer,), depth_attachment=None)
        #     self.fbos_pingpong.append(fbo_pingpang)

        # textures and fbo for bloom mipmaps
        self.mip_chain = [] # large to small
        for i in range(self.mip_depth):
            mip_size_float = (pw/2**(i+1), ph/2**(i+1))
            mip_size_int = (int(pw/2**(i+1)), int(ph/2**(i+1)))
            
            mip_map = self.ctx.texture(
                size = mip_size_int,
                components = 3, ##
                internal_format = GL_R11F_G11F_B10F
            )
            mip_map.repeat_x, mip_map.repeat_y = False, False
            self.mip_chain.append((mip_size_float, mip_size_int, mip_map))
        
        self.fbo_bloom = self.ctx.framebuffer(
            color_attachments = (self.mip_chain[0][-1],) # color attachment of fbo_bloom will change dynamically during rendering
        )
        
        # pbr shader program
        self.gaussian_blur_program = self.ctx.program(
            vertex_shader = get_shader_code_from_file_extended('pbr/quad_vert.glsl'),
            fragment_shader = get_shader_code_from_file_extended('pbr/gaussian_blur_frag.glsl')
        )
        
        # # bloom shader program (legacy)
        # self.bloom_final_program = self.ctx.program(
        #     vertex_shader = get_shader_code_from_file_extended('pbr/quad_vert.glsl'),
        #     fragment_shader = get_shader_code_from_file_extended('pbr/bloom_final_frag.glsl')
        # )
        # self.bloom_final_program["hdr_rendered"] = 0  # glUniform1i(0, 0)
        # self.bloom_final_program["bright_blurred"] = 1  # glUniform1i(1, 1)
        # self.bloom_final_program['exposure'] = self.exposure

        # bloom downsample shader program
        self.downsample_program = self.ctx.program(
            vertex_shader = get_shader_code_from_file_extended('pbr/quad_vert.glsl'),
            fragment_shader = get_shader_code_from_file_extended('pbr/downsample_frag.glsl')
        )
        self.downsample_program["srcTexture"] = 0 # texture

        # bloom upsample shader program
        self.upsample_program = self.ctx.program(
            vertex_shader = get_shader_code_from_file_extended('pbr/quad_vert.glsl'),
            fragment_shader = get_shader_code_from_file_extended('pbr/upsample_frag.glsl')
        )
        self.upsample_program["srcTexture"] = 0
        self.upsample_program["filterRadius"] = self.bloom_filter_radius

        # bloom final shader program
        self.bloom_final_program = self.ctx.program(
            vertex_shader = get_shader_code_from_file_extended('pbr/quad_vert.glsl'),
            fragment_shader = get_shader_code_from_file_extended('pbr/bloom_final_frag.glsl')
        )
        self.bloom_final_program["scene"] = 0
        self.bloom_final_program["bloomBlur"] = 1
        self.bloom_final_program["exposure"] = self.exposure
        self.bloom_final_program["bloomStrength"] = self.bloom_strength

        # no bloom shader program (tone mapping + gamma correction)
        self.hdr_final_program = self.ctx.program(
            vertex_shader = get_shader_code_from_file_extended('pbr/quad_vert.glsl'),
            fragment_shader = get_shader_code_from_file_extended('pbr/no_bloom_final_frag.glsl')
        )
        self.hdr_final_program["hdr_rendered"] = 0
        self.hdr_final_program['exposure'] = self.exposure

    def init_light_source(self):
        # NOTE: This light source only affacts non-PBR mobjects. If you want it 
        # to also affacts PBR mobjects, add it to the scene explicitly:
        # self.add(self.camera.light_source)
        self.light_source = PointLight(self.light_source_position)

    def init_frame(self) -> None:
        self.frame = MyCameraFrame(**self.frame_config)

    def refresh_perspective_uniforms(self):
        frame = self.frame
        pw, ph = self.get_pixel_shape()
        fw, fh = frame.get_shape()

        # TODO, this should probably be a mobject uniform, with
        # the camera taking care of the conversion factor
        anti_alias_width = self.anti_alias_width / (ph / fh)
        rotation = frame.get_inverse_camera_rotation_matrix()

        view_matrix = frame.get_view_matrix()

        self.perspective_uniforms = {
            "frame_shape":              frame.get_shape(),
            "anti_alias_width":         anti_alias_width,

            # for compatibility with Mobjects (PBRCamera can also render normal Surface)
            "camera_offset":            tuple(frame.get_center()),
            "camera_rotation":          tuple(np.array(rotation).T.flatten()),
            "camera_position":          tuple(frame.get_implied_camera_location()),
            "focal_distance":           frame.get_focal_distance(),
            "light_source_position":    tuple(self.light_source.get_location()),
            
            # specifically for PBR objects
            "relative_focal_distance":  frame.get_focal_distance() / frame.get_scale(), # FIXME: not sure why unscale it, but it just works!
            "view":                     tuple(view_matrix.T.flatten()), # including frame scaling information
            "bloom_threshold":          self.bloom_threshold
        }

    def clear(self): # called in Scene.update_frame(), improper?
        self.fbo.clear(1., 0., 0., 1.)
        self.fbo_hdr_msaa.clear(0., 0., 0., 1.)
        self.fbo_hdr.clear(0., 0., 0., 1.)
        # self.fbos_pingpong[0].clear(0., 0., 0., 1.)
        # self.fbos_pingpong[1].clear(0., 0., 0., 1.)

    def get_raw_fbo_data(self, dtype: str = 'f1'):
        return self.fbo.read(
            viewport=self.fbo.viewport,
            components=self.n_channels,
            dtype=dtype
        )
    
    def use_pbr_textures(self, program: moderngl.Program, material: PBRMaterial):
        program['height_scale'] = material.height_scale
        for tid, name, texture  in material.get_pbr_textures(self.ctx):
            texture.use(location = tid)
            program['tex_' + name].value = tid

    def use_light_sources(self, program: moderngl.Program, lights: List[PointLight]):
        MAX_LIGHTS = 16

        light_count = len(lights)
        if light_count > MAX_LIGHTS:
            raise ValueError(f'Too many lights! Got {light_count}, but MAX_LIGHTS is {MAX_LIGHTS}.')

        light_positions = np.zeros((MAX_LIGHTS, 3), dtype='f4')
        light_colors = np.zeros((MAX_LIGHTS, 3), dtype='f4')
        for i, light in enumerate(lights):
            light_positions[i] = light.get_location()
            light_colors[i] = light.get_light_color()
        
        program['light_positions'].write(light_positions.flatten().tobytes())
        program['light_colors'].write(light_colors.flatten().tobytes())
        program['light_count'].value = light_count
    
    def render(self, render_group: dict[str]) -> None:
        if isinstance(render_group["shader_wrapper"], PBRShaderWrapper):
            self.use_pbr_textures(render_group["prog"], render_group["shader_wrapper"].material)
            self.use_light_sources(render_group["prog"], render_group["lights"])
        super().render(render_group)

    def capture(self, *mobjects: Mobject): # TODO: support light objects
        self.refresh_perspective_uniforms()
        
        self.fbo_hdr_msaa.use()
        # Fuck! this may change the readbuffer & drawbuffer in the background! equivelent to:
        # glReadBuffer(GL_COLOR_ATTACHMENT0)
        # glDrawBuffers([GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1])
        # BindFramebuffer(GL_FRAMEBUFFER, self->framebuffer_obj)
        
        # render_texture_on_quad(
        #     self.ctx,
        #     mobjects[-1].material.get_property_texture(self.ctx, "ao"),
        #     self.fbo
        # )
        # program = get_quad_prog(self.ctx)
        # self.fbo.use()
        # render_quad(self.ctx, program)
        # return

        lights = [mobject for mobject in mobjects if isinstance(mobject, PointLight)]
        for mobject in mobjects:
            if not isinstance(mobject, PointLight):
                for render_group in self.get_render_group_list(mobject):
                    render_group["lights"] = lights
                    self.render(render_group)

        glDisable(GL_DEPTH_TEST)
        
        blit_fbo(self.ctx, self.fbo_hdr_msaa, self.fbo_hdr) # resolve from multisampling fbo into the normal fbo
        if self.bloom:
            self.fbo_bloom.use() # glViewPort(self.mip_chain[0].viewport)
            self.hdr_color_buffer.use(location=0)
            self.downsample_program["srcResolution"] = (self.pixel_width, self.pixel_height)
            self.downsample_program["karis_average"] = 1 # enable karis average

            # down sample
            glDisable(GL_BLEND)
            for mip_size_float, mip_size_int, mip_map in self.mip_chain:
                self.fbo_bloom.viewport = (0, 0, *mip_size_int)
                glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, mip_map.glo, 0)
                
                render_quad(self.ctx, self.downsample_program)
                
                mip_map.use(location=0)
                self.downsample_program["srcResolution"] = mip_size_float
                self.downsample_program["karis_average"] = 0

            # up sample
            # Enable additive blending
            glEnable(GL_BLEND)
            glBlendFunc(GL_ONE, GL_ONE)
            glBlendEquation(GL_FUNC_ADD)
            
            for this_mip, next_mip in zip(self.mip_chain[::-1], self.mip_chain[-2::-1]):
                this_size_f, this_size_i, this_mip_map = this_mip
                next_size_f, next_size_i, next_mip_map = next_mip
                
                this_mip_map.use(location=0)
                self.fbo_bloom.viewport = (0, 0, *next_size_f)
                glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, next_mip_map.glo, 0)
                render_quad(self.ctx, self.upsample_program)

            glDisable(GL_BLEND)

            # final
            self.hdr_color_buffer.use(location=0)
            self.mip_chain[0][-1].use(location=1)
            self.fbo.use()
            render_quad(self.ctx, self.bloom_final_program)
            
            self.set_ctx_blending(True) # restore blending
            glBlendEquation(GL_FUNC_ADD)
            # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        else:
            self.hdr_color_buffer.use()
            self.fbo.use()
            render_quad(self.ctx, self.hdr_final_program)


class PBRScene(Scene):
    CONFIG = {
        "camera_class": PBRCamera,
        "camera_config":{},
        "window_config": {
            "size": (1920 * 2, 1080 * 2)
        },
    }
