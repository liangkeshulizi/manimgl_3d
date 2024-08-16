#version 330 core

out vec4 FragColor;
in vec2 tex_coords_v;

uniform sampler2D scene;
uniform sampler2D bloomBlur;

uniform float exposure;
uniform float bloomStrength = 0.04f;


void main()
{
    // bloom mix
    vec3 hdrColor = texture(scene, tex_coords_v).rgb;
    vec3 bloomColor = texture(bloomBlur, tex_coords_v).rgb;
    vec3 result =  mix(hdrColor, bloomColor, bloomStrength); // linear interpolation
    
    // tone mapping
    result = vec3(1.0) - exp(-result * exposure);
    
    // gamma correction
    result = pow(result, vec3(1.0 / 2.2));
    
    FragColor = vec4(result, 1.0);
}
