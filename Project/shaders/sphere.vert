uniform vec2 resolution;
attribute vec4 center;
attribute float radius;
varying vec4 v_center;
varying float v_radius;

void main()
{
    v_radius = radius;
    v_center = gl_ModelViewProjectionMatrix * center;
    gl_PointSize = 2.0 + ceil(2.0*v_radius);
    //gl_Position = vec4(2.0*center.xy/resolution-1.0, center.z, 1.0);
    gl_Position = v_center;
}