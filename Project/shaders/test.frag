// uniform vec4 Light_ambient;
// uniform vec4 Light_diffuse;
// uniform vec4 Light_specular;
// uniform float Material_shininess;
// uniform vec4 Material_specular;
// uniform vec4 Material_diffuse;
// uniform vec3 camera_pos;
uniform vec3 material_ambient; // The material for ambient light
uniform vec3 global_ambient; // The global ambient light
uniform vec3 light_pos; // The position of the light in world space
uniform vec3 light_color;
uniform vec3 object_color;
uniform vec3 camera_pos; // The position of the camera in world space

in vec3 frag_pos;
in vec3 normal; // Assumes that this is normalize already
void main() {
    // The global component of the light
    vec3 global = material_ambient * global_ambient;

    // The diffuse component of the light
    vec3 light_dir = normalize(light_pos - frag_pos); // Get the direction from the fragment to the light
    float diff = max(dot(normal, light_dir), 0.0); // Dot the normal with the light direction
    vec3 diffuse = diff * light_color;

    // The specular component of the light
    float specular_strength = 0.5;
    vec3 view_dir = normalize(camera_pos - frag_pos); // The direction from the fragment to the viewer
    vec3 halfway_dir = normalize(light_dir + view_dir); // Use the blinn-phong halfway vector
    float spec = pow(max(dot(normal, halfway_dir), 0.0), 32);
    vec3 specular = specular_strength * spec * light_color;

    // Sum up all components of the light
    vec3 result = (global + diff + specular) * object_color;
    gl_FragColor = vec4(result, 1.0);
}