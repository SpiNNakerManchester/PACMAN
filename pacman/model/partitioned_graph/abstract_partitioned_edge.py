from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractPartitionedEdge(object):
    """ Represents part of a division of an edge to match the division of the\
        vertices on either side of the edge
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
        :raise None: Raises no known exceptions
        """
        self._pre_subvertex = pre_subvertex
        self._post_subvertex = post_subvertex
        self._label = label

    @abstractmethod
    def is_partitioned_edge(self):
        """ helper method for isinstance

        :return:
        """

    @property
    def pre_subvertex(self):
        """ The subvertex at the start of the subedge

        :return: the incoming subvertex
        :rtype: :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :raise None: Raises no known exceptions
        """
        return self._pre_subvertex

    @property
    def post_subvertex(self):
        """ The subvertex at the end of the subedge

        :return: the outgoing subvertex
        :rtype: :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :raise None: Raises no known exceptions
        """
        return self._post_subvertex

    @property
    def label(self):
        """ The label of the subedge

        :return: The name, or None if there is no label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label

    def __str__(self):
        return "{}:{}:{}".format(self.label, self.pre_subvertex,
                                 self.post_subvertex)

    def __repr__(self):
        return self.__str__()
