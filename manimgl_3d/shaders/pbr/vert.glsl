#version 330 core

uniform vec2 frame_shape;
uniform float anti_alias_width;
uniform vec3 camera_offset;
uniform mat3 camera_rotation;
uniform float is_fixed_in_frame;
uniform float focal_distance;
uniform vec4 clip_plane;

in vec3 point;
in vec3 du_point;
in vec3 dv_point;
in vec4 color;

out vec3 WorldPos;
out vec3 Normal;
out vec4 Color;

const float DEFAULT_FRAME_HEIGHT = 8.0;
const float ASPECT_RATIO = 16.0 / 9.0;
const float X_SCALE = 2.0 / DEFAULT_FRAME_HEIGHT / ASPECT_RATIO;
const float Y_SCALE = 2.0 / DEFAULT_FRAME_HEIGHT;


void emit_gl_Position(vec3 point){
    vec4 fixed_point = vec4(point, 1.0);
    vec4 rotated_point = vec4(camera_rotation * (point - camera_offset), 1.0);
    
    vec4 result = mix(rotated_point, fixed_point, is_fixed_in_frame);
    
    // Essentially a projection matrix
    result.x *= X_SCALE;
    result.y *= Y_SCALE;
    result.z /= focal_distance;
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
    Color = color;
    WorldPos = point;
    Normal = get_surface_unit_normal_vector(point, du_point, dv_point);
    
    // Emit gl position
    gl_Position = emit_gl_Position(point);

    // Not sure what this does
    if(clip_plane.xyz != vec3(0.0, 0.0, 0.0)){
        gl_ClipDistance[0] = dot(vec4(point, 1.0), clip_plane);
    }

}