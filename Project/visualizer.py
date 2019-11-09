import sys
import OpenGL.GL as gl
import OpenGL.GLUT as glut
import OpenGL.GLU as glu
from OpenGL.arrays import vbo
from OpenGL.GL import shaders
from glm import *
import numpy as np
import networkx as nx
import OpenGLContext.scenegraph.basenodes as basenodes

# CREDIT
# https://www.labri.fr/perso/nrougier/python-opengl/#about-this-book
# http://pyopengl.sourceforge.net/context/tutorials/shader_1.html
# https://paroj.github.io/gltut/index.html
# https://schneide.blog/2016/07/15/generating-an-icosphere-in-c/

class Icosphere():
    def icosahedron(self):
        X = 0.525731112119133606
        Z = 0.850650808352039932
        N = 0.0

        vertices = [vec3(-X,N,Z), vec3(X,N,Z), vec3(-X,N,-Z), vec3(X,N,-Z),
                    vec3(N,Z,X), vec3(N,Z,-X), vec3(N,-Z,X), vec3(N,-Z,-X),
                    vec3(Z,X,N), vec3(-Z,X, N), vec3(Z,-X,N), vec3(-Z,-X, N)]

        triangles = [  vec3(0,4,1),vec3(0,9,4),vec3(9,5,4),vec3(4,5,8),vec3(4,8,1),
                    vec3(8,10,1),vec3(8,3,10),vec3(5,3,8),vec3(5,2,3),vec3(2,7,3),
                    vec3(7,10,3),vec3(7,6,10),vec3(7,11,6),vec3(11,0,6),vec3(0,1,6),
                    vec3(6,1,10),vec3(9,0,11),vec3(9,11,2),vec3(9,2,5),vec3(7,2,11)]

        return vertices, triangles

    def get_vertex_for_edge(self, lookup, vertices, first_index, second_index):
        if first_index > second_index:
            first_index, second_index = second_index, first_index

        if not (first_index, second_index) in lookup:
            v_0 = vertices[int(first_index)]
            v_1 = vertices[int(second_index)]
            v_new = normalize(v_0 + v_1)
            vertices.append(v_new)
            lookup[(first_index, second_index)] = len(vertices) - 1

        return lookup[(first_index, second_index)]

    def subdivide(self, vertices, triangles):
        # Stores the index that vertices between edges are
        lookup = {}
        result = []

        for triangle in triangles:
            mid = []
            for i in range(3):
                mid.append(self.get_vertex_for_edge(lookup, vertices, triangle[i], triangle[(i + 1) % 3]))

            result.append(vec3(triangle[0], mid[0], mid[2]))
            result.append(vec3(triangle[1], mid[1], mid[0]))
            result.append(vec3(triangle[2], mid[2], mid[1]))
            result.append(vec3(mid[0], mid[1], mid[2]))

        return result

    def make_icosphere(self, subdivisions):
        vertices, triangles = self.icosahedron()
        for i in range(subdivisions):
            triangles = self.subdivide(vertices, triangles)
        return vertices, triangles

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

class RenderSphere(Renderer):
    def __init__(self, graph):
        super().__init__(graph)
        self.shader = self.read_shaders("test.vert", "test.frag")

        self.locations = {}

        for uniform in (
            'Global_ambient',
            'Light_ambient','Light_diffuse','Light_location',
            'Light_specular',
            'Material_ambient','Material_diffuse',
            'Material_shininess','Material_specular', 'offset'):
            location = gl.glGetUniformLocation( self.shader, uniform )
            if location in (None,-1):
                print('Warning, no uniform: %s'%( uniform ))
            self.locations[uniform] = location

        for attribute in ('Vertex_position', 'Vertex_normal'):
            location = gl.glGetAttribLocation( self.shader, attribute )
            if location in (None,-1):
                print('Warning, no attribute: %s'%( attribute ))
            self.locations[attribute] = location

        vertices, triangles = Icosphere().make_icosphere(1)
        vertex_data = np.array([[f for f in vec] for vec in vertices], 'f')
        vertex_data *= 0.1
        self.indices = np.array([f for vec in triangles for f in vec], 'uint32')
        self.vertex_vbo = vbo.VBO(vertex_data)
        self.indices_vbo = vbo.VBO(self.indices)
        self.stride = len(vertex_data[0])*4 # n items per row, and each row is 4 bytes

    def render(self, resolution, tick, offset=(0,0,0)):
        shaders.glUseProgram(self.shader)
        try:
            self.vertex_vbo.bind()
            try:
                gl.glUniform4f( self.locations['Global_ambient'], .05,.05,.05,.1 )
                gl.glUniform4f( self.locations['Light_ambient'], .1,.1,.1, 1.0 )
                gl.glUniform4f( self.locations['Light_diffuse'], .25,.25,.25,1 )
                gl.glUniform4f( self.locations['Light_specular'], 0.0,1.0,0,1 )
                gl.glUniform3f( self.locations['Light_location'], -2,0,0 )
                gl.glUniform4f( self.locations['Material_ambient'], .1,.1,.1, 1.0 )
                gl.glUniform4f( self.locations['Material_diffuse'], .15,.15,.15, 1 )
                gl.glUniform4f( self.locations['Material_specular'], 1.0,1.0,1.0, 1.0 )
                gl.glUniform1f( self.locations['Material_shininess'], .95)
                gl.glUniform3f( self.locations['offset'], *offset )

                gl.glEnableVertexAttribArray( self.locations["Vertex_position"] )
                gl.glEnableVertexAttribArray( self.locations["Vertex_normal"] )
                gl.glVertexAttribPointer(
                    self.locations["Vertex_position"],
                    3, gl.GL_FLOAT,False, self.stride, self.vertex_vbo
                )
                gl.glVertexAttribPointer(
                    self.locations["Vertex_normal"],
                    3, gl.GL_FLOAT,False, self.stride, self.vertex_vbo
                )
                gl.glDrawElements(gl.GL_TRIANGLES, len(self.indices), gl.GL_UNSIGNED_INT, self.indices)
            finally:
                self.vertex_vbo.unbind()
                gl.glDisableVertexAttribArray( self.locations["Vertex_position"] )
                gl.glDisableVertexAttribArray( self.locations["Vertex_normal"] )
        finally:
            shaders.glUseProgram(0) # Go back to the legacy pipeline

# In charge of rendering a spring representation of the network
class SpringNetworkRenderer(Renderer):
    def __init__(self, graph):
        super().__init__(graph)
        self.sphere_radius = 10
        self.sphere_data = np.array([[0, 0, 1]], 'f')

        self.shader = self.read_shaders("sphere.vert", "sphere.frag")

        self.locations = {}

        # for uniform in ('resolution',):
        #     location = gl.glGetUniformLocation( self.shader, uniform )
        #     if location in (None,-1):
        #         print('Warning, no uniform: %s'%( uniform ))
        #     self.locations[uniform] = location

        # for attribute in ('center','radius'):
        #     location = gl.glGetAttribLocation( self.shader, attribute )
        #     if location in (None,-1):
        #         print('Warning, no attribute: %s'%( attribute ))
        #     self.locations[attribute] = location

        self.convertNodes()

        self.sphere_renderer = RenderSphere(graph)

    def convertNodes(self):
        array = []
        for pos in nx.spring_layout(self.graph, dim=3).values():
            array.append([*pos, self.sphere_radius])

        self.sphere_data = np.array(array, 'f')

    def render(self, resolution, tick):
        for pos in self.sphere_data:
            self.sphere_renderer.render(resolution, tick, pos[:3])
        # shaders.glUseProgram(self.shader)
        # scaled_data = np.array([np.concatenate(((row[:2]), row[2:3], [1], row[3:])) for row in self.sphere_data], 'f')
        # position_values = len(scaled_data[0]) - 1
        # sphere_vbo = vbo.VBO(scaled_data)
        # try:
        #     sphere_vbo.bind()
        #     try:
        #         gl.glUniform2f( self.locations["resolution"], *resolution )
        #         gl.glEnableVertexAttribArray( self.locations["center"] )
        #         gl.glEnableVertexAttribArray( self.locations["radius"] )
        #         stride = len(scaled_data[0])*4 # n items per row, and each row is 4 bytes
        #         gl.glVertexAttribPointer(
        #             self.locations["center"],
        #             position_values, gl.GL_FLOAT,False, stride, sphere_vbo
        #         )
        #         gl.glVertexAttribPointer(
        #             self.locations["radius"],
        #             1, gl.GL_FLOAT,False, stride, sphere_vbo + position_values * 4
        #         )
        #         gl.glEnable(gl.GL_PROGRAM_POINT_SIZE )
        #         gl.glDrawArrays(gl.GL_POINTS, 0, self.graph.number_of_nodes())
        #         gl.glDisable(gl.GL_PROGRAM_POINT_SIZE )
        #     finally:
        #         sphere_vbo.unbind()
        #         gl.glDisableVertexAttribArray( self.locations["center"] )
        #         gl.glDisableVertexAttribArray( self.locations["radius"] )
        # finally:
        #     shaders.glUseProgram(0) # Go back to the legacy pipeline

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

        err = gl.glGetError()
        if err != gl.GL_NO_ERROR:
            print('GLERROR: ', glu.gluErrorString( err ))
            sys.exit()

        glut.glutSwapBuffers()
        glut.glutPostRedisplay()

    def reshape(self, width,height):
        self.resolution = (width, height)
        gl.glViewport(0, 0, width, height)
        self.aspect = width / height if height > 0 else 1
        self.project()

    def keyboard(self, key, x, y):
        if key == b'\x1b':
            sys.exit()

    def idle(self):
        self.tick = glut.glutGet(glut.GLUT_ELAPSED_TIME);

graph = nx.fast_gnp_random_graph(100, 0.5)
pos = nx.spring_layout(graph)
context = Context(graph)
context.renderers.append(SpringNetworkRenderer(graph))
glut.glutMainLoop()