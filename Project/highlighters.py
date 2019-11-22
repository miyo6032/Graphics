import numpy as np
import networkx as nx
import colorsys
import partition
import math

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
        return Material((0.2, 0.2, 0.2), (0.5, 0.5, 0.5), (1.0, 1.0, 1.0), 0)

    def get_edge_strengths(self):
        if not hasattr(self, "edge_strengths"):
            if nx.is_directed(self.graph):
                self.edge_strengths = [1 if self.graph.has_edge(edge[1], edge[0]) else 0 for edge in self.graph.edges()]
            else:
                self.edge_strengths = [1 for edge in self.graph.edges()]

        return self.edge_strengths

class LightHighlighter(Highlighter):
    def __init__(self):
        graph = nx.fast_gnp_random_graph(1, 0)
        super().__init__(graph)
        self.light_material = Material((2, 2, 2), (1, 1, 1), (1, 1, 1), 1)

    def get_node_colors(self):
        return [self.light_material]

    def get_light_color(self):
        return self.light_material

# Creates a partition based on max likelihoods and render that in nodes
class PartitionHighlighter(Highlighter):
    def __init__(self, graph):
        super().__init__(graph)
        z = partition.get_partition_n(graph, c = 2, trials = 5)
        max_degree = 1 / max(z)
        hue = lambda group : (group * max_degree) * 0.7 # Make it less than 1 so we don't get red values for max and min
        self.node_colors = [Material(
                colorsys.hsv_to_rgb(hue(group), 0.5, 1), 
                colorsys.hsv_to_rgb(hue(group), 0.5, 1),
            (0.5, 0.5, 0.5), 32) for group in z]
        self.edge_colors = [(*colorsys.hsv_to_rgb(hue(z[node]), 0.5, 1), 0.5) for edge in graph.edges for node in edge]

    def get_edge_colors(self):
        return self.edge_colors

    def get_node_colors(self):
        return self.node_colors