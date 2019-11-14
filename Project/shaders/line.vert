#version 330

attribute vec3 vertex_position;
attribute vec4 line_color;

uniform mat4 model_mat;
uniform mat4 view_mat;
uniform mat4 proj_mat;

out vec4 frag_line_color;

void main() {
    gl_Position = proj_mat * view_mat * model_mat * vec4(vertex_position, 1.0);
    frag_line_color = line_color;
}