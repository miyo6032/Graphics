#version 330
layout (lines) in;
layout (line_strip, max_vertices = 20) out;

uniform mat4 view_mat;
uniform mat4 proj_mat;

uniform float time;

in VERTEX_OUT {
    vec4 color;
} geometry_in[];

out vec4 frag_line_color;

void main() {
    gl_Position = proj_mat * view_mat * gl_in[0].gl_Position;
    frag_line_color = geometry_in[0].color;
    EmitVertex();
    gl_Position = proj_mat * view_mat * gl_in[1].gl_Position;
    frag_line_color = geometry_in[1].color;
    EmitVertex();
    EndPrimitive();
}
