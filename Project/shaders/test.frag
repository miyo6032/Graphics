#version 330

struct Material {
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float shininess;
}; 

struct Light {
    vec3 position;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
};
  
uniform Material material;
uniform Light light;

uniform vec3 light_pos; // The position of the light in world space
uniform vec3 object_color;
uniform vec3 camera_pos; // The position of the camera in world space

in vec3 frag_pos;
in vec3 normal; // Assumes that this is normalize already
void main() {
    // The ambient component of the light
    vec3 ambient = light.ambient * material.ambient;

    // The diffuse component of the light
    vec3 light_dir = normalize(light_pos - frag_pos); // Get the direction from the fragment to the light
    float diff = max(dot(normal, light_dir), 0.0); // Dot the normal with the light direction
    vec3 diffuse = diff * light.diffuse * material.diffuse;

    // The specular component of the light
    vec3 view_dir = normalize(camera_pos - frag_pos); // The direction from the fragment to the viewer
    vec3 halfway_dir = normalize(light_dir + view_dir); // Use the blinn-phong halfway vector
    float spec = pow(max(dot(normal, halfway_dir), 0.0), material.shininess);
    vec3 specular = spec * light.specular * material.specular;

    // Sum up all components of the light
    vec3 result = ambient + diffuse + specular;
    gl_FragColor = vec4(result, 1.0);
}