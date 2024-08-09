// TODO: this is a hack to fix the z-buffer glitch for the vanilla manimgl Mobjects

// uniform vec3 camera_offset;
// uniform mat3 camera_rotation;

// Note: only compatible with PBRCamera !
uniform mat4 view;
uniform float relative_focal_distance;

const float DEFAULT_FRAME_HEIGHT = 8.0;
const float ASPECT_RATIO = 16.0 / 9.0;
const float X_SCALE = 2.0 / DEFAULT_FRAME_HEIGHT / ASPECT_RATIO;
const float Y_SCALE = 2.0 / DEFAULT_FRAME_HEIGHT;

// this is totally a hack, not the right way to do this.
float perspective_scale_factor(float z, float focal_distance){
    return 1.0;// max(0.0, focal_distance / (focal_distance - z));
}

// copied from the latest version of manimgl
vec4 get_gl_Position(vec3 point){
    // FIX: this introduces unnecessary overhead
    vec4 rotated_point = vec4(point, 1.0);
    vec4 fixed_point = inverse(view) * rotated_point;
    
    vec4 result = mix(rotated_point, fixed_point, is_fixed_in_frame);
    
    // Essentially a projection matrix
    result.x *= X_SCALE;
    result.y *= Y_SCALE;
    result.z /= relative_focal_distance;
    result.w = 1.0 - result.z;

    // Flip and scale to prevent premature clipping
    result.z *= -0.1;
    return result;
}