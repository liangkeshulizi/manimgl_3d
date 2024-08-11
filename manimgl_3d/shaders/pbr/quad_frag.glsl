#version 330 core

uniform sampler2D tex_img;
in vec2 tex_coords_v;
out vec4 FragColor;

void main(){
    FragColor = texture(tex_img, tex_coords_v);
}