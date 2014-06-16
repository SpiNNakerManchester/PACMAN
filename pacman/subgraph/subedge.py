__author__ = 'daviess'

class Subedge(object):
    """A subedge object"""

    def __init__(self, label, edge, pre_subvertex, post_subvertex):
        """Create a new edge
        :param label: The name of the edge
        :type label: str
        :param edge: The edge to which this subedge refers
        :type edge: pacman.graph.edge.Edge
        :param pre_subvertex: the outgoing subvertex
        :type pre_subvertex: pacman.subgraph.subvertex.Subvertex
        :param post_subvertex: the incoming subvertex
        :type post_subvertex: pacman.subgraph.subvertex.Subvertex
        :return: a Subedge
        :rtype: pacman.subgraph.subedge.Subedge
        :raises None: Raises no known exceptions
        """
        pass

    @property
    def pre_subvertex(self):
        """ Return the outgoing subvertex
        :return: the outgoing subvertex
        :rtype: pacman.subgraph.subvertex.Subvertex
        :raises None: Raises no known exceptions
        """
        pass

    @property
    def post_subvertex(self):
        """ Return the incoming subvertex
        :return: the incoming subvertex
        :rtype: pacman.subgraph.subvertex.Subvertex
        :raises None: Raises no known exceptions
        """
        pass

    @property
    def edge(self):
        """ Return the edge to which this subedge refers
        :return: the edge to which this subedge refers
        :rtype: pacman.graph.edge.Edge
        :raises None: Raises no known exceptions
        """
        pass

    @property
    def label(self):
        """ Get the label of the subedge
        :return: The name of the subedge
        :rtype: str
        :raises None: Raises no known exceptions
        """
        pass
