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

# Abstract class to get node highlights
class Highlighter():
    def get_node_colors(self):
        pass

    # Return a list of colors where each pair correspond to an edge.
    def get_edge_colors(self):
        pass
    
    # Return a list of colors where each corresponds to a node
    def get_light_color(self):
        return Material((0.2, 0.2, 0.2), (0.5, 0.5, 0.5), (1.0, 1.0, 1.0), 0)

# Make the node brighter depending on its degree
class DegreeHighlighter(Highlighter):
    def __init__(self, graph):
        degrees = [degree for node, degree in graph.degree]
        max_degree = 1 / max(degrees)
        self.colors = [Material(
                colorsys.hsv_to_rgb(0, 0.5, degree * max_degree), 
                colorsys.hsv_to_rgb(0, 0.5, degree * max_degree),
            (0.5, 0.5, 0.5), 32) for degree in degrees]

        self.edge_colors = [(2, 1, 2, 0.5) for edge in graph.edges for node in edge]
 
    def get_edge_colors(self):
        return self.edge_colors

    def get_node_colors(self):
        return self.colors

# Highlights triangles within the network
class MotifHighlighter(Highlighter):
    def __init__(self, graph):
        self.graph = graph

        degrees = [degree for node, degree in graph.degree]
        max_degree = 1 / max(degrees)
        self.colors = [Material(
                colorsys.hsv_to_rgb(0,0.5,0.5), 
                colorsys.hsv_to_rgb(0,0.5,0.5),
            (0.5, 0.5, 0.5), 32) for degree in degrees]

        triangles = self.find_triangles()
        for node in triangles:
            self.colors[node].ambient = colorsys.hsv_to_rgb(0.5,0.5,1)

        self.edges = map(lambda edge : (1, 0.5, 0.5, 1) if edge[0] in triangles and edge[1] in triangles else (1, 1, 1, 0.5), graph.edges())
        self.edges = [self.edges[math.floor(i*0.5)] for i in len(degrees)] # Because we need the colors twice for each edge point

    def get_edge_colors(self):
        return list(self.edges)

    def get_node_colors(self):
        return self.colors

    # Find all nodes that are part of a triangle
    def find_triangles(self):
        triangles = set()
        for node in self.graph:
            for neighbor in self.graph.neighbors(node):
                for second_neighbor in self.graph.neighbors(neighbor):
                    if neighbor != second_neighbor and self.graph.has_edge(second_neighbor, node):
                        triangles.update((node, neighbor, second_neighbor))
        return triangles

# Creates a partition based on max likelihoods and render that in nodes
class PartitionHighlighter(Highlighter):
    def __init__(self, graph):

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