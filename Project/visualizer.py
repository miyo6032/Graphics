import sys
import OpenGL.GL as gl
import OpenGL.GLUT as glut
from OpenGL.arrays import vbo
from OpenGL.GL import shaders
import numpy as np
import networkx as nx

class Renderer:
    def __init__(self, graph):
        self.graph = graph

    def render(self, resolution, tick):
        pass

# In charge of rendering a spring representation of the network
class SpringNetworkRenderer(Renderer):
    def __init__(self, graph):
        super().__init__(graph)
        self.sphere_radius = 10
        self.sphere_data = np.array([[0, 0, 1]], 'f')
        self.vertex_code = """
            uniform vec2 resolution;
            attribute vec3 center;
            attribute float radius;
            varying vec3 v_center;
            varying float v_radius;
            void main()
            {
                v_radius = radius;
                v_center = center;
                gl_PointSize = 2.0 + ceil(2.0*radius);
                gl_Position = vec4(2.0*center.xy/resolution-1.0, center.z, 1.0);
            }
        """

        self.fragment_code = """
            varying vec3 v_center;
            varying float v_radius;
            void main()
            {
                vec4 global_ambient = vec4(0.3, 0.0, 0.0, 0.0);
                vec2 p = (gl_FragCoord.xy - v_center.xy)/v_radius;
                float z = 1.0 - length(p);
                if (z < 0.0) discard;

                // Specify the actual depth the fragment is supposed to be at  
                // (otherwise it is at v_center by default)
                gl_FragDepth = 0.5*v_center.z + 0.5*(1.0 - z);

                vec3 color = vec3(1.0, 0.0, 0.0);
                vec3 normal = normalize(vec3(p.xy, z));
                vec3 direction = normalize(vec3(1.0, 1.0, 1.0)); // Direction of the light
                float diffuse = max(0.0, dot(direction, normal));
                float specular = pow(diffuse, 24.0);
                gl_FragColor = global_ambient + vec4(max(diffuse*color, specular*vec3(1.0)), 1.0);
            }
        """

        # Compile the shaders
        try:
            vertex_shader = shaders.compileShader(self.vertex_code, gl.GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(self.fragment_code, gl.GL_FRAGMENT_SHADER)
            self.shader = shaders.compileProgram(vertex_shader,fragment_shader)
        except(gl.GLError, RuntimeError) as err:
            print("Shader Compilation Error:")
            print(err)
            exit()

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
        gl.glLoadIdentity()
        shaders.glUseProgram(self.shader)
        scaled_data = np.array([np.concatenate(((row[:2] * 25) + 250, row[2:3] * 3, row[3:])) for row in self.sphere_data], 'f')
        sphere_vbo = vbo.VBO(scaled_data)
        try:
            sphere_vbo.bind()
            try:
                gl.glUniform2f( self.locations["resolution"], *resolution )
                gl.glEnableVertexAttribArray( self.locations["center"] )
                gl.glEnableVertexAttribArray( self.locations["radius"] )
                stride = 4*4 # 4 items per row, and each row is 4 bytes
                gl.glVertexAttribPointer(
                    self.locations["center"],
                    3, gl.GL_FLOAT,False, stride, sphere_vbo
                )
                gl.glVertexAttribPointer(
                    self.locations["radius"],
                    1, gl.GL_FLOAT,False, stride, sphere_vbo+12
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
        self.init_glut()

    def init_glut(self):
        glut.glutInit() # Creates the opengl context
        glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA)
        glut.glutCreateWindow('3D Network Visualizer')
        glut.glutReshapeWindow(*self.resolution)
        glut.glutReshapeFunc(self.reshape)
        glut.glutDisplayFunc(self.display)
        glut.glutKeyboardFunc(self.keyboard)

    def display(self):
        for renderer in self.renderers:
            renderer.render(self.resolution, self.tick)
        glut.glutSwapBuffers()

    def reshape(self, width,height):
        self.resolution = (width, height)
        dim = 2.5
        w2h = width/height if height > 0 else 1
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(-w2h*dim,+w2h*dim, -dim,+dim, -dim,+dim)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

    def keyboard(self, key, x, y):
        if key == b'\x1b':
            sys.exit( )

    def idle(self):
        self.tick = glut.glutGet(glut.GLUT_ELAPSED_TIME);

graph = nx.fast_gnp_random_graph(10, 0.5)
pos = nx.spring_layout(graph)
context = Context(graph)
context.renderers.append(SpringNetworkRenderer(graph))
glut.glutMainLoop()