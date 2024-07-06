// TODO: not used yet
// TODO: this is a hack to fix the z-buffer glitch for the vanilla manimgl Mobjects


uniform float is_fixed_in_frame;
uniform mat4 view;
uniform float focal_distance;

const float DEFAULT_FRAME_HEIGHT = 8.0;
const float ASPECT_RATIO = 16.0 / 9.0;
const float X_SCALE = 2.0 / DEFAULT_FRAME_HEIGHT / ASPECT_RATIO;
const float Y_SCALE = 2.0 / DEFAULT_FRAME_HEIGHT;


float perspective_scale_factor(float z, float focal_distance){
    return max(0.0, focal_distance / (focal_distance - z));
}

// copied from the latest version of manimgl
vec4 get_gl_Position(vec3 point){
    // FIX: this introduces unnecessary overhead
    vec4 fixed_point = vec4(inverse(camera_rotation) * point + camera_offset, 1.0);
    vec4 rotated_point = vec4(point, 1.0);
    
    vec4 result = mix(rotated_point, fixed_point, is_fixed_in_frame);
    
    // Essentially a projection matrix
    result.x *= X_SCALE;
    result.y *= Y_SCALE;
    result.z /= focal_distance;
    result.w = 1.0 - result.z;

    // Flip and scale to prevent premature clipping
    result.z *= -0.1;
    return result;
}