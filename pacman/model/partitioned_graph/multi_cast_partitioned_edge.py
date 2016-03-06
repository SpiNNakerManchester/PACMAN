from pacman.model.partitioned_graph.abstract_partitioned_edge import \
    AbstractPartitionedEdge


class MultiCastPartitionedEdge(AbstractPartitionedEdge):
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
        """
        AbstractPartitionedEdge.__init__(self, pre_subvertex, post_subvertex,
                                         label)

    def is_partitioned_edge(self):
        return True
