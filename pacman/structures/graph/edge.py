__author__ = 'stokesa6,daviess'


class Edge(object):
    """ Creates a new edge object """

    def __init__(self, pre_vertex, post_vertex, label=None):
        """

        :param pre_vertex: the outgoing vertex
        :param post_vertex: the incoming vertex
        :param label: The name of the edge
        :type pre_vertex: pacman.graph.vertex.Vertex
        :type post_vertex: pacman.graph.vertex.Vertex
        :type label: str or None
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
        :rtype: str or None
        :raise None: Raises no known exceptions
        """
        return self._label
