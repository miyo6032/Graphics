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
            attribute vec4 center;
            attribute float radius;
            varying vec4 v_center;
            varying float v_radius;
            void main()
            {
                v_radius = radius;
                v_center = center;
                gl_PointSize = 2.0 + ceil(2.0*radius);
                //gl_Position = gl_ModelViewProjectionMatrix * vec4(2.0*center.xy/resolution-1.0, center.z, 1.0);
                gl_Position = center * gl_ModelViewProjectionMatrix;
            }
        """

        self.fragment_code = """
            varying vec4 v_center;
            varying float v_radius;
            void main()
            {
                vec4 global_ambient = vec4(0.3, 0.0, 0.0, 0.0);
                vec2 p = (gl_FragCoord.xy - v_center.xy)/v_radius;
                float z = 1.0 - length(p);
                //if (z < 0.0) discard;

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
                stride = len(scaled_data[0])*4 # 5 items per row, and each row is 4 bytes
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

class FogRenderer(Renderer):
    def __init__(self, graph):
        super().__init__(graph)
        vertex_code = """
        uniform float end_fog;
        uniform vec4 fog_color;
        void main()
        {
            float fog; // amount of fog to apply
            float fog_coord; // distance for fog calculation...
            gl_Position = ftransform();
            fog_coord = abs(gl_Position.z);
            fog_coord = clamp( fog_coord, 0.0, end_fog);
            fog = (end_fog - fog_coord)/end_fog;
            fog = clamp( fog, 0.0, 1.0);
            gl_FrontColor = mix(fog_color, gl_Color, fog);
        }
        """

        fragment_code = """
        void main()
        {
            gl_FragColor = gl_Color;
        }
        """

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
        # data = np.array([np.concatenate((v[:3] * 0.25, v[3:])) for v in data], 'f')
        self.vbo = vbo.VBO(data) # Turn it into a format that opengl can use

        try:
            vertex_shader = shaders.compileShader(vertex_code, gl.GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fragment_code, gl.GL_FRAGMENT_SHADER)
            self.shader = shaders.compileProgram(vertex_shader,fragment_shader)
        except(gl.GLError, RuntimeError) as err:
            print("Shader Compilation Error:")
            print(err)
            exit()

        self.locations = {
            'end_fog': gl.glGetUniformLocation( self.shader, 'end_fog' ),
            'fog_color': gl.glGetUniformLocation( self.shader, 'fog_color' ),
        }

    def render(self, resolution, tick):
        shaders.glUseProgram(self.shader)
        gl.glUniform1f(self.locations['end_fog'],10)
        gl.glUniform4f(self.locations['fog_color'],0,0,0,1)
        try:
            self.vbo.bind()
            try:
                gl.glClear(gl.GL_COLOR_BUFFER_BIT)
                gl.glEnableClientState(gl.GL_VERTEX_ARRAY);
                gl.glEnableClientState(gl.GL_COLOR_ARRAY);
                gl.glVertexPointer(3, gl.GL_FLOAT, 24, self.vbo)
                gl.glColorPointer(3, gl.GL_FLOAT, 24, self.vbo + 12)
                gl.glDrawArrays(gl.GL_TRIANGLES, 0, 9)
            finally:
                self.vbo.unbind()
                gl.glDisableClientState(gl.GL_VERTEX_ARRAY);
                gl.glDisableClientState(gl.GL_COLOR_ARRAY);
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
            sys.exit( )

    def idle(self):
        self.tick = glut.glutGet(glut.GLUT_ELAPSED_TIME);

graph = nx.fast_gnp_random_graph(10, 0.5)
pos = nx.spring_layout(graph)
context = Context(graph)
context.renderers.append(FogRenderer(graph))
glut.glutMainLoop()