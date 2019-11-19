#version 330

attribute vec3 vertex_position;
attribute vec4 line_color;

uniform mat4 model_mat;

// Use an interface block to push to geometry shader
// I dunno why besides good practice and good organization
out VERTEX_OUT {
    vec4 color;
} vs_out;

void main() {
    gl_Position = model_mat * vec4(vertex_position, 1.0);
    vs_out.color = line_color;
}