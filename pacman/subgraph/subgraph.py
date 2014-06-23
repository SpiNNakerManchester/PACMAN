__author__ = 'daviess'


class Subgraph(object):
    """ Creates a subgraph object related to a graph """

    def __init__(self, graph, label=None, subvertices=None, subedges=None):
        """

        :param graph: the graph object to which this subgraph refers
        :param label: an identifier for the subgraph
        :param subvertices: a collection of vertices
        :param subedges: a collection of edges
        :type graph: pacman.graph.graph.Graph
        :type label: str or None
        :type subvertices: None or iterable object
        :type subedges: None or iterable object
        :return: a new subgraph object
        :rtype: pacman.subgraph.subgraph.Subgraph
        :raise None: does not raise any known exceptions
        """
        self._label = label
        self._graph = graph
        self._subvertices = list()
        self._subedges = list()

        self.add_subvertices(subvertices)
        self.add_subedges(subedges)

    def add_subvertex(self, subvertex):
        """
        Adds a subvertex object to this graph object

        :param subvertex: a subvertex to be added to the graph
        :type subvertex: pacman.subgraph.subvertex.Subvertex
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass

    def add_subvertices(self, subvertices):
        """
        Adds a collection of subvertex objects to this subgraph object

        :param subvertices: an iterable object containing subvertex objects to be added\
                         to the subgraph
        :type subvertices: iterable object
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass


    def add_subedge(self, subedge):
        """
        Adds a subedge object to this subgraph object

        :param subedge: a subedge to be added to the subgraph
        :type subedge: pacman.subgraph.subedge.Subedge
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass

    def add_subedges(self, subedges):
        """
        Adds a collection of subedge objects to this subgraph object

        :param subedges: an iterable object containing subedge objects to be added\
                         to the subgraph
        :type subedges: iterable object
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass

    def outgoing_subedges_from_subvertex(self, subvertex):
        """
        Locates a collection of subedges which contain the subvertex as its\
        pre_subvertex. Can return an empty collection if no subedges exist\
        that meet the criteria

        :param subvertex: the subvertex which will be used to locate its outgoing\
                       subedges
        :type subvertex:  pacman.subgraph.subvertex.Subvertex
        :return: a list of subedges which have subvertex as their pre_subvertex
        :rtype: iterable object
        :raise None: does not raise any known exceptions
        """
        pass

    def incoming_subedges_from_subvertex(self, subvertex):
        """
        Locates a collection of subedges which contain the subvertex as its\
        post_subvertex. Can return an empty collection if no subedges exist\
        that meet the criteria

        :param subvertex: the subvertex which will be used to locate its incoming\
                       subedges
        :type subvertex:  pacman.subgraph.subvertex.Subvertex
        :return: a list of subedges which have subvertex as their post_subvertex
        :rtype: iterable object
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def graph(self):
        """
        Returns the graph object on which this subgraph has been instantiated

        :return: a graph object connected with this subgraph
        :rtype: pacman.graph.graph.Graph
        """
        return self._graph

    @property
    def subvertices(self):
        """
        Returns the subvertices collection from this subgraph object

        :return: an iterable object that contains the subvertices of this subgraph
        :rtype: iterable object
        """
        return self._subvertices

    @property
    def subedges(self):
        """
        Returns the subedges collection from this subgraph object

        :return: an iterable object that contains the subedges of this subgraph
        :rtype: iterable object
        """
        return self._subedges

    @property
    def label(self):
        """
        Returns the label of the subgraph

        :return: The name of the subgraph
        :rtype: str or None
        :raise None: Raises no known exceptions
        """
        return self._label