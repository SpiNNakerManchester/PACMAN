from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
from pacman.model.partitioned_graph.abstract_partitioned_edge import \
    AbstractPartitionedEdge


@add_metaclass(ABCMeta)
class FixedRoutePartitionedEdge(AbstractPartitionedEdge):
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
        AbstractPartitionedEdge.__init__(self, pre_subvertex, post_subvertex,
                                         label)

    @abstractmethod
    def is_fixed_route_partitioned_edge(self):
        """ helper method for is instance

        :return:
        """

    def is_partitioned_edge(self):
        """ helper method for is instance

        :return:
        """
        return True