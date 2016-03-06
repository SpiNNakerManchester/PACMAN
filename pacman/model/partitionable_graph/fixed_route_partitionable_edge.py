from pacman.model.partitioned_graph.fixed_route_partitioned_edge import \
    FixedRoutePartitionedEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.partitionable_graph.abstract_partitionable_edge \
    import AbstractPartitionableEdge
from pacman import exceptions


class FixedRoutePartitionableEdge(AbstractPartitionableEdge):
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
        AbstractPartitionableEdge.__init__(self, pre_subvertex, post_subvertex,
                                           label)

    def is_partitionable_edge(self):
        """ helper method for is instance

        :return:
        """
        return True

    def create_subedge(self, pre_subvertex, post_subvertex, label=None):
        """ Create a fixed route partitioned edge from a fixed route\
            partitionable edge
        :param pre_subvertex: the source subvertex
        :param post_subvertex: the destination partitioned subvertex
        :param label: the label associated with the partitioned edge
        :param constraints: any constraints needed for the partitioned edge
        :return: the FixedRoutePartitionedEdge
        """
        if not isinstance(pre_subvertex, PartitionedVertex):
            raise exceptions.PacmanInvalidParameterException(
                "pre_subvertex", str(pre_subvertex),
                "Must be a PartitionedVertex")
        if not isinstance(post_subvertex, PartitionedVertex):
            raise exceptions.PacmanInvalidParameterException(
                "post_subvertex", str(post_subvertex),
                "Must be a PartitionedVertex")

        if label is None and self.label is not None:
            label = self.label

        return FixedRoutePartitionedEdge(pre_subvertex, post_subvertex, label)
