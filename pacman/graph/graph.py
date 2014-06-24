__author__ = 'stokesa6'

from pacman.graph.vertex import Vertex
from pacman.graph.edge import Edge


class Graph(object):
    """ Creates a new graph object """

    def __init__(self, label=None, vertices=None, edges=None):
        """

        :param label: an identifier for the graph
        :param vertices: a collection of vertices
        :param edges: a collection of edges
        :type label: str or None
        :type vertices: None or iterable object
        :type edges: None or iterable object
        :return: a new graph object
        :rtype: pacman.graph.graph.Graph
        :raise None: does not raise any known exceptions
        """
        self._label = label
        self._vertices = list()
        self._edges = list()

        self.add_vertices(vertices)
        self.add_edges(edges)

    def add_vertex(self, vertex):
        """
        Adds a vertex object to this graph object

        :param vertex: a vertex to be added to the graph
        :type vertex: pacman.graph.vertex.Vertex
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        if vertex is not None and isinstance(vertex, Vertex):
            self._vertices.append(vertex)


    def add_vertices(self, vertices):
        """
        Adds a collection of vertex objects to this graph object

        :param vertices: an iterable object containing vertex objects to be\
               added to the graph
        :type vertices: iterable object
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        if vertices is not None:
            for next_vertex in vertices:
                self.add_vertex(next_vertex)


    def add_edge(self, edge):
        """
        Adds a edge object to this graph object

        :param edge: a edge to be added to the graph
        :type edge: pacman.graph.edge.Edge
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        if edge is not None and isinstance(edge, Edge):
            self._edges.append(edge)

    def add_edges(self, edges):
        """
        Adds a collection of edge objects to this graph object

        :param edges: an iterable object containing edge objects to be\
                      added to the graph
        :type edges: iterable object
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        if edges is not None:
            for next_edge in edges:
                self.add_edge(next_edge)

    def outgoing_edges_from_vertex(self, vertex):
        """
        Locates a collection of edges which contain the vertex as its\
        pre_vertex. Can return an empty collection if no edges exist that\
        meet the criteria

        :param vertex: the vertex which will be used to locate its outgoing\
                       edges
        :type vertex:  pacman.graph.vertex.Vertex
        :return: a list of edges which have vertex as their pre_vertex
        :rtype: list of pacman.graph.edge.Edge
        :raise None: does not raise any known exceptions
        """
        return_list = list()

        for temp_edge in self._edges:
            if temp_edge.pre_vertex == vertex:
                return_list.append(temp_edge)

        return return_list

    def incoming_edges_to_vertex(self, vertex):
        """
        Locates a collection of edges which contain the vertex as its\
        post_vertex. Can return an empty collection if no edges exist that\
        meet the criteria

        :param vertex: the vertex which will be used to locate its incoming\
                       edges
        :type vertex:  pacman.graph.vertex.Vertex
        :return: a list of edges which have vertex as their post_vertex
        :rtype: list of pacman.graph.edge.Edge
        :raise None: does not raise any known exceptions
        """
        return_list = list()

        for temp_edge in self._edges:
            if temp_edge.post_vertex == vertex:
                return_list.append(temp_edge)

        return return_list

    @property
    def label(self):
        """
        Returns the label of the graph

        :return: The name of the graph
        :rtype: str or None
        :raise None: Raises no known exceptions
        """
        return self._label

    @property
    def vertices(self):
        """
        Returns the vertices collection from this graph object

        :return: an iterable object that contains the vertices of this graph
        :rtype: iterable object
        """
        return self._vertices

    @property
    def edges(self):
        """
        Returns the edges collection from this graph object

        :return: an iterable object that contains the edges of this graph
        :rtype: iterable object
        """
        return self._edges

