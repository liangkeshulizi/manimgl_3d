#version 330 core

uniform sampler2D hdr_rendered;

uniform float exposure;

in vec2 tex_coords_v;
out vec4 FragColor;

void main(){
    // tone mapping
    vec3 result = vec3(1.0) - exp( - texture(hdr_rendered, tex_coords_v).rgb * exposure );
    
    // gamma correct
    result = pow(result, vec3(1.0 / 2.2));
    
    FragColor = vec4(result, 1.0);
}