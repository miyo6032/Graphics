import sys
import OpenGL.GL as gl
import OpenGL.GLUT as glut
import OpenGL.GLU as glu
from OpenGL.arrays import vbo
from OpenGL.GL import shaders
import numpy as np
import networkx as nx

# CREDIT
# https://www.labri.fr/perso/nrougier/python-opengl/#about-this-book
# http://pyopengl.sourceforge.net/context/tutorials/shader_1.html
# https://paroj.github.io/gltut/index.html

class Renderer:
    def __init__(self, graph):
        self.graph = graph

    # Loads the shader from files attempts to compile them, and returns the shader program
    def read_shaders(self, vertex_file, fragment_file):
        with open("./shaders/" + vertex_file, 'r') as file:
            vertex_code = file.read()
        with open("./shaders/" + fragment_file, 'r') as file:
            fragment_code = file.read()

        # Compile the shaders
        try:
            vertex_shader = shaders.compileShader(vertex_code, gl.GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fragment_code, gl.GL_FRAGMENT_SHADER)
            shader = shaders.compileProgram(vertex_shader,fragment_shader)
            return shader
        except(gl.GLError, RuntimeError) as err:
            print("Shader Compilation Error:")
            print(err)
            exit()

    def render(self, resolution, tick):
        pass

# In charge of rendering a spring representation of the network
class SpringNetworkRenderer(Renderer):
    def __init__(self, graph):
        super().__init__(graph)
        self.sphere_radius = 10
        self.sphere_data = np.array([[0, 0, 1]], 'f')

        self.shader = self.read_shaders("sphere.vert", "sphere.frag")

        self.locations = {}

        for uniform in ('resolution',):
            location = gl.glGetUniformLocation( self.shader, uniform )
            if location in (None,-1):
                print('Warning, no uniform: %s'%( uniform ))
            self.locations[uniform] = location

        for attribute in ('center','radius'):
            location = gl.glGetAttribLocation( self.shader, attribute )
            if location in (None,-1):
                print('Warning, no attribute: %s'%( uniform ))
            self.locations[attribute] = location

        self.convertNodes()

    def convertNodes(self):
        array = []
        for pos in nx.spring_layout(self.graph, dim=3).values():
            array.append([*pos, self.sphere_radius])

        self.sphere_data = np.array(array, 'f')

    def render(self, resolution, tick):
        shaders.glUseProgram(self.shader)
        scaled_data = np.array([np.concatenate(((row[:2]), row[2:3], [1], row[3:])) for row in self.sphere_data], 'f')
        # print(scaled_data)
        # exit(0)
        position_values = len(scaled_data[0]) - 1
        sphere_vbo = vbo.VBO(scaled_data)
        try:
            sphere_vbo.bind()
            try:
                gl.glUniform2f( self.locations["resolution"], *resolution )
                gl.glEnableVertexAttribArray( self.locations["center"] )
                gl.glEnableVertexAttribArray( self.locations["radius"] )
                stride = len(scaled_data[0])*4 # n items per row, and each row is 4 bytes
                gl.glVertexAttribPointer(
                    self.locations["center"],
                    position_values, gl.GL_FLOAT,False, stride, sphere_vbo
                )
                gl.glVertexAttribPointer(
                    self.locations["radius"],
                    1, gl.GL_FLOAT,False, stride, sphere_vbo + position_values * 4
                )
                gl.glEnable(gl.GL_PROGRAM_POINT_SIZE )
                gl.glDrawArrays(gl.GL_POINTS, 0, self.graph.number_of_nodes())
                gl.glDisable(gl.GL_PROGRAM_POINT_SIZE )
            finally:
                sphere_vbo.unbind()
                gl.glDisableVertexAttribArray( self.locations["center"] )
                gl.glDisableVertexAttribArray( self.locations["radius"] )
        finally:
            shaders.glUseProgram(0) # Go back to the legacy pipeline

class Context:
    def __init__(self, graph):
        self.graph = graph
        self.renderers = []
        self.resolution = (512, 512)
        self.tick = 0
        self.aspect = 1
        self.angle = 0
        self.elevation = 0
        self.fov = 55 # Field of view
        self.dim = 5 # Size of world
        self.init_glut()

    def approxCos(self, angle):
        return np.cos(3.1415926/180*angle)

    def approxSin(self, angle):
        return np.sin(3.1415926/180*angle)

    def init_glut(self):
        glut.glutInit() # Creates the opengl context
        glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
        glut.glutCreateWindow('3D Network Visualizer')
        glut.glutReshapeWindow(*self.resolution)
        glut.glutReshapeFunc(self.reshape)
        glut.glutDisplayFunc(self.display)
        glut.glutKeyboardFunc(self.keyboard)
        glut.glutSpecialFunc(self.special)

    def project(self):
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(self.fov, self.aspect, self.dim/4, 4*self.dim)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

    def special(self, key, x, y):
        if key == glut.GLUT_KEY_RIGHT:
            self.angle += 5
        if key == glut.GLUT_KEY_LEFT:
            self.angle -= 5
        if key == glut.GLUT_KEY_UP:
            self.elevation += 5
        if key == glut.GLUT_KEY_DOWN:
            self.elevation -= 5

        self.elevation %= 360
        self.angle %= 360

        self.project()

    def display(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glLoadIdentity();

        Ex = -2*self.dim*self.approxSin(self.angle)*self.approxCos(self.elevation);
        Ey = +2*self.dim*self.approxSin(self.elevation);
        Ez = +2*self.dim*self.approxCos(self.angle)*self.approxCos(self.elevation);
        glu.gluLookAt(Ex,Ey,Ez , 0,0,0 , 0, self.approxCos(self.elevation),0);

        for renderer in self.renderers:
            renderer.render(self.resolution, self.tick)
        glut.glutSwapBuffers()
        glut.glutPostRedisplay();

    def reshape(self, width,height):
        self.resolution = (width, height)
        gl.glViewport(0, 0, width, height)
        self.project()

    def keyboard(self, key, x, y):
        if key == b'\x1b':
            sys.exit()

    def idle(self):
        self.tick = glut.glutGet(glut.GLUT_ELAPSED_TIME);

graph = nx.fast_gnp_random_graph(10, 0.5)
pos = nx.spring_layout(graph)
context = Context(graph)
context.renderers.append(SpringNetworkRenderer(graph))
glut.glutMainLoop()