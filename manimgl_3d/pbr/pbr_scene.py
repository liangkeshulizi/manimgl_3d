from manimlib import *
from manimgl_3d.camera_frame import MyCameraFrame
from manimgl_3d.pbr.surface_pbr import PointLight
from manimgl_3d.shader_compatibility import get_shader_code_from_file_extended
from manimgl_3d.utils.gl_utils import render_quad, blit_fbo, gl_blit_fbo

from OpenGL.GL import * # FIX
from typing import List

# TODO: support multiple light sources and light types (other than point light source)
class PBRCamera(Camera):
    
    CONFIG = {
        'frame_config' : {},
        'light_source_position': [-10., 10., 10.],
        'samples': 0,      # for multisampling anti-alias
        'exposure': 1.0,   # for HDR tone mapping
        'bloom': False,
        'bloom_threshold': 1.0,
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
        self.set_ctx_blending(True)

    def init_pbr(self) -> None:
        pw, ph = self.pixel_width, self.pixel_height

        # HDR MSAA FBO -> hdr_color_buffer_msaa, hdr_bright_buffer_msaa
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

        # HDR FBO -> hdr_color_buffer, hdr_bright_buffer
        self.hdr_color_buffer = self.ctx.texture(
                size=(pw, ph),
                components=self.n_channels,
                internal_format = GL_RGBA16F
            )
        self.hdr_color_buffer.repeat_x, self.hdr_color_buffer.repeat_y = False, False
        self.hdr_bright_buffer = self.ctx.texture(
            size=(pw, ph),
            components=self.n_channels,
            internal_format = GL_RGBA16F
        )
        self.hdr_bright_buffer.repeat_x, self.hdr_bright_buffer.repeat_y = False, False
        self.fbo_hdr = self.ctx.framebuffer(
            color_attachments = (self.hdr_color_buffer, self.hdr_bright_buffer),
            depth_attachment = self.ctx.depth_renderbuffer((pw, ph))
        )

        # FBO for bloom effect
        self.fbos_pingpong: List[moderngl.Framebuffer] = []
        for _ in range(2):
            pingpang_color_buffer = self.ctx.texture(
                size=(pw, ph),
                components=self.n_channels,
                internal_format = GL_RGBA16F # HDR
            )
            pingpang_color_buffer.repeat_x, pingpang_color_buffer.repeat_y = False, False
            fbo_pingpang = self.ctx.framebuffer(color_attachments=(pingpang_color_buffer,), depth_attachment=None)
            self.fbos_pingpong.append(fbo_pingpang)
        
        # shader programs
        self.gaussian_blur_program = self.ctx.program(
            vertex_shader = get_shader_code_from_file_extended('pbr/quad_vert.glsl'),
            fragment_shader = get_shader_code_from_file_extended('pbr/gaussian_blur_frag.glsl')
        )
        
        self.bloom_final_program = self.ctx.program(
            vertex_shader = get_shader_code_from_file_extended('pbr/quad_vert.glsl'),
            fragment_shader = get_shader_code_from_file_extended('pbr/bloom_final_frag.glsl')
        )
        self.bloom_final_program["hdr_rendered"] = 0  # glUniform1i(0, 0)
        self.bloom_final_program["bright_blurred"] = 1  # glUniform1i(1, 1)
        self.bloom_final_program['exposure'] = self.exposure
        
        self.no_bloom_final_program = self.ctx.program(
            vertex_shader = get_shader_code_from_file_extended('pbr/quad_vert.glsl'),
            fragment_shader = get_shader_code_from_file_extended('pbr/no_bloom_final_frag.glsl')
        )
        self.no_bloom_final_program["hdr_rendered"] = 0
        self.no_bloom_final_program['exposure'] = self.exposure

    def init_light_source(self):
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
            "light_color":              tuple(self.light_source.get_light_color()),
            "relative_focal_distance":  frame.get_focal_distance() / frame.get_scale(), # FIXED: not sure why unscale it, but it just works!
            "view":                     tuple(view_matrix.T.flatten()), # including frame scaling information
            "bloom_threshold":          self.bloom_threshold
        }

    def clear(self): # called in Scene.update_frame(), improper?
        self.fbo.clear(1., 0., 0., 1.)
        self.fbo_hdr_msaa.clear(0., 0., 0., 1.)
        self.fbo_hdr.clear(0., 0., 0., 1.)
        self.fbos_pingpong[0].clear(0., 0., 0., 1.)
        self.fbos_pingpong[1].clear(0., 0., 0., 1.)

    def get_raw_fbo_data(self, dtype: str = 'f1'):
        return self.fbo.read(
            viewport=self.fbo.viewport,
            components=self.n_channels,
            dtype=dtype
        )

    def capture(self, *mobjects: Mobject): # TODO: support light objects
        self.refresh_perspective_uniforms()
        
        self.fbo_hdr_msaa.use()
        # Fuck! this may change the readbuffer & drawbuffer in the background! equivelent to:
        # glReadBuffer(GL_COLOR_ATTACHMENT0)
        # glDrawBuffers([GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1])
        # BindFramebuffer(GL_FRAMEBUFFER, self->framebuffer_obj)
        
        for mobject in mobjects:
            for render_group in self.get_render_group_list(mobject):
                self.render(render_group)

        glDisable(GL_DEPTH_TEST)

        blit_fbo(self.ctx, self.fbo_hdr_msaa, self.fbo_hdr) # resolve from multisampling fbo into the normal fbo
        if self.bloom:
            self.hdr_bright_buffer.use()
            self.fbos_pingpong[0].use()
            render_quad(self.ctx, self.gaussian_blur_program)
            
            # glActiveTexture(GL_TEXTURE0)
            # glBindTexture(GL_TEXTURE_2D, self.fbos_pingpong[0].color_attachments[0].glo)
            # glActiveTexture(GL_TEXTURE1)
            # glBindTexture(GL_TEXTURE_2D, self.hdr_color_buffer.glo)
            self.hdr_color_buffer.use(location=0)
            self.fbos_pingpong[0].color_attachments[0].use(location=1)
            self.fbo.use()
            render_quad(self.ctx, self.bloom_final_program)
        else:
            self.hdr_color_buffer.use()
            self.fbo.use()
            render_quad(self.ctx, self.no_bloom_final_program)


class PBRScene(Scene):
    CONFIG = {
        "camera_class": PBRCamera, # SurfacePBRs should come with CameraPBR
        # TODO: delete it. Implemenet standalong light mobject to determine lighting setups.
        "camera_config":{
        "light_source_position" : OUT * 5 + LEFT * 5
        }
    }