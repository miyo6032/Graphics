import sys
import OpenGL.GL as gl
import OpenGL.GLUT as glut
from OpenGL.arrays import vbo
from OpenGL.GL import shaders
import numpy as np

# Shaders
vertex_code = """
varying vec4 vertex_color;
void main()
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    vertex_color = gl_Color;
}
"""

fragment_code = """
varying vec4 vertex_color;
void main()
{
    gl_FragColor = vertex_color;
}
"""

# Holds the data
# Right now it is just a triangle and a square
data = np.array( [
    [  0, 1, 0,  0,1,0 ],
    [ -1,-1, 0,  1,1,0 ],
    [  1,-1, 0,  0,1,1 ],
    [  2,-1, 0,  1,0,0 ],
    [  4,-1, 0,  0,1,0 ],
    [  4, 1, 0,  0,0,1 ],
    [  2,-1, 0,  1,0,0 ],
    [  4, 1, 0,  0,0,1 ],
    [  2, 1, 0,  0,1,1 ],
    ],'f')

data = np.array([np.concatenate((v[:3] * 0.25, v[3:])) for v in data], 'f')
print(data)
vbo = vbo.VBO(data) # Turn it into a format that opengl can use

glut.glutInit() # Creates the opengl context
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA)
glut.glutCreateWindow('Hello world!')
glut.glutReshapeWindow(512,512)

try:
    vertex_shader = shaders.compileShader(vertex_code, gl.GL_VERTEX_SHADER)
    fragment_shader = shaders.compileShader(fragment_code, gl.GL_FRAGMENT_SHADER)

    shader = shaders.compileProgram(vertex_shader,fragment_shader)
except(gl.GLError, RuntimeError) as err:
    print("Shader Compilation Error:")
    print(err)
    exit()

# The redisplay function that gets called every update
def display():
    shaders.glUseProgram(shader)
    try:
        vbo.bind()
        try:
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY);
            gl.glEnableClientState(gl.GL_COLOR_ARRAY);
            gl.glVertexPointer(3, gl.GL_FLOAT, 24, vbo)
            gl.glColorPointer(3, gl.GL_FLOAT, 24, vbo + 12)
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, 9)
        finally:
            vbo.unbind()
            gl.glDisableClientState(gl.GL_VERTEX_ARRAY);
            gl.glDisableClientState(gl.GL_COLOR_ARRAY);
    finally:
        shaders.glUseProgram(0) # Go back to the legacy pipeline
    glut.glutSwapBuffers()

def reshape(width,height):
    gl.glViewport(0, 0, width, height)

def keyboard( key, x, y ):
    if key == b'\x1b':
        sys.exit( )

glut.glutReshapeFunc(reshape)
glut.glutDisplayFunc(display)
glut.glutKeyboardFunc(keyboard)
glut.glutMainLoop()