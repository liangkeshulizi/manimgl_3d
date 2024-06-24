#version 330 core
precision highp float;

in vec2 coords;
out vec2 coords_v; // the coordinates of the fragment in screen space (ranging from -1 to 1)
out vec3 position; // the Real-World Position of the point on the camera frame

uniform mat3 camera_rotation;
uniform vec3 camera_offset;
uniform vec2 frame_shape;

void main(){
    coords_v = coords;
    position = inverse(camera_rotation) * vec3(coords * frame_shape / 2., 0.0) + camera_offset; // right or not?
    gl_Position = vec4(coords, 0.0, 1.0); // Normalized Device Coordinates
}