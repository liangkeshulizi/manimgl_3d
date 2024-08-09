#version 330 core

uniform sampler2D image;

in vec2 tex_coords_v;
out vec4 FragColor;

uniform float weight[6] = float[] (0.25, 0.2270270270, 0.1945945946, 0.1216216216, 0.0540540541, 0.0162162162);

void main(){
    vec2 tex_offset = 1.0 / textureSize(image, 0);
    vec3 result = vec3(0.);
    vec2 coords;
    float weight2d;
    for(int i = -20; i < 20; ++i){
        for(int j = -20; j < 20; ++j){
            coords = tex_coords_v + vec2(tex_offset.x * i, tex_offset.y * j);
            // weight2d = weight[abs(i)] * weight[abs(j)] * .8; /////////
            // result += texture(image, coords).rgb * weight2d;
            result += texture(image, coords).rgb * 1./(40.*40.);
        }
    }
    FragColor = vec4(result, 1.0);
    // FragColor = vec4(0., 1., 0., 1.0);
}