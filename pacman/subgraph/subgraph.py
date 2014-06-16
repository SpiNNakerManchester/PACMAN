__author__ = 'daviess'

class Subgraph(object):
    """ a subgraph object """

    def __init__(self, label, graph, subvertices=None, subedges=None):
        """ create a subgraph object
        :param label: an identifier for the subgraph
        :param graph: the graph object to which this subgraph refers
        :param subvertices: a collection of vertices
        :param subedges: a collection of edges
        :type label: str
        :type graph: pacman.graph.graph.Graph
        :type subvertices: None or iterable object
        :type subedges: None or iterable object
        :return: a new subgraph object
        :rtype: pacman.subgraph.subgraph.Subgraph
        :raises None: does not raise any known exceptions
        """
        pass

    def add_subvertex(self, subvertex):
        """ adds a subvertex object to this graph object
        :param subvertex: a subvertex to be added to the graph
        :type subvertex: pacman.subgraph.subvertex.Subvertex
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def add_subvertices(self, subvertices):
        """ adds a collection of subvertex objects to this subgraph object
        :param subvertices: an iterable object containing
                         subvertex objects to be added
                         to the subgraph
        :type subvertices: iterable object
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass


    def add_subedge(self, subedge):
        """ adds a subedge object to this subgraph object
        :param subedge: a subedge to be added to the subgraph
        :type subedge: pacman.subgraph.subedge.Subedge
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def add_subedges(self, subedges):
        """ adds a collection of subedge objects to this subgraph object
        :param subedges: an iterable object containing
                         subedge objects to be added
                         to the subgraph
        :type subedges: iterable object
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def outgoing_subedges_from_subvertex(self, subvertex):
        """ locates a collection of subedges which contain the subvertex as its
            pre_subvertex. Can return an empty collection if no subedges exist
            that meet the criteria
        :param subvertex: the subvertex which will be used to locate its outgoing
                       subedges
        :type subvertex:  pacman.subgraph.subvertex.Subvertex
        :return: a list of subedges which have subvertex as their pre_subvertex
        :rtype: iterable object
        :raises None: does not raise any known exceptions
        """
        pass

    def incoming_subedges_from_subvertex(self, subvertex):
        """ locates a collection of subedges which contain the subvertex as its
            post_subvertex. Can return an empty collection if no subedges exist
            that meet the criteria
        :param subvertex: the subvertex which will be used to locate its incoming
                       subedges
        :type subvertex:  pacman.subgraph.subvertex.Subvertex
        :return: a list of subedges which have subvertex as their post_subvertex
        :rtype: iterable object
        :raises None: does not raise any known exceptions
        """
        pass

    @property
    def graph(self):
        """returns the graph object on which this subgraph has been instantiated
        :return: a graph object connected with this subgraph
        :rtype: pacman.graph.graph.Graph
        """

    @property
    def subvertices(self):
        """returns the subvertices collection from this subgraph object
        :return: an iterable object that contains the subvertices of this subgraph
        :rtype: iterable object
        """

    @property
    def subedges(self):
        """returns the subedges collection from this subgraph object
        :return: an iterable object that contains the subedges of this subgraph
        :rtype: iterable object
        """
