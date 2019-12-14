import importlib
import visualizer as vs
import networkx as nx
import highlighters as hl
import colorsys
import partition
from pathlib import Path
import functools
import random as rand
import numpy as np

# Shows the neighbors of a selected network
def neighbors_highlighter(G):
    highlighter = hl.Highlighter(G)

    def on_node_selection(node):
        return "Node: {}".format(node)

    highlighter.set_node_text(on_node_selection)

    def color(node):
        return (0.5, 0.5, 0.5)

    node_colors = [hl.Material(
        color(node), 
        color(node),
        color(node), 
        32) for node in G.nodes]
    
    edge_colors = [(0.8, 0.8, 0.8, 0.05) for edge in G.edges for node in edge]
    highlighter.set_node_colors(node_colors)
    highlighter.set_edge_colors(edge_colors)
    return highlighter

def text_highlighter(G):
    highlighter = hl.Highlighter(G)
    highlighter.set_node_radius(0.01)

    if nx.is_directed(G):
        reciprocities = list(nx.algorithms.reciprocity(G, nodes=G.nodes).values())

    def display_node_attributes(node):
        """Accepts a node, calculates various attributes, and formats it into a string"""

        text = G[node]["name"] if hasattr(G[node], "name") else "Node: " + str(node)

        if nx.is_directed(G):
            text += ", In Degree: " + str(G.in_degree[node])
            text += ", Out Degree: " + str(G.out_degree[node])
        else:
            text += "Degree: " + str(G.degree[node])

        eccentricity = max(nx.single_source_shortest_path_length(G, node))
        text += ", Ecentricity: " + str(eccentricity)

        if nx.is_directed(G):
            text += ", Reciprocity: {:.2f}".format(reciprocities[node])

        return text
    highlighter.set_node_text(display_node_attributes)

    degrees = [degree for node, degree in G.in_degree]
    median_degree = np.median(degrees)
    def color(degree):
        return (0.5, 0.5, 1) if degree < (median_degree * 9) else (15, 10, 10)
    node_colors = [hl.Material(
            color(degree), 
            color(degree),
            color(degree), 
            32) for degree in degrees]

    edge_colors = [(0.8, 0.8, 0.8, 0.05) for edge in G.edges for node in edge]
    highlighter.set_node_colors(node_colors)
    highlighter.set_edge_colors(edge_colors)
    return highlighter

def degree_vibrance_highlighter(G, use_hue=False):
    """Sets node colors and edges to be brighter the higher degree they have. Singletons are black."""

    highlighter = hl.Highlighter(G)
    highlighter.layout = nx.spring_layout(G, dim=3, scale=1000)
    degrees = [degree for node, degree in G.degree]
    max_degree = 1 / max(degrees)
    hue = lambda degree : (degree * max_degree) * 0.7 # Make it less than 1 so we don't get red values for max and min
    node_colors = [hl.Material(
            colorsys.hsv_to_rgb(hue(degree) if use_hue else 0, 1, 1), 
            colorsys.hsv_to_rgb(hue(degree) if use_hue else 0, 1, 1),
            colorsys.hsv_to_rgb(0, 0.0, 1), 
            1) for degree in degrees]

    edge_colors = [(*node_colors[node].ambient, 0.5) for edge in G.edges for node in edge]

    node_colors[139] = hl.Material(
            (0.5, 1, 1), 
            (0.5, 1, 1),
            (0.5, 1, 1), 
            1)

    highlighter.set_node_colors(node_colors)
    highlighter.set_edge_colors(edge_colors)
    highlighter.set_light_color(hl.Material((15, 15, 15), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0))
    return highlighter

# Will highlight all triangles, or feed foward loops
def triangle_highlighter(G, name, feed_back_loop=False):
    highlighter = hl.Highlighter(G)
    highlighter.name = name
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

    triangle_nodes, triangle_edges = find_feed_back_loop() if feed_back_loop else find_triangles()
    node_colors = [triangle_material if node in triangle_nodes else normal_material for node in G.nodes]

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

def load_network(filename):
    path = Path(__file__).parent / "./data/{}".format(filename)
    return nx.convert_node_labels_to_integers(nx.read_gml(str(path), label='id')) # map node names to integers (0:n-1) [because indexing]

g_metabolism = load_network("metabolism_afulgidus.gml")
metabolism_in_degree = [degree for node, degree in g_metabolism.in_degree]
mean_in_degree = sum(metabolism_in_degree) / g_metabolism.number_of_nodes()

metabolism_null = nx.fast_gnp_random_graph(g_metabolism.number_of_nodes(), mean_in_degree / g_metabolism.number_of_nodes(), directed=True)

g_karate = load_network("karate.gml")
g_yeast = load_network("yeast_spliceosome.gml")
g_grass = load_network("grass_web.gml")
path = Path(__file__).parent / "./data/p.pacificus_neural.synaptic_1.graphml"
g_multi = nx.convert_node_labels_to_integers(nx.read_graphml(str(path))) # map node names to integers (0:n-1) [because indexing]
g_neural = nx.Graph()                     # G will be a simple graph
g_neural.add_edges_from(g_multi.edges())        # G is now a simplified Gmulti (tricky :)

G_30 = nx.fast_gnp_random_graph(30, 3 / 30, directed=True)

G_300 = nx.fast_gnp_random_graph(300, 3 / 300)

block_nodes = [10, 15, 10, 15]

# Create an ordered structure
block_matrix = [
    [10 / block_nodes[0], 5 / block_nodes[0], 1 / block_nodes[0], 0],
    [5 / block_nodes[0], 10 / block_nodes[1], 5 / block_nodes[1], 1 / block_nodes[1]],
    [1 / block_nodes[0], 5 / block_nodes[1], 10 / block_nodes[2], 5 / block_nodes[2]],
    [0                  , 1 / block_nodes[1], 5 / block_nodes[2], 10 / block_nodes[3]]
]

block_model = nx.stochastic_block_model(block_nodes, block_matrix)

rand.seed(101) # Just to make sure the visualizations we have don't get messed up due to bad luck
vs.visualize(highlighters=[
    text_highlighter(g_metabolism),
    triangle_highlighter(G_300, "ER Network, N: 300, <k>: 3"), 
    # triangle_highlighter(g_yeast, "Yeast Splicesome"), 
    # triangle_highlighter(g_grass, "Grass Web"), 
    # partition_highlighter(g_karate, "karate_partition"),
    # partition_highlighter(block_model, "block_partition", c=4),
    # partition_highlighter(g_metabolism, "metabolism_partition"),
    # partition_layout_adjusted(g_metabolism, "metabolism_partition"), 
    # partition_highlighter(g_neural, "neural_partition"),
    # partition_layout_adjusted(g_neural, "neural_partition"),
    # partition_highlighter(g_yeast, "yeast_partition"),
    # partition_layout_adjusted(g_yeast, "yeast_partition"), 
    # partition_highlighter(g_grass, "grass_web_partition"),
    # partition_layout_adjusted(g_grass, "grass_web_partition"), 
    # degree_vibrance_highlighter(g_karate, use_hue=True), 
    # triangle_highlighter(g_karate, "Karate Network"), 
    # triangle_highlighter(metabolism_null, "Metabolism Network", feed_back_loop=True),
    ], view_mode=0)