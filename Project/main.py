import visualizer as vs
import networkx as nx
import highlighters as hl
import colorsys
import partition
from pathlib import Path

def degree_vibrance_highlighter(G):
    """Sets node colors and edges to be brighter the higher degree they have. Singletons are black."""

    highlighter = hl.Highlighter(G)
    degrees = [degree for node, degree in G.degree]
    max_degree = 1 / max(degrees)
    node_colors = [hl.Material(
            colorsys.hsv_to_rgb(0, 0.5, degree * max_degree), 
            colorsys.hsv_to_rgb(0, 0.5, degree * max_degree),
            colorsys.hsv_to_rgb(0, 0.0, degree * max_degree), 
            32) for degree in degrees]

    edge_colors = [(*node_colors[node].ambient, 0.5) for edge in G.edges for node in edge]
    highlighter.set_node_colors(node_colors)
    highlighter.set_edge_colors(edge_colors)
    return highlighter

def triangle_highlighter(G):
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

    node_colors = [normal_material for degree in degrees]

    triangle_nodes, triangle_edges = find_triangles()
    for node in triangle_nodes:
        node_colors[node] = triangle_material # replace nodes in triangle with a special material

    # Edges that are a part of a triangle are highlighted with a special color
    edge_colors = [triangle_edge_color if edge in triangle_edges else normal_edge_color for edge in G.edges for node in edge]

    highlighter.set_node_colors(node_colors)
    highlighter.set_edge_colors(edge_colors)
    return highlighter

# Creates a partition based on max likelihoods and render that in nodes
def partition_highlighter(G):
    highlighter = hl.Highlighter(G)
    z = partition.get_partition_n(G, c = 2, trials = 5)
    max_degree = 1 / max(z)
    hue = lambda group : (group * max_degree) * 0.7 # Make it less than 1 so we don't get red values for max and min
    node_colors = [hl.Material(
                colorsys.hsv_to_rgb(hue(group), 1, 1), 
                colorsys.hsv_to_rgb(hue(group), 1, 1),
            (0.5, 0.5, 0.5), 32) for group in z]
    edge_colors = [(*colorsys.hsv_to_rgb(hue(z[node]), 1, 1), 0.5) for edge in G.edges for node in edge]
    highlighter.set_node_colors(node_colors)
    highlighter.set_edge_colors(edge_colors)
    return highlighter

G_300 = nx.fast_gnp_random_graph(300, 3 / 300)

g_di = nx.fast_gnp_random_graph(100, 3 / 100, directed=True) 

path = Path(__file__).parent / "./data/karate.gml"
Go     = nx.read_gml(str(path), label='id')
G      = nx.convert_node_labels_to_integers(Go) # map node names to integers (0:n-1) [because indexing]

vs.visualize(G, highlighters=[partition_highlighter(G), degree_vibrance_highlighter(g_di), triangle_highlighter(G_300), degree_vibrance_highlighter(G)], view_mode=0)