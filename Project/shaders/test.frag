vec2 phong_weightCalc(
    in vec3 light_pos, // light position
    in vec3 half_light, // half-way vector between light and view
    in vec3 frag_normal, // geometry normal
    in float shininess
) {
    // returns vec2( ambientMult, diffuseMult )
    float n_dot_pos = max( 0.0, dot(
        frag_normal, light_pos
    ));
    float n_dot_half = 0.0;
    if (n_dot_pos > -.05) {
        n_dot_half = pow(max(0.0,dot(
            half_light, frag_normal
        )), shininess);
    }
    return vec2( n_dot_pos, n_dot_half);
}

uniform vec4 Global_ambient;
uniform vec4 Light_ambient;
uniform vec4 Light_diffuse;
uniform vec4 Light_specular;
uniform vec3 Light_location;
uniform float Material_shininess;
uniform vec4 Material_specular;
uniform vec4 Material_ambient;
uniform vec4 Material_diffuse;
varying vec3 baseNormal;
void main() {
    // normalized eye-coordinate Light location
    vec3 EC_Light_location = normalize(
        gl_NormalMatrix * Light_location
    );
    // half-vector calculation
    vec3 Light_half = normalize(
        EC_Light_location - vec3( 0,0,-1 )
    );
    vec2 weights = phong_weightCalc(
        EC_Light_location,
        Light_half,
        baseNormal,
        Material_shininess
    );
    gl_FragColor = clamp(
    (
        (Global_ambient * Material_ambient)
        + (Light_ambient * Material_ambient)
        + (Light_diffuse * Material_diffuse * weights.x)
        // material's shininess is the only change here...
        + (Light_specular * Material_specular * weights.y)
    ), 0.0, 1.0);
}