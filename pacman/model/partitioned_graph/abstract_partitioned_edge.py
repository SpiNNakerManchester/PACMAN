from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractPartitionedEdge(object):
    """ Represents part of a division of an edge to match the division of the\
        vertices on either side of the edge
    """

    def __init__(self, pre_subvertex, post_subvertex, label=None, weight=1):
        """

        :param pre_subvertex: the subvertex at the start of the subedge
        :type pre_subvertex:\
                    :py:class:`pacman.model.graph.simple_partitioned_vertex.PartitionedVertex`
        :param post_subvertex: the subvertex at the end of the subedge
        :type post_subvertex:\
                    :py:class:`pacman.model.graph.simple_partitioned_vertex.PartitionedVertex`
        :param constraints: The constraints of the vertex
        :type constraints: list of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :param label: The name of the edge
        :type label: str
        :param weight: an optional weight for the edge (default is 1)
        :type weight: int
        :raise None: Raises no known exceptions
        """
        self._pre_subvertex = pre_subvertex
        self._post_subvertex = post_subvertex
        self._label = label
        self._weight = weight

    @abstractmethod
    def is_partitioned_edge(self):
        """ helper method for isinstance

        :return:
        """

    @property
    def pre_subvertex(self):
        """ The partitioned vertex at the start of the edge

        :return: the incoming partitioned vertex
        :rtype:\
                    :py:class:`pacman.model.graph.simple_partitioned_vertex.PartitionedVertex`
        :raise None: Raises no known exceptions
        """
        return self._pre_subvertex

    @property
    def post_subvertex(self):
        """ The partitioned vertex at the end of the edge

        :return: the outgoing partitioned vertex
        :rtype:\
                    :py:class:`pacman.model.graph.simple_partitioned_vertex.PartitionedVertex`
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

    @property
    def weight(self):
        """ The weight of the edge in the graph relative to other weights; an\
            indication of the amount of traffic that might flow down the edge

        :return: The weight of the edge
        :rtype: int
        """
        return self._weight

    def __str__(self):
        return "PartitionedEdge:{}->{}".format(self._pre_subvertex,
                                               self._post_subvertex)
