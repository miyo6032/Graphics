#version 330

uniform mat4 model_mat;
uniform mat4 view_mat;
uniform mat4 proj_mat;

attribute vec3 vertex_position; // The vertex position
attribute vec3 vertex_normal; // The normal

out vec3 frag_pos; // Outputs the vertex position in world space
out vec3 normal; // Send the normal along to the fragment shader

void main() {
    vec3 world_vec3 = vec3(model_mat * vec4(vertex_position, 1.0));
    gl_Position =  proj_mat * view_mat * vec4(world_vec3, 1.0);
    normal = normalize(vertex_normal);
    frag_pos = world_vec3;
}