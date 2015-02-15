class PartitionedEdge(object):
    """ Represents an edge between two PartitionedVertex instances
    """

    def __init__(self, pre_subvertex, post_subvertex, label=None):
        """

        :param pre_subvertex: the subvertex at the start of the subedge
        :type pre_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param post_subvertex: the subvertex at the end of the subedge
        :type post_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param label: The name of the edge
        :type label: str
        :param n_keys: The number of distinct keys required by the partitioned\
                    edge for routing purposes
        :raise None: Raises no known exceptions
        """
        self._pre_subvertex = pre_subvertex
        self._post_subvertex = post_subvertex
        self._label = label

    @property
    def pre_subvertex(self):
        """ The partitioned vertex at the start of the edge

        :return: the incoming partitioned vertex
        :rtype: :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :raise None: Raises no known exceptions
        """
        return self._pre_subvertex

    @property
    def post_subvertex(self):
        """ The partitioned vertex at the end of the edge

        :return: the outgoing partitioned vertex
        :rtype: :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :raise None: Raises no known exceptions
        """
        return self._post_subvertex

    @property
    def label(self):
        """ The label of the edge

        :return: The name, or None if there is no label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label

    def __str__(self):
        return "PartitionedEdge between {}:{}".format(self._pre_subvertex,
                                                      self._post_subvertex)

    def __repr__(self):
        return self.__str__()
