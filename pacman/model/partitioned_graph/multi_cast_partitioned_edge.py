from pacman.model.partitioned_graph.abstract_partitioned_edge import \
    AbstractPartitionedEdge


class MultiCastPartitionedEdge(AbstractPartitionedEdge):
    """ Represents part of a division of an edge to match the division of the\
        vertices on either side of the edge
    """

    def __init__(self, pre_subvertex, post_subvertex, label=None,
                 constraints=None):
        """

        :param pre_subvertex: the subvertex at the start of the subedge
        :type pre_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param post_subvertex: the subvertex at the end of the subedge
        :type post_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param label: The name of the edge
        :type label: str
        :param constraints: constraitns for this edge
        :type constraints: iterable of :
        pacman.model.constraints.abstract_constraints.abstract_constraint.AbstractConstraint
        :raise None: Raises no known exceptions
        """
        AbstractPartitionedEdge.__init__(self, pre_subvertex, post_subvertex,
                                         constraints, label)

    def is_partitioned_edge(self):
        """ helper method for is instance

        :return:
        """
        return True
