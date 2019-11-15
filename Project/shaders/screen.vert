#version 330

attribute vec2 quad_pos;
attribute vec2 tex_coord;

out vec2 TexCoords;

void main()
{
    gl_Position = vec4(quad_pos.x, quad_pos.y, 0.0, 1.0); 
    TexCoords = tex_coord;
}  