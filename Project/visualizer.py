import sys
import OpenGL.GL as gl
import OpenGL.GLUT as glut
import OpenGL.GLU as glu
from OpenGL.arrays import vbo
from OpenGL.GL import shaders
import glm
import numpy as np
import networkx as nx

# CREDIT from these tutorials
# https://www.labri.fr/perso/nrougier/python-opengl/#about-this-book
# http://pyopengl.sourceforge.net/context/tutorials/shader_1.html
# https://paroj.github.io/gltut/index.html
# https://schneide.blog/2016/07/15/generating-an-icosphere-in-c/
# https://learnopengl.com/Getting-started/OpenGL

class Icosphere():
    def icosahedron(self):
        X = 0.525731112119133606
        Z = 0.850650808352039932
        N = 0.0

        vertices = [glm.vec3(-X,N,Z), glm.vec3(X,N,Z), glm.vec3(-X,N,-Z), glm.vec3(X,N,-Z),
                    glm.vec3(N,Z,X), glm.vec3(N,Z,-X), glm.vec3(N,-Z,X), glm.vec3(N,-Z,-X),
                    glm.vec3(Z,X,N), glm.vec3(-Z,X, N), glm.vec3(Z,-X,N), glm.vec3(-Z,-X, N)]

        triangles = [  glm.vec3(0,4,1),glm.vec3(0,9,4),glm.vec3(9,5,4),glm.vec3(4,5,8),glm.vec3(4,8,1),
                    glm.vec3(8,10,1),glm.vec3(8,3,10),glm.vec3(5,3,8),glm.vec3(5,2,3),glm.vec3(2,7,3),
                    glm.vec3(7,10,3),glm.vec3(7,6,10),glm.vec3(7,11,6),glm.vec3(11,0,6),glm.vec3(0,1,6),
                    glm.vec3(6,1,10),glm.vec3(9,0,11),glm.vec3(9,11,2),glm.vec3(9,2,5),glm.vec3(7,2,11)]

        return vertices, triangles

    def get_vertex_for_edge(self, lookup, vertices, first_index, second_index):
        if first_index > second_index:
            first_index, second_index = second_index, first_index

        if not (first_index, second_index) in lookup:
            v_0 = vertices[int(first_index)]
            v_1 = vertices[int(second_index)]
            v_new = glm.normalize(v_0 + v_1)
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

            result.append(glm.vec3(triangle[0], mid[0], mid[2]))
            result.append(glm.vec3(triangle[1], mid[1], mid[0]))
            result.append(glm.vec3(triangle[2], mid[2], mid[1]))
            result.append(glm.vec3(mid[0], mid[1], mid[2]))

        return result

    def make_icosphere(self, subdivisions):
        vertices, triangles = self.icosahedron()
        for i in range(subdivisions):
            triangles = self.subdivide(vertices, triangles)
        return vertices, triangles

class Renderer:
    def approxCos(self, angle):
        return np.cos(3.1415926/180*angle)

    def approxSin(self, angle):
        return np.sin(3.1415926/180*angle)

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

    def get_locations(self, shader, uniforms, attributes):
        locations = {}
        for uniform in uniforms:
            location = gl.glGetUniformLocation( shader, uniform )
            if location in (None,-1):
                print('Warning, no uniform: %s'%( uniform ))
            locations[uniform] = location

        for attribute in attributes:
            location = gl.glGetAttribLocation( shader, attribute )
            if location in (None,-1):
                print('Warning, no attribute: %s'%( attribute ))
            locations[attribute] = location

        return locations

    def render(self, tick, offset, camera_pos, light_pos, view_mat, proj_mat):
        pass

# Pass in a flattened list of edges and it will render them all
class RenderLine(Renderer):
    def __init__(self, edges):
        self.shader = self.read_shaders("line.vert", "line.frag")

        uniforms = ['model_mat', 'view_mat', 'proj_mat', 'line_color']
        attributes = ['vertex_position']
        self.locations = self.get_locations(self.shader, uniforms, attributes)
        self.vertex_vbo = vbo.VBO(np.array(edges, 'f'))
        self.num_lines = len(edges) / 2

    def render(self, tick, offset, camera_pos, light_pos, view_mat, proj_mat):
        model_mat = glm.translate(glm.mat4(1), glm.vec3(*offset))

        shaders.glUseProgram(self.shader)
        try:
            self.vertex_vbo.bind()
            try:
                gl.glUniformMatrix4fv( self.locations['model_mat'], 1, gl.GL_FALSE, glm.value_ptr(model_mat))
                gl.glUniformMatrix4fv( self.locations['view_mat'], 1, gl.GL_FALSE, glm.value_ptr(view_mat))
                gl.glUniformMatrix4fv( self.locations['proj_mat'], 1, gl.GL_FALSE, glm.value_ptr(proj_mat))
                gl.glUniform4f( self.locations['line_color'], 1,1,1,1 )
                gl.glEnableVertexAttribArray( self.locations["vertex_position"] )
                gl.glVertexAttribPointer(self.locations["vertex_position"], 3, gl.GL_FLOAT,False, 3 * 4, self.vertex_vbo)
                gl.glDrawArrays(gl.GL_LINES, 0, int(self.num_lines))
            finally:
                self.vertex_vbo.unbind()
                gl.glDisableVertexAttribArray( self.locations["vertex_position"] )
        finally:
            shaders.glUseProgram(0) # Go back to the legacy pipeline

# Renders a single sphere at a time
class RenderSphere(Renderer):
    def __init__(self, radius = 1, subdivisions = 1):
        self.shader = self.read_shaders("test.vert", "test.frag")

        uniforms = ['global_ambient','light_pos','material_ambient', 'camera_pos', 'object_color', 'light_color', 'model_mat', 'view_mat', 'proj_mat']
        attibutes = ['vertex_position', 'vertex_normal']
        self.locations = self.get_locations(self.shader, uniforms, attibutes)

        vertices, triangles = Icosphere().make_icosphere(subdivisions)
        vertex_data = np.array([[f * radius for f in vec] for vec in vertices], 'f')
        self.indices = np.array([f for vec in triangles for f in vec], 'uint32')
        self.vertex_vbo = vbo.VBO(vertex_data)
        self.indices_vbo = vbo.VBO(self.indices)
        self.stride = len(vertex_data[0])*4 # n items per row, and each row is 4 bytes

    def render(self, tick, offset, camera_pos, light_pos, view_mat, proj_mat):
        model_mat = glm.translate(glm.mat4(1), glm.vec3(*offset))
        shaders.glUseProgram(self.shader)
        try:
            self.vertex_vbo.bind()
            try:
                gl.glUniform3f( self.locations['camera_pos'], *camera_pos )
                gl.glUniform3f( self.locations['global_ambient'], .25,.25,.25 )
                gl.glUniform3f( self.locations['material_ambient'], .5,.5,.5 )
                gl.glUniform3f( self.locations['object_color'], .8,.5,.5 )
                gl.glUniform3f( self.locations['light_color'], 1,1,1 )
                gl.glUniform3f( self.locations['light_pos'], *light_pos)
                gl.glUniformMatrix4fv( self.locations['model_mat'], 1, gl.GL_FALSE, glm.value_ptr(model_mat))
                gl.glUniformMatrix4fv( self.locations['view_mat'], 1, gl.GL_FALSE, glm.value_ptr(view_mat))
                gl.glUniformMatrix4fv( self.locations['proj_mat'], 1, gl.GL_FALSE, glm.value_ptr(proj_mat))

                gl.glEnableVertexAttribArray( self.locations["vertex_position"] )
                gl.glEnableVertexAttribArray( self.locations["vertex_normal"] )
                gl.glVertexAttribPointer(
                    self.locations["vertex_position"],
                    3, gl.GL_FLOAT,False, self.stride, self.vertex_vbo
                )
                gl.glVertexAttribPointer(
                    self.locations["vertex_normal"],
                    3, gl.GL_FLOAT,False, self.stride, self.vertex_vbo
                )
                gl.glDrawElements(gl.GL_TRIANGLES, len(self.indices), gl.GL_UNSIGNED_INT, self.indices)
            finally:
                self.vertex_vbo.unbind()
                gl.glDisableVertexAttribArray( self.locations["vertex_position"] )
                gl.glDisableVertexAttribArray( self.locations["vertex_normal"] )
        finally:
            shaders.glUseProgram(0) # Go back to the legacy pipeline

# In charge of rendering a spring representation of the network
class SpringNetworkRenderer(Renderer):
    def __init__(self, graph):
        spring_layout = nx.spring_layout(graph, dim=3, scale=3)
        self.nodes = [pos for pos in spring_layout.values()]
        self.edges = [spring_layout[node] for edge in graph.edges() for node in edge]

        self.sphere_renderer = RenderSphere(radius=0.1, subdivisions=2)
        self.line_renderer = RenderLine(self.edges)

    def render(self, tick, offset, camera_pos, light_pos, view_mat, proj_mat):
        degree = np.round((tick * 0.1)) % 360;
        light_pos = (self.approxCos(degree) * 2, self.approxSin(degree) * 2, 1)

        for pos in self.nodes:
            self.sphere_renderer.render(tick, pos, camera_pos, light_pos, view_mat, proj_mat)

        self.line_renderer.render(tick, (0, 0, 0), camera_pos, light_pos, view_mat, proj_mat)

        self.sphere_renderer.render(tick, light_pos, camera_pos, light_pos, view_mat, proj_mat)

class Context:
    def __init__(self, graph):
        self.graph = graph
        self.renderers = []
        self.tick = 0
        self.aspect = 1
        self.angle = 0
        self.elevation = 0
        self.fov = 55 # Field of view
        self.dim = 5 # Size of world
        self.init_glut()
        self.setup_camera()

    def setup_camera(self):
        Ex = -2*self.dim*self.approxSin(self.angle)*self.approxCos(self.elevation);
        Ey = +2*self.dim*self.approxSin(self.elevation);
        Ez = +2*self.dim*self.approxCos(self.angle)*self.approxCos(self.elevation);
        self.camera_pos = glm.vec3(Ex, Ey, Ez)
        camera_target = glm.vec3(0)

        self.view_mat = glm.lookAt(self.camera_pos, camera_target, glm.vec3(0, self.approxCos(self.elevation), 0))

    def approxCos(self, angle):
        return np.cos(3.1415926/180*angle)

    def approxSin(self, angle):
        return np.sin(3.1415926/180*angle)

    def init_glut(self):
        glut.glutInit() # Creates the opengl context
        glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
        glut.glutCreateWindow('3D Network Visualizer')
        glut.glutReshapeWindow(512, 512)
        glut.glutReshapeFunc(self.reshape)
        glut.glutDisplayFunc(self.display)
        glut.glutKeyboardFunc(self.keyboard)
        glut.glutSpecialFunc(self.special)
        glut.glutIdleFunc(self.idle)

    def project(self):
        self.proj_mat = glm.perspective(glm.radians(self.fov), self.aspect, self.dim/4, 4*self.dim);
        self.setup_camera()

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

        for renderer in self.renderers:
            renderer.render(self.tick, (0, 0, 0), self.camera_pos, None, self.view_mat, self.proj_mat)

        err = gl.glGetError()
        if err != gl.GL_NO_ERROR:
            print('GLERROR: ', glu.gluErrorString( err ))
            sys.exit()

        glut.glutSwapBuffers()
        glut.glutPostRedisplay()

    def reshape(self, width,height):
        gl.glViewport(0, 0, width, height)
        self.aspect = width / height if height > 0 else 1
        self.project()

    def keyboard(self, key, x, y):
        if key == b'\x1b':
            sys.exit()

    def idle(self):
        self.tick = glut.glutGet(glut.GLUT_ELAPSED_TIME);

graph = nx.fast_gnp_random_graph(1000, 3 / 100)
context = Context(graph)
context.renderers.append(SpringNetworkRenderer(graph))
glut.glutMainLoop()