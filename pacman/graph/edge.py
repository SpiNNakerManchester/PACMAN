__author__ = 'stokesa6'
class Edge(object):
    """An edge object"""

    def __init__(self, pre_vertex, post_vertex, label):
        """Create a new edge
        :param label: The name of the edge
        :type label: str
        :param pre_vertex: the outgoing vertex
        :type pre_vertex: pacman.graph.vertex.Vertex
        :param post_vertex:  the incoming vertex
        :type post_vertex: pacman.graph.vertex.Vertex
        :return: an Edge
        :rtype: pacman.graphg.edge.Edge
        :raises None: Raises no known exceptions
        """
