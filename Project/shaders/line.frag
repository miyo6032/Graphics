#version 330
layout (location = 0) out vec4 FragColor;
layout (location = 1) out vec4 BrightColor;  

in vec4 frag_line_color;

void main() {
    FragColor = frag_line_color;

    // check whether fragment output is higher than threshold, if so output as brightness color
    float bloom_threshold = dot(FragColor.rgb, vec3(0.2126, 0.7152, 0.0722)); // Unbalanced because some colors are more "bright" to the eye
    if(bloom_threshold > 1.0)
        BrightColor = vec4(FragColor.rgb, 1.0);
    else
        BrightColor = vec4(0.0, 0.0, 0.0, 1.0);
}
