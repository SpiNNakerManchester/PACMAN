from pacman.model.graph.vertex import Vertex
from pacman.model.graph.edge import Edge
from pacman.exceptions import PacmanInvalidParameterException


class Graph(object):
    """ Represents a collection of vertices and edges between vertices that
        make up a graph
    """

    def __init__(self, label=None, vertices=None, edges=None):
        """

        :param label: An identifier for the graph
        :type label: str
        :param vertices: An iterable of initial vertices in the graph
        :type vertices: iterable of :py:class:`pacman.model.graph.vertex.Vertex`
        :param edges: An iterable of initial edges in the graph
        :type edges: iterable of :py:class:`pacman.model.graph.edge.Edge`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the edges is not valid
                    * If one of the vertices in not valid
        """
        self._label = label
        self._vertices = list()
        self._edges = list()

        self._outgoing_edges = dict()
        self._incoming_edges = dict()

        self.add_vertices(vertices)
        self.add_edges(edges)

    def add_vertex(self, vertex):
        """ Add a vertex to this graph

        :param vertex: a vertex to be added to the graph
        :type vertex: :py:class:`pacman.model.graph.vertex.Vertex`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the vertex\
                    is not valid
        """
        if vertex is not None and isinstance(vertex, Vertex):
            self._vertices.append(vertex)
            self._outgoing_edges[vertex] = list()
            self._incoming_edges[vertex] = list()
        else:
            raise PacmanInvalidParameterException(
                    "vertex", vertex, 
                    "Must be an instance of pacman.model.graph.vertex.Vertex")

    def add_vertices(self, vertices):
        """ Add an iterable of vertices to this graph

        :param vertices: an iterable of vertices to be added to the graph
        :type vertices: iterable of :py:class:`pacman.model.graph.vertex.Vertex`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If any vertex\
                    in the iterable is not valid
        """
        if vertices is not None:
            for next_vertex in vertices:
                self.add_vertex(next_vertex)


    def add_edge(self, edge):
        """ Add an edge to this graph

        :param edge: an edge to be added to the graph
        :type edge: :py:class:`pacman.model.graph.edge.Edge`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the edge\
                    is not valid
        """
        if edge is not None and isinstance(edge, Edge):
            self._edges.append(edge)
            self._outgoing_edges[edge.pre_vertex].append(edge)
            self._incoming_edges[edge.post_vertex].append(edge)
        else:
            raise PacmanInvalidParameterException(
                    "edge", edge,
                    "Must be an instance of pacman.model.graph.edge.Edge")

    def add_edges(self, edges):
        """ Add an iterable of edges to this graph

        :param edges: an iterable of edges to be added to the graph
        :type edges: iterable of :py:class:`pacman.model.graph.edge.Edge`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If any edge\
                    in the iterable is not valid
        """
        if edges is not None:
            for next_edge in edges:
                self.add_edge(next_edge)

    def outgoing_edges_from_vertex(self, vertex):
        """ Locate a collection of edges for which vertex is the pre_vertex.\
            Can return an empty collection.

        :param vertex: the vertex for which to find the outgoing edges
        :type vertex: :py:class:`pacman.model.graph.vertex.Vertex`
        :return: an iterable of edges which have vertex as their pre_vertex
        :rtype: iterable of :py:class:`pacman.model.graph.edge.Edge`
        :raise None: does not raise any known exceptions
        """

        return self._outgoing_edges[vertex]


    def incoming_edges_to_vertex(self, vertex):
        """ Locate a collection of edges for which vertex is the post_vertex.\
            Can return an empty collection.

        :param vertex: the vertex for which to find the incoming edges
        :type vertex: :py:class:`pacman.model.graph.vertex.Vertex`
        :return: an iterable of edges which have vertex as their post_vertex
        :rtype: iterable of :py:class:`pacman.model.graph.edge.Edge`
        :raise None: does not raise any known exceptions
        """

        return self._incoming_edges[vertex]

    @property
    def label(self):
        """ The label of the graph

        :return: The label or None if there is no label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label

    @property
    def vertices(self):
        """ The vertices of the graph

        :return: an iterable of vertices
        :rtype: iterable of :py:class:`pacman.model.graph.vertex.Vertex`
        """
        return self._vertices

    @property
    def edges(self):
        """ The edges of the graph

        :return: an iterable of edges
        :rtype: iterable of :py:class:`pacman.model.graph.edge.Edge`
        """
        return self._edges
