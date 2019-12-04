import visualizer as vs
import networkx as nx
import highlighters as hl
import colorsys
import partition
from pathlib import Path
import functools
import random as rand
import numpy as np

def neon_highlighter(G):
    """Displays nodes as bright blue and edges as white"""

    highlighter = hl.Highlighter(G)
    degrees = [degree for node, degree in G.degree]
    max_degree = 1 / max(degrees)
    node_colors = [hl.Material(
            (1, 1, 10), 
            (1, 1, 10),
            (1, 1, 10), 
            1) for degree in degrees]

    edge_colors = [(0.8, 0.8, 0.8, 0.5) for edge in G.edges for node in edge]
    highlighter.set_node_colors(node_colors)
    highlighter.set_edge_colors(edge_colors)
    highlighter.set_light_color(hl.Material((5, 5, 5), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0)) # Makes the nodes neon
    return highlighter

def degree_vibrance_highlighter(G, use_hue=False):
    """Sets node colors and edges to be brighter the higher degree they have. Singletons are black."""

    highlighter = hl.Highlighter(G)
    degrees = [degree for node, degree in G.degree]
    max_degree = 1 / max(degrees)
    hue = lambda degree : (degree * max_degree) * 0.7 # Make it less than 1 so we don't get red values for max and min
    node_colors = [hl.Material(
            colorsys.hsv_to_rgb(hue(degree) if use_hue else 0, 1, degree * max_degree), 
            colorsys.hsv_to_rgb(hue(degree) if use_hue else 0, 1, degree * max_degree),
            colorsys.hsv_to_rgb(0, 0.0, degree * max_degree), 
            32) for degree in degrees]

    edge_colors = [(*node_colors[node].ambient, 0.5) for edge in G.edges for node in edge]
    highlighter.set_node_colors(node_colors)
    highlighter.set_edge_colors(edge_colors)
    return highlighter

# Will highlight all triangles, or feed foward loops
def triangle_highlighter(G, feed_back_loop=False):
    highlighter = hl.Highlighter(G)
    degrees = [degree for node, degree in G.degree]
    normal_material = hl.Material(colorsys.hsv_to_rgb(0,0.5,0.5), colorsys.hsv_to_rgb(0,0.5,0.5), (0.5, 0.5, 0.5), 32)
    triangle_material = hl.Material(colorsys.hsv_to_rgb(0.5,0.5,1), colorsys.hsv_to_rgb(0.5,0.5,1), (0.5, 0.5, 0.5), 32)
    normal_edge_color = (*normal_material.ambient, 0.5)
    triangle_edge_color = (*colorsys.hsv_to_rgb(0.5,0.5,2), 0.5)

    # Find all nodes that are part of a triangle
    def find_triangles():
        triangle_nodes = set()
        triangle_edges = set()
        for node in G:
            for neighbor in G.neighbors(node):
                for second_neighbor in G.neighbors(neighbor):
                    if neighbor != second_neighbor and G.has_edge(second_neighbor, node):
                        triangle_nodes.update((node, neighbor, second_neighbor))
                        triangle_edges.update(((node, neighbor), (neighbor, second_neighbor), (second_neighbor, node), (neighbor, node), (second_neighbor, neighbor), (node, second_neighbor)))
        return triangle_nodes, triangle_edges

    def find_feed_back_loop():
        triangle_nodes = set()
        triangle_edges = set()
        for node in G:
            for neighbor in G.neighbors(node):
                for second_neighbor in G.neighbors(neighbor):
                    if neighbor != second_neighbor and node in G.neighbors(second_neighbor):
                        triangle_nodes.update((node, neighbor, second_neighbor))
                        triangle_edges.update(((node, second_neighbor), (node, neighbor), (neighbor, second_neighbor)))
        return triangle_nodes, triangle_edges

    node_colors = [normal_material for degree in degrees]

    triangle_nodes, triangle_edges = find_feed_back_loop() if feed_back_loop else find_triangles()
    for node in triangle_nodes:
        node_colors[node] = triangle_material # replace nodes in triangle with a special material

    # Edges that are a part of a triangle are highlighted with a special color
    edge_colors = [triangle_edge_color if edge in triangle_edges else normal_edge_color for edge in G.edges for node in edge]

    highlighter.set_node_colors(node_colors)
    highlighter.set_edge_colors(edge_colors)
    return highlighter

# Get the partition either from a cache or generate it using the likelihood algorithm
def get_partition(G, partition_filename, c = 2):
    path = Path(__file__).parent / "./data/" / partition_filename
    try:
        with path.open() as file:
            z = [int(i) for i in file.read().split(" ")]
    except:
        z = partition.get_partition_n(G, c = c, trials = 5)
        path.touch()
        path.write_text(functools.reduce(lambda acc, x: str(acc) + " " + str(x), z)) # Save to cache
    return z

# Creates a partition based on max likelihoods and render that in nodes
def partition_highlighter(G, partition_filename, c = 2):
    z = get_partition(G, partition_filename, c)

    highlighter = hl.Highlighter(G)
    max_degree = 1 / max(z)
    hue = lambda group : (group * max_degree) * 0.6 # Make it less than 1 so we don't get red values for max and min
    node_colors = [hl.Material(
                colorsys.hsv_to_rgb(hue(group), 1, 1), 
                colorsys.hsv_to_rgb(hue(group), 1, 1),
            (0.0, 0.0, 0.0), 1) for group in z]
    edge_colors = [(*colorsys.hsv_to_rgb(hue(z[node]), 1, 1), 0.5) for edge in G.edges for node in edge]
    highlighter.set_node_colors(node_colors)
    highlighter.set_edge_colors(edge_colors)
    highlighter.set_light_color(hl.Material((5, 5, 5), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0)) # Makes the nodes neon!

    return highlighter

# Adjust the positions of the initial layout 
def partition_layout_adjusted(G, partition_filename):
    highlighter = partition_highlighter(G, partition_filename)
    z = get_partition(G, partition_filename)
    group_0 = lambda : [rand.random() * 0.01 + 0.1 for i in range(3)]
    group_1 = lambda : [rand.random() * 0.01 - 0.1 for i in range(3)]
    pos = {node : group_1() if z[node] == 1 else group_0() for node in G}
    highlighter.layout = nx.spring_layout(G, dim=3, scale=9, pos=pos)
    return highlighter

path = Path(__file__).parent / "./data/metabolism_afulgidus.gml"
g_metabolism = nx.convert_node_labels_to_integers(nx.read_gml(str(path), label='id')) # map node names to integers (0:n-1) [because indexing]
metabolism_in_degree = [degree for node, degree in g_metabolism.in_degree]
mean_in_degree = sum(metabolism_in_degree) / g_metabolism.number_of_nodes()

metabolism_null = nx.fast_gnp_random_graph(g_metabolism.number_of_nodes(), mean_in_degree / g_metabolism.number_of_nodes(), directed=True)

path = Path(__file__).parent / "./data/karate.gml"
g_karate = nx.convert_node_labels_to_integers(nx.read_gml(str(path), label='id')) # map node names to integers (0:n-1) [because indexing]

G_30 = nx.fast_gnp_random_graph(30, 3 / 30, directed=True)

G_300 = nx.fast_gnp_random_graph(300, 3 / 300)

block_nodes = [10, 15, 10, 15]

# Create a tiered structure
block_matrix = [
    [10 / block_nodes[0], 5 / block_nodes[0], 1 / block_nodes[0], 0],
    [5 / block_nodes[0], 10 / block_nodes[1], 5 / block_nodes[1], 1 / block_nodes[1]],
    [1 / block_nodes[0], 5 / block_nodes[1], 10 / block_nodes[2], 5 / block_nodes[2]],
    [0                  , 1 / block_nodes[1], 5 / block_nodes[2], 10 / block_nodes[3]]
]

block_model = nx.stochastic_block_model(block_nodes, block_matrix)

rand.seed(101) # Just to make sure the visualizations we have don't get messed up due to bad luck
vs.visualize(highlighters=[
    neon_highlighter(G_30),
    triangle_highlighter(G_300), 
    partition_highlighter(g_karate, "karate_partition"),
    partition_highlighter(block_model, "block_partition", c=4),
    partition_highlighter(g_metabolism, "metabolism_partition"), 
    partition_layout_adjusted(g_metabolism, "metabolism_partition"), 
    degree_vibrance_highlighter(g_karate, use_hue=True), 
    triangle_highlighter(g_karate), 
    triangle_highlighter(g_metabolism, feed_back_loop=True), 
    triangle_highlighter(metabolism_null, feed_back_loop=True)
    ], view_mode=0)