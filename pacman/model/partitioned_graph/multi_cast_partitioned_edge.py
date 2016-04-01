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
        :raise None: Raises no known exceptions
        """
        AbstractPartitionedEdge.__init__(self, pre_subvertex, post_subvertex,
                                         label)

    def is_partitioned_edge(self):
        return True

    def __eq__(self, other):
        if not isinstance(other, MultiCastPartitionedEdge):
            return False
        else:
            if (self._pre_subvertex == other.pre_subvertex and
                    self._post_subvertex == other.post_subvertex and
                    self._label == other.label):
                return True
            else:
                return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        if self._label is None:
            return hash((self._pre_subvertex, self._post_subvertex))
        return hash((self._pre_subvertex, self._post_subvertex, self._label))

