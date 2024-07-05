// This is for fixing the z-buffer glitch in the original release of manimgl,
// which is never used by PBRMobject and MobjectRT itself.

shufhuf

const vec2 DEFAULT_FRAME_SHAPE = vec2(8.0 * 16.0 / 9.0, 8.0);

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