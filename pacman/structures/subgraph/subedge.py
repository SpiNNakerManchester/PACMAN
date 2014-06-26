__author__ = 'daviess'


class Subedge(object):
    """Creates a new subedge object related to an edge"""

    def __init__(self, edge, pre_subvertex, post_subvertex, label=None):
        """

        :param edge: The edge to which this subedge refers
        :param pre_subvertex: the outgoing subvertex
        :param post_subvertex: the incoming subvertex
        :param label: The name of the edge
        :type edge: pacman.graph.edge.Edge
        :type pre_subvertex: pacman.subgraph.subvertex.Subvertex
        :type post_subvertex: pacman.subgraph.subvertex.Subvertex
        :type label: str or None
        :return: a Subedge
        :rtype: pacman.subgraph.subedge.Subedge
        :raise None: Raises no known exceptions
        """
        pass

    @property
    def pre_subvertex(self):
        """
        Returns the outgoing subvertex

        :return: the outgoing subvertex
        :rtype: pacman.subgraph.subvertex.Subvertex
        :raise None: Raises no known exceptions
        """
        pass

    @property
    def post_subvertex(self):
        """
        Returns the incoming subvertex

        :return: the incoming subvertex
        :rtype: pacman.subgraph.subvertex.Subvertex
        :raise None: Raises no known exceptions
        """
        pass

    @property
    def edge(self):
        """
        Returns the edge to which this subedge refers

        :return: the edge to which this subedge refers
        :rtype: pacman.graph.edge.Edge
        :raise None: Raises no known exceptions
        """
        pass

    @property
    def label(self):
        """
        Returns the label of the subedge

        :return: The name of the subedge
        :rtype: str or None
        :raise None: Raises no known exceptions
        """
        pass
