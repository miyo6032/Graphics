#version 330
layout (lines) in;
layout (line_strip, max_vertices = 20) out;

// Since I want to work with world space in this shader,
// I'm pulling in these matrices here instead of the vertex shader.
uniform mat4 view_mat;
uniform mat4 proj_mat;

// Time for animation
uniform float time;

in VERTEX_OUT {
    vec4 color;
} geometry_in[];

out vec4 frag_line_color;

void main() {
    // Get the direction the line is facing
    vec3 direction = gl_in[1].gl_Position.xyz - gl_in[0].gl_Position.xyz;
    float stripe_length = length(direction) * 0.1;

    vec3 increment = normalize(direction) * stripe_length;
    vec3 offset = increment * time; // Offset where the stripes come from the line
    vec3 end_offset = increment * (1 - time); // Offset where the strips go into the line
    vec3 position = gl_in[0].gl_Position.xyz + offset;

    // This alternates the colors in an animated fashion.
    // The ends are particularly tricky to make sure they don't go thought the node to the other side
    gl_Position = proj_mat * view_mat * gl_in[0].gl_Position;
    frag_line_color = geometry_in[0].color;
    EmitVertex();
    gl_Position = proj_mat * view_mat * vec4(position, 1.0);
    frag_line_color = vec4(0);
    EmitVertex();
    position += offset;
    gl_Position = proj_mat * view_mat * vec4(position, 1.0);
    frag_line_color = geometry_in[0].color;
    EmitVertex();

    for(int i = 0; i < 9; i++)
    {
        gl_Position = proj_mat * view_mat * vec4(position, 1.0);
        if(i % 2 == 0){
            frag_line_color = geometry_in[0].color;
        }
        else{
            frag_line_color = vec4(0);
        }
        EmitVertex();
        position += increment;
    }

    position += end_offset - increment;

    gl_Position = proj_mat * view_mat * vec4(position, 1.0);
    frag_line_color = vec4(0);
    EmitVertex();
    position += end_offset;
    gl_Position = proj_mat * view_mat * gl_in[1].gl_Position;
    frag_line_color = geometry_in[0].color;
    EmitVertex();

    EndPrimitive();
}  