import numpy as np
import networkx as nx
import colorsys
import math

# This defines the way the surface will interact with lighting in a fine grain manner
class Material():
    def __init__(self, ambient, diffuse, specular, shininess):
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular
        self.shininess = shininess

    def __repr__(self):
        return "Ambient: ({}, {}, {}), Diffuse: ({}, {}, {}), Specular: ({}, {}, {}), Shininess: {}".format(
            *self.ambient, *self.diffuse, *self.specular, self.shininess)

class Highlighter():
    def __init__(self, graph):
        self.graph = graph
        self.layout = self.spring_layout = nx.spring_layout(graph, dim=3, scale=9)
        self.node_colors=[Material(colorsys.hsv_to_rgb(np.random.rand(), 1, 1), colorsys.hsv_to_rgb(np.random.rand(), 1, 1), (0.5, 0.5, 0.5), 32) for node in graph.nodes()]
        self.edge_colors=[(0.5, 0.5, 0.5, 0.5) for edge in graph.edges for node in edge]
        self.light_color = Material((0.2, 0.2, 0.2), (0.5, 0.5, 0.5), (1.0, 1.0, 1.0), 0)
        
        def print_name_degree(focused_node):
            name = self.graph[focused_node]["name"] if hasattr(self.graph[focused_node], "name") else "Node: " + str(focused_node)
            if nx.is_directed(self.graph):
                degrees = "In Degree: " + str(self.graph.in_degree[focused_node])
                degrees += ", Out Degree: " + str(self.graph.out_degree[focused_node])
            else:
                degrees = "Degree: " + str(self.graph.degree[focused_node])
            return name + ", " + degrees

        self.text_func = print_name_degree

    def set_node_colors(self, node_colors):
        """Accepts an array of Materials that correspond to the colors of each node in the network"""

        self.node_colors = node_colors

    def set_edge_colors(self, edge_colors):
        """Accepts an array of tuples of four values which correspond to the colors from one node to the next node"""

        self.edge_colors = edge_colors

    def get_node_colors(self):
        return self.node_colors

    def get_edge_colors(self):
        return self.edge_colors

    def get_edges(self):
        return self.graph.edges()

    def get_node_radius(self):
        return 0.05

    def get_layout(self):
        return self.layout

    def get_light_color(self):
        return self.light_color

    def set_light_color(self, light_color):
        """Sets the light color to a material"""

        self.light_color = light_color

    def get_edge_strengths(self):
        if not hasattr(self, "edge_strengths"):
            if nx.is_directed(self.graph):
                self.edge_strengths = [1 if self.graph.has_edge(edge[1], edge[0]) else 0 for edge in self.graph.edges()]
            else:
                self.edge_strengths = [1 for edge in self.graph.edges()]

        return self.edge_strengths

    def set_node_text(self, text_func):
        """Accepts a function that takes in the node number, and return a string that is the node description"""

        self.text_func = text_func

    def print_node(self, focused_node):
        return self.text_func(focused_node)

class LightHighlighter(Highlighter):
    def __init__(self):
        graph = nx.fast_gnp_random_graph(1, 0)
        super().__init__(graph)
        self.light_material = Material((1.1, 1.1, 1.1), (1, 1, 1), (1, 1, 1), 1)

    def get_node_colors(self):
        return [self.light_material]

    def get_light_color(self):
        return self.light_material