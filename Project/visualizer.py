import sys
import OpenGL.GL as gl
import OpenGL.GLUT as glut
import OpenGL.GLU as glu
from OpenGL.arrays import vbo
from OpenGL.GL import shaders
import glm
import numpy as np
import networkx as nx
import highlighters as hl

# CREDIT from these tutorials
# https://www.labri.fr/perso/nrougier/python-opengl/#about-this-book
# http://pyopengl.sourceforge.net/context/tutorials/shader_1.html
# https://paroj.github.io/gltut/index.html
# https://schneide.blog/2016/07/15/generating-an-icosphere-in-c/
# https://learnopengl.com/Getting-started/OpenGL
# https://en.wikibooks.org/wiki/OpenGL_Programming/Glescraft_4

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
    def __init__(self, edges, colors):
        self.num_points = len(edges)
        self.shader = self.read_shaders("line.vert", "line.frag")

        uniforms = ['model_mat', 'view_mat', 'proj_mat']
        attributes = ['vertex_position', 'line_color']
        self.locations = self.get_locations(self.shader, uniforms, attributes)
        the_vbo = [[*edges, *colors] for edges, colors in zip(edges, colors)]
        self.vertex_vbo = vbo.VBO(np.array(the_vbo, 'f'))

    def render(self, tick, offset, camera_pos, light_pos, view_mat, proj_mat):
        model_mat = glm.translate(glm.mat4(1), glm.vec3(*offset))

        shaders.glUseProgram(self.shader)
        try:
            self.vertex_vbo.bind()
            try:
                gl.glUniformMatrix4fv( self.locations['model_mat'], 1, gl.GL_FALSE, glm.value_ptr(model_mat))
                gl.glUniformMatrix4fv( self.locations['view_mat'], 1, gl.GL_FALSE, glm.value_ptr(view_mat))
                gl.glUniformMatrix4fv( self.locations['proj_mat'], 1, gl.GL_FALSE, glm.value_ptr(proj_mat))
                gl.glEnableVertexAttribArray( self.locations["vertex_position"] )
                gl.glEnableVertexAttribArray( self.locations['line_color'] )
                gl.glVertexAttribPointer(self.locations["vertex_position"], 3, gl.GL_FLOAT,False, 7 * 4, self.vertex_vbo)
                gl.glVertexAttribPointer(self.locations["line_color"], 4, gl.GL_FLOAT,False, 7 * 4, self.vertex_vbo + 3 * 4)
                gl.glDrawArrays(gl.GL_LINES, 0, int(self.num_points))
            finally:
                self.vertex_vbo.unbind()
                gl.glDisableVertexAttribArray( self.locations["line_color"] )
                gl.glDisableVertexAttribArray( self.locations["vertex_position"] )
        finally:
            shaders.glUseProgram(0) # Go back to the legacy pipeline

# Renders n spheres at given positions
class RenderSpheres(Renderer):
    def __init__(self, positions, colors, light_color, radius = 1, subdivisions = 1):
        self.positions = positions
        self.colors = colors
        self.light_color = light_color

        self.shader = self.read_shaders("test.vert", "test.frag")
        uniforms = [
        'material.ambient', 'material.diffuse', 'material.specular', 'material.shininess',
        'light.ambient', 'light.diffuse', 'light.specular', 'light_pos',
        'camera_pos', 'model_mat', 'view_mat', 'proj_mat']
        attibutes = ['vertex_position', 'vertex_normal']
        self.locations = self.get_locations(self.shader, uniforms, attibutes)

        vertices, triangles = Icosphere().make_icosphere(subdivisions)
        self.vertex_data = np.array([[f * radius for f in vec] for vec in vertices], 'f')
        self.indices = np.array([f for vec in triangles for f in vec], 'uint32')
        self.stride = len(self.vertex_data[0])*4 # n items per row, and each row is 4 bytes

    def render(self, tick, offset, camera_pos, light_pos, view_mat, proj_mat):
        shaders.glUseProgram(self.shader)
        try:
            gl.glUniform3f( self.locations['camera_pos'], *camera_pos )
            gl.glUniform3f( self.locations['light_pos'], *light_pos)
            gl.glUniform3f( self.locations['light.ambient'], *self.light_color.ambient )
            gl.glUniform3f( self.locations['light.diffuse'], *self.light_color.diffuse )
            gl.glUniform3f( self.locations['light.specular'], *self.light_color.specular )
            gl.glUniformMatrix4fv( self.locations['view_mat'], 1, gl.GL_FALSE, glm.value_ptr(view_mat))
            gl.glUniformMatrix4fv( self.locations['proj_mat'], 1, gl.GL_FALSE, glm.value_ptr(proj_mat))

            gl.glEnableVertexAttribArray( self.locations["vertex_position"] )
            gl.glEnableVertexAttribArray( self.locations["vertex_normal"] )
            gl.glVertexAttribPointer(
                self.locations["vertex_position"],
                3, gl.GL_FLOAT,False, self.stride, self.vertex_data
            )
            gl.glVertexAttribPointer(
                self.locations["vertex_normal"],
                3, gl.GL_FLOAT,False, self.stride, self.vertex_data
            )
            for position, material in zip(self.positions, self.colors):
                gl.glUniform3f( self.locations['material.ambient'], *material.ambient )
                gl.glUniform3f( self.locations['material.diffuse'], *material.diffuse)
                gl.glUniform3f( self.locations['material.specular'], *material.specular )
                gl.glUniform1f( self.locations['material.shininess'], material.shininess )

                model_mat = glm.translate(glm.mat4(1), glm.vec3(*offset) + glm.vec3(*position))
                gl.glUniformMatrix4fv( self.locations['model_mat'], 1, gl.GL_FALSE, glm.value_ptr(model_mat))
                
                gl.glDrawElements(gl.GL_TRIANGLES, len(self.indices), gl.GL_UNSIGNED_INT, self.indices)
        finally:
            gl.glDisableVertexAttribArray( self.locations["vertex_position"] )
            gl.glDisableVertexAttribArray( self.locations["vertex_normal"] )
            shaders.glUseProgram(0) # Go back to the legacy pipeline

# In charge of rendering a spring representation of the network
class SpringNetworkRenderer(Renderer):
    def __init__(self, graph):
        spring_layout = nx.spring_layout(graph, dim=3, scale=9)
        self.nodes = [pos for node, pos in spring_layout.items()]
        self.edges = [spring_layout[node] for edge in graph.edges() for node in edge]
        light_material = hl.Material((1, 1, 1), (1, 1, 1), (1, 1, 1), 1)
        highlighter = hl.PartitionHighlighter(graph)

        self.light_renderer = RenderSpheres([(0, 0, 0)], [light_material], light_material, radius=0.05, subdivisions=2)
        self.nodes_renderer = RenderSpheres(self.nodes, highlighter.get_node_colors(), highlighter.get_light_color(), radius=0.05, subdivisions=2)
        self.line_renderer = RenderLine(self.edges, highlighter.get_edge_colors())

        self.screen_shaders = self.read_shaders("screen.vert", "screen.frag")

        self.quad_vbo = vbo.VBO(np.array([
        [-1,  1,  0, 1],
        [-1, -1,  0, 0],
        [1, -1,  1, 0],

        [-1,  1,  0, 1],
        [ 1, -1,  1, 0],
        [ 1,  1,  1, 1]
        ], 'f'))

        # Setup VAO for screen quad

        uniforms = ['texture']
        attributes = ['quad_pos', 'tex_coord']
        self.locations = self.get_locations(self.screen_shaders, uniforms, attributes)

        # Setup frame buffer business for post processing
        self.frame_buffer = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.frame_buffer)

        self.texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, 1024, 1024, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR);
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.texture, 0);  

        rbo = gl.glGenRenderbuffers(1);
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, rbo); 
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH24_STENCIL8, 1024, 1024);  
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0);
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_STENCIL_ATTACHMENT, gl.GL_RENDERBUFFER, rbo);

        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) == gl.GL_FRAMEBUFFER_COMPLETE:
            print("Victory??!!")
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        # gl.glDeleteFramebuffers(1, [frame_buffer])

    def render(self, tick, offset, camera_pos, light_pos, view_mat, proj_mat):
        degree = np.round((tick * 0.1)) % 360;
        light_pos = (self.approxCos(degree) * 2, self.approxSin(degree) * 2, 1)

        # First pass
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.frame_buffer)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glClearColor(0.1, 0.1, 0.1, 1.0);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT);

        self.nodes_renderer.render(tick, (0, 0, 0), camera_pos, light_pos, view_mat, proj_mat)

        gl.glEnable(gl.GL_BLEND);
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA);  
        self.line_renderer.render(tick, (0, 0, 0), camera_pos, light_pos, view_mat, proj_mat)
        gl.glDisable(gl.GL_BLEND);

        self.light_renderer.render(tick, light_pos, camera_pos, light_pos, view_mat, proj_mat)

        # Second pass
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glDisable(gl.GL_DEPTH_TEST);
        gl.glClearColor(1.0, 1.0, 1.0, 1.0);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT);

        shaders.glUseProgram(self.screen_shaders)
        self.quad_vbo.bind()
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glEnableVertexAttribArray( self.locations["quad_pos"] )
        gl.glEnableVertexAttribArray( self.locations["tex_coord"] )
        stride = 4*4 # 4 items per row
        gl.glVertexAttribPointer(self.locations["quad_pos"],2, gl.GL_FLOAT,False, stride, self.quad_vbo)
        gl.glVertexAttribPointer(self.locations["tex_coord"],2, gl.GL_FLOAT,False, stride, self.quad_vbo + (2 * 4))
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
        self.quad_vbo.unbind()
        gl.glDisableVertexAttribArray( self.locations["quad_pos"] )
        gl.glDisableVertexAttribArray( self.locations["tex_coord"] )

class Context:
    def __init__(self, graph):
        self.graph = graph
        self.renderers = []
        self.tick = 0 # World ticks in milleseconds
        self.aspect = 1
        self.angle = 0
        self.elevation = 0
        self.fov = 55 # Field of view
        self.dim = 5 # Size of world
        self.view_mode = 1 # 0 for overhead and 1 for first person
        self.camera_pos = glm.vec3(0, 0, 3)
        self.camera_front = glm.vec3(0, 0, -1)
        self.camera_up = glm.vec3(0, 1, 0)
        self.prev_frame_time = 0
        self.delta_time = 0
        self.init_glut()
        self.setup_camera()
        self.warp = False; # To keep the motion function from being called after we warp the mouse pointer

    def setup_camera(self):
        if self.view_mode == 0:
            Ex = -2*self.dim*self.approxSin(self.angle)*self.approxCos(self.elevation);
            Ey = +2*self.dim*self.approxSin(self.elevation);
            Ez = +2*self.dim*self.approxCos(self.angle)*self.approxCos(self.elevation);
            self.camera_pos = glm.vec3(Ex, Ey, Ez)
            camera_target = glm.vec3(0)

            self.view_mat = glm.lookAt(self.camera_pos, camera_target, glm.vec3(0, self.approxCos(self.elevation), 0))
        elif self.view_mode == 1:
            self.camera_front.x = np.cos(glm.radians(self.angle)) * np.cos(glm.radians(self.elevation))
            self.camera_front.y = np.sin(glm.radians(self.elevation))
            self.camera_front.z = np.sin(glm.radians(self.angle)) * np.cos(glm.radians(self.elevation))
            self.camera_front = glm.normalize(self.camera_front)
            self.view_mat = glm.lookAt(self.camera_pos, self.camera_pos + self.camera_front, self.camera_up)

    def approxCos(self, angle):
        return np.cos(3.1415926/180*angle)

    def approxSin(self, angle):
        return np.sin(3.1415926/180*angle)

    def init_glut(self):
        glut.glutInit() # Creates the opengl context
        glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
        glut.glutCreateWindow('3D Network Visualizer')
        glut.glutReshapeWindow(1024, 1024)
        glut.glutReshapeFunc(self.reshape)
        glut.glutDisplayFunc(self.display)
        glut.glutKeyboardFunc(self.keyboard)
        glut.glutSpecialFunc(self.special)
        glut.glutIdleFunc(self.idle)
        glut.glutMotionFunc(self.mouse_motion)
        glut.glutPassiveMotionFunc(self.mouse_motion)
        glut.glutMouseFunc(self.mouse)
        if self.view_mode == 1:
            glut.glutSetCursor(glut.GLUT_CURSOR_NONE)

    def mouse(self, button, state, x, y):
        if self.view_mode != 1 or state == glut.GLUT_UP:
            return

        if button == 3:
            self.fov = np.clip(self.fov + 1, 30, 90)
        elif button == 4:
            self.fov = np.clip(self.fov - 1, 30, 90)

        self.project()

    def mouse_motion(self, x, y):
        if self.view_mode != 1:
            return

        if not self.warp:
            x_center = glut.glutGet(glut.GLUT_WINDOW_WIDTH) / 2
            y_center = glut.glutGet(glut.GLUT_WINDOW_HEIGHT) / 2

            dx = x - x_center
            dy = y - y_center

            sensitivity = 0.05
            dx *= sensitivity
            dy *= sensitivity

            self.angle = self.angle + dx
            self.elevation = min(max(self.elevation - dy, -89.9), 89.9)

            self.warp = True
            glut.glutWarpPointer(int(x_center), int(y_center))
        else:
            self.warp = False

        self.project()

    def project(self):
        self.proj_mat = glm.perspective(glm.radians(self.fov), self.aspect, self.dim/16, 4*self.dim);
        self.setup_camera()

    def special(self, key, x, y):
        if self.view_mode == 0:
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

        elif self.view_mode == 1:
            camera_speed = 25 * 0.001 * self.delta_time
            if key == glut.GLUT_KEY_UP:
                self.camera_pos += camera_speed * self.camera_front
            if key == glut.GLUT_KEY_DOWN:
                self.camera_pos -= camera_speed * self.camera_front
            if key == glut.GLUT_KEY_RIGHT:
                self.camera_pos += glm.normalize(glm.cross(self.camera_front, self.camera_up)) * camera_speed
            if key == glut.GLUT_KEY_LEFT:
                self.camera_pos -= glm.normalize(glm.cross(self.camera_front, self.camera_up)) * camera_speed

        self.project()

    def display(self):
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
        self.delta_time = self.tick - self.prev_frame_time
        self.prev_frame_time = self.tick

# graph = nx.fast_gnp_random_graph(100, 3 / 100)

fname1 = 'data/karate.gml'
Go     = nx.read_gml('./' + fname1, label='id')
G      = nx.convert_node_labels_to_integers(Go) # map node names to integers (0:n-1) [because indexing]

context = Context(G)
context.renderers.append(SpringNetworkRenderer(G))
glut.glutMainLoop()