attribute vec3 Vertex_position;
attribute vec3 Vertex_normal;
uniform vec3 offset;
varying vec3 baseNormal;
void main() {
    gl_Position = gl_ModelViewProjectionMatrix * vec4(
        Vertex_position + offset, 1.0
    );
    baseNormal = gl_NormalMatrix * normalize(Vertex_normal);
}