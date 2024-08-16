#version 330 core

uniform sampler2D hdr_rendered;
uniform sampler2D bright_blurred;

uniform float exposure;

in vec2 tex_coords_v;
out vec4 FragColor;

void main(){
    // blending
    vec4 color_hdr = texture(hdr_rendered, tex_coords_v);
    vec4 color_bright = texture(bright_blurred, tex_coords_v);
    vec3 color = color_hdr.rgb + color_bright.rgb;
    
    // tone mapping
    vec3 result = vec3(1.0) - exp( - color * exposure );
    
    // gamma correct
    result = pow(result, vec3(1.0 / 2.2));
    
    FragColor = vec4(result, 1.0);
}