__author__ = 'stokesa6,daviess'


class Edge(object):
    """ Creates a new edge object """

    def __init__(self, label, pre_vertex, post_vertex):
        """

        :param label: The name of the edge
        :type label: str
        :param pre_vertex: the outgoing vertex
        :type pre_vertex: pacman.graph.vertex.Vertex
        :param post_vertex: the incoming vertex
        :type post_vertex: pacman.graph.vertex.Vertex
        :return: an Edge
        :rtype: pacman.graph.edge.Edge
        :raise None: Raises no known exceptions
        """
        self._label = label
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex

    @property
    def pre_vertex(self):
        """
        Returns the outgoing vertex

        :return: the outgoing vertex
        :rtype: pacman.graph.vertex.Vertex
        :raise None: Raises no known exceptions
        """
        return self._pre_vertex

    @property
    def post_vertex(self):
        """
        Returns the incoming vertex

        :return: the incoming vertex
        :rtype: pacman.graph.vertex.Vertex
        :raise None: Raises no known exceptions
        """
        return self._post_vertex

    @property
    def label(self):
        """
        Gets the label of the edge

        :return: The name of the edge
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label
