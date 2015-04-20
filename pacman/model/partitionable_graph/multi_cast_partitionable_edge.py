from pacman.model.partitioned_graph.multi_cast_partitioned_edge import \
    MultiCastPartitionedEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.abstract_classes.abstract_partitionable_edge import \
    AbstractPartitionableEdge
from pacman import exceptions


class MultiCastPartitionableEdge(AbstractPartitionableEdge):
    """ Represents part of a division of an edge to match the division of the\
        vertices on either side of the edge
    """

    def __init__(self, pre_vertex, post_vertex, constraints=None, label=None):
        """

        :param pre_subvertex: the subvertex at the start of the subedge
        :type pre_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param post_subvertex: the subvertex at the end of the subedge
        :type post_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param constraints: The constraints of the edge
        :type constraints: list of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :param label: The name of the edge
        :type label: str
        :raise None: Raises no known exceptions
        """
        AbstractPartitionableEdge.__init__(self, pre_vertex, post_vertex,
                                           label, constraints)

    def is_partitionable_edge(self):
        """ helper method for is instance

        :return:
        """
        return True

    def create_subedge(self, pre_subvertex, post_subvertex, label=None,
                       constraints=None):
        """
        method for creating a partitioned multicast edge
        :param pre_subvertex: the soruce partitioned vertex
        :param post_subvertex: the destination partitioned vertex
        :param label: the label of this partitioned edge
        :param constraints: the constraints wnated to be put on this
        partitioned edge
        :return:
        """
        if not isinstance(pre_subvertex, PartitionedVertex):
            raise exceptions.PacmanInvalidParameterException(
                "pre_subvertex", str(pre_subvertex),
                "Must be a PartitionedVertex")
        if not isinstance(post_subvertex, PartitionedVertex):
            raise exceptions.PacmanInvalidParameterException(
                "post_subvertex", str(post_subvertex), "PartitionedVertex")

        if label is None and self.label is not None:
            label = self.label

        return MultiCastPartitionedEdge(pre_subvertex, post_subvertex, label,
                                        constraints)
