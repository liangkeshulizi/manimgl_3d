#version 330 core

uniform float is_fixed_in_frame;
uniform float relative_focal_distance;
uniform mat4 view;
uniform float height_scale;

uniform sampler2D tex_height;

in vec3 point;
// in vec3 du_point;
// in vec3 dv_point;
in vec3 normal;
in vec3 tangent;
in vec2 tex_coords;

out vec3 WorldPos;
out vec3 Normal;
out vec3 Tangent;
out vec2 tex_coords_v;

const float DEFAULT_FRAME_HEIGHT = 8.0;
const float ASPECT_RATIO = 16.0 / 9.0;
const float X_SCALE = 2.0 / DEFAULT_FRAME_HEIGHT / ASPECT_RATIO;
const float Y_SCALE = 2.0 / DEFAULT_FRAME_HEIGHT;


void emit_gl_Position(vec3 point){

    vec4 fixed_point = vec4(point, 1.0);
    vec4 rotated_point = view * fixed_point; // also scaled at this point 
    
    vec4 result = mix(rotated_point, fixed_point, is_fixed_in_frame);
    
    // Essentially a projection matrix
    result.x *= X_SCALE;
    result.y *= Y_SCALE;
    result.z /= relative_focal_distance;
    result.w = 1.0 - result.z;

    // Flip and scale to prevent premature clipping
    result.z *= -0.1;
    gl_Position = result;
}

vec3 get_surface_unit_normal_vector(vec3 point, vec3 du_point, vec3 dv_point){
    vec3 cp = cross(
        (du_point - point),
        (dv_point - point)
    );
    if(length(cp) == 0){
        // Instead choose a normal to just dv_point - point in the direction of point
        vec3 v2 = dv_point - point;
        cp = cross(cross(v2, point), v2);
    }
    return normalize(cp);
}

void main(){
    tex_coords_v = tex_coords;

    WorldPos = point;

    // Normal = get_surface_unit_normal_vector(point, du_point, dv_point);
    Normal = normalize(normal);
    
    // Gram–Schmidt process
    // Tangent = normalize(du_point - point);
    // Tangent = normalize(Tangent - dot(Tangent, Normal) * Normal);
    Tangent = normalize(tangent);
    
    float height = texture(tex_height, tex_coords).r;

    // Emit gl position
    emit_gl_Position(point + Normal * height * height_scale);

    // if(clip_plane.xyz != vec3(0.0, 0.0, 0.0)){
    //     gl_ClipDistance[0] = dot(vec4(point, 1.0), clip_plane);
    // }

}