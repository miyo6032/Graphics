#version 330
out vec4 FragColor;
  
in vec2 TexCoords;

uniform sampler2D texture;
  
uniform bool horizontal;
uniform float weight[5] = float[] (0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);

/*
 * Does a double pass gaussian blur (for efficency) to make the 
 * bloom effect for objects marked as bright
 * taken from https://learnopengl.com/Advanced-Lighting/Bloom
 */
void main()
{             
    vec2 tex_offset = 1.0 / textureSize(texture, 0); // gets size of single texel
    vec3 result = texture(texture, TexCoords).rgb * weight[0]; // current fragment's contribution
    if(horizontal)
    {
        for(int i = 1; i < 5; ++i)
        {
            result += texture(texture, TexCoords + vec2(tex_offset.x * i, 0.0)).rgb * weight[i];
            result += texture(texture, TexCoords - vec2(tex_offset.x * i, 0.0)).rgb * weight[i];
        }
    }
    else
    {
        for(int i = 1; i < 5; ++i)
        {
            result += texture(texture, TexCoords + vec2(0.0, tex_offset.y * i)).rgb * weight[i];
            result += texture(texture, TexCoords - vec2(0.0, tex_offset.y * i)).rgb * weight[i];
        }
    }
    FragColor = vec4(result, 1.0);
}