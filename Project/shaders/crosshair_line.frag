#version 330
out vec4 FragColor;

in vec4 frag_line_color;

void main() {
    FragColor = frag_line_color;
}
