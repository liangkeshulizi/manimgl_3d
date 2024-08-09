#version 330 core

layout (location = 0) in vec3 point;
layout (location = 1) in vec2 tex_coords;

out vec2 tex_coords_v;

void main(){
    tex_coords_v = tex_coords;
    gl_Position = vec4(point, 1.0);
}