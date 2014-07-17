class Subedge(object):
    """ Represents part of a division of an edge to match the division of the\
        vertices on either side of the edge
    """

    def __init__(self, edge, pre_subvertex, post_subvertex, label=None):
        """
        :param edge: The edge which this is a subedge of
        :type edge: :py:class:`pacman.model.graph.edge.Edge`
        :param pre_subvertex: the subvertex at the start of the subedge
        :type pre_subvertex:\
                    :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :param post_subvertex: the subvertex at the end of the subedge
        :type post_subvertex:\
                    :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :param label: The name of the edge
        :type label: str
        :raise None: Raises no known exceptions
        """
        self._edge = edge
        self._pre_subvertex = pre_subvertex
        self._post_subvertex = post_subvertex
        self._label = label

    @property
    def pre_subvertex(self):
        """ The subvertex at the start of the subedge

        :return: the incoming subvertex
        :rtype: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :raise None: Raises no known exceptions
        """
        return  self._pre_subvertex

    @property
    def post_subvertex(self):
        """ The subvertex at the end of the subedge

        :return: the outgoing subvertex
        :rtype: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :raise None: Raises no known exceptions
        """
        return self._post_subvertex

    @property
    def edge(self):
        """ The edge to which this subedge refers

        :return: the edge
        :rtype: :py:class:`pacman.model.graph.edge.Edge`
        :raise None: Raises no known exceptions
        """
        return self._edge

    @property
    def label(self):
        """ The label of the subedge

        :return: The name, or None if there is no label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label
