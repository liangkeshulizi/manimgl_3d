'''This can be seen as a playground where I tinker with different implementations with PyOpenGL and ModernGL.'''

import numpy as np
import glm
from OpenGL.GL import *
import moderngl as mgl
from functools import cache
from PIL import Image
from typing import Union, Sequence

from manimgl_3d.shader_compatibility import get_shader_code_from_file_extended


def _my_texture_configuration(texture: mgl.Texture) -> None: # abondoned
    glBindTexture(GL_TEXTURE_2D, texture.glo)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

# implemented with PyOpenGL
@cache
def gl_get_quad_vao() -> int:
    # data
    quadVertices = glm.array(glm.float32,
            #positions      texture Coords
            -1.0,  1.0, 0.0, 0.0, 1.0,
            -1.0, -1.0, 0.0, 0.0, 0.0,
             1.0,  1.0, 0.0, 1.0, 1.0,
             1.0, -1.0, 0.0, 1.0, 0.0
    )
    # set up vao and vbo
    VAO_name = glGenVertexArrays(1)
    VBO_name = glGenBuffers(1)
    glBindVertexArray(VAO_name)
    glBindBuffer(GL_ARRAY_BUFFER, VBO_name)
    glBufferData(GL_ARRAY_BUFFER, quadVertices.nbytes, quadVertices.ptr, GL_STATIC_DRAW)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * glm.sizeof(glm.float32), None) # point
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * glm.sizeof(glm.float32), ctypes.c_void_p(3 * glm.sizeof(glm.float32))) # tex_coords

    return VAO_name

def gl_render_quad(): 
    '''Render using current context and bound shaders.'''
    quadVAO = gl_get_quad_vao()
    glBindVertexArray(quadVAO)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
    glBindVertexArray(0)


# implemented with moderngl

# NOTE: Due to the nature of modergl, whenever a VertexArray within a different context/program is needed,
# a new instance of VertexArray needs to be created. There is currently no way to ensure the old VAO is
# release properly.
@cache
def get_quad_vao(context: mgl.Context, program: mgl.Program) -> mgl.VertexArray:
    # data
    coords = np.array([
            -1.0,  1.0, 0.0, 0.0, 1.0,
            -1.0, -1.0, 0.0, 0.0, 0.0,
             1.0,  1.0, 0.0, 1.0, 1.0,
             1.0, -1.0, 0.0, 1.0, 0.0
        ], dtype = 'f4') # 4 bytes (32 bits) per float
    vbo = context.buffer(coords.tobytes())

    # NOTE: Buffer Format only describes the layout of data input from the app side,
    # while Internal Format describes the data format stored internally.
    vao = context.vertex_array(
            program = program,
            content = [(vbo, "3f4 2f4 /v", 'point', 'tex_coords')],
        )
    return vao

def render_quad(context: mgl.Context, program: mgl.Program):
    vao = get_quad_vao(context, program)
    vao.render(mgl.TRIANGLE_STRIP)

@cache
def get_quad_prog(ctx: mgl.Context):
    return ctx.program(
        vertex_shader=get_shader_code_from_file_extended('pbr/quad_vert.glsl'),
        fragment_shader=get_shader_code_from_file_extended('pbr/quad_frag.glsl')
    )

def render_texture_on_quad(ctx: mgl.Context, texture: mgl.Texture, frambuffer: mgl.Framebuffer):
    program = get_quad_prog(ctx)
    
    frambuffer.use()
    texture.use(location=0)
    program['tex_img'] = 0

    render_quad(ctx, program)


# implemented with PyopenGL
def gl_blit_fbo(src_fbo: mgl.Framebuffer, dst_fbo: mgl.Framebuffer, color_buffer_correspond = True, read_color_buffer = None, *,
             default_frame_color_buffer=GL_BACK
            ):
    '''ModernGL wrapper for Blit function in OpenGL, used for framebuffer copying and multisample resolving.'''
    if src_fbo.glo == dst_fbo.glo:
        return
    if color_buffer_correspond: # read color buffers -> CORRESPONDING color attachments
        if not (src_fbo.glo and dst_fbo.glo):
            raise ValueError("Please set `color_buffer_correspond` to False for copying from/to default framebuffer.")
        if len(src_fbo.color_attachments) != len(dst_fbo.color_attachments):
            raise ValueError("Destination and source framebuffers have different number of color attachments!")
        for i in range(len(src_fbo.color_attachments)):
            glBindFramebuffer(GL_READ_FRAMEBUFFER, src_fbo.glo)
            glReadBuffer(GL_COLOR_ATTACHMENT0 + i)
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, dst_fbo.glo)
            glDrawBuffer(GL_COLOR_ATTACHMENT0 + i)
            glBlitFramebuffer(
                *src_fbo.viewport,
                *dst_fbo.viewport,
                GL_COLOR_BUFFER_BIT, GL_LINEAR
            )
    else: # read_color_buffer -> EACH color attachments
        if read_color_buffer is None:
            read_color_buffer = GL_COLOR_ATTACHMENT0 if src_fbo.glo else default_frame_color_buffer
        glBindFramebuffer(GL_READ_FRAMEBUFFER, src_fbo.glo)
        glReadBuffer(read_color_buffer)
        
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, dst_fbo.glo)
        if dst_fbo.glo: # target is custom buffer
            glDrawBuffers([GL_COLOR_ATTACHMENT0 + i for i in range(len(dst_fbo.color_attachments))])
        else: # target is default buffer
            glDrawBuffer(default_frame_color_buffer)
        glBlitFramebuffer(
            *src_fbo.viewport,
            *dst_fbo.viewport,
            GL_COLOR_BUFFER_BIT, GL_LINEAR
        )

# implemented with ModernGL
def blit_fbo(context: mgl.Context, src_fbo: mgl.Framebuffer, dst_fbo: mgl.Framebuffer):
    # NOTE: CANNOT handle default framebuffer correctly.
    context.copy_framebuffer(dst_fbo, src_fbo)


@cache
def image_path_to_texture(context: mgl.Context, path: str) -> mgl.Texture:
    im = Image.open(path).convert("RGBA")
    return context.texture(
        size=im.size,
        components=len(im.getbands()), # 4
        data=im.tobytes()
    )

# TODO: can't cache because np.ndarray is not hashable
def get_solid_texture(context: mgl.Context, value: Union[float, np.ndarray, Sequence[float]], *, dtype = 'f4') -> mgl.Context:
    # NOTE: Only support float value
    if isinstance(value, float):
        value = (value,)
    data = np.array([*value], dtype = dtype)
    return context.texture(
        size = (1,1),
        components = len(value),
        data = data.tobytes(),
        dtype = dtype
    )

# TODO
# def gl_guassian_blur(input_texture: mgl.Texture):