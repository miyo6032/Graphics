attribute vec3 vertex_position; // The vertex position
attribute vec3 vertex_normal; // The normal

// The offset from model space to world space
// Apparently people use a matrix for this, but whatever,
// I'll learn that eventually maybe
uniform vec3 offset;

out vec3 frag_pos; // Outputs the vertex position in world space
out vec3 normal; // Send the normal along to the fragment shader

void main() {
    vec3 world_vec3 = vertex_position + offset;
    gl_Position = gl_ModelViewProjectionMatrix * vec4(world_vec3, 1.0);
    normal = normalize(vertex_normal);
    frag_pos = world_vec3;
}