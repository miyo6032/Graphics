#version 330

in vec3 vertex_position;
in vec4 line_color;
in float edge_strength; // 0 for if the line is directed, 1 if the line is strongly connected aka connected from both sides or undirected
// Graphically, this just means 0 for an animated line, and 1 for a regular line

uniform mat4 model_mat;

// Use an interface block to push to geometry shader
// I dunno why besides good practice and good organization
out VERTEX_OUT {
    vec4 color;
    float line_strength;
} vs_out;

void main() {
    gl_Position = model_mat * vec4(vertex_position, 1.0);
    vs_out.color = line_color;
    vs_out.line_strength = edge_strength;
}