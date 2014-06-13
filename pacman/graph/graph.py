__author__ = 'stokesa6'

class Graph(object):


    def __init__(self, label, vertexes=None, edges=None):
        ''' create a graph object
        :param label: a identifier for the graph
        :param vertexes: a collection of vertexes
        :param edges: a collection of edges
        :type label: str
        :type vertexes: None or iterable object
        :type edges: None or iterable object
        :return: a new graph object
        :rtype: pacman.graph.graph.Graph
        :raises None: does not raise any known exceptions
        '''
        pass


    def add_vertex(self, vertex):
        ''' adds a vertex object to this graph object
        :param vertex: a vertex to be added to the graph
        :type vertex: pacman.graph.vertex.Vertex
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        '''
        pass

    def add_vertexes(self, vertexes):
        ''' adds a collection of vertex objects to this graph object
        :param vertexes: a iterable object containing vertex objects to be
                         added to the graph
        :type vertexes: iterable object
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        '''
        pass


    def add_edge(self, edge):
        ''' adds a edge object to this graph object
        :param edge: a edge to be added to the graph
        :type edge: pacman.graph.edge.Edge
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        '''
        pass

    def add_edges(self, edges):
        ''' adds a collection of edge objects to this graph object
        :param edges: a iterable object containing edge objects to be
                      added to the graph
        :type edges: iterable object
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        '''
        pass

    def outgoing_edges_from_vertex(self, vertex):
        ''' locates a collection of edges which contain the vertex as its
            pre_vertex. Can return an empty collection if no edges exists that
            meet the criteria
        :param vertex: the vertex which will be used to locate its outgoing
                       edges
        :type vertex:  pacman.graph.vertex.Vertex
        :return: a list of edges which have vertex as their pre_vertex
        :rtype: iterable object
        :raises None: does not raise any known exceptions
        '''
        pass

    def incoming_edges_from_vertex(self, vertex):
        ''' locates a collection of edges which contain the vertex as its
            post_vertex. Can return an empty collection if no edges exists that
            meet the criteria
        :param vertex: the vertex which will be used to locate its incoming
                       edges
        :type vertex:  pacman.graph.vertex.Vertex
        :return: a list of edges which have vertex as their post_vertex
        :rtype: iterable object
        :raises None: does not raise any known exceptions
        '''
        pass

