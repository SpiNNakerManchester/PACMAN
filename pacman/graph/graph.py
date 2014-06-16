__author__ = 'stokesa6'

class Graph(object):
    """ a graph object """

    def __init__(self, label, vertices=None, edges=None):
        """ create a graph object
        :param label: an identifier for the graph
        :param vertices: a collection of vertices
        :param edges: a collection of edges
        :type label: str
        :type vertices: None or iterable object
        :type edges: None or iterable object
        :return: a new graph object
        :rtype: pacman.graph.graph.Graph
        :raises None: does not raise any known exceptions
        """
        pass


    def add_vertex(self, vertex):
        """ adds a vertex object to this graph object
        :param vertex: a vertex to be added to the graph
        :type vertex: pacman.graph.vertex.Vertex
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def add_vertices(self, vertices):
        """ adds a collection of vertex objects to this graph object
        :param vertices: an iterable object containing vertex objects to be
                         added to the graph
        :type vertices: iterable object
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass


    def add_edge(self, edge):
        """ adds a edge object to this graph object
        :param edge: a edge to be added to the graph
        :type edge: pacman.graph.edge.Edge
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def add_edges(self, edges):
        """ adds a collection of edge objects to this graph object
        :param edges: an iterable object containing edge objects to be
                      added to the graph
        :type edges: iterable object
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def outgoing_edges_from_vertex(self, vertex):
        """ locates a collection of edges which contain the vertex as its
            pre_vertex. Can return an empty collection if no edges exist that
            meet the criteria
        :param vertex: the vertex which will be used to locate its outgoing
                       edges
        :type vertex:  pacman.graph.vertex.Vertex
        :return: a list of edges which have vertex as their pre_vertex
        :rtype: iterable object
        :raises None: does not raise any known exceptions
        """
        pass

    def incoming_edges_from_vertex(self, vertex):
        """ locates a collection of edges which contain the vertex as its
            post_vertex. Can return an empty collection if no edges exist that
            meet the criteria
        :param vertex: the vertex which will be used to locate its incoming
                       edges
        :type vertex:  pacman.graph.vertex.Vertex
        :return: a list of edges which have vertex as their post_vertex
        :rtype: iterable object
        :raises None: does not raise any known exceptions
        """
        pass

    @property
    def vertices(self):
        """returns the vertices collection from this graph object
        :return: an iterable object that contains the vertices of this graph
        :rtype: iterable object
        """

    @property
    def edges(self):
        """
        returns the edges collection from this graph object
        :return: an iterable object that contains the edges of this graph
        :rtype: iterable object
        """
