import sys
import OpenGL.GL as gl
import OpenGL.GLUT as glut
import OpenGL.GLU as glu
from OpenGL.arrays import vbo
from OpenGL.GL import shaders
import glm
import numpy as np
import highlighters as hl
from pathlib import Path

# CREDIT from these tutorials
# https://www.labri.fr/perso/nrougier/python-opengl/#about-this-book
# http://pyopengl.sourceforge.net/context/tutorials/shader_1.html
# https://paroj.github.io/gltut/index.html
# https://schneide.blog/2016/07/15/generating-an-icosphere-in-c/
# https://learnopengl.com/Getting-started/OpenGL
# https://en.wikibooks.org/wiki/OpenGL_Programming/Glescraft_4
# https://en.wikibooks.org/wiki/OpenGL_Programming/Object_selection

# From a previous homework: generates a sphere from an icosahedron
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

# Base class that provides some functions for rendering
class Renderer:
    def approxCos(self, angle):
        return np.cos(3.1415926/180*angle)

    def approxSin(self, angle):
        return np.sin(3.1415926/180*angle)

    # Loads the shader from files attempts to compile them, and returns the shader program
    def read_shaders(self, vertex_file, fragment_file, geometry=None):
        with (Path(__file__).parent / "./shaders/" / vertex_file).open()  as file:
            vertex_code = file.read()
        with (Path(__file__).parent / "./shaders/" / fragment_file).open()  as file:
            fragment_code = file.read()
        if geometry:
            with (Path(__file__).parent / "./shaders/" / geometry).open() as file:
                geometry_code = file.read()

        # Compile the shaders
        try:
            vertex_shader = shaders.compileShader(vertex_code, gl.GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fragment_code, gl.GL_FRAGMENT_SHADER)
            if geometry:
                geometry_shader = shaders.compileShader(geometry_code, gl.GL_GEOMETRY_SHADER)
                shader = shaders.compileProgram(vertex_shader,fragment_shader,geometry_shader)
            else:
                shader = shaders.compileProgram(vertex_shader,fragment_shader)
            return shader
        except(gl.GLError, RuntimeError) as err:
            print("Shader Compilation Error:")
            print(str(err).replace('\\n', '\n'))
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
    
    # Called by glut in the glut display function to render opengl
    def render(self, tick, offset, light_pos, context):
        pass

    # Called whenever the highlighter parameters change
    def set_highlighter(self, highlighter):
        pass

# Pass in a flattened list of edges and it will render them all
# The highlighter determines what colors ands styles the lines have
class RenderLine(Renderer):
    def __init__(self):
        self.shader = self.read_shaders("network_line.vert", "bloom_line.frag", "striped_line.geom")

        uniforms = ['time', 'model_mat', 'view_mat', 'proj_mat']
        attributes = ['vertex_position', 'line_color', 'edge_strength']
        self.locations = self.get_locations(self.shader, uniforms, attributes)

    def set_highlighter(self, highlighter):
        self.edges = [highlighter.get_layout()[node] for edge in highlighter.get_edges() for node in edge]
        self.num_points = len(self.edges)

        edge_strengths = highlighter.get_edge_strengths()
        edge_strengths = [edge_strengths[int(np.floor(i / 2))] for i in range(len(edge_strengths * 2))]
        the_vbo = [[*edges, *colors, edge_strength] for edges, colors, edge_strength in zip(self.edges, highlighter.get_edge_colors(), edge_strengths)]
        self.vertex_vbo = vbo.VBO(np.array(the_vbo, 'f'))

    def render(self, tick, offset, light_pos, context):
        model_mat = glm.translate(glm.mat4(1), glm.vec3(*offset))

        shaders.glUseProgram(self.shader)
        try:
            self.vertex_vbo.bind()
            try:
                gl.glUniform1f(self.locations['time'], ((tick % 1000) * 0.001))
                gl.glUniformMatrix4fv( self.locations['model_mat'], 1, gl.GL_FALSE, glm.value_ptr(model_mat))
                gl.glUniformMatrix4fv( self.locations['view_mat'], 1, gl.GL_FALSE, glm.value_ptr(context.view_mat))
                gl.glUniformMatrix4fv( self.locations['proj_mat'], 1, gl.GL_FALSE, glm.value_ptr(context.proj_mat))
                gl.glEnableVertexAttribArray( self.locations["vertex_position"] )
                gl.glEnableVertexAttribArray( self.locations['line_color'] )
                gl.glEnableVertexAttribArray( self.locations['edge_strength'] )
                gl.glVertexAttribPointer(self.locations["vertex_position"], 3, gl.GL_FLOAT,False, 8 * 4, self.vertex_vbo)
                gl.glVertexAttribPointer(self.locations["line_color"], 4, gl.GL_FLOAT,False, 8 * 4, self.vertex_vbo + 3 * 4)
                gl.glVertexAttribPointer(self.locations["edge_strength"], 1, gl.GL_FLOAT,False, 8 * 4, self.vertex_vbo + 7 * 4)
                gl.glDrawArrays(gl.GL_LINES, 0, int(self.num_points))
            finally:
                self.vertex_vbo.unbind()
                gl.glDisableVertexAttribArray( self.locations["edge_strength"] )
                gl.glDisableVertexAttribArray( self.locations["line_color"] )
                gl.glDisableVertexAttribArray( self.locations["vertex_position"] )
        finally:
            shaders.glUseProgram(0) # Go back to the legacy pipeline

# Renders n spheres at given positions
class RenderSpheres(Renderer):
    def __init__(self, subdivisions = 1):
        self.shader = self.read_shaders("spheres.vert", "spheres.frag")
        uniforms = [
        'material.ambient', 'material.diffuse', 'material.specular', 'material.shininess',
        'light.ambient', 'light.diffuse', 'light.specular', 'light_pos',
        'camera_pos', 'model_mat', 'view_mat', 'proj_mat']
        attibutes = ['vertex_position', 'vertex_normal']
        self.locations = self.get_locations(self.shader, uniforms, attibutes)

        self.vertices, self.triangles = Icosphere().make_icosphere(subdivisions)

    def set_highlighter(self, highlighter):
        self.radius = highlighter.get_node_radius()
        self.positions = highlighter.get_layout().values()
        self.colors = highlighter.get_node_colors()
        self.light_color = highlighter.get_light_color()

        self.vertex_data = np.array([[f * self.radius for f in vec] for vec in self.vertices], 'f')
        self.indices = np.array([f for vec in self.triangles for f in vec], 'uint32')
        self.stride = len(self.vertex_data[0])*4 # n items per row, and each row is 4 bytes

    def render(self, tick, offset, light_pos, context):
        shaders.glUseProgram(self.shader)
        try:
            gl.glUniform3f( self.locations['camera_pos'], *context.camera_pos )
            gl.glUniform3f( self.locations['light_pos'], *light_pos)
            gl.glUniform3f( self.locations['light.ambient'], *self.light_color.ambient )
            gl.glUniform3f( self.locations['light.diffuse'], *self.light_color.diffuse )
            gl.glUniform3f( self.locations['light.specular'], *self.light_color.specular )
            gl.glUniformMatrix4fv( self.locations['view_mat'], 1, gl.GL_FALSE, glm.value_ptr(context.view_mat))
            gl.glUniformMatrix4fv( self.locations['proj_mat'], 1, gl.GL_FALSE, glm.value_ptr(context.proj_mat))

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
class NetworkRenderer(Renderer):
    def __init__(self, highlighter, aspect):
        self.focused_node = None # Will keep a reference of the node that the pointer is currently hovering over

        self.light_renderer = RenderSpheres(subdivisions=2)
        self.nodes_renderer = RenderSpheres(subdivisions=2)
        self.line_renderer = RenderLine()
        self.crosshair_renderer = Crosshair()
        self.set_highlighter(highlighter)

        self.screen_shaders = self.read_shaders("screen.vert", "screen.frag")
        self.blur_shaders = self.read_shaders("screen.vert", "gaussian_blur.frag")

        # Setup VAO for screen quad and blur filter
        blur_uniforms = ['image', 'horizontal']
        hdr_uniforms = ['scene', 'bloomBlur', 'exposure']
        attributes = ['quad_pos', 'tex_coord']
        self.hdr_locations = self.get_locations(self.screen_shaders, hdr_uniforms, attributes)
        self.blur_locations = self.get_locations(self.blur_shaders, blur_uniforms, attributes)

        shaders.glUseProgram(self.screen_shaders)
        gl.glUniform1i(self.hdr_locations["scene"], 0)
        gl.glUniform1i(self.hdr_locations["bloomBlur"], 1)

        shaders.glUseProgram(self.blur_shaders)
        gl.glUniform1i(self.blur_locations["image"], 0)

        # The vbo for two triangles to make a quad
        self.quad_vbo = vbo.VBO(np.array([
        [-1,  1,  0, 1],
        [-1, -1,  0, 0],
        [1, -1,  1, 0],

        [-1,  1,  0, 1],
        [ 1, -1,  1, 0],
        [ 1,  1,  1, 1]
        ], 'f'))

        self.setup_frame_buffer(aspect)

        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            print("Error: frame buffers have not been completed")
            exit(0)

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    # Because frame buffers are only as large as the resolution of the screen, they have to be updated whenever
    # the screen gets resized, which is why this function is called to create new framebuffers in the reshape function
    def setup_frame_buffer(self, aspect):
        if hasattr(self, "frame_buffer"):
            gl.glDeleteFramebuffers(1, [self.frame_buffer])

        self.aspect = aspect

        # Setup frame buffer business for post processing
        self.frame_buffer = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.frame_buffer)

        self.color_buffers = gl.glGenTextures(2)

        # Attach two framebuffers to do bloom so we don't need more than 1 extra rendering pass
        # Basically, our fragment shaders will output two color values, and those two color values
        # get put into the two buffers respectively. The first is the normal output, and the second
        # is the blur output for bright lighting
        for i in range(2):
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.color_buffers[i])
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB16F, *aspect, 0, gl.GL_RGB, gl.GL_FLOAT, None)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0 + i, gl.GL_TEXTURE_2D, self.color_buffers[i], 0)

        gl.glDrawBuffers(2, [gl.GL_COLOR_ATTACHMENT0, gl.GL_COLOR_ATTACHMENT1])

        # This is our custom depth buffer since we are replacing the default framebuffer
        # Without this depth buffer, the depth test fails
        rbo = gl.glGenRenderbuffers(1);
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, rbo); 
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH24_STENCIL8, *aspect);
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0);
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_STENCIL_ATTACHMENT, gl.GL_RENDERBUFFER, rbo);

        # Create ping-pong framebuffers for the gaussian blur so we can
        # apply it multiple times and control how much we blur
        self.blur_frame_buffers = gl.glGenFramebuffers(2);
        self.blur_tex_buffers = gl.glGenTextures(2);

        gl.glEnable(gl.GL_DEPTH_TEST)

        # Create two framebuffers to create the blur effect that will bounce back and forth
        for i in range(2):
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.blur_frame_buffers[i])
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.blur_tex_buffers[i])
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB16F, *aspect, 0, gl.GL_RGB, gl.GL_FLOAT, None)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.blur_tex_buffers[i], 0)

    def set_highlighter(self, highlighter):
        self.highlighter = highlighter
        if self.focused_node != None:
            self.nodes_renderer.colors[self.focused_node] = self.prev_focused_material
        self.focused_node = None
        self.nodes_renderer.set_highlighter(highlighter)
        self.line_renderer.set_highlighter(highlighter)

    def render(self, tick, offset, light_pos, context):
        degree = np.round((tick * 0.1)) % 360;
        light_pos = (10, 10, 10)

        # Reset the previously focused node back to its original color
        if self.focused_node != None:
            self.nodes_renderer.colors[self.focused_node] = self.prev_focused_material

        self.focused_node = self.findFocusedNode(context, self.highlighter.get_node_radius())

        # First pass (the normal render)

        # Resise viewport to match the framebuffer size
        gl.glViewport(0, 0, *self.aspect)

        # Bind the hdr framebuffer (which is the one that contains two color buffers)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.frame_buffer)
        gl.glClearColor(0, 0, 0, 1.0);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT);

        # Make the focused node bright
        if self.focused_node != None:
            self.prev_focused_material = self.nodes_renderer.colors[self.focused_node]
            self.nodes_renderer.colors[self.focused_node] = hl.Material((1, 1, 1), (1, 1, 1), (1, 1, 1), 1)

        self.nodes_renderer.render(tick, (0, 0, 0), light_pos, context)

        gl.glEnable(gl.GL_BLEND);
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA);  
        self.line_renderer.render(tick, (0, 0, 0), light_pos, context)
        gl.glDisable(gl.GL_BLEND);

        # Second gaussian "ping pong" blur pass

        # Make sure we use the first texture (because we are using more than one texture)
        gl.glActiveTexture(gl.GL_TEXTURE0);
        shaders.glUseProgram(self.blur_shaders)

        # Blur back and forth between the two blur frame buffers
        blur_iterations = 10
        for i in range(blur_iterations):
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.blur_frame_buffers[i % 2]); 
            gl.glUniform1ui( self.blur_locations['horizontal'], i % 2 )
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.color_buffers[1] if i == 0 else self.blur_tex_buffers[(i + 1) % 2])
            self.renderScreenQuad(self.blur_locations)

        # Back to normal viewport
        gl.glViewport(0, 0, glut.glutGet(glut.GLUT_WINDOW_WIDTH), glut.glutGet(glut.GLUT_WINDOW_HEIGHT) )

        # Third HDR tonemapping pass

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glClearColor(1.0, 1.0, 1.0, 1.0);
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT);
        shaders.glUseProgram(self.screen_shaders)
        gl.glUniform1f(self.hdr_locations["exposure"], 1)

        # Combine the normal buffer and the blurred buffer into one output
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.color_buffers[0])
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.blur_tex_buffers[0])
        self.renderScreenQuad(self.hdr_locations)

        # Only render crosshair for first person
        if context.view_mode == 1:
            gl.glDisable(gl.GL_DEPTH_TEST)
            self.crosshair_renderer.render(tick, light_pos, light_pos, context)
            gl.glEnable(gl.GL_DEPTH_TEST)

        # Render node text if we need to
        shaders.glUseProgram(0)
        if self.focused_node != None:
            self.glutPrint(self.highlighter.print_node(self.focused_node), pos=(5, 25))

    # Helper function to render a screen quad across the viewport
    def renderScreenQuad(self, locations):
        self.quad_vbo.bind()
        gl.glEnableVertexAttribArray( locations["quad_pos"] )
        gl.glEnableVertexAttribArray( locations["tex_coord"] )
        stride = 4*4 # 4 items per row
        gl.glVertexAttribPointer(locations["quad_pos"],2, gl.GL_FLOAT,False, stride, self.quad_vbo)
        gl.glVertexAttribPointer(locations["tex_coord"],2, gl.GL_FLOAT,False, stride, self.quad_vbo + (2 * 4))
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
        self.quad_vbo.unbind()
        gl.glDisableVertexAttribArray( locations["quad_pos"] )
        gl.glDisableVertexAttribArray( locations["tex_coord"] )

    # If the view mode is first person, the coordinates detected node is simply just the center
    # of the screen, which is the camera front vector I already have stored
    # For overhead perspective, it gets more complicated, but basically it convert the mouse window
    # coordinates into world space using the glm unProject method
    def findFocusedNode(self, context, sphere_radius):
        max_focus_distance = 64
        x_1 = context.camera_pos
        if context.view_mode == 1:
            x_2 = (context.camera_front * max_focus_distance) + context.camera_pos
        else:
            width = glut.glutGet(glut.GLUT_WINDOW_WIDTH)
            height = glut.glutGet(glut.GLUT_WINDOW_HEIGHT)
            viewport = glm.vec4(0, 0, width, height)

            # The z value is apparently the z buffer depth. It seems to work fine when I give it a depth of 0.
            window_coord = glm.vec3(context.mouse_pos[0], height - context.mouse_pos[1] - 1, 0)
            
            # Convert from window coordinates back to world coordinates
            world_coord = glm.unProject(window_coord, context.view_mat, context.proj_mat, viewport)

            # Convert world coordinates into a ray that goes in the direction of the mouse
            x_2 = glm.normalize(world_coord - x_1) * max_focus_distance + context.camera_pos

        denominator = 1 / np.linalg.norm(x_2 - x_1)
        closest_node = None
        closest_distance = np.inf

        for node, pos in self.highlighter.get_layout().items():
            x_0 = glm.vec3(pos)

            # Minimize and find distance to the line
            distance = np.linalg.norm(glm.cross(x_0 - x_1, x_0 - x_2)) * denominator
            distance_to_camera = glm.distance(x_0, x_1)

            # Since it is a sphere, the collision is if the distance to the line within the radius
            # Since multiple nodes would be within the line of sight, choose the one closest to the camera
            if distance < sphere_radius and distance_to_camera < closest_distance:
                closest_node = node
                closest_distance = distance_to_camera

        return closest_node

    # Print some text to opengl
    def glutPrint(self, string, pos=(5, 5)):
        gl.glLoadIdentity()
        gl.glColor3f(1,1,1)
        gl.glWindowPos2i(*pos)

        for ch in string:
            glut.glutBitmapCharacter(glut.GLUT_BITMAP_HELVETICA_18, ord(ch))

# Renders a simple crosshair using two lines in normalized device coordiates
class Crosshair(Renderer):
    def __init__(self):
        self.shader = self.read_shaders("line.vert", "crosshair_line.frag")
        uniforms = ['model_mat', 'view_mat', 'proj_mat']
        attributes = ['vertex_position', 'line_color']
        self.locations = self.get_locations(self.shader, uniforms, attributes)

        edges = [(-0.011, 0, 0), (0.01, 0, 0), (0, -0.015, 0), (0, 0.01, 0)]
        self.num_points = len(edges)
        colors = [(0.5, 0.5, 0.5, 1)]*4
        the_vbo = [[*edges, *colors] for edges, colors in zip(edges, colors)]
        self.vertex_vbo = vbo.VBO(np.array(the_vbo, 'f'))

    def render(self, tick, offset, light_pos, context):
        identity_mat = glm.mat4(1)
        shaders.glUseProgram(self.shader)
        try:
            self.vertex_vbo.bind()
            try:
                gl.glUniformMatrix4fv( self.locations['model_mat'], 1, gl.GL_FALSE, glm.value_ptr(identity_mat))
                gl.glUniformMatrix4fv( self.locations['view_mat'], 1, gl.GL_FALSE, glm.value_ptr(identity_mat))
                gl.glUniformMatrix4fv( self.locations['proj_mat'], 1, gl.GL_FALSE, glm.value_ptr(identity_mat))
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

class Context:
    def __init__(self, highlighters, view_mode, resolution):
        self.tick = 0 # World ticks in milleseconds
        self.fov = 55 # Field of view
        self.resolution = resolution
        self.overhead_view_distance = 5;
        self.aspect = self.resolution[0] / self.resolution[1]
        self.view_mode = view_mode # 0 for overhead and 1 for first person
        self.prev_frame_time = 0
        self.delta_time = 0
        self.reset_view()
        self.init_glut()
        self.setup_view_proj()
        self.warp = False; # To keep the motion function from being called after we warp the mouse pointer
        self.highlighter = 0
        self.highlighters = highlighters
        self.renderer = NetworkRenderer(self.highlighters[self.highlighter], self.resolution)
        self.mouse_pos = (0, 0)

    def reset_view(self):
        self.camera_pos = glm.vec3(0, 0, 3)
        self.camera_front = glm.vec3(0, 0, -1)
        self.camera_up = glm.vec3(0, 1, 0)
        self.angle = 0
        self.elevation = 0

    def setup_view_proj(self):
        if self.view_mode == 0:
            Ex = -2*self.overhead_view_distance*self.approxSin(self.angle)*self.approxCos(self.elevation);
            Ey = +2*self.overhead_view_distance*self.approxSin(self.elevation);
            Ez = +2*self.overhead_view_distance*self.approxCos(self.angle)*self.approxCos(self.elevation);
            self.camera_pos = glm.vec3(Ex, Ey, Ez)
            camera_target = glm.vec3(0)
            self.view_mat = glm.lookAt(self.camera_pos, camera_target, glm.vec3(0, self.approxCos(self.elevation), 0))

        elif self.view_mode == 1:
            self.camera_front.x = np.cos(glm.radians(self.angle)) * np.cos(glm.radians(self.elevation))
            self.camera_front.y = np.sin(glm.radians(self.elevation))
            self.camera_front.z = np.sin(glm.radians(self.angle)) * np.cos(glm.radians(self.elevation))
            self.camera_front = glm.normalize(self.camera_front)
            self.view_mat = glm.lookAt(self.camera_pos, self.camera_pos + self.camera_front, self.camera_up)

        self.proj_mat = glm.perspective(glm.radians(self.fov), self.aspect, 0.25, 64);

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
        glut.glutIdleFunc(self.idle)
        glut.glutMotionFunc(self.mouse_motion)
        glut.glutPassiveMotionFunc(self.mouse_motion)
        glut.glutMouseFunc(self.mouse)

    def mouse(self, button, state, x, y):
        if state == glut.GLUT_UP:
            return

        if button == 3:
            self.fov = np.clip(self.fov + 1, 30, 90)
        elif button == 4:
            self.fov = np.clip(self.fov - 1, 30, 90)

        self.setup_view_proj()

    def mouse_motion(self, x, y):
        self.mouse_pos = (x, y)

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

        self.setup_view_proj()

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

        self.setup_view_proj()

    def display(self):
        self.renderer.render(self.tick, (0, 0, 0), None, self)

        err = gl.glGetError()
        if err != gl.GL_NO_ERROR:
            print('GLERROR: ', glu.gluErrorString( err ))
            sys.exit()

        glut.glutSwapBuffers()
        glut.glutPostRedisplay()

    def reshape(self, width, height):
        self.aspect = width / height if height > 0 else 1
        self.resolution = [width, height]
        self.renderer.setup_frame_buffer(self.resolution)
        self.setup_view_proj()

    def keyboard(self, key, x, y):
        if key == b'\x1b':
            glut.glutLeaveMainLoop() # I use this because exiting throws exceptions

        elif key == b'n':
            self.highlighter = (self.highlighter + 1) % len(self.highlighters)
            self.renderer.set_highlighter(self.highlighters[self.highlighter])
            glut.glutPostRedisplay()
        elif key == b'b':
            self.highlighter = (self.highlighter - 1) % len(self.highlighters)
            self.renderer.set_highlighter(self.highlighters[self.highlighter])
            glut.glutPostRedisplay()
        elif key == b'v':
            self.view_mode = 0 if self.view_mode == 1 else 1
            if self.view_mode == 1:
                glut.glutSetCursor(glut.GLUT_CURSOR_NONE)
            else:
                glut.glutSetCursor(glut.GLUT_CURSOR_RIGHT_ARROW)
            self.reset_view()
            self.setup_view_proj()
            glut.glutPostRedisplay()

    def idle(self):
        self.tick = glut.glutGet(glut.GLUT_ELAPSED_TIME);
        self.delta_time = self.tick - self.prev_frame_time
        self.prev_frame_time = self.tick

def visualize(highlighters=None, view_mode=1, resolution=(1280, 720)):
    """Generates an opengl window that renders the given network"""

    if highlighters == None:
        print("No highlighter specified: nothing to show")
        return

    try:
        highlighters = [highlighter for highlighter in highlighters]
    except TypeError as te:
        highlighters = [highlighters]

    Context(highlighters, view_mode, resolution)
    glut.glutMainLoop()
